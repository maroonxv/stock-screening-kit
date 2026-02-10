"""
Property-based tests for FilterGroup serialization round-trip

Feature: stock-screening-platform
Property 7: FilterGroup 序列化 round-trip

**Validates: Requirements 3.12**

Property Description:
对于任意有效的 FilterGroup 对象（包括递归嵌套的子组），调用 to_dict() 然后 from_dict() 
应产生一个与原始对象等价的 FilterGroup，保留所有嵌套结构。
"""
import uuid
import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite

from contexts.screening.domain.models.filter_group import FilterGroup
from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import (
    NumericValue, TextValue, ListValue, RangeValue, TimeSeriesValue
)
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from contexts.screening.domain.enums.enums import LogicalOperator, ValueType


# =============================================================================
# 分类指标字段 (从 test_filter_condition_serialization_properties.py 复用)
# =============================================================================

# 获取所有 NUMERIC 类型的字段
NUMERIC_FIELDS = [f for f in IndicatorField if f.value_type == ValueType.NUMERIC]

# 获取所有 TEXT 类型的字段
TEXT_FIELDS = [f for f in IndicatorField if f.value_type == ValueType.TEXT]


# =============================================================================
# 值生成策略 (从 test_filter_condition_serialization_properties.py 复用)
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
# FilterCondition 生成策略 (从 test_filter_condition_serialization_properties.py 复用)
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
# FilterGroup 生成策略
# =============================================================================

def group_id_strategy():
    """生成有效的 group_id (UUID 字符串)"""
    return st.builds(lambda: str(uuid.uuid4()))


@composite
def logical_operator_strategy(draw):
    """生成逻辑运算符"""
    return draw(st.sampled_from(list(LogicalOperator)))


@composite
def flat_filter_group_strategy(draw):
    """
    生成扁平的 FilterGroup（无嵌套子组）
    
    包含 0-5 个条件，无子组。
    """
    group_id = draw(group_id_strategy())
    operator = draw(logical_operator_strategy())
    conditions = draw(st.lists(
        valid_filter_condition_strategy,
        min_size=0,
        max_size=5
    ))
    return FilterGroup(
        group_id=group_id,
        operator=operator,
        conditions=conditions,
        sub_groups=[]
    )


@composite
def nested_filter_group_strategy(draw, max_depth=3):
    """
    生成递归嵌套的 FilterGroup
    
    Args:
        max_depth: 最大嵌套深度
        
    生成策略:
    - 每层包含 0-3 个条件
    - 每层包含 0-2 个子组（深度递减）
    - 深度为 0 时只生成扁平组
    """
    group_id = draw(group_id_strategy())
    operator = draw(logical_operator_strategy())
    conditions = draw(st.lists(
        valid_filter_condition_strategy,
        min_size=0,
        max_size=3
    ))
    
    if max_depth <= 0:
        # 达到最大深度，不再生成子组
        sub_groups = []
    else:
        # 递归生成子组
        num_sub_groups = draw(st.integers(min_value=0, max_value=2))
        sub_groups = []
        for _ in range(num_sub_groups):
            sub_group = draw(nested_filter_group_strategy(max_depth=max_depth - 1))
            sub_groups.append(sub_group)
    
    return FilterGroup(
        group_id=group_id,
        operator=operator,
        conditions=conditions,
        sub_groups=sub_groups
    )


@composite
def deeply_nested_filter_group_strategy(draw):
    """
    生成深度嵌套的 FilterGroup（用于测试深层嵌套）
    
    固定深度为 3-5 层。
    """
    depth = draw(st.integers(min_value=3, max_value=5))
    return draw(nested_filter_group_strategy(max_depth=depth))


@composite
def filter_group_with_single_condition(draw):
    """生成只包含单个条件的 FilterGroup"""
    group_id = draw(group_id_strategy())
    operator = draw(logical_operator_strategy())
    condition = draw(valid_filter_condition_strategy)
    return FilterGroup(
        group_id=group_id,
        operator=operator,
        conditions=[condition],
        sub_groups=[]
    )


@composite
def filter_group_with_only_sub_groups(draw):
    """生成只包含子组（无直接条件）的 FilterGroup"""
    group_id = draw(group_id_strategy())
    operator = draw(logical_operator_strategy())
    sub_groups = draw(st.lists(
        flat_filter_group_strategy(),
        min_size=1,
        max_size=3
    ))
    return FilterGroup(
        group_id=group_id,
        operator=operator,
        conditions=[],
        sub_groups=sub_groups
    )


@composite
def empty_filter_group_strategy(draw):
    """生成空的 FilterGroup（无条件和子组）"""
    group_id = draw(group_id_strategy())
    operator = draw(logical_operator_strategy())
    return FilterGroup(
        group_id=group_id,
        operator=operator,
        conditions=[],
        sub_groups=[]
    )


# 组合所有有效的 FilterGroup 策略
valid_filter_group_strategy = st.one_of(
    flat_filter_group_strategy(),
    nested_filter_group_strategy(max_depth=3),
    filter_group_with_single_condition(),
    filter_group_with_only_sub_groups(),
    empty_filter_group_strategy()
)


# =============================================================================
# Property 7: FilterGroup 序列化 round-trip
# **Validates: Requirements 3.12**
# =============================================================================

@settings(max_examples=100)
@given(group=valid_filter_group_strategy)
def test_filter_group_serialization_round_trip(group):
    """
    Property 7: FilterGroup 序列化 round-trip
    
    **Validates: Requirements 3.12**
    
    对于任意有效的 FilterGroup 对象（包括递归嵌套的子组），调用 to_dict() 然后 from_dict() 
    应产生一个与原始对象等价的 FilterGroup，保留所有嵌套结构。
    """
    # 序列化为字典
    serialized = group.to_dict()
    
    # 从字典反序列化
    deserialized = FilterGroup.from_dict(serialized)
    
    # 验证等价性
    assert deserialized == group
    assert deserialized.group_id == group.group_id
    assert deserialized.operator == group.operator
    assert len(deserialized.conditions) == len(group.conditions)
    assert len(deserialized.sub_groups) == len(group.sub_groups)


@settings(max_examples=100)
@given(group=flat_filter_group_strategy())
def test_flat_filter_group_round_trip(group):
    """
    Property 7.1: 扁平 FilterGroup 序列化 round-trip
    
    **Validates: Requirements 3.12**
    
    对于无嵌套子组的 FilterGroup，序列化后反序列化应保持等价。
    """
    serialized = group.to_dict()
    deserialized = FilterGroup.from_dict(serialized)
    
    assert deserialized == group
    assert len(deserialized.sub_groups) == 0


@settings(max_examples=100)
@given(group=nested_filter_group_strategy(max_depth=3))
def test_nested_filter_group_round_trip(group):
    """
    Property 7.2: 嵌套 FilterGroup 序列化 round-trip
    
    **Validates: Requirements 3.12**
    
    对于包含递归嵌套子组的 FilterGroup，序列化后反序列化应保持等价，
    包括所有嵌套层级的结构。
    """
    serialized = group.to_dict()
    deserialized = FilterGroup.from_dict(serialized)
    
    assert deserialized == group
    
    # 验证嵌套结构保持一致
    def verify_nested_structure(original, restored):
        assert original.group_id == restored.group_id
        assert original.operator == restored.operator
        assert len(original.conditions) == len(restored.conditions)
        assert len(original.sub_groups) == len(restored.sub_groups)
        
        for orig_cond, rest_cond in zip(original.conditions, restored.conditions):
            assert orig_cond == rest_cond
        
        for orig_sub, rest_sub in zip(original.sub_groups, restored.sub_groups):
            verify_nested_structure(orig_sub, rest_sub)
    
    verify_nested_structure(group, deserialized)


@settings(max_examples=100)
@given(group=deeply_nested_filter_group_strategy())
def test_deeply_nested_filter_group_round_trip(group):
    """
    Property 7.3: 深度嵌套 FilterGroup 序列化 round-trip
    
    **Validates: Requirements 3.12**
    
    对于深度嵌套（3-5层）的 FilterGroup，序列化后反序列化应保持等价。
    """
    serialized = group.to_dict()
    deserialized = FilterGroup.from_dict(serialized)
    
    assert deserialized == group


@settings(max_examples=100)
@given(group=empty_filter_group_strategy())
def test_empty_filter_group_round_trip(group):
    """
    Property 7.4: 空 FilterGroup 序列化 round-trip
    
    **Validates: Requirements 3.12**
    
    对于空的 FilterGroup（无条件和子组），序列化后反序列化应保持等价。
    """
    serialized = group.to_dict()
    deserialized = FilterGroup.from_dict(serialized)
    
    assert deserialized == group
    assert len(deserialized.conditions) == 0
    assert len(deserialized.sub_groups) == 0


@settings(max_examples=100)
@given(group=filter_group_with_only_sub_groups())
def test_filter_group_with_only_sub_groups_round_trip(group):
    """
    Property 7.5: 只含子组的 FilterGroup 序列化 round-trip
    
    **Validates: Requirements 3.12**
    
    对于只包含子组（无直接条件）的 FilterGroup，序列化后反序列化应保持等价。
    """
    serialized = group.to_dict()
    deserialized = FilterGroup.from_dict(serialized)
    
    assert deserialized == group
    assert len(deserialized.conditions) == 0
    assert len(deserialized.sub_groups) > 0


@settings(max_examples=100)
@given(group=valid_filter_group_strategy)
def test_serialized_dict_structure(group):
    """
    Property 7.6: 序列化字典结构验证
    
    **Validates: Requirements 3.12**
    
    序列化后的字典应包含正确的键：group_id、operator、conditions、sub_groups。
    """
    serialized = group.to_dict()
    
    # 验证字典结构
    assert 'group_id' in serialized
    assert 'operator' in serialized
    assert 'conditions' in serialized
    assert 'sub_groups' in serialized
    
    # 验证字段值类型
    assert isinstance(serialized['group_id'], str)
    assert isinstance(serialized['operator'], str)
    assert isinstance(serialized['conditions'], list)
    assert isinstance(serialized['sub_groups'], list)
    
    # 验证 operator 是有效的 LogicalOperator 值
    assert serialized['operator'] in [op.value for op in LogicalOperator]


@settings(max_examples=100)
@given(group=valid_filter_group_strategy)
def test_double_round_trip(group):
    """
    Property 7.7: 双重 round-trip 验证
    
    **Validates: Requirements 3.12**
    
    对于任意有效的 FilterGroup，执行两次 round-trip 后应仍然等价。
    """
    # 第一次 round-trip
    serialized1 = group.to_dict()
    deserialized1 = FilterGroup.from_dict(serialized1)
    
    # 第二次 round-trip
    serialized2 = deserialized1.to_dict()
    deserialized2 = FilterGroup.from_dict(serialized2)
    
    # 验证等价性
    assert deserialized2 == group
    assert serialized1 == serialized2


@settings(max_examples=100)
@given(group=valid_filter_group_strategy)
def test_hash_consistency_after_round_trip(group):
    """
    Property 7.8: round-trip 后哈希值一致性
    
    **Validates: Requirements 3.12**
    
    对于任意有效的 FilterGroup，round-trip 后的哈希值应与原始对象一致。
    """
    serialized = group.to_dict()
    deserialized = FilterGroup.from_dict(serialized)
    
    assert hash(deserialized) == hash(group)


@settings(max_examples=100)
@given(group=nested_filter_group_strategy(max_depth=3))
def test_condition_count_preserved_after_round_trip(group):
    """
    Property 7.9: round-trip 后条件总数保持一致
    
    **Validates: Requirements 3.12**
    
    对于任意有效的 FilterGroup，round-trip 后的条件总数应与原始对象一致。
    """
    original_count = group.count_total_conditions()
    
    serialized = group.to_dict()
    deserialized = FilterGroup.from_dict(serialized)
    
    assert deserialized.count_total_conditions() == original_count


@settings(max_examples=100)
@given(group=nested_filter_group_strategy(max_depth=3))
def test_has_any_condition_preserved_after_round_trip(group):
    """
    Property 7.10: round-trip 后 has_any_condition 结果保持一致
    
    **Validates: Requirements 3.12**
    
    对于任意有效的 FilterGroup，round-trip 后的 has_any_condition() 结果应与原始对象一致。
    """
    original_has_condition = group.has_any_condition()
    
    serialized = group.to_dict()
    deserialized = FilterGroup.from_dict(serialized)
    
    assert deserialized.has_any_condition() == original_has_condition


@settings(max_examples=100)
@given(group=valid_filter_group_strategy)
def test_all_logical_operators_round_trip(group):
    """
    Property 7.11: 所有逻辑运算符的 round-trip 验证
    
    **Validates: Requirements 3.12**
    
    验证 AND、OR、NOT 三种逻辑运算符的 FilterGroup 都能正确序列化和反序列化。
    """
    serialized = group.to_dict()
    deserialized = FilterGroup.from_dict(serialized)
    
    # 验证运算符保持一致
    assert deserialized.operator == group.operator
    assert deserialized.operator.value == serialized['operator']
