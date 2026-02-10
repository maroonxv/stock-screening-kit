"""
策略 DTO 单元测试

测试 CreateStrategyRequest、UpdateStrategyRequest、StrategyResponse、ScreeningResultResponse
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

from contexts.screening.interface.dto.strategy_dto import (
    CreateStrategyRequest,
    UpdateStrategyRequest,
    StrategyResponse,
    ScoredStockResponse,
    ScreeningResultResponse,
)


class TestCreateStrategyRequest:
    """CreateStrategyRequest 测试"""
    
    def test_from_dict_valid_data(self):
        """测试有效数据解析"""
        data = {
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
            'tags': ['tag1', 'tag2']
        }
        
        request = CreateStrategyRequest.from_dict(data)
        
        assert request.name == 'Test Strategy'
        assert request.filters == data['filters']
        assert request.scoring_config == data['scoring_config']
        assert request.description == 'Test description'
        assert request.tags == ['tag1', 'tag2']
    
    def test_from_dict_minimal_data(self):
        """测试最小必填数据解析"""
        data = {
            'name': 'Test Strategy',
            'filters': {'operator': 'AND', 'conditions': []},
            'scoring_config': {'weights': {'ROE': 1.0}}
        }
        
        request = CreateStrategyRequest.from_dict(data)
        
        assert request.name == 'Test Strategy'
        assert request.description is None
        assert request.tags is None
    
    def test_from_dict_empty_data(self):
        """测试空数据抛出异常"""
        with pytest.raises(ValueError, match="请求数据不能为空"):
            CreateStrategyRequest.from_dict({})
        
        with pytest.raises(ValueError, match="请求数据不能为空"):
            CreateStrategyRequest.from_dict(None)
    
    def test_from_dict_missing_name(self):
        """测试缺少 name 字段抛出异常"""
        data = {
            'filters': {'operator': 'AND'},
            'scoring_config': {'weights': {}}
        }
        
        with pytest.raises(ValueError, match="缺少必填字段: name"):
            CreateStrategyRequest.from_dict(data)
    
    def test_from_dict_empty_name(self):
        """测试空 name 抛出异常"""
        data = {
            'name': '',
            'filters': {'operator': 'AND'},
            'scoring_config': {'weights': {}}
        }
        
        with pytest.raises(ValueError, match="策略名称不能为空"):
            CreateStrategyRequest.from_dict(data)
        
        data['name'] = '   '
        with pytest.raises(ValueError, match="策略名称不能为空"):
            CreateStrategyRequest.from_dict(data)
    
    def test_from_dict_missing_filters(self):
        """测试缺少 filters 字段抛出异常"""
        data = {
            'name': 'Test',
            'scoring_config': {'weights': {}}
        }
        
        with pytest.raises(ValueError, match="缺少必填字段: filters"):
            CreateStrategyRequest.from_dict(data)
    
    def test_from_dict_invalid_filters_type(self):
        """测试 filters 类型错误抛出异常"""
        data = {
            'name': 'Test',
            'filters': 'invalid',
            'scoring_config': {'weights': {}}
        }
        
        with pytest.raises(ValueError, match="filters 必须是对象类型"):
            CreateStrategyRequest.from_dict(data)
    
    def test_from_dict_missing_scoring_config(self):
        """测试缺少 scoring_config 字段抛出异常"""
        data = {
            'name': 'Test',
            'filters': {'operator': 'AND'}
        }
        
        with pytest.raises(ValueError, match="缺少必填字段: scoring_config"):
            CreateStrategyRequest.from_dict(data)
    
    def test_from_dict_invalid_scoring_config_type(self):
        """测试 scoring_config 类型错误抛出异常"""
        data = {
            'name': 'Test',
            'filters': {'operator': 'AND'},
            'scoring_config': 'invalid'
        }
        
        with pytest.raises(ValueError, match="scoring_config 必须是对象类型"):
            CreateStrategyRequest.from_dict(data)
    
    def test_from_dict_invalid_tags_type(self):
        """测试 tags 类型错误抛出异常"""
        data = {
            'name': 'Test',
            'filters': {'operator': 'AND'},
            'scoring_config': {'weights': {}},
            'tags': 'invalid'
        }
        
        with pytest.raises(ValueError, match="tags 必须是数组类型"):
            CreateStrategyRequest.from_dict(data)
    
    def test_from_dict_strips_name(self):
        """测试 name 会被去除首尾空格"""
        data = {
            'name': '  Test Strategy  ',
            'filters': {'operator': 'AND'},
            'scoring_config': {'weights': {}}
        }
        
        request = CreateStrategyRequest.from_dict(data)
        assert request.name == 'Test Strategy'
    
    def test_to_dict(self):
        """测试序列化为字典"""
        request = CreateStrategyRequest(
            name='Test',
            filters={'operator': 'AND'},
            scoring_config={'weights': {}},
            description='Desc',
            tags=['tag1']
        )
        
        result = request.to_dict()
        
        assert result['name'] == 'Test'
        assert result['filters'] == {'operator': 'AND'}
        assert result['scoring_config'] == {'weights': {}}
        assert result['description'] == 'Desc'
        assert result['tags'] == ['tag1']
    
    def test_to_dict_without_optional_fields(self):
        """测试不包含可选字段的序列化"""
        request = CreateStrategyRequest(
            name='Test',
            filters={'operator': 'AND'},
            scoring_config={'weights': {}}
        )
        
        result = request.to_dict()
        
        assert 'description' not in result
        assert 'tags' not in result


class TestUpdateStrategyRequest:
    """UpdateStrategyRequest 测试"""
    
    def test_from_dict_all_fields(self):
        """测试所有字段解析"""
        data = {
            'name': 'Updated Name',
            'filters': {'operator': 'OR'},
            'scoring_config': {'weights': {'PE': 1.0}},
            'description': 'Updated desc',
            'tags': ['new_tag']
        }
        
        request = UpdateStrategyRequest.from_dict(data)
        
        assert request.name == 'Updated Name'
        assert request.filters == {'operator': 'OR'}
        assert request.scoring_config == {'weights': {'PE': 1.0}}
        assert request.description == 'Updated desc'
        assert request.tags == ['new_tag']
    
    def test_from_dict_partial_fields(self):
        """测试部分字段解析"""
        data = {'name': 'New Name'}
        
        request = UpdateStrategyRequest.from_dict(data)
        
        assert request.name == 'New Name'
        assert request.filters is None
        assert request.scoring_config is None
        assert request.description is None
        assert request.tags is None
    
    def test_from_dict_empty_data(self):
        """测试空数据返回无更新的请求对象"""
        request = UpdateStrategyRequest.from_dict({})
        assert request.name is None
        assert request.filters is None
        assert request.scoring_config is None
        assert request.description is None
        assert request.tags is None
        assert not request.has_updates()
    
    def test_from_dict_empty_name(self):
        """测试空 name 抛出异常"""
        data = {'name': ''}
        
        with pytest.raises(ValueError, match="策略名称不能为空"):
            UpdateStrategyRequest.from_dict(data)
    
    def test_from_dict_invalid_filters_type(self):
        """测试 filters 类型错误抛出异常"""
        data = {'filters': 'invalid'}
        
        with pytest.raises(ValueError, match="filters 必须是对象类型"):
            UpdateStrategyRequest.from_dict(data)
    
    def test_from_dict_invalid_scoring_config_type(self):
        """测试 scoring_config 类型错误抛出异常"""
        data = {'scoring_config': 'invalid'}
        
        with pytest.raises(ValueError, match="scoring_config 必须是对象类型"):
            UpdateStrategyRequest.from_dict(data)
    
    def test_from_dict_invalid_tags_type(self):
        """测试 tags 类型错误抛出异常"""
        data = {'tags': 'invalid'}
        
        with pytest.raises(ValueError, match="tags 必须是数组类型"):
            UpdateStrategyRequest.from_dict(data)
    
    def test_has_updates_true(self):
        """测试 has_updates 返回 True"""
        request = UpdateStrategyRequest(name='New Name')
        assert request.has_updates() is True
        
        request = UpdateStrategyRequest(filters={'operator': 'AND'})
        assert request.has_updates() is True
    
    def test_has_updates_false(self):
        """测试 has_updates 返回 False"""
        request = UpdateStrategyRequest()
        assert request.has_updates() is False
    
    def test_to_dict_only_non_none(self):
        """测试只序列化非 None 字段"""
        request = UpdateStrategyRequest(name='New Name', description='Desc')
        
        result = request.to_dict()
        
        assert result == {'name': 'New Name', 'description': 'Desc'}
        assert 'filters' not in result
        assert 'scoring_config' not in result
        assert 'tags' not in result


class TestStrategyResponse:
    """StrategyResponse 测试"""
    
    def test_from_domain(self):
        """测试从领域对象创建响应"""
        # 创建 mock 领域对象
        mock_strategy = MagicMock()
        mock_strategy.strategy_id.value = 'test-id-123'
        mock_strategy.name = 'Test Strategy'
        mock_strategy.description = 'Test description'
        mock_strategy.filters.to_dict.return_value = {'operator': 'AND', 'conditions': []}
        mock_strategy.scoring_config.to_dict.return_value = {'weights': {'ROE': 1.0}}
        mock_strategy.tags = ['tag1', 'tag2']
        mock_strategy.is_template = False
        mock_strategy.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_strategy.updated_at = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        
        response = StrategyResponse.from_domain(mock_strategy)
        
        assert response.strategy_id == 'test-id-123'
        assert response.name == 'Test Strategy'
        assert response.description == 'Test description'
        assert response.filters == {'operator': 'AND', 'conditions': []}
        assert response.scoring_config == {'weights': {'ROE': 1.0}}
        assert response.tags == ['tag1', 'tag2']
        assert response.is_template is False
        assert '2024-01-01' in response.created_at
        assert '2024-01-02' in response.updated_at
    
    def test_to_dict(self):
        """测试序列化为字典"""
        response = StrategyResponse(
            strategy_id='test-id',
            name='Test',
            description='Desc',
            filters={'operator': 'AND'},
            scoring_config={'weights': {}},
            tags=['tag1'],
            is_template=True,
            created_at='2024-01-01T00:00:00+00:00',
            updated_at='2024-01-02T00:00:00+00:00'
        )
        
        result = response.to_dict()
        
        assert result['strategy_id'] == 'test-id'
        assert result['name'] == 'Test'
        assert result['description'] == 'Desc'
        assert result['filters'] == {'operator': 'AND'}
        assert result['scoring_config'] == {'weights': {}}
        assert result['tags'] == ['tag1']
        assert result['is_template'] is True
        assert result['created_at'] == '2024-01-01T00:00:00+00:00'
        assert result['updated_at'] == '2024-01-02T00:00:00+00:00'


class TestScoredStockResponse:
    """ScoredStockResponse 测试"""
    
    def test_from_domain(self):
        """测试从领域对象创建响应"""
        from contexts.screening.domain.enums.indicator_field import IndicatorField
        
        # 创建 mock 领域对象
        mock_scored_stock = MagicMock()
        mock_scored_stock.stock_code.code = '600000.SH'
        mock_scored_stock.stock_name = '浦发银行'
        mock_scored_stock.score = 85.5
        mock_scored_stock.score_breakdown = {IndicatorField.ROE: 0.5, IndicatorField.PE: 0.3}
        mock_scored_stock.indicator_values = {IndicatorField.ROE: 0.15, IndicatorField.PE: 10.5}
        mock_scored_stock.matched_conditions = []
        
        response = ScoredStockResponse.from_domain(mock_scored_stock)
        
        assert response.stock_code == '600000.SH'
        assert response.stock_name == '浦发银行'
        assert response.score == 85.5
        assert 'ROE' in response.score_breakdown
        assert 'PE' in response.score_breakdown
        assert 'ROE' in response.indicator_values
        assert 'PE' in response.indicator_values
    
    def test_to_dict(self):
        """测试序列化为字典"""
        response = ScoredStockResponse(
            stock_code='600000.SH',
            stock_name='浦发银行',
            score=85.5,
            score_breakdown={'ROE': 0.5},
            indicator_values={'ROE': 0.15},
            matched_conditions=[]
        )
        
        result = response.to_dict()
        
        assert result['stock_code'] == '600000.SH'
        assert result['stock_name'] == '浦发银行'
        assert result['score'] == 85.5
        assert result['score_breakdown'] == {'ROE': 0.5}
        assert result['indicator_values'] == {'ROE': 0.15}
        assert result['matched_conditions'] == []


class TestScreeningResultResponse:
    """ScreeningResultResponse 测试"""
    
    def test_from_domain(self):
        """测试从领域对象创建响应"""
        # 创建 mock 领域对象
        mock_result = MagicMock()
        mock_result.matched_stocks = []
        mock_result.total_scanned = 1000
        mock_result.matched_count = 50
        mock_result.match_rate = 0.05
        mock_result.execution_time = 1.5
        mock_result.filters_applied.to_dict.return_value = {'operator': 'AND'}
        mock_result.scoring_config.to_dict.return_value = {'weights': {}}
        mock_result.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        response = ScreeningResultResponse.from_domain(mock_result)
        
        assert response.matched_stocks == []
        assert response.total_scanned == 1000
        assert response.matched_count == 50
        assert response.match_rate == 0.05
        assert response.execution_time == 1.5
        assert response.filters_applied == {'operator': 'AND'}
        assert response.scoring_config == {'weights': {}}
        assert '2024-01-01' in response.timestamp
    
    def test_to_dict(self):
        """测试序列化为字典"""
        response = ScreeningResultResponse(
            matched_stocks=[],
            total_scanned=1000,
            matched_count=50,
            match_rate=0.05,
            execution_time=1.5,
            filters_applied={'operator': 'AND'},
            scoring_config={'weights': {}},
            timestamp='2024-01-01T12:00:00+00:00'
        )
        
        result = response.to_dict()
        
        assert result['matched_stocks'] == []
        assert result['total_scanned'] == 1000
        assert result['matched_count'] == 50
        assert result['match_rate'] == 0.05
        assert result['execution_time'] == 1.5
        assert result['filters_applied'] == {'operator': 'AND'}
        assert result['scoring_config'] == {'weights': {}}
        assert result['timestamp'] == '2024-01-01T12:00:00+00:00'
