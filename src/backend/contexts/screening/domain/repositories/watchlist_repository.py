"""
自选股列表仓储接口定义

IWatchListRepository 定义了自选股列表持久化的抽象接口。
领域层定义接口，基础设施层提供实现。

Requirements:
- 4.4, 4.5: 领域层定义 Repository 接口
- 6.4: 基础设施层实现 WatchListRepository
"""
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.watchlist import WatchList
    from ..value_objects.identifiers import WatchListId


class IWatchListRepository(ABC):
    """
    自选股列表仓储接口
    
    定义自选股列表的 CRUD 操作抽象方法。
    
    实现类应在基础设施层提供，负责：
    - 将 WatchList 领域对象映射到 PO 模型
    - 处理 stocks 列表的 JSONB 序列化
    - 管理数据库事务
    """
    
    @abstractmethod
    def save(self, watchlist: 'WatchList') -> None:
        """
        保存自选股列表
        
        如果列表已存在（相同 ID），则更新；否则创建新记录。
        
        Args:
            watchlist: 要保存的自选股列表
            
        Note:
            - 实现应使用 merge 或 upsert 语义
            - 保存后应刷新会话以确保数据一致性
        """
        pass
    
    @abstractmethod
    def find_by_id(self, watchlist_id: 'WatchListId') -> Optional['WatchList']:
        """
        根据 ID 查找自选股列表
        
        Args:
            watchlist_id: 列表唯一标识符
            
        Returns:
            如果找到返回 WatchList，否则返回 None
        """
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional['WatchList']:
        """
        根据名称查找自选股列表
        
        Args:
            name: 列表名称
            
        Returns:
            如果找到返回 WatchList，否则返回 None
            
        Note:
            - 名称应该是唯一的
            - 用于检查名称重复
        """
        pass
    
    @abstractmethod
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List['WatchList']:
        """
        分页查询所有自选股列表
        
        Args:
            limit: 返回的最大记录数（默认 100）
            offset: 跳过的记录数（默认 0）
            
        Returns:
            自选股列表，按更新时间降序排列
        """
        pass
    
    @abstractmethod
    def delete(self, watchlist_id: 'WatchListId') -> None:
        """
        删除自选股列表
        
        Args:
            watchlist_id: 要删除的列表 ID
            
        Note:
            - 如果列表不存在，应静默处理（不抛出异常）
            - 删除后应刷新会话
        """
        pass
    
    @abstractmethod
    def exists(self, watchlist_id: 'WatchListId') -> bool:
        """
        检查列表是否存在
        
        Args:
            watchlist_id: 列表唯一标识符
            
        Returns:
            如果存在返回 True，否则返回 False
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        获取列表总数
        
        Returns:
            列表总数
        """
        pass
