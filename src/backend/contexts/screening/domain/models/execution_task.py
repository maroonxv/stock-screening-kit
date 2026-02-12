"""ExecutionTask 实体

表示一次策略执行的后台任务，包含任务状态、进度和结果。

Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 1.7
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..enums.task_status import TaskStatus
from ..exceptions import InvalidTaskStateError


class ExecutionTask:
    """执行任务实体"""

    def __init__(
        self,
        task_id: str,
        strategy_id: str,
        status: TaskStatus = TaskStatus.PENDING,
        progress: int = 0,
        total_steps: int = 100,
        current_step: str = "",
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        created_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        self._task_id = task_id
        self._strategy_id = strategy_id
        self._status = status
        self._progress = progress
        self._total_steps = total_steps
        self._current_step = current_step
        self._result = result
        self._error_message = error_message
        self._created_at = created_at or datetime.now(timezone.utc)
        self._started_at = started_at
        self._completed_at = completed_at
        self._cancelled = status == TaskStatus.CANCELLED

    @classmethod
    def create(cls, strategy_id: str) -> "ExecutionTask":
        """创建新任务，初始状态为 PENDING"""
        return cls(
            task_id=str(uuid.uuid4()),
            strategy_id=strategy_id,
            status=TaskStatus.PENDING,
            progress=0,
        )

    def start(self) -> None:
        """开始执行，PENDING -> RUNNING"""
        if self._status != TaskStatus.PENDING:
            raise InvalidTaskStateError(
                f"无法从 {self._status.value} 状态启动任务"
            )
        self._status = TaskStatus.RUNNING
        self._started_at = datetime.now(timezone.utc)

    def update_progress(self, progress: int, current_step: str) -> None:
        """更新执行进度"""
        if self._status != TaskStatus.RUNNING:
            return
        self._progress = max(0, min(progress, 100))
        self._current_step = current_step

    def complete(self, result: Dict[str, Any]) -> None:
        """完成执行，RUNNING -> COMPLETED"""
        if self._status != TaskStatus.RUNNING:
            raise InvalidTaskStateError(
                f"无法从 {self._status.value} 状态完成任务"
            )
        self._status = TaskStatus.COMPLETED
        self._progress = 100
        self._result = result
        self._completed_at = datetime.now(timezone.utc)

    def fail(self, error_message: str) -> None:
        """执行失败，RUNNING/PENDING -> FAILED"""
        if self._status not in (TaskStatus.RUNNING, TaskStatus.PENDING):
            raise InvalidTaskStateError(
                f"无法从 {self._status.value} 状态标记失败"
            )
        self._status = TaskStatus.FAILED
        self._error_message = error_message
        self._completed_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        """取消任务，PENDING/RUNNING -> CANCELLED"""
        if self._status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            raise InvalidTaskStateError(
                f"无法从 {self._status.value} 状态取消任务"
            )
        self._status = TaskStatus.CANCELLED
        self._cancelled = True
        self._completed_at = datetime.now(timezone.utc)

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def progress(self) -> int:
        return self._progress

    @property
    def total_steps(self) -> int:
        return self._total_steps

    @property
    def current_step(self) -> str:
        return self._current_step

    @property
    def result(self) -> Optional[Dict[str, Any]]:
        return self._result

    @property
    def error_message(self) -> Optional[str]:
        return self._error_message

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def started_at(self) -> Optional[datetime]:
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        return self._completed_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExecutionTask):
            return False
        return self._task_id == other._task_id

    def __hash__(self) -> int:
        return hash(self._task_id)

    def __repr__(self) -> str:
        return (
            f"ExecutionTask(task_id='{self._task_id}', "
            f"strategy_id='{self._strategy_id}', "
            f"status={self._status.value})"
        )
