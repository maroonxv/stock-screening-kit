"""InvestigationTask 聚合根

调研任务聚合根，管理任务的完整生命周期，包括：
- 任务创建（验证查询文本非空）
- 状态转换：start()、complete()、fail()、cancel()
- 进度更新：update_progress()
- 执行时长计算：duration 属性

状态机：
  PENDING -> RUNNING (start)
  RUNNING -> COMPLETED (complete)
  RUNNING -> FAILED (fail)
  PENDING/RUNNING -> CANCELLED (cancel)
"""

from datetime import datetime
from typing import Optional, List, Union

from ..enums.enums import TaskType, TaskStatus
from ..exceptions import InvalidTaskStateError
from ..value_objects.identifiers import TaskId
from ..value_objects.agent_step import AgentStep
from ..value_objects.industry_insight import IndustryInsight
from ..value_objects.credibility_report import CredibilityReport


class InvestigationTask:
    """调研任务聚合根 - 管理任务生命周期

    封装 AI 驱动的调研任务（快速行业认知或概念可信度验证）的完整生命周期。
    通过状态机控制任务状态转换，确保业务规则在领域层中被正确执行。
    """

    def __init__(
        self,
        task_id: TaskId,
        task_type: TaskType,
        query: str,
        status: TaskStatus = TaskStatus.PENDING,
        progress: int = 0,
        agent_steps: Optional[List[AgentStep]] = None,
        result: Union[IndustryInsight, CredibilityReport, None] = None,
        error_message: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        """初始化 InvestigationTask

        Args:
            task_id: 任务唯一标识符
            task_type: 任务类型（行业认知或概念验证）
            query: 用户输入的查询文本
            status: 任务状态，默认 PENDING
            progress: 进度百分比（0-100），默认 0
            agent_steps: Agent 执行步骤列表，默认空列表
            result: 任务结果（IndustryInsight 或 CredibilityReport），默认 None
            error_message: 错误信息，默认 None
            created_at: 创建时间，默认当前时间
            updated_at: 更新时间，默认当前时间
            completed_at: 完成时间，默认 None

        Raises:
            ValueError: 如果查询文本为空或仅包含空白字符
        """
        if not query or not query.strip():
            raise ValueError("查询文本不能为空")

        self._task_id = task_id
        self._task_type = task_type
        self._query = query.strip()
        self._status = status
        self._progress = progress
        self._agent_steps = agent_steps or []
        self._result = result
        self._error_message = error_message
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()
        self._completed_at = completed_at

    # === 状态转换方法 ===

    def start(self):
        """启动任务：PENDING -> RUNNING

        将任务状态从 PENDING 转换为 RUNNING，并更新 updated_at 时间戳。

        Raises:
            InvalidTaskStateError: 如果当前状态不是 PENDING
        """
        if self._status != TaskStatus.PENDING:
            raise InvalidTaskStateError(
                f"只能从 PENDING 状态启动任务，当前状态: {self._status.value}"
            )
        self._status = TaskStatus.RUNNING
        self._updated_at = datetime.utcnow()

    def complete(self, result: Union[IndustryInsight, CredibilityReport]):
        """完成任务：RUNNING -> COMPLETED

        将任务状态从 RUNNING 转换为 COMPLETED，保存结果，
        将进度设为 100，并记录完成时间。

        Args:
            result: 任务结果（IndustryInsight 或 CredibilityReport）

        Raises:
            InvalidTaskStateError: 如果当前状态不是 RUNNING
        """
        if self._status != TaskStatus.RUNNING:
            raise InvalidTaskStateError(
                f"只能从 RUNNING 状态完成任务，当前状态: {self._status.value}"
            )
        self._status = TaskStatus.COMPLETED
        self._result = result
        self._progress = 100
        self._completed_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()

    def fail(self, error_message: str):
        """标记任务失败：RUNNING -> FAILED

        将任务状态从 RUNNING 转换为 FAILED，保存错误信息，
        并记录完成时间。

        Args:
            error_message: 错误描述信息

        Raises:
            InvalidTaskStateError: 如果当前状态不是 RUNNING
        """
        if self._status != TaskStatus.RUNNING:
            raise InvalidTaskStateError(
                f"只能从 RUNNING 状态标记失败，当前状态: {self._status.value}"
            )
        self._status = TaskStatus.FAILED
        self._error_message = error_message
        self._completed_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()

    def cancel(self):
        """取消任务：PENDING/RUNNING -> CANCELLED

        将任务状态从 PENDING 或 RUNNING 转换为 CANCELLED，
        并记录完成时间。

        Raises:
            InvalidTaskStateError: 如果当前状态不是 PENDING 或 RUNNING
        """
        if self._status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            raise InvalidTaskStateError(
                f"只能取消 PENDING 或 RUNNING 状态的任务，当前状态: {self._status.value}"
            )
        self._status = TaskStatus.CANCELLED
        self._completed_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()

    # === 进度更新 ===

    def update_progress(self, progress: int, agent_step: AgentStep):
        """更新进度并追加 Agent 步骤

        将进度值限制在 0-100 范围内（自动 clamp），
        并将 agent_step 追加到 agent_steps 列表。

        Args:
            progress: 进度百分比，会被 clamp 到 0-100 范围
            agent_step: 要追加的 Agent 执行步骤
        """
        self._progress = max(0, min(100, progress))
        self._agent_steps.append(agent_step)
        self._updated_at = datetime.utcnow()

    # === 计算属性 ===

    @property
    def duration(self) -> Optional[float]:
        """返回任务执行时长（秒）

        计算从 created_at 到 completed_at 的时间差。
        如果任务尚未完成（completed_at 为 None），返回 None。

        Returns:
            执行时长（秒），或 None（任务未完成时）
        """
        if self._completed_at is None:
            return None
        return (self._completed_at - self._created_at).total_seconds()

    # === 属性访问器 ===

    @property
    def task_id(self) -> TaskId:
        """获取任务唯一标识符"""
        return self._task_id

    @property
    def task_type(self) -> TaskType:
        """获取任务类型"""
        return self._task_type

    @property
    def query(self) -> str:
        """获取查询文本"""
        return self._query

    @property
    def status(self) -> TaskStatus:
        """获取任务状态"""
        return self._status

    @property
    def progress(self) -> int:
        """获取进度百分比（0-100）"""
        return self._progress

    @property
    def agent_steps(self) -> List[AgentStep]:
        """获取 Agent 执行步骤列表（防御性拷贝）"""
        return list(self._agent_steps)

    @property
    def result(self) -> Union[IndustryInsight, CredibilityReport, None]:
        """获取任务结果"""
        return self._result

    @property
    def error_message(self) -> Optional[str]:
        """获取错误信息"""
        return self._error_message

    @property
    def created_at(self) -> datetime:
        """获取创建时间"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """获取最后更新时间"""
        return self._updated_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """获取完成时间"""
        return self._completed_at

    def __repr__(self):
        """返回字符串表示"""
        return (
            f"InvestigationTask(task_id={self._task_id!r}, "
            f"task_type={self._task_type.value}, "
            f"status={self._status.value}, "
            f"progress={self._progress})"
        )
