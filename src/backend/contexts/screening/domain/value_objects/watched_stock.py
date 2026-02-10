"""
自选股值对象定义

WatchedStock 是一个不可变的值对象，表示用户关注的股票。
包含股票代码、名称、添加时间、备注和标签。

Requirements:
- 3.6: WatchedStock 值对象，包含 stock_code、stock_name、added_at、note、tags
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# 导入 StockCode
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from shared_kernel.value_objects.stock_code import StockCode


class WatchedStock:
    """
    自选股值对象
    
    表示用户关注的股票，包含：
    - stock_code: 股票代码（StockCode）
    - stock_name: 股票名称
    - added_at: 添加时间
    - note: 备注（可选）
    - tags: 标签列表（可选）
    """
    
    def __init__(
        self,
        stock_code: StockCode,
        stock_name: str,
        added_at: Optional[datetime] = None,
        note: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        """
        构造自选股
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            added_at: 添加时间（默认为当前时间）
            note: 备注
            tags: 标签列表
            
        Raises:
            ValueError: 如果股票名称为空
        """
        if not stock_name or not stock_name.strip():
            raise ValueError("股票名称不能为空")
        
        self._stock_code = stock_code
        self._stock_name = stock_name
        self._added_at = added_at or datetime.now(timezone.utc)
        self._note = note
        self._tags = list(tags) if tags else None
    
    @property
    def stock_code(self) -> StockCode:
        """获取股票代码"""
        return self._stock_code
    
    @property
    def stock_name(self) -> str:
        """获取股票名称"""
        return self._stock_name
    
    @property
    def added_at(self) -> datetime:
        """获取添加时间"""
        return self._added_at
    
    @property
    def note(self) -> Optional[str]:
        """获取备注"""
        return self._note
    
    @property
    def tags(self) -> Optional[List[str]]:
        """获取标签列表（返回副本以保证不可变性）"""
        return list(self._tags) if self._tags else None
    
    def with_note(self, note: Optional[str]) -> 'WatchedStock':
        """
        创建带有新备注的副本
        
        Args:
            note: 新备注
            
        Returns:
            新的 WatchedStock 实例
        """
        return WatchedStock(
            stock_code=self._stock_code,
            stock_name=self._stock_name,
            added_at=self._added_at,
            note=note,
            tags=self._tags
        )
    
    def with_tags(self, tags: Optional[List[str]]) -> 'WatchedStock':
        """
        创建带有新标签的副本
        
        Args:
            tags: 新标签列表
            
        Returns:
            新的 WatchedStock 实例
        """
        return WatchedStock(
            stock_code=self._stock_code,
            stock_name=self._stock_name,
            added_at=self._added_at,
            note=self._note,
            tags=tags
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'stock_code': self._stock_code.code,
            'stock_name': self._stock_name,
            'added_at': self._added_at.isoformat(),
            'note': self._note,
            'tags': self._tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WatchedStock':
        """
        从字典反序列化
        
        Args:
            data: 包含所有属性的字典
            
        Returns:
            WatchedStock 实例
        """
        stock_code = StockCode(data['stock_code'])
        
        added_at_str = data.get('added_at')
        added_at = datetime.fromisoformat(added_at_str) if added_at_str else None
        
        return cls(
            stock_code=stock_code,
            stock_name=data['stock_name'],
            added_at=added_at,
            note=data.get('note'),
            tags=data.get('tags')
        )
    
    def __eq__(self, other: object) -> bool:
        """判断两个 WatchedStock 是否相等"""
        if not isinstance(other, WatchedStock):
            return False
        return (
            self._stock_code == other._stock_code and
            self._stock_name == other._stock_name and
            self._added_at == other._added_at and
            self._note == other._note and
            self._tags == other._tags
        )
    
    def __hash__(self) -> int:
        """计算哈希值"""
        return hash((
            self._stock_code,
            self._stock_name,
            self._added_at
        ))
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return (
            f"WatchedStock(stock_code={self._stock_code}, "
            f"stock_name='{self._stock_name}', "
            f"added_at={self._added_at.isoformat()})"
        )
