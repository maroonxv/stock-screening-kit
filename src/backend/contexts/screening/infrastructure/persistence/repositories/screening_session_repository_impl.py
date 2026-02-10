"""
ScreeningSessionRepository 实现

实现 IScreeningSessionRepository 接口，负责 ScreeningSession 聚合根的持久化。
处理 PO ↔ 领域对象映射，包含 top_stocks、other_stock_codes、filters_snapshot、
scoring_config_snapshot 的 JSONB 序列化/反序列化。

Requirements:
- 6.3: 实现 ScreeningSessionRepository，在 ScreeningSession 领域对象和 PO 模型之间进行映射
"""
from typing import List, Optional

from ..models.screening_session_po import ScreeningSessionPO
from ....domain.repositories.screening_session_repository import IScreeningSessionRepository
from ....domain.models.screening_session import ScreeningSession
from ....domain.models.filter_group import FilterGroup
from ....domain.value_objects.scoring_config import ScoringConfig
from ....domain.value_objects.scored_stock import ScoredStock
from ....domain.value_objects.identifiers import SessionId, StrategyId


class ScreeningSessionRepositoryImpl(IScreeningSessionRepository):
    """
    筛选会话仓储实现
    
    使用 SQLAlchemy session 进行数据库操作。
    负责 ScreeningSession 领域对象与 ScreeningSessionPO 持久化对象之间的映射。
    
    映射说明:
    - session_id (SessionId) <-> id (String)
    - strategy_id (StrategyId) <-> strategy_id (String)
    - top_stocks (List[ScoredStock]) <-> top_stocks (JSONB) - 使用 to_dict/from_dict 序列化
    - other_stock_codes (List[str]) <-> other_stock_codes (JSONB)
    - filters_snapshot (FilterGroup) <-> filters_snapshot (JSONB) - 使用 to_dict/from_dict 序列化
    - scoring_config_snapshot (ScoringConfig) <-> scoring_config_snapshot (JSONB) - 使用 to_dict/from_dict 序列化
    """
    
    def __init__(self, session):
        """
        初始化仓储
        
        Args:
            session: SQLAlchemy 数据库会话
        """
        self._session = session
    
    def save(self, screening_session: ScreeningSession) -> None:
        """
        保存筛选会话
        
        创建新的筛选会话记录。使用 merge 实现 upsert 语义。
        
        Args:
            screening_session: 要保存的筛选会话
        """
        po = self._to_po(screening_session)
        self._session.merge(po)
        self._session.flush()
    
    def find_by_id(self, session_id: SessionId) -> Optional[ScreeningSession]:
        """
        根据 ID 查找筛选会话
        
        Args:
            session_id: 会话唯一标识符
            
        Returns:
            如果找到返回 ScreeningSession，否则返回 None
        """
        po = self._session.query(ScreeningSessionPO).get(session_id.value)
        return self._to_domain(po) if po else None
    
    def find_by_strategy_id(
        self,
        strategy_id: StrategyId,
        limit: int = 10
    ) -> List[ScreeningSession]:
        """
        根据策略 ID 查找筛选会话
        
        Args:
            strategy_id: 策略唯一标识符
            limit: 返回的最大记录数（默认 10）
            
        Returns:
            该策略的筛选会话列表，按执行时间降序排列
        """
        pos = (
            self._session.query(ScreeningSessionPO)
            .filter(ScreeningSessionPO.strategy_id == strategy_id.value)
            .order_by(ScreeningSessionPO.executed_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(po) for po in pos]
    
    def find_recent(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List[ScreeningSession]:
        """
        查询最近的筛选会话
        
        Args:
            limit: 返回的最大记录数（默认 20）
            offset: 跳过的记录数（默认 0）
            
        Returns:
            筛选会话列表，按执行时间降序排列
        """
        pos = (
            self._session.query(ScreeningSessionPO)
            .order_by(ScreeningSessionPO.executed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_domain(po) for po in pos]
    
    def delete(self, session_id: SessionId) -> None:
        """
        删除筛选会话
        
        Args:
            session_id: 要删除的会话 ID
            
        Note:
            如果会话不存在，静默处理（不抛出异常）
        """
        po = self._session.query(ScreeningSessionPO).get(session_id.value)
        if po:
            self._session.delete(po)
            self._session.flush()
    
    def delete_by_strategy_id(self, strategy_id: StrategyId) -> int:
        """
        删除指定策略的所有会话
        
        Args:
            strategy_id: 策略唯一标识符
            
        Returns:
            删除的会话数量
        """
        deleted_count = (
            self._session.query(ScreeningSessionPO)
            .filter(ScreeningSessionPO.strategy_id == strategy_id.value)
            .delete(synchronize_session='fetch')
        )
        self._session.flush()
        return deleted_count
    
    def count(self) -> int:
        """
        获取会话总数
        
        Returns:
            会话总数
        """
        return self._session.query(ScreeningSessionPO).count()
    
    def count_by_strategy_id(self, strategy_id: StrategyId) -> int:
        """
        获取指定策略的会话数量
        
        Args:
            strategy_id: 策略唯一标识符
            
        Returns:
            该策略的会话数量
        """
        return (
            self._session.query(ScreeningSessionPO)
            .filter(ScreeningSessionPO.strategy_id == strategy_id.value)
            .count()
        )
    
    # ==================== 私有映射方法 ====================
    
    def _to_po(self, screening_session: ScreeningSession) -> ScreeningSessionPO:
        """
        将领域对象转换为持久化对象
        
        Args:
            screening_session: ScreeningSession 领域对象
            
        Returns:
            ScreeningSessionPO 持久化对象
            
        Note:
            - top_stocks 使用 to_dict() 序列化为 JSONB
            - other_stock_codes 直接存储为 JSONB 数组
            - filters_snapshot 使用 to_dict() 序列化为 JSONB
            - scoring_config_snapshot 使用 to_dict() 序列化为 JSONB
        """
        return ScreeningSessionPO(
            id=screening_session.session_id.value,
            strategy_id=screening_session.strategy_id.value,
            strategy_name=screening_session.strategy_name,
            executed_at=screening_session.executed_at,
            total_scanned=screening_session.total_scanned,
            execution_time=screening_session.execution_time,
            top_stocks=[stock.to_dict() for stock in screening_session.top_stocks],
            other_stock_codes=screening_session.other_stock_codes,
            filters_snapshot=screening_session.filters_snapshot.to_dict(),
            scoring_config_snapshot=screening_session.scoring_config_snapshot.to_dict()
        )
    
    def _to_domain(self, po: ScreeningSessionPO) -> ScreeningSession:
        """
        将持久化对象转换为领域对象
        
        Args:
            po: ScreeningSessionPO 持久化对象
            
        Returns:
            ScreeningSession 领域对象
            
        Note:
            - top_stocks JSONB 使用 ScoredStock.from_dict() 反序列化
            - other_stock_codes 从 JSONB 数组直接读取
            - filters_snapshot JSONB 使用 FilterGroup.from_dict() 反序列化
            - scoring_config_snapshot JSONB 使用 ScoringConfig.from_dict() 反序列化
        """
        top_stocks = [
            ScoredStock.from_dict(stock_data)
            for stock_data in (po.top_stocks or [])
        ]
        
        return ScreeningSession(
            session_id=SessionId.from_string(po.id),
            strategy_id=StrategyId.from_string(po.strategy_id),
            strategy_name=po.strategy_name,
            executed_at=po.executed_at,
            total_scanned=po.total_scanned,
            execution_time=po.execution_time,
            top_stocks=top_stocks,
            other_stock_codes=po.other_stock_codes or [],
            filters_snapshot=FilterGroup.from_dict(po.filters_snapshot),
            scoring_config_snapshot=ScoringConfig.from_dict(po.scoring_config_snapshot)
        )
