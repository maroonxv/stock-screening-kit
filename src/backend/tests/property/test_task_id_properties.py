"""TaskId UUID 验证属性基测试

Property 3: TaskId UUID 验证一致性
对于任意字符串 s，如果 s 是有效的 UUID 格式，则 TaskId.from_string(s) 应成功构造；
如果 s 不是有效的 UUID 格式，则应抛出 ValueError。
此外，TaskId.generate() 生成的 TaskId 应始终包含有效的 UUID。
"""

import uuid

import pytest
from hypothesis import given, strategies as st, settings

from contexts.intelligence.domain.value_objects.identifiers import TaskId


# === Hypothesis 自定义策略 ===

# 生成有效的 UUID 字符串
valid_uuid_strings = st.builds(lambda: str(uuid.uuid4()))

# 生成无效的 UUID 字符串（非 UUID 格式的文本）
invalid_uuid_strings = st.text(min_size=0, max_size=100).filter(
    lambda s: not _is_valid_uuid(s)
)


def _is_valid_uuid(s: str) -> bool:
    """辅助函数：判断字符串是否为有效的 UUID 格式"""
    try:
        uuid.UUID(s)
        return True
    except (ValueError, AttributeError):
        return False


# Feature: investment-intelligence-context, Property 3: TaskId UUID 验证一致性
# **Validates: Requirements 1.13**


@settings(max_examples=100)
@given(data=st.data())
def test_generate_always_produces_valid_uuid(data):
    """Property 3 (生成有效性): TaskId.generate() 生成的 TaskId 应始终包含有效的 UUID。

    **Validates: Requirements 1.13**
    """
    task_id = TaskId.generate()

    # value 属性应为有效的 UUID 字符串
    assert task_id.value is not None
    parsed = uuid.UUID(task_id.value)
    assert str(parsed) == task_id.value


@settings(max_examples=100)
@given(uuid_str=valid_uuid_strings)
def test_from_string_with_valid_uuid_succeeds(uuid_str):
    """Property 3 (正向): 有效的 UUID 格式字符串应成功构造 TaskId。

    **Validates: Requirements 1.13**
    """
    task_id = TaskId.from_string(uuid_str)
    assert task_id.value == uuid_str


@settings(max_examples=100)
@given(invalid_str=invalid_uuid_strings)
def test_from_string_with_invalid_string_raises_value_error(invalid_str):
    """Property 3 (反向): 非 UUID 格式的字符串应抛出 ValueError。

    **Validates: Requirements 1.13**
    """
    with pytest.raises(ValueError):
        TaskId.from_string(invalid_str)


@settings(max_examples=100)
@given(uuid_str=valid_uuid_strings)
def test_two_task_ids_with_same_uuid_are_equal(uuid_str):
    """Property 3 (等价性): 使用相同 UUID 字符串创建的两个 TaskId 应相等。

    **Validates: Requirements 1.13**
    """
    task_id_1 = TaskId.from_string(uuid_str)
    task_id_2 = TaskId.from_string(uuid_str)
    assert task_id_1 == task_id_2
    assert hash(task_id_1) == hash(task_id_2)


@settings(max_examples=100)
@given(data=st.data())
def test_generate_produces_unique_ids(data):
    """Property 3 (唯一性): TaskId.generate() 连续生成的 ID 应互不相同。

    **Validates: Requirements 1.13**
    """
    task_id_1 = TaskId.generate()
    task_id_2 = TaskId.generate()
    assert task_id_1 != task_id_2
    assert task_id_1.value != task_id_2.value
