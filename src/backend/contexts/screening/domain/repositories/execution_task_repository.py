"""执行任务仓储接口

Requirements: 8.1
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.execution_task import ExecutionTask


class IExecutionTaskRepository(ABC):
    """执行任务仓储接口"""

    @abstractmethod
    def save(self, task: ExecutionTask) -> None:
        """保存或更新任务"""
        pass

    @abstractmethod
    def find_by_id(self, task_id: str) -> Optional[ExecutionTask]:
        """根据 ID 查找任务"""
        pass

    @abstractmethod
    def find_by_strategy_id(
        self, strategy_id: str, limit: int = 10
    ) -> List[ExecutionTask]:
        """查找策略的执行任务"""
        pass

    @abstractmethod
    def find_recent(self, limit: int = 20) -> List[ExecutionTask]:
        """查找最近的任务"""
        pass

    @abstractmethod
    def find_running_tasks(self) -> List[ExecutionTask]:
        """查找所有运行中的任务"""
        pass

    @abstractmethod
    def cleanup_old_tasks(self, keep_count: int = 100) -> int:
        """清理旧任务，保留最近 N 条"""
        pass
