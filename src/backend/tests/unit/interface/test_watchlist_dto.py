"""
自选股列表 DTO 单元测试

测试 CreateWatchlistRequest、AddStockRequest、WatchlistResponse 等
的请求验证和响应格式化功能。

Requirements:
- 8.10: 实现 DTO 类用于请求验证和响应格式化
- 8.11: API 请求包含无效数据时返回 HTTP 400 和描述性错误信息
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contexts.screening.interface.dto.watchlist_dto import (
    CreateWatchlistRequest,
    UpdateWatchlistRequest,
    AddStockRequest,
    WatchedStockResponse,
    WatchlistResponse,
    WatchlistSummaryResponse,
)


class TestCreateWatchlistRequest:
    """CreateWatchlistRequest 测试"""
    
    def test_from_dict_valid_data(self):
        """测试有效数据解析"""
        data = {
            'name': 'My Watchlist',
            'description': 'Test description'
        }
        
        request = CreateWatchlistRequest.from_dict(data)
        
        assert request.name == 'My Watchlist'
        assert request.description == 'Test description'
    
    def test_from_dict_minimal_data(self):
        """测试最小必填数据解析"""
        data = {'name': 'My Watchlist'}
        
        request = CreateWatchlistRequest.from_dict(data)
        
        assert request.name == 'My Watchlist'
        assert request.description is None
    
    def test_from_dict_empty_data(self):
        """测试空数据抛出异常"""
        with pytest.raises(ValueError, match="请求数据不能为空"):
            CreateWatchlistRequest.from_dict({})
        
        with pytest.raises(ValueError, match="请求数据不能为空"):
            CreateWatchlistRequest.from_dict(None)
    
    def test_from_dict_missing_name(self):
        """测试缺少 name 字段抛出异常"""
        data = {'description': 'Test'}
        
        with pytest.raises(ValueError, match="缺少必填字段: name"):
            CreateWatchlistRequest.from_dict(data)
    
    def test_from_dict_empty_name(self):
        """测试空 name 抛出异常"""
        data = {'name': ''}
        
        with pytest.raises(ValueError, match="自选股列表名称不能为空"):
            CreateWatchlistRequest.from_dict(data)
        
        data['name'] = '   '
        with pytest.raises(ValueError, match="自选股列表名称不能为空"):
            CreateWatchlistRequest.from_dict(data)
    
    def test_from_dict_strips_name(self):
        """测试 name 会被去除首尾空格"""
        data = {'name': '  My Watchlist  '}
        
        request = CreateWatchlistRequest.from_dict(data)
        assert request.name == 'My Watchlist'
    
    def test_to_dict(self):
        """测试序列化为字典"""
        request = CreateWatchlistRequest(
            name='My Watchlist',
            description='Test description'
        )
        
        result = request.to_dict()
        
        assert result['name'] == 'My Watchlist'
        assert result['description'] == 'Test description'
    
    def test_to_dict_without_description(self):
        """测试不包含 description 的序列化"""
        request = CreateWatchlistRequest(name='My Watchlist')
        
        result = request.to_dict()
        
        assert result == {'name': 'My Watchlist'}
        assert 'description' not in result


class TestUpdateWatchlistRequest:
    """UpdateWatchlistRequest 测试"""
    
    def test_from_dict_all_fields(self):
        """测试所有字段解析"""
        data = {
            'name': 'Updated Name',
            'description': 'Updated description'
        }
        
        request = UpdateWatchlistRequest.from_dict(data)
        
        assert request.name == 'Updated Name'
        assert request.description == 'Updated description'
    
    def test_from_dict_partial_fields(self):
        """测试部分字段解析"""
        data = {'name': 'New Name'}
        
        request = UpdateWatchlistRequest.from_dict(data)
        
        assert request.name == 'New Name'
        assert request.description is None
    
    def test_from_dict_empty_data(self):
        """测试空数据抛出异常"""
        with pytest.raises(ValueError, match="请求数据不能为空"):
            UpdateWatchlistRequest.from_dict({})
    
    def test_from_dict_empty_name(self):
        """测试空 name 抛出异常"""
        data = {'name': ''}
        
        with pytest.raises(ValueError, match="自选股列表名称不能为空"):
            UpdateWatchlistRequest.from_dict(data)
    
    def test_has_updates_true(self):
        """测试 has_updates 返回 True"""
        request = UpdateWatchlistRequest(name='New Name')
        assert request.has_updates() is True
        
        request = UpdateWatchlistRequest(description='New Desc')
        assert request.has_updates() is True
    
    def test_has_updates_false(self):
        """测试 has_updates 返回 False"""
        request = UpdateWatchlistRequest()
        assert request.has_updates() is False
    
    def test_to_dict_only_non_none(self):
        """测试只序列化非 None 字段"""
        request = UpdateWatchlistRequest(name='New Name')
        
        result = request.to_dict()
        
        assert result == {'name': 'New Name'}
        assert 'description' not in result


class TestAddStockRequest:
    """AddStockRequest 测试"""
    
    def test_from_dict_valid_data(self):
        """测试有效数据解析"""
        data = {
            'stock_code': '600000.SH',
            'stock_name': '浦发银行',
            'note': 'Test note',
            'tags': ['银行', '蓝筹']
        }
        
        request = AddStockRequest.from_dict(data)
        
        assert request.stock_code == '600000.SH'
        assert request.stock_name == '浦发银行'
        assert request.note == 'Test note'
        assert request.tags == ['银行', '蓝筹']
    
    def test_from_dict_minimal_data(self):
        """测试最小必填数据解析"""
        data = {
            'stock_code': '600000.SH',
            'stock_name': '浦发银行'
        }
        
        request = AddStockRequest.from_dict(data)
        
        assert request.stock_code == '600000.SH'
        assert request.stock_name == '浦发银行'
        assert request.note is None
        assert request.tags is None
    
    def test_from_dict_empty_data(self):
        """测试空数据抛出异常"""
        with pytest.raises(ValueError, match="请求数据不能为空"):
            AddStockRequest.from_dict({})
        
        with pytest.raises(ValueError, match="请求数据不能为空"):
            AddStockRequest.from_dict(None)
    
    def test_from_dict_missing_stock_code(self):
        """测试缺少 stock_code 字段抛出异常"""
        data = {'stock_name': '浦发银行'}
        
        with pytest.raises(ValueError, match="缺少必填字段: stock_code"):
            AddStockRequest.from_dict(data)
    
    def test_from_dict_empty_stock_code(self):
        """测试空 stock_code 抛出异常"""
        data = {
            'stock_code': '',
            'stock_name': '浦发银行'
        }
        
        with pytest.raises(ValueError, match="股票代码不能为空"):
            AddStockRequest.from_dict(data)
    
    def test_from_dict_missing_stock_name(self):
        """测试缺少 stock_name 字段抛出异常"""
        data = {'stock_code': '600000.SH'}
        
        with pytest.raises(ValueError, match="缺少必填字段: stock_name"):
            AddStockRequest.from_dict(data)
    
    def test_from_dict_empty_stock_name(self):
        """测试空 stock_name 抛出异常"""
        data = {
            'stock_code': '600000.SH',
            'stock_name': ''
        }
        
        with pytest.raises(ValueError, match="股票名称不能为空"):
            AddStockRequest.from_dict(data)
    
    def test_from_dict_invalid_tags_type(self):
        """测试 tags 类型错误抛出异常"""
        data = {
            'stock_code': '600000.SH',
            'stock_name': '浦发银行',
            'tags': 'invalid'
        }
        
        with pytest.raises(ValueError, match="tags 必须是数组类型"):
            AddStockRequest.from_dict(data)
    
    def test_from_dict_strips_values(self):
        """测试值会被去除首尾空格"""
        data = {
            'stock_code': '  600000.SH  ',
            'stock_name': '  浦发银行  '
        }
        
        request = AddStockRequest.from_dict(data)
        assert request.stock_code == '600000.SH'
        assert request.stock_name == '浦发银行'
    
    def test_to_dict(self):
        """测试序列化为字典"""
        request = AddStockRequest(
            stock_code='600000.SH',
            stock_name='浦发银行',
            note='Test note',
            tags=['银行']
        )
        
        result = request.to_dict()
        
        assert result['stock_code'] == '600000.SH'
        assert result['stock_name'] == '浦发银行'
        assert result['note'] == 'Test note'
        assert result['tags'] == ['银行']
    
    def test_to_dict_without_optional_fields(self):
        """测试不包含可选字段的序列化"""
        request = AddStockRequest(
            stock_code='600000.SH',
            stock_name='浦发银行'
        )
        
        result = request.to_dict()
        
        assert result == {
            'stock_code': '600000.SH',
            'stock_name': '浦发银行'
        }
        assert 'note' not in result
        assert 'tags' not in result


class TestWatchedStockResponse:
    """WatchedStockResponse 测试"""
    
    def test_from_domain(self):
        """测试从领域对象创建响应"""
        # 创建 mock 领域对象
        mock_watched_stock = MagicMock()
        mock_watched_stock.stock_code.code = '600000.SH'
        mock_watched_stock.stock_name = '浦发银行'
        mock_watched_stock.added_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_watched_stock.note = 'Test note'
        mock_watched_stock.tags = ['银行', '蓝筹']
        
        response = WatchedStockResponse.from_domain(mock_watched_stock)
        
        assert response.stock_code == '600000.SH'
        assert response.stock_name == '浦发银行'
        assert '2024-01-01' in response.added_at
        assert response.note == 'Test note'
        assert response.tags == ['银行', '蓝筹']
    
    def test_to_dict(self):
        """测试序列化为字典"""
        response = WatchedStockResponse(
            stock_code='600000.SH',
            stock_name='浦发银行',
            added_at='2024-01-01T12:00:00+00:00',
            note='Test note',
            tags=['银行']
        )
        
        result = response.to_dict()
        
        assert result['stock_code'] == '600000.SH'
        assert result['stock_name'] == '浦发银行'
        assert result['added_at'] == '2024-01-01T12:00:00+00:00'
        assert result['note'] == 'Test note'
        assert result['tags'] == ['银行']


class TestWatchlistResponse:
    """WatchlistResponse 测试"""
    
    def test_from_domain(self):
        """测试从领域对象创建响应"""
        # 创建 mock watched stock
        mock_watched_stock = MagicMock()
        mock_watched_stock.stock_code.code = '600000.SH'
        mock_watched_stock.stock_name = '浦发银行'
        mock_watched_stock.added_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_watched_stock.note = None
        mock_watched_stock.tags = None
        
        # 创建 mock watchlist
        mock_watchlist = MagicMock()
        mock_watchlist.watchlist_id.value = 'watchlist-id-123'
        mock_watchlist.name = 'My Watchlist'
        mock_watchlist.description = 'Test description'
        mock_watchlist.stocks = [mock_watched_stock]
        mock_watchlist.stock_count.return_value = 1
        mock_watchlist.created_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_watchlist.updated_at = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
        
        response = WatchlistResponse.from_domain(mock_watchlist)
        
        assert response.watchlist_id == 'watchlist-id-123'
        assert response.name == 'My Watchlist'
        assert response.description == 'Test description'
        assert len(response.stocks) == 1
        assert response.stocks[0].stock_code == '600000.SH'
        assert response.stock_count == 1
        assert '2024-01-01' in response.created_at
        assert '2024-01-02' in response.updated_at
    
    def test_from_domain_empty_stocks(self):
        """测试空股票列表的领域对象转换"""
        mock_watchlist = MagicMock()
        mock_watchlist.watchlist_id.value = 'watchlist-id-123'
        mock_watchlist.name = 'Empty Watchlist'
        mock_watchlist.description = None
        mock_watchlist.stocks = []
        mock_watchlist.stock_count.return_value = 0
        mock_watchlist.created_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_watchlist.updated_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        
        response = WatchlistResponse.from_domain(mock_watchlist)
        
        assert response.stocks == []
        assert response.stock_count == 0
    
    def test_to_dict(self):
        """测试序列化为字典"""
        watched_stock = WatchedStockResponse(
            stock_code='600000.SH',
            stock_name='浦发银行',
            added_at='2024-01-01T12:00:00+00:00',
            note=None,
            tags=None
        )
        
        response = WatchlistResponse(
            watchlist_id='watchlist-id-123',
            name='My Watchlist',
            description='Test description',
            stocks=[watched_stock],
            stock_count=1,
            created_at='2024-01-01T10:00:00+00:00',
            updated_at='2024-01-02T10:00:00+00:00'
        )
        
        result = response.to_dict()
        
        assert result['watchlist_id'] == 'watchlist-id-123'
        assert result['name'] == 'My Watchlist'
        assert result['description'] == 'Test description'
        assert len(result['stocks']) == 1
        assert result['stocks'][0]['stock_code'] == '600000.SH'
        assert result['stock_count'] == 1
        assert result['created_at'] == '2024-01-01T10:00:00+00:00'
        assert result['updated_at'] == '2024-01-02T10:00:00+00:00'


class TestWatchlistSummaryResponse:
    """WatchlistSummaryResponse 测试"""
    
    def test_from_domain(self):
        """测试从领域对象创建摘要响应"""
        mock_watchlist = MagicMock()
        mock_watchlist.watchlist_id.value = 'watchlist-id-123'
        mock_watchlist.name = 'My Watchlist'
        mock_watchlist.description = 'Test description'
        mock_watchlist.stock_count.return_value = 5
        mock_watchlist.created_at = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        mock_watchlist.updated_at = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
        
        response = WatchlistSummaryResponse.from_domain(mock_watchlist)
        
        assert response.watchlist_id == 'watchlist-id-123'
        assert response.name == 'My Watchlist'
        assert response.description == 'Test description'
        assert response.stock_count == 5
        assert '2024-01-01' in response.created_at
        assert '2024-01-02' in response.updated_at
    
    def test_to_dict(self):
        """测试序列化为字典"""
        response = WatchlistSummaryResponse(
            watchlist_id='watchlist-id-123',
            name='My Watchlist',
            description='Test description',
            stock_count=5,
            created_at='2024-01-01T10:00:00+00:00',
            updated_at='2024-01-02T10:00:00+00:00'
        )
        
        result = response.to_dict()
        
        assert result['watchlist_id'] == 'watchlist-id-123'
        assert result['name'] == 'My Watchlist'
        assert result['description'] == 'Test description'
        assert result['stock_count'] == 5
        assert result['created_at'] == '2024-01-01T10:00:00+00:00'
        assert result['updated_at'] == '2024-01-02T10:00:00+00:00'
        # 确保不包含 stocks 详细列表
        assert 'stocks' not in result
