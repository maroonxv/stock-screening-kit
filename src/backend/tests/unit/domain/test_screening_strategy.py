"""
ScreeningStrategy 聚合根单元测试

测试 ScreeningStrategy 的核心功能：
- 构造和属性访问
- 验证：名称非空、filters 包含至少一个条件
- execute() 方法：过滤 → 评分 → 排序 → 返回 ScreeningResult
- 修改方法
- 序列化 to_dict() / from_dict()

Requirements:
- 2.1: ScreeningStrategy 聚合根包含所有属性
- 2.6: 空名称创建时抛出验证错误
- 2.7: 不包含任何条件的 filters 创建时抛出验证错误
- 5.6: execute() 返回按 score 降序排列的结果
"""
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from contexts.screening.domain.models.screening_strategy import ScreeningStrategy
from contexts.screening.domain.models.filter_group import FilterGroup
from contexts.screening.domain.value_objects.identifiers import StrategyId
from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
from contexts.screening.domain.value_objects.screening_result import ScreeningResult
from contexts.screening.domain.value_objects.scored_stock import ScoredStock
from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import NumericValue
from contexts.screening.domain.enums.enums import LogicalOperator, NormalizationMethod
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from shared_kernel.value_objects.stock_code import StockCode


# ==================== 测试辅助函数 ====================

def create_valid_filter_group():
    """创建一个有效的 FilterGroup（包含至少一个条件）"""
    condition = FilterCondition(
        field=IndicatorField.ROE,
        operator=ComparisonOperator.GREATER_THAN,
        value=NumericValue(0.15)
    )
    return FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[condition]
    )


def create_empty_filter_group():
    """创建一个空的 FilterGroup（不包含任何条件）"""
    return FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[],
        sub_groups=[]
    )


def create_valid_scoring_config():
    """创建一个有效的 ScoringConfig"""
    return ScoringConfig(
        weights={IndicatorField.ROE: 0.5, IndicatorField.PE: 0.5},
        normalization_method=NormalizationMethod.MIN_MAX
    )


def create_mock_stock(stock_code_str: str, stock_name: str, roe: float = 0.2, pe: float = 15.0):
    """创建模拟的股票实体"""
    stock = Mock()
    stock.stock_code = StockCode(stock_code_str)
    stock.stock_name = stock_name
    stock.roe = roe
    stock.pe = pe
    return stock


def create_mock_calc_service(indicator_values: dict = None):
    """创建模拟的指标计算服务"""
    calc_service = Mock()
    if indicator_values:
        calc_service.calculate_indicator = Mock(
            side_effect=lambda field, stock: indicator_values.get(field, getattr(stock, field.name.lower(), None))
        )
    else:
        calc_service.calculate_indicator = Mock(
            side_effect=lambda field, stock: getattr(stock, field.name.lower(), None)
        )
    return calc_service


def create_mock_scoring_service(scored_stocks: list = None):
    """创建模拟的评分服务"""
    scoring_service = Mock()
    if scored_stocks is not None:
        scoring_service.score_stocks = Mock(return_value=scored_stocks)
    else:
        # 默认行为：为每个股票创建一个 ScoredStock
        def default_score_stocks(stocks, scoring_config, calc_service):
            result = []
            for i, stock in enumerate(stocks):
                scored = ScoredStock(
                    stock_code=stock.stock_code,
                    stock_name=stock.stock_name,
                    score=float(len(stocks) - i)  # 简单的递减分数
                )
                result.append(scored)
            return result
        scoring_service.score_stocks = Mock(side_effect=default_score_stocks)
    return scoring_service


# ==================== 构造测试 ====================

class TestScreeningStrategyConstruction:
    """ScreeningStrategy 构造测试"""
    
    def test_create_with_required_params(self):
        """测试使用必需参数创建 ScreeningStrategy"""
        strategy_id = StrategyId.generate()
        name = "测试策略"
        filters = create_valid_filter_group()
        scoring_config = create_valid_scoring_config()
        
        strategy = ScreeningStrategy(
            strategy_id=strategy_id,
            name=name,
            filters=filters,
            scoring_config=scoring_config
        )
        
        assert strategy.strategy_id == strategy_id
        assert strategy.name == name
        assert strategy.filters == filters
        assert strategy.scoring_config == scoring_config
        assert strategy.description is None
        assert strategy.tags == []
        assert strategy.is_template is False
        assert strategy.created_at is not None
        assert strategy.updated_at is not None
    
    def test_create_with_all_params(self):
        """测试使用所有参数创建 ScreeningStrategy"""
        strategy_id = StrategyId.generate()
        name = "完整策略"
        filters = create_valid_filter_group()
        scoring_config = create_valid_scoring_config()
        description = "这是一个完整的测试策略"
        tags = ["价值投资", "高ROE"]
        is_template = True
        created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        updated_at = datetime(2024, 1, 2, tzinfo=timezone.utc)
        
        strategy = ScreeningStrategy(
            strategy_id=strategy_id,
            name=name,
            filters=filters,
            scoring_config=scoring_config,
            description=description,
            tags=tags,
            is_template=is_template,
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert strategy.strategy_id == strategy_id
        assert strategy.name == name
        assert strategy.description == description
        assert strategy.tags == tags
        assert strategy.is_template is True
        assert strategy.created_at == created_at
        assert strategy.updated_at == updated_at
    
    def test_name_is_stripped(self):
        """测试名称会被去除首尾空格"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="  带空格的名称  ",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        assert strategy.name == "带空格的名称"
    
    def test_tags_property_returns_copy(self):
        """测试 tags 属性返回副本"""
        tags = ["tag1", "tag2"]
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config(),
            tags=tags
        )
        
        # 修改返回的列表不应影响原始数据
        returned_tags = strategy.tags
        returned_tags.append("tag3")
        
        assert len(strategy.tags) == 2


# ==================== 验证测试 ====================

class TestScreeningStrategyValidation:
    """ScreeningStrategy 验证测试"""
    
    def test_empty_name_raises_error(self):
        """测试空名称抛出 ValueError - Requirements 2.6"""
        with pytest.raises(ValueError) as exc_info:
            ScreeningStrategy(
                strategy_id=StrategyId.generate(),
                name="",
                filters=create_valid_filter_group(),
                scoring_config=create_valid_scoring_config()
            )
        
        assert "策略名称不能为空" in str(exc_info.value)
    
    def test_whitespace_only_name_raises_error(self):
        """测试仅包含空格的名称抛出 ValueError - Requirements 2.6"""
        with pytest.raises(ValueError) as exc_info:
            ScreeningStrategy(
                strategy_id=StrategyId.generate(),
                name="   ",
                filters=create_valid_filter_group(),
                scoring_config=create_valid_scoring_config()
            )
        
        assert "策略名称不能为空" in str(exc_info.value)
    
    def test_none_name_raises_error(self):
        """测试 None 名称抛出 ValueError - Requirements 2.6"""
        with pytest.raises(ValueError) as exc_info:
            ScreeningStrategy(
                strategy_id=StrategyId.generate(),
                name=None,
                filters=create_valid_filter_group(),
                scoring_config=create_valid_scoring_config()
            )
        
        assert "策略名称不能为空" in str(exc_info.value)
    
    def test_empty_filters_raises_error(self):
        """测试空筛选条件抛出 ValueError - Requirements 2.7"""
        with pytest.raises(ValueError) as exc_info:
            ScreeningStrategy(
                strategy_id=StrategyId.generate(),
                name="测试策略",
                filters=create_empty_filter_group(),
                scoring_config=create_valid_scoring_config()
            )
        
        assert "筛选条件不能为空" in str(exc_info.value)
    
    def test_nested_empty_filters_raises_error(self):
        """测试嵌套空筛选条件抛出 ValueError - Requirements 2.7"""
        # 创建一个嵌套但仍然为空的 FilterGroup
        empty_child = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[],
            sub_groups=[]
        )
        empty_parent = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR,
            conditions=[],
            sub_groups=[empty_child]
        )
        
        with pytest.raises(ValueError) as exc_info:
            ScreeningStrategy(
                strategy_id=StrategyId.generate(),
                name="测试策略",
                filters=empty_parent,
                scoring_config=create_valid_scoring_config()
            )
        
        assert "筛选条件不能为空" in str(exc_info.value)


# ==================== execute() 方法测试 ====================

class TestScreeningStrategyExecute:
    """ScreeningStrategy.execute() 方法测试"""
    
    def test_execute_returns_screening_result(self):
        """测试 execute() 返回 ScreeningResult"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        stocks = [
            create_mock_stock("600000.SH", "浦发银行", roe=0.20, pe=10.0),
            create_mock_stock("600001.SH", "测试股票", roe=0.25, pe=15.0)
        ]
        
        calc_service = create_mock_calc_service()
        scoring_service = create_mock_scoring_service()
        
        result = strategy.execute(stocks, scoring_service, calc_service)
        
        assert isinstance(result, ScreeningResult)
        assert result.total_scanned == 2
        assert result.execution_time >= 0
    
    def test_execute_filters_stocks(self):
        """测试 execute() 正确过滤股票"""
        # 创建一个 ROE > 0.15 的筛选条件
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        filters = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition]
        )
        
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="高ROE策略",
            filters=filters,
            scoring_config=create_valid_scoring_config()
        )
        
        # 创建股票：一个满足条件，一个不满足
        stock1 = create_mock_stock("600000.SH", "高ROE股票", roe=0.20, pe=10.0)
        stock2 = create_mock_stock("600001.SH", "低ROE股票", roe=0.10, pe=15.0)
        stocks = [stock1, stock2]
        
        calc_service = create_mock_calc_service()
        scoring_service = create_mock_scoring_service()
        
        result = strategy.execute(stocks, scoring_service, calc_service)
        
        # 验证只有满足条件的股票被传递给评分服务
        scoring_service.score_stocks.assert_called_once()
        scored_stocks = scoring_service.score_stocks.call_args[0][0]
        assert len(scored_stocks) == 1
        assert scored_stocks[0].stock_code.code == "600000.SH"
    
    def test_execute_results_sorted_by_score_descending(self):
        """测试 execute() 结果按 score 降序排列 - Requirements 5.6"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        stocks = [
            create_mock_stock("600000.SH", "股票A", roe=0.20, pe=10.0),
            create_mock_stock("600001.SH", "股票B", roe=0.25, pe=15.0),
            create_mock_stock("600002.SH", "股票C", roe=0.30, pe=20.0)
        ]
        
        # 创建带有不同分数的 ScoredStock（故意乱序）
        scored_stocks = [
            ScoredStock(stock_code=StockCode("600000.SH"), stock_name="股票A", score=50.0),
            ScoredStock(stock_code=StockCode("600001.SH"), stock_name="股票B", score=80.0),
            ScoredStock(stock_code=StockCode("600002.SH"), stock_name="股票C", score=30.0)
        ]
        
        calc_service = create_mock_calc_service()
        scoring_service = create_mock_scoring_service(scored_stocks)
        
        result = strategy.execute(stocks, scoring_service, calc_service)
        
        # 验证结果按 score 降序排列
        assert len(result.matched_stocks) == 3
        assert result.matched_stocks[0].score == 80.0  # 最高分
        assert result.matched_stocks[1].score == 50.0
        assert result.matched_stocks[2].score == 30.0  # 最低分
    
    def test_execute_with_empty_candidate_stocks(self):
        """测试 execute() 处理空候选股票列表"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        calc_service = create_mock_calc_service()
        scoring_service = create_mock_scoring_service([])
        
        result = strategy.execute([], scoring_service, calc_service)
        
        assert result.total_scanned == 0
        assert len(result.matched_stocks) == 0
    
    def test_execute_records_execution_time(self):
        """测试 execute() 记录执行时间"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        stocks = [create_mock_stock("600000.SH", "测试股票", roe=0.20, pe=10.0)]
        calc_service = create_mock_calc_service()
        scoring_service = create_mock_scoring_service()
        
        result = strategy.execute(stocks, scoring_service, calc_service)
        
        assert result.execution_time >= 0
    
    def test_execute_includes_filters_and_scoring_config_in_result(self):
        """测试 execute() 结果包含 filters 和 scoring_config"""
        filters = create_valid_filter_group()
        scoring_config = create_valid_scoring_config()
        
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=filters,
            scoring_config=scoring_config
        )
        
        stocks = [create_mock_stock("600000.SH", "测试股票", roe=0.20, pe=10.0)]
        calc_service = create_mock_calc_service()
        scoring_service = create_mock_scoring_service()
        
        result = strategy.execute(stocks, scoring_service, calc_service)
        
        assert result.filters_applied == filters
        assert result.scoring_config == scoring_config


# ==================== 修改方法测试 ====================

class TestScreeningStrategyUpdateMethods:
    """ScreeningStrategy 修改方法测试"""
    
    def test_update_name(self):
        """测试更新策略名称"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="原始名称",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        original_updated_at = strategy.updated_at
        
        strategy.update_name("新名称")
        
        assert strategy.name == "新名称"
        assert strategy.updated_at > original_updated_at
    
    def test_update_name_with_empty_raises_error(self):
        """测试更新为空名称抛出错误"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="原始名称",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        with pytest.raises(ValueError) as exc_info:
            strategy.update_name("")
        
        assert "策略名称不能为空" in str(exc_info.value)
    
    def test_update_description(self):
        """测试更新策略描述"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        original_updated_at = strategy.updated_at
        
        strategy.update_description("新描述")
        
        assert strategy.description == "新描述"
        assert strategy.updated_at > original_updated_at
    
    def test_update_filters(self):
        """测试更新筛选条件"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        original_updated_at = strategy.updated_at
        
        new_condition = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(20.0)
        )
        new_filters = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[new_condition]
        )
        
        strategy.update_filters(new_filters)
        
        assert strategy.filters == new_filters
        assert strategy.updated_at > original_updated_at
    
    def test_update_filters_with_empty_raises_error(self):
        """测试更新为空筛选条件抛出错误"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        with pytest.raises(ValueError) as exc_info:
            strategy.update_filters(create_empty_filter_group())
        
        assert "筛选条件不能为空" in str(exc_info.value)
    
    def test_update_scoring_config(self):
        """测试更新评分配置"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        original_updated_at = strategy.updated_at
        
        new_scoring_config = ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.Z_SCORE
        )
        
        strategy.update_scoring_config(new_scoring_config)
        
        assert strategy.scoring_config == new_scoring_config
        assert strategy.updated_at > original_updated_at
    
    def test_update_tags(self):
        """测试更新标签"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config(),
            tags=["原始标签"]
        )
        original_updated_at = strategy.updated_at
        
        strategy.update_tags(["新标签1", "新标签2"])
        
        assert strategy.tags == ["新标签1", "新标签2"]
        assert strategy.updated_at > original_updated_at
    
    def test_set_as_template(self):
        """测试设置为模板"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config(),
            is_template=False
        )
        original_updated_at = strategy.updated_at
        
        strategy.set_as_template(True)
        
        assert strategy.is_template is True
        assert strategy.updated_at > original_updated_at


# ==================== 序列化测试 ====================

class TestScreeningStrategySerialization:
    """ScreeningStrategy 序列化测试"""
    
    def test_to_dict(self):
        """测试序列化为字典"""
        strategy_id = StrategyId.generate()
        filters = create_valid_filter_group()
        scoring_config = create_valid_scoring_config()
        created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        updated_at = datetime(2024, 1, 2, tzinfo=timezone.utc)
        
        strategy = ScreeningStrategy(
            strategy_id=strategy_id,
            name="测试策略",
            filters=filters,
            scoring_config=scoring_config,
            description="测试描述",
            tags=["tag1", "tag2"],
            is_template=True,
            created_at=created_at,
            updated_at=updated_at
        )
        
        result = strategy.to_dict()
        
        assert result['strategy_id'] == strategy_id.value
        assert result['name'] == "测试策略"
        assert result['description'] == "测试描述"
        assert result['tags'] == ["tag1", "tag2"]
        assert result['is_template'] is True
        assert 'filters' in result
        assert 'scoring_config' in result
        assert result['created_at'] == created_at.isoformat()
        assert result['updated_at'] == updated_at.isoformat()
    
    def test_from_dict(self):
        """测试从字典反序列化"""
        strategy_id = str(uuid.uuid4())
        data = {
            'strategy_id': strategy_id,
            'name': '测试策略',
            'description': '测试描述',
            'filters': {
                'group_id': str(uuid.uuid4()),
                'operator': 'AND',
                'conditions': [
                    {
                        'field': 'ROE',
                        'operator': '>',
                        'value': {'type': 'numeric', 'value': 0.15}
                    }
                ],
                'sub_groups': []
            },
            'scoring_config': {
                'weights': {'ROE': 0.5, 'PE': 0.5},
                'normalization_method': 'min_max'
            },
            'tags': ['tag1', 'tag2'],
            'is_template': True,
            'created_at': '2024-01-01T00:00:00+00:00',
            'updated_at': '2024-01-02T00:00:00+00:00'
        }
        
        strategy = ScreeningStrategy.from_dict(data)
        
        assert strategy.strategy_id.value == strategy_id
        assert strategy.name == '测试策略'
        assert strategy.description == '测试描述'
        assert strategy.tags == ['tag1', 'tag2']
        assert strategy.is_template is True
        assert strategy.filters is not None
        assert strategy.scoring_config is not None
    
    def test_serialization_round_trip(self):
        """测试序列化往返"""
        original = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config(),
            description="测试描述",
            tags=["tag1", "tag2"],
            is_template=True
        )
        
        # 序列化然后反序列化
        data = original.to_dict()
        restored = ScreeningStrategy.from_dict(data)
        
        # 验证关键属性相等
        assert restored.strategy_id == original.strategy_id
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.tags == original.tags
        assert restored.is_template == original.is_template


# ==================== 相等性测试 ====================

class TestScreeningStrategyEquality:
    """ScreeningStrategy 相等性测试"""
    
    def test_equal_strategies(self):
        """测试相等的策略"""
        strategy_id = StrategyId.generate()
        
        strategy1 = ScreeningStrategy(
            strategy_id=strategy_id,
            name="策略1",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        strategy2 = ScreeningStrategy(
            strategy_id=strategy_id,
            name="策略2",  # 名称不同但 ID 相同
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        # 基于 strategy_id 判断相等
        assert strategy1 == strategy2
    
    def test_not_equal_different_ids(self):
        """测试不同 ID 的策略不相等"""
        strategy1 = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="相同名称",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        strategy2 = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="相同名称",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        assert strategy1 != strategy2
    
    def test_not_equal_to_non_strategy(self):
        """测试与非 ScreeningStrategy 对象不相等"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        assert strategy != "not a strategy"
        assert strategy != 123
        assert strategy != None
    
    def test_hash_consistency(self):
        """测试哈希一致性"""
        strategy_id = StrategyId.generate()
        
        strategy1 = ScreeningStrategy(
            strategy_id=strategy_id,
            name="策略1",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        strategy2 = ScreeningStrategy(
            strategy_id=strategy_id,
            name="策略2",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config()
        )
        
        # 相等的对象应该有相同的哈希值
        assert hash(strategy1) == hash(strategy2)


# ==================== __repr__ 测试 ====================

class TestScreeningStrategyRepr:
    """ScreeningStrategy __repr__ 测试"""
    
    def test_repr(self):
        """测试字符串表示"""
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name="测试策略",
            filters=create_valid_filter_group(),
            scoring_config=create_valid_scoring_config(),
            is_template=True
        )
        
        repr_str = repr(strategy)
        
        assert "ScreeningStrategy" in repr_str
        assert "测试策略" in repr_str
        assert "is_template=True" in repr_str
