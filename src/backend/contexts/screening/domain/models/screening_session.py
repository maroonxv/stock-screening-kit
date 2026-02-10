"""
ScreeningSession 聚合根实现

ScreeningSession 记录某次筛选的执行结果，是筛选上下文的核心聚合根之一。
包含筛选会话的完整信息，包括策略快照、执行结果和统计数据。

Requirements:
- 2.2: ScreeningSession 聚合根包含所有属性（session_id、strategy_id、strategy_name、
       executed_at、total_scanned、execution_time、top_stocks、other_stock_codes、
       filters_snapshot、scoring_config_snapshot）
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..value_objects.identifiers import SessionId, StrategyId
from ..value_objects.scored_stock import ScoredStock
from ..value_objects.scoring_config import ScoringConfig
from .filter_group import FilterGroup

if TYPE_CHECKING:
    from ..value_objects.screening_result import ScreeningResult
    from shared_kernel.value_objects.stock_code import StockCode


class ScreeningSession:
    """
    筛选会话聚合根
    
    记录某次筛选的执行结果，包含：
    - session_id: 会话唯一标识符（SessionId）
    - strategy_id: 策略ID（StrategyId）
    - strategy_name: 策略名称
    - executed_at: 执行时间
    - total_scanned: 扫描的股票总数
    - execution_time: 执行耗时（秒）
    - top_stocks: 前N名股票（ScoredStock列表）
    - other_stock_codes: 其他匹配股票代码列表
    - filters_snapshot: 筛选条件快照（FilterGroup）
    - scoring_config_snapshot: 评分配置快照（ScoringConfig）
    
    核心行为:
    - create_from_result(): 从 ScreeningResult 创建 ScreeningSession
    """
    
    # 默认保存的 top_stocks 数量
    DEFAULT_TOP_N = 50
    
    def __init__(
        self,
        session_id: SessionId,
        strategy_id: StrategyId,
        strategy_name: str,
        executed_at: datetime,
        total_scanned: int,
        execution_time: float,
        top_stocks: List[ScoredStock],
        other_stock_codes: List[str],
        filters_snapshot: FilterGroup,
        scoring_config_snapshot: ScoringConfig
    ):
        """
        构造筛选会话
        
        Args:
            session_id: 会话唯一标识符
            strategy_id: 策略ID
            strategy_name: 策略名称
            executed_at: 执行时间
            total_scanned: 扫描的股票总数
            execution_time: 执行耗时（秒）
            top_stocks: 前N名股票列表
            other_stock_codes: 其他匹配股票代码列表
            filters_snapshot: 筛选条件快照
            scoring_config_snapshot: 评分配置快照
            
        Raises:
            ValueError: 如果策略名称为空、total_scanned 为负数或 execution_time 为负数
        """
        # 验证策略名称非空
        if not strategy_name or not strategy_name.strip():
            raise ValueError("策略名称不能为空")
        
        # 验证 total_scanned 非负
        if total_scanned < 0:
            raise ValueError("扫描总数不能为负数")
        
        # 验证 execution_time 非负
        if execution_time < 0:
            raise ValueError("执行时间不能为负数")
        
        self._session_id = session_id
        self._strategy_id = strategy_id
        self._strategy_name = strategy_name.strip()
        self._executed_at = executed_at
        self._total_scanned = total_scanned
        self._execution_time = execution_time
        self._top_stocks = list(top_stocks) if top_stocks else []
        self._other_stock_codes = list(other_stock_codes) if other_stock_codes else []
        self._filters_snapshot = filters_snapshot
        self._scoring_config_snapshot = scoring_config_snapshot
    
    # ==================== 工厂方法 ====================
    
    @classmethod
    def create_from_result(
        cls,
        strategy_id: StrategyId,
        strategy_name: str,
        result: 'ScreeningResult',
        top_n: int = DEFAULT_TOP_N
    ) -> 'ScreeningSession':
        """
        从 ScreeningResult 创建 ScreeningSession
        
        将筛选结果转换为持久化的会话记录。前 top_n 名股票保存完整信息，
        其余匹配股票只保存股票代码。
        
        Args:
            strategy_id: 策略ID
            strategy_name: 策略名称
            result: 筛选结果（ScreeningResult）
            top_n: 保存完整信息的前N名股票数量（默认50）
            
        Returns:
            ScreeningSession 实例
        """
        # 获取匹配的股票列表
        matched_stocks = result.matched_stocks
        
        # 分离 top_stocks 和 other_stock_codes
        top_stocks = matched_stocks[:top_n]
        other_stocks = matched_stocks[top_n:]
        other_stock_codes = [stock.stock_code.code for stock in other_stocks]
        
        return cls(
            session_id=SessionId.generate(),
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            executed_at=result.timestamp,
            total_scanned=result.total_scanned,
            execution_time=result.execution_time,
            top_stocks=top_stocks,
            other_stock_codes=other_stock_codes,
            filters_snapshot=result.filters_applied,
            scoring_config_snapshot=result.scoring_config
        )
    
    # ==================== 属性访问器 ====================
    
    @property
    def session_id(self) -> SessionId:
        """获取会话唯一标识符"""
        return self._session_id
    
    @property
    def strategy_id(self) -> StrategyId:
        """获取策略ID"""
        return self._strategy_id
    
    @property
    def strategy_name(self) -> str:
        """获取策略名称"""
        return self._strategy_name
    
    @property
    def executed_at(self) -> datetime:
        """获取执行时间"""
        return self._executed_at
    
    @property
    def total_scanned(self) -> int:
        """获取扫描的股票总数"""
        return self._total_scanned
    
    @property
    def execution_time(self) -> float:
        """获取执行耗时（秒）"""
        return self._execution_time
    
    @property
    def top_stocks(self) -> List[ScoredStock]:
        """获取前N名股票列表（返回副本以保证不可变性）"""
        return list(self._top_stocks)
    
    @property
    def other_stock_codes(self) -> List[str]:
        """获取其他匹配股票代码列表（返回副本以保证不可变性）"""
        return list(self._other_stock_codes)
    
    @property
    def filters_snapshot(self) -> FilterGroup:
        """获取筛选条件快照"""
        return self._filters_snapshot
    
    @property
    def scoring_config_snapshot(self) -> ScoringConfig:
        """获取评分配置快照"""
        return self._scoring_config_snapshot
    
    # ==================== 计算属性 ====================
    
    @property
    def matched_count(self) -> int:
        """获取匹配的股票总数（top_stocks + other_stock_codes）"""
        return len(self._top_stocks) + len(self._other_stock_codes)
    
    @property
    def match_rate(self) -> float:
        """获取匹配率（匹配数/扫描总数）"""
        if self._total_scanned == 0:
            return 0.0
        return self.matched_count / self._total_scanned
    
    @property
    def top_stocks_count(self) -> int:
        """获取 top_stocks 数量"""
        return len(self._top_stocks)
    
    @property
    def other_stocks_count(self) -> int:
        """获取 other_stock_codes 数量"""
        return len(self._other_stock_codes)
    
    # ==================== 序列化方法 ====================
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'session_id': self._session_id.value,
            'strategy_id': self._strategy_id.value,
            'strategy_name': self._strategy_name,
            'executed_at': self._executed_at.isoformat(),
            'total_scanned': self._total_scanned,
            'execution_time': self._execution_time,
            'top_stocks': [stock.to_dict() for stock in self._top_stocks],
            'other_stock_codes': self._other_stock_codes,
            'filters_snapshot': self._filters_snapshot.to_dict(),
            'scoring_config_snapshot': self._scoring_config_snapshot.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScreeningSession':
        """
        从字典反序列化
        
        Args:
            data: 包含所有属性的字典
            
        Returns:
            ScreeningSession 实例
        """
        session_id = SessionId.from_string(data['session_id'])
        strategy_id = StrategyId.from_string(data['strategy_id'])
        
        executed_at_str = data.get('executed_at')
        executed_at = datetime.fromisoformat(executed_at_str) if executed_at_str else datetime.now(timezone.utc)
        
        top_stocks = [
            ScoredStock.from_dict(stock_data)
            for stock_data in data.get('top_stocks', [])
        ]
        
        filters_snapshot = FilterGroup.from_dict(data['filters_snapshot'])
        scoring_config_snapshot = ScoringConfig.from_dict(data['scoring_config_snapshot'])
        
        return cls(
            session_id=session_id,
            strategy_id=strategy_id,
            strategy_name=data['strategy_name'],
            executed_at=executed_at,
            total_scanned=data['total_scanned'],
            execution_time=data['execution_time'],
            top_stocks=top_stocks,
            other_stock_codes=data.get('other_stock_codes', []),
            filters_snapshot=filters_snapshot,
            scoring_config_snapshot=scoring_config_snapshot
        )
    
    # ==================== 特殊方法 ====================
    
    def __eq__(self, other: object) -> bool:
        """
        判断两个 ScreeningSession 是否相等
        
        基于 session_id 判断相等性（聚合根标识）
        """
        if not isinstance(other, ScreeningSession):
            return False
        return self._session_id == other._session_id
    
    def __hash__(self) -> int:
        """
        计算哈希值
        
        基于 session_id 计算哈希值
        """
        return hash(self._session_id)
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return (
            f"ScreeningSession(session_id={self._session_id!r}, "
            f"strategy_name='{self._strategy_name}', "
            f"executed_at={self._executed_at.isoformat()}, "
            f"matched_count={self.matched_count})"
        )
