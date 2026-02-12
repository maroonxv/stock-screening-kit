"""异步执行服务

编排后台策略执行，管理任务生命周期和进度推送。

Requirements: 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3
"""
import logging
from typing import List, Optional, TYPE_CHECKING

from ...domain.enums.task_status import TaskStatus
from ...domain.exceptions import (
    InvalidTaskStateError,
    StrategyNotFoundError,
    TaskNotFoundError,
)
from ...domain.models.execution_task import ExecutionTask
from ...domain.models.screening_session import ScreeningSession
from ...domain.value_objects.identifiers import StrategyId
from ...domain.value_objects.screening_result import ScreeningResult

if TYPE_CHECKING:
    from ...domain.repositories.execution_task_repository import IExecutionTaskRepository
    from ...domain.repositories.screening_strategy_repository import IScreeningStrategyRepository
    from ...domain.repositories.screening_session_repository import IScreeningSessionRepository
    from shared_kernel.interfaces.market_data_repository import IMarketDataRepository
    from ...domain.services.scoring_service import IScoringService
    from ...domain.services.indicator_calculation_service import IIndicatorCalculationService
    from ...infrastructure.services.background_executor import BackgroundExecutor
    from ...interface.websocket.screening_ws_emitter import ScreeningWebSocketEmitter

logger = logging.getLogger(__name__)


class AsyncExecutionService:
    """异步执行服务"""

    PHASE_FETCH_LIST = "fetch_list"
    PHASE_FETCH_DATA = "fetch_data"
    PHASE_FILTER = "filter"
    PHASE_SCORE = "score"
    PHASE_SAVE = "save"

    def __init__(
        self,
        task_repo: 'IExecutionTaskRepository',
        strategy_repo: 'IScreeningStrategyRepository',
        session_repo: 'IScreeningSessionRepository',
        market_data_repo: 'IMarketDataRepository',
        scoring_service: 'IScoringService',
        calc_service: 'IIndicatorCalculationService',
        executor: 'BackgroundExecutor',
        ws_emitter: 'ScreeningWebSocketEmitter',
    ):
        self._task_repo = task_repo
        self._strategy_repo = strategy_repo
        self._session_repo = session_repo
        self._market_data_repo = market_data_repo
        self._scoring_service = scoring_service
        self._calc_service = calc_service
        self._executor = executor
        self._ws_emitter = ws_emitter

    def start_execution(self, strategy_id: str) -> ExecutionTask:
        """启动异步执行，返回任务对象"""
        strategy = self._strategy_repo.find_by_id(
            StrategyId.from_string(strategy_id)
        )
        if not strategy:
            raise StrategyNotFoundError(f"策略 {strategy_id} 不存在")

        task = ExecutionTask.create(strategy_id)
        self._task_repo.save(task)

        self._executor.submit(
            task.task_id,
            self._execute_task,
            task.task_id,
            strategy_id,
        )
        return task

    def _execute_task(self, task_id: str, strategy_id: str) -> None:
        """在后台线程中执行任务（需要 Flask 应用上下文）"""
        from app import create_app, db

        app = create_app()
        with app.app_context():
            # 在新的应用上下文中重新创建 repo 实例
            from ...infrastructure.persistence.repositories.execution_task_repository_impl import (
                ExecutionTaskRepositoryImpl,
            )
            from ...infrastructure.persistence.repositories.screening_strategy_repository_impl import (
                ScreeningStrategyRepositoryImpl,
            )
            from ...infrastructure.persistence.repositories.screening_session_repository_impl import (
                ScreeningSessionRepositoryImpl,
            )

            task_repo = ExecutionTaskRepositoryImpl(db.session)
            strategy_repo = ScreeningStrategyRepositoryImpl(db.session)
            session_repo = ScreeningSessionRepositoryImpl(db.session)

            task = task_repo.find_by_id(task_id)
            if not task:
                return

            try:
                task.start()
                task_repo.save(task)
                db.session.commit()
                self._ws_emitter.emit_status_changed(task_id, TaskStatus.RUNNING.value)

                # 阶段 1: 获取股票列表
                self._update_progress(task, task_repo, db, self.PHASE_FETCH_LIST, 5, "获取股票列表...")
                stock_codes = self._market_data_repo.get_all_stock_codes()
                total_stocks = len(stock_codes)

                if task.is_cancelled:
                    return

                # 阶段 2: 获取股票数据
                self._update_progress(
                    task, task_repo, db, self.PHASE_FETCH_DATA, 10,
                    f"开始获取 {total_stocks} 只股票数据...",
                )
                stocks = self._fetch_stocks_with_progress(
                    task, task_repo, db, stock_codes, total_stocks
                )

                if task.is_cancelled:
                    return

                # 阶段 3: 执行筛选
                strategy = strategy_repo.find_by_id(StrategyId.from_string(strategy_id))
                self._update_progress(task, task_repo, db, self.PHASE_FILTER, 70, "执行筛选条件...")
                matched = self._filter_with_progress(task, task_repo, db, strategy, stocks)

                if task.is_cancelled:
                    return

                # 阶段 4: 评分
                self._update_progress(task, task_repo, db, self.PHASE_SCORE, 85, "计算评分...")
                scored = self._scoring_service.score_stocks(
                    matched, strategy.scoring_config, self._calc_service
                )
                scored.sort(key=lambda s: s.score, reverse=True)

                # 阶段 5: 保存结果
                self._update_progress(task, task_repo, db, self.PHASE_SAVE, 95, "保存结果...")

                result = ScreeningResult(
                    matched_stocks=scored,
                    total_scanned=len(stocks),
                    execution_time=0,
                    filters_applied=strategy.filters,
                    scoring_config=strategy.scoring_config,
                )

                session = ScreeningSession.create_from_result(
                    strategy_id=strategy.strategy_id,
                    strategy_name=strategy.name,
                    result=result,
                )
                session_repo.save(session)

                result_dict = {
                    'session_id': session.session_id.value,
                    'matched_count': len(scored),
                    'total_scanned': len(stocks),
                    'top_stocks': [
                        {'code': s.stock_code.code, 'name': s.stock_name, 'score': s.score}
                        for s in scored[:10]
                    ],
                }

                task.complete(result_dict)
                task_repo.save(task)
                db.session.commit()
                self._ws_emitter.emit_completed(task_id, result_dict)

            except Exception as e:
                logger.exception(f"任务 {task_id} 执行失败")
                try:
                    task.fail(str(e))
                except InvalidTaskStateError:
                    pass
                task_repo.save(task)
                db.session.commit()
                self._ws_emitter.emit_failed(task_id, str(e))

    def _fetch_stocks_with_progress(self, task, task_repo, db, stock_codes, total):
        """带进度报告的股票数据获取"""
        stocks = []
        batch_size = 100

        for i in range(0, len(stock_codes), batch_size):
            if task.is_cancelled:
                return stocks

            batch = stock_codes[i:i + batch_size]
            batch_stocks = self._market_data_repo.get_stocks_by_codes(batch)
            stocks.extend(batch_stocks)

            progress = 10 + int((i + len(batch)) / total * 55)  # 10-65%
            self._update_progress(
                task, task_repo, db, self.PHASE_FETCH_DATA, progress,
                f"已获取 {len(stocks)}/{total} 只股票数据",
            )

        return stocks

    def _filter_with_progress(self, task, task_repo, db, strategy, stocks):
        """带进度报告的筛选"""
        matched = []
        total = len(stocks)

        for i, stock in enumerate(stocks):
            if task.is_cancelled:
                return matched

            if strategy.filters.match(stock, self._calc_service):
                matched.append(stock)

            if i % 100 == 0 and i > 0:
                progress = 70 + int(i / total * 15)  # 70-85%
                self._update_progress(
                    task, task_repo, db, self.PHASE_FILTER, progress,
                    f"已筛选 {i}/{total}，匹配 {len(matched)} 只",
                )

        return matched

    def _update_progress(self, task, task_repo, db, phase, progress, message):
        """更新进度并推送"""
        task.update_progress(progress, phase)
        task_repo.save(task)
        db.session.commit()
        self._ws_emitter.emit_progress(task.task_id, phase, progress, message)

    def get_task(self, task_id: str) -> Optional[ExecutionTask]:
        return self._task_repo.find_by_id(task_id)

    def list_tasks(self, limit: int = 20) -> List[ExecutionTask]:
        return self._task_repo.find_recent(limit)

    def cancel_task(self, task_id: str) -> bool:
        task = self._task_repo.find_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"任务 {task_id} 不存在")

        task.cancel()
        self._task_repo.save(task)
        self._executor.cancel(task_id)
        self._ws_emitter.emit_status_changed(task_id, TaskStatus.CANCELLED.value)
        return True
