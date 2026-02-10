"""
Property-based tests for FilterGroup.match logic semantics

Feature: stock-screening-platform
Property 9: FilterGroup.match 逻辑语义一致性

**Validates: Requirements 5.3, 5.4, 5.5**

Property Description:
对于任意 FilterGroup、Stock 和 calc_service，当 operator 为 AND 时，match 结果应等于所有子条件结果的逻辑与；
当 operator 为 OR 时，应等于逻辑或；当 operator 为 NOT 时，应等于单个子元素结果的取反。

Requirements:
- 5.3: AND 运算符 - 所有条件和子组都匹配时返回 True
- 5.4: OR 运算符 - 至少一个条件或子组匹配时返回 True
- 5.5: NOT 运算符 - 对单个子元素的结果取反
"""
import uuid
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
from unittest.mock import Mock
from typing import List, Tuple

from contexts.screening.domain.models.filter_group import FilterGroup
from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import (
    NumericValue, TextValue, ListValue, RangeValue
)
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from contexts.screening.domain.enums.enums import LogicalOperator, ValueType


# =============================================================================
# 分类指标字段
# =============================================================================

NUMERIC_FIELDS = [f for f in IndicatorField if f.value_type == ValueType.NUMERIC]
TEXT_FIELDS = [f for f in IndicatorField if f.value_type == ValueType.TEXT]



# =============================================================================
# Mock Calc Service 策略
# =============================================================================

class MockCalcService:
    """
    模拟的指标计算服务
    
    通过预设的结果映射来控制条件评估结果。
    """
    def __init__(self, indicator_values: dict):
        """
        Args:
            indicator_values: IndicatorField -> 实际值的映射
        """
        self._indicator_values = indicator_values
    
    def calculate_indicator(self, field: IndicatorField, stock) -> any:
        """返回预设的指标值"""
        return self._indicator_values.get(field)


class MockStock:
    """模拟的股票实体"""
    pass


# =============================================================================
# 条件评估结果控制策略
# =============================================================================

@composite
def condition_with_controlled_result(draw, expected_result: bool):
    """
    生成一个 FilterCondition，并配置 calc_service 使其评估结果为指定值
    
    Args:
        expected_result: 期望的评估结果 (True/False)
        
    Returns:
        Tuple[FilterCondition, dict]: (条件, 指标值映射)
    """
    field = draw(st.sampled_from(NUMERIC_FIELDS))
    threshold = draw(st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False))
    
    if expected_result:
        # 要使 GREATER_THAN 返回 True，actual > threshold
        actual_value = threshold + draw(st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False))
    else:
        # 要使 GREATER_THAN 返回 False，actual <= threshold
        actual_value = threshold - draw(st.floats(min_value=0.0, max_value=threshold, allow_nan=False, allow_infinity=False))
    
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.GREATER_THAN,
        value=NumericValue(threshold)
    )
    
    indicator_values = {field: actual_value}
    
    return (condition, indicator_values)


@composite
def multiple_conditions_with_results(draw, results: List[bool]):
    """
    生成多个 FilterCondition，每个条件的评估结果由 results 列表指定
    
    Args:
        results: 每个条件期望的评估结果列表
        
    Returns:
        Tuple[List[FilterCondition], dict]: (条件列表, 合并的指标值映射)
    """
    conditions = []
    all_indicator_values = {}
    
    # 使用不同的字段避免冲突
    available_fields = list(NUMERIC_FIELDS)
    assume(len(results) <= len(available_fields))
    
    for i, expected_result in enumerate(results):
        field = available_fields[i]
        threshold = draw(st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False))
        
        if expected_result:
            actual_value = threshold + draw(st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False))
        else:
            actual_value = threshold - draw(st.floats(min_value=0.0, max_value=threshold, allow_nan=False, allow_infinity=False))
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        
        conditions.append(condition)
        all_indicator_values[field] = actual_value
    
    return (conditions, all_indicator_values)



# =============================================================================
# Property 9.1: AND 运算符逻辑语义
# **Validates: Requirements 5.3**
# =============================================================================

@settings(max_examples=100)
@given(
    results=st.lists(st.booleans(), min_size=1, max_size=5)
)
def test_and_operator_equals_all_results(results):
    """
    Property 9.1: AND 运算符等于所有结果的逻辑与
    
    **Validates: Requirements 5.3**
    
    对于任意 FilterGroup（operator=AND）和任意条件评估结果列表，
    match() 的结果应等于 all(results)。
    """
    # 确保有足够的字段
    assume(len(results) <= len(NUMERIC_FIELDS))
    
    # 构建条件和指标值
    conditions = []
    indicator_values = {}
    
    for i, expected_result in enumerate(results):
        field = NUMERIC_FIELDS[i]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0  # > threshold -> True
        else:
            actual_value = threshold - 10.0  # < threshold -> False
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
    
    # 创建 AND 组
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=conditions
    )
    
    # 创建 mock 对象
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    # 验证 match 结果等于 all(results)
    expected = all(results)
    actual = group.match(stock, calc_service)
    
    assert actual == expected, f"AND group match={actual}, expected all({results})={expected}"


@settings(max_examples=100)
@given(st.data())
def test_and_operator_all_true_returns_true(data):
    """
    Property 9.1.1: AND 运算符 - 所有条件为真时返回 True
    
    **Validates: Requirements 5.3**
    """
    num_conditions = data.draw(st.integers(min_value=1, max_value=5))
    assume(num_conditions <= len(NUMERIC_FIELDS))
    
    conditions = []
    indicator_values = {}
    
    for i in range(num_conditions):
        field = NUMERIC_FIELDS[i]
        threshold = data.draw(st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False))
        actual_value = threshold + data.draw(st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False))
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
    
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=conditions
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    assert group.match(stock, calc_service) is True


@settings(max_examples=100)
@given(st.data())
def test_and_operator_one_false_returns_false(data):
    """
    Property 9.1.2: AND 运算符 - 至少一个条件为假时返回 False
    
    **Validates: Requirements 5.3**
    """
    num_conditions = data.draw(st.integers(min_value=2, max_value=5))
    assume(num_conditions <= len(NUMERIC_FIELDS))
    
    # 随机选择一个条件为假
    false_index = data.draw(st.integers(min_value=0, max_value=num_conditions - 1))
    
    conditions = []
    indicator_values = {}
    
    for i in range(num_conditions):
        field = NUMERIC_FIELDS[i]
        threshold = data.draw(st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False))
        
        if i == false_index:
            # 这个条件为假
            actual_value = threshold - data.draw(st.floats(min_value=0.01, max_value=threshold, allow_nan=False, allow_infinity=False))
        else:
            # 其他条件为真
            actual_value = threshold + data.draw(st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False))
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
    
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=conditions
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    assert group.match(stock, calc_service) is False



# =============================================================================
# Property 9.2: OR 运算符逻辑语义
# **Validates: Requirements 5.4**
# =============================================================================

@settings(max_examples=100)
@given(
    results=st.lists(st.booleans(), min_size=1, max_size=5)
)
def test_or_operator_equals_any_results(results):
    """
    Property 9.2: OR 运算符等于所有结果的逻辑或
    
    **Validates: Requirements 5.4**
    
    对于任意 FilterGroup（operator=OR）和任意条件评估结果列表，
    match() 的结果应等于 any(results)。
    """
    assume(len(results) <= len(NUMERIC_FIELDS))
    
    conditions = []
    indicator_values = {}
    
    for i, expected_result in enumerate(results):
        field = NUMERIC_FIELDS[i]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
    
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.OR,
        conditions=conditions
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    expected = any(results)
    actual = group.match(stock, calc_service)
    
    assert actual == expected, f"OR group match={actual}, expected any({results})={expected}"


@settings(max_examples=100)
@given(st.data())
def test_or_operator_one_true_returns_true(data):
    """
    Property 9.2.1: OR 运算符 - 至少一个条件为真时返回 True
    
    **Validates: Requirements 5.4**
    """
    num_conditions = data.draw(st.integers(min_value=2, max_value=5))
    assume(num_conditions <= len(NUMERIC_FIELDS))
    
    # 随机选择一个条件为真
    true_index = data.draw(st.integers(min_value=0, max_value=num_conditions - 1))
    
    conditions = []
    indicator_values = {}
    
    for i in range(num_conditions):
        field = NUMERIC_FIELDS[i]
        threshold = data.draw(st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False))
        
        if i == true_index:
            actual_value = threshold + data.draw(st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False))
        else:
            actual_value = threshold - data.draw(st.floats(min_value=0.01, max_value=threshold, allow_nan=False, allow_infinity=False))
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
    
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.OR,
        conditions=conditions
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    assert group.match(stock, calc_service) is True


@settings(max_examples=100)
@given(st.data())
def test_or_operator_all_false_returns_false(data):
    """
    Property 9.2.2: OR 运算符 - 所有条件为假时返回 False
    
    **Validates: Requirements 5.4**
    """
    num_conditions = data.draw(st.integers(min_value=1, max_value=5))
    assume(num_conditions <= len(NUMERIC_FIELDS))
    
    conditions = []
    indicator_values = {}
    
    for i in range(num_conditions):
        field = NUMERIC_FIELDS[i]
        threshold = data.draw(st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False))
        actual_value = threshold - data.draw(st.floats(min_value=0.01, max_value=threshold, allow_nan=False, allow_infinity=False))
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
    
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.OR,
        conditions=conditions
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    assert group.match(stock, calc_service) is False



# =============================================================================
# Property 9.3: NOT 运算符逻辑语义
# **Validates: Requirements 5.5**
# =============================================================================

@settings(max_examples=100)
@given(
    first_result=st.booleans()
)
def test_not_operator_negates_first_result(first_result):
    """
    Property 9.3: NOT 运算符等于第一个结果的取反
    
    **Validates: Requirements 5.5**
    
    对于任意 FilterGroup（operator=NOT）和第一个条件的评估结果，
    match() 的结果应等于 not first_result。
    """
    field = NUMERIC_FIELDS[0]
    threshold = 50.0
    
    if first_result:
        actual_value = threshold + 10.0
    else:
        actual_value = threshold - 10.0
    
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.GREATER_THAN,
        value=NumericValue(threshold)
    )
    
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        conditions=[condition]
    )
    
    stock = MockStock()
    calc_service = MockCalcService({field: actual_value})
    
    expected = not first_result
    actual = group.match(stock, calc_service)
    
    assert actual == expected, f"NOT group match={actual}, expected not {first_result}={expected}"


@settings(max_examples=100)
@given(st.data())
def test_not_operator_negates_true_to_false(data):
    """
    Property 9.3.1: NOT 运算符 - 对真条件取反返回 False
    
    **Validates: Requirements 5.5**
    """
    field = NUMERIC_FIELDS[0]
    threshold = data.draw(st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    actual_value = threshold + data.draw(st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False))
    
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.GREATER_THAN,
        value=NumericValue(threshold)
    )
    
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        conditions=[condition]
    )
    
    stock = MockStock()
    calc_service = MockCalcService({field: actual_value})
    
    assert group.match(stock, calc_service) is False


@settings(max_examples=100)
@given(st.data())
def test_not_operator_negates_false_to_true(data):
    """
    Property 9.3.2: NOT 运算符 - 对假条件取反返回 True
    
    **Validates: Requirements 5.5**
    """
    field = NUMERIC_FIELDS[0]
    threshold = data.draw(st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    actual_value = threshold - data.draw(st.floats(min_value=0.01, max_value=threshold, allow_nan=False, allow_infinity=False))
    
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.GREATER_THAN,
        value=NumericValue(threshold)
    )
    
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        conditions=[condition]
    )
    
    stock = MockStock()
    calc_service = MockCalcService({field: actual_value})
    
    assert group.match(stock, calc_service) is True


@settings(max_examples=100)
@given(
    sub_group_result=st.booleans()
)
def test_not_operator_negates_sub_group_result(sub_group_result):
    """
    Property 9.3.3: NOT 运算符 - 对子组结果取反
    
    **Validates: Requirements 5.5**
    
    NOT 运算符也应该正确处理子组的结果。
    """
    field = NUMERIC_FIELDS[0]
    threshold = 50.0
    
    if sub_group_result:
        actual_value = threshold + 10.0
    else:
        actual_value = threshold - 10.0
    
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.GREATER_THAN,
        value=NumericValue(threshold)
    )
    
    # 创建子组
    sub_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[condition]
    )
    
    # 创建 NOT 组，包含子组
    not_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        sub_groups=[sub_group]
    )
    
    stock = MockStock()
    calc_service = MockCalcService({field: actual_value})
    
    expected = not sub_group_result
    actual = not_group.match(stock, calc_service)
    
    assert actual == expected



# =============================================================================
# Property 9.4: 空组行为
# **Validates: Requirements 5.3, 5.4, 5.5**
# =============================================================================

@settings(max_examples=100)
@given(st.just(None))
def test_and_empty_group_returns_true(_):
    """
    Property 9.4.1: AND 空组返回 True
    
    **Validates: Requirements 5.3**
    
    空集的全称量化为真：对于空集中的所有元素，任何条件都成立。
    """
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[],
        sub_groups=[]
    )
    
    stock = MockStock()
    calc_service = MockCalcService({})
    
    assert group.match(stock, calc_service) is True


@settings(max_examples=100)
@given(st.just(None))
def test_or_empty_group_returns_false(_):
    """
    Property 9.4.2: OR 空组返回 False
    
    **Validates: Requirements 5.4**
    
    空集的存在量化为假：空集中不存在任何满足条件的元素。
    """
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.OR,
        conditions=[],
        sub_groups=[]
    )
    
    stock = MockStock()
    calc_service = MockCalcService({})
    
    assert group.match(stock, calc_service) is False


@settings(max_examples=100)
@given(st.just(None))
def test_not_empty_group_returns_true(_):
    """
    Property 9.4.3: NOT 空组返回 True
    
    **Validates: Requirements 5.5**
    
    空组没有元素可取反，默认返回 True。
    """
    group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        conditions=[],
        sub_groups=[]
    )
    
    stock = MockStock()
    calc_service = MockCalcService({})
    
    assert group.match(stock, calc_service) is True


# =============================================================================
# Property 9.5: 嵌套组逻辑语义
# **Validates: Requirements 5.3, 5.4, 5.5**
# =============================================================================

@settings(max_examples=100)
@given(
    sub_results=st.lists(st.booleans(), min_size=1, max_size=3)
)
def test_and_with_sub_groups_equals_all(sub_results):
    """
    Property 9.5.1: AND 组包含子组时，结果等于所有子组结果的逻辑与
    
    **Validates: Requirements 5.3**
    """
    assume(len(sub_results) <= len(NUMERIC_FIELDS))
    
    sub_groups = []
    indicator_values = {}
    
    for i, expected_result in enumerate(sub_results):
        field = NUMERIC_FIELDS[i]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        
        sub_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition]
        )
        sub_groups.append(sub_group)
        indicator_values[field] = actual_value
    
    root_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        sub_groups=sub_groups
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    expected = all(sub_results)
    actual = root_group.match(stock, calc_service)
    
    assert actual == expected


@settings(max_examples=100)
@given(
    sub_results=st.lists(st.booleans(), min_size=1, max_size=3)
)
def test_or_with_sub_groups_equals_any(sub_results):
    """
    Property 9.5.2: OR 组包含子组时，结果等于所有子组结果的逻辑或
    
    **Validates: Requirements 5.4**
    """
    assume(len(sub_results) <= len(NUMERIC_FIELDS))
    
    sub_groups = []
    indicator_values = {}
    
    for i, expected_result in enumerate(sub_results):
        field = NUMERIC_FIELDS[i]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        
        sub_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition]
        )
        sub_groups.append(sub_group)
        indicator_values[field] = actual_value
    
    root_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.OR,
        sub_groups=sub_groups
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    expected = any(sub_results)
    actual = root_group.match(stock, calc_service)
    
    assert actual == expected



# =============================================================================
# Property 9.6: 混合条件和子组
# **Validates: Requirements 5.3, 5.4, 5.5**
# =============================================================================

@settings(max_examples=100)
@given(
    condition_results=st.lists(st.booleans(), min_size=1, max_size=2),
    sub_group_results=st.lists(st.booleans(), min_size=1, max_size=2)
)
def test_and_with_mixed_conditions_and_sub_groups(condition_results, sub_group_results):
    """
    Property 9.6.1: AND 组同时包含条件和子组时，结果等于所有结果的逻辑与
    
    **Validates: Requirements 5.3**
    """
    total_elements = len(condition_results) + len(sub_group_results)
    assume(total_elements <= len(NUMERIC_FIELDS))
    
    conditions = []
    sub_groups = []
    indicator_values = {}
    field_index = 0
    
    # 创建直接条件
    for expected_result in condition_results:
        field = NUMERIC_FIELDS[field_index]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
        field_index += 1
    
    # 创建子组
    for expected_result in sub_group_results:
        field = NUMERIC_FIELDS[field_index]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        sub_condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        
        sub_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[sub_condition]
        )
        sub_groups.append(sub_group)
        indicator_values[field] = actual_value
        field_index += 1
    
    root_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=conditions,
        sub_groups=sub_groups
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    all_results = condition_results + sub_group_results
    expected = all(all_results)
    actual = root_group.match(stock, calc_service)
    
    assert actual == expected


@settings(max_examples=100)
@given(
    condition_results=st.lists(st.booleans(), min_size=1, max_size=2),
    sub_group_results=st.lists(st.booleans(), min_size=1, max_size=2)
)
def test_or_with_mixed_conditions_and_sub_groups(condition_results, sub_group_results):
    """
    Property 9.6.2: OR 组同时包含条件和子组时，结果等于所有结果的逻辑或
    
    **Validates: Requirements 5.4**
    """
    total_elements = len(condition_results) + len(sub_group_results)
    assume(total_elements <= len(NUMERIC_FIELDS))
    
    conditions = []
    sub_groups = []
    indicator_values = {}
    field_index = 0
    
    for expected_result in condition_results:
        field = NUMERIC_FIELDS[field_index]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
        field_index += 1
    
    for expected_result in sub_group_results:
        field = NUMERIC_FIELDS[field_index]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        sub_condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        
        sub_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[sub_condition]
        )
        sub_groups.append(sub_group)
        indicator_values[field] = actual_value
        field_index += 1
    
    root_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.OR,
        conditions=conditions,
        sub_groups=sub_groups
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    all_results = condition_results + sub_group_results
    expected = any(all_results)
    actual = root_group.match(stock, calc_service)
    
    assert actual == expected



# =============================================================================
# Property 9.7: 深度嵌套逻辑语义
# **Validates: Requirements 5.3, 5.4, 5.5**
# =============================================================================

@settings(max_examples=100)
@given(
    level1_results=st.lists(st.booleans(), min_size=1, max_size=2),
    level2_results=st.lists(st.booleans(), min_size=1, max_size=2)
)
def test_deeply_nested_and_or_combination(level1_results, level2_results):
    """
    Property 9.7.1: 深度嵌套组的逻辑语义一致性
    
    **Validates: Requirements 5.3, 5.4**
    
    测试结构: AND(OR(conditions...), OR(conditions...))
    """
    total_conditions = len(level1_results) + len(level2_results)
    assume(total_conditions <= len(NUMERIC_FIELDS))
    
    indicator_values = {}
    field_index = 0
    
    # 创建第一个 OR 子组
    or_group1_conditions = []
    for expected_result in level1_results:
        field = NUMERIC_FIELDS[field_index]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        or_group1_conditions.append(condition)
        indicator_values[field] = actual_value
        field_index += 1
    
    or_group1 = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.OR,
        conditions=or_group1_conditions
    )
    
    # 创建第二个 OR 子组
    or_group2_conditions = []
    for expected_result in level2_results:
        field = NUMERIC_FIELDS[field_index]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        or_group2_conditions.append(condition)
        indicator_values[field] = actual_value
        field_index += 1
    
    or_group2 = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.OR,
        conditions=or_group2_conditions
    )
    
    # 创建根 AND 组
    root_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        sub_groups=[or_group1, or_group2]
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    # 期望结果: any(level1_results) AND any(level2_results)
    expected = any(level1_results) and any(level2_results)
    actual = root_group.match(stock, calc_service)
    
    assert actual == expected


@settings(max_examples=100)
@given(
    inner_result=st.booleans()
)
def test_not_of_and_group(inner_result):
    """
    Property 9.7.2: NOT(AND(...)) 的逻辑语义
    
    **Validates: Requirements 5.5**
    """
    field = NUMERIC_FIELDS[0]
    threshold = 50.0
    
    if inner_result:
        actual_value = threshold + 10.0
    else:
        actual_value = threshold - 10.0
    
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.GREATER_THAN,
        value=NumericValue(threshold)
    )
    
    and_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=[condition]
    )
    
    not_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        sub_groups=[and_group]
    )
    
    stock = MockStock()
    calc_service = MockCalcService({field: actual_value})
    
    expected = not inner_result
    actual = not_group.match(stock, calc_service)
    
    assert actual == expected


@settings(max_examples=100)
@given(
    inner_results=st.lists(st.booleans(), min_size=1, max_size=3)
)
def test_not_of_or_group(inner_results):
    """
    Property 9.7.3: NOT(OR(...)) 的逻辑语义
    
    **Validates: Requirements 5.5**
    """
    assume(len(inner_results) <= len(NUMERIC_FIELDS))
    
    conditions = []
    indicator_values = {}
    
    for i, expected_result in enumerate(inner_results):
        field = NUMERIC_FIELDS[i]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
    
    or_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.OR,
        conditions=conditions
    )
    
    not_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        sub_groups=[or_group]
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    # NOT(OR(...)) = not any(inner_results)
    expected = not any(inner_results)
    actual = not_group.match(stock, calc_service)
    
    assert actual == expected



# =============================================================================
# Property 9.8: 逻辑等价性验证
# **Validates: Requirements 5.3, 5.4, 5.5**
# =============================================================================

@settings(max_examples=100)
@given(
    results=st.lists(st.booleans(), min_size=2, max_size=4)
)
def test_de_morgan_law_not_and_equals_or_not(results):
    """
    Property 9.8.1: 德摩根定律验证 - NOT(AND(a,b)) = OR(NOT(a), NOT(b))
    
    **Validates: Requirements 5.3, 5.4, 5.5**
    
    验证 FilterGroup 的逻辑运算符遵循德摩根定律。
    """
    assume(len(results) <= len(NUMERIC_FIELDS))
    
    conditions = []
    indicator_values = {}
    
    for i, expected_result in enumerate(results):
        field = NUMERIC_FIELDS[i]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
    
    # 构建 NOT(AND(conditions...))
    and_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.AND,
        conditions=conditions
    )
    
    not_and_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        sub_groups=[and_group]
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    # NOT(AND(a,b,...)) = not all(results)
    not_and_result = not_and_group.match(stock, calc_service)
    expected = not all(results)
    
    assert not_and_result == expected


@settings(max_examples=100)
@given(
    results=st.lists(st.booleans(), min_size=2, max_size=4)
)
def test_de_morgan_law_not_or_equals_and_not(results):
    """
    Property 9.8.2: 德摩根定律验证 - NOT(OR(a,b)) = AND(NOT(a), NOT(b))
    
    **Validates: Requirements 5.3, 5.4, 5.5**
    """
    assume(len(results) <= len(NUMERIC_FIELDS))
    
    conditions = []
    indicator_values = {}
    
    for i, expected_result in enumerate(results):
        field = NUMERIC_FIELDS[i]
        threshold = 50.0
        
        if expected_result:
            actual_value = threshold + 10.0
        else:
            actual_value = threshold - 10.0
        
        condition = FilterCondition(
            field=field,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(threshold)
        )
        conditions.append(condition)
        indicator_values[field] = actual_value
    
    # 构建 NOT(OR(conditions...))
    or_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.OR,
        conditions=conditions
    )
    
    not_or_group = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        sub_groups=[or_group]
    )
    
    stock = MockStock()
    calc_service = MockCalcService(indicator_values)
    
    # NOT(OR(a,b,...)) = not any(results)
    not_or_result = not_or_group.match(stock, calc_service)
    expected = not any(results)
    
    assert not_or_result == expected


@settings(max_examples=100)
@given(
    result=st.booleans()
)
def test_double_negation_elimination(result):
    """
    Property 9.8.3: 双重否定消除 - NOT(NOT(a)) = a
    
    **Validates: Requirements 5.5**
    """
    field = NUMERIC_FIELDS[0]
    threshold = 50.0
    
    if result:
        actual_value = threshold + 10.0
    else:
        actual_value = threshold - 10.0
    
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.GREATER_THAN,
        value=NumericValue(threshold)
    )
    
    # 构建 NOT(NOT(condition))
    inner_not = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        conditions=[condition]
    )
    
    outer_not = FilterGroup(
        group_id=str(uuid.uuid4()),
        operator=LogicalOperator.NOT,
        sub_groups=[inner_not]
    )
    
    stock = MockStock()
    calc_service = MockCalcService({field: actual_value})
    
    # NOT(NOT(a)) = a
    double_not_result = outer_not.match(stock, calc_service)
    
    assert double_not_result == result

