"""
Property-based tests for ScreeningStrategy.execute result ordering

Feature: stock-screening-platform
Property 10: ScreeningStrategy.execute 结果有序性

**Validates: Requirements 5.6**

Property Description:
对于任意 ScreeningStrategy 和候选股票列表，execute() 返回的 ScreeningResult 中的 
matched_stocks 应按 score 降序排列，且所有 matched_stocks 中的股票都应满足策略的筛选条件。

Requirements:
- 5.6: execute() 返回按 score 降序排列的结果
"""
import uuid
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
from typing import List, Dict, Any, Optional

from contexts.screening.domain.models.screening_strategy import ScreeningStrategy
from contexts.screening.domain.models.filter_group import FilterGroup
from contexts.screening.domain.models.stock import Stock
from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import NumericValue, RangeValue
from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
from contexts.screening.domain.value_objects.scored_stock import ScoredStock
from contexts.screening.domain.value_objects.identifiers import StrategyId
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from contexts.screening.domain.enums.enums import LogicalOperator, ValueType, NormalizationMethod
from shared_kernel.value_objects.stock_code import StockCode


# =============================================================================
# 分类指标字段
# =============================================================================

NUMERIC_FIELDS = [f for f in IndicatorField if f.value_type == ValueType.NUMERIC]
TEXT_FIELDS = [f for f in IndicatorField if f.value_type == ValueType.TEXT]


# =============================================================================
# Mock Services
# =============================================================================

class MockCalcService:
    """
    模拟的指标计算服务
    
    通过预设的结果映射来控制指标计算结果。
    """
    def __init__(self, indicator_values: Dict[IndicatorField, Dict[str, Any]]):
        """
        Args:
            indicator_values: IndicatorField -> {stock_code: value} 的映射
        """
        self._indicator_values = indicator_values
    
    def calculate_indicator(self, field: IndicatorField, stock: Stock) -> Any:
        """返回预设的指标值"""
        field_values = self._indicator_values.get(field, {})
        return field_values.get(stock.stock_code.code)


class MockScoringService:
    """
    模拟的评分服务
    
    根据预设的分数映射返回评分结果。
    """
    def __init__(self, scores: Dict[str, float]):
        """
        Args:
            scores: stock_code -> score 的映射
        """
        self._scores = scores
    
    def score_stocks(
        self, 
        stocks: List[Stock], 
        scoring_config: ScoringConfig,
        calc_service: Any
    ) -> List[ScoredStock]:
        """返回带评分的股票列表"""
        scored_stocks = []
        for stock in stocks:
            score = self._scores.get(stock.stock_code.code, 0.0)
            scored_stock = ScoredStock(
                stock_code=stock.stock_code,
                stock_name=stock.stock_name,
                score=score,
                score_breakdown={},
                indicator_values={},
                matched_conditions=[]
            )
            scored_stocks.append(scored_stock)
        return scored_stocks


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@composite
def valid_stock_code_strategy(draw):
    """生成有效的股票代码"""
    numeric_part = draw(st.from_regex(r'\d{6}', fullmatch=True))
    exchange = draw(st.sampled_from(['SH', 'SZ']))
    return f"{numeric_part}.{exchange}"


@composite
def stock_strategy(draw, stock_code: Optional[str] = None):
    """生成股票实体"""
    if stock_code is None:
        stock_code = draw(valid_stock_code_strategy())
    
    stock_name = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(
        whitelist_categories=('L',), whitelist_characters='股份有限公司'
    )))
    
    # 生成财务指标
    roe = draw(st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False))
    pe = draw(st.floats(min_value=0.1, max_value=200.0, allow_nan=False, allow_infinity=False))
    pb = draw(st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False))
    
    return Stock(
        stock_code=StockCode(stock_code),
        stock_name=stock_name if stock_name.strip() else "测试股票",
        roe=roe,
        pe=pe,
        pb=pb
    )


@composite
def stocks_with_scores_strategy(draw, min_stocks: int = 1, max_stocks: int = 10):
    """
    生成股票列表和对应的分数映射
    
    Returns:
        Tuple[List[Stock], Dict[str, float]]: (股票列表, 分数映射)
    """
    num_stocks = draw(st.integers(min_value=min_stocks, max_value=max_stocks))
    
    stocks = []
    scores = {}
    used_codes = set()
    
    for i in range(num_stocks):
        # 生成唯一的股票代码
        while True:
            numeric_part = draw(st.from_regex(r'\d{6}', fullmatch=True))
            exchange = draw(st.sampled_from(['SH', 'SZ']))
            code = f"{numeric_part}.{exchange}"
            if code not in used_codes:
                used_codes.add(code)
                break
        
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"股票{i+1}",
            roe=draw(st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False)),
            pe=draw(st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False)),
            pb=draw(st.floats(min_value=0.5, max_value=20.0, allow_nan=False, allow_infinity=False))
        )
        stocks.append(stock)
        
        # 生成分数
        score = draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
        scores[code] = score
    
    return (stocks, scores)


@composite
def simple_filter_group_strategy(draw, threshold: Optional[float] = None):
    """
    生成简单的筛选条件组（单个条件）
    
    Args:
        threshold: 可选的阈值，如果不提供则随机生成
    """
    field = IndicatorField.ROE  # 使用 ROE 作为筛选字段
    
    if threshold is None:
        threshold = draw(st.floats(min_value=0.01, max_value=0.3, allow_nan=False, allow_infinity=False))
    
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.GREATER_THAN,
        value=NumericValue(threshold)
    )
    
    return FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[condition]
    )


@composite
def valid_scoring_config_strategy(draw):
    """生成有效的评分配置"""
    # 选择 1-3 个数值类型字段
    num_fields = draw(st.integers(min_value=1, max_value=3))
    fields = draw(st.lists(
        st.sampled_from(NUMERIC_FIELDS),
        min_size=num_fields,
        max_size=num_fields,
        unique=True
    ))
    
    if len(fields) == 1:
        weights = {fields[0]: 1.0}
    else:
        # 生成归一化的权重
        raw_weights = [draw(st.floats(min_value=0.1, max_value=1.0)) for _ in fields]
        total = sum(raw_weights)
        weights = {field: weight / total for field, weight in zip(fields, raw_weights)}
    
    return ScoringConfig(
        weights=weights,
        normalization_method=NormalizationMethod.MIN_MAX
    )


@composite
def screening_strategy_strategy(draw, filters: Optional[FilterGroup] = None):
    """生成筛选策略"""
    if filters is None:
        filters = draw(simple_filter_group_strategy())
    
    scoring_config = draw(valid_scoring_config_strategy())
    
    return ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name=f"测试策略_{uuid.uuid4().hex[:8]}",
        filters=filters,
        scoring_config=scoring_config
    )


# =============================================================================
# Property 10.1: 结果按 score 降序排列
# **Validates: Requirements 5.6**
# =============================================================================

@settings(max_examples=100)
@given(
    num_stocks=st.integers(min_value=2, max_value=10),
    scores_list=st.lists(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=10
    )
)
def test_execute_results_sorted_by_score_descending(num_stocks, scores_list):
    """
    Property 10.1: execute() 返回的结果按 score 降序排列
    
    **Validates: Requirements 5.6**
    
    对于任意 ScreeningStrategy 和候选股票列表，execute() 返回的 ScreeningResult 
    中的 matched_stocks 应按 score 降序排列。
    """
    # 确保分数列表长度与股票数量匹配
    actual_num = min(num_stocks, len(scores_list))
    if actual_num < 2:
        return  # 跳过无效情况
    
    # 创建股票和分数映射
    stocks = []
    scores = {}
    threshold = 0.001
    
    for i in range(actual_num):
        code = f"{600000 + i:06d}.SH"
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"股票{i+1}",
            roe=0.15  # 确保通过筛选
        )
        stocks.append(stock)
        scores[code] = scores_list[i]
    
    # 创建筛选条件
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    indicator_values = {
        IndicatorField.ROE: {stock.stock_code.code: 0.15 for stock in stocks}
    }
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(scores)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    # 验证结果按 score 降序排列
    matched_stocks = result.matched_stocks
    if len(matched_stocks) > 1:
        for i in range(len(matched_stocks) - 1):
            assert matched_stocks[i].score >= matched_stocks[i + 1].score, \
                f"结果未按 score 降序排列: {matched_stocks[i].score} < {matched_stocks[i + 1].score}"


@settings(max_examples=100)
@given(
    scores=st.lists(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=10
    )
)
def test_execute_results_sorted_with_various_scores(scores):
    """
    Property 10.1.1: 各种分数组合下结果仍按降序排列
    
    **Validates: Requirements 5.6**
    
    测试不同分数分布（包括相同分数、极端值等）下的排序正确性。
    """
    # 创建股票
    stocks = []
    score_map = {}
    for i, score in enumerate(scores):
        code = f"{600000 + i:06d}.SH"
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"股票{i+1}",
            roe=0.15  # 确保通过筛选
        )
        stocks.append(stock)
        score_map[code] = score
    
    # 创建简单的筛选条件
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.1)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    indicator_values = {
        IndicatorField.ROE: {stock.stock_code.code: 0.15 for stock in stocks}
    }
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(score_map)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    # 验证结果按 score 降序排列
    matched_stocks = result.matched_stocks
    for i in range(len(matched_stocks) - 1):
        assert matched_stocks[i].score >= matched_stocks[i + 1].score, \
            f"结果未按 score 降序排列: index {i}: {matched_stocks[i].score} < {matched_stocks[i + 1].score}"


@settings(max_examples=100)
@given(
    same_score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    num_stocks=st.integers(min_value=2, max_value=5)
)
def test_execute_results_with_equal_scores(same_score, num_stocks):
    """
    Property 10.1.2: 相同分数的股票排序稳定
    
    **Validates: Requirements 5.6**
    
    当多只股票具有相同分数时，排序应该是稳定的（不会出现错误）。
    """
    # 创建股票，所有股票具有相同分数
    stocks = []
    score_map = {}
    for i in range(num_stocks):
        code = f"{600000 + i:06d}.SH"
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"股票{i+1}",
            roe=0.15
        )
        stocks.append(stock)
        score_map[code] = same_score
    
    # 创建筛选条件
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.1)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    indicator_values = {
        IndicatorField.ROE: {stock.stock_code.code: 0.15 for stock in stocks}
    }
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(score_map)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    # 验证所有结果分数相等
    matched_stocks = result.matched_stocks
    assert len(matched_stocks) == num_stocks
    for stock in matched_stocks:
        assert stock.score == same_score


# =============================================================================
# Property 10.2: 所有匹配股票满足筛选条件
# **Validates: Requirements 5.6**
# =============================================================================

@settings(max_examples=100)
@given(st.data())
def test_all_matched_stocks_satisfy_filter_conditions(data):
    """
    Property 10.2: 所有 matched_stocks 中的股票都满足策略的筛选条件
    
    **Validates: Requirements 5.6**
    
    对于任意 ScreeningStrategy 和候选股票列表，execute() 返回的 ScreeningResult 
    中的所有 matched_stocks 都应满足策略的筛选条件。
    """
    # 生成阈值
    threshold = data.draw(st.floats(min_value=0.05, max_value=0.25, allow_nan=False, allow_infinity=False))
    
    # 创建股票，一些满足条件，一些不满足
    num_stocks = data.draw(st.integers(min_value=3, max_value=10))
    stocks = []
    indicator_values = {IndicatorField.ROE: {}}
    scores = {}
    
    for i in range(num_stocks):
        code = f"{600000 + i:06d}.SH"
        # 随机决定是否满足条件
        should_match = data.draw(st.booleans())
        if should_match:
            roe_value = threshold + data.draw(st.floats(min_value=0.01, max_value=0.2, allow_nan=False, allow_infinity=False))
        else:
            roe_value = threshold - data.draw(st.floats(min_value=0.01, max_value=threshold - 0.001, allow_nan=False, allow_infinity=False))
        
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"股票{i+1}",
            roe=roe_value
        )
        stocks.append(stock)
        indicator_values[IndicatorField.ROE][code] = roe_value
        scores[code] = data.draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    
    # 创建筛选条件: ROE > threshold
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(scores)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    # 验证所有匹配的股票都满足筛选条件
    for scored_stock in result.matched_stocks:
        stock_code = scored_stock.stock_code.code
        actual_roe = indicator_values[IndicatorField.ROE][stock_code]
        assert actual_roe > threshold, \
            f"股票 {stock_code} 的 ROE ({actual_roe}) 不满足条件 > {threshold}"


@settings(max_examples=100)
@given(st.data())
def test_non_matching_stocks_excluded_from_results(data):
    """
    Property 10.2.1: 不满足条件的股票不会出现在结果中
    
    **Validates: Requirements 5.6**
    
    对于任意 ScreeningStrategy，不满足筛选条件的股票不应出现在 matched_stocks 中。
    """
    threshold = 0.15
    
    # 创建一些满足条件和不满足条件的股票
    num_matching = data.draw(st.integers(min_value=1, max_value=5))
    num_non_matching = data.draw(st.integers(min_value=1, max_value=5))
    
    stocks = []
    indicator_values = {IndicatorField.ROE: {}}
    scores = {}
    matching_codes = set()
    non_matching_codes = set()
    
    # 创建满足条件的股票
    for i in range(num_matching):
        code = f"{600000 + i:06d}.SH"
        roe_value = threshold + 0.05 + i * 0.01
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"匹配股票{i+1}",
            roe=roe_value
        )
        stocks.append(stock)
        indicator_values[IndicatorField.ROE][code] = roe_value
        scores[code] = 50.0 + i
        matching_codes.add(code)
    
    # 创建不满足条件的股票
    for i in range(num_non_matching):
        code = f"{600100 + i:06d}.SH"
        roe_value = threshold - 0.05 - i * 0.01
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"不匹配股票{i+1}",
            roe=roe_value
        )
        stocks.append(stock)
        indicator_values[IndicatorField.ROE][code] = roe_value
        scores[code] = 80.0 + i  # 给不匹配的股票更高的分数
        non_matching_codes.add(code)
    
    # 创建筛选条件
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(scores)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    # 验证结果中只包含满足条件的股票
    result_codes = {s.stock_code.code for s in result.matched_stocks}
    
    # 所有匹配的股票都应该在结果中
    assert result_codes == matching_codes, \
        f"结果中的股票代码 {result_codes} 与预期 {matching_codes} 不符"
    
    # 不匹配的股票不应该在结果中
    for code in non_matching_codes:
        assert code not in result_codes, \
            f"不满足条件的股票 {code} 不应出现在结果中"


@settings(max_examples=100)
@given(st.data())
def test_complex_filter_conditions_satisfied(data):
    """
    Property 10.2.2: 复杂筛选条件（多条件 AND）下所有匹配股票满足所有条件
    
    **Validates: Requirements 5.6**
    
    对于包含多个条件的 AND 组，所有匹配的股票都应满足所有条件。
    """
    # 生成两个阈值
    roe_threshold = data.draw(st.floats(min_value=0.05, max_value=0.2, allow_nan=False, allow_infinity=False))
    pe_threshold = data.draw(st.floats(min_value=5.0, max_value=30.0, allow_nan=False, allow_infinity=False))
    
    # 创建股票
    num_stocks = data.draw(st.integers(min_value=3, max_value=8))
    stocks = []
    indicator_values = {
        IndicatorField.ROE: {},
        IndicatorField.PE: {}
    }
    scores = {}
    
    for i in range(num_stocks):
        code = f"{600000 + i:06d}.SH"
        
        # 随机生成指标值
        roe_value = data.draw(st.floats(min_value=0.01, max_value=0.4, allow_nan=False, allow_infinity=False))
        pe_value = data.draw(st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False))
        
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"股票{i+1}",
            roe=roe_value,
            pe=pe_value
        )
        stocks.append(stock)
        indicator_values[IndicatorField.ROE][code] = roe_value
        indicator_values[IndicatorField.PE][code] = pe_value
        scores[code] = data.draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    
    # 创建复杂筛选条件: ROE > roe_threshold AND PE < pe_threshold
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[
            FilterCondition(
                field=IndicatorField.ROE,
                operator=ComparisonOperator.GREATER_THAN,
                value=NumericValue(roe_threshold)
            ),
            FilterCondition(
                field=IndicatorField.PE,
                operator=ComparisonOperator.LESS_THAN,
                value=NumericValue(pe_threshold)
            )
        ]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 0.5, IndicatorField.PE: 0.5},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(scores)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    # 验证所有匹配的股票都满足所有条件
    for scored_stock in result.matched_stocks:
        stock_code = scored_stock.stock_code.code
        actual_roe = indicator_values[IndicatorField.ROE][stock_code]
        actual_pe = indicator_values[IndicatorField.PE][stock_code]
        
        assert actual_roe > roe_threshold, \
            f"股票 {stock_code} 的 ROE ({actual_roe}) 不满足条件 > {roe_threshold}"
        assert actual_pe < pe_threshold, \
            f"股票 {stock_code} 的 PE ({actual_pe}) 不满足条件 < {pe_threshold}"


# =============================================================================
# Property 10.3: 结果完整性
# **Validates: Requirements 5.6**
# =============================================================================

@settings(max_examples=100)
@given(st.data())
def test_execute_returns_all_matching_stocks(data):
    """
    Property 10.3: execute() 返回所有满足条件的股票
    
    **Validates: Requirements 5.6**
    
    对于任意 ScreeningStrategy，所有满足筛选条件的股票都应出现在结果中。
    """
    threshold = 0.15
    
    # 创建股票
    num_stocks = data.draw(st.integers(min_value=3, max_value=10))
    stocks = []
    indicator_values = {IndicatorField.ROE: {}}
    scores = {}
    expected_matching_codes = set()
    
    for i in range(num_stocks):
        code = f"{600000 + i:06d}.SH"
        # 随机决定是否满足条件
        should_match = data.draw(st.booleans())
        if should_match:
            roe_value = threshold + 0.01 + i * 0.01
            expected_matching_codes.add(code)
        else:
            roe_value = threshold - 0.01 - i * 0.01
        
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"股票{i+1}",
            roe=roe_value
        )
        stocks.append(stock)
        indicator_values[IndicatorField.ROE][code] = roe_value
        scores[code] = data.draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    
    # 创建筛选条件
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(scores)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    # 验证结果包含所有满足条件的股票
    result_codes = {s.stock_code.code for s in result.matched_stocks}
    assert result_codes == expected_matching_codes, \
        f"结果中的股票代码 {result_codes} 与预期 {expected_matching_codes} 不符"


@settings(max_examples=100)
@given(st.data())
def test_execute_total_scanned_equals_input_count(data):
    """
    Property 10.3.1: total_scanned 等于输入的候选股票数量
    
    **Validates: Requirements 5.6**
    
    ScreeningResult 的 total_scanned 应等于传入的候选股票列表长度。
    """
    # 生成股票
    num_stocks = data.draw(st.integers(min_value=1, max_value=15))
    stocks = []
    indicator_values = {IndicatorField.ROE: {}}
    scores = {}
    
    for i in range(num_stocks):
        code = f"{600000 + i:06d}.SH"
        roe_value = data.draw(st.floats(min_value=0.01, max_value=0.4, allow_nan=False, allow_infinity=False))
        
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"股票{i+1}",
            roe=roe_value
        )
        stocks.append(stock)
        indicator_values[IndicatorField.ROE][code] = roe_value
        scores[code] = data.draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    
    # 创建筛选条件
    threshold = data.draw(st.floats(min_value=0.05, max_value=0.3, allow_nan=False, allow_infinity=False))
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(scores)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    # 验证 total_scanned 等于输入的股票数量
    assert result.total_scanned == num_stocks, \
        f"total_scanned ({result.total_scanned}) 应等于输入股票数量 ({num_stocks})"


# =============================================================================
# Property 10.4: 边界情况
# **Validates: Requirements 5.6**
# =============================================================================

@settings(max_examples=100)
@given(st.just(None))
def test_execute_with_empty_candidate_list(_):
    """
    Property 10.4.1: 空候选列表返回空结果
    
    **Validates: Requirements 5.6**
    
    当候选股票列表为空时，execute() 应返回空的 matched_stocks。
    """
    # 创建筛选条件
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.1)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    calc_service = MockCalcService({})
    scoring_service = MockScoringService({})
    
    # 执行策略（空列表）
    result = strategy.execute([], scoring_service, calc_service)
    
    # 验证结果
    assert len(result.matched_stocks) == 0
    assert result.total_scanned == 0


@settings(max_examples=100)
@given(st.data())
def test_execute_with_no_matching_stocks(data):
    """
    Property 10.4.2: 无匹配股票时返回空结果
    
    **Validates: Requirements 5.6**
    
    当没有股票满足筛选条件时，execute() 应返回空的 matched_stocks。
    """
    # 设置一个很高的阈值
    threshold = 0.9
    
    # 创建股票，所有股票都不满足条件
    num_stocks = data.draw(st.integers(min_value=1, max_value=5))
    stocks = []
    indicator_values = {IndicatorField.ROE: {}}
    scores = {}
    
    for i in range(num_stocks):
        code = f"{600000 + i:06d}.SH"
        roe_value = data.draw(st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False))
        
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"股票{i+1}",
            roe=roe_value
        )
        stocks.append(stock)
        indicator_values[IndicatorField.ROE][code] = roe_value
        scores[code] = data.draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    
    # 创建筛选条件（阈值很高，没有股票能满足）
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(scores)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    # 验证结果为空
    assert len(result.matched_stocks) == 0
    assert result.total_scanned == num_stocks


@settings(max_examples=100)
@given(st.data())
def test_execute_with_single_matching_stock(data):
    """
    Property 10.4.3: 单个匹配股票时结果正确
    
    **Validates: Requirements 5.6**
    
    当只有一只股票满足条件时，结果应只包含该股票。
    """
    threshold = 0.15
    
    # 创建一个满足条件的股票和多个不满足条件的股票
    num_non_matching = data.draw(st.integers(min_value=1, max_value=5))
    stocks = []
    indicator_values = {IndicatorField.ROE: {}}
    scores = {}
    
    # 创建满足条件的股票
    matching_code = "600000.SH"
    matching_roe = threshold + 0.1
    matching_score = data.draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    
    matching_stock = Stock(
        stock_code=StockCode(matching_code),
        stock_name="匹配股票",
        roe=matching_roe
    )
    stocks.append(matching_stock)
    indicator_values[IndicatorField.ROE][matching_code] = matching_roe
    scores[matching_code] = matching_score
    
    # 创建不满足条件的股票
    for i in range(num_non_matching):
        code = f"{600001 + i:06d}.SH"
        roe_value = threshold - 0.05 - i * 0.01
        
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"不匹配股票{i+1}",
            roe=roe_value
        )
        stocks.append(stock)
        indicator_values[IndicatorField.ROE][code] = roe_value
        scores[code] = data.draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    
    # 创建筛选条件
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(scores)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    # 验证结果只包含一只股票
    assert len(result.matched_stocks) == 1
    assert result.matched_stocks[0].stock_code.code == matching_code
    assert result.matched_stocks[0].score == matching_score


# =============================================================================
# Property 10.5: 排序与筛选的组合验证
# **Validates: Requirements 5.6**
# =============================================================================

@settings(max_examples=100)
@given(st.data())
def test_execute_sorting_and_filtering_combined(data):
    """
    Property 10.5: 排序和筛选同时正确
    
    **Validates: Requirements 5.6**
    
    综合验证：结果按 score 降序排列，且所有股票都满足筛选条件。
    """
    threshold = 0.1
    
    # 创建股票
    num_stocks = data.draw(st.integers(min_value=5, max_value=15))
    stocks = []
    indicator_values = {IndicatorField.ROE: {}}
    scores = {}
    
    for i in range(num_stocks):
        code = f"{600000 + i:06d}.SH"
        roe_value = data.draw(st.floats(min_value=0.01, max_value=0.4, allow_nan=False, allow_infinity=False))
        score = data.draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
        
        stock = Stock(
            stock_code=StockCode(code),
            stock_name=f"股票{i+1}",
            roe=roe_value
        )
        stocks.append(stock)
        indicator_values[IndicatorField.ROE][code] = roe_value
        scores[code] = score
    
    # 创建筛选条件
    filters = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )]
    )
    
    # 创建策略
    strategy = ScreeningStrategy(
        strategy_id=StrategyId.generate(),
        name="测试策略",
        filters=filters,
        scoring_config=ScoringConfig(
            weights={IndicatorField.ROE: 1.0},
            normalization_method=NormalizationMethod.MIN_MAX
        )
    )
    
    # 创建 mock 服务
    calc_service = MockCalcService(indicator_values)
    scoring_service = MockScoringService(scores)
    
    # 执行策略
    result = strategy.execute(stocks, scoring_service, calc_service)
    
    matched_stocks = result.matched_stocks
    
    # 验证 1: 所有匹配的股票都满足筛选条件
    for scored_stock in matched_stocks:
        stock_code = scored_stock.stock_code.code
        actual_roe = indicator_values[IndicatorField.ROE][stock_code]
        assert actual_roe > threshold, \
            f"股票 {stock_code} 的 ROE ({actual_roe}) 不满足条件 > {threshold}"
    
    # 验证 2: 结果按 score 降序排列
    for i in range(len(matched_stocks) - 1):
        assert matched_stocks[i].score >= matched_stocks[i + 1].score, \
            f"结果未按 score 降序排列: {matched_stocks[i].score} < {matched_stocks[i + 1].score}"
    
    # 验证 3: 结果数量正确（等于满足条件的股票数量）
    expected_count = sum(
        1 for code, roe in indicator_values[IndicatorField.ROE].items()
        if roe > threshold
    )
    assert len(matched_stocks) == expected_count, \
        f"结果数量 ({len(matched_stocks)}) 与预期 ({expected_count}) 不符"
