"""WebSocket 事件处理模块

提供 WebSocket 事件推送功能，用于实时推送任务进度和完成通知。

Requirements: 8.6, 8.7
"""

from .websocket_emitter import WebSocketEmitter

__all__ = ["WebSocketEmitter"]
