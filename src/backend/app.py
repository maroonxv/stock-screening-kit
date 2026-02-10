"""Flask 应用入口"""
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

from config import config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # 导入 PO 模型以便 Flask-Migrate 能够检测到它们
    # 这些导入必须在 db.init_app 之后进行
    with app.app_context():
        from contexts.screening.infrastructure.persistence.models import (
            ScreeningStrategyPO,
            ScreeningSessionPO,
            WatchListPO,
        )
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 健康检查端点
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy'}), 200
    
    return app


def register_blueprints(app):
    """注册所有蓝图"""
    # 导入并注册 screening context 的 controllers
    from contexts.screening.interface.controllers.strategy_controller import (
        strategy_bp,
        init_strategy_controller
    )
    from contexts.screening.interface.controllers.session_controller import (
        session_bp,
        init_session_controller
    )
    from contexts.screening.interface.controllers.watchlist_controller import (
        watchlist_bp,
        init_watchlist_controller
    )
    
    # 初始化控制器依赖
    init_strategy_controller(lambda: get_strategy_service(app))
    init_session_controller(lambda: get_session_repo(app))
    init_watchlist_controller(lambda: get_watchlist_service(app))
    
    # 注册蓝图
    app.register_blueprint(strategy_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(watchlist_bp)


def get_strategy_service(app):
    """
    创建并返回 ScreeningStrategyService 实例
    
    这个函数负责组装所有依赖并创建服务实例。
    在实际应用中，这里会创建真实的 Repository 和 Service 实例。
    
    Args:
        app: Flask 应用实例
        
    Returns:
        ScreeningStrategyService 实例
    """
    from contexts.screening.application.services.screening_strategy_service import (
        ScreeningStrategyService
    )
    from contexts.screening.infrastructure.persistence.repositories.screening_strategy_repository_impl import (
        ScreeningStrategyRepositoryImpl
    )
    from contexts.screening.infrastructure.persistence.repositories.screening_session_repository_impl import (
        ScreeningSessionRepositoryImpl
    )
    from contexts.screening.infrastructure.services.scoring_service_impl import (
        ScoringServiceImpl
    )
    from contexts.screening.infrastructure.services.indicator_calculation_service_impl import (
        IndicatorCalculationServiceImpl
    )
    
    # 获取数据库会话
    # 注意：在实际应用中，应该使用 Flask-SQLAlchemy 的 session
    # 这里简化处理，假设使用 db.session
    session = db.session
    
    # 创建 Repository 实例
    strategy_repo = ScreeningStrategyRepositoryImpl(session)
    session_repo = ScreeningSessionRepositoryImpl(session)
    
    # 创建领域服务实例
    scoring_service = ScoringServiceImpl()
    calc_service = IndicatorCalculationServiceImpl()
    
    # 创建市场数据仓储（这里使用 mock，实际应该连接真实数据源）
    # TODO: 实现真实的 MarketDataRepository
    from unittest.mock import MagicMock
    market_data_repo = MagicMock()
    
    # 创建应用服务
    service = ScreeningStrategyService(
        strategy_repo=strategy_repo,
        session_repo=session_repo,
        market_data_repo=market_data_repo,
        scoring_service=scoring_service,
        calc_service=calc_service
    )
    
    return service


def get_session_repo(app):
    """
    创建并返回 IScreeningSessionRepository 实例
    
    Session Controller 直接使用 Repository 而非 Application Service，
    因为会话查询是只读操作，不需要应用层编排。
    
    Args:
        app: Flask 应用实例
        
    Returns:
        IScreeningSessionRepository 实例
    """
    from contexts.screening.infrastructure.persistence.repositories.screening_session_repository_impl import (
        ScreeningSessionRepositoryImpl
    )
    
    session = db.session
    return ScreeningSessionRepositoryImpl(session)


def get_watchlist_service(app):
    """
    创建并返回 WatchListService 实例
    
    Args:
        app: Flask 应用实例
        
    Returns:
        WatchListService 实例
    """
    from contexts.screening.application.services.watchlist_service import (
        WatchListService
    )
    from contexts.screening.infrastructure.persistence.repositories.watchlist_repository_impl import (
        WatchListRepositoryImpl
    )
    
    session = db.session
    watchlist_repo = WatchListRepositoryImpl(session)
    
    return WatchListService(watchlist_repo=watchlist_repo)


def register_error_handlers(app):
    """注册全局错误处理器"""
    from contexts.screening.domain.exceptions import (
        DomainError, ValidationError, DuplicateNameError,
        StrategyNotFoundError, WatchListNotFoundError,
        StockNotFoundError, DuplicateStockError,
        ScoringError, IndicatorCalculationError
    )
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({'error': str(error)}), 400
    
    @app.errorhandler(DuplicateNameError)
    def handle_duplicate_name_error(error):
        return jsonify({'error': str(error)}), 409
    
    @app.errorhandler(DuplicateStockError)
    def handle_duplicate_stock_error(error):
        return jsonify({'error': str(error)}), 409
    
    @app.errorhandler(StrategyNotFoundError)
    def handle_strategy_not_found_error(error):
        return jsonify({'error': str(error)}), 404
    
    @app.errorhandler(WatchListNotFoundError)
    def handle_watchlist_not_found_error(error):
        return jsonify({'error': str(error)}), 404
    
    @app.errorhandler(StockNotFoundError)
    def handle_stock_not_found_error(error):
        return jsonify({'error': str(error)}), 404
    
    @app.errorhandler(ScoringError)
    def handle_scoring_error(error):
        return jsonify({'error': str(error)}), 500
    
    @app.errorhandler(IndicatorCalculationError)
    def handle_indicator_calculation_error(error):
        return jsonify({'error': str(error)}), 500
    
    @app.errorhandler(DomainError)
    def handle_domain_error(error):
        return jsonify({'error': str(error)}), 500
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
