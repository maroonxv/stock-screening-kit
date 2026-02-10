"""
WatchList Controller - 自选股列表 REST API 控制器

实现自选股列表的 RESTful API 端点：
- POST /api/screening/watchlists（创建）
- GET /api/screening/watchlists（分页列表）
- GET /api/screening/watchlists/<id>（详情）
- PUT /api/screening/watchlists/<id>（更新）
- DELETE /api/screening/watchlists/<id>（删除）
- POST /api/screening/watchlists/<id>/stocks（添加股票）
- DELETE /api/screening/watchlists/<id>/stocks/<stock_code>（移除股票）

Requirements:
- 8.9: CRUD 端点 /api/screening/watchlists
"""
from flask import Blueprint, request, jsonify
from typing import Callable, Optional

from ..dto.watchlist_dto import (
    CreateWatchlistRequest,
    UpdateWatchlistRequest,
    AddStockRequest,
    WatchlistResponse,
    WatchlistSummaryResponse,
)
from ...application.services.watchlist_service import WatchListService
from ...domain.exceptions import (
    DuplicateNameError,
    DuplicateStockError,
    StockNotFoundError,
    WatchListNotFoundError,
)


# 创建蓝图
watchlist_bp = Blueprint(
    'screening_watchlists',
    __name__,
    url_prefix='/api/screening/watchlists'
)


# 服务实例获取函数（用于依赖注入）
_get_watchlist_service: Optional[Callable[[], WatchListService]] = None


def init_watchlist_controller(get_service_func: Callable[[], WatchListService]) -> None:
    """
    初始化控制器的服务依赖
    
    Args:
        get_service_func: 返回 WatchListService 实例的函数
    """
    global _get_watchlist_service
    _get_watchlist_service = get_service_func


def get_watchlist_service() -> WatchListService:
    """
    获取自选股列表服务实例
    
    Returns:
        WatchListService 实例
        
    Raises:
        RuntimeError: 如果服务未初始化
    """
    if _get_watchlist_service is None:
        raise RuntimeError("Watchlist controller not initialized. Call init_watchlist_controller first.")
    return _get_watchlist_service()


# ==================== API 端点 ====================


@watchlist_bp.route('', methods=['POST'])
def create_watchlist():
    """
    创建新的自选股列表
    
    Request Body:
        {
            "name": "列表名称",
            "description": "可选描述"
        }
    
    Returns:
        201: 创建成功，返回列表详情
        400: 请求数据无效
        409: 列表名称已存在
    
    Requirements: 8.9
    """
    try:
        # 解析请求数据
        data = request.get_json()
        if data is None:
            return jsonify({'error': '请求体不能为空'}), 400
        
        # 验证并转换为 DTO
        dto = CreateWatchlistRequest.from_dict(data)
        
        # 调用服务创建列表
        service = get_watchlist_service()
        watchlist = service.create_watchlist(
            name=dto.name,
            description=dto.description
        )
        
        # 返回响应
        response = WatchlistResponse.from_domain(watchlist)
        return jsonify(response.to_dict()), 201
        
    except ValueError as e:
        # DTO 验证错误或领域验证错误
        return jsonify({'error': str(e)}), 400
    except DuplicateNameError as e:
        return jsonify({'error': str(e)}), 409


@watchlist_bp.route('', methods=['GET'])
def list_watchlists():
    """
    分页列出所有自选股列表
    
    Query Parameters:
        limit: 返回的最大记录数（默认 100）
        offset: 跳过的记录数（默认 0）
    
    Returns:
        200: 列表
        {
            "watchlists": [...],
            "limit": 每页数量,
            "offset": 偏移量
        }
    
    Requirements: 8.9
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
    
    # 调用服务获取列表
    service = get_watchlist_service()
    watchlists = service.list_watchlists(limit=limit, offset=offset)
    
    # 转换为响应 DTO（使用摘要格式）
    watchlist_responses = [
        WatchlistSummaryResponse.from_domain(w).to_dict()
        for w in watchlists
    ]
    
    return jsonify({
        'watchlists': watchlist_responses,
        'limit': limit,
        'offset': offset
    }), 200


@watchlist_bp.route('/<watchlist_id>', methods=['GET'])
def get_watchlist(watchlist_id: str):
    """
    根据 ID 获取自选股列表详情
    
    Path Parameters:
        watchlist_id: 列表 UUID
    
    Returns:
        200: 列表详情
        404: 列表不存在
    
    Requirements: 8.9
    """
    try:
        # 调用服务获取列表
        service = get_watchlist_service()
        watchlist = service.get_watchlist(watchlist_id)
        
        if watchlist is None:
            return jsonify({'error': f'自选股列表 {watchlist_id} 不存在'}), 404
        
        # 返回响应
        response = WatchlistResponse.from_domain(watchlist)
        return jsonify(response.to_dict()), 200
        
    except ValueError as e:
        # 无效的 UUID 格式
        return jsonify({'error': f'无效的列表 ID: {watchlist_id}'}), 400


@watchlist_bp.route('/<watchlist_id>', methods=['PUT'])
def update_watchlist(watchlist_id: str):
    """
    更新自选股列表
    
    Path Parameters:
        watchlist_id: 列表 UUID
    
    Request Body:
        {
            "name": "新名称（可选）",
            "description": "新描述（可选）"
        }
    
    Returns:
        200: 更新成功，返回列表详情
        400: 请求数据无效
        404: 列表不存在
        409: 新名称与其他列表重复
    
    Requirements: 8.9
    """
    try:
        # 解析请求数据
        data = request.get_json()
        if data is None:
            return jsonify({'error': '请求体不能为空'}), 400
        
        # 验证并转换为 DTO
        dto = UpdateWatchlistRequest.from_dict(data)
        
        # 检查是否有更新字段
        if not dto.has_updates():
            return jsonify({'error': '请求体中没有需要更新的字段'}), 400
        
        # 调用服务更新列表
        service = get_watchlist_service()
        watchlist = service.update_watchlist(
            watchlist_id_str=watchlist_id,
            name=dto.name,
            description=dto.description
        )
        
        # 返回响应
        response = WatchlistResponse.from_domain(watchlist)
        return jsonify(response.to_dict()), 200
        
    except ValueError as e:
        # DTO 验证错误或领域验证错误
        return jsonify({'error': str(e)}), 400
    except WatchListNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except DuplicateNameError as e:
        return jsonify({'error': str(e)}), 409


@watchlist_bp.route('/<watchlist_id>', methods=['DELETE'])
def delete_watchlist(watchlist_id: str):
    """
    删除自选股列表
    
    Path Parameters:
        watchlist_id: 列表 UUID
    
    Returns:
        204: 删除成功（无内容）
        404: 列表不存在
    
    Requirements: 8.9
    """
    try:
        # 调用服务删除列表
        service = get_watchlist_service()
        service.delete_watchlist(watchlist_id)
        
        # 返回 204 No Content
        return '', 204
        
    except ValueError as e:
        # 无效的 UUID 格式
        return jsonify({'error': f'无效的列表 ID: {watchlist_id}'}), 400
    except WatchListNotFoundError as e:
        return jsonify({'error': str(e)}), 404


@watchlist_bp.route('/<watchlist_id>/stocks', methods=['POST'])
def add_stock(watchlist_id: str):
    """
    向自选股列表添加股票
    
    Path Parameters:
        watchlist_id: 列表 UUID
    
    Request Body:
        {
            "stock_code": "600000.SH",
            "stock_name": "浦发银行",
            "note": "可选备注",
            "tags": ["可选标签"]
        }
    
    Returns:
        200: 添加成功，返回更新后的列表详情
        400: 请求数据无效
        404: 列表不存在
        409: 股票已存在于列表中
    
    Requirements: 8.9
    """
    try:
        # 解析请求数据
        data = request.get_json()
        if data is None:
            return jsonify({'error': '请求体不能为空'}), 400
        
        # 验证并转换为 DTO
        dto = AddStockRequest.from_dict(data)
        
        # 调用服务添加股票
        service = get_watchlist_service()
        watchlist = service.add_stock(
            watchlist_id_str=watchlist_id,
            stock_code_str=dto.stock_code,
            stock_name=dto.stock_name,
            note=dto.note,
            tags=dto.tags
        )
        
        # 返回响应
        response = WatchlistResponse.from_domain(watchlist)
        return jsonify(response.to_dict()), 200
        
    except ValueError as e:
        # DTO 验证错误或股票代码格式无效
        return jsonify({'error': str(e)}), 400
    except WatchListNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except DuplicateStockError as e:
        return jsonify({'error': str(e)}), 409


@watchlist_bp.route('/<watchlist_id>/stocks/<stock_code>', methods=['DELETE'])
def remove_stock(watchlist_id: str, stock_code: str):
    """
    从自选股列表移除股票
    
    Path Parameters:
        watchlist_id: 列表 UUID
        stock_code: 股票代码（如 600000.SH）
    
    Returns:
        200: 移除成功，返回更新后的列表详情
        400: 股票代码格式无效
        404: 列表不存在或股票不在列表中
    
    Requirements: 8.9
    """
    try:
        # 调用服务移除股票
        service = get_watchlist_service()
        watchlist = service.remove_stock(
            watchlist_id_str=watchlist_id,
            stock_code_str=stock_code
        )
        
        # 返回响应
        response = WatchlistResponse.from_domain(watchlist)
        return jsonify(response.to_dict()), 200
        
    except ValueError as e:
        # 无效的 UUID 格式或股票代码格式
        return jsonify({'error': str(e)}), 400
    except WatchListNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except StockNotFoundError as e:
        return jsonify({'error': str(e)}), 404
