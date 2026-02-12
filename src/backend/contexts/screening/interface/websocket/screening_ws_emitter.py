"""筛选上下文 WebSocket 事件推送器

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ScreeningWebSocketEmitter:
    """筛选上下文 WebSocket 事件推送器"""

    NAMESPACE = '/screening'

    def __init__(self, socketio=None):
        self._socketio = socketio

    def emit_status_changed(self, task_id: str, status: str, **extra) -> None:
        """推送任务状态变化事件"""
        self._emit('task_status_changed', {
            'task_id': task_id, 'status': status, **extra
        })

    def emit_progress(
        self,
        task_id: str,
        phase: str,
        progress: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """推送任务进度事件"""
        self._emit('task_progress', {
            'task_id': task_id,
            'phase': phase,
            'progress': progress,
            'message': message,
            'details': details or {},
        })

    def emit_completed(self, task_id: str, result_summary: Dict[str, Any]) -> None:
        """推送任务完成事件"""
        self._emit('task_completed', {
            'task_id': task_id, 'result': result_summary
        })

    def emit_failed(self, task_id: str, error: str) -> None:
        """推送任务失败事件"""
        self._emit('task_failed', {
            'task_id': task_id, 'error': error
        })

    def _emit(self, event: str, data: Dict[str, Any]) -> None:
        if self._socketio is None:
            logger.debug("WebSocket 未配置，跳过事件: %s", event)
            return
        try:
            self._socketio.emit(event, data, namespace=self.NAMESPACE)
        except Exception as e:
            logger.error("WebSocket 推送失败: event=%s, error=%s", event, str(e))
