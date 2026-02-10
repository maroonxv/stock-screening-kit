"""CredibilityScore 值对象属性基测试

Property 1: CredibilityScore 范围验证
对于任意整数 n，如果 0 <= n <= 100，则 CredibilityScore(n) 应成功构造且 score 属性等于 n；
如果 n < 0 或 n > 100 或 n 不是整数，则 CredibilityScore(n) 应抛出 ValueError。
"""

import pytest
from hypothesis import given, strategies as st, settings

from contexts.intelligence.domain.value_objects.credibility_score import CredibilityScore


# === Hypothesis 自定义策略 ===

valid_credibility_scores = st.builds(
    CredibilityScore, score=st.integers(min_value=0, max_value=100)
)

invalid_credibility_scores = st.one_of(
    st.integers(max_value=-1), st.integers(min_value=101)
)


# Feature: investment-intelligence-context, Property 1: CredibilityScore 范围验证
# **Validates: Requirements 1.4, 1.12**


@settings(max_examples=100)
@given(score=st.integers(min_value=0, max_value=100))
def test_valid_score_constructs_successfully(score):
    """Property 1 (正向): 有效评分 (0-100 整数) 应成功构造且 score 属性等于输入值。

    **Validates: Requirements 1.4, 1.12**
    """
    cs = CredibilityScore(score)
    assert cs.score == score


@settings(max_examples=100)
@given(score=invalid_credibility_scores)
def test_invalid_score_raises_value_error(score):
    """Property 1 (反向 - 越界): 超出 0-100 范围的整数应抛出 ValueError。

    **Validates: Requirements 1.4, 1.12**
    """
    with pytest.raises(ValueError):
        CredibilityScore(score)


@settings(max_examples=100)
@given(
    value=st.one_of(
        st.floats(allow_nan=True, allow_infinity=True),
        st.text(),
        st.none(),
        st.binary(),
        st.lists(st.integers()),
    )
)
def test_non_integer_types_raise_value_error(value):
    """Property 1 (反向 - 类型): 非整数类型 (float, string, None 等) 应抛出 ValueError。

    **Validates: Requirements 1.4, 1.12**
    """
    with pytest.raises((ValueError, TypeError)):
        CredibilityScore(value)


@settings(max_examples=100)
@given(score=st.integers(min_value=0, max_value=100))
def test_level_property_returns_correct_value(score):
    """Property 1 (等级映射): level 属性应根据评分范围返回正确的可信度等级。

    - 80-100: "高可信度"
    - 50-79: "中可信度"
    - 0-49: "低可信度"

    **Validates: Requirements 1.4, 1.12**
    """
    cs = CredibilityScore(score)
    if score >= 80:
        assert cs.level == "高可信度"
    elif score >= 50:
        assert cs.level == "中可信度"
    else:
        assert cs.level == "低可信度"
