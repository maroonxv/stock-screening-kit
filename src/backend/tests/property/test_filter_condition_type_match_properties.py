"""
Property-based tests for FilterCondition type matching constraints

Feature: stock-screening-platform
Property 5: FilterCondition 类型匹配约束

**Validates: Requirements 3.9**

Property Description:
对于任意 IndicatorField 和 IndicatorValue 的组合，如果 field 的 value_type 是 NUMERIC 
但 value 是 TextValue 或 ListValue，则构造 FilterCondition 应抛出 TypeError。
反之，如果 field 的 value_type 是 TEXT 但 value 是 NumericValue 或 RangeValue，
也应抛出 TypeError。
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
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


# 适用于 NUMERIC 字段的值类型
numeric_compatible_values = st.one_of(
    numeric_value_strategy(),
    range_value_strategy(),
    time_series_value_strategy()
)

# 适用于 TEXT 字段的值类型
text_compatible_values = st.one_of(
    text_value_strategy(),
    list_value_strategy()
)

# 不适用于 NUMERIC 字段的值类型（TEXT 类型值）
numeric_incompatible_values = st.one_of(
    text_value_strategy(),
    list_value_strategy()
)

# 不适用于 TEXT 字段的值类型（NUMERIC 类型值）
text_incompatible_values = st.one_of(
    numeric_value_strategy(),
    range_value_strategy()
)


# =============================================================================
# 运算符策略
# =============================================================================

# 适用于 NumericValue 的运算符
numeric_operators = st.sampled_from([
    ComparisonOperator.GREATER_THAN,
    ComparisonOperator.LESS_THAN,
    ComparisonOperator.EQUALS,
    ComparisonOperator.GREATER_OR_EQUAL,
    ComparisonOperator.LESS_OR_EQUAL,
    ComparisonOperator.NOT_EQUALS
])

# 适用于 TextValue 的运算符
text_operators = st.sampled_from([
    ComparisonOperator.EQUALS,
    ComparisonOperator.NOT_EQUALS
])


# =============================================================================
# Property 5: FilterCondition 类型匹配约束
# **Validates: Requirements 3.9**
# =============================================================================

@settings(max_examples=100)
@given(
    field=st.sampled_from(NUMERIC_FIELDS),
    value=text_value_strategy()
)
def test_numeric_field_with_text_value_raises_type_error(field, value):
    """
    Property 5.1: NUMERIC 字段配合 TextValue 应抛出 TypeError
    
    **Validates: Requirements 3.9**
    
    对于任意 NUMERIC 类型的 IndicatorField，如果使用 TextValue 构造 FilterCondition，
    应抛出 TypeError
    """
    with pytest.raises(TypeError, match="需要数值类型的值"):
        FilterCondition(
            field=field,
            operator=ComparisonOperator.EQUALS,
            value=value
        )


@settings(max_examples=100)
@given(
    field=st.sampled_from(NUMERIC_FIELDS),
    value=list_value_strategy()
)
def test_numeric_field_with_list_value_raises_type_error(field, value):
    """
    Property 5.2: NUMERIC 字段配合 ListValue 应抛出 TypeError
    
    **Validates: Requirements 3.9**
    
    对于任意 NUMERIC 类型的 IndicatorField，如果使用 ListValue 构造 FilterCondition，
    应抛出 TypeError
    """
    with pytest.raises(TypeError, match="需要数值类型的值"):
        FilterCondition(
            field=field,
            operator=ComparisonOperator.IN,
            value=value
        )


@settings(max_examples=100)
@given(
    field=st.sampled_from(TEXT_FIELDS),
    value=numeric_value_strategy()
)
def test_text_field_with_numeric_value_raises_type_error(field, value):
    """
    Property 5.3: TEXT 字段配合 NumericValue 应抛出 TypeError
    
    **Validates: Requirements 3.9**
    
    对于任意 TEXT 类型的 IndicatorField，如果使用 NumericValue 构造 FilterCondition，
    应抛出 TypeError
    """
    with pytest.raises(TypeError, match="需要文本类型的值"):
        FilterCondition(
            field=field,
            operator=ComparisonOperator.EQUALS,
            value=value
        )


@settings(max_examples=100)
@given(
    field=st.sampled_from(TEXT_FIELDS),
    value=range_value_strategy()
)
def test_text_field_with_range_value_raises_type_error(field, value):
    """
    Property 5.4: TEXT 字段配合 RangeValue 应抛出 TypeError
    
    **Validates: Requirements 3.9**
    
    对于任意 TEXT 类型的 IndicatorField，如果使用 RangeValue 构造 FilterCondition，
    应抛出 TypeError
    """
    with pytest.raises(TypeError, match="需要文本类型的值"):
        FilterCondition(
            field=field,
            operator=ComparisonOperator.BETWEEN,
            value=value
        )


@settings(max_examples=100)
@given(
    field=st.sampled_from(NUMERIC_FIELDS),
    value=numeric_value_strategy(),
    operator=numeric_operators
)
def test_numeric_field_with_numeric_value_accepted(field, value, operator):
    """
    Property 5.5: NUMERIC 字段配合 NumericValue 应成功构造
    
    **Validates: Requirements 3.9**
    
    对于任意 NUMERIC 类型的 IndicatorField，使用 NumericValue 和兼容运算符
    构造 FilterCondition 应成功
    """
    condition = FilterCondition(
        field=field,
        operator=operator,
        value=value
    )
    
    assert condition.field == field
    assert condition.operator == operator
    assert condition.value.to_dict() == value.to_dict()


@settings(max_examples=100)
@given(
    field=st.sampled_from(NUMERIC_FIELDS),
    value=range_value_strategy()
)
def test_numeric_field_with_range_value_accepted(field, value):
    """
    Property 5.6: NUMERIC 字段配合 RangeValue 应成功构造
    
    **Validates: Requirements 3.9**
    
    对于任意 NUMERIC 类型的 IndicatorField，使用 RangeValue 和 BETWEEN 运算符
    构造 FilterCondition 应成功
    """
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.BETWEEN,
        value=value
    )
    
    assert condition.field == field
    assert condition.operator == ComparisonOperator.BETWEEN
    assert condition.value.to_dict() == value.to_dict()


@settings(max_examples=100)
@given(
    field=st.sampled_from(NUMERIC_FIELDS),
    value=time_series_value_strategy()
)
def test_numeric_field_with_time_series_value_accepted(field, value):
    """
    Property 5.7: NUMERIC 字段配合 TimeSeriesValue 应成功构造
    
    **Validates: Requirements 3.9**
    
    对于任意 NUMERIC 类型的 IndicatorField，使用 TimeSeriesValue 
    构造 FilterCondition 应成功
    """
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.EQUALS,
        value=value
    )
    
    assert condition.field == field
    assert condition.value.to_dict() == value.to_dict()


@settings(max_examples=100)
@given(
    field=st.sampled_from(TEXT_FIELDS),
    value=text_value_strategy(),
    operator=text_operators
)
def test_text_field_with_text_value_accepted(field, value, operator):
    """
    Property 5.8: TEXT 字段配合 TextValue 应成功构造
    
    **Validates: Requirements 3.9**
    
    对于任意 TEXT 类型的 IndicatorField，使用 TextValue 和兼容运算符
    构造 FilterCondition 应成功
    """
    condition = FilterCondition(
        field=field,
        operator=operator,
        value=value
    )
    
    assert condition.field == field
    assert condition.operator == operator
    assert condition.value.to_dict() == value.to_dict()


@settings(max_examples=100)
@given(
    field=st.sampled_from(TEXT_FIELDS),
    value=list_value_strategy()
)
def test_text_field_with_list_value_accepted(field, value):
    """
    Property 5.9: TEXT 字段配合 ListValue 应成功构造
    
    **Validates: Requirements 3.9**
    
    对于任意 TEXT 类型的 IndicatorField，使用 ListValue 和 IN 运算符
    构造 FilterCondition 应成功
    """
    condition = FilterCondition(
        field=field,
        operator=ComparisonOperator.IN,
        value=value
    )
    
    assert condition.field == field
    assert condition.operator == ComparisonOperator.IN
    assert condition.value.to_dict() == value.to_dict()


@settings(max_examples=100)
@given(
    field=st.sampled_from(NUMERIC_FIELDS),
    value=numeric_incompatible_values
)
def test_numeric_field_rejects_all_text_type_values(field, value):
    """
    Property 5.10: NUMERIC 字段应拒绝所有文本类型值
    
    **Validates: Requirements 3.9**
    
    对于任意 NUMERIC 类型的 IndicatorField，使用任何文本类型值
    （TextValue 或 ListValue）构造 FilterCondition 应抛出 TypeError
    """
    with pytest.raises(TypeError, match="需要数值类型的值"):
        FilterCondition(
            field=field,
            operator=ComparisonOperator.EQUALS,
            value=value
        )


@settings(max_examples=100)
@given(
    field=st.sampled_from(TEXT_FIELDS),
    value=text_incompatible_values
)
def test_text_field_rejects_all_numeric_type_values(field, value):
    """
    Property 5.11: TEXT 字段应拒绝所有数值类型值
    
    **Validates: Requirements 3.9**
    
    对于任意 TEXT 类型的 IndicatorField，使用任何数值类型值
    （NumericValue 或 RangeValue）构造 FilterCondition 应抛出 TypeError
    """
    with pytest.raises(TypeError, match="需要文本类型的值"):
        FilterCondition(
            field=field,
            operator=ComparisonOperator.EQUALS,
            value=value
        )


@settings(max_examples=100)
@given(
    field=st.sampled_from(NUMERIC_FIELDS),
    value=numeric_compatible_values
)
def test_numeric_field_accepts_all_numeric_type_values(field, value):
    """
    Property 5.12: NUMERIC 字段应接受所有数值类型值
    
    **Validates: Requirements 3.9**
    
    对于任意 NUMERIC 类型的 IndicatorField，使用任何数值类型值
    （NumericValue、RangeValue 或 TimeSeriesValue）构造 FilterCondition 应成功
    """
    # 选择合适的运算符
    if isinstance(value, RangeValue):
        operator = ComparisonOperator.BETWEEN
    else:
        operator = ComparisonOperator.EQUALS
    
    condition = FilterCondition(
        field=field,
        operator=operator,
        value=value
    )
    
    assert condition.field == field
    assert condition.value.to_dict() == value.to_dict()


@settings(max_examples=100)
@given(
    field=st.sampled_from(TEXT_FIELDS),
    value=text_compatible_values
)
def test_text_field_accepts_all_text_type_values(field, value):
    """
    Property 5.13: TEXT 字段应接受所有文本类型值
    
    **Validates: Requirements 3.9**
    
    对于任意 TEXT 类型的 IndicatorField，使用任何文本类型值
    （TextValue 或 ListValue）构造 FilterCondition 应成功
    """
    # 选择合适的运算符
    if isinstance(value, ListValue):
        operator = ComparisonOperator.IN
    else:
        operator = ComparisonOperator.EQUALS
    
    condition = FilterCondition(
        field=field,
        operator=operator,
        value=value
    )
    
    assert condition.field == field
    assert condition.value.to_dict() == value.to_dict()
