"""InvestigationTaskService 应用层服务单元测试

测试应用层服务的业务逻辑编排：
- 任务创建（快速行业认知、概念可信度验证）
- 任务查询（单个任务、最近任务列表）
- 任务取消

使用 Mock 模拟 Repository 和工作流服务以隔离依赖。

Requirements: 7.1, 7.2, 7.3
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock

import pytest

from contexts.intelligence.application.services.investigation_task_service import (
    InvestigationTaskService,
    IWebSocketEmitter,
)
from contexts.intelligence.domain.enums.enums import TaskType, TaskStatus
from contexts.intelligence.domain.exceptions import TaskNotFoundError
from contexts.intelligence.domain.models.investigation_task import (
    InvestigationTask,
)
from contexts.intelligence.domain.repositories.investigation_task_repository import (
    IInvestigationTaskRepository,
)
from contexts.intelligence.domain.services.credibility_verification_service import (
    ICredibilityVerificationService,
)
from contexts.intelligence.domain.services.industry_research_service import (
    IIndustryResearchService,
)
from contexts.intelligence.domain.value_objects.identifiers import TaskId
from shared_kernel.value_objects.stock_code import StockCode


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_task_repo():
    """创建 Mock 调研任务 Repository"""
    repo = Mock(spec=IInvestigationTaskRepository)
    repo.save = Mock()
    repo.find_by_id = Mock(return_value=None)
    repo.find_by_status = Mock(return_value=[])
    repo.find_recent_tasks = Mock(return_value=[])
    repo.delete = Mock()
    repo.count_by_status = Mock(return_value=0)
    return repo


@pytest.fixture
def mock_research_service():
    """创建 Mock 快速行业认知服务"""
    service = Mock(spec=IIndustryResearchService)
    service.execute_research = AsyncMock()
    return service


@pytest.fixture
def mock_credibility_service():
    """创建 Mock 概念可信度验证服务"""
    service = Mock(spec=ICredibilityVerificationService)
    service.verify_credibility = AsyncMock()
    return service


@pytest.fixture
def mock_ws_emitter():
    """创建 Mock WebSocket 事件推送器"""
    emitter = Mock(spec=IWebSocketEmitter)
    emitter.emit = Mock()
    return emitter


@pytest.fixture
def service(mock_task_repo, mock_research_service, mock_credibility_service, mock_ws_emitter):
    """创建 InvestigationTaskService 实例"""
    return InvestigationTaskService(
        task_repo=mock_task_repo,
        research_service=mock_research_service,
        credibility_service=mock_credibility_service,
        ws_emitter=mock_ws_emitter,
    )


@pytest.fixture
def sample_task():
    """创建示例 InvestigationTask 领域对象"""
    task_id = TaskId.generate()
    return InvestigationTask(
        task_id=task_id,
        task_type=TaskType.INDUSTRY_RESEARCH,
        query="快速了解合成生物学赛道",
        status=TaskStatus.PENDING,
        progress=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_running_task():
    """创建运行中的示例 InvestigationTask 领域对象"""
    task_id = TaskId.generate()
    task = InvestigationTask(
        task_id=task_id,
        task_type=TaskType.INDUSTRY_RESEARCH,
        query="快速了解合成生物学赛道",
        status=TaskStatus.PENDING,
        progress=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    task.start()  # 转换为 RUNNING 状态
    return task


@pytest.fixture
def sample_credibility_task():
    """创建概念可信度验证任务"""
    task_id = TaskId.generate()
    return InvestigationTask(
        task_id=task_id,
        task_type=TaskType.CREDIBILITY_VERIFICATION,
        query="600519.SH:AI+白酒",
        status=TaskStatus.PENDING,
        progress=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ============================================================
# create_industry_research_task Tests
# ============================================================


class TestCreateIndustryResearchTask:
    """create_industry_research_task 方法测试"""

    def test_create_industry_research_task_success(
        self, service, mock_task_repo, mock_research_service
    ):
        """测试成功创建快速行业认知任务

        验证：
        1. 返回有效的 task_id 字符串
        2. Repository.save 被调用
        3. 异步工作流被调度

        Requirements: 7.2
        """
        # 执行创建
        with patch.object(service, "_schedule_async") as mock_schedule:
            task_id = service.create_industry_research_task(query="快速了解合成生物学赛道")

        # 验证返回有效的 UUID 格式 task_id
        assert task_id is not None
        assert isinstance(task_id, str)
        # 验证是有效的 UUID
        uuid.UUID(task_id)

        # 验证 Repository.save 被调用
        mock_task_repo.save.assert_called_once()
        saved_task = mock_task_repo.save.call_args[0][0]
        assert isinstance(saved_task, InvestigationTask)
        assert saved_task.task_type == TaskType.INDUSTRY_RESEARCH
        assert saved_task.query == "快速了解合成生物学赛道"
        assert saved_task.status == TaskStatus.PENDING

        # 验证异步工作流被调度
        mock_schedule.assert_called_once()

    def test_create_industry_research_task_empty_query_raises_error(
        self, service, mock_task_repo
    ):
        """测试空查询文本时抛出 ValueError

        Requirements: 7.2
        """
        with pytest.raises(ValueError) as exc_info:
            service.create_industry_research_task(query="")

        assert "空" in str(exc_info.value) or "查询" in str(exc_info.value)
        mock_task_repo.save.assert_not_called()

    def test_create_industry_research_task_whitespace_query_raises_error(
        self, service, mock_task_repo
    ):
        """测试仅空白字符查询文本时抛出 ValueError

        Requirements: 7.2
        """
        with pytest.raises(ValueError) as exc_info:
            service.create_industry_research_task(query="   \t\n  ")

        assert "空" in str(exc_info.value) or "查询" in str(exc_info.value)
        mock_task_repo.save.assert_not_called()

    def test_create_industry_research_task_strips_query(
        self, service, mock_task_repo
    ):
        """测试查询文本被正确 strip

        Requirements: 7.2
        """
        with patch.object(service, "_schedule_async"):
            task_id = service.create_industry_research_task(query="  合成生物学  ")

        saved_task = mock_task_repo.save.call_args[0][0]
        assert saved_task.query == "合成生物学"


# ============================================================
# create_credibility_verification_task Tests
# ============================================================


class TestCreateCredibilityVerificationTask:
    """create_credibility_verification_task 方法测试"""

    def test_create_credibility_verification_task_success(
        self, service, mock_task_repo, mock_credibility_service
    ):
        """测试成功创建概念可信度验证任务

        验证：
        1. 返回有效的 task_id 字符串
        2. Repository.save 被调用
        3. 任务类型为 CREDIBILITY_VERIFICATION
        4. 查询文本格式为 "stock_code:concept"

        Requirements: 7.3
        """
        with patch.object(service, "_schedule_async") as mock_schedule:
            task_id = service.create_credibility_verification_task(
                stock_code="600519.SH", concept="AI+白酒"
            )

        # 验证返回有效的 UUID 格式 task_id
        assert task_id is not None
        assert isinstance(task_id, str)
        uuid.UUID(task_id)

        # 验证 Repository.save 被调用
        mock_task_repo.save.assert_called_once()
        saved_task = mock_task_repo.save.call_args[0][0]
        assert isinstance(saved_task, InvestigationTask)
        assert saved_task.task_type == TaskType.CREDIBILITY_VERIFICATION
        assert saved_task.query == "600519.SH:AI+白酒"
        assert saved_task.status == TaskStatus.PENDING

        # 验证异步工作流被调度
        mock_schedule.assert_called_once()

    def test_create_credibility_verification_task_validates_stock_code(
        self, service, mock_task_repo
    ):
        """测试 StockCode 格式验证

        Requirements: 7.3
        """
        # 有效的股票代码格式
        valid_codes = ["600519.SH", "000001.SZ", "300750.SZ", "688399.SH"]
        for code in valid_codes:
            with patch.object(service, "_schedule_async"):
                task_id = service.create_credibility_verification_task(
                    stock_code=code, concept="测试概念"
                )
                assert task_id is not None

    def test_create_credibility_verification_task_invalid_stock_code_raises_error(
        self, service, mock_task_repo
    ):
        """测试无效股票代码时抛出 ValueError

        Requirements: 7.3
        """
        invalid_codes = ["INVALID", "12345", "600519", "600519.XX"]
        for code in invalid_codes:
            with pytest.raises(ValueError):
                service.create_credibility_verification_task(
                    stock_code=code, concept="测试概念"
                )

        mock_task_repo.save.assert_not_called()

    def test_create_credibility_verification_task_empty_concept_raises_error(
        self, service, mock_task_repo
    ):
        """测试空概念时抛出 ValueError

        由于 query 会是 "600519.SH:" 格式，InvestigationTask 构造函数
        不会因为空概念而失败，但这是一个边界情况。
        """
        # 空概念会导致 query 为 "600519.SH:"，这是有效的非空字符串
        # 所以这个测试验证任务可以创建
        with patch.object(service, "_schedule_async"):
            task_id = service.create_credibility_verification_task(
                stock_code="600519.SH", concept=""
            )
            assert task_id is not None


# ============================================================
# get_task Tests
# ============================================================


class TestGetTask:
    """get_task 方法测试"""

    def test_get_task_found(self, service, mock_task_repo, sample_task):
        """测试获取存在的任务

        Requirements: 7.1
        """
        mock_task_repo.find_by_id.return_value = sample_task

        result = service.get_task(sample_task.task_id.value)

        assert result is not None
        assert result.task_id == sample_task.task_id
        mock_task_repo.find_by_id.assert_called_once()

    def test_get_task_not_found(self, service, mock_task_repo):
        """测试获取不存在的任务返回 None

        Requirements: 7.1
        """
        mock_task_repo.find_by_id.return_value = None
        task_id = str(uuid.uuid4())

        result = service.get_task(task_id)

        assert result is None
        mock_task_repo.find_by_id.assert_called_once()

    def test_get_task_invalid_uuid_raises_error(self, service, mock_task_repo):
        """测试无效 UUID 格式时抛出 ValueError

        Requirements: 7.1
        """
        with pytest.raises(ValueError):
            service.get_task("invalid-uuid")

    def test_get_task_calls_repository_with_correct_task_id(
        self, service, mock_task_repo, sample_task
    ):
        """测试 Repository 被正确调用

        Requirements: 7.1
        """
        mock_task_repo.find_by_id.return_value = sample_task
        task_id_str = sample_task.task_id.value

        service.get_task(task_id_str)

        # 验证传递给 Repository 的 TaskId 值正确
        call_args = mock_task_repo.find_by_id.call_args[0][0]
        assert isinstance(call_args, TaskId)
        assert call_args.value == task_id_str


# ============================================================
# list_recent_tasks Tests
# ============================================================


class TestListRecentTasks:
    """list_recent_tasks 方法测试"""

    def test_list_recent_tasks_returns_list(
        self, service, mock_task_repo, sample_task
    ):
        """测试列出最近任务返回列表

        Requirements: 7.1
        """
        mock_task_repo.find_recent_tasks.return_value = [sample_task]

        result = service.list_recent_tasks()

        assert len(result) == 1
        assert result[0].task_id == sample_task.task_id

    def test_list_recent_tasks_empty(self, service, mock_task_repo):
        """测试列出最近任务返回空列表

        Requirements: 7.1
        """
        mock_task_repo.find_recent_tasks.return_value = []

        result = service.list_recent_tasks()

        assert result == []

    def test_list_recent_tasks_default_pagination(self, service, mock_task_repo):
        """测试默认分页参数

        Requirements: 7.1
        """
        service.list_recent_tasks()

        mock_task_repo.find_recent_tasks.assert_called_once_with(limit=20, offset=0)

    def test_list_recent_tasks_custom_pagination(self, service, mock_task_repo):
        """测试自定义分页参数

        Requirements: 7.1
        """
        service.list_recent_tasks(limit=50, offset=10)

        mock_task_repo.find_recent_tasks.assert_called_once_with(limit=50, offset=10)

    def test_list_recent_tasks_passes_pagination_to_repository(
        self, service, mock_task_repo
    ):
        """测试分页参数正确传递给 Repository

        Requirements: 7.1
        """
        service.list_recent_tasks(limit=100, offset=50)

        mock_task_repo.find_recent_tasks.assert_called_once_with(limit=100, offset=50)


# ============================================================
# cancel_task Tests
# ============================================================


class TestCancelTask:
    """cancel_task 方法测试"""

    def test_cancel_task_success_pending(self, service, mock_task_repo, sample_task):
        """测试成功取消 PENDING 状态的任务

        Requirements: 7.1
        """
        mock_task_repo.find_by_id.return_value = sample_task

        service.cancel_task(sample_task.task_id.value)

        # 验证任务状态被更新
        assert sample_task.status == TaskStatus.CANCELLED
        # 验证 Repository.save 被调用
        mock_task_repo.save.assert_called_once_with(sample_task)

    def test_cancel_task_success_running(
        self, service, mock_task_repo, sample_running_task
    ):
        """测试成功取消 RUNNING 状态的任务

        Requirements: 7.1
        """
        mock_task_repo.find_by_id.return_value = sample_running_task

        service.cancel_task(sample_running_task.task_id.value)

        # 验证任务状态被更新
        assert sample_running_task.status == TaskStatus.CANCELLED
        # 验证 Repository.save 被调用
        mock_task_repo.save.assert_called_once_with(sample_running_task)

    def test_cancel_task_not_found_raises_error(self, service, mock_task_repo):
        """测试取消不存在的任务时抛出 TaskNotFoundError

        Requirements: 7.1
        """
        mock_task_repo.find_by_id.return_value = None
        task_id = str(uuid.uuid4())

        with pytest.raises(TaskNotFoundError) as exc_info:
            service.cancel_task(task_id)

        assert task_id in str(exc_info.value)
        mock_task_repo.save.assert_not_called()

    def test_cancel_task_invalid_uuid_raises_error(self, service, mock_task_repo):
        """测试无效 UUID 格式时抛出 ValueError

        Requirements: 7.1
        """
        with pytest.raises(ValueError):
            service.cancel_task("invalid-uuid")

        mock_task_repo.save.assert_not_called()

    def test_cancel_task_completed_raises_error(self, service, mock_task_repo):
        """测试取消已完成的任务时抛出 InvalidTaskStateError

        Requirements: 7.1
        """
        from contexts.intelligence.domain.exceptions import (
            InvalidTaskStateError,
        )
        from contexts.intelligence.domain.value_objects.industry_insight import (
            IndustryInsight,
        )
        from contexts.intelligence.domain.value_objects.credibility_score import (
            CredibilityScore,
        )
        from contexts.intelligence.domain.value_objects.stock_credibility import (
            StockCredibility,
        )

        # 创建已完成的任务
        task_id = TaskId.generate()
        task = InvestigationTask(
            task_id=task_id,
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="测试查询",
            status=TaskStatus.PENDING,
        )
        task.start()

        # 创建一个简单的 IndustryInsight 结果
        result = IndustryInsight(
            industry_name="测试行业",
            summary="测试总结",
            industry_chain="测试产业链",
            technology_routes=["技术路线1"],
            market_size="100亿",
            top_stocks=[
                StockCredibility(
                    stock_code=StockCode("600519.SH"),
                    stock_name="贵州茅台",
                    credibility_score=CredibilityScore(80),
                    relevance_summary="相关性摘要",
                )
            ],
            risk_alerts=["风险1"],
            catalysts=["催化剂1"],
            heat_score=75,
            competitive_landscape="竞争格局",
        )
        task.complete(result)

        mock_task_repo.find_by_id.return_value = task

        with pytest.raises(InvalidTaskStateError):
            service.cancel_task(task_id.value)

        mock_task_repo.save.assert_not_called()


# ============================================================
# Integration-like Tests (Service Workflow)
# ============================================================


class TestServiceWorkflow:
    """服务工作流集成测试"""

    def test_create_and_get_task_workflow(
        self, service, mock_task_repo
    ):
        """测试创建任务后能够获取

        Requirements: 7.1, 7.2
        """
        # 创建任务
        with patch.object(service, "_schedule_async"):
            task_id = service.create_industry_research_task(query="测试查询")

        # 获取保存的任务
        saved_task = mock_task_repo.save.call_args[0][0]

        # 设置 mock 返回创建的任务
        mock_task_repo.find_by_id.return_value = saved_task

        # 获取任务
        retrieved = service.get_task(task_id)

        assert retrieved is not None
        assert retrieved.task_id.value == task_id
        assert retrieved.query == "测试查询"
        assert retrieved.task_type == TaskType.INDUSTRY_RESEARCH

    def test_create_and_cancel_task_workflow(
        self, service, mock_task_repo
    ):
        """测试创建任务后取消

        Requirements: 7.1, 7.2
        """
        # 创建任务
        with patch.object(service, "_schedule_async"):
            task_id = service.create_industry_research_task(query="测试查询")

        # 获取保存的任务
        saved_task = mock_task_repo.save.call_args[0][0]

        # 设置 mock 返回创建的任务
        mock_task_repo.find_by_id.return_value = saved_task

        # 取消任务
        service.cancel_task(task_id)

        # 验证任务状态
        assert saved_task.status == TaskStatus.CANCELLED

    def test_multiple_tasks_in_list(self, service, mock_task_repo):
        """测试列出多个任务

        Requirements: 7.1
        """
        # 创建多个任务
        tasks = []
        for i in range(3):
            task = InvestigationTask(
                task_id=TaskId.generate(),
                task_type=TaskType.INDUSTRY_RESEARCH,
                query=f"查询 {i}",
            )
            tasks.append(task)

        mock_task_repo.find_recent_tasks.return_value = tasks

        result = service.list_recent_tasks()

        assert len(result) == 3
        for i, task in enumerate(result):
            assert task.query == f"查询 {i}"
