"""InvestigationTaskRepository 实现

实现 IInvestigationTaskRepository 接口，负责 InvestigationTask 聚合根的持久化。
处理 PO ↔ 领域对象映射，包含 AgentStep、IndustryInsight 和 CredibilityReport 的
JSONB 序列化/反序列化。

Requirements:
- 5.2: 实现 InvestigationTaskRepositoryImpl，在 InvestigationTask 领域对象和 PO 模型之间进行双向映射
- 5.3: 保存 InvestigationTask 后按 ID 检索时，返回等价的领域对象，包含所有嵌套的值对象
- 5.4: 使用 JSONB 存储 result 字段，支持 IndustryInsight 和 CredibilityReport 两种类型的序列化与反序列化
"""

from typing import Optional, List

from contexts.intelligence.domain.repositories.investigation_task_repository import (
    IInvestigationTaskRepository,
)
from contexts.intelligence.domain.models.investigation_task import InvestigationTask
from contexts.intelligence.domain.value_objects.identifiers import TaskId
from contexts.intelligence.domain.value_objects.agent_step import AgentStep
from contexts.intelligence.domain.value_objects.industry_insight import IndustryInsight
from contexts.intelligence.domain.value_objects.credibility_report import (
    CredibilityReport,
)
from contexts.intelligence.domain.enums.enums import TaskType, TaskStatus
from ..models.investigation_task_po import InvestigationTaskPO


class InvestigationTaskRepositoryImpl(IInvestigationTaskRepository):
    """调研任务仓储实现

    使用 SQLAlchemy session 进行数据库操作。
    负责 InvestigationTask 领域对象与 InvestigationTaskPO 持久化对象之间的映射。

    映射说明:
    - task_id (TaskId) <-> id (String)
    - task_type (TaskType) <-> task_type (String) - 使用枚举 value
    - status (TaskStatus) <-> status (String) - 使用枚举 value
    - agent_steps (List[AgentStep]) <-> agent_steps (JSONB) - 使用 to_dict/from_dict 序列化
    - result (IndustryInsight|CredibilityReport) <-> result (JSONB) - 使用 to_dict/from_dict 序列化
    - result_type (str) <-> result_type (String) - 区分 result 类型
    """

    def __init__(self, session):
        """初始化仓储

        Args:
            session: SQLAlchemy 数据库会话
        """
        self._session = session

    def save(self, task: InvestigationTask) -> None:
        """保存调研任务

        如果任务已存在（相同 ID），则更新；否则创建新记录。
        使用 merge 实现 upsert 语义。

        Args:
            task: 要保存的调研任务
        """
        po = self._to_po(task)
        self._session.merge(po)
        self._session.flush()

    def find_by_id(self, task_id: TaskId) -> Optional[InvestigationTask]:
        """根据任务 ID 查找调研任务

        Args:
            task_id: 任务唯一标识符

        Returns:
            如果找到返回 InvestigationTask，否则返回 None
        """
        po = self._session.query(InvestigationTaskPO).get(task_id.value)
        return self._to_domain(po) if po else None

    def find_by_status(
        self, status: TaskStatus, limit: int = 20
    ) -> List[InvestigationTask]:
        """根据状态查找调研任务

        Args:
            status: 任务状态
            limit: 返回结果数量上限，默认 20

        Returns:
            符合条件的 InvestigationTask 列表
        """
        pos = (
            self._session.query(InvestigationTaskPO)
            .filter(InvestigationTaskPO.status == status.value)
            .limit(limit)
            .all()
        )
        return [self._to_domain(po) for po in pos]

    def find_recent_tasks(
        self, limit: int = 20, offset: int = 0
    ) -> List[InvestigationTask]:
        """查找最近的调研任务（按创建时间降序）

        Args:
            limit: 返回结果数量上限，默认 20
            offset: 偏移量，默认 0

        Returns:
            InvestigationTask 列表，按创建时间降序排列
        """
        pos = (
            self._session.query(InvestigationTaskPO)
            .order_by(InvestigationTaskPO.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_domain(po) for po in pos]

    def delete(self, task_id: TaskId) -> None:
        """删除调研任务

        Args:
            task_id: 要删除的任务 ID

        Note:
            如果任务不存在，静默处理（不抛出异常）
        """
        po = self._session.query(InvestigationTaskPO).get(task_id.value)
        if po:
            self._session.delete(po)
            self._session.flush()

    def count_by_status(self, status: TaskStatus) -> int:
        """统计指定状态的任务数量

        Args:
            status: 任务状态

        Returns:
            符合条件的任务数量
        """
        return (
            self._session.query(InvestigationTaskPO)
            .filter(InvestigationTaskPO.status == status.value)
            .count()
        )

    # ==================== 私有映射方法 ====================

    def _to_po(self, task: InvestigationTask) -> InvestigationTaskPO:
        """将领域对象转换为持久化对象

        Args:
            task: InvestigationTask 领域对象

        Returns:
            InvestigationTaskPO 持久化对象

        Note:
            - agent_steps 使用 AgentStep.to_dict() 序列化为 JSONB 数组
            - result 使用 to_dict() 序列化为 JSONB
            - result_type 根据 result 的实际类型设置为 "industry_insight" 或 "credibility_report"
        """
        result_dict = task.result.to_dict() if task.result else None
        result_type = None
        if isinstance(task.result, IndustryInsight):
            result_type = "industry_insight"
        elif isinstance(task.result, CredibilityReport):
            result_type = "credibility_report"

        return InvestigationTaskPO(
            id=task.task_id.value,
            task_type=task.task_type.value,
            query=task.query,
            status=task.status.value,
            progress=task.progress,
            agent_steps=[s.to_dict() for s in task.agent_steps],
            result=result_dict,
            result_type=result_type,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
        )

    def _to_domain(self, po: InvestigationTaskPO) -> InvestigationTask:
        """将持久化对象转换为领域对象

        Args:
            po: InvestigationTaskPO 持久化对象

        Returns:
            InvestigationTask 领域对象

        Note:
            - agent_steps JSONB 使用 AgentStep.from_dict() 反序列化
            - result JSONB 根据 result_type 使用 IndustryInsight.from_dict() 或
              CredibilityReport.from_dict() 反序列化
        """
        result = None
        if po.result:
            if po.result_type == "industry_insight":
                result = IndustryInsight.from_dict(po.result)
            elif po.result_type == "credibility_report":
                result = CredibilityReport.from_dict(po.result)

        return InvestigationTask(
            task_id=TaskId.from_string(po.id),
            task_type=TaskType(po.task_type),
            query=po.query,
            status=TaskStatus(po.status),
            progress=po.progress,
            agent_steps=[AgentStep.from_dict(s) for s in (po.agent_steps or [])],
            result=result,
            error_message=po.error_message,
            created_at=po.created_at,
            updated_at=po.updated_at,
            completed_at=po.completed_at,
        )
