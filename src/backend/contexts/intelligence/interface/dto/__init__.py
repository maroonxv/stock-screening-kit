"""接口层 DTO 模块

导出请求和响应 DTO 类。
"""
from .task_request_dto import (
    IndustryResearchRequest,
    CredibilityVerificationRequest,
)
from .task_response_dto import TaskResponseDTO

__all__ = [
    'IndustryResearchRequest',
    'CredibilityVerificationRequest',
    'TaskResponseDTO',
]
