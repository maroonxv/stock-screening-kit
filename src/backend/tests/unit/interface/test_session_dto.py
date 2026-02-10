"""
会话 DTO 单元测试

测试 SessionResponse、SessionSummaryResponse 的响应格式化功能。

Requirements:
- 8.10: 实现 DTO 类用于请求验证和响应格式化
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contexts.screening.interface.dto.session_dto import (
    SessionResponse,
    SessionSummaryResponse,
)


class TestSessionResponse:
    """SessionResponse 测试"""
    
    def test_from_domain(self):
        """测试从领域对象创建响应"""
        # 创建 mock 领域对象
        mock_session = MagicMock()
        mock_session.session_id.value = 'session-id-123'
        mock_session.strategy_id.value = 'strategy-id-456'
        mock_session.strategy_name = 'Test Strategy'
        mock_session.executed_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_session.total_scanned = 1000
        mock_session.matched_count = 50
        mock_session.match_rate = 0.05
        mock_session.execution_time = 1.5
        mock_session.top_stocks = []
        mock_session.other_stock_codes = ['600001.SH', '600002.SH']
        mock_session.filters_snapshot.to_dict.return_value = {'operator': 'AND', 'conditions': []}
        mock_session.scoring_config_snapshot.to_dict.return_value = {'weights': {'ROE': 1.0}}
        
        response = SessionResponse.from_domain(mock_session)
        
        assert response.session_id == 'session-id-123'
        assert response.strategy_id == 'strategy-id-456'
        assert response.strategy_name == 'Test Strategy'
        assert '2024-01-01' in response.executed_at
        assert response.total_scanned == 1000
        assert response.matched_count == 50
        assert response.match_rate == 0.05
        assert response.execution_time == 1.5
        assert response.top_stocks == []
        assert response.other_stock_codes == ['600001.SH', '600002.SH']
        assert response.filters_snapshot == {'operator': 'AND', 'conditions': []}
        assert response.scoring_config_snapshot == {'weights': {'ROE': 1.0}}
    
    def test_from_domain_with_top_stocks(self):
        """测试带 top_stocks 的领域对象转换"""
        from contexts.screening.domain.enums.indicator_field import IndicatorField
        
        # 创建 mock scored stock
        mock_scored_stock = MagicMock()
        mock_scored_stock.stock_code.code = '600000.SH'
        mock_scored_stock.stock_name = '浦发银行'
        mock_scored_stock.score = 85.5
        mock_scored_stock.score_breakdown = {IndicatorField.ROE: 0.5}
        mock_scored_stock.indicator_values = {IndicatorField.ROE: 0.15}
        mock_scored_stock.matched_conditions = []
        
        # 创建 mock session
        mock_session = MagicMock()
        mock_session.session_id.value = 'session-id-123'
        mock_session.strategy_id.value = 'strategy-id-456'
        mock_session.strategy_name = 'Test Strategy'
        mock_session.executed_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_session.total_scanned = 1000
        mock_session.matched_count = 50
        mock_session.match_rate = 0.05
        mock_session.execution_time = 1.5
        mock_session.top_stocks = [mock_scored_stock]
        mock_session.other_stock_codes = []
        mock_session.filters_snapshot.to_dict.return_value = {'operator': 'AND'}
        mock_session.scoring_config_snapshot.to_dict.return_value = {'weights': {}}
        
        response = SessionResponse.from_domain(mock_session)
        
        assert len(response.top_stocks) == 1
        assert response.top_stocks[0].stock_code == '600000.SH'
        assert response.top_stocks[0].stock_name == '浦发银行'
        assert response.top_stocks[0].score == 85.5
    
    def test_to_dict(self):
        """测试序列化为字典"""
        from contexts.screening.interface.dto.strategy_dto import ScoredStockResponse
        
        scored_stock = ScoredStockResponse(
            stock_code='600000.SH',
            stock_name='浦发银行',
            score=85.5,
            score_breakdown={'ROE': 0.5},
            indicator_values={'ROE': 0.15},
            matched_conditions=[]
        )
        
        response = SessionResponse(
            session_id='session-id-123',
            strategy_id='strategy-id-456',
            strategy_name='Test Strategy',
            executed_at='2024-01-01T12:00:00+00:00',
            total_scanned=1000,
            matched_count=50,
            match_rate=0.05,
            execution_time=1.5,
            top_stocks=[scored_stock],
            other_stock_codes=['600001.SH'],
            filters_snapshot={'operator': 'AND'},
            scoring_config_snapshot={'weights': {}}
        )
        
        result = response.to_dict()
        
        assert result['session_id'] == 'session-id-123'
        assert result['strategy_id'] == 'strategy-id-456'
        assert result['strategy_name'] == 'Test Strategy'
        assert result['executed_at'] == '2024-01-01T12:00:00+00:00'
        assert result['total_scanned'] == 1000
        assert result['matched_count'] == 50
        assert result['match_rate'] == 0.05
        assert result['execution_time'] == 1.5
        assert len(result['top_stocks']) == 1
        assert result['top_stocks'][0]['stock_code'] == '600000.SH'
        assert result['other_stock_codes'] == ['600001.SH']
        assert result['filters_snapshot'] == {'operator': 'AND'}
        assert result['scoring_config_snapshot'] == {'weights': {}}


class TestSessionSummaryResponse:
    """SessionSummaryResponse 测试"""
    
    def test_from_domain(self):
        """测试从领域对象创建摘要响应"""
        # 创建 mock 领域对象
        mock_session = MagicMock()
        mock_session.session_id.value = 'session-id-123'
        mock_session.strategy_id.value = 'strategy-id-456'
        mock_session.strategy_name = 'Test Strategy'
        mock_session.executed_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_session.total_scanned = 1000
        mock_session.matched_count = 50
        mock_session.match_rate = 0.05
        mock_session.execution_time = 1.5
        
        response = SessionSummaryResponse.from_domain(mock_session)
        
        assert response.session_id == 'session-id-123'
        assert response.strategy_id == 'strategy-id-456'
        assert response.strategy_name == 'Test Strategy'
        assert '2024-01-01' in response.executed_at
        assert response.total_scanned == 1000
        assert response.matched_count == 50
        assert response.match_rate == 0.05
        assert response.execution_time == 1.5
    
    def test_to_dict(self):
        """测试序列化为字典"""
        response = SessionSummaryResponse(
            session_id='session-id-123',
            strategy_id='strategy-id-456',
            strategy_name='Test Strategy',
            executed_at='2024-01-01T12:00:00+00:00',
            total_scanned=1000,
            matched_count=50,
            match_rate=0.05,
            execution_time=1.5
        )
        
        result = response.to_dict()
        
        assert result['session_id'] == 'session-id-123'
        assert result['strategy_id'] == 'strategy-id-456'
        assert result['strategy_name'] == 'Test Strategy'
        assert result['executed_at'] == '2024-01-01T12:00:00+00:00'
        assert result['total_scanned'] == 1000
        assert result['matched_count'] == 50
        assert result['match_rate'] == 0.05
        assert result['execution_time'] == 1.5
        # 确保不包含详细字段
        assert 'top_stocks' not in result
        assert 'other_stock_codes' not in result
        assert 'filters_snapshot' not in result
        assert 'scoring_config_snapshot' not in result
