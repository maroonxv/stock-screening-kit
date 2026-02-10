"""WebSocket 事件推送器单元测试

测试 WebSocketEmitter 类的事件推送功能。

Requirements: 8.6, 8.7
"""

import pytest
from unittest.mock import Mock, call

from contexts.intelligence.interface.websocket.websocket_emitter import (
    WebSocketEmitter,
    NullWebSocketEmitter,
)


class TestWebSocketEmitter:
    """WebSocketEmitter 单元测试"""

    def test_emit_with_socketio_configured(self):
        """测试配置了 SocketIO 时的事件推送"""
        # Arrange
        mock_socketio = Mock()
        emitter = WebSocketEmitter(socketio=mock_socketio, namespace="/test")
        event = "task_progress"
        data = {"task_id": "123", "progress": 50}

        # Act
        emitter.emit(event, data)

        # Assert
        mock_socketio.emit.assert_called_once_with(
            event, data, namespace="/test"
        )

    def test_emit_without_socketio_configured(self):
        """测试未配置 SocketIO 时的事件推送（静默忽略）"""
        # Arrange
        emitter = WebSocketEmitter(socketio=None)
        event = "task_progress"
        data = {"task_id": "123", "progress": 50}

        # Act & Assert - 不应抛出异常
        emitter.emit(event, data)

    def test_emit_handles_socketio_exception(self):
        """测试 SocketIO 推送异常时的错误处理"""
        # Arrange
        mock_socketio = Mock()
        mock_socketio.emit.side_effect = Exception("Connection error")
        emitter = WebSocketEmitter(socketio=mock_socketio)
        event = "task_progress"
        data = {"task_id": "123", "progress": 50}

        # Act & Assert - 不应抛出异常
        emitter.emit(event, data)

    def test_emit_task_progress(self):
        """测试 emit_task_progress 便捷方法

        Requirements: 8.6
        """
        # Arrange
        mock_socketio = Mock()
        emitter = WebSocketEmitter(socketio=mock_socketio, namespace="/intelligence")
        task_id = "test-task-123"
        progress = 75
        agent_step = {
            "agent_name": "行业背景速览",
            "status": "completed",
            "output_summary": "分析完成",
        }

        # Act
        emitter.emit_task_progress(task_id, progress, agent_step)

        # Assert
        mock_socketio.emit.assert_called_once_with(
            "task_progress",
            {
                "task_id": task_id,
                "progress": progress,
                "agent_step": agent_step,
            },
            namespace="/intelligence",
        )

    def test_emit_task_completed(self):
        """测试 emit_task_completed 便捷方法

        Requirements: 8.7
        """
        # Arrange
        mock_socketio = Mock()
        emitter = WebSocketEmitter(socketio=mock_socketio, namespace="/intelligence")
        task_id = "test-task-456"
        result = {
            "industry_name": "合成生物学",
            "summary": "行业总结...",
            "heat_score": 85,
        }

        # Act
        emitter.emit_task_completed(task_id, result)

        # Assert
        mock_socketio.emit.assert_called_once_with(
            "task_completed",
            {
                "task_id": task_id,
                "result": result,
            },
            namespace="/intelligence",
        )

    def test_emit_task_failed(self):
        """测试 emit_task_failed 便捷方法"""
        # Arrange
        mock_socketio = Mock()
        emitter = WebSocketEmitter(socketio=mock_socketio, namespace="/intelligence")
        task_id = "test-task-789"
        error = "LLM 服务调用超时"

        # Act
        emitter.emit_task_failed(task_id, error)

        # Assert
        mock_socketio.emit.assert_called_once_with(
            "task_failed",
            {
                "task_id": task_id,
                "error": error,
            },
            namespace="/intelligence",
        )

    def test_default_namespace(self):
        """测试默认命名空间"""
        # Arrange
        mock_socketio = Mock()
        emitter = WebSocketEmitter(socketio=mock_socketio)

        # Assert
        assert emitter.namespace == "/intelligence"

    def test_custom_namespace(self):
        """测试自定义命名空间"""
        # Arrange
        mock_socketio = Mock()
        emitter = WebSocketEmitter(socketio=mock_socketio, namespace="/custom")

        # Assert
        assert emitter.namespace == "/custom"

    def test_is_configured_true(self):
        """测试 is_configured 属性（已配置）"""
        # Arrange
        mock_socketio = Mock()
        emitter = WebSocketEmitter(socketio=mock_socketio)

        # Assert
        assert emitter.is_configured is True

    def test_is_configured_false(self):
        """测试 is_configured 属性（未配置）"""
        # Arrange
        emitter = WebSocketEmitter(socketio=None)

        # Assert
        assert emitter.is_configured is False

    def test_event_constants(self):
        """测试事件常量定义"""
        assert WebSocketEmitter.EVENT_TASK_PROGRESS == "task_progress"
        assert WebSocketEmitter.EVENT_TASK_COMPLETED == "task_completed"
        assert WebSocketEmitter.EVENT_TASK_FAILED == "task_failed"


class TestNullWebSocketEmitter:
    """NullWebSocketEmitter 单元测试"""

    def test_emit_does_nothing(self):
        """测试 emit 方法静默忽略"""
        # Arrange
        emitter = NullWebSocketEmitter()

        # Act & Assert - 不应抛出异常
        emitter.emit("task_progress", {"task_id": "123"})

    def test_emit_task_progress_does_nothing(self):
        """测试 emit_task_progress 方法静默忽略"""
        # Arrange
        emitter = NullWebSocketEmitter()

        # Act & Assert - 不应抛出异常
        emitter.emit_task_progress("123", 50, {"agent_name": "test"})

    def test_emit_task_completed_does_nothing(self):
        """测试 emit_task_completed 方法静默忽略"""
        # Arrange
        emitter = NullWebSocketEmitter()

        # Act & Assert - 不应抛出异常
        emitter.emit_task_completed("123", {"result": "test"})

    def test_emit_task_failed_does_nothing(self):
        """测试 emit_task_failed 方法静默忽略"""
        # Arrange
        emitter = NullWebSocketEmitter()

        # Act & Assert - 不应抛出异常
        emitter.emit_task_failed("123", "error message")


class TestWebSocketEmitterIntegration:
    """WebSocketEmitter 集成场景测试"""

    def test_multiple_events_sequence(self):
        """测试多个事件的顺序推送"""
        # Arrange
        mock_socketio = Mock()
        emitter = WebSocketEmitter(socketio=mock_socketio, namespace="/intelligence")
        task_id = "workflow-task-001"

        # Act - 模拟工作流执行过程中的事件序列
        emitter.emit_task_progress(task_id, 20, {"agent_name": "Agent1", "status": "completed"})
        emitter.emit_task_progress(task_id, 40, {"agent_name": "Agent2", "status": "completed"})
        emitter.emit_task_progress(task_id, 60, {"agent_name": "Agent3", "status": "completed"})
        emitter.emit_task_progress(task_id, 80, {"agent_name": "Agent4", "status": "completed"})
        emitter.emit_task_progress(task_id, 100, {"agent_name": "Agent5", "status": "completed"})
        emitter.emit_task_completed(task_id, {"industry_name": "Test Industry"})

        # Assert
        assert mock_socketio.emit.call_count == 6

    def test_workflow_failure_scenario(self):
        """测试工作流失败场景的事件推送"""
        # Arrange
        mock_socketio = Mock()
        emitter = WebSocketEmitter(socketio=mock_socketio, namespace="/intelligence")
        task_id = "failing-task-001"

        # Act - 模拟工作流执行失败
        emitter.emit_task_progress(task_id, 20, {"agent_name": "Agent1", "status": "completed"})
        emitter.emit_task_progress(task_id, 40, {"agent_name": "Agent2", "status": "running"})
        emitter.emit_task_failed(task_id, "Agent2 执行超时")

        # Assert
        assert mock_socketio.emit.call_count == 3
        # 验证最后一个调用是 task_failed
        last_call = mock_socketio.emit.call_args_list[-1]
        assert last_call == call(
            "task_failed",
            {"task_id": task_id, "error": "Agent2 执行超时"},
            namespace="/intelligence",
        )
