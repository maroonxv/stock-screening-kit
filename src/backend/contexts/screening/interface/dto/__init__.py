"""
DTO 模块

包含接口层的数据传输对象（DTO）类，用于请求验证和响应格式化。

Requirements:
- 8.10: 实现 DTO 类用于请求验证和响应格式化
"""

from .strategy_dto import (
    CreateStrategyRequest,
    UpdateStrategyRequest,
    StrategyResponse,
    ScoredStockResponse,
    ScreeningResultResponse,
)

from .session_dto import (
    SessionResponse,
    SessionSummaryResponse,
)

from .watchlist_dto import (
    CreateWatchlistRequest,
    UpdateWatchlistRequest,
    AddStockRequest,
    WatchedStockResponse,
    WatchlistResponse,
    WatchlistSummaryResponse,
)

__all__ = [
    # Strategy DTOs
    'CreateStrategyRequest',
    'UpdateStrategyRequest',
    'StrategyResponse',
    'ScoredStockResponse',
    'ScreeningResultResponse',
    # Session DTOs
    'SessionResponse',
    'SessionSummaryResponse',
    # Watchlist DTOs
    'CreateWatchlistRequest',
    'UpdateWatchlistRequest',
    'AddStockRequest',
    'WatchedStockResponse',
    'WatchlistResponse',
    'WatchlistSummaryResponse',
]
