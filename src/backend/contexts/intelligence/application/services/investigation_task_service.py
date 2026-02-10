"""应用层 - InvestigationTaskService

编排调研任务的创建、执行和查询。负责：
- 创建快速行业认知任务和概念可信度验证任务
- 持久化任务到 Repository
- 异步启动 LangGraph 工作流（fire-and-forget）
- 通过回调更新任务进度并推送 WebSocket 事件
- 工作流完成/失败时更新任务状态并推送事件

依赖倒置：所有依赖通过构造函数注入抽象接口，不依赖具体实现。

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import asyncio
import logging
from typing import List, Optional, Protocol

from ...domain.enums.enums import TaskType, TaskStatus
from ...domain.exceptions import TaskNotFoundError
from ...domain.models.investigation_task import InvestigationTask
from ...domain.repositories.investigation_task_repository import (
    IInvestigationTaskRepository,
)
from ...domain.services.credibility_verification_service import (
    ICredibilityVerificationService,
)
from ...domain.services.industry_research_service import IIndustryResearchService
from ...domain.value_objects.agent_step import AgentStep
from ...domain.value_objects.identifiers import TaskId

from shared_kernel.value_objects.stock_code import StockCode

logger = logging.getLogger(__name__)


class IWebSocketEmitter(Protocol):
    """WebSocket 事件推送接口

    定义 WebSocket 事件推送的最小契约。
    接口层（Flask-SocketIO）提供具体实现。
    """

    def emit(self, event: str, data: dict) -> None:
        """推送 WebSocket 事件

        Args:
            event: 事件名称（如 'task_progress', 'task_completed'）
            data: 事件数据字典
        """
        ...


class InvestigationTaskService:
    """应用层调研任务服务

    编排调研任务的完整生命周期：创建 -> 持久化 -> 异步执行工作流 -> 进度更新 -> 完成/失败。
    通过依赖注入接收 Repository、工作流服务和 WebSocket 推送器。

    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """

    def __init__(
        self,
        task_repo: IInvestigationTaskRepository,
        research_service: IIndustryResearchService,
        credibility_service: ICredibilityVerificationService,
        ws_emitter: IWebSocketEmitter,
    ):
        """初始化 InvestigationTaskService

        Args:
            task_repo: 调研任务 Repository（领域层接口）
            research_service: 快速行业认知服务（领域层接口）
            credibility_service: 概念可信度验证服务（领域层接口）
            ws_emitter: WebSocket 事件推送器
        """
        self._task_repo = task_repo
        self._research_service = research_service
        self._credibility_service = credibility_service
        self._ws_emitter = ws_emitter

    # === 任务创建方法 ===

    def create_industry_research_task(self, query: str) -> str:
        """创建快速行业认知任务

        创建 InvestigationTask 聚合根，持久化到 Repository，
        异步启动 LangGraph 行业认知工作流，返回 task_id。

        Args:
            query: 用户查询文本（如"快速了解合成生物学赛道"）

        Returns:
            任务 ID 字符串

        Raises:
            ValueError: 如果查询文本为空

        Requirements: 7.2
        """
        task = InvestigationTask(
            task_id=TaskId.generate(),
            task_type=TaskType.INDUSTRY_RESEARCH,
            query=query,
        )
        self._task_repo.save(task)

        # 异步启动工作流（fire-and-forget）
        self._schedule_async(self._run_research_workflow(task.task_id))

        return task.task_id.value

    def create_credibility_verification_task(
        self, stock_code: str, concept: str
    ) -> str:
        """创建概念可信度验证任务

        创建 InvestigationTask 聚合根，持久化到 Repository，
        异步启动 LangGraph 可信度验证工作流，返回 task_id。

        Args:
            stock_code: 股票代码字符串（如 "600519.SH"）
            concept: 被验证的概念（如 "AI+白酒"）

        Returns:
            任务 ID 字符串

        Raises:
            ValueError: 如果 stock_code 或 concept 为空/无效

        Requirements: 7.3
        """
        # 验证 stock_code 格式（StockCode 值对象会做格式校验）
        stock_code_vo = StockCode(stock_code)

        task = InvestigationTask(
            task_id=TaskId.generate(),
            task_type=TaskType.CREDIBILITY_VERIFICATION,
            query=f"{stock_code}:{concept}",
        )
        self._task_repo.save(task)

        # 异步启动工作流（fire-and-forget）
        self._schedule_async(
            self._run_credibility_workflow(task.task_id, stock_code_vo, concept)
        )

        return task.task_id.value

    # === 查询方法 ===

    def get_task(self, task_id_str: str) -> Optional[InvestigationTask]:
        """根据 ID 查询调研任务

        Args:
            task_id_str: 任务 ID 字符串

        Returns:
            InvestigationTask 实例，不存在时返回 None

        Requirements: 7.1
        """
        task_id = TaskId.from_string(task_id_str)
        return self._task_repo.find_by_id(task_id)

    def list_recent_tasks(
        self, limit: int = 20, offset: int = 0
    ) -> List[InvestigationTask]:
        """分页列出最近的调研任务

        Args:
            limit: 返回结果数量上限，默认 20
            offset: 偏移量，默认 0

        Returns:
            InvestigationTask 列表，按创建时间降序排列

        Requirements: 7.1
        """
        return self._task_repo.find_recent_tasks(limit=limit, offset=offset)

    # === 任务操作方法 ===

    def cancel_task(self, task_id_str: str) -> None:
        """取消调研任务

        Args:
            task_id_str: 任务 ID 字符串

        Raises:
            TaskNotFoundError: 如果任务不存在
            InvalidTaskStateError: 如果任务状态不允许取消

        Requirements: 7.1
        """
        task_id = TaskId.from_string(task_id_str)
        task = self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(f"任务 {task_id_str} 不存在")
        task.cancel()
        self._task_repo.save(task)

    # === 异步工作流执行 ===

    async def _run_research_workflow(self, task_id: TaskId) -> None:
        """异步执行快速行业认知工作流

        1. 从 Repository 加载任务
        2. 启动任务（PENDING -> RUNNING）
        3. 执行工作流，通过回调更新进度和推送 WebSocket 事件
        4. 工作流完成后更新任务为 COMPLETED 并推送完成事件
        5. 工作流失败时更新任务为 FAILED

        Args:
            task_id: 任务唯一标识符

        Requirements: 7.2, 7.4, 7.5
        """
        task = self._task_repo.find_by_id(task_id)
        if task is None:
            logger.error("任务 %s 不存在，无法启动工作流", task_id.value)
            return

        # 检查任务是否已被取消
        if task.status == TaskStatus.CANCELLED:
            logger.info("任务 %s 已被取消，跳过工作流执行", task_id.value)
            return

        try:
            # 启动任务：PENDING -> RUNNING
            task.start()
            self._task_repo.save(task)

            def on_progress(progress: int, agent_step: AgentStep) -> None:
                """进度回调：更新任务进度并推送 WebSocket 事件

                Requirements: 7.4
                """
                task.update_progress(progress, agent_step)
                self._task_repo.save(task)
                self._ws_emitter.emit(
                    "task_progress",
                    {
                        "task_id": task_id.value,
                        "progress": progress,
                        "agent_step": agent_step.to_dict(),
                    },
                )

            # 执行行业认知工作流
            result = await self._research_service.execute_research(
                task.query, progress_callback=on_progress
            )

            # 重新加载任务以检查是否已被取消
            task = self._task_repo.find_by_id(task_id)
            if task is None or task.status == TaskStatus.CANCELLED:
                logger.info("任务 %s 在工作流执行期间被取消", task_id.value)
                return

            # 完成任务：RUNNING -> COMPLETED
            task.complete(result)
            self._task_repo.save(task)
            self._ws_emitter.emit(
                "task_completed",
                {
                    "task_id": task_id.value,
                    "result": result.to_dict(),
                },
            )

        except Exception as e:
            logger.error(
                "行业认知工作流执行失败 (task_id=%s): %s",
                task_id.value,
                str(e),
                exc_info=True,
            )
            # 重新加载任务以获取最新状态
            task = self._task_repo.find_by_id(task_id)
            if task is not None and task.status == TaskStatus.RUNNING:
                task.fail(str(e))
                self._task_repo.save(task)
                self._ws_emitter.emit(
                    "task_failed",
                    {
                        "task_id": task_id.value,
                        "error": str(e),
                    },
                )

    async def _run_credibility_workflow(
        self, task_id: TaskId, stock_code: StockCode, concept: str
    ) -> None:
        """异步执行概念可信度验证工作流

        1. 从 Repository 加载任务
        2. 启动任务（PENDING -> RUNNING）
        3. 执行工作流，通过回调更新进度和推送 WebSocket 事件
        4. 工作流完成后更新任务为 COMPLETED 并推送完成事件
        5. 工作流失败时更新任务为 FAILED

        Args:
            task_id: 任务唯一标识符
            stock_code: 股票代码值对象
            concept: 被验证的概念

        Requirements: 7.3, 7.4, 7.5
        """
        task = self._task_repo.find_by_id(task_id)
        if task is None:
            logger.error("任务 %s 不存在，无法启动工作流", task_id.value)
            return

        # 检查任务是否已被取消
        if task.status == TaskStatus.CANCELLED:
            logger.info("任务 %s 已被取消，跳过工作流执行", task_id.value)
            return

        try:
            # 启动任务：PENDING -> RUNNING
            task.start()
            self._task_repo.save(task)

            def on_progress(progress: int, agent_step: AgentStep) -> None:
                """进度回调：更新任务进度并推送 WebSocket 事件

                Requirements: 7.4
                """
                task.update_progress(progress, agent_step)
                self._task_repo.save(task)
                self._ws_emitter.emit(
                    "task_progress",
                    {
                        "task_id": task_id.value,
                        "progress": progress,
                        "agent_step": agent_step.to_dict(),
                    },
                )

            # 执行可信度验证工作流
            result = await self._credibility_service.verify_credibility(
                stock_code, concept, progress_callback=on_progress
            )

            # 重新加载任务以检查是否已被取消
            task = self._task_repo.find_by_id(task_id)
            if task is None or task.status == TaskStatus.CANCELLED:
                logger.info("任务 %s 在工作流执行期间被取消", task_id.value)
                return

            # 完成任务：RUNNING -> COMPLETED
            task.complete(result)
            self._task_repo.save(task)
            self._ws_emitter.emit(
                "task_completed",
                {
                    "task_id": task_id.value,
                    "result": result.to_dict(),
                },
            )

        except Exception as e:
            logger.error(
                "可信度验证工作流执行失败 (task_id=%s): %s",
                task_id.value,
                str(e),
                exc_info=True,
            )
            # 重新加载任务以获取最新状态
            task = self._task_repo.find_by_id(task_id)
            if task is not None and task.status == TaskStatus.RUNNING:
                task.fail(str(e))
                self._task_repo.save(task)
                self._ws_emitter.emit(
                    "task_failed",
                    {
                        "task_id": task_id.value,
                        "error": str(e),
                    },
                )

    # === 辅助方法 ===

    @staticmethod
    def _schedule_async(coro) -> None:
        """调度异步协程执行（fire-and-forget）

        尝试在当前运行的事件循环中创建任务。
        如果没有运行中的事件循环，则创建新的事件循环执行。

        Args:
            coro: 要执行的异步协程
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            # 没有运行中的事件循环，创建新线程执行
            import threading

            def _run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()

            thread = threading.Thread(target=_run_in_thread, daemon=True)
            thread.start()
