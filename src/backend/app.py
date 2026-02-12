"""Flask 应用入口"""
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import SocketIO

from config import config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()


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
    
    # 初始化 Flask-SocketIO
    # 配置 WebSocket 支持，允许跨域连接
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='threading',  # 使用线程模式以兼容同步代码
    )
    
    # 导入 PO 模型以便 Flask-Migrate 能够检测到它们
    # 这些导入必须在 db.init_app 之后进行
    with app.app_context():
        from contexts.screening.infrastructure.persistence.models import (
            ScreeningStrategyPO,
            ScreeningSessionPO,
            WatchListPO,
            ExecutionTaskPO,
        )
        # 导入 Intelligence Context 的 PO 模型
        from contexts.intelligence.infrastructure.persistence.models.investigation_task_po import (
            InvestigationTaskPO,
        )
    
    # 自动事务管理：成功请求 commit，失败请求 rollback
    @app.after_request
    def _commit_on_success(response):
        if response.status_code < 400:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
        else:
            db.session.rollback()
        return response

    @app.teardown_request
    def _remove_session(exception=None):
        if exception:
            db.session.rollback()
        db.session.remove()

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
    
    # 导入并注册 intelligence context 的 controllers
    from contexts.intelligence.interface.controllers.intelligence_controller import (
        intelligence_bp,
        init_app as init_intelligence_controller
    )
    
    # 初始化控制器依赖
    init_strategy_controller(lambda: get_strategy_service(app))
    init_session_controller(lambda: get_session_repo(app))
    init_watchlist_controller(lambda: get_watchlist_service(app))
    
    # 初始化 intelligence 控制器依赖
    init_intelligence_controller(get_intelligence_service(app))
    
    # 注册蓝图
    app.register_blueprint(strategy_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(intelligence_bp)


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
    
    # 创建市场数据仓储（使用 AKShare 获取真实数据）
    from shared_kernel.infrastructure.akshare_market_data_repository import (
        AKShareMarketDataRepository
    )
    market_data_repo = AKShareMarketDataRepository(max_workers=5)
    
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


def get_intelligence_service(app):
    """
    创建并返回 InvestigationTaskService 实例
    
    负责组装 Intelligence Context 的所有依赖：
    - InvestigationTaskRepositoryImpl: 任务持久化
    - IndustryResearchWorkflowService: 快速行业认知 LangGraph 工作流
    - CredibilityVerificationWorkflowService: 概念可信度验证 LangGraph 工作流
    - WebSocketEmitter: WebSocket 事件推送
    
    Args:
        app: Flask 应用实例
        
    Returns:
        InvestigationTaskService 实例
        
    Requirements: 8.1-8.7
    """
    from contexts.intelligence.application.services.investigation_task_service import (
        InvestigationTaskService
    )
    from contexts.intelligence.infrastructure.persistence.repositories.investigation_task_repository_impl import (
        InvestigationTaskRepositoryImpl
    )
    from contexts.intelligence.interface.websocket.websocket_emitter import (
        WebSocketEmitter
    )
    from contexts.intelligence.infrastructure.ai.industry_research_workflow import (
        IndustryResearchWorkflowService,
        create_redis_checkpointer,
    )
    from contexts.intelligence.infrastructure.ai.credibility_workflow import (
        CredibilityVerificationWorkflowService
    )
    from contexts.intelligence.infrastructure.ai.deepseek_client import (
        DeepSeekClient,
        DeepSeekConfig,
    )
    
    # 获取数据库会话
    session = db.session
    
    # 创建 Repository 实例
    task_repo = InvestigationTaskRepositoryImpl(session)
    
    # 创建 WebSocket 推送器
    ws_emitter = WebSocketEmitter(socketio=socketio, namespace='/intelligence')
    
    # 创建 DeepSeek 客户端
    # 从环境变量读取 API 配置
    deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    deepseek_base_url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    
    # 创建 DeepSeek 配置
    # 如果 API key 为空，使用占位符（在测试环境中不会实际调用 API）
    if deepseek_api_key:
        deepseek_config = DeepSeekConfig(
            api_key=deepseek_api_key,
            base_url=deepseek_base_url,
        )
        deepseek_client = DeepSeekClient(config=deepseek_config)
    else:
        # 在没有 API key 的情况下，创建一个带有占位符的配置
        # 这允许应用启动，但实际 API 调用会失败
        deepseek_config = DeepSeekConfig(
            api_key='placeholder-key-not-configured',
            base_url=deepseek_base_url,
        )
        deepseek_client = DeepSeekClient(config=deepseek_config)
    
    # 创建 Redis checkpointer（用于 LangGraph 状态持久化）
    checkpointer = create_redis_checkpointer()
    
    # 创建工作流服务实例
    research_service = IndustryResearchWorkflowService(
        deepseek_client=deepseek_client,
        checkpointer=checkpointer,
    )
    
    credibility_service = CredibilityVerificationWorkflowService(
        deepseek_client=deepseek_client,
        checkpointer=checkpointer,
    )
    
    # 创建应用服务
    service = InvestigationTaskService(
        task_repo=task_repo,
        research_service=research_service,
        credibility_service=credibility_service,
        ws_emitter=ws_emitter,
    )
    
    return service


def register_error_handlers(app):
    """注册全局错误处理器"""
    from contexts.screening.domain.exceptions import (
        DomainError, ValidationError, DuplicateNameError,
        StrategyNotFoundError, WatchListNotFoundError,
        StockNotFoundError, DuplicateStockError,
        ScoringError, IndicatorCalculationError
    )
    
    # 导入 Intelligence Context 的异常
    from contexts.intelligence.domain.exceptions import (
        IntelligenceDomainError,
        InvalidTaskStateError,
        TaskNotFoundError,
        AnalysisTimeoutError,
        LLMServiceError,
    )
    
    # === Screening Context 错误处理器 ===
    
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
    
    # === Intelligence Context 错误处理器 ===
    # 根据设计文档的错误处理映射表：
    # - InvalidTaskStateError -> 409 (状态冲突)
    # - TaskNotFoundError -> 404 (任务不存在)
    # - AnalysisTimeoutError -> 504 (分析超时)
    # - LLMServiceError -> 502 (LLM 服务异常)
    
    @app.errorhandler(InvalidTaskStateError)
    def handle_invalid_task_state_error(error):
        """处理无效任务状态转换异常"""
        return jsonify({'error': str(error)}), 409
    
    @app.errorhandler(TaskNotFoundError)
    def handle_task_not_found_error(error):
        """处理任务不存在异常"""
        return jsonify({'error': str(error)}), 404
    
    @app.errorhandler(AnalysisTimeoutError)
    def handle_analysis_timeout_error(error):
        """处理分析超时异常"""
        return jsonify({'error': str(error)}), 504
    
    @app.errorhandler(LLMServiceError)
    def handle_llm_service_error(error):
        """处理 LLM 服务调用异常"""
        return jsonify({'error': str(error)}), 502
    
    @app.errorhandler(IntelligenceDomainError)
    def handle_intelligence_domain_error(error):
        """处理其他智能分析上下文领域异常"""
        return jsonify({'error': str(error)}), 500
    
    # === 通用错误处理器 ===
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app = create_app()
    # 使用 socketio.run 以支持 WebSocket
    socketio.run(app, host='0.0.0.0', port=5015, debug=True, allow_unsafe_werkzeug=True)
