"""
会话相关 DTO 类

包含筛选会话的响应 DTO：
- SessionResponse: 会话响应

Requirements:
- 8.10: 实现 DTO 类用于请求验证和响应格式化
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.models.screening_session import ScreeningSession

from .strategy_dto import ScoredStockResponse


@dataclass
class SessionResponse:
    """
    会话响应 DTO
    
    用于将 ScreeningSession 领域对象转换为 API 响应格式。
    
    Attributes:
        session_id: 会话唯一标识符
        strategy_id: 策略ID
        strategy_name: 策略名称
        executed_at: 执行时间
        total_scanned: 扫描的股票总数
        matched_count: 匹配的股票数量
        match_rate: 匹配率
        execution_time: 执行耗时（秒）
        top_stocks: 前N名股票列表
        other_stock_codes: 其他匹配股票代码列表
        filters_snapshot: 筛选条件快照
        scoring_config_snapshot: 评分配置快照
    """
    session_id: str
    strategy_id: str
    strategy_name: str
    executed_at: str
    total_scanned: int
    matched_count: int
    match_rate: float
    execution_time: float
    top_stocks: List[ScoredStockResponse]
    other_stock_codes: List[str]
    filters_snapshot: Dict[str, Any]
    scoring_config_snapshot: Dict[str, Any]
    
    @classmethod
    def from_domain(cls, session: 'ScreeningSession') -> 'SessionResponse':
        """
        从领域对象创建响应 DTO
        
        Args:
            session: ScreeningSession 领域对象
            
        Returns:
            SessionResponse 实例
        """
        top_stocks = [
            ScoredStockResponse.from_domain(stock)
            for stock in session.top_stocks
        ]
        
        return cls(
            session_id=session.session_id.value,
            strategy_id=session.strategy_id.value,
            strategy_name=session.strategy_name,
            executed_at=session.executed_at.isoformat(),
            total_scanned=session.total_scanned,
            matched_count=session.matched_count,
            match_rate=session.match_rate,
            execution_time=session.execution_time,
            top_stocks=top_stocks,
            other_stock_codes=session.other_stock_codes,
            filters_snapshot=session.filters_snapshot.to_dict(),
            scoring_config_snapshot=session.scoring_config_snapshot.to_dict()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'session_id': self.session_id,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_name,
            'executed_at': self.executed_at,
            'total_scanned': self.total_scanned,
            'matched_count': self.matched_count,
            'match_rate': self.match_rate,
            'execution_time': self.execution_time,
            'top_stocks': [stock.to_dict() for stock in self.top_stocks],
            'other_stock_codes': self.other_stock_codes,
            'filters_snapshot': self.filters_snapshot,
            'scoring_config_snapshot': self.scoring_config_snapshot
        }


@dataclass
class SessionSummaryResponse:
    """
    会话摘要响应 DTO
    
    用于列表展示时的简化会话信息。
    
    Attributes:
        session_id: 会话唯一标识符
        strategy_id: 策略ID
        strategy_name: 策略名称
        executed_at: 执行时间
        total_scanned: 扫描的股票总数
        matched_count: 匹配的股票数量
        match_rate: 匹配率
        execution_time: 执行耗时（秒）
    """
    session_id: str
    strategy_id: str
    strategy_name: str
    executed_at: str
    total_scanned: int
    matched_count: int
    match_rate: float
    execution_time: float
    
    @classmethod
    def from_domain(cls, session: 'ScreeningSession') -> 'SessionSummaryResponse':
        """
        从领域对象创建响应 DTO
        
        Args:
            session: ScreeningSession 领域对象
            
        Returns:
            SessionSummaryResponse 实例
        """
        return cls(
            session_id=session.session_id.value,
            strategy_id=session.strategy_id.value,
            strategy_name=session.strategy_name,
            executed_at=session.executed_at.isoformat(),
            total_scanned=session.total_scanned,
            matched_count=session.matched_count,
            match_rate=session.match_rate,
            execution_time=session.execution_time
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'session_id': self.session_id,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_name,
            'executed_at': self.executed_at,
            'total_scanned': self.total_scanned,
            'matched_count': self.matched_count,
            'match_rate': self.match_rate,
            'execution_time': self.execution_time
        }
