"""
Property-based tests for ScoringConfig weight constraints

Feature: stock-screening-platform
Property 4: ScoringConfig 权重之和约束

**Validates: Requirements 3.8**

Property Description:
对于任意一组 IndicatorField 到 float 的映射 weights，如果 sum(weights.values()) 
不等于 1.0（在浮点精度容差内），则构造 ScoringConfig 应抛出验证错误。
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.enums import NormalizationMethod


# 获取所有可用的指标字段
ALL_INDICATOR_FIELDS = list(IndicatorField)


@composite
def valid_weights_strategy(draw):
    """
    生成权重之和等于 1.0 的有效权重映射
    
    使用 Dirichlet 分布的简化版本：生成随机正数并归一化
    """
    # 随机选择 1-5 个不重复的指标字段
    num_fields = draw(st.integers(min_value=1, max_value=min(5, len(ALL_INDICATOR_FIELDS))))
    fields = draw(st.lists(
        st.sampled_from(ALL_INDICATOR_FIELDS),
        min_size=num_fields,
        max_size=num_fields,
        unique=True
    ))
    
    if len(fields) == 1:
        return {fields[0]: 1.0}
    
    # 生成随机正数权重
    raw_weights = [draw(st.floats(min_value=0.01, max_value=1.0)) for _ in fields]
    total = sum(raw_weights)
    
    # 归一化使总和为 1.0
    normalized = {field: weight / total for field, weight in zip(fields, raw_weights)}
    
    return normalized


@composite
def invalid_weights_strategy(draw):
    """
    生成权重之和不等于 1.0 的无效权重映射
    """
    # 随机选择 1-5 个不重复的指标字段
    num_fields = draw(st.integers(min_value=1, max_value=min(5, len(ALL_INDICATOR_FIELDS))))
    fields = draw(st.lists(
        st.sampled_from(ALL_INDICATOR_FIELDS),
        min_size=num_fields,
        max_size=num_fields,
        unique=True
    ))
    
    # 生成随机权重（不归一化）
    weights = {}
    for field in fields:
        weights[field] = draw(st.floats(min_value=0.01, max_value=0.5))
    
    total = sum(weights.values())
    
    # 确保总和不等于 1.0（超出容差范围）
    assume(abs(total - 1.0) > ScoringConfig.TOLERANCE)
    
    return weights


# =============================================================================
# Property 4: ScoringConfig 权重之和约束
# **Validates: Requirements 3.8**
# =============================================================================

@settings(max_examples=100)
@given(weights=valid_weights_strategy())
def test_valid_weights_sum_to_one_accepted(weights):
    """
    Property 4.1: 权重之和等于 1.0 时应成功构造
    
    **Validates: Requirements 3.8**
    
    对于任意一组指标字段，如果权重之和等于 1.0（在容差范围内），
    则 ScoringConfig 应成功构造
    """
    # 应该成功构造
    config = ScoringConfig(weights=weights)
    
    # 验证权重之和在容差范围内
    total = sum(config.weights.values())
    assert abs(total - 1.0) <= ScoringConfig.TOLERANCE, \
        f"权重之和 {total} 应该在 1.0 的容差范围内"


@settings(max_examples=100)
@given(weights=invalid_weights_strategy())
def test_invalid_weights_sum_raises_error(weights):
    """
    Property 4.2: 权重之和不等于 1.0 时应抛出错误
    
    **Validates: Requirements 3.8**
    
    对于任意一组指标字段，如果权重之和不等于 1.0（超出容差范围），
    则构造 ScoringConfig 应抛出 ValueError
    """
    total = sum(weights.values())
    
    # 应该抛出错误
    with pytest.raises(ValueError, match="权重之和必须等于 1.0"):
        ScoringConfig(weights=weights)


@settings(max_examples=100)
@given(
    weights=valid_weights_strategy(),
    deviation=st.floats(min_value=0.1, max_value=1.0)
)
def test_weights_with_positive_deviation_rejected(weights, deviation):
    """
    Property 4.3: 权重之和大于 1.0 时应抛出错误
    
    **Validates: Requirements 3.8**
    
    对于任意有效权重映射，添加正偏差使总和大于 1.0 后，
    构造应失败
    """
    # 复制权重并添加偏差
    modified_weights = dict(weights)
    first_field = list(modified_weights.keys())[0]
    modified_weights[first_field] += deviation
    
    total = sum(modified_weights.values())
    assume(abs(total - 1.0) > ScoringConfig.TOLERANCE)
    
    with pytest.raises(ValueError, match="权重之和必须等于 1.0"):
        ScoringConfig(weights=modified_weights)


@settings(max_examples=100)
@given(
    weights=valid_weights_strategy(),
    factor=st.floats(min_value=0.1, max_value=0.9)
)
def test_weights_with_negative_deviation_rejected(weights, factor):
    """
    Property 4.4: 权重之和小于 1.0 时应抛出错误
    
    **Validates: Requirements 3.8**
    
    对于任意有效权重映射，缩小权重使总和小于 1.0 后，
    构造应失败
    """
    # 缩小所有权重
    modified_weights = {field: weight * factor for field, weight in weights.items()}
    
    total = sum(modified_weights.values())
    assume(abs(total - 1.0) > ScoringConfig.TOLERANCE)
    
    with pytest.raises(ValueError, match="权重之和必须等于 1.0"):
        ScoringConfig(weights=modified_weights)


@settings(max_examples=100)
@given(
    weights=valid_weights_strategy(),
    normalization=st.sampled_from(list(NormalizationMethod))
)
def test_normalization_method_preserved(weights, normalization):
    """
    Property 4.5: 归一化方法应被正确保存
    
    **Validates: Requirements 3.8**
    
    对于任意有效的 ScoringConfig，归一化方法应该被正确保存和返回
    """
    config = ScoringConfig(weights=weights, normalization_method=normalization)
    
    assert config.normalization_method == normalization


@settings(max_examples=100)
@given(weights=valid_weights_strategy())
def test_weights_immutability(weights):
    """
    Property 4.6: 权重映射应该是不可变的
    
    **Validates: Requirements 3.8**
    
    对于任意 ScoringConfig，修改返回的权重字典不应影响原对象
    """
    config = ScoringConfig(weights=weights)
    
    # 获取权重副本
    returned_weights = config.weights
    original_len = len(returned_weights)
    original_values = dict(returned_weights)
    
    # 尝试修改返回的字典
    for field in ALL_INDICATOR_FIELDS:
        if field not in returned_weights:
            returned_weights[field] = 0.1
            break
    
    # 原对象应该保持不变
    assert len(config.weights) == original_len
    assert config.weights == original_values


@settings(max_examples=100)
@given(weights=valid_weights_strategy())
def test_serialization_round_trip_preserves_weights_sum(weights):
    """
    Property 4.7: 序列化往返应保持权重之和约束
    
    **Validates: Requirements 3.8**
    
    对于任意有效的 ScoringConfig，序列化后再反序列化应保持权重之和等于 1.0
    """
    config1 = ScoringConfig(weights=weights)
    
    # 序列化
    data = config1.to_dict()
    
    # 反序列化
    config2 = ScoringConfig.from_dict(data)
    
    # 权重之和应该仍然等于 1.0
    total = sum(config2.weights.values())
    assert abs(total - 1.0) <= ScoringConfig.TOLERANCE, \
        f"反序列化后权重之和 {total} 应该在 1.0 的容差范围内"
    
    # 两个配置应该相等
    assert config1 == config2


@settings(max_examples=100)
@given(weights=valid_weights_strategy())
def test_get_weight_returns_zero_for_missing_fields(weights):
    """
    Property 4.8: 对于不存在的字段，get_weight 应返回 0.0
    
    **Validates: Requirements 3.8**
    
    对于任意 ScoringConfig 和不在权重映射中的字段，
    get_weight 应返回 0.0
    """
    config = ScoringConfig(weights=weights)
    
    # 找一个不在权重映射中的字段
    for field in ALL_INDICATOR_FIELDS:
        if field not in weights:
            assert config.get_weight(field) == 0.0
            break


@settings(max_examples=100)
@given(weights=valid_weights_strategy())
def test_all_weights_non_negative(weights):
    """
    Property 4.9: 所有权重应该是非负的
    
    **Validates: Requirements 3.8**
    
    对于任意有效的 ScoringConfig，所有权重值都应该 >= 0
    """
    config = ScoringConfig(weights=weights)
    
    for weight in config.weights.values():
        assert weight >= 0.0, f"权重 {weight} 应该是非负的"


@settings(max_examples=100)
@given(
    weights=valid_weights_strategy(),
    negative_weight=st.floats(min_value=-1.0, max_value=-0.01)
)
def test_negative_weight_raises_error(weights, negative_weight):
    """
    Property 4.10: 负权重应抛出错误
    
    **Validates: Requirements 3.8**
    
    对于任意权重映射，如果包含负权重，则构造应失败
    """
    # 将第一个字段的权重设为负数
    modified_weights = dict(weights)
    first_field = list(modified_weights.keys())[0]
    modified_weights[first_field] = negative_weight
    
    # 应该抛出错误（可能是负权重错误或权重之和错误）
    with pytest.raises(ValueError):
        ScoringConfig(weights=modified_weights)


@settings(max_examples=100)
@given(st.data())
def test_empty_weights_raises_error(data):
    """
    Property 4.11: 空权重映射应抛出错误
    
    **Validates: Requirements 3.8**
    
    空的权重映射应该导致构造失败
    """
    with pytest.raises(ValueError, match="权重映射不能为空"):
        ScoringConfig(weights={})
