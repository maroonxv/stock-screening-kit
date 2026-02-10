"""
Session Controller 单元测试

测试筛选会话 REST API 端点的请求处理和响应格式化功能。

Requirements:
- 8.7: GET /api/screening/sessions 用于列出最近的筛选会话
- 8.8: GET /api/screening/sessions/<id> 用于获取会话详情
- 8.11: API 请求包含无效数据时返回 HTTP 400 和描述性错误信息
- 8.12: 请求的资源不存在时返回 HTTP 404
"""
import pytest
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock
from flask import Flask

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contexts.screening.interface.controllers.session_controller import (
    session_bp,
    init_session_controller,
)


# 使用有效的 UUID 作为测试 ID
TEST_SESSION_ID = str(uuid.uuid4())
TEST_STRATEGY_ID = str(uuid.uuid4())


@pytest.fixture
def app():
    """创建测试 Flask 应用"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(session_bp)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def mock_repo():
    """创建 mock 仓储"""
    return MagicMock()


@pytest.fixture
def mock_session():
    """创建 mock 会话对象"""
    mock = MagicMock()
    mock.session_id.value = TEST_SESSION_ID
    mock.strategy_id.value = TEST_STRATEGY_ID
    mock.strategy_name = 'Test Strategy'
    mock.executed_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock.total_scanned = 1000
    mock.matched_count = 50
    mock.match_rate = 0.05
    mock.execution_time = 1.5
    mock.top_stocks = []
    mock.other_stock_codes = []
    mock.filters_snapshot.to_dict.return_value = {
        'group_id': 'test-group',
        'operator': 'AND',
        'conditions': [],
        'sub_groups': []
    }
    mock.scoring_config_snapshot.to_dict.return_value = {
        'weights': {'ROE': 1.0},
        'normalization_method': 'min_max'
    }
    return mock


@pytest.fixture(autouse=True)
def setup_controller(mock_repo):
    """自动初始化控制器"""
    init_session_controller(lambda: mock_repo)
    yield
    # 清理
    from contexts.screening.interface.controllers import session_controller
    session_controller._get_session_repo = None


# ==================== 测试 GET /api/screening/sessions ====================


class TestListSessions:
    """测试列出会话端点 (Requirements 8.7)"""
    
    def test_list_sessions_default_params(self, client, mock_repo, mock_session):
        """测试使用默认参数列出会话"""
        mock_repo.find_recent.return_value = [mock_session]
        
        response = client.get('/api/screening/sessions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sessions' in data
        assert len(data['sessions']) == 1
        assert data['limit'] == 20
        assert data['offset'] == 0
        
        mock_repo.find_recent.assert_called_once_with(limit=20, offset=0)
    
    def test_list_sessions_custom_params(self, client, mock_repo, mock_session):
        """测试使用自定义参数列出会话"""
        mock_repo.find_recent.return_value = [mock_session]
        
        response = client.get('/api/screening/sessions?limit=10&offset=5')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 10
        assert data['offset'] == 5
        
        mock_repo.find_recent.assert_called_once_with(limit=10, offset=5)
    
    def test_list_sessions_limit_validation(self, client, mock_repo):
        """测试 limit 参数验证"""
        mock_repo.find_recent.return_value = []
        
        # 测试负数 limit
        response = client.get('/api/screening/sessions?limit=-1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 1  # 应该被修正为 1
        
        # 测试超大 limit
        response = client.get('/api/screening/sessions?limit=200')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 100  # 应该被限制为 100
    
    def test_list_sessions_offset_validation(self, client, mock_repo):
        """测试 offset 参数验证"""
        mock_repo.find_recent.return_value = []
        
        # 测试负数 offset
        response = client.get('/api/screening/sessions?offset=-5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['offset'] == 0  # 应该被修正为 0
    
    def test_list_sessions_empty_result(self, client, mock_repo):
        """测试空结果"""
        mock_repo.find_recent.return_value = []
        
        response = client.get('/api/screening/sessions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['sessions'] == []
    
    def test_list_sessions_by_strategy_id(self, client, mock_repo, mock_session):
        """测试按策略ID过滤会话"""
        mock_repo.find_by_strategy_id.return_value = [mock_session]
        
        response = client.get(f'/api/screening/sessions?strategy_id={TEST_STRATEGY_ID}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sessions' in data
        assert len(data['sessions']) == 1
        
        # 验证调用了正确的方法
        mock_repo.find_by_strategy_id.assert_called_once()
    
    def test_list_sessions_invalid_strategy_id(self, client, mock_repo):
        """测试无效的策略ID格式"""
        response = client.get('/api/screening/sessions?strategy_id=invalid-uuid')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_list_sessions_response_format(self, client, mock_repo, mock_session):
        """测试响应格式（摘要格式）"""
        mock_repo.find_recent.return_value = [mock_session]
        
        response = client.get('/api/screening/sessions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # 验证摘要格式包含的字段
        session = data['sessions'][0]
        assert 'session_id' in session
        assert 'strategy_id' in session
        assert 'strategy_name' in session
        assert 'executed_at' in session
        assert 'total_scanned' in session
        assert 'matched_count' in session
        assert 'match_rate' in session
        assert 'execution_time' in session
        
        # 摘要格式不应包含详细字段
        assert 'top_stocks' not in session
        assert 'other_stock_codes' not in session
        assert 'filters_snapshot' not in session
        assert 'scoring_config_snapshot' not in session



# ==================== 测试 GET /api/screening/sessions/<id> ====================


class TestGetSession:
    """测试获取会话详情端点 (Requirements 8.8)"""
    
    def test_get_session_success(self, client, mock_repo, mock_session):
        """测试成功获取会话详情"""
        mock_repo.find_by_id.return_value = mock_session
        
        response = client.get(f'/api/screening/sessions/{TEST_SESSION_ID}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['session_id'] == TEST_SESSION_ID
        assert data['strategy_id'] == TEST_STRATEGY_ID
        assert data['strategy_name'] == 'Test Strategy'
        assert data['total_scanned'] == 1000
        assert data['matched_count'] == 50
        assert data['match_rate'] == 0.05
        assert data['execution_time'] == 1.5
        
        # 详情格式应包含完整字段
        assert 'top_stocks' in data
        assert 'other_stock_codes' in data
        assert 'filters_snapshot' in data
        assert 'scoring_config_snapshot' in data
    
    def test_get_session_not_found(self, client, mock_repo):
        """测试会话不存在 (Requirements 8.12)"""
        mock_repo.find_by_id.return_value = None
        nonexistent_id = str(uuid.uuid4())
        
        response = client.get(f'/api/screening/sessions/{nonexistent_id}')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert nonexistent_id in data['error']
    
    def test_get_session_invalid_id(self, client, mock_repo):
        """测试无效的 ID 格式 (Requirements 8.11)"""
        response = client.get('/api/screening/sessions/invalid-uuid-format')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


# ==================== 测试控制器初始化 ====================


class TestControllerInitialization:
    """测试控制器初始化"""
    
    def test_controller_not_initialized(self, app):
        """测试未初始化时的错误处理"""
        # 清除初始化
        from contexts.screening.interface.controllers import session_controller
        session_controller._get_session_repo = None
        
        client = app.test_client()
        
        # 未初始化时应抛出 RuntimeError
        with pytest.raises(RuntimeError, match="Session controller not initialized"):
            client.get('/api/screening/sessions')
