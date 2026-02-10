"""
ScreeningStrategyService 单元测试

测试应用层服务的业务逻辑编排。
使用 Mock 模拟 Repository 和领域服务以隔离依赖。

Requirements:
- 7.1: 实现 create_strategy、update_strategy、delete_strategy、get_strategy、
       list_strategies、execute_strategy 方法
- 7.3: execute_strategy 加载候选股票 → 调用 execute() → 创建 ScreeningSession → 
       持久化会话 → 返回结果
- 7.4: 使用重复名称调用 create_strategy 时抛出适当的错误
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, call
import uuid

from contexts.screening.application.services.screening_strategy_service import (
    ScreeningStrategyService
)
from contexts.screening.domain.models.screening_strategy import ScreeningStrategy
from contexts.screening.domain.models.screening_session import ScreeningSession
from contexts.screening.domain.models.filter_group import FilterGroup
from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
from contexts.screening.domain.value_objects.identifiers import StrategyId
from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import NumericValue
from contexts.screening.domain.value_objects.screening_result import ScreeningResult
from contexts.screening.domain.value_objects.scored_stock import ScoredStock
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from contexts.screening.domain.enums.enums import LogicalOperator, NormalizationMethod
from contexts.screening.domain.exceptions import (
    DuplicateNameError,
    StrategyNotFoundError,
)
from shared_kernel.value_objects.stock_code import StockCode


class TestScreeningStrategyService:
    """ScreeningStrategyService 单元测试"""
    
    @pytest.fixture
    def mock_strategy_repo(self):
        """创建 Mock 策略仓储"""
        repo = Mock()
        repo.save = Mock()
        repo.find_by_id = Mock(return_value=None)
        repo.find_by_name = Mock(return_value=None)
        repo.find_all = Mock(return_value=[])
        repo.delete = Mock()
        repo.exists = Mock(return_value=False)
        repo.count = Mock(return_value=0)
        return repo
    
    @pytest.fixture
    def mock_session_repo(self):
        """创建 Mock 会话仓储"""
        repo = Mock()
        repo.save = Mock()
        repo.find_by_id = Mock(return_value=None)
        repo.find_by_strategy_id = Mock(return_value=[])
        repo.find_recent = Mock(return_value=[])
        return repo
    
    @pytest.fixture
    def mock_market_data_repo(self):
        """创建 Mock 市场数据仓储"""
        repo = Mock()
        repo.get_all_stock_codes = Mock(return_value=[])
        repo.get_stocks_by_codes = Mock(return_value=[])
        return repo
    
    @pytest.fixture
    def mock_scoring_service(self):
        """创建 Mock 评分服务"""
        service = Mock()
        service.score_stocks = Mock(return_value=[])
        return service
    
    @pytest.fixture
    def mock_calc_service(self):
        """创建 Mock 指标计算服务"""
        service = Mock()
        service.calculate_indicator = Mock(return_value=0.0)
        return service
    
    @pytest.fixture
    def service(
        self,
        mock_strategy_repo,
        mock_session_repo,
        mock_market_data_repo,
        mock_scoring_service,
        mock_calc_service
    ):
        """创建 ScreeningStrategyService 实例"""
        return ScreeningStrategyService(
            strategy_repo=mock_strategy_repo,
            session_repo=mock_session_repo,
            market_data_repo=mock_market_data_repo,
            scoring_service=mock_scoring_service,
            calc_service=mock_calc_service
        )
    
    @pytest.fixture
    def sample_filters_dict(self):
        """创建示例筛选条件字典"""
        return {
            'group_id': str(uuid.uuid4()),
            'operator': 'AND',
            'conditions': [
                {
                    'field': 'ROE',
                    'operator': '>',
                    'value': {'type': 'numeric', 'value': 0.15, 'unit': None}
                }
            ],
            'sub_groups': []
        }
    
    @pytest.fixture
    def sample_scoring_config_dict(self):
        """创建示例评分配置字典"""
        return {
            'weights': {'ROE': 0.5, 'PE': 0.5},
            'normalization_method': 'min_max'
        }
    
    @pytest.fixture
    def sample_strategy(self, sample_filters_dict, sample_scoring_config_dict):
        """创建示例 ScreeningStrategy 领域对象"""
        strategy_id = StrategyId.generate()
        
        filters = FilterGroup.from_dict(sample_filters_dict)
        scoring_config = ScoringConfig.from_dict(sample_scoring_config_dict)
        
        now = datetime.now(timezone.utc)
        
        return ScreeningStrategy(
            strategy_id=strategy_id,
            name="测试策略",
            description="这是一个测试策略",
            filters=filters,
            scoring_config=scoring_config,
            tags=["测试", "高ROE"],
            is_template=False,
            created_at=now,
            updated_at=now
        )
    
    # ==================== create_strategy 测试 ====================
    
    def test_create_strategy_success(
        self,
        service,
        mock_strategy_repo,
        sample_filters_dict,
        sample_scoring_config_dict
    ):
        """测试成功创建策略"""
        # 设置 mock：名称不存在
        mock_strategy_repo.find_by_name.return_value = None
        
        # 执行创建
        result = service.create_strategy(
            name="新策略",
            filters_dict=sample_filters_dict,
            scoring_config_dict=sample_scoring_config_dict,
            description="测试描述",
            tags=["标签1", "标签2"]
        )
        
        # 验证返回的策略
        assert result is not None
        assert result.name == "新策略"
        assert result.description == "测试描述"
        assert result.tags == ["标签1", "标签2"]
        
        # 验证 save 被调用
        mock_strategy_repo.save.assert_called_once()
    
    def test_create_strategy_duplicate_name_raises_error(
        self,
        service,
        mock_strategy_repo,
        sample_strategy,
        sample_filters_dict,
        sample_scoring_config_dict
    ):
        """测试创建重复名称策略时抛出 DuplicateNameError"""
        # 设置 mock：名称已存在
        mock_strategy_repo.find_by_name.return_value = sample_strategy
        
        # 执行创建并验证异常
        with pytest.raises(DuplicateNameError) as exc_info:
            service.create_strategy(
                name="测试策略",  # 与 sample_strategy 同名
                filters_dict=sample_filters_dict,
                scoring_config_dict=sample_scoring_config_dict
            )
        
        assert "测试策略" in str(exc_info.value)
        
        # 验证 save 未被调用
        mock_strategy_repo.save.assert_not_called()
    
    def test_create_strategy_empty_name_raises_error(
        self,
        service,
        mock_strategy_repo,
        sample_filters_dict,
        sample_scoring_config_dict
    ):
        """测试创建空名称策略时抛出 ValueError"""
        # 设置 mock：名称不存在
        mock_strategy_repo.find_by_name.return_value = None
        
        # 执行创建并验证异常
        with pytest.raises(ValueError) as exc_info:
            service.create_strategy(
                name="",  # 空名称
                filters_dict=sample_filters_dict,
                scoring_config_dict=sample_scoring_config_dict
            )
        
        assert "名称" in str(exc_info.value) or "空" in str(exc_info.value)
    
    def test_create_strategy_without_optional_params(
        self,
        service,
        mock_strategy_repo,
        sample_filters_dict,
        sample_scoring_config_dict
    ):
        """测试不提供可选参数时成功创建策略"""
        # 设置 mock：名称不存在
        mock_strategy_repo.find_by_name.return_value = None
        
        # 执行创建（不提供 description 和 tags）
        result = service.create_strategy(
            name="简单策略",
            filters_dict=sample_filters_dict,
            scoring_config_dict=sample_scoring_config_dict
        )
        
        # 验证返回的策略
        assert result is not None
        assert result.name == "简单策略"
        assert result.description is None
        assert result.tags == []
    
    # ==================== update_strategy 测试 ====================
    
    def test_update_strategy_success(
        self,
        service,
        mock_strategy_repo,
        sample_strategy
    ):
        """测试成功更新策略"""
        # 设置 mock：策略存在
        mock_strategy_repo.find_by_id.return_value = sample_strategy
        mock_strategy_repo.find_by_name.return_value = None
        
        # 执行更新
        result = service.update_strategy(
            strategy_id_str=sample_strategy.strategy_id.value,
            name="更新后的名称",
            description="更新后的描述"
        )
        
        # 验证返回的策略
        assert result is not None
        assert result.name == "更新后的名称"
        assert result.description == "更新后的描述"
        
        # 验证 save 被调用
        mock_strategy_repo.save.assert_called_once()
    
    def test_update_strategy_not_found_raises_error(
        self,
        service,
        mock_strategy_repo
    ):
        """测试更新不存在的策略时抛出 StrategyNotFoundError"""
        # 设置 mock：策略不存在
        mock_strategy_repo.find_by_id.return_value = None
        
        strategy_id = str(uuid.uuid4())
        
        # 执行更新并验证异常
        with pytest.raises(StrategyNotFoundError) as exc_info:
            service.update_strategy(
                strategy_id_str=strategy_id,
                name="新名称"
            )
        
        assert strategy_id in str(exc_info.value)
    
    def test_update_strategy_duplicate_name_raises_error(
        self,
        service,
        mock_strategy_repo,
        sample_strategy
    ):
        """测试更新为重复名称时抛出 DuplicateNameError"""
        # 创建另一个策略
        other_strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="其他策略",
            filters=sample_strategy.filters,
            scoring_config=sample_strategy.scoring_config
        )
        
        # 设置 mock：当前策略存在，新名称与其他策略重复
        mock_strategy_repo.find_by_id.return_value = sample_strategy
        mock_strategy_repo.find_by_name.return_value = other_strategy
        
        # 执行更新并验证异常
        with pytest.raises(DuplicateNameError) as exc_info:
            service.update_strategy(
                strategy_id_str=sample_strategy.strategy_id.value,
                name="其他策略"  # 与 other_strategy 同名
            )
        
        assert "其他策略" in str(exc_info.value)
    
    def test_update_strategy_same_name_allowed(
        self,
        service,
        mock_strategy_repo,
        sample_strategy
    ):
        """测试更新为相同名称时允许（自己的名称）"""
        # 设置 mock：当前策略存在，名称查询返回自己
        mock_strategy_repo.find_by_id.return_value = sample_strategy
        mock_strategy_repo.find_by_name.return_value = sample_strategy  # 返回自己
        
        # 执行更新（使用相同名称）
        result = service.update_strategy(
            strategy_id_str=sample_strategy.strategy_id.value,
            name=sample_strategy.name  # 相同名称
        )
        
        # 验证成功
        assert result is not None
        mock_strategy_repo.save.assert_called_once()
    
    def test_update_strategy_partial_update(
        self,
        service,
        mock_strategy_repo,
        sample_strategy
    ):
        """测试部分更新（只更新部分字段）"""
        original_name = sample_strategy.name
        original_description = sample_strategy.description
        
        # 设置 mock：策略存在
        mock_strategy_repo.find_by_id.return_value = sample_strategy
        
        # 只更新 tags
        result = service.update_strategy(
            strategy_id_str=sample_strategy.strategy_id.value,
            tags=["新标签"]
        )
        
        # 验证只有 tags 被更新
        assert result is not None
        assert result.name == original_name  # 名称未变
        assert result.tags == ["新标签"]  # tags 已更新
    
    def test_update_strategy_filters(
        self,
        service,
        mock_strategy_repo,
        sample_strategy,
        sample_filters_dict
    ):
        """测试更新筛选条件"""
        # 设置 mock：策略存在
        mock_strategy_repo.find_by_id.return_value = sample_strategy
        
        # 创建新的筛选条件
        new_filters_dict = {
            'group_id': str(uuid.uuid4()),
            'operator': 'OR',
            'conditions': [
                {
                    'field': 'PE',
                    'operator': '<',
                    'value': {'type': 'numeric', 'value': 20.0, 'unit': None}
                }
            ],
            'sub_groups': []
        }
        
        # 执行更新
        result = service.update_strategy(
            strategy_id_str=sample_strategy.strategy_id.value,
            filters_dict=new_filters_dict
        )
        
        # 验证筛选条件已更新
        assert result is not None
        assert result.filters.operator == LogicalOperator.OR
    
    # ==================== delete_strategy 测试 ====================
    
    def test_delete_strategy_success(
        self,
        service,
        mock_strategy_repo,
        sample_strategy
    ):
        """测试成功删除策略"""
        # 设置 mock：策略存在
        mock_strategy_repo.exists.return_value = True
        
        # 执行删除
        service.delete_strategy(sample_strategy.strategy_id.value)
        
        # 验证 delete 被调用
        mock_strategy_repo.delete.assert_called_once()
    
    def test_delete_strategy_not_found_raises_error(
        self,
        service,
        mock_strategy_repo
    ):
        """测试删除不存在的策略时抛出 StrategyNotFoundError"""
        # 设置 mock：策略不存在
        mock_strategy_repo.exists.return_value = False
        
        strategy_id = str(uuid.uuid4())
        
        # 执行删除并验证异常
        with pytest.raises(StrategyNotFoundError) as exc_info:
            service.delete_strategy(strategy_id)
        
        assert strategy_id in str(exc_info.value)
        
        # 验证 delete 未被调用
        mock_strategy_repo.delete.assert_not_called()
    
    # ==================== get_strategy 测试 ====================
    
    def test_get_strategy_found(
        self,
        service,
        mock_strategy_repo,
        sample_strategy
    ):
        """测试获取存在的策略"""
        # 设置 mock：策略存在
        mock_strategy_repo.find_by_id.return_value = sample_strategy
        
        # 执行获取
        result = service.get_strategy(sample_strategy.strategy_id.value)
        
        # 验证返回的策略
        assert result is not None
        assert result.strategy_id == sample_strategy.strategy_id
    
    def test_get_strategy_not_found(
        self,
        service,
        mock_strategy_repo
    ):
        """测试获取不存在的策略返回 None"""
        # 设置 mock：策略不存在
        mock_strategy_repo.find_by_id.return_value = None
        
        strategy_id = str(uuid.uuid4())
        
        # 执行获取
        result = service.get_strategy(strategy_id)
        
        # 验证返回 None
        assert result is None
    
    # ==================== list_strategies 测试 ====================
    
    def test_list_strategies_returns_list(
        self,
        service,
        mock_strategy_repo,
        sample_strategy
    ):
        """测试列出策略返回列表"""
        # 设置 mock：返回策略列表
        mock_strategy_repo.find_all.return_value = [sample_strategy]
        
        # 执行列出
        result = service.list_strategies()
        
        # 验证返回列表
        assert len(result) == 1
        assert result[0].strategy_id == sample_strategy.strategy_id
    
    def test_list_strategies_empty(
        self,
        service,
        mock_strategy_repo
    ):
        """测试列出策略返回空列表"""
        # 设置 mock：返回空列表
        mock_strategy_repo.find_all.return_value = []
        
        # 执行列出
        result = service.list_strategies()
        
        # 验证返回空列表
        assert result == []
    
    def test_list_strategies_with_pagination(
        self,
        service,
        mock_strategy_repo
    ):
        """测试列出策略使用分页参数"""
        # 设置 mock
        mock_strategy_repo.find_all.return_value = []
        
        # 执行列出
        service.list_strategies(limit=50, offset=10)
        
        # 验证分页参数
        mock_strategy_repo.find_all.assert_called_once_with(limit=50, offset=10)
    
    # ==================== execute_strategy 测试 ====================
    
    def test_execute_strategy_success(
        self,
        service,
        mock_strategy_repo,
        mock_session_repo,
        mock_market_data_repo,
        mock_scoring_service,
        mock_calc_service,
        sample_strategy
    ):
        """测试成功执行策略"""
        # 设置 mock：策略存在
        mock_strategy_repo.find_by_id.return_value = sample_strategy
        
        # 设置 mock：市场数据
        stock_codes = [StockCode("600000.SH"), StockCode("000001.SZ")]
        mock_market_data_repo.get_all_stock_codes.return_value = stock_codes
        
        # 创建 mock 股票
        mock_stock1 = Mock()
        mock_stock1.stock_code = stock_codes[0]
        mock_stock2 = Mock()
        mock_stock2.stock_code = stock_codes[1]
        mock_market_data_repo.get_stocks_by_codes.return_value = [mock_stock1, mock_stock2]
        
        # 设置 mock：评分服务返回带评分的股票
        scored_stock = Mock(spec=ScoredStock)
        scored_stock.stock_code = stock_codes[0]
        scored_stock.stock_name = "测试股票"
        scored_stock.score = 85.0
        mock_scoring_service.score_stocks.return_value = [scored_stock]
        
        # 执行策略
        result = service.execute_strategy(sample_strategy.strategy_id.value)
        
        # 验证返回结果
        assert result is not None
        assert isinstance(result, ScreeningResult)
        
        # 验证会话被保存
        mock_session_repo.save.assert_called_once()
    
    def test_execute_strategy_not_found_raises_error(
        self,
        service,
        mock_strategy_repo
    ):
        """测试执行不存在的策略时抛出 StrategyNotFoundError"""
        # 设置 mock：策略不存在
        mock_strategy_repo.find_by_id.return_value = None
        
        strategy_id = str(uuid.uuid4())
        
        # 执行并验证异常
        with pytest.raises(StrategyNotFoundError) as exc_info:
            service.execute_strategy(strategy_id)
        
        assert strategy_id in str(exc_info.value)
    
    def test_execute_strategy_workflow(
        self,
        service,
        mock_strategy_repo,
        mock_session_repo,
        mock_market_data_repo,
        mock_scoring_service,
        mock_calc_service,
        sample_strategy
    ):
        """测试执行策略的完整工作流"""
        # 设置 mock：策略存在
        mock_strategy_repo.find_by_id.return_value = sample_strategy
        
        # 设置 mock：市场数据
        stock_codes = [StockCode("600000.SH")]
        mock_market_data_repo.get_all_stock_codes.return_value = stock_codes
        
        mock_stock = Mock()
        mock_stock.stock_code = stock_codes[0]
        mock_market_data_repo.get_stocks_by_codes.return_value = [mock_stock]
        
        # 设置 mock：评分服务
        mock_scoring_service.score_stocks.return_value = []
        
        # 执行策略
        service.execute_strategy(sample_strategy.strategy_id.value)
        
        # 验证工作流步骤
        # 1. 加载策略
        mock_strategy_repo.find_by_id.assert_called_once()
        
        # 2. 获取候选股票
        mock_market_data_repo.get_all_stock_codes.assert_called_once()
        mock_market_data_repo.get_stocks_by_codes.assert_called_once_with(stock_codes)
        
        # 3. 评分服务被调用
        mock_scoring_service.score_stocks.assert_called_once()
        
        # 4. 会话被保存
        mock_session_repo.save.assert_called_once()
    
    def test_execute_strategy_creates_session(
        self,
        service,
        mock_strategy_repo,
        mock_session_repo,
        mock_market_data_repo,
        mock_scoring_service,
        sample_strategy
    ):
        """测试执行策略创建会话"""
        # 设置 mock
        mock_strategy_repo.find_by_id.return_value = sample_strategy
        mock_market_data_repo.get_all_stock_codes.return_value = []
        mock_market_data_repo.get_stocks_by_codes.return_value = []
        mock_scoring_service.score_stocks.return_value = []
        
        # 执行策略
        service.execute_strategy(sample_strategy.strategy_id.value)
        
        # 验证会话被保存
        mock_session_repo.save.assert_called_once()
        
        # 获取保存的会话
        saved_session = mock_session_repo.save.call_args[0][0]
        
        # 验证会话属性
        assert isinstance(saved_session, ScreeningSession)
        assert saved_session.strategy_id == sample_strategy.strategy_id
        assert saved_session.strategy_name == sample_strategy.name
    
    def test_execute_strategy_with_empty_stocks(
        self,
        service,
        mock_strategy_repo,
        mock_session_repo,
        mock_market_data_repo,
        mock_scoring_service,
        sample_strategy
    ):
        """测试执行策略时没有候选股票"""
        # 设置 mock：策略存在，但没有股票
        mock_strategy_repo.find_by_id.return_value = sample_strategy
        mock_market_data_repo.get_all_stock_codes.return_value = []
        mock_market_data_repo.get_stocks_by_codes.return_value = []
        mock_scoring_service.score_stocks.return_value = []
        
        # 执行策略
        result = service.execute_strategy(sample_strategy.strategy_id.value)
        
        # 验证结果
        assert result is not None
        assert result.total_scanned == 0
        assert len(result.matched_stocks) == 0


class TestScreeningStrategyServiceIntegration:
    """ScreeningStrategyService 集成测试（使用真实领域对象）"""
    
    @pytest.fixture
    def mock_strategy_repo(self):
        """创建 Mock 策略仓储"""
        repo = Mock()
        repo.save = Mock()
        repo.find_by_id = Mock(return_value=None)
        repo.find_by_name = Mock(return_value=None)
        repo.find_all = Mock(return_value=[])
        repo.delete = Mock()
        repo.exists = Mock(return_value=False)
        return repo
    
    @pytest.fixture
    def mock_session_repo(self):
        """创建 Mock 会话仓储"""
        repo = Mock()
        repo.save = Mock()
        return repo
    
    @pytest.fixture
    def mock_market_data_repo(self):
        """创建 Mock 市场数据仓储"""
        repo = Mock()
        repo.get_all_stock_codes = Mock(return_value=[])
        repo.get_stocks_by_codes = Mock(return_value=[])
        return repo
    
    @pytest.fixture
    def mock_scoring_service(self):
        """创建 Mock 评分服务"""
        service = Mock()
        service.score_stocks = Mock(return_value=[])
        return service
    
    @pytest.fixture
    def mock_calc_service(self):
        """创建 Mock 指标计算服务"""
        service = Mock()
        service.calculate_indicator = Mock(return_value=0.0)
        return service
    
    @pytest.fixture
    def service(
        self,
        mock_strategy_repo,
        mock_session_repo,
        mock_market_data_repo,
        mock_scoring_service,
        mock_calc_service
    ):
        """创建 ScreeningStrategyService 实例"""
        return ScreeningStrategyService(
            strategy_repo=mock_strategy_repo,
            session_repo=mock_session_repo,
            market_data_repo=mock_market_data_repo,
            scoring_service=mock_scoring_service,
            calc_service=mock_calc_service
        )
    
    def test_create_and_get_strategy(
        self,
        service,
        mock_strategy_repo
    ):
        """测试创建策略后能够获取"""
        # 创建策略
        filters_dict = {
            'group_id': str(uuid.uuid4()),
            'operator': 'AND',
            'conditions': [
                {
                    'field': 'ROE',
                    'operator': '>',
                    'value': {'type': 'numeric', 'value': 0.15, 'unit': None}
                }
            ],
            'sub_groups': []
        }
        
        scoring_config_dict = {
            'weights': {'ROE': 1.0},
            'normalization_method': 'min_max'
        }
        
        created = service.create_strategy(
            name="集成测试策略",
            filters_dict=filters_dict,
            scoring_config_dict=scoring_config_dict,
            description="集成测试描述",
            tags=["集成测试"]
        )
        
        # 设置 mock 返回创建的策略
        mock_strategy_repo.find_by_id.return_value = created
        
        # 获取策略
        retrieved = service.get_strategy(created.strategy_id.value)
        
        # 验证
        assert retrieved is not None
        assert retrieved.strategy_id == created.strategy_id
        assert retrieved.name == "集成测试策略"
        assert retrieved.description == "集成测试描述"
        assert retrieved.tags == ["集成测试"]

