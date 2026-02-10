"""Flask Blueprint 控制器 - 智能分析 RESTful API

实现智能分析上下文的 RESTful API 端点：
- POST /api/intelligence/tasks/industry-research - 创建快速行业认知任务
- POST /api/intelligence/tasks/credibility-verification - 创建概念可信度验证任务
- GET /api/intelligence/tasks/<task_id> - 查询任务详情
- GET /api/intelligence/tasks - 分页列出最近的调研任务
- POST /api/intelligence/tasks/<task_id>/cancel - 取消任务

错误处理：
- 400: 无效请求数据（ValueError）
- 404: 任务不存在（TaskNotFoundError）
- 409: 状态冲突（InvalidTaskStateError）

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.9, 8.10**
"""

from flask import Blueprint, request, jsonify
from typing import Optional

from ...application.services.investigation_task_service import InvestigationTaskService
from ...domain.exceptions import (
    TaskNotFoundError,
    InvalidTaskStateError,
    IntelligenceDomainError,
)
from ..dto.task_request_dto import (
    IndustryResearchRequest,
    CredibilityVerificationRequest,
)
from ..dto.task_response_dto import TaskResponseDTO


# 创建 Blueprint
intelligence_bp = Blueprint(
    'intelligence',
    __name__,
    url_prefix='/api/intelligence'
)

# 服务实例（通过 init_app 或工厂函数注入）
_task_service: Optional[InvestigationTaskService] = None


def init_app(task_service: InvestigationTaskService) -> None:
    """初始化控制器依赖
    
    通过此函数注入 InvestigationTaskService 实例。
    应在 Flask 应用启动时调用。
    
    Args:
        task_service: InvestigationTaskService 实例
    """
    global _task_service
    _task_service = task_service


def get_task_service() -> InvestigationTaskService:
    """获取任务服务实例
    
    Returns:
        InvestigationTaskService 实例
        
    Raises:
        RuntimeError: 如果服务未初始化
    """
    if _task_service is None:
        raise RuntimeError(
            "InvestigationTaskService 未初始化，请先调用 init_app()"
        )
    return _task_service


# === API 端点 ===


@intelligence_bp.route('/tasks/industry-research', methods=['POST'])
def create_industry_research():
    """创建快速行业认知任务
    
    请求体：
        {
            "query": "快速了解合成生物学赛道"
        }
    
    响应：
        201: {"task_id": "<uuid>"}
        400: {"error": "<错误信息>"}
    
    **Validates: Requirements 8.1**
    """
    try:
        # 解析和验证请求数据
        data = request.get_json(silent=True)
        req = IndustryResearchRequest.from_dict(data)
        req.validate()
        
        # 创建任务
        task_service = get_task_service()
        task_id = task_service.create_industry_research_task(req.query)
        
        return jsonify({'task_id': task_id}), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@intelligence_bp.route('/tasks/credibility-verification', methods=['POST'])
def create_credibility_verification():
    """创建概念可信度验证任务
    
    请求体：
        {
            "stock_code": "600519.SH",
            "concept": "AI+白酒"
        }
    
    响应：
        201: {"task_id": "<uuid>"}
        400: {"error": "<错误信息>"}
    
    **Validates: Requirements 8.2**
    """
    try:
        # 解析和验证请求数据
        data = request.get_json(silent=True)
        req = CredibilityVerificationRequest.from_dict(data)
        req.validate()
        
        # 创建任务
        task_service = get_task_service()
        task_id = task_service.create_credibility_verification_task(
            req.stock_code, req.concept
        )
        
        return jsonify({'task_id': task_id}), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@intelligence_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """查询任务详情
    
    路径参数：
        task_id: 任务唯一标识符（UUID）
    
    响应：
        200: TaskResponseDTO 序列化后的 JSON
        400: {"error": "<错误信息>"} - 无效的 task_id 格式
        404: {"error": "<错误信息>"} - 任务不存在
    
    **Validates: Requirements 8.3**
    """
    try:
        task_service = get_task_service()
        task = task_service.get_task(task_id)
        
        if task is None:
            return jsonify({'error': f'任务 {task_id} 不存在'}), 404
        
        response_dto = TaskResponseDTO.from_domain(task)
        return jsonify(response_dto.to_dict()), 200
        
    except ValueError as e:
        # 无效的 task_id 格式（UUID 验证失败）
        return jsonify({'error': str(e)}), 400


@intelligence_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """分页列出最近的调研任务
    
    查询参数：
        limit: 返回结果数量上限，默认 20，最大 100
        offset: 偏移量，默认 0
    
    响应：
        200: [TaskResponseDTO, ...]
        400: {"error": "<错误信息>"} - 无效的查询参数
    
    **Validates: Requirements 8.4**
    """
    try:
        # 解析查询参数
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 参数验证
        if limit < 1:
            return jsonify({'error': 'limit 必须大于 0'}), 400
        if limit > 100:
            limit = 100  # 限制最大值
        if offset < 0:
            return jsonify({'error': 'offset 不能为负数'}), 400
        
        task_service = get_task_service()
        tasks = task_service.list_recent_tasks(limit=limit, offset=offset)
        
        response = [TaskResponseDTO.from_domain(task).to_dict() for task in tasks]
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@intelligence_bp.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id: str):
    """取消任务
    
    路径参数：
        task_id: 任务唯一标识符（UUID）
    
    响应：
        200: {"message": "任务已取消"}
        400: {"error": "<错误信息>"} - 无效的 task_id 格式
        404: {"error": "<错误信息>"} - 任务不存在
        409: {"error": "<错误信息>"} - 任务状态不允许取消
    
    **Validates: Requirements 8.5**
    """
    try:
        task_service = get_task_service()
        task_service.cancel_task(task_id)
        
        return jsonify({'message': '任务已取消'}), 200
        
    except TaskNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except InvalidTaskStateError as e:
        return jsonify({'error': str(e)}), 409
    except ValueError as e:
        # 无效的 task_id 格式（UUID 验证失败）
        return jsonify({'error': str(e)}), 400


# === 错误处理器 ===


@intelligence_bp.errorhandler(TaskNotFoundError)
def handle_task_not_found(error: TaskNotFoundError):
    """处理任务不存在异常
    
    **Validates: Requirements 8.10**
    """
    return jsonify({'error': str(error)}), 404


@intelligence_bp.errorhandler(InvalidTaskStateError)
def handle_invalid_task_state(error: InvalidTaskStateError):
    """处理无效任务状态异常"""
    return jsonify({'error': str(error)}), 409


@intelligence_bp.errorhandler(ValueError)
def handle_value_error(error: ValueError):
    """处理数据验证异常
    
    **Validates: Requirements 8.9**
    """
    return jsonify({'error': str(error)}), 400


@intelligence_bp.errorhandler(IntelligenceDomainError)
def handle_domain_error(error: IntelligenceDomainError):
    """处理其他领域异常"""
    return jsonify({'error': str(error)}), 500

