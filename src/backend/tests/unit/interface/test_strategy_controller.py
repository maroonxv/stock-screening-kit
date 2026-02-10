"""
Strategy Controller 单元测试

测试筛选策略 REST API 端点的请求处理和响应格式化功能。

Requirements:
- 8.1: POST /api/screening/strategies 用于创建新的筛选策略
- 8.2: GET /api/screening/strategies 用于分页列出所有策略
- 8.3: GET /api/screening/strategies/<id> 用于按 ID 获取策略
- 8.4: PUT /api/screening/strategies/<id> 用于更新策略
- 8.5: DELETE /api/screening/strategies/<id> 用于删除策略
- 8.6: POST /api/screening/strategies/<id>/execute 用于执行策略并返回结果
- 8.11: API 请求包含无效数据时返回 HTTP 400 和描述性错误信息
- 8.12: 请求的资源不存在时返回 HTTP 404
"""
import pytest
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock
from flask import Flask

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contexts.screening.interface.controllers.strategy_controller import (
    strategy_bp,
    init_strategy_controller,
)
from contexts.screening.domain.exceptions import (
    DuplicateNameError,
    StrategyNotFoundError,
)


@pytest.fixture
def app():
    """创建测试 Flask 应用"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(strategy_bp)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def mock_service():
    """创建 mock 服务"""
    return MagicMock()


@pytest.fixture
def mock_strategy():
    """创建 mock 策略对象"""
    mock = MagicMock()
    mock.strategy_id.value = 'test-strategy-id-123'
    mock.name = 'Test Strategy'
    mock.description = 'Test description'
    mock.filters.to_dict.return_value = {
        'group_id': 'test-group',
        'operator': 'AND',
        'conditions': [],
        'sub_groups': []
    }
    mock.scoring_config.to_dict.return_value = {
        'weights': {'ROE': 1.0},
        'normalization_method': 'min_max'
    }
    mock.tags = ['test']
    mock.is_template = False
    mock.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock.updated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return mock


@pytest.fixture
def mock_result():
    """创建 mock 筛选结果对象"""
    mock = MagicMock()
    mock.matched_stocks = []
    mock.total_scanned = 100
    mock.matched_count = 0
    mock.match_rate = 0.0
    mock.execution_time = 0.5
    mock.filters_applied.to_dict.return_value = {
        'group_id': 'test-group',
        'operator': 'AND',
        'conditions': [],
        'sub_groups': []
    }
    mock.scoring_config.to_dict.return_value = {
        'weights': {'ROE': 1.0},
        'normalization_method': 'min_max'
    }
    mock.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return mock


@pytest.fixture(autouse=True)
def setup_controller(mock_service):
    """自动初始化控制器"""
    init_strategy_controller(lambda: mock_service)
    yield
    # 清理
    from contexts.screening.interface.controllers import strategy_controller
    strategy_controller._get_strategy_service = None


# ==================== 测试 POST /api/screening/strategies ====================


class TestCreateStrategy:
    """测试创建策略端点 (Requirements 8.1)"""
    
    def test_create_strategy_success(self, client, mock_service, mock_strategy):
        """测试成功创建策略"""
        # 准备
        mock_service.create_strategy.return_value = mock_strategy
        
        request_data = {
            'name': 'Test Strategy',
            'filters': {
                'group_id': 'test-group',
                'operator': 'AND',
                'conditions': [],
                'sub_groups': []
            },
            'scoring_config': {
                'weights': {'ROE': 1.0},
                'normalization_method': 'min_max'
            },
            'description': 'Test description',
            'tags': ['test']
        }
        
        # 执行
        response = client.post(
            '/api/screening/strategies',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # 验证
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['strategy_id'] == 'test-strategy-id-123'
        assert data['name'] == 'Test Strategy'
        assert data['description'] == 'Test description'
        
        # 验证服务调用
        mock_service.create_strategy.assert_called_once_with(
            name='Test Strategy',
            filters_dict=request_data['filters'],
            scoring_config_dict=request_data['scoring_config'],
            description='Test description',
            tags=['test']
        )
    
    def test_create_strategy_missing_name(self, client, mock_service):
        """测试缺少名称字段 (Requirements 8.11)"""
        request_data = {
            'filters': {'group_id': 'test', 'operator': 'AND', 'conditions': []},
            'scoring_config': {'weights': {'ROE': 1.0}, 'normalization_method': 'min_max'}
        }
        
        response = client.post(
            '/api/screening/strategies',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'name' in data['error'].lower()

    
    def test_create_strategy_empty_name(self, client, mock_service):
        """测试空名称 (Requirements 8.11)"""
        request_data = {
            'name': '   ',
            'filters': {'group_id': 'test', 'operator': 'AND', 'conditions': []},
            'scoring_config': {'weights': {'ROE': 1.0}, 'normalization_method': 'min_max'}
        }
        
        response = client.post(
            '/api/screening/strategies',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_strategy_missing_filters(self, client, mock_service):
        """测试缺少筛选条件 (Requirements 8.11)"""
        request_data = {
            'name': 'Test Strategy',
            'scoring_config': {'weights': {'ROE': 1.0}, 'normalization_method': 'min_max'}
        }
        
        response = client.post(
            '/api/screening/strategies',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'filters' in data['error'].lower()
    
    def test_create_strategy_missing_scoring_config(self, client, mock_service):
        """测试缺少评分配置 (Requirements 8.11)"""
        request_data = {
            'name': 'Test Strategy',
            'filters': {'group_id': 'test', 'operator': 'AND', 'conditions': []}
        }
        
        response = client.post(
            '/api/screening/strategies',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'scoring_config' in data['error'].lower()
    
    def test_create_strategy_duplicate_name(self, client, mock_service):
        """测试重复名称 (Requirements 8.11)"""
        mock_service.create_strategy.side_effect = DuplicateNameError("策略名称 'Test Strategy' 已存在")
        
        request_data = {
            'name': 'Test Strategy',
            'filters': {'group_id': 'test', 'operator': 'AND', 'conditions': []},
            'scoring_config': {'weights': {'ROE': 1.0}, 'normalization_method': 'min_max'}
        }
        
        response = client.post(
            '/api/screening/strategies',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_strategy_empty_body(self, client, mock_service):
        """测试空请求体 (Requirements 8.11)"""
        response = client.post(
            '/api/screening/strategies',
            data='',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


# ==================== 测试 GET /api/screening/strategies ====================


class TestListStrategies:
    """测试列出策略端点 (Requirements 8.2)"""
    
    def test_list_strategies_default_params(self, client, mock_service, mock_strategy):
        """测试使用默认参数列出策略"""
        mock_service.list_strategies.return_value = [mock_strategy]
        
        response = client.get('/api/screening/strategies')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'strategies' in data
        assert len(data['strategies']) == 1
        assert data['limit'] == 100
        assert data['offset'] == 0
        
        mock_service.list_strategies.assert_called_once_with(limit=100, offset=0)
    
    def test_list_strategies_custom_params(self, client, mock_service, mock_strategy):
        """测试使用自定义参数列出策略"""
        mock_service.list_strategies.return_value = [mock_strategy]
        
        response = client.get('/api/screening/strategies?limit=10&offset=5')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 10
        assert data['offset'] == 5
        
        mock_service.list_strategies.assert_called_once_with(limit=10, offset=5)
    
    def test_list_strategies_limit_validation(self, client, mock_service):
        """测试 limit 参数验证"""
        mock_service.list_strategies.return_value = []
        
        # 测试负数 limit
        response = client.get('/api/screening/strategies?limit=-1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 1  # 应该被修正为 1
        
        # 测试超大 limit
        response = client.get('/api/screening/strategies?limit=2000')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 1000  # 应该被限制为 1000
    
    def test_list_strategies_offset_validation(self, client, mock_service):
        """测试 offset 参数验证"""
        mock_service.list_strategies.return_value = []
        
        # 测试负数 offset
        response = client.get('/api/screening/strategies?offset=-5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['offset'] == 0  # 应该被修正为 0
    
    def test_list_strategies_empty_result(self, client, mock_service):
        """测试空结果"""
        mock_service.list_strategies.return_value = []
        
        response = client.get('/api/screening/strategies')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['strategies'] == []



# ==================== 测试 GET /api/screening/strategies/<id> ====================


class TestGetStrategy:
    """测试获取策略详情端点 (Requirements 8.3)"""
    
    def test_get_strategy_success(self, client, mock_service, mock_strategy):
        """测试成功获取策略"""
        mock_service.get_strategy.return_value = mock_strategy
        
        response = client.get('/api/screening/strategies/test-strategy-id-123')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['strategy_id'] == 'test-strategy-id-123'
        assert data['name'] == 'Test Strategy'
        
        mock_service.get_strategy.assert_called_once_with('test-strategy-id-123')
    
    def test_get_strategy_not_found(self, client, mock_service):
        """测试策略不存在 (Requirements 8.12)"""
        mock_service.get_strategy.return_value = None
        
        response = client.get('/api/screening/strategies/nonexistent-id')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_strategy_invalid_id(self, client, mock_service):
        """测试无效的 ID 格式"""
        mock_service.get_strategy.side_effect = ValueError("Invalid UUID")
        
        response = client.get('/api/screening/strategies/invalid-id')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


# ==================== 测试 PUT /api/screening/strategies/<id> ====================


class TestUpdateStrategy:
    """测试更新策略端点 (Requirements 8.4)"""
    
    def test_update_strategy_success(self, client, mock_service, mock_strategy):
        """测试成功更新策略"""
        mock_service.update_strategy.return_value = mock_strategy
        
        request_data = {
            'name': 'Updated Strategy',
            'description': 'Updated description'
        }
        
        response = client.put(
            '/api/screening/strategies/test-strategy-id-123',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['strategy_id'] == 'test-strategy-id-123'
        
        mock_service.update_strategy.assert_called_once()
    
    def test_update_strategy_not_found(self, client, mock_service):
        """测试更新不存在的策略 (Requirements 8.12)"""
        mock_service.update_strategy.side_effect = StrategyNotFoundError("策略不存在")
        
        request_data = {'name': 'Updated Strategy'}
        
        response = client.put(
            '/api/screening/strategies/nonexistent-id',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_update_strategy_duplicate_name(self, client, mock_service):
        """测试更新为重复名称"""
        mock_service.update_strategy.side_effect = DuplicateNameError("名称已存在")
        
        request_data = {'name': 'Duplicate Name'}
        
        response = client.put(
            '/api/screening/strategies/test-strategy-id-123',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_update_strategy_empty_body(self, client, mock_service):
        """测试空请求体 (Requirements 8.11)"""
        response = client.put(
            '/api/screening/strategies/test-strategy-id-123',
            data='',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_update_strategy_no_updates(self, client, mock_service):
        """测试没有更新字段"""
        request_data = {}
        
        response = client.put(
            '/api/screening/strategies/test-strategy-id-123',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert '没有需要更新的字段' in data['error']


# ==================== 测试 DELETE /api/screening/strategies/<id> ====================


class TestDeleteStrategy:
    """测试删除策略端点 (Requirements 8.5)"""
    
    def test_delete_strategy_success(self, client, mock_service):
        """测试成功删除策略"""
        mock_service.delete_strategy.return_value = None
        
        response = client.delete('/api/screening/strategies/test-strategy-id-123')
        
        assert response.status_code == 204
        assert response.data == b''
        
        mock_service.delete_strategy.assert_called_once_with('test-strategy-id-123')
    
    def test_delete_strategy_not_found(self, client, mock_service):
        """测试删除不存在的策略 (Requirements 8.12)"""
        mock_service.delete_strategy.side_effect = StrategyNotFoundError("策略不存在")
        
        response = client.delete('/api/screening/strategies/nonexistent-id')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_delete_strategy_invalid_id(self, client, mock_service):
        """测试无效的 ID 格式"""
        mock_service.delete_strategy.side_effect = ValueError("Invalid UUID")
        
        response = client.delete('/api/screening/strategies/invalid-id')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


# ==================== 测试 POST /api/screening/strategies/<id>/execute ====================


class TestExecuteStrategy:
    """测试执行策略端点 (Requirements 8.6)"""
    
    def test_execute_strategy_success(self, client, mock_service, mock_result):
        """测试成功执行策略"""
        mock_service.execute_strategy.return_value = mock_result
        
        response = client.post('/api/screening/strategies/test-strategy-id-123/execute')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'matched_stocks' in data
        assert 'total_scanned' in data
        assert 'execution_time' in data
        assert data['total_scanned'] == 100
        
        mock_service.execute_strategy.assert_called_once_with('test-strategy-id-123')
    
    def test_execute_strategy_not_found(self, client, mock_service):
        """测试执行不存在的策略 (Requirements 8.12)"""
        mock_service.execute_strategy.side_effect = StrategyNotFoundError("策略不存在")
        
        response = client.post('/api/screening/strategies/nonexistent-id/execute')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_execute_strategy_invalid_id(self, client, mock_service):
        """测试无效的 ID 格式"""
        mock_service.execute_strategy.side_effect = ValueError("Invalid UUID")
        
        response = client.post('/api/screening/strategies/invalid-id/execute')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


# ==================== 测试控制器初始化 ====================


class TestControllerInitialization:
    """测试控制器初始化"""
    
    def test_controller_not_initialized(self, app):
        """测试未初始化时的错误处理"""
        from contexts.screening.interface.controllers import strategy_controller
        strategy_controller._get_strategy_service = None
        
        client = app.test_client()
        
        with pytest.raises(RuntimeError, match="Strategy controller not initialized"):
            client.get('/api/screening/strategies')