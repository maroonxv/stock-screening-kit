"""
任务响应 DTO 单元测试

测试 TaskResponseDTO 的领域对象转换和响应格式化功能。

Requirements:
- 8.8: 实现 DTO 类用于请求验证和响应格式化
"""
import pytest
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contexts.intelligence.interface.dto.task_response_dto import TaskResponseDTO
from contexts.intelligence.domain.models.investigation_task import InvestigationTask
from contexts.intelligence.domain.value_objects.identifiers import TaskId
from contexts.intelligence.domain.value_objects.agent_step import AgentStep
from contexts.intelligence.domain.value_objects.credibility_score import CredibilityScore
from contexts.intelligence.domain.value_objects.stock_credibility import StockCredibility
from contexts.intelligence.domain.value_objects.industry_insight import IndustryInsight
from contexts.intelligence.domain.value_objects.credibility_report import (
    CredibilityReport,
    MainBusinessMatch,
    EvidenceAnalysis,
    HypeHistory,
    SupplyChainLogic,
)
from contexts.intelligence.domain.enums.enums import (
    TaskType,
    TaskStatus,
    AgentStepStatus,
    RiskLabel,
)
from shared_kernel.value_objects.stock_code import StockCode


class TestTaskResponseDTOFromDomain:
    """TaskResponseDTO.from_domain 测试"""
    
    def test_from_domain_pending_task(self):
        """测试 PENDING 状态任务的转换"""
        task_id = TaskId.generate()
        created_at = datetime(2024, 1, 15, 10, 0, 0)
        updated_at = datetime(2024, 1, 15, 10, 0, 0)
        
        task = InvestigationTask(
            task_id=task_id,
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="快速了解合成生物学赛道",
            status=TaskStatus.PENDING,
            progress=0,
            agent_steps=[],
            result=None,
            error_message=None,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=None,
        )
        
        dto = TaskResponseDTO.from_domain(task)
        
        assert dto.task_id == task_id.value
        assert dto.task_type == "industry_research"
        assert dto.query == "快速了解合成生物学赛道"
        assert dto.status == "pending"
        assert dto.progress == 0
        assert dto.agent_steps == []
        assert dto.result is None
        assert dto.error_message is None
        assert dto.created_at == "2024-01-15T10:00:00"
        assert dto.updated_at == "2024-01-15T10:00:00"
        assert dto.completed_at is None
        assert dto.duration is None
    
    def test_from_domain_running_task_with_agent_steps(self):
        """测试 RUNNING 状态任务（带 Agent 步骤）的转换"""
        task_id = TaskId.generate()
        created_at = datetime(2024, 1, 15, 10, 0, 0)
        updated_at = datetime(2024, 1, 15, 10, 5, 0)
        
        agent_step = AgentStep(
            agent_name="行业背景速览",
            status=AgentStepStatus.COMPLETED,
            started_at=datetime(2024, 1, 15, 10, 1, 0),
            completed_at=datetime(2024, 1, 15, 10, 3, 0),
            output_summary="合成生物学行业总结已生成",
            error_message=None,
        )
        
        task = InvestigationTask(
            task_id=task_id,
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="快速了解合成生物学赛道",
            status=TaskStatus.RUNNING,
            progress=40,
            agent_steps=[agent_step],
            result=None,
            error_message=None,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=None,
        )
        
        dto = TaskResponseDTO.from_domain(task)
        
        assert dto.status == "running"
        assert dto.progress == 40
        assert len(dto.agent_steps) == 1
        assert dto.agent_steps[0]["agent_name"] == "行业背景速览"
        assert dto.agent_steps[0]["status"] == "completed"
        assert dto.agent_steps[0]["output_summary"] == "合成生物学行业总结已生成"
        assert dto.result is None
        assert dto.duration is None
    
    def test_from_domain_completed_task_with_industry_insight(self):
        """测试 COMPLETED 状态任务（带 IndustryInsight 结果）的转换"""
        task_id = TaskId.generate()
        created_at = datetime(2024, 1, 15, 10, 0, 0)
        updated_at = datetime(2024, 1, 15, 10, 30, 0)
        completed_at = datetime(2024, 1, 15, 10, 30, 0)
        
        # 创建 IndustryInsight 结果
        stock_credibility = StockCredibility(
            stock_code=StockCode("688399.SH"),
            stock_name="硕世生物",
            credibility_score=CredibilityScore(85),
            relevance_summary="主营业务与合成生物学高度相关",
        )
        
        industry_insight = IndustryInsight(
            industry_name="合成生物学",
            summary="合成生物学是一个新兴领域...",
            industry_chain="上游：基因合成 → 中游：菌株构建 → 下游：产品应用",
            technology_routes=["基因编辑", "代谢工程", "蛋白质设计"],
            market_size="全球市场规模约 500 亿美元",
            top_stocks=[stock_credibility],
            risk_alerts=["行业处于早期阶段", "商业化路径不确定"],
            catalysts=["政策支持", "技术突破"],
            heat_score=75,
            competitive_landscape="行业集中度低，竞争格局分散",
        )
        
        task = InvestigationTask(
            task_id=task_id,
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="快速了解合成生物学赛道",
            status=TaskStatus.COMPLETED,
            progress=100,
            agent_steps=[],
            result=industry_insight,
            error_message=None,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
        )
        
        dto = TaskResponseDTO.from_domain(task)
        
        assert dto.status == "completed"
        assert dto.progress == 100
        assert dto.result is not None
        assert dto.result["industry_name"] == "合成生物学"
        assert dto.result["heat_score"] == 75
        assert len(dto.result["top_stocks"]) == 1
        assert dto.result["top_stocks"][0]["stock_code"] == "688399.SH"
        assert dto.result["top_stocks"][0]["credibility_score"]["score"] == 85
        assert dto.completed_at == "2024-01-15T10:30:00"
        assert dto.duration == 1800.0  # 30 minutes in seconds
    
    def test_from_domain_completed_task_with_credibility_report(self):
        """测试 COMPLETED 状态任务（带 CredibilityReport 结果）的转换"""
        task_id = TaskId.generate()
        created_at = datetime(2024, 1, 15, 10, 0, 0)
        updated_at = datetime(2024, 1, 15, 10, 10, 0)
        completed_at = datetime(2024, 1, 15, 10, 10, 0)
        
        # 创建 CredibilityReport 结果
        credibility_report = CredibilityReport(
            stock_code=StockCode("600519.SH"),
            stock_name="贵州茅台",
            concept="AI+白酒",
            overall_score=CredibilityScore(15),
            main_business_match=MainBusinessMatch(
                score=5,
                main_business_description="白酒生产与销售",
                match_analysis="主营业务与 AI 无关联",
            ),
            evidence=EvidenceAnalysis(
                score=10,
                patents=[],
                orders=[],
                partnerships=[],
                analysis="未发现 AI 相关专利或订单",
            ),
            hype_history=HypeHistory(
                score=30,
                past_concepts=["元宇宙", "区块链"],
                analysis="历史上曾蹭过多个热点概念",
            ),
            supply_chain_logic=SupplyChainLogic(
                score=5,
                upstream=["高粱", "小麦"],
                downstream=["经销商", "零售"],
                analysis="供应链与 AI 无逻辑关联",
            ),
            risk_labels=[RiskLabel.PURE_HYPE, RiskLabel.BUSINESS_MISMATCH],
            conclusion="该公司声称的 AI+白酒 概念可信度极低，属于纯蹭热点",
        )
        
        task = InvestigationTask(
            task_id=task_id,
            task_type=TaskType.CREDIBILITY_VERIFICATION,
            query="600519.SH:AI+白酒",
            status=TaskStatus.COMPLETED,
            progress=100,
            agent_steps=[],
            result=credibility_report,
            error_message=None,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
        )
        
        dto = TaskResponseDTO.from_domain(task)
        
        assert dto.task_type == "credibility_verification"
        assert dto.status == "completed"
        assert dto.result is not None
        assert dto.result["stock_code"] == "600519.SH"
        assert dto.result["stock_name"] == "贵州茅台"
        assert dto.result["concept"] == "AI+白酒"
        assert dto.result["overall_score"]["score"] == 15
        assert dto.result["main_business_match"]["score"] == 5
        assert dto.result["risk_labels"] == ["pure_hype", "business_mismatch"]
        assert dto.duration == 600.0  # 10 minutes in seconds
    
    def test_from_domain_failed_task(self):
        """测试 FAILED 状态任务的转换"""
        task_id = TaskId.generate()
        created_at = datetime(2024, 1, 15, 10, 0, 0)
        updated_at = datetime(2024, 1, 15, 10, 5, 0)
        completed_at = datetime(2024, 1, 15, 10, 5, 0)
        
        task = InvestigationTask(
            task_id=task_id,
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="快速了解合成生物学赛道",
            status=TaskStatus.FAILED,
            progress=40,
            agent_steps=[],
            result=None,
            error_message="LLM 服务调用超时",
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
        )
        
        dto = TaskResponseDTO.from_domain(task)
        
        assert dto.status == "failed"
        assert dto.progress == 40
        assert dto.result is None
        assert dto.error_message == "LLM 服务调用超时"
        assert dto.completed_at == "2024-01-15T10:05:00"
        assert dto.duration == 300.0  # 5 minutes in seconds
    
    def test_from_domain_cancelled_task(self):
        """测试 CANCELLED 状态任务的转换"""
        task_id = TaskId.generate()
        created_at = datetime(2024, 1, 15, 10, 0, 0)
        updated_at = datetime(2024, 1, 15, 10, 2, 0)
        completed_at = datetime(2024, 1, 15, 10, 2, 0)
        
        task = InvestigationTask(
            task_id=task_id,
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="快速了解合成生物学赛道",
            status=TaskStatus.CANCELLED,
            progress=20,
            agent_steps=[],
            result=None,
            error_message=None,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
        )
        
        dto = TaskResponseDTO.from_domain(task)
        
        assert dto.status == "cancelled"
        assert dto.progress == 20
        assert dto.result is None
        assert dto.error_message is None
        assert dto.completed_at == "2024-01-15T10:02:00"
        assert dto.duration == 120.0  # 2 minutes in seconds


class TestTaskResponseDTOToDict:
    """TaskResponseDTO.to_dict 测试"""
    
    def test_to_dict_returns_all_fields(self):
        """测试 to_dict 返回所有字段"""
        dto = TaskResponseDTO(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            task_type="industry_research",
            query="快速了解合成生物学赛道",
            status="pending",
            progress=0,
            agent_steps=[],
            result=None,
            error_message=None,
            created_at="2024-01-15T10:00:00",
            updated_at="2024-01-15T10:00:00",
            completed_at=None,
            duration=None,
        )
        
        result = dto.to_dict()
        
        assert result == {
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "task_type": "industry_research",
            "query": "快速了解合成生物学赛道",
            "status": "pending",
            "progress": 0,
            "agent_steps": [],
            "result": None,
            "error_message": None,
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-01-15T10:00:00",
            "completed_at": None,
            "duration": None,
        }
    
    def test_to_dict_with_agent_steps(self):
        """测试 to_dict 包含 agent_steps"""
        agent_steps = [
            {
                "agent_name": "行业背景速览",
                "status": "completed",
                "started_at": "2024-01-15T10:01:00",
                "completed_at": "2024-01-15T10:03:00",
                "output_summary": "行业总结已生成",
                "error_message": None,
            }
        ]
        
        dto = TaskResponseDTO(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            task_type="industry_research",
            query="快速了解合成生物学赛道",
            status="running",
            progress=40,
            agent_steps=agent_steps,
            result=None,
            error_message=None,
            created_at="2024-01-15T10:00:00",
            updated_at="2024-01-15T10:05:00",
            completed_at=None,
            duration=None,
        )
        
        result = dto.to_dict()
        
        assert result["agent_steps"] == agent_steps
    
    def test_to_dict_with_result(self):
        """测试 to_dict 包含 result"""
        result_data = {
            "industry_name": "合成生物学",
            "summary": "合成生物学是...",
            "heat_score": 75,
        }
        
        dto = TaskResponseDTO(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            task_type="industry_research",
            query="快速了解合成生物学赛道",
            status="completed",
            progress=100,
            agent_steps=[],
            result=result_data,
            error_message=None,
            created_at="2024-01-15T10:00:00",
            updated_at="2024-01-15T10:30:00",
            completed_at="2024-01-15T10:30:00",
            duration=1800.0,
        )
        
        result = dto.to_dict()
        
        assert result["result"] == result_data
        assert result["completed_at"] == "2024-01-15T10:30:00"
        assert result["duration"] == 1800.0


class TestTaskResponseDTOProperties:
    """TaskResponseDTO 属性访问器测试"""
    
    def test_all_properties_accessible(self):
        """测试所有属性都可访问"""
        dto = TaskResponseDTO(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            task_type="industry_research",
            query="快速了解合成生物学赛道",
            status="completed",
            progress=100,
            agent_steps=[{"agent_name": "test"}],
            result={"industry_name": "test"},
            error_message="test error",
            created_at="2024-01-15T10:00:00",
            updated_at="2024-01-15T10:30:00",
            completed_at="2024-01-15T10:30:00",
            duration=1800.0,
        )
        
        assert dto.task_id == "550e8400-e29b-41d4-a716-446655440000"
        assert dto.task_type == "industry_research"
        assert dto.query == "快速了解合成生物学赛道"
        assert dto.status == "completed"
        assert dto.progress == 100
        assert dto.agent_steps == [{"agent_name": "test"}]
        assert dto.result == {"industry_name": "test"}
        assert dto.error_message == "test error"
        assert dto.created_at == "2024-01-15T10:00:00"
        assert dto.updated_at == "2024-01-15T10:30:00"
        assert dto.completed_at == "2024-01-15T10:30:00"
        assert dto.duration == 1800.0


class TestTaskResponseDTORepr:
    """TaskResponseDTO __repr__ 测试"""
    
    def test_repr_format(self):
        """测试 __repr__ 格式"""
        dto = TaskResponseDTO(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            task_type="industry_research",
            query="快速了解合成生物学赛道",
            status="running",
            progress=40,
            agent_steps=[],
            result=None,
            error_message=None,
            created_at="2024-01-15T10:00:00",
            updated_at="2024-01-15T10:05:00",
            completed_at=None,
            duration=None,
        )
        
        repr_str = repr(dto)
        
        assert "TaskResponseDTO" in repr_str
        assert "550e8400-e29b-41d4-a716-446655440000" in repr_str
        assert "industry_research" in repr_str
        assert "running" in repr_str
        assert "40" in repr_str


class TestTaskResponseDTOIntegration:
    """TaskResponseDTO 集成测试"""
    
    def test_from_domain_to_dict_roundtrip(self):
        """测试 from_domain -> to_dict 完整流程"""
        task_id = TaskId.generate()
        created_at = datetime(2024, 1, 15, 10, 0, 0)
        updated_at = datetime(2024, 1, 15, 10, 30, 0)
        completed_at = datetime(2024, 1, 15, 10, 30, 0)
        
        # 创建带完整数据的任务
        agent_step = AgentStep(
            agent_name="行业背景速览",
            status=AgentStepStatus.COMPLETED,
            started_at=datetime(2024, 1, 15, 10, 1, 0),
            completed_at=datetime(2024, 1, 15, 10, 3, 0),
            output_summary="行业总结已生成",
            error_message=None,
        )
        
        stock_credibility = StockCredibility(
            stock_code=StockCode("688399.SH"),
            stock_name="硕世生物",
            credibility_score=CredibilityScore(85),
            relevance_summary="主营业务与合成生物学高度相关",
        )
        
        industry_insight = IndustryInsight(
            industry_name="合成生物学",
            summary="合成生物学是一个新兴领域...",
            industry_chain="上游：基因合成 → 中游：菌株构建 → 下游：产品应用",
            technology_routes=["基因编辑", "代谢工程"],
            market_size="全球市场规模约 500 亿美元",
            top_stocks=[stock_credibility],
            risk_alerts=["行业处于早期阶段"],
            catalysts=["政策支持"],
            heat_score=75,
            competitive_landscape="行业集中度低",
        )
        
        task = InvestigationTask(
            task_id=task_id,
            task_type=TaskType.INDUSTRY_RESEARCH,
            query="快速了解合成生物学赛道",
            status=TaskStatus.COMPLETED,
            progress=100,
            agent_steps=[agent_step],
            result=industry_insight,
            error_message=None,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
        )
        
        # 转换为 DTO 并获取字典
        dto = TaskResponseDTO.from_domain(task)
        result = dto.to_dict()
        
        # 验证所有字段
        assert result["task_id"] == task_id.value
        assert result["task_type"] == "industry_research"
        assert result["query"] == "快速了解合成生物学赛道"
        assert result["status"] == "completed"
        assert result["progress"] == 100
        assert len(result["agent_steps"]) == 1
        assert result["agent_steps"][0]["agent_name"] == "行业背景速览"
        assert result["result"]["industry_name"] == "合成生物学"
        assert result["result"]["heat_score"] == 75
        assert len(result["result"]["top_stocks"]) == 1
        assert result["error_message"] is None
        assert result["created_at"] == "2024-01-15T10:00:00"
        assert result["updated_at"] == "2024-01-15T10:30:00"
        assert result["completed_at"] == "2024-01-15T10:30:00"
        assert result["duration"] == 1800.0
