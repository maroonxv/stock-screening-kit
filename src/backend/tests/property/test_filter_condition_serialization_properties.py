"""
Property-based tests for FilterCondition serialization round-trip

Feature: stock-screening-platform
Property 6: FilterCondition 序列化 round-trip

**Validates: Requirements 3.11**

Property Description:
对于任意有效的 FilterCondition 对象，调用 to_dict() 然后 from_dict() 
应产生一个与原始对象等价的 FilterCondition。
"""
import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite

from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import (
    NumericValue, TextValue, ListValue, RangeValue, TimeSeriesValue
)
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from contexts.screening.domain.enums.enums import ValueType


# =============================================================================
# 分类指标字段
# =============================================================================

# 获取所有 NUMERIC 类型的字段
NUMERIC_FIELDS = [f for f in IndicatorField if f.value_type == ValueType.NUMERIC]

# 获取所有 TEXT 类型的字段
TEXT_FIELDS = [f for f in IndicatorField if f.value_type == ValueType.TEXT]


# =============================================================================
# 值生成策略
# =============================================================================

@composite
def numeric_value_strategy(draw):
    """生成有效的 NumericValue"""
    value = draw(st.floats(
        min_value=-1e6, 
        max_value=1e6,
        allow_nan=False, 
        allow_infinity=False
    ))
    unit = draw(st.one_of(st.none(), st.text(min_size=1, max_size=10)))
    return NumericValue(value=value, unit=unit)


@composite
def text_value_strategy(draw):
    """生成有效的 TextValue"""
    value = draw(st.text(min_size=1, max_size=50))
    return TextValue(value=value)


@composite
def list_value_strategy(draw):
    """生成有效的 ListValue"""
    values = draw(st.lists(
        st.text(min_size=1, max_size=20),
        min_size=1,
        max_size=10
    ))
    return ListValue(values=values)


@composite
def range_value_strategy(draw):
    """生成有效的 RangeValue (确保 min <= max)"""
    a = draw(st.floats(
        min_value=-1e6, 
        max_value=1e6,
        allow_nan=False, 
        allow_infinity=False
    ))
    b = draw(st.floats(
        min_value=-1e6, 
        max_value=1e6,
        allow_nan=False, 
        allow_infinity=False
    ))
    return RangeValue(min_val=min(a, b), max_val=max(a, b))


@composite
def time_series_value_strategy(draw):
    """生成有效的 TimeSeriesValue"""
    years = draw(st.integers(min_value=1, max_value=10))
    threshold = draw(st.one_of(
        st.none(),
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
    ))
    return TimeSeriesValue(years=years, threshold=threshold)


# =============================================================================
# 运算符策略
# =============================================================================

# 适用于 NumericValue 的运算符
NUMERIC_VALUE_OPERATORS = [
    ComparisonOperator.GREATER_THAN,
    ComparisonOperator.LESS_THAN,
    ComparisonOperator.EQUALS,
    ComparisonOperator.GREATER_OR_EQUAL,
    ComparisonOperator.LESS_OR_EQUAL,
    ComparisonOperator.NOT_EQUALS
]

# 适用于 TextValue 的运算符
TEXT_VALUE_OPERATORS = [
    ComparisonOperator.EQUALS,
    ComparisonOperator.NOT_EQUALS
]


# =============================================================================
# FilterCondition 生成策略
# =============================================================================

@composite
def filter_condition_with_numeric_value(draw):
    """生成使用 NumericValue 的有效 FilterCondition"""
    field = draw(st.sampled_from(NUMERIC_FIELDS))
    operator = draw(st.sampled_from(NUMERIC_VALUE_OPERATORS))
    value = draw(numeric_value_strategy())
    return FilterCondition(field=field, operator=operator, value=value)


@composite
def filter_condition_with_range_value(draw):
    """生成使用 RangeValue 的有效 FilterCondition"""
    field = draw(st.sampled_from(NUMERIC_FIELDS))
    operator = draw(st.sampled_from([
        ComparisonOperator.BETWEEN,
        ComparisonOperator.NOT_BETWEEN
    ]))
    value = draw(range_value_strategy())
    return FilterCondition(field=field, operator=operator, value=value)


@composite
def filter_condition_with_time_series_value(draw):
    """生成使用 TimeSeriesValue 的有效 FilterCondition"""
    field = draw(st.sampled_from(NUMERIC_FIELDS))
    # TimeSeriesValue 可以使用基本比较运算符
    operator = draw(st.sampled_from(NUMERIC_VALUE_OPERATORS))
    value = draw(time_series_value_strategy())
    return FilterCondition(field=field, operator=operator, value=value)


@composite
def filter_condition_with_text_value(draw):
    """生成使用 TextValue 的有效 FilterCondition"""
    field = draw(st.sampled_from(TEXT_FIELDS))
    operator = draw(st.sampled_from(TEXT_VALUE_OPERATORS))
    value = draw(text_value_strategy())
    return FilterCondition(field=field, operator=operator, value=value)


@composite
def filter_condition_with_list_value(draw):
    """生成使用 ListValue 的有效 FilterCondition"""
    field = draw(st.sampled_from(TEXT_FIELDS))
    operator = draw(st.sampled_from([
        ComparisonOperator.IN,
        ComparisonOperator.NOT_IN
    ]))
    value = draw(list_value_strategy())
    return FilterCondition(field=field, operator=operator, value=value)


# 组合所有有效的 FilterCondition 策略
valid_filter_condition_strategy = st.one_of(
    filter_condition_with_numeric_value(),
    filter_condition_with_range_value(),
    filter_condition_with_time_series_value(),
    filter_condition_with_text_value(),
    filter_condition_with_list_value()
)


# =============================================================================
# Property 6: FilterCondition 序列化 round-trip
# **Validates: Requirements 3.11**
# =============================================================================

@settings(max_examples=100)
@given(condition=valid_filter_condition_strategy)
def test_filter_condition_serialization_round_trip(condition):
    """
    Property 6: FilterCondition 序列化 round-trip
    
    **Validates: Requirements 3.11**
    
    对于任意有效的 FilterCondition 对象，调用 to_dict() 然后 from_dict() 
    应产生一个与原始对象等价的 FilterCondition。
    """
    # 序列化为字典
    serialized = condition.to_dict()
    
    # 从字典反序列化
    deserialized = FilterCondition.from_dict(serialized)
    
    # 验证等价性
    assert deserialized == condition
    assert deserialized.field == condition.field
    assert deserialized.operator == condition.operator
    assert deserialized.value.to_dict() == condition.value.to_dict()


@settings(max_examples=100)
@given(condition=filter_condition_with_numeric_value())
def test_numeric_value_filter_condition_round_trip(condition):
    """
    Property 6.1: NumericValue FilterCondition 序列化 round-trip
    
    **Validates: Requirements 3.11**
    
    对于使用 NumericValue 的 FilterCondition，序列化后反序列化应保持等价。
    """
    serialized = condition.to_dict()
    deserialized = FilterCondition.from_dict(serialized)
    
    assert deserialized == condition
    assert isinstance(deserialized.value, NumericValue)


@settings(max_examples=100)
@given(condition=filter_condition_with_range_value())
def test_range_value_filter_condition_round_trip(condition):
    """
    Property 6.2: RangeValue FilterCondition 序列化 round-trip
    
    **Validates: Requirements 3.11**
    
    对于使用 RangeValue 的 FilterCondition，序列化后反序列化应保持等价。
    """
    serialized = condition.to_dict()
    deserialized = FilterCondition.from_dict(serialized)
    
    assert deserialized == condition
    assert isinstance(deserialized.value, RangeValue)


@settings(max_examples=100)
@given(condition=filter_condition_with_time_series_value())
def test_time_series_value_filter_condition_round_trip(condition):
    """
    Property 6.3: TimeSeriesValue FilterCondition 序列化 round-trip
    
    **Validates: Requirements 3.11**
    
    对于使用 TimeSeriesValue 的 FilterCondition，序列化后反序列化应保持等价。
    """
    serialized = condition.to_dict()
    deserialized = FilterCondition.from_dict(serialized)
    
    assert deserialized == condition
    assert isinstance(deserialized.value, TimeSeriesValue)


@settings(max_examples=100)
@given(condition=filter_condition_with_text_value())
def test_text_value_filter_condition_round_trip(condition):
    """
    Property 6.4: TextValue FilterCondition 序列化 round-trip
    
    **Validates: Requirements 3.11**
    
    对于使用 TextValue 的 FilterCondition，序列化后反序列化应保持等价。
    """
    serialized = condition.to_dict()
    deserialized = FilterCondition.from_dict(serialized)
    
    assert deserialized == condition
    assert isinstance(deserialized.value, TextValue)


@settings(max_examples=100)
@given(condition=filter_condition_with_list_value())
def test_list_value_filter_condition_round_trip(condition):
    """
    Property 6.5: ListValue FilterCondition 序列化 round-trip
    
    **Validates: Requirements 3.11**
    
    对于使用 ListValue 的 FilterCondition，序列化后反序列化应保持等价。
    """
    serialized = condition.to_dict()
    deserialized = FilterCondition.from_dict(serialized)
    
    assert deserialized == condition
    assert isinstance(deserialized.value, ListValue)


@settings(max_examples=100)
@given(condition=valid_filter_condition_strategy)
def test_serialized_dict_structure(condition):
    """
    Property 6.6: 序列化字典结构验证
    
    **Validates: Requirements 3.11**
    
    序列化后的字典应包含正确的键：field、operator、value。
    """
    serialized = condition.to_dict()
    
    # 验证字典结构
    assert 'field' in serialized
    assert 'operator' in serialized
    assert 'value' in serialized
    
    # 验证字段值类型
    assert isinstance(serialized['field'], str)
    assert isinstance(serialized['operator'], str)
    assert isinstance(serialized['value'], dict)
    
    # 验证 value 字典包含 type 键
    assert 'type' in serialized['value']


@settings(max_examples=100)
@given(condition=valid_filter_condition_strategy)
def test_double_round_trip(condition):
    """
    Property 6.7: 双重 round-trip 验证
    
    **Validates: Requirements 3.11**
    
    对于任意有效的 FilterCondition，执行两次 round-trip 后应仍然等价。
    """
    # 第一次 round-trip
    serialized1 = condition.to_dict()
    deserialized1 = FilterCondition.from_dict(serialized1)
    
    # 第二次 round-trip
    serialized2 = deserialized1.to_dict()
    deserialized2 = FilterCondition.from_dict(serialized2)
    
    # 验证等价性
    assert deserialized2 == condition
    assert serialized1 == serialized2


@settings(max_examples=100)
@given(condition=valid_filter_condition_strategy)
def test_hash_consistency_after_round_trip(condition):
    """
    Property 6.8: round-trip 后哈希值一致性
    
    **Validates: Requirements 3.11**
    
    对于任意有效的 FilterCondition，round-trip 后的哈希值应与原始对象一致。
    """
    serialized = condition.to_dict()
    deserialized = FilterCondition.from_dict(serialized)
    
    assert hash(deserialized) == hash(condition)
