"""执行任务状态枚举

Requirements: 1.2
"""
from enum import Enum


class TaskStatus(Enum):
    """执行任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
