"""
Intelligence Controller 集成测试

使用真实的服务实现（带内存 Repository）测试 API 端点的完整请求/响应流程。
与单元测试不同，这些测试不使用 mock，而是测试完整的集成路径。

Requirements:
- 8.1: POST /api/intelligence/tasks/industry-research
- 8.2: POST /api/intelligence/tasks/credibility-verification
- 8.3: GET /api/intelligence/tasks/<task_id>
- 8.4: GET /api/intelligence/tasks
- 8.5: POST /api/intelligence/tasks/<task_id>/cancel
- 8.9: API 请求包含无效数据时返回 HTTP 400
- 8.10: 请求的任务不存在时返回 HTTP 404
"""
import pytest
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contexts.intelligence.interface.controllers.intelligence_controller import (
    intelligence_bp,
    init_app,
)
from contexts.intelligence.application.services.investigation_task_service import (
    InvestigationTaskService,
    IWebSocketEmitter,
)
from contexts.intelligence.domain.repositories.investigation_task_repository import (
    IInvestigationTaskRepository,
)
from contexts.intelligence.domain.services.industry_research_service import (
    IIndustryResearchService,
)
from contexts.intelligence.domain.services.credibility_verification_service import (
    ICredibilityVerificationService,
)
from contexts.intelligence.domain.models.investigation_task import InvestigationTask
from contexts.intelligence.domain.value_objects.identifiers import TaskId
from contexts.intelligence.domain.value_objects.industry_insight import IndustryInsight
from contexts.intelligence.domain.value_objects.credibility_report import (
    CredibilityReport,
    MainBusinessMatch,
    EvidenceAnalysis,
    HypeHistory,
    SupplyChainLogic,
)
from contexts.intelligence.domain.value_objects.credibility_score import CredibilityScore
from contexts.intelligence.domain.value_objects.stock_credibility import StockCredibility
from contexts.intelligence.domain.enums.enums import TaskStatus, TaskType, RiskLabel

from shared_kernel.value_objects.stock_code import StockCode


# === 内存实现（用于集成测试） ===


class InMemoryTaskRepository(IInvestigationTaskRepository):
    """内存任务 Repository 实现
    
    用于集成测试，不依赖数据库。
    """
    
    def __init__(self):
        self._tasks: Dict[str, InvestigationTask] = {}
    
    def save(self, task: InvestigationTask) -> None:
        self._tasks[task.task_id.value] = task
    
    def find_by_id(self, task_id: TaskId) -> Optional[InvestigationTask]:
        return self._tasks.get(task_id.value)
    
    def find_by_status(
        self, status: TaskStatus, limit: int = 20
    ) -> List[InvestigationTask]:
        result = [t for t in self._tasks.values() if t.status == status]
        return sorted(result, key=lambda t: t.created_at, reverse=True)[:limit]
    
    def find_recent_tasks(
        self, limit: int = 20, offset: int = 0
    ) -> List[InvestigationTask]:
        all_tasks = sorted(
            self._tasks.values(), key=lambda t: t.created_at, reverse=True
        )
        return all_tasks[offset:offset + limit]
    
    def delete(self, task_id: TaskId) -> None:
        self._tasks.pop(task_id.value, None)
    
    def count_by_status(self, status: TaskStatus) -> int:
        return sum(1 for t in self._tasks.values() if t.status == status)
    
    def clear(self) -> None:
        """清空所有任务（测试辅助方法）"""
        self._tasks.clear()


class StubResearchService(IIndustryResearchService):
    """存根行业研究服务
    
    用于集成测试，不执行真实的 AI 工作流。
    """
    
    async def execute_research(self, query: str, progress_callback=None) -> IndustryInsight:
        # 返回一个简单的 IndustryInsight 结果
        return IndustryInsight(
            industry_name="测试行业",
            summary="测试行业总结",
            industry_chain="上游 -> 中游 -> 下游",
            technology_routes=["技术路线1", "技术路线2"],
            market_size="100亿",
            top_stocks=[
                StockCredibility(
                    stock_code=StockCode("600519.SH"),
                    stock_name="测试股票",
                    credibility_score=CredibilityScore(80),
                    relevance_summary="高度相关"
                )
            ],
            risk_alerts=["风险1"],
            catalysts=["催化剂1"],
            heat_score=75,
            competitive_landscape="竞争格局描述"
        )


class StubCredibilityService(ICredibilityVerificationService):
    """存根可信度验证服务
    
    用于集成测试，不执行真实的 AI 工作流。
    """
    
    async def verify_credibility(
        self, stock_code: StockCode, concept: str, progress_callback=None
    ) -> CredibilityReport:
        return CredibilityReport(
            stock_code=stock_code,
            stock_name="测试股票",
            concept=concept,
            overall_score=CredibilityScore(50),
            main_business_match=MainBusinessMatch(
                score=60,
                main_business_description="主营业务描述",
                match_analysis="匹配分析"
            ),
            evidence=EvidenceAnalysis(
                score=50,
                patents=["专利1"],
                orders=["订单1"],
                partnerships=["合作伙伴1"],
                analysis="证据分析"
            ),
            hype_history=HypeHistory(
                score=70,
                past_concepts=["历史概念1"],
                analysis="历史分析"
            ),
            supply_chain_logic=SupplyChainLogic(
                score=55,
                upstream=["上游1"],
                downstream=["下游1"],
                analysis="供应链分析"
            ),
            risk_labels=[RiskLabel.WEAK_EVIDENCE],
            conclusion="测试结论"
        )


class StubWebSocketEmitter(IWebSocketEmitter):
    """存根 WebSocket 推送器
    
    用于集成测试，记录推送的事件但不实际发送。
    """
    
    def __init__(self):
        self.events: List[tuple] = []
    
    def emit(self, event: str, data: dict) -> None:
        self.events.append((event, data))
    
    def clear(self) -> None:
        self.events.clear()


# === Fixtures ===


@pytest.fixture
def task_repo():
    """创建内存任务 Repository"""
    return InMemoryTaskRepository()


@pytest.fixture
def research_service():
    """创建存根行业研究服务"""
    return StubResearchService()


@pytest.fixture
def credibility_service():
    """创建存根可信度验证服务"""
    return StubCredibilityService()


@pytest.fixture
def ws_emitter():
    """创建存根 WebSocket 推送器"""
    return StubWebSocketEmitter()


@pytest.fixture
def task_service(task_repo, research_service, credibility_service, ws_emitter):
    """创建真实的 InvestigationTaskService"""
    return InvestigationTaskService(
        task_repo=task_repo,
        research_service=research_service,
        credibility_service=credibility_service,
        ws_emitter=ws_emitter,
    )


@pytest.fixture
def app(task_service):
    """创建测试 Flask 应用"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(intelligence_bp)
    init_app(task_service)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture(autouse=True)
def cleanup_controller():
    """清理控制器状态"""
    yield
    from contexts.intelligence.interface.controllers import intelligence_controller
    intelligence_controller._task_service = None


# === 集成测试：创建行业认知任务 ===


class TestCreateIndustryResearchIntegration:
    """创建快速行业认知任务集成测试
    
    **Validates: Requirements 8.1, 8.9**
    """
    
    def test_create_and_retrieve_task(self, client, task_repo):
        """测试创建任务后可以通过 API 查询到"""
        request_data = {'query': '快速了解合成生物学赛道'}
        
        # 创建任务
        response = client.post(
            '/api/intelligence/tasks/industry-research',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        task_id = data['task_id']
        
        # 验证任务已持久化到 Repository
        task = task_repo.find_by_id(TaskId.from_string(task_id))
        assert task is not None
        assert task.query == '快速了解合成生物学赛道'
        assert task.task_type == TaskType.INDUSTRY_RESEARCH
        assert task.status == TaskStatus.PENDING
        
        # 通过 API 查询任务
        get_response = client.get(f'/api/intelligence/tasks/{task_id}')
        assert get_response.status_code == 200
        task_data = json.loads(get_response.data)
        assert task_data['task_id'] == task_id
        assert task_data['query'] == '快速了解合成生物学赛道'
        assert task_data['task_type'] == 'industry_research'
    
    def test_invalid_request_returns_400(self, client):
        """测试无效请求返回 400
        
        **Validates: Requirements 8.9**
        """
        # 空 query
        response = client.post(
            '/api/intelligence/tasks/industry-research',
            data=json.dumps({'query': ''}),
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # 缺少 query 字段
        response = client.post(
            '/api/intelligence/tasks/industry-research',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # 无效 JSON
        response = client.post(
            '/api/intelligence/tasks/industry-research',
            data='not json',
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # 空请求体
        response = client.post(
            '/api/intelligence/tasks/industry-research',
            data='',
            content_type='application/json'
        )
        assert response.status_code == 400


# === 集成测试：创建可信度验证任务 ===


class TestCreateCredibilityVerificationIntegration:
    """创建概念可信度验证任务集成测试
    
    **Validates: Requirements 8.2, 8.9**
    """
    
    def test_create_and_retrieve_task(self, client, task_repo):
        """测试创建可信度验证任务后可以通过 API 查询到"""
        request_data = {'stock_code': '600519.SH', 'concept': 'AI+白酒'}
        
        # 创建任务
        response = client.post(
            '/api/intelligence/tasks/credibility-verification',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        task_id = data['task_id']
        
        # 验证任务已持久化
        task = task_repo.find_by_id(TaskId.from_string(task_id))
        assert task is not None
        assert task.task_type == TaskType.CREDIBILITY_VERIFICATION
        assert '600519.SH' in task.query
        assert 'AI+白酒' in task.query
        
        # 通过 API 查询任务
        get_response = client.get(f'/api/intelligence/tasks/{task_id}')
        assert get_response.status_code == 200
        task_data = json.loads(get_response.data)
        assert task_data['task_type'] == 'credibility_verification'
    
    def test_invalid_stock_code_returns_400(self, client):
        """测试无效股票代码返回 400
        
        **Validates: Requirements 8.9**
        """
        # 无效格式的股票代码
        response = client.post(
            '/api/intelligence/tasks/credibility-verification',
            data=json.dumps({'stock_code': 'INVALID', 'concept': 'AI'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert '无效的股票代码格式' in data['error']
    
    def test_missing_fields_returns_400(self, client):
        """测试缺少必填字段返回 400
        
        **Validates: Requirements 8.9**
        """
        # 缺少 stock_code
        response = client.post(
            '/api/intelligence/tasks/credibility-verification',
            data=json.dumps({'concept': 'AI'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # 缺少 concept
        response = client.post(
            '/api/intelligence/tasks/credibility-verification',
            data=json.dumps({'stock_code': '600519.SH'}),
            content_type='application/json'
        )
        assert response.status_code == 400


# === 集成测试：查询任务 ===


class TestGetTaskIntegration:
    """查询任务详情集成测试
    
    **Validates: Requirements 8.3, 8.9, 8.10**
    """
    
    def test_get_existing_task(self, client, task_repo):
        """测试查询存在的任务"""
        # 先创建一个任务
        task = InvestigationTask(
            task_id=TaskId.generate(),
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="测试查询"
        )
        task_repo.save(task)
        
        # 查询任务
        response = client.get(f'/api/intelligence/tasks/{task.task_id.value}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['task_id'] == task.task_id.value
        assert data['query'] == '测试查询'
        assert data['status'] == 'pending'
    
    def test_get_nonexistent_task_returns_404(self, client):
        """测试查询不存在的任务返回 404
        
        **Validates: Requirements 8.10**
        """
        non_existent_id = str(uuid.uuid4())
        
        response = client.get(f'/api/intelligence/tasks/{non_existent_id}')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert '不存在' in data['error']
    
    def test_get_task_invalid_uuid_returns_400(self, client):
        """测试无效 UUID 格式返回 400
        
        **Validates: Requirements 8.9**
        """
        response = client.get('/api/intelligence/tasks/not-a-valid-uuid')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


# === 集成测试：列出任务 ===


class TestListTasksIntegration:
    """分页列出任务集成测试
    
    **Validates: Requirements 8.4, 8.9**
    """
    
    def test_list_empty_tasks(self, client):
        """测试空任务列表"""
        response = client.get('/api/intelligence/tasks')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []
    
    def test_list_multiple_tasks(self, client, task_repo):
        """测试列出多个任务"""
        # 创建多个任务
        for i in range(3):
            task = InvestigationTask(
                task_id=TaskId.generate(),
                task_type=TaskType.INDUSTRY_RESEARCH,
                query=f"查询{i}"
            )
            task_repo.save(task)
        
        response = client.get('/api/intelligence/tasks')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 3
    
    def test_list_tasks_with_pagination(self, client, task_repo):
        """测试分页参数"""
        # 创建 5 个任务
        for i in range(5):
            task = InvestigationTask(
                task_id=TaskId.generate(),
                task_type=TaskType.INDUSTRY_RESEARCH,
                query=f"查询{i}"
            )
            task_repo.save(task)
        
        # 测试 limit
        response = client.get('/api/intelligence/tasks?limit=2')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        
        # 测试 offset
        response = client.get('/api/intelligence/tasks?limit=2&offset=2')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
    
    def test_list_tasks_invalid_params_returns_400(self, client):
        """测试无效分页参数返回 400
        
        **Validates: Requirements 8.9**
        """
        # limit < 1
        response = client.get('/api/intelligence/tasks?limit=0')
        assert response.status_code == 400
        
        # 负数 offset
        response = client.get('/api/intelligence/tasks?offset=-1')
        assert response.status_code == 400


# === 集成测试：取消任务 ===


class TestCancelTaskIntegration:
    """取消任务集成测试
    
    **Validates: Requirements 8.5, 8.9, 8.10**
    """
    
    def test_cancel_pending_task(self, client, task_repo):
        """测试取消 PENDING 状态的任务"""
        # 创建一个 PENDING 任务
        task = InvestigationTask(
            task_id=TaskId.generate(),
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="待取消的任务"
        )
        task_repo.save(task)
        
        # 取消任务
        response = client.post(f'/api/intelligence/tasks/{task.task_id.value}/cancel')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == '任务已取消'
        
        # 验证任务状态已更新
        updated_task = task_repo.find_by_id(task.task_id)
        assert updated_task.status == TaskStatus.CANCELLED
    
    def test_cancel_running_task(self, client, task_repo):
        """测试取消 RUNNING 状态的任务"""
        # 创建一个 RUNNING 任务
        task = InvestigationTask(
            task_id=TaskId.generate(),
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="运行中的任务"
        )
        task.start()  # PENDING -> RUNNING
        task_repo.save(task)
        
        # 取消任务
        response = client.post(f'/api/intelligence/tasks/{task.task_id.value}/cancel')
        
        assert response.status_code == 200
        
        # 验证任务状态已更新
        updated_task = task_repo.find_by_id(task.task_id)
        assert updated_task.status == TaskStatus.CANCELLED
    
    def test_cancel_nonexistent_task_returns_404(self, client):
        """测试取消不存在的任务返回 404
        
        **Validates: Requirements 8.10**
        """
        non_existent_id = str(uuid.uuid4())
        
        response = client.post(f'/api/intelligence/tasks/{non_existent_id}/cancel')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_cancel_completed_task_returns_409(self, client, task_repo, research_service):
        """测试取消已完成的任务返回 409（状态冲突）"""
        # 创建一个 COMPLETED 任务
        task = InvestigationTask(
            task_id=TaskId.generate(),
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="已完成的任务"
        )
        task.start()  # PENDING -> RUNNING
        
        # 创建一个简单的 IndustryInsight 结果
        result = IndustryInsight(
            industry_name="测试行业",
            summary="总结",
            industry_chain="产业链",
            technology_routes=["路线1"],
            market_size="100亿",
            top_stocks=[],
            risk_alerts=[],
            catalysts=[],
            heat_score=50,
            competitive_landscape="竞争格局"
        )
        task.complete(result)  # RUNNING -> COMPLETED
        task_repo.save(task)
        
        # 尝试取消已完成的任务
        response = client.post(f'/api/intelligence/tasks/{task.task_id.value}/cancel')
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_cancel_failed_task_returns_409(self, client, task_repo):
        """测试取消已失败的任务返回 409（状态冲突）"""
        # 创建一个 FAILED 任务
        task = InvestigationTask(
            task_id=TaskId.generate(),
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="已失败的任务"
        )
        task.start()  # PENDING -> RUNNING
        task.fail("测试错误")  # RUNNING -> FAILED
        task_repo.save(task)
        
        # 尝试取消已失败的任务
        response = client.post(f'/api/intelligence/tasks/{task.task_id.value}/cancel')
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_cancel_task_invalid_uuid_returns_400(self, client):
        """测试无效 UUID 格式返回 400
        
        **Validates: Requirements 8.9**
        """
        response = client.post('/api/intelligence/tasks/invalid-uuid/cancel')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


# === 集成测试：完整工作流 ===


class TestFullWorkflowIntegration:
    """完整工作流集成测试
    
    测试从创建任务到查询结果的完整流程。
    """
    
    def test_create_list_get_cancel_workflow(self, client, task_repo):
        """测试创建 -> 列表 -> 查询 -> 取消的完整流程"""
        # 1. 创建任务
        create_response = client.post(
            '/api/intelligence/tasks/industry-research',
            data=json.dumps({'query': '测试完整流程'}),
            content_type='application/json'
        )
        assert create_response.status_code == 201
        task_id = json.loads(create_response.data)['task_id']
        
        # 2. 列表中应该包含该任务
        list_response = client.get('/api/intelligence/tasks')
        assert list_response.status_code == 200
        tasks = json.loads(list_response.data)
        assert len(tasks) == 1
        assert tasks[0]['task_id'] == task_id
        
        # 3. 查询任务详情
        get_response = client.get(f'/api/intelligence/tasks/{task_id}')
        assert get_response.status_code == 200
        task_data = json.loads(get_response.data)
        assert task_data['status'] == 'pending'
        
        # 4. 取消任务
        cancel_response = client.post(f'/api/intelligence/tasks/{task_id}/cancel')
        assert cancel_response.status_code == 200
        
        # 5. 验证任务状态已更新
        get_response = client.get(f'/api/intelligence/tasks/{task_id}')
        assert get_response.status_code == 200
        task_data = json.loads(get_response.data)
        assert task_data['status'] == 'cancelled'
    
    def test_multiple_task_types(self, client, task_repo):
        """测试创建不同类型的任务"""
        # 创建行业认知任务
        response1 = client.post(
            '/api/intelligence/tasks/industry-research',
            data=json.dumps({'query': '行业认知查询'}),
            content_type='application/json'
        )
        assert response1.status_code == 201
        
        # 创建可信度验证任务
        response2 = client.post(
            '/api/intelligence/tasks/credibility-verification',
            data=json.dumps({'stock_code': '000001.SZ', 'concept': 'AI概念'}),
            content_type='application/json'
        )
        assert response2.status_code == 201
        
        # 列表应该包含两个任务
        list_response = client.get('/api/intelligence/tasks')
        assert list_response.status_code == 200
        tasks = json.loads(list_response.data)
        assert len(tasks) == 2
        
        # 验证任务类型
        task_types = {t['task_type'] for t in tasks}
        assert 'industry_research' in task_types
        assert 'credibility_verification' in task_types
