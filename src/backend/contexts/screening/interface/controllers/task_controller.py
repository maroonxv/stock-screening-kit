"""Task Controller - 执行任务 REST API 控制器

Requirements: 2.2, 2.3, 2.4, 2.7
"""
from flask import Blueprint, request, jsonify
from typing import Callable, Optional

from ..dto.task_dto import TaskResponse
from ...application.services.async_execution_service import AsyncExecutionService
from ...domain.exceptions import InvalidTaskStateError, TaskNotFoundError

task_bp = Blueprint(
    'screening_tasks', __name__,
    url_prefix='/api/screening/tasks',
)

_get_execution_service: Optional[Callable[[], AsyncExecutionService]] = None


def init_task_controller(get_service_func: Callable[[], AsyncExecutionService]) -> None:
    global _get_execution_service
    _get_execution_service = get_service_func


def get_execution_service() -> AsyncExecutionService:
    if _get_execution_service is None:
        raise RuntimeError("Task controller not initialized.")
    return _get_execution_service()


@task_bp.route('', methods=['GET'])
def list_tasks():
    """列出执行任务"""
    limit = request.args.get('limit', 20, type=int)
    service = get_execution_service()
    tasks = service.list_tasks(limit)
    return jsonify({
        'tasks': [TaskResponse.from_domain(t).to_dict() for t in tasks]
    })


@task_bp.route('/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """获取任务详情"""
    service = get_execution_service()
    task = service.get_task(task_id)
    if not task:
        return jsonify({'error': f'任务 {task_id} 不存在'}), 404
    return jsonify(TaskResponse.from_domain(task).to_dict())


@task_bp.route('/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id: str):
    """取消任务"""
    service = get_execution_service()
    try:
        service.cancel_task(task_id)
        return jsonify({'message': '任务已取消'})
    except TaskNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except InvalidTaskStateError as e:
        return jsonify({'error': str(e)}), 409
