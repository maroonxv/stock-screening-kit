"""
App 全局错误处理与蓝图注册 单元测试

测试 app.py 中的全局错误处理器和蓝图注册功能。

Requirements:
- 8.11: WHEN API 请求包含无效数据时, THEN THE Interface_Layer SHALL 返回 HTTP 400 和描述性错误信息
- 8.12: WHEN 请求的资源不存在时, THEN THE Interface_Layer SHALL 返回 HTTP 404
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from flask import Flask

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contexts.screening.domain.exceptions import (
    DomainError,
    ValidationError,
    DuplicateNameError,
    DuplicateStockError,
    StrategyNotFoundError,
    WatchListNotFoundError,
    StockNotFoundError,
    ScoringError,
    IndicatorCalculationError,
)


@pytest.fixture
def app():
    """创建带有全局错误处理器的测试 Flask 应用"""
    app = Flask(__name__)
    app.config['TESTING'] = True

    # 注册错误处理器（直接从 app.py 导入）
    from app import register_error_handlers
    register_error_handlers(app)

    # 创建测试路由，用于触发各种领域异常
    @app.route('/test/validation-error')
    def trigger_validation_error():
        raise ValidationError("字段 name 不能为空")

    @app.route('/test/duplicate-name-error')
    def trigger_duplicate_name_error():
        raise DuplicateNameError("策略名称 'Test' 已存在")

    @app.route('/test/duplicate-stock-error')
    def trigger_duplicate_stock_error():
        raise DuplicateStockError("股票 600000.SH 已存在于列表中")

    @app.route('/test/strategy-not-found-error')
    def trigger_strategy_not_found_error():
        raise StrategyNotFoundError("策略 abc-123 不存在")

    @app.route('/test/watchlist-not-found-error')
    def trigger_watchlist_not_found_error():
        raise WatchListNotFoundError("自选股列表 abc-123 不存在")

    @app.route('/test/stock-not-found-error')
    def trigger_stock_not_found_error():
        raise StockNotFoundError("股票 600000.SH 不在列表中")

    @app.route('/test/scoring-error')
    def trigger_scoring_error():
        raise ScoringError("评分计算失败")

    @app.route('/test/indicator-calculation-error')
    def trigger_indicator_calculation_error():
        raise IndicatorCalculationError("指标计算失败")

    @app.route('/test/domain-error')
    def trigger_domain_error():
        raise DomainError("未知领域错误")

    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


# ==================== 测试 400 错误处理 (Requirements 8.11) ====================


class TestValidationErrorHandler:
    """测试 ValidationError → HTTP 400 映射"""

    def test_validation_error_returns_400(self, client):
        """ValidationError 应返回 HTTP 400"""
        response = client.get('/test/validation-error')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert '字段 name 不能为空' in data['error']

    def test_validation_error_response_format(self, client):
        """ValidationError 响应应包含 JSON 格式的错误信息"""
        response = client.get('/test/validation-error')

        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'error' in data
        assert isinstance(data['error'], str)


# ==================== 测试 404 错误处理 (Requirements 8.12) ====================


class TestNotFoundErrorHandlers:
    """测试 NotFound 类异常 → HTTP 404 映射"""

    def test_strategy_not_found_returns_404(self, client):
        """StrategyNotFoundError 应返回 HTTP 404"""
        response = client.get('/test/strategy-not-found-error')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert '策略 abc-123 不存在' in data['error']

    def test_watchlist_not_found_returns_404(self, client):
        """WatchListNotFoundError 应返回 HTTP 404"""
        response = client.get('/test/watchlist-not-found-error')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert '自选股列表 abc-123 不存在' in data['error']

    def test_stock_not_found_returns_404(self, client):
        """StockNotFoundError 应返回 HTTP 404"""
        response = client.get('/test/stock-not-found-error')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert '股票 600000.SH 不在列表中' in data['error']

    def test_http_404_for_unknown_route(self, client):
        """访问不存在的路由应返回 HTTP 404"""
        response = client.get('/nonexistent/route')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


# ==================== 测试 409 错误处理 ====================


class TestDuplicateErrorHandlers:
    """测试 Duplicate 类异常 → HTTP 409 映射"""

    def test_duplicate_name_returns_409(self, client):
        """DuplicateNameError 应返回 HTTP 409"""
        response = client.get('/test/duplicate-name-error')

        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data
        assert "策略名称 'Test' 已存在" in data['error']

    def test_duplicate_stock_returns_409(self, client):
        """DuplicateStockError 应返回 HTTP 409"""
        response = client.get('/test/duplicate-stock-error')

        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data
        assert '股票 600000.SH 已存在于列表中' in data['error']


# ==================== 测试 500 错误处理 ====================


class TestServerErrorHandlers:
    """测试服务端错误 → HTTP 500 映射"""

    def test_scoring_error_returns_500(self, client):
        """ScoringError 应返回 HTTP 500"""
        response = client.get('/test/scoring-error')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert '评分计算失败' in data['error']

    def test_indicator_calculation_error_returns_500(self, client):
        """IndicatorCalculationError 应返回 HTTP 500"""
        response = client.get('/test/indicator-calculation-error')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert '指标计算失败' in data['error']

    def test_generic_domain_error_returns_500(self, client):
        """未映射的 DomainError 应返回 HTTP 500"""
        response = client.get('/test/domain-error')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


# ==================== 测试蓝图注册 ====================


class TestBlueprintRegistration:
    """测试所有蓝图是否正确注册"""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        """创建使用 SQLite 内存数据库的测试应用，避免 PostgreSQL 依赖"""
        os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        from app import create_app
        from config import TestingConfig

        # 临时覆盖测试配置的数据库 URI
        original_uri = TestingConfig.SQLALCHEMY_DATABASE_URI
        TestingConfig.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        try:
            self.app = create_app('testing')
        finally:
            TestingConfig.SQLALCHEMY_DATABASE_URI = original_uri

    def test_all_blueprints_registered(self):
        """验证所有三个蓝图都已注册到应用"""
        blueprint_names = list(self.app.blueprints.keys())

        # 验证三个蓝图都已注册
        assert 'screening_strategies' in blueprint_names
        assert 'screening_sessions' in blueprint_names
        assert 'screening_watchlists' in blueprint_names

    def test_strategy_routes_registered(self):
        """验证策略相关路由已注册"""
        rules = [rule.rule for rule in self.app.url_map.iter_rules()]

        assert '/api/screening/strategies' in rules
        assert '/api/screening/strategies/<strategy_id>' in rules
        assert '/api/screening/strategies/<strategy_id>/execute' in rules

    def test_session_routes_registered(self):
        """验证会话相关路由已注册"""
        rules = [rule.rule for rule in self.app.url_map.iter_rules()]

        assert '/api/screening/sessions' in rules
        assert '/api/screening/sessions/<session_id>' in rules

    def test_watchlist_routes_registered(self):
        """验证自选股列表相关路由已注册"""
        rules = [rule.rule for rule in self.app.url_map.iter_rules()]

        assert '/api/screening/watchlists' in rules
        assert '/api/screening/watchlists/<watchlist_id>' in rules
        assert '/api/screening/watchlists/<watchlist_id>/stocks' in rules
        assert '/api/screening/watchlists/<watchlist_id>/stocks/<stock_code>' in rules

    def test_health_check_endpoint(self):
        """验证健康检查端点已注册"""
        client = self.app.test_client()

        response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


# ==================== 测试错误响应一致性 ====================


class TestErrorResponseConsistency:
    """测试所有错误响应格式的一致性"""

    def test_all_error_responses_have_error_key(self, client):
        """所有错误响应都应包含 'error' 键"""
        error_routes = [
            '/test/validation-error',
            '/test/duplicate-name-error',
            '/test/duplicate-stock-error',
            '/test/strategy-not-found-error',
            '/test/watchlist-not-found-error',
            '/test/stock-not-found-error',
            '/test/scoring-error',
            '/test/indicator-calculation-error',
            '/test/domain-error',
            '/nonexistent/route',
        ]

        for route in error_routes:
            response = client.get(route)
            data = json.loads(response.data)
            assert 'error' in data, f"Route {route} missing 'error' key in response"
            assert isinstance(data['error'], str), f"Route {route} 'error' should be a string"

    def test_all_error_responses_are_json(self, client):
        """所有错误响应都应是 JSON 格式"""
        error_routes = [
            '/test/validation-error',
            '/test/duplicate-name-error',
            '/test/strategy-not-found-error',
            '/test/domain-error',
            '/nonexistent/route',
        ]

        for route in error_routes:
            response = client.get(route)
            assert response.content_type == 'application/json', \
                f"Route {route} should return JSON, got {response.content_type}"
