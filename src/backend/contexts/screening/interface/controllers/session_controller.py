"""
Session Controller - 筛选会话 REST API 控制器

实现筛选会话的 RESTful API 端点：
- GET /api/screening/sessions（列出最近的筛选会话）
- GET /api/screening/sessions/<id>（获取会话详情）

Requirements:
- 8.7: GET /api/screening/sessions 用于列出最近的筛选会话
- 8.8: GET /api/screening/sessions/<id> 用于获取会话详情
"""
from flask import Blueprint, request, jsonify
from typing import Callable, Optional

from ..dto.session_dto import SessionResponse, SessionSummaryResponse
from ...domain.repositories.screening_session_repository import IScreeningSessionRepository
from ...domain.value_objects.identifiers import SessionId


# 创建蓝图
session_bp = Blueprint(
    'screening_sessions',
    __name__,
    url_prefix='/api/screening/sessions'
)


# 仓储实例获取函数（用于依赖注入）
_get_session_repo: Optional[Callable[[], IScreeningSessionRepository]] = None


def init_session_controller(get_repo_func: Callable[[], IScreeningSessionRepository]) -> None:
    """
    初始化控制器的仓储依赖
    
    Args:
        get_repo_func: 返回 IScreeningSessionRepository 实例的函数
    """
    global _get_session_repo
    _get_session_repo = get_repo_func


def get_session_repo() -> IScreeningSessionRepository:
    """
    获取会话仓储实例
    
    Returns:
        IScreeningSessionRepository 实例
        
    Raises:
        RuntimeError: 如果仓储未初始化
    """
    if _get_session_repo is None:
        raise RuntimeError("Session controller not initialized. Call init_session_controller first.")
    return _get_session_repo()


# ==================== API 端点 ====================


@session_bp.route('', methods=['GET'])
def list_sessions():
    """
    列出最近的筛选会话
    
    Query Parameters:
        limit: 返回的最大记录数（默认 20）
        offset: 跳过的记录数（默认 0）
        strategy_id: 可选，按策略ID过滤
    
    Returns:
        200: 会话列表
        {
            "sessions": [...],
            "limit": 每页数量,
            "offset": 偏移量
        }
    
    Requirements: 8.7
    """
    # 解析分页参数
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    strategy_id = request.args.get('strategy_id', type=str)
    
    # 参数验证
    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100
    if offset < 0:
        offset = 0
    
    # 获取仓储
    repo = get_session_repo()
    
    # 根据是否有 strategy_id 过滤来选择查询方法
    if strategy_id:
        try:
            from ...domain.value_objects.identifiers import StrategyId
            strategy_id_obj = StrategyId.from_string(strategy_id)
            sessions = repo.find_by_strategy_id(strategy_id_obj, limit=limit)
            # find_by_strategy_id 不支持 offset，需要手动处理
            sessions = sessions[offset:offset + limit] if offset > 0 else sessions[:limit]
        except ValueError:
            return jsonify({'error': f'无效的策略 ID: {strategy_id}'}), 400
    else:
        sessions = repo.find_recent(limit=limit, offset=offset)
    
    # 转换为响应 DTO（使用摘要格式）
    session_responses = [
        SessionSummaryResponse.from_domain(s).to_dict()
        for s in sessions
    ]
    
    return jsonify({
        'sessions': session_responses,
        'limit': limit,
        'offset': offset
    }), 200


@session_bp.route('/<session_id>', methods=['GET'])
def get_session(session_id: str):
    """
    根据 ID 获取筛选会话详情
    
    Path Parameters:
        session_id: 会话 UUID
    
    Returns:
        200: 会话详情
        404: 会话不存在
    
    Requirements: 8.8
    """
    try:
        # 解析会话 ID
        session_id_obj = SessionId.from_string(session_id)
        
        # 获取仓储并查询
        repo = get_session_repo()
        session = repo.find_by_id(session_id_obj)
        
        if session is None:
            return jsonify({'error': f'会话 {session_id} 不存在'}), 404
        
        # 返回完整响应
        response = SessionResponse.from_domain(session)
        return jsonify(response.to_dict()), 200
        
    except ValueError as e:
        # 无效的 UUID 格式
        return jsonify({'error': f'无效的会话 ID: {session_id}'}), 400
