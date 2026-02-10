"""
标识符值对象定义
"""
import uuid
from typing import Any


class StrategyId:
    """筛选策略标识符值对象"""
    
    def __init__(self, value: str):
        """
        Args:
            value: UUID 字符串
            
        Raises:
            ValueError: 如果 value 不是有效的 UUID 格式
        """
        try:
            # 验证是否为有效的 UUID
            uuid.UUID(value)
        except (ValueError, AttributeError, TypeError) as e:
            raise ValueError(f"无效的 UUID 格式: {value}") from e
        self._value = value
    
    @property
    def value(self) -> str:
        """获取标识符值"""
        return self._value
    
    @classmethod
    def generate(cls) -> 'StrategyId':
        """生成新的策略标识符"""
        return cls(str(uuid.uuid4()))
    
    @classmethod
    def from_string(cls, value: str) -> 'StrategyId':
        """从字符串创建标识符"""
        return cls(value)
    
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, StrategyId) and self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)
    
    def __repr__(self) -> str:
        return f"StrategyId('{self._value}')"
    
    def __str__(self) -> str:
        return self._value


class SessionId:
    """筛选会话标识符值对象"""
    
    def __init__(self, value: str):
        """
        Args:
            value: UUID 字符串
            
        Raises:
            ValueError: 如果 value 不是有效的 UUID 格式
        """
        try:
            # 验证是否为有效的 UUID
            uuid.UUID(value)
        except (ValueError, AttributeError, TypeError) as e:
            raise ValueError(f"无效的 UUID 格式: {value}") from e
        self._value = value
    
    @property
    def value(self) -> str:
        """获取标识符值"""
        return self._value
    
    @classmethod
    def generate(cls) -> 'SessionId':
        """生成新的会话标识符"""
        return cls(str(uuid.uuid4()))
    
    @classmethod
    def from_string(cls, value: str) -> 'SessionId':
        """从字符串创建标识符"""
        return cls(value)
    
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, SessionId) and self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)
    
    def __repr__(self) -> str:
        return f"SessionId('{self._value}')"
    
    def __str__(self) -> str:
        return self._value


class WatchListId:
    """自选股列表标识符值对象"""
    
    def __init__(self, value: str):
        """
        Args:
            value: UUID 字符串
            
        Raises:
            ValueError: 如果 value 不是有效的 UUID 格式
        """
        try:
            # 验证是否为有效的 UUID
            uuid.UUID(value)
        except (ValueError, AttributeError, TypeError) as e:
            raise ValueError(f"无效的 UUID 格式: {value}") from e
        self._value = value
    
    @property
    def value(self) -> str:
        """获取标识符值"""
        return self._value
    
    @classmethod
    def generate(cls) -> 'WatchListId':
        """生成新的自选股列表标识符"""
        return cls(str(uuid.uuid4()))
    
    @classmethod
    def from_string(cls, value: str) -> 'WatchListId':
        """从字符串创建标识符"""
        return cls(value)
    
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, WatchListId) and self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)
    
    def __repr__(self) -> str:
        return f"WatchListId('{self._value}')"
    
    def __str__(self) -> str:
        return self._value
