"""
仓储接口

本模块定义仓储的抽象接口。
领域层定义接口，基础设施层提供实现。

包含：
- IScreeningStrategyRepository: 筛选策略仓储接口
- IScreeningSessionRepository: 筛选会话仓储接口
- IWatchListRepository: 自选股列表仓储接口
- IHistoricalDataProvider: 历史数据提供者接口
"""
from .screening_strategy_repository import IScreeningStrategyRepository
from .screening_session_repository import IScreeningSessionRepository
from .watchlist_repository import IWatchListRepository
from .historical_data_provider import IHistoricalDataProvider

__all__ = [
    'IScreeningStrategyRepository',
    'IScreeningSessionRepository',
    'IWatchListRepository',
    'IHistoricalDataProvider',
]
