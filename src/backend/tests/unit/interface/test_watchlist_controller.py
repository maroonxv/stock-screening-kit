"""
WatchList Controller 单元测试

测试自选股列表 REST API 端点的请求处理和响应格式化功能。

Requirements:
- 8.9: CRUD 端点 /api/screening/watchlists
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

from contexts.screening.interface.controllers.watchlist_controller import (
    watchlist_bp,
    init_watchlist_controller,
)
from contexts.screening.domain.exceptions import (
    DuplicateNameError,
    DuplicateStockError,
    StockNotFoundError,
    WatchListNotFoundError,
)

# 使用有效的 UUID 作为测试 ID
TEST_WATCHLIST_ID = str(uuid.uuid4())


@pytest.fixture
def app():
    """创建测试 Flask 应用"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(watchlist_bp)
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
def mock_watchlist():
    mock = MagicMock()
    mock.watchlist_id.value = TEST_WATCHLIST_ID
    mock.name = 'Test Watchlist'
    mock.description = 'Test description'
    mock.stocks = []
    mock.stock_count.return_value = 0
    mock.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock.updated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return mock


@pytest.fixture
def mock_watchlist_with_stocks():
    mock = MagicMock()
    mock.watchlist_id.value = TEST_WATCHLIST_ID
    mock.name = 'Test Watchlist'
    mock.description = 'Test description'
    mock_stock = MagicMock()
    mock_stock.stock_code.code = '600000.SH'
    mock_stock.stock_name = '浦发银行'
    mock_stock.added_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_stock.note = 'Test note'
    mock_stock.tags = ['银行', '金融']
    mock.stocks = [mock_stock]
    mock.stock_count.return_value = 1
    mock.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock.updated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return mock


@pytest.fixture(autouse=True)
def setup_controller(mock_service):
    init_watchlist_controller(lambda: mock_service)
    yield
    from contexts.screening.interface.controllers import watchlist_controller
    watchlist_controller._get_watchlist_service = None


class TestCreateWatchlist:
    def test_create_watchlist_success(self, client, mock_service, mock_watchlist):
        mock_service.create_watchlist.return_value = mock_watchlist
        request_data = {'name': 'Test Watchlist', 'description': 'Test description'}
        response = client.post('/api/screening/watchlists', data=json.dumps(request_data), content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['watchlist_id'] == TEST_WATCHLIST_ID
        assert data['name'] == 'Test Watchlist'
        mock_service.create_watchlist.assert_called_once_with(name='Test Watchlist', description='Test description')

    def test_create_watchlist_minimal(self, client, mock_service, mock_watchlist):
        mock_watchlist.description = None
        mock_service.create_watchlist.return_value = mock_watchlist
        response = client.post('/api/screening/watchlists', data=json.dumps({'name': 'Test Watchlist'}), content_type='application/json')
        assert response.status_code == 201
        mock_service.create_watchlist.assert_called_once_with(name='Test Watchlist', description=None)

    def test_create_watchlist_missing_name(self, client, mock_service):
        response = client.post('/api/screening/watchlists', data=json.dumps({'description': 'Test'}), content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'name' in data['error'].lower()

    def test_create_watchlist_empty_name(self, client, mock_service):
        response = client.post('/api/screening/watchlists', data=json.dumps({'name': '   '}), content_type='application/json')
        assert response.status_code == 400

    def test_create_watchlist_duplicate_name(self, client, mock_service):
        mock_service.create_watchlist.side_effect = DuplicateNameError("已存在")
        response = client.post('/api/screening/watchlists', data=json.dumps({'name': 'Test'}), content_type='application/json')
        assert response.status_code == 409

    def test_create_watchlist_empty_body(self, client, mock_service):
        response = client.post('/api/screening/watchlists', data='', content_type='application/json')
        assert response.status_code == 400


class TestListWatchlists:
    def test_list_watchlists_default_params(self, client, mock_service, mock_watchlist):
        mock_service.list_watchlists.return_value = [mock_watchlist]
        response = client.get('/api/screening/watchlists')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'watchlists' in data
        assert len(data['watchlists']) == 1
        assert data['limit'] == 100
        assert data['offset'] == 0
        mock_service.list_watchlists.assert_called_once_with(limit=100, offset=0)

    def test_list_watchlists_custom_params(self, client, mock_service, mock_watchlist):
        mock_service.list_watchlists.return_value = [mock_watchlist]
        response = client.get('/api/screening/watchlists?limit=10&offset=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 10
        assert data['offset'] == 5
        mock_service.list_watchlists.assert_called_once_with(limit=10, offset=5)

    def test_list_watchlists_limit_validation(self, client, mock_service):
        mock_service.list_watchlists.return_value = []
        response = client.get('/api/screening/watchlists?limit=-1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 1
        response = client.get('/api/screening/watchlists?limit=2000')
        data = json.loads(response.data)
        assert data['limit'] == 1000

    def test_list_watchlists_offset_validation(self, client, mock_service):
        mock_service.list_watchlists.return_value = []
        response = client.get('/api/screening/watchlists?offset=-5')
        data = json.loads(response.data)
        assert data['offset'] == 0

    def test_list_watchlists_empty_result(self, client, mock_service):
        mock_service.list_watchlists.return_value = []
        response = client.get('/api/screening/watchlists')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['watchlists'] == []

    def test_list_watchlists_response_format(self, client, mock_service, mock_watchlist):
        mock_service.list_watchlists.return_value = [mock_watchlist]
        response = client.get('/api/screening/watchlists')
        data = json.loads(response.data)
        watchlist = data['watchlists'][0]
        assert 'watchlist_id' in watchlist
        assert 'name' in watchlist
        assert 'stock_count' in watchlist
        assert 'stocks' not in watchlist


class TestGetWatchlist:
    def test_get_watchlist_success(self, client, mock_service, mock_watchlist_with_stocks):
        mock_service.get_watchlist.return_value = mock_watchlist_with_stocks
        response = client.get(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['watchlist_id'] == TEST_WATCHLIST_ID
        assert data['stock_count'] == 1
        assert 'stocks' in data
        assert len(data['stocks']) == 1
        assert data['stocks'][0]['stock_code'] == '600000.SH'

    def test_get_watchlist_not_found(self, client, mock_service):
        mock_service.get_watchlist.return_value = None
        nid = str(uuid.uuid4())
        response = client.get(f'/api/screening/watchlists/{nid}')
        assert response.status_code == 404

    def test_get_watchlist_invalid_id(self, client, mock_service):
        mock_service.get_watchlist.side_effect = ValueError("Invalid UUID")
        response = client.get('/api/screening/watchlists/invalid-id')
        assert response.status_code == 400


class TestUpdateWatchlist:
    def test_update_watchlist_success(self, client, mock_service, mock_watchlist):
        mock_service.update_watchlist.return_value = mock_watchlist
        request_data = {'name': 'Updated Watchlist', 'description': 'Updated description'}
        response = client.put(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}', data=json.dumps(request_data), content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['watchlist_id'] == TEST_WATCHLIST_ID
        mock_service.update_watchlist.assert_called_once_with(watchlist_id_str=TEST_WATCHLIST_ID, name='Updated Watchlist', description='Updated description')

    def test_update_watchlist_not_found(self, client, mock_service):
        mock_service.update_watchlist.side_effect = WatchListNotFoundError("列表不存在")
        nid = str(uuid.uuid4())
        response = client.put(f'/api/screening/watchlists/{nid}', data=json.dumps({'name': 'Updated'}), content_type='application/json')
        assert response.status_code == 404

    def test_update_watchlist_duplicate_name(self, client, mock_service):
        mock_service.update_watchlist.side_effect = DuplicateNameError("名称已存在")
        response = client.put(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}', data=json.dumps({'name': 'Dup'}), content_type='application/json')
        assert response.status_code == 409

    def test_update_watchlist_empty_body(self, client, mock_service):
        response = client.put(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}', data='', content_type='application/json')
        assert response.status_code == 400

    def test_update_watchlist_no_updates(self, client, mock_service):
        response = client.put(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}', data=json.dumps({}), content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert '没有需要更新的字段' in data['error']


class TestDeleteWatchlist:
    def test_delete_watchlist_success(self, client, mock_service):
        mock_service.delete_watchlist.return_value = None
        response = client.delete(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}')
        assert response.status_code == 204
        assert response.data == b''
        mock_service.delete_watchlist.assert_called_once_with(TEST_WATCHLIST_ID)

    def test_delete_watchlist_not_found(self, client, mock_service):
        mock_service.delete_watchlist.side_effect = WatchListNotFoundError("列表不存在")
        nid = str(uuid.uuid4())
        response = client.delete(f'/api/screening/watchlists/{nid}')
        assert response.status_code == 404

    def test_delete_watchlist_invalid_id(self, client, mock_service):
        mock_service.delete_watchlist.side_effect = ValueError("Invalid UUID")
        response = client.delete('/api/screening/watchlists/invalid-id')
        assert response.status_code == 400


class TestAddStock:
    def test_add_stock_success(self, client, mock_service, mock_watchlist_with_stocks):
        mock_service.add_stock.return_value = mock_watchlist_with_stocks
        request_data = {'stock_code': '600000.SH', 'stock_name': '浦发银行', 'note': 'Test note', 'tags': ['银行', '金融']}
        response = client.post(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}/stocks', data=json.dumps(request_data), content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['watchlist_id'] == TEST_WATCHLIST_ID
        assert data['stock_count'] == 1
        mock_service.add_stock.assert_called_once_with(watchlist_id_str=TEST_WATCHLIST_ID, stock_code_str='600000.SH', stock_name='浦发银行', note='Test note', tags=['银行', '金融'])

    def test_add_stock_minimal(self, client, mock_service, mock_watchlist_with_stocks):
        mock_service.add_stock.return_value = mock_watchlist_with_stocks
        request_data = {'stock_code': '600000.SH', 'stock_name': '浦发银行'}
        response = client.post(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}/stocks', data=json.dumps(request_data), content_type='application/json')
        assert response.status_code == 200
        mock_service.add_stock.assert_called_once_with(watchlist_id_str=TEST_WATCHLIST_ID, stock_code_str='600000.SH', stock_name='浦发银行', note=None, tags=None)

    def test_add_stock_missing_stock_code(self, client, mock_service):
        response = client.post(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}/stocks', data=json.dumps({'stock_name': '浦发银行'}), content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'stock_code' in data['error'].lower()

    def test_add_stock_missing_stock_name(self, client, mock_service):
        response = client.post(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}/stocks', data=json.dumps({'stock_code': '600000.SH'}), content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'stock_name' in data['error'].lower()

    def test_add_stock_watchlist_not_found(self, client, mock_service):
        mock_service.add_stock.side_effect = WatchListNotFoundError("列表不存在")
        nid = str(uuid.uuid4())
        response = client.post(f'/api/screening/watchlists/{nid}/stocks', data=json.dumps({'stock_code': '600000.SH', 'stock_name': '浦发银行'}), content_type='application/json')
        assert response.status_code == 404

    def test_add_stock_duplicate(self, client, mock_service):
        mock_service.add_stock.side_effect = DuplicateStockError("股票已存在")
        response = client.post(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}/stocks', data=json.dumps({'stock_code': '600000.SH', 'stock_name': '浦发银行'}), content_type='application/json')
        assert response.status_code == 409

    def test_add_stock_empty_body(self, client, mock_service):
        response = client.post(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}/stocks', data='', content_type='application/json')
        assert response.status_code == 400


class TestRemoveStock:
    def test_remove_stock_success(self, client, mock_service, mock_watchlist):
        mock_service.remove_stock.return_value = mock_watchlist
        response = client.delete(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}/stocks/600000.SH')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['watchlist_id'] == TEST_WATCHLIST_ID
        mock_service.remove_stock.assert_called_once_with(watchlist_id_str=TEST_WATCHLIST_ID, stock_code_str='600000.SH')

    def test_remove_stock_watchlist_not_found(self, client, mock_service):
        mock_service.remove_stock.side_effect = WatchListNotFoundError("列表不存在")
        nid = str(uuid.uuid4())
        response = client.delete(f'/api/screening/watchlists/{nid}/stocks/600000.SH')
        assert response.status_code == 404

    def test_remove_stock_not_found(self, client, mock_service):
        mock_service.remove_stock.side_effect = StockNotFoundError("股票不在列表中")
        response = client.delete(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}/stocks/600000.SH')
        assert response.status_code == 404

    def test_remove_stock_invalid_code(self, client, mock_service):
        mock_service.remove_stock.side_effect = ValueError("无效的股票代码格式")
        response = client.delete(f'/api/screening/watchlists/{TEST_WATCHLIST_ID}/stocks/INVALID')
        assert response.status_code == 400


class TestControllerInitialization:
    def test_controller_not_initialized(self, app):
        from contexts.screening.interface.controllers import watchlist_controller
        watchlist_controller._get_watchlist_service = None
        client = app.test_client()
        with pytest.raises(RuntimeError, match="Watchlist controller not initialized"):
            client.get('/api/screening/watchlists')
