"""接口层模块

包含 Flask Controller、DTO 和 WebSocket 事件处理。

Requirements: 8.1-8.10
"""

from .websocket import WebSocketEmitter

__all__ = ["WebSocketEmitter"]
