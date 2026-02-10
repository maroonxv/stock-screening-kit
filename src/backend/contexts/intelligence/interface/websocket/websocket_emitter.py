"""WebSocket 事件推送器

实现 IWebSocketEmitter 协议，使用 Flask-SocketIO 推送 WebSocket 事件。

支持的事件类型：
- task_progress: 任务进度更新（包含进度百分比和 Agent 步骤信息）
- task_completed: 任务完成通知（包含任务结果）
- task_failed: 任务失败通知（包含错误信息）

Requirements: 8.6, 8.7
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class WebSocketEmitter:
    """WebSocket 事件推送器

    实现 IWebSocketEmitter 协议，封装 Flask-SocketIO 的事件推送功能。
    可注入到 InvestigationTaskService 中用于实时推送任务状态更新。

    事件格式：
    - task_progress: {task_id: str, progress: int, agent_step: dict}
    - task_completed: {task_id: str, result: dict}
    - task_failed: {task_id: str, error: str}

    Requirements: 8.6, 8.7
    """

    # 支持的事件类型
    EVENT_TASK_PROGRESS = "task_progress"
    EVENT_TASK_COMPLETED = "task_completed"
    EVENT_TASK_FAILED = "task_failed"

    def __init__(self, socketio: Optional[Any] = None, namespace: str = "/intelligence"):
        """初始化 WebSocketEmitter

        Args:
            socketio: Flask-SocketIO 实例。如果为 None，则事件推送将被静默忽略（用于测试）。
            namespace: WebSocket 命名空间，默认为 '/intelligence'
        """
        self._socketio = socketio
        self._namespace = namespace

    def emit(self, event: str, data: Dict[str, Any]) -> None:
        """推送 WebSocket 事件

        实现 IWebSocketEmitter 协议的 emit 方法。
        如果 socketio 实例未配置，则静默忽略（便于测试和开发）。

        Args:
            event: 事件名称（如 'task_progress', 'task_completed', 'task_failed'）
            data: 事件数据字典

        Requirements: 8.6, 8.7
        """
        if self._socketio is None:
            logger.debug(
                "WebSocket 未配置，跳过事件推送: event=%s, data=%s",
                event,
                data,
            )
            return

        try:
            self._socketio.emit(event, data, namespace=self._namespace)
            logger.debug(
                "WebSocket 事件已推送: event=%s, namespace=%s, data=%s",
                event,
                self._namespace,
                data,
            )
        except Exception as e:
            # WebSocket 推送失败不应影响主业务流程
            logger.error(
                "WebSocket 事件推送失败: event=%s, error=%s",
                event,
                str(e),
                exc_info=True,
            )

    def emit_task_progress(
        self, task_id: str, progress: int, agent_step: Dict[str, Any]
    ) -> None:
        """推送任务进度更新事件

        便捷方法，用于推送 task_progress 事件。

        Args:
            task_id: 任务 ID
            progress: 进度百分比（0-100）
            agent_step: Agent 步骤信息字典

        Requirements: 8.6
        """
        self.emit(
            self.EVENT_TASK_PROGRESS,
            {
                "task_id": task_id,
                "progress": progress,
                "agent_step": agent_step,
            },
        )

    def emit_task_completed(self, task_id: str, result: Dict[str, Any]) -> None:
        """推送任务完成事件

        便捷方法，用于推送 task_completed 事件。

        Args:
            task_id: 任务 ID
            result: 任务结果字典（IndustryInsight 或 CredibilityReport 的序列化结果）

        Requirements: 8.7
        """
        self.emit(
            self.EVENT_TASK_COMPLETED,
            {
                "task_id": task_id,
                "result": result,
            },
        )

    def emit_task_failed(self, task_id: str, error: str) -> None:
        """推送任务失败事件

        便捷方法，用于推送 task_failed 事件。

        Args:
            task_id: 任务 ID
            error: 错误信息
        """
        self.emit(
            self.EVENT_TASK_FAILED,
            {
                "task_id": task_id,
                "error": error,
            },
        )

    @property
    def namespace(self) -> str:
        """获取 WebSocket 命名空间"""
        return self._namespace

    @property
    def is_configured(self) -> bool:
        """检查 WebSocket 是否已配置"""
        return self._socketio is not None


class NullWebSocketEmitter:
    """空实现的 WebSocket 推送器

    用于测试或不需要 WebSocket 功能的场景。
    所有 emit 调用都会被静默忽略。
    """

    def emit(self, event: str, data: Dict[str, Any]) -> None:
        """静默忽略所有事件推送"""
        pass

    def emit_task_progress(
        self, task_id: str, progress: int, agent_step: Dict[str, Any]
    ) -> None:
        """静默忽略进度更新"""
        pass

    def emit_task_completed(self, task_id: str, result: Dict[str, Any]) -> None:
        """静默忽略完成事件"""
        pass

    def emit_task_failed(self, task_id: str, error: str) -> None:
        """静默忽略失败事件"""
        pass
