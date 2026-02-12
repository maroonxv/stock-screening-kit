"""执行任务 DTO

Requirements: 2.2
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ...domain.models.execution_task import ExecutionTask


@dataclass
class TaskResponse:
    task_id: str
    strategy_id: str
    status: str
    progress: int
    current_step: str
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]

    @classmethod
    def from_domain(cls, task: ExecutionTask) -> 'TaskResponse':
        return cls(
            task_id=task.task_id,
            strategy_id=task.strategy_id,
            status=task.status.value,
            progress=task.progress,
            current_step=task.current_step,
            result=task.result,
            error_message=task.error_message,
            created_at=task.created_at.isoformat(),
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'strategy_id': self.strategy_id,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'result': self.result,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
        }
