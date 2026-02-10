"""
Property-based tests for ComparisonOperator.apply method

Feature: stock-screening-platform
Property 8: ComparisonOperator.apply 与原生运算符一致

**Validates: Requirements 4.6, 4.7, 4.8**
"""
import pytest
from hypothesis import given, strategies as st, settings

from contexts.screening.domain.enums import ComparisonOperator
from contexts.screening.domain.value_objects.indicator_value import (
    NumericValue, TextValue, ListValue, RangeValue
)


# Hypothesis strategies for generating test data
numeric_strategy = st.floats(
    min_value=-1e6, 
    max_value=1e6,
    allow_nan=False, 
    allow_infinity=False
)

text_strategy = st.text(min_size=1, max_size=50)

list_strategy = st.lists(
    st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.text(min_size=1, max_size=20)
    ),
    min_size=1,
    max_size=10
)


@settings(max_examples=20)
@given(actual=numeric_strategy, expected=numeric_strategy)
def test_greater_than_consistency(actual, expected):
    """
    Property 8.1: GREATER_THAN 运算符与原生 > 运算符一致
    
    对于任意数值 actual 和 expected，
    ComparisonOperator.GREATER_THAN.apply(actual, NumericValue(expected))
    应等于 actual > expected
    """
    result = ComparisonOperator.GREATER_THAN.apply(actual, NumericValue(expected))
    assert result == (actual > expected)


@settings(max_examples=20)
@given(actual=numeric_strategy, expected=numeric_strategy)
def test_less_than_consistency(actual, expected):
    """
    Property 8.2: LESS_THAN 运算符与原生 < 运算符一致
    """
    result = ComparisonOperator.LESS_THAN.apply(actual, NumericValue(expected))
    assert result == (actual < expected)


@settings(max_examples=20)
@given(actual=numeric_strategy, expected=numeric_strategy)
def test_equals_consistency(actual, expected):
    """
    Property 8.3: EQUALS 运算符与原生 == 运算符一致
    """
    result = ComparisonOperator.EQUALS.apply(actual, NumericValue(expected))
    assert result == (actual == expected)


@settings(max_examples=20)
@given(actual=numeric_strategy, expected=numeric_strategy)
def test_greater_or_equal_consistency(actual, expected):
    """
    Property 8.4: GREATER_OR_EQUAL 运算符与原生 >= 运算符一致
    """
    result = ComparisonOperator.GREATER_OR_EQUAL.apply(actual, NumericValue(expected))
    assert result == (actual >= expected)


@settings(max_examples=20)
@given(actual=numeric_strategy, expected=numeric_strategy)
def test_less_or_equal_consistency(actual, expected):
    """
    Property 8.5: LESS_OR_EQUAL 运算符与原生 <= 运算符一致
    """
    result = ComparisonOperator.LESS_OR_EQUAL.apply(actual, NumericValue(expected))
    assert result == (actual <= expected)


@settings(max_examples=20)
@given(actual=numeric_strategy, expected=numeric_strategy)
def test_not_equals_consistency(actual, expected):
    """
    Property 8.6: NOT_EQUALS 运算符与原生 != 运算符一致
    """
    result = ComparisonOperator.NOT_EQUALS.apply(actual, NumericValue(expected))
    assert result == (actual != expected)


@settings(max_examples=20)
@given(
    actual=st.one_of(st.integers(min_value=-1000, max_value=1000), text_strategy),
    values=list_strategy
)
def test_in_consistency(actual, values):
    """
    Property 8.7: IN 运算符与原生 in 运算符一致
    
    对于任意值 actual 和列表 values，
    ComparisonOperator.IN.apply(actual, ListValue(values))
    应等于 actual in values
    """
    result = ComparisonOperator.IN.apply(actual, ListValue(values))
    assert result == (actual in values)


@settings(max_examples=20)
@given(
    actual=st.one_of(st.integers(min_value=-1000, max_value=1000), text_strategy),
    values=list_strategy
)
def test_not_in_consistency(actual, values):
    """
    Property 8.8: NOT_IN 运算符与原生 not in 运算符一致
    """
    result = ComparisonOperator.NOT_IN.apply(actual, ListValue(values))
    assert result == (actual not in values)


@settings(max_examples=20)
@given(
    actual=numeric_strategy,
    min_val=numeric_strategy,
    max_val=numeric_strategy
)
def test_between_consistency(actual, min_val, max_val):
    """
    Property 8.9: BETWEEN 运算符与原生区间判断一致
    
    对于任意数值 actual、min_val 和 max_val，
    ComparisonOperator.BETWEEN.apply(actual, RangeValue(min(min_val, max_val), max(min_val, max_val)))
    应等于 min(min_val, max_val) <= actual <= max(min_val, max_val)
    """
    # 确保 min <= max
    min_v = min(min_val, max_val)
    max_v = max(min_val, max_val)
    
    result = ComparisonOperator.BETWEEN.apply(actual, RangeValue(min_v, max_v))
    expected = min_v <= actual <= max_v
    assert result == expected


@settings(max_examples=20)
@given(
    actual=numeric_strategy,
    min_val=numeric_strategy,
    max_val=numeric_strategy
)
def test_not_between_consistency(actual, min_val, max_val):
    """
    Property 8.10: NOT_BETWEEN 运算符与原生区间判断取反一致
    """
    # 确保 min <= max
    min_v = min(min_val, max_val)
    max_v = max(min_val, max_val)
    
    result = ComparisonOperator.NOT_BETWEEN.apply(actual, RangeValue(min_v, max_v))
    expected = not (min_v <= actual <= max_v)
    assert result == expected


@settings(max_examples=20)
@given(actual=text_strategy, expected=text_strategy)
def test_text_equals_consistency(actual, expected):
    """
    Property 8.11: 文本类型的 EQUALS 运算符一致性
    """
    result = ComparisonOperator.EQUALS.apply(actual, TextValue(expected))
    assert result == (actual == expected)


@settings(max_examples=20)
@given(actual=text_strategy, expected=text_strategy)
def test_text_not_equals_consistency(actual, expected):
    """
    Property 8.12: 文本类型的 NOT_EQUALS 运算符一致性
    """
    result = ComparisonOperator.NOT_EQUALS.apply(actual, TextValue(expected))
    assert result == (actual != expected)
