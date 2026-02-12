"""
Strategy Controller - 筛选策略 REST API 控制器

实现筛选策略的 RESTful API 端点：
- POST /api/screening/strategies（创建）
- GET /api/screening/strategies（分页列表）
- GET /api/screening/strategies/<id>（详情）
- PUT /api/screening/strategies/<id>（更新）
- DELETE /api/screening/strategies/<id>（删除）
- POST /api/screening/strategies/<id>/execute（执行）

Requirements:
- 8.1: POST /api/screening/strategies 用于创建新的筛选策略
- 8.2: GET /api/screening/strategies 用于分页列出所有策略
- 8.3: GET /api/screening/strategies/<id> 用于按 ID 获取策略
- 8.4: PUT /api/screening/strategies/<id> 用于更新策略
- 8.5: DELETE /api/screening/strategies/<id> 用于删除策略
- 8.6: POST /api/screening/strategies/<id>/execute 用于执行策略并返回结果
"""
from flask import Blueprint, request, jsonify, current_app
from typing import Callable, Optional

from ..dto.strategy_dto import (
    CreateStrategyRequest,
    UpdateStrategyRequest,
    StrategyResponse,
    ScreeningResultResponse,
)
from ...application.services.screening_strategy_service import ScreeningStrategyService
from ...application.services.async_execution_service import AsyncExecutionService
from ...domain.exceptions import (
    DuplicateNameError,
    StrategyNotFoundError,
    ValidationError,
)


# 创建蓝图
strategy_bp = Blueprint(
    'screening_strategies',
    __name__,
    url_prefix='/api/screening/strategies'
)


# 服务实例获取函数（用于依赖注入）
_get_strategy_service: Optional[Callable[[], ScreeningStrategyService]] = None
_get_execution_service: Optional[Callable[[], AsyncExecutionService]] = None


def init_strategy_controller(
    get_service_func: Callable[[], ScreeningStrategyService],
    get_execution_service_func: Optional[Callable[[], AsyncExecutionService]] = None,
) -> None:
    """
    初始化控制器的服务依赖
    
    Args:
        get_service_func: 返回 ScreeningStrategyService 实例的函数
        get_execution_service_func: 返回 AsyncExecutionService 实例的函数
    """
    global _get_strategy_service, _get_execution_service
    _get_strategy_service = get_service_func
    _get_execution_service = get_execution_service_func


def get_strategy_service() -> ScreeningStrategyService:
    """
    获取策略服务实例
    
    Returns:
        ScreeningStrategyService 实例
        
    Raises:
        RuntimeError: 如果服务未初始化
    """
    if _get_strategy_service is None:
        raise RuntimeError("Strategy controller not initialized. Call init_strategy_controller first.")
    return _get_strategy_service()


# ==================== API 端点 ====================


@strategy_bp.route('', methods=['POST'])
def create_strategy():
    """
    创建新的筛选策略
    
    Request Body:
        {
            "name": "策略名称",
            "filters": {...},
            "scoring_config": {...},
            "description": "可选描述",
            "tags": ["可选标签"]
        }
    
    Returns:
        201: 创建成功，返回策略详情
        400: 请求数据无效
        409: 策略名称已存在
    
    Requirements: 8.1
    """
    try:
        # 解析请求数据
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({'error': '请求体不能为空'}), 400
        
        # 验证并转换为 DTO
        dto = CreateStrategyRequest.from_dict(data)
        
        # 调用服务创建策略
        service = get_strategy_service()
        strategy = service.create_strategy(
            name=dto.name,
            filters_dict=dto.filters,
            scoring_config_dict=dto.scoring_config,
            description=dto.description,
            tags=dto.tags
        )
        
        # 返回响应
        response = StrategyResponse.from_domain(strategy)
        return jsonify(response.to_dict()), 201
        
    except ValueError as e:
        # DTO 验证错误或领域验证错误
        return jsonify({'error': str(e)}), 400
    except DuplicateNameError as e:
        return jsonify({'error': str(e)}), 409


@strategy_bp.route('', methods=['GET'])
def list_strategies():
    """
    分页列出所有筛选策略
    
    Query Parameters:
        limit: 返回的最大记录数（默认 100）
        offset: 跳过的记录数（默认 0）
    
    Returns:
        200: 策略列表
        {
            "strategies": [...],
            "total": 总数,
            "limit": 每页数量,
            "offset": 偏移量
        }
    
    Requirements: 8.2
    """
    # 解析分页参数
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # 参数验证
    if limit < 1:
        limit = 1
    if limit > 1000:
        limit = 1000
    if offset < 0:
        offset = 0
    
    # 调用服务获取策略列表
    service = get_strategy_service()
    strategies = service.list_strategies(limit=limit, offset=offset)
    
    # 转换为响应 DTO
    strategy_responses = [
        StrategyResponse.from_domain(s).to_dict()
        for s in strategies
    ]
    
    return jsonify({
        'strategies': strategy_responses,
        'limit': limit,
        'offset': offset
    }), 200


@strategy_bp.route('/<strategy_id>', methods=['GET'])
def get_strategy(strategy_id: str):
    """
    根据 ID 获取筛选策略详情
    
    Path Parameters:
        strategy_id: 策略 UUID
    
    Returns:
        200: 策略详情
        404: 策略不存在
    
    Requirements: 8.3
    """
    try:
        # 调用服务获取策略
        service = get_strategy_service()
        strategy = service.get_strategy(strategy_id)
        
        if strategy is None:
            return jsonify({'error': f'策略 {strategy_id} 不存在'}), 404
        
        # 返回响应
        response = StrategyResponse.from_domain(strategy)
        return jsonify(response.to_dict()), 200
        
    except ValueError as e:
        # 无效的 UUID 格式
        return jsonify({'error': f'无效的策略 ID: {strategy_id}'}), 400


@strategy_bp.route('/<strategy_id>', methods=['PUT'])
def update_strategy(strategy_id: str):
    """
    更新筛选策略
    
    Path Parameters:
        strategy_id: 策略 UUID
    
    Request Body:
        {
            "name": "新名称（可选）",
            "filters": {...}（可选）,
            "scoring_config": {...}（可选）,
            "description": "新描述（可选）",
            "tags": ["新标签"]（可选）
        }
    
    Returns:
        200: 更新成功，返回策略详情
        400: 请求数据无效
        404: 策略不存在
        409: 新名称与其他策略重复
    
    Requirements: 8.4
    """
    try:
        # 解析请求数据
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({'error': '请求体不能为空'}), 400
        
        # 验证并转换为 DTO
        dto = UpdateStrategyRequest.from_dict(data)
        
        # 检查是否有更新字段
        if not dto.has_updates():
            return jsonify({'error': '请求体中没有需要更新的字段'}), 400
        
        # 调用服务更新策略
        service = get_strategy_service()
        strategy = service.update_strategy(
            strategy_id_str=strategy_id,
            name=dto.name,
            filters_dict=dto.filters,
            scoring_config_dict=dto.scoring_config,
            description=dto.description,
            tags=dto.tags
        )
        
        # 返回响应
        response = StrategyResponse.from_domain(strategy)
        return jsonify(response.to_dict()), 200
        
    except ValueError as e:
        # DTO 验证错误或领域验证错误
        return jsonify({'error': str(e)}), 400
    except StrategyNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except DuplicateNameError as e:
        return jsonify({'error': str(e)}), 409


@strategy_bp.route('/<strategy_id>', methods=['DELETE'])
def delete_strategy(strategy_id: str):
    """
    删除筛选策略
    
    Path Parameters:
        strategy_id: 策略 UUID
    
    Returns:
        204: 删除成功（无内容）
        404: 策略不存在
    
    Requirements: 8.5
    """
    try:
        # 调用服务删除策略
        service = get_strategy_service()
        service.delete_strategy(strategy_id)
        
        # 返回 204 No Content
        return '', 204
        
    except ValueError as e:
        # 无效的 UUID 格式
        return jsonify({'error': f'无效的策略 ID: {strategy_id}'}), 400
    except StrategyNotFoundError as e:
        return jsonify({'error': str(e)}), 404


@strategy_bp.route('/<strategy_id>/execute', methods=['POST'])
def execute_strategy(strategy_id: str):
    """
    异步执行筛选策略
    
    Path Parameters:
        strategy_id: 策略 UUID
    
    Returns:
        202: 任务已创建，返回 task_id
        404: 策略不存在
    
    Requirements: 2.1, 2.5, 2.6
    """
    try:
        if _get_execution_service is None:
            return jsonify({'error': '异步执行服务未初始化'}), 500
        
        execution_service = _get_execution_service()
        task = execution_service.start_execution(strategy_id)
        return jsonify({
            'task_id': task.task_id,
            'status': task.status.value,
            'message': '任务已提交，请通过 WebSocket 或轮询获取进度',
        }), 202
        
    except ValueError as e:
        return jsonify({'error': f'无效的策略 ID: {strategy_id}'}), 400
    except StrategyNotFoundError as e:
        return jsonify({'error': str(e)}), 404
