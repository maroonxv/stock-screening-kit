"""
筛选结果值对象定义

ScreeningResult 是一个不可变的值对象，表示筛选策略执行后的结果。
包含匹配的股票列表、扫描总数、执行时间、应用的筛选条件、评分配置和时间戳。

Requirements:
- 3.4: ScreeningResult 值对象，包含 matched_stocks、total_scanned、execution_time、filters_applied、scoring_config、timestamp
"""
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .scored_stock import ScoredStock
    from .scoring_config import ScoringConfig
    from ..models.filter_group import FilterGroup


class ScreeningResult:
    """
    筛选结果值对象
    
    表示筛选策略执行后的结果，包含：
    - matched_stocks: 匹配的股票列表（ScoredStock）
    - total_scanned: 扫描的股票总数
    - execution_time: 执行时间（秒）
    - filters_applied: 应用的筛选条件组（FilterGroup）
    - scoring_config: 评分配置（ScoringConfig）
    - timestamp: 执行时间戳
    """
    
    def __init__(
        self,
        matched_stocks: List['ScoredStock'],
        total_scanned: int,
        execution_time: float,
        filters_applied: 'FilterGroup',
        scoring_config: 'ScoringConfig',
        timestamp: Optional[datetime] = None
    ):
        """
        构造筛选结果
        
        Args:
            matched_stocks: 匹配的股票列表
            total_scanned: 扫描的股票总数
            execution_time: 执行时间（秒）
            filters_applied: 应用的筛选条件组
            scoring_config: 评分配置
            timestamp: 执行时间戳（默认为当前时间）
            
        Raises:
            ValueError: 如果 total_scanned 为负数或 execution_time 为负数
        """
        if total_scanned < 0:
            raise ValueError("扫描总数不能为负数")
        if execution_time < 0:
            raise ValueError("执行时间不能为负数")
        
        self._matched_stocks = list(matched_stocks) if matched_stocks else []
        self._total_scanned = total_scanned
        self._execution_time = execution_time
        self._filters_applied = filters_applied
        self._scoring_config = scoring_config
        self._timestamp = timestamp or datetime.now(timezone.utc)
    
    @property
    def matched_stocks(self) -> List['ScoredStock']:
        """获取匹配的股票列表（返回副本以保证不可变性）"""
        return list(self._matched_stocks)
    
    @property
    def total_scanned(self) -> int:
        """获取扫描的股票总数"""
        return self._total_scanned
    
    @property
    def execution_time(self) -> float:
        """获取执行时间（秒）"""
        return self._execution_time
    
    @property
    def filters_applied(self) -> 'FilterGroup':
        """获取应用的筛选条件组"""
        return self._filters_applied
    
    @property
    def scoring_config(self) -> 'ScoringConfig':
        """获取评分配置"""
        return self._scoring_config
    
    @property
    def timestamp(self) -> datetime:
        """获取执行时间戳"""
        return self._timestamp
    
    @property
    def matched_count(self) -> int:
        """获取匹配的股票数量"""
        return len(self._matched_stocks)
    
    @property
    def match_rate(self) -> float:
        """获取匹配率（匹配数/扫描总数）"""
        if self._total_scanned == 0:
            return 0.0
        return len(self._matched_stocks) / self._total_scanned
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'matched_stocks': [stock.to_dict() for stock in self._matched_stocks],
            'total_scanned': self._total_scanned,
            'execution_time': self._execution_time,
            'filters_applied': self._filters_applied.to_dict(),
            'scoring_config': self._scoring_config.to_dict(),
            'timestamp': self._timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScreeningResult':
        """
        从字典反序列化
        
        Args:
            data: 包含所有属性的字典
            
        Returns:
            ScreeningResult 实例
        """
        from .scored_stock import ScoredStock
        from .scoring_config import ScoringConfig
        from ..models.filter_group import FilterGroup
        
        matched_stocks = [
            ScoredStock.from_dict(stock_data)
            for stock_data in data.get('matched_stocks', [])
        ]
        
        filters_applied = FilterGroup.from_dict(data['filters_applied'])
        scoring_config = ScoringConfig.from_dict(data['scoring_config'])
        
        timestamp_str = data.get('timestamp')
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else None
        
        return cls(
            matched_stocks=matched_stocks,
            total_scanned=data['total_scanned'],
            execution_time=data['execution_time'],
            filters_applied=filters_applied,
            scoring_config=scoring_config,
            timestamp=timestamp
        )
    
    def __eq__(self, other: object) -> bool:
        """判断两个 ScreeningResult 是否相等"""
        if not isinstance(other, ScreeningResult):
            return False
        return (
            len(self._matched_stocks) == len(other._matched_stocks) and
            all(s1 == s2 for s1, s2 in zip(self._matched_stocks, other._matched_stocks)) and
            self._total_scanned == other._total_scanned and
            self._execution_time == other._execution_time and
            self._filters_applied.to_dict() == other._filters_applied.to_dict() and
            self._scoring_config == other._scoring_config and
            self._timestamp == other._timestamp
        )
    
    def __hash__(self) -> int:
        """计算哈希值"""
        return hash((
            self._total_scanned,
            self._execution_time,
            self._timestamp
        ))
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return (
            f"ScreeningResult(matched_count={len(self._matched_stocks)}, "
            f"total_scanned={self._total_scanned}, "
            f"execution_time={self._execution_time:.3f}s, "
            f"timestamp={self._timestamp.isoformat()})"
        )
