"""
筛选策略仓储接口定义

IScreeningStrategyRepository 定义了筛选策略持久化的抽象接口。
领域层定义接口，基础设施层提供实现。

Requirements:
- 4.4, 4.5: 领域层定义 Repository 接口
- 6.2: 基础设施层实现 ScreeningStrategyRepository
"""
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.screening_strategy import ScreeningStrategy
    from ..value_objects.identifiers import StrategyId


class IScreeningStrategyRepository(ABC):
    """
    筛选策略仓储接口
    
    定义筛选策略的 CRUD 操作抽象方法。
    
    实现类应在基础设施层提供，负责：
    - 将 ScreeningStrategy 领域对象映射到 PO 模型
    - 处理 FilterGroup 和 ScoringConfig 的 JSONB 序列化
    - 管理数据库事务
    """
    
    @abstractmethod
    def save(self, strategy: 'ScreeningStrategy') -> None:
        """
        保存筛选策略
        
        如果策略已存在（相同 ID），则更新；否则创建新记录。
        
        Args:
            strategy: 要保存的筛选策略
            
        Note:
            - 实现应使用 merge 或 upsert 语义
            - 保存后应刷新会话以确保数据一致性
        """
        pass
    
    @abstractmethod
    def find_by_id(self, strategy_id: 'StrategyId') -> Optional['ScreeningStrategy']:
        """
        根据 ID 查找筛选策略
        
        Args:
            strategy_id: 策略唯一标识符
            
        Returns:
            如果找到返回 ScreeningStrategy，否则返回 None
        """
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional['ScreeningStrategy']:
        """
        根据名称查找筛选策略
        
        Args:
            name: 策略名称
            
        Returns:
            如果找到返回 ScreeningStrategy，否则返回 None
            
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
    ) -> List['ScreeningStrategy']:
        """
        分页查询所有筛选策略
        
        Args:
            limit: 返回的最大记录数（默认 100）
            offset: 跳过的记录数（默认 0）
            
        Returns:
            筛选策略列表，按更新时间降序排列
        """
        pass
    
    @abstractmethod
    def delete(self, strategy_id: 'StrategyId') -> None:
        """
        删除筛选策略
        
        Args:
            strategy_id: 要删除的策略 ID
            
        Note:
            - 如果策略不存在，应静默处理（不抛出异常）
            - 删除后应刷新会话
        """
        pass
    
    @abstractmethod
    def exists(self, strategy_id: 'StrategyId') -> bool:
        """
        检查策略是否存在
        
        Args:
            strategy_id: 策略唯一标识符
            
        Returns:
            如果存在返回 True，否则返回 False
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        获取策略总数
        
        Returns:
            策略总数
        """
        pass
