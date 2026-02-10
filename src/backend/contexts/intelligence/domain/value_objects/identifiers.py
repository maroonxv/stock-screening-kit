"""标识符值对象模块

包含调研任务相关的标识符值对象。
"""

import uuid


class TaskId:
    """调研任务唯一标识符

    使用 UUID 格式确保全局唯一性。提供工厂方法用于生成新 ID 和从字符串解析。
    """

    def __init__(self, value: str):
        """初始化 TaskId

        Args:
            value: UUID 格式的字符串

        Raises:
            ValueError: 如果 value 不是有效的 UUID 格式
        """
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValueError(f"无效的 TaskId 格式: {value}")
        self._value = value

    @classmethod
    def generate(cls) -> "TaskId":
        """生成一个新的随机 TaskId

        Returns:
            包含新生成 UUID 的 TaskId 实例
        """
        return cls(str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> "TaskId":
        """从字符串创建 TaskId

        Args:
            value: UUID 格式的字符串

        Returns:
            TaskId 实例

        Raises:
            ValueError: 如果 value 不是有效的 UUID 格式
        """
        return cls(value)

    @property
    def value(self) -> str:
        """获取 TaskId 的字符串值"""
        return self._value

    def __eq__(self, other):
        """判断两个 TaskId 是否相等"""
        return isinstance(other, TaskId) and self._value == other._value

    def __hash__(self):
        """返回 TaskId 的哈希值，支持在集合和字典中使用"""
        return hash(self._value)

    def __repr__(self):
        """返回 TaskId 的字符串表示"""
        return f"TaskId('{self._value}')"
