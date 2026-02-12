"""ExecutionTaskRepository 实现

Requirements: 8.1, 8.3, 8.4
"""
from typing import List, Optional

from ..models.execution_task_po import ExecutionTaskPO
from ....domain.repositories.execution_task_repository import IExecutionTaskRepository
from ....domain.models.execution_task import ExecutionTask
from ....domain.enums.task_status import TaskStatus


class ExecutionTaskRepositoryImpl(IExecutionTaskRepository):
    """执行任务仓储实现"""

    def __init__(self, session):
        self._session = session

    def save(self, task: ExecutionTask) -> None:
        po = self._to_po(task)
        self._session.merge(po)
        self._session.flush()

    def find_by_id(self, task_id: str) -> Optional[ExecutionTask]:
        po = self._session.query(ExecutionTaskPO).get(task_id)
        return self._to_domain(po) if po else None

    def find_by_strategy_id(
        self, strategy_id: str, limit: int = 10
    ) -> List[ExecutionTask]:
        pos = (
            self._session.query(ExecutionTaskPO)
            .filter(ExecutionTaskPO.strategy_id == strategy_id)
            .order_by(ExecutionTaskPO.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(po) for po in pos]

    def find_recent(self, limit: int = 20) -> List[ExecutionTask]:
        pos = (
            self._session.query(ExecutionTaskPO)
            .order_by(ExecutionTaskPO.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(po) for po in pos]

    def find_running_tasks(self) -> List[ExecutionTask]:
        pos = (
            self._session.query(ExecutionTaskPO)
            .filter(ExecutionTaskPO.status == TaskStatus.RUNNING.value)
            .all()
        )
        return [self._to_domain(po) for po in pos]

    def cleanup_old_tasks(self, keep_count: int = 100) -> int:
        """清理旧任务，保留最近 keep_count 条"""
        total = self._session.query(ExecutionTaskPO).count()
        if total <= keep_count:
            return 0

        # 找到第 keep_count 条记录的 created_at 作为截止时间
        cutoff_row = (
            self._session.query(ExecutionTaskPO.created_at)
            .order_by(ExecutionTaskPO.created_at.desc())
            .offset(keep_count)
            .first()
        )
        if not cutoff_row:
            return 0

        deleted = (
            self._session.query(ExecutionTaskPO)
            .filter(ExecutionTaskPO.created_at <= cutoff_row[0])
            .delete(synchronize_session='fetch')
        )
        self._session.flush()
        return deleted

    # ==================== 映射方法 ====================

    def _to_po(self, task: ExecutionTask) -> ExecutionTaskPO:
        return ExecutionTaskPO(
            id=task.task_id,
            strategy_id=task.strategy_id,
            status=task.status.value,
            progress=task.progress,
            current_step=task.current_step,
            result=task.result,
            error_message=task.error_message,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
        )

    def _to_domain(self, po: ExecutionTaskPO) -> ExecutionTask:
        return ExecutionTask(
            task_id=po.id,
            strategy_id=po.strategy_id,
            status=TaskStatus(po.status),
            progress=po.progress or 0,
            current_step=po.current_step or "",
            result=po.result,
            error_message=po.error_message,
            created_at=po.created_at,
            started_at=po.started_at,
            completed_at=po.completed_at,
        )
