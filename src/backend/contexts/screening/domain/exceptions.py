"""领域层异常定义"""


class DomainError(Exception):
    """领域层基础异常"""
    pass


class DuplicateStockError(DomainError):
    """WatchList 中添加重复股票"""
    pass


class StockNotFoundError(DomainError):
    """WatchList 中移除不存在的股票"""
    pass


class DuplicateNameError(DomainError):
    """策略或列表名称重复"""
    pass


class StrategyNotFoundError(DomainError):
    """策略不存在"""
    pass


class WatchListNotFoundError(DomainError):
    """自选股列表不存在"""
    pass


class ScoringError(DomainError):
    """评分计算错误"""
    pass


class IndicatorCalculationError(DomainError):
    """指标计算错误"""
    pass


class ValidationError(DomainError):
    """通用验证错误"""
    pass


class InvalidTaskStateError(DomainError):
    """非法任务状态转换"""
    pass


class TaskNotFoundError(DomainError):
    """执行任务不存在"""
    pass
