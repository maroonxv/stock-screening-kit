"""
筛选会话仓储接口定义

IScreeningSessionRepository 定义了筛选会话持久化的抽象接口。
领域层定义接口，基础设施层提供实现。

Requirements:
- 4.4, 4.5: 领域层定义 Repository 接口
- 6.3: 基础设施层实现 ScreeningSessionRepository
"""
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.screening_session import ScreeningSession
    from ..value_objects.identifiers import SessionId, StrategyId


class IScreeningSessionRepository(ABC):
    """
    筛选会话仓储接口
    
    定义筛选会话的持久化操作抽象方法。
    
    实现类应在基础设施层提供，负责：
    - 将 ScreeningSession 领域对象映射到 PO 模型
    - 处理 top_stocks、other_stock_codes 的 JSONB 序列化
    - 处理 filters_snapshot、scoring_config_snapshot 的 JSONB 序列化
    - 管理数据库事务
    """
    
    @abstractmethod
    def save(self, session: 'ScreeningSession') -> None:
        """
        保存筛选会话
        
        创建新的筛选会话记录。
        
        Args:
            session: 要保存的筛选会话
            
        Note:
            - 会话通常只创建不更新
            - 保存后应刷新会话以确保数据一致性
        """
        pass
    
    @abstractmethod
    def find_by_id(self, session_id: 'SessionId') -> Optional['ScreeningSession']:
        """
        根据 ID 查找筛选会话
        
        Args:
            session_id: 会话唯一标识符
            
        Returns:
            如果找到返回 ScreeningSession，否则返回 None
        """
        pass
    
    @abstractmethod
    def find_by_strategy_id(
        self,
        strategy_id: 'StrategyId',
        limit: int = 10
    ) -> List['ScreeningSession']:
        """
        根据策略 ID 查找筛选会话
        
        Args:
            strategy_id: 策略唯一标识符
            limit: 返回的最大记录数（默认 10）
            
        Returns:
            该策略的筛选会话列表，按执行时间降序排列
        """
        pass
    
    @abstractmethod
    def find_recent(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List['ScreeningSession']:
        """
        查询最近的筛选会话
        
        Args:
            limit: 返回的最大记录数（默认 20）
            offset: 跳过的记录数（默认 0）
            
        Returns:
            筛选会话列表，按执行时间降序排列
        """
        pass
    
    @abstractmethod
    def delete(self, session_id: 'SessionId') -> None:
        """
        删除筛选会话
        
        Args:
            session_id: 要删除的会话 ID
            
        Note:
            - 如果会话不存在，应静默处理（不抛出异常）
            - 删除后应刷新会话
        """
        pass
    
    @abstractmethod
    def delete_by_strategy_id(self, strategy_id: 'StrategyId') -> int:
        """
        删除指定策略的所有会话
        
        Args:
            strategy_id: 策略唯一标识符
            
        Returns:
            删除的会话数量
            
        Note:
            - 用于删除策略时级联删除相关会话
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        获取会话总数
        
        Returns:
            会话总数
        """
        pass
    
    @abstractmethod
    def count_by_strategy_id(self, strategy_id: 'StrategyId') -> int:
        """
        获取指定策略的会话数量
        
        Args:
            strategy_id: 策略唯一标识符
            
        Returns:
            该策略的会话数量
        """
        pass
