"""调研任务 Repository 接口

定义 IInvestigationTaskRepository 抽象接口，用于 InvestigationTask 聚合根的持久化。
领域层定义接口，基础设施层（SQLAlchemy + PostgreSQL）提供具体实现。
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from ..models.investigation_task import InvestigationTask
from ..value_objects.identifiers import TaskId
from ..enums.enums import TaskStatus


class IInvestigationTaskRepository(ABC):
    """调研任务 Repository 接口

    定义 InvestigationTask 聚合根的持久化契约，包括保存、查询、删除和统计操作。
    基础设施层通过 SQLAlchemy ORM 实现此接口，在领域对象和 PO 模型之间进行双向映射。
    """

    @abstractmethod
    def save(self, task: InvestigationTask) -> None:
        """保存调研任务

        如果任务已存在则更新，否则创建新记录。

        Args:
            task: InvestigationTask 聚合根实例
        """
        ...

    @abstractmethod
    def find_by_id(self, task_id: TaskId) -> Optional[InvestigationTask]:
        """根据任务 ID 查找调研任务

        Args:
            task_id: 任务唯一标识符

        Returns:
            InvestigationTask 实例，如果不存在则返回 None
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def delete(self, task_id: TaskId) -> None:
        """删除调研任务

        Args:
            task_id: 任务唯一标识符
        """
        ...

    @abstractmethod
    def count_by_status(self, status: TaskStatus) -> int:
        """统计指定状态的任务数量

        Args:
            status: 任务状态

        Returns:
            符合条件的任务数量
        """
        ...
