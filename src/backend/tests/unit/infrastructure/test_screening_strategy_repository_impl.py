"""
ScreeningStrategyRepositoryImpl 单元测试

测试 Repository 实现的 PO ↔ 领域对象映射逻辑。
使用 Mock 模拟 SQLAlchemy session 以隔离数据库依赖。

Requirements:
- 6.2: 实现 ScreeningStrategyRepository，在 ScreeningStrategy 领域对象和 PO 模型之间进行映射
- 6.7: 保存 ScreeningStrategy 后按 ID 检索时，返回等价的领域对象，包含所有嵌套的 FilterGroup
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
import uuid

from contexts.screening.infrastructure.persistence.repositories.screening_strategy_repository_impl import (
    ScreeningStrategyRepositoryImpl
)
from contexts.screening.infrastructure.persistence.models.screening_strategy_po import (
    ScreeningStrategyPO
)
from contexts.screening.domain.models.screening_strategy import ScreeningStrategy
from contexts.screening.domain.models.filter_group import FilterGroup
from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
from contexts.screening.domain.value_objects.identifiers import StrategyId
from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import NumericValue
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from contexts.screening.domain.enums.enums import LogicalOperator, NormalizationMethod


class TestScreeningStrategyRepositoryImpl:
    """ScreeningStrategyRepositoryImpl 单元测试"""
    
    @pytest.fixture
    def mock_session(self):
        """创建 Mock SQLAlchemy session"""
        session = Mock()
        session.query = Mock(return_value=Mock())
        session.merge = Mock()
        session.flush = Mock()
        session.delete = Mock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        """创建 Repository 实例"""
        return ScreeningStrategyRepositoryImpl(mock_session)
    
    @pytest.fixture
    def sample_strategy(self):
        """创建示例 ScreeningStrategy 领域对象"""
        strategy_id = StrategyId.generate()
        
        # 创建筛选条件
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        # 创建筛选条件组
        filters = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition],
            sub_groups=[]
        )
        
        # 创建评分配置
        scoring_config = ScoringConfig(
            weights={IndicatorField.ROE: 0.5, IndicatorField.PE: 0.5},
            normalization_method=NormalizationMethod.MIN_MAX
        )
        
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
    
    @pytest.fixture
    def sample_po(self, sample_strategy):
        """创建示例 ScreeningStrategyPO 持久化对象"""
        po = Mock(spec=ScreeningStrategyPO)
        po.id = sample_strategy.strategy_id.value
        po.name = sample_strategy.name
        po.description = sample_strategy.description
        po.filters = sample_strategy.filters.to_dict()
        po.scoring_config = sample_strategy.scoring_config.to_dict()
        po.tags = sample_strategy.tags
        po.is_template = sample_strategy.is_template
        po.created_at = sample_strategy.created_at
        po.updated_at = sample_strategy.updated_at
        return po
    
    # ==================== save 方法测试 ====================
    
    def test_save_calls_merge_and_flush(self, repository, mock_session, sample_strategy):
        """测试 save 方法调用 merge 和 flush"""
        repository.save(sample_strategy)
        
        # 验证 merge 被调用
        mock_session.merge.assert_called_once()
        
        # 验证 flush 被调用
        mock_session.flush.assert_called_once()
    
    def test_save_converts_domain_to_po(self, repository, mock_session, sample_strategy):
        """测试 save 方法正确转换领域对象为 PO"""
        repository.save(sample_strategy)
        
        # 获取传递给 merge 的 PO 对象
        call_args = mock_session.merge.call_args
        po = call_args[0][0]
        
        # 验证 PO 属性
        assert po.id == sample_strategy.strategy_id.value
        assert po.name == sample_strategy.name
        assert po.description == sample_strategy.description
        assert po.filters == sample_strategy.filters.to_dict()
        assert po.scoring_config == sample_strategy.scoring_config.to_dict()
        assert po.tags == sample_strategy.tags
        assert po.is_template == sample_strategy.is_template
        assert po.created_at == sample_strategy.created_at
        assert po.updated_at == sample_strategy.updated_at
    
    # ==================== find_by_id 方法测试 ====================
    
    def test_find_by_id_returns_domain_object_when_found(
        self, repository, mock_session, sample_strategy, sample_po
    ):
        """测试 find_by_id 找到记录时返回领域对象"""
        # 设置 mock 返回 PO
        mock_query = Mock()
        mock_query.get = Mock(return_value=sample_po)
        mock_session.query.return_value = mock_query
        
        # 执行查询
        result = repository.find_by_id(sample_strategy.strategy_id)
        
        # 验证返回的领域对象
        assert result is not None
        assert result.strategy_id == sample_strategy.strategy_id
        assert result.name == sample_strategy.name
        assert result.description == sample_strategy.description
        assert result.is_template == sample_strategy.is_template
    
    def test_find_by_id_returns_none_when_not_found(
        self, repository, mock_session
    ):
        """测试 find_by_id 未找到记录时返回 None"""
        # 设置 mock 返回 None
        mock_query = Mock()
        mock_query.get = Mock(return_value=None)
        mock_session.query.return_value = mock_query
        
        # 执行查询
        strategy_id = StrategyId.generate()
        result = repository.find_by_id(strategy_id)
        
        # 验证返回 None
        assert result is None
    
    # ==================== find_by_name 方法测试 ====================
    
    def test_find_by_name_returns_domain_object_when_found(
        self, repository, mock_session, sample_strategy, sample_po
    ):
        """测试 find_by_name 找到记录时返回领域对象"""
        # 设置 mock 返回 PO
        mock_query = Mock()
        mock_query.filter_by = Mock(return_value=Mock(first=Mock(return_value=sample_po)))
        mock_session.query.return_value = mock_query
        
        # 执行查询
        result = repository.find_by_name(sample_strategy.name)
        
        # 验证返回的领域对象
        assert result is not None
        assert result.name == sample_strategy.name
    
    def test_find_by_name_returns_none_when_not_found(
        self, repository, mock_session
    ):
        """测试 find_by_name 未找到记录时返回 None"""
        # 设置 mock 返回 None
        mock_query = Mock()
        mock_query.filter_by = Mock(return_value=Mock(first=Mock(return_value=None)))
        mock_session.query.return_value = mock_query
        
        # 执行查询
        result = repository.find_by_name("不存在的策略")
        
        # 验证返回 None
        assert result is None
    
    # ==================== find_all 方法测试 ====================
    
    def test_find_all_returns_list_of_domain_objects(
        self, repository, mock_session, sample_po
    ):
        """测试 find_all 返回领域对象列表"""
        # 创建多个 PO
        po_list = [sample_po]
        
        # 设置 mock 返回 PO 列表
        mock_query = Mock()
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=po_list)
        mock_session.query.return_value = mock_query
        
        # 执行查询
        result = repository.find_all(limit=10, offset=0)
        
        # 验证返回列表
        assert len(result) == 1
        assert result[0].name == sample_po.name
    
    def test_find_all_returns_empty_list_when_no_records(
        self, repository, mock_session
    ):
        """测试 find_all 无记录时返回空列表"""
        # 设置 mock 返回空列表
        mock_query = Mock()
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_session.query.return_value = mock_query
        
        # 执行查询
        result = repository.find_all()
        
        # 验证返回空列表
        assert result == []
    
    def test_find_all_applies_pagination(self, repository, mock_session):
        """测试 find_all 正确应用分页参数"""
        # 设置 mock
        mock_query = Mock()
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_session.query.return_value = mock_query
        
        # 执行查询
        repository.find_all(limit=50, offset=10)
        
        # 验证分页参数
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(50)
    
    # ==================== delete 方法测试 ====================
    
    def test_delete_removes_existing_record(
        self, repository, mock_session, sample_po
    ):
        """测试 delete 删除存在的记录"""
        # 设置 mock 返回 PO
        mock_query = Mock()
        mock_query.get = Mock(return_value=sample_po)
        mock_session.query.return_value = mock_query
        
        # 执行删除
        strategy_id = StrategyId.from_string(sample_po.id)
        repository.delete(strategy_id)
        
        # 验证 delete 和 flush 被调用
        mock_session.delete.assert_called_once_with(sample_po)
        mock_session.flush.assert_called_once()
    
    def test_delete_does_nothing_when_not_found(
        self, repository, mock_session
    ):
        """测试 delete 记录不存在时静默处理"""
        # 设置 mock 返回 None
        mock_query = Mock()
        mock_query.get = Mock(return_value=None)
        mock_session.query.return_value = mock_query
        
        # 执行删除
        strategy_id = StrategyId.generate()
        repository.delete(strategy_id)
        
        # 验证 delete 未被调用
        mock_session.delete.assert_not_called()
    
    # ==================== exists 方法测试 ====================
    
    def test_exists_returns_true_when_found(self, repository, mock_session):
        """测试 exists 记录存在时返回 True"""
        # 设置 mock 返回 count > 0
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=1)
        mock_session.query.return_value = mock_query
        
        # 执行检查
        strategy_id = StrategyId.generate()
        result = repository.exists(strategy_id)
        
        # 验证返回 True
        assert result is True
    
    def test_exists_returns_false_when_not_found(self, repository, mock_session):
        """测试 exists 记录不存在时返回 False"""
        # 设置 mock 返回 count = 0
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=0)
        mock_session.query.return_value = mock_query
        
        # 执行检查
        strategy_id = StrategyId.generate()
        result = repository.exists(strategy_id)
        
        # 验证返回 False
        assert result is False
    
    # ==================== count 方法测试 ====================
    
    def test_count_returns_total_records(self, repository, mock_session):
        """测试 count 返回记录总数"""
        # 设置 mock 返回 count
        mock_query = Mock()
        mock_query.count = Mock(return_value=5)
        mock_session.query.return_value = mock_query
        
        # 执行计数
        result = repository.count()
        
        # 验证返回值
        assert result == 5
    
    # ==================== 映射测试 ====================
    
    def test_to_domain_preserves_nested_filter_group(
        self, repository, mock_session
    ):
        """测试 _to_domain 保留嵌套的 FilterGroup 结构"""
        # 创建嵌套的 FilterGroup 结构
        nested_filters = {
            'group_id': str(uuid.uuid4()),
            'operator': 'AND',
            'conditions': [
                {
                    'field': 'ROE',
                    'operator': '>',
                    'value': {'type': 'numeric', 'value': 0.15, 'unit': None}
                }
            ],
            'sub_groups': [
                {
                    'group_id': str(uuid.uuid4()),
                    'operator': 'OR',
                    'conditions': [
                        {
                            'field': 'PE',
                            'operator': '<',
                            'value': {'type': 'numeric', 'value': 20.0, 'unit': None}
                        },
                        {
                            'field': 'PB',
                            'operator': '<',
                            'value': {'type': 'numeric', 'value': 3.0, 'unit': None}
                        }
                    ],
                    'sub_groups': []
                }
            ]
        }
        
        scoring_config = {
            'weights': {'ROE': 1.0},
            'normalization_method': 'min_max'
        }
        
        # 创建 PO
        po = Mock(spec=ScreeningStrategyPO)
        po.id = str(uuid.uuid4())
        po.name = "嵌套测试策略"
        po.description = None
        po.filters = nested_filters
        po.scoring_config = scoring_config
        po.tags = []
        po.is_template = False
        po.created_at = datetime.now(timezone.utc)
        po.updated_at = datetime.now(timezone.utc)
        
        # 设置 mock 返回 PO
        mock_query = Mock()
        mock_query.get = Mock(return_value=po)
        mock_session.query.return_value = mock_query
        
        # 执行查询
        strategy_id = StrategyId.from_string(po.id)
        result = repository.find_by_id(strategy_id)
        
        # 验证嵌套结构被正确还原
        assert result is not None
        assert result.filters.operator == LogicalOperator.AND
        assert len(result.filters.conditions) == 1
        assert len(result.filters.sub_groups) == 1
        
        # 验证子组
        sub_group = result.filters.sub_groups[0]
        assert sub_group.operator == LogicalOperator.OR
        assert len(sub_group.conditions) == 2
    
    def test_to_domain_handles_empty_tags(self, repository, mock_session):
        """测试 _to_domain 处理空 tags"""
        # 创建 PO，tags 为 None
        po = Mock(spec=ScreeningStrategyPO)
        po.id = str(uuid.uuid4())
        po.name = "空标签测试"
        po.description = None
        po.filters = {
            'group_id': str(uuid.uuid4()),
            'operator': 'AND',
            'conditions': [
                {
                    'field': 'ROE',
                    'operator': '>',
                    'value': {'type': 'numeric', 'value': 0.1, 'unit': None}
                }
            ],
            'sub_groups': []
        }
        po.scoring_config = {
            'weights': {'ROE': 1.0},
            'normalization_method': 'min_max'
        }
        po.tags = None  # 空 tags
        po.is_template = False
        po.created_at = datetime.now(timezone.utc)
        po.updated_at = datetime.now(timezone.utc)
        
        # 设置 mock 返回 PO
        mock_query = Mock()
        mock_query.get = Mock(return_value=po)
        mock_session.query.return_value = mock_query
        
        # 执行查询
        strategy_id = StrategyId.from_string(po.id)
        result = repository.find_by_id(strategy_id)
        
        # 验证 tags 为空列表
        assert result is not None
        assert result.tags == []
