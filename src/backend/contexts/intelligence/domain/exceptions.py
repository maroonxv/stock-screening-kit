"""智能分析上下文领域层异常定义"""


class IntelligenceDomainError(Exception):
    """智能分析上下文基础异常"""
    pass


class InvalidTaskStateError(IntelligenceDomainError):
    """无效的任务状态转换"""
    pass


class TaskNotFoundError(IntelligenceDomainError):
    """任务不存在"""
    pass


class AnalysisTimeoutError(IntelligenceDomainError):
    """分析超时"""
    pass


class LLMServiceError(IntelligenceDomainError):
    """LLM 服务调用错误"""
    pass
