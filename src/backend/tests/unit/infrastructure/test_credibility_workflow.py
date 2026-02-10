"""概念可信度验证 LangGraph 工作流单元测试

测试 CredibilityVerificationState、Agent 节点函数、工作流构建、
风险标签推断和 CredibilityVerificationWorkflowService。

Requirements: 6.3, 6.7
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.backend.contexts.intelligence.domain.enums.enums import (
    AgentStepStatus,
    RiskLabel,
)
from src.backend.contexts.intelligence.domain.exceptions import LLMServiceError
from src.backend.contexts.intelligence.domain.value_objects.agent_step import AgentStep
from src.backend.contexts.intelligence.domain.value_objects.credibility_report import (
    CredibilityReport,
)
from src.backend.contexts.intelligence.infrastructure.ai.deepseek_client import (
    ChatCompletion,
    DeepSeekClient,
    DeepSeekConfig,
)
from src.backend.contexts.intelligence.infrastructure.ai.credibility_workflow import (
    CREDIBILITY_AGENT_NAMES,
    CREDIBILITY_AGENT_PROGRESS,
    CredibilityVerificationState,
    CredibilityVerificationWorkflowService,
    _infer_risk_labels,
    build_credibility_verification_workflow,
)
from shared_kernel.value_objects.stock_code import StockCode


# ============================================================
# Helper: Create a mock DeepSeek client
# ============================================================


def _make_mock_deepseek_client(responses: list[str] | None = None):
    """Create a mock DeepSeekClient that returns predefined responses.

    Args:
        responses: List of JSON string responses for sequential calls.
                   If None, uses default responses for all 4 agents.
    """
    if responses is None:
        responses = [
            # Agent 1: main_business_match
            json.dumps({
                "score": 85,
                "main_business_description": "该公司主营固态电池研发与生产",
                "match_analysis": "主营业务与固态电池概念高度匹配",
            }),
            # Agent 2: evidence_collection
            json.dumps({
                "score": 70,
                "patents": ["固态电池专利CN202310001", "电解质专利CN202310002"],
                "orders": ["与宁德时代签订供货协议"],
                "partnerships": ["与中科院合作研发"],
                "analysis": "有一定的实质证据支撑",
            }),
            # Agent 3: hype_history_detection
            json.dumps({
                "score": 80,
                "past_concepts": ["锂电池"],
                "analysis": "历史上仅涉及锂电池概念，蹭热点记录较少",
            }),
            # Agent 4: supply_chain_logic
            json.dumps({
                "score": 75,
                "upstream": ["电解质材料", "正极材料"],
                "downstream": ["新能源汽车", "储能系统"],
                "analysis": "供应链逻辑合理，上下游关系清晰",
            }),
        ]

    config = DeepSeekConfig(
        api_key="test-key",
        base_url="https://api.test.com/v1",
        timeout=10.0,
        max_retries=0,
    )
    client = DeepSeekClient(config)

    call_count = 0

    async def mock_chat(messages, **kwargs):
        nonlocal call_count
        idx = min(call_count, len(responses) - 1)
        call_count += 1
        return ChatCompletion(
            content=responses[idx],
            model="deepseek-chat",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
        )

    client.chat = mock_chat
    return client


# ============================================================
# CREDIBILITY_AGENT_NAMES and CREDIBILITY_AGENT_PROGRESS Tests
# ============================================================


class TestCredibilityAgentConstants:
    """Agent 常量测试"""

    def test_agent_names_has_all_four_agents(self):
        """测试 CREDIBILITY_AGENT_NAMES 包含所有 4 个 Agent"""
        expected_keys = {
            "main_business_match",
            "evidence_collection",
            "hype_history_detection",
            "supply_chain_logic",
        }
        assert set(CREDIBILITY_AGENT_NAMES.keys()) == expected_keys

    def test_agent_names_are_chinese(self):
        """测试 Agent 显示名称为中文"""
        assert CREDIBILITY_AGENT_NAMES["main_business_match"] == "主营业务匹配分析"
        assert CREDIBILITY_AGENT_NAMES["evidence_collection"] == "实质证据收集"
        assert CREDIBILITY_AGENT_NAMES["hype_history_detection"] == "历史蹭热点检测"
        assert CREDIBILITY_AGENT_NAMES["supply_chain_logic"] == "供应链逻辑分析"

    def test_agent_progress_values_are_increasing(self):
        """测试 Agent 进度值递增"""
        ordered_agents = [
            "main_business_match",
            "evidence_collection",
            "hype_history_detection",
            "supply_chain_logic",
        ]
        progress_values = [CREDIBILITY_AGENT_PROGRESS[a] for a in ordered_agents]
        assert progress_values == sorted(progress_values)
        assert all(0 < p <= 100 for p in progress_values)


# ============================================================
# _infer_risk_labels Tests
# ============================================================


class TestInferRiskLabels:
    """风险标签推断测试"""

    def test_no_risk_labels_for_high_scores(self):
        """测试高评分时无风险标签"""
        labels = _infer_risk_labels(
            main_business_score=85,
            evidence_score=80,
            hype_score=90,
            supply_chain_score=85,
            hype_past_concepts=["锂电池"],
        )
        assert labels == []

    def test_business_mismatch_label(self):
        """测试主营业务不匹配标签"""
        labels = _infer_risk_labels(
            main_business_score=20,
            evidence_score=80,
            hype_score=90,
            supply_chain_score=85,
            hype_past_concepts=[],
        )
        assert RiskLabel.BUSINESS_MISMATCH in labels

    def test_weak_evidence_label(self):
        """测试证据不足标签"""
        labels = _infer_risk_labels(
            main_business_score=80,
            evidence_score=20,
            hype_score=90,
            supply_chain_score=85,
            hype_past_concepts=[],
        )
        assert RiskLabel.WEAK_EVIDENCE in labels

    def test_pure_hype_label(self):
        """测试纯蹭热点标签（主业不匹配 + 证据不足 + 蹭热点历史差）"""
        labels = _infer_risk_labels(
            main_business_score=10,
            evidence_score=10,
            hype_score=20,
            supply_chain_score=10,
            hype_past_concepts=["元宇宙", "区块链", "AI"],
        )
        assert RiskLabel.PURE_HYPE in labels
        assert RiskLabel.BUSINESS_MISMATCH in labels
        assert RiskLabel.WEAK_EVIDENCE in labels

    def test_frequent_concept_change_label_by_count(self):
        """测试频繁概念切换标签（历史概念数 >= 3）"""
        labels = _infer_risk_labels(
            main_business_score=80,
            evidence_score=80,
            hype_score=60,
            supply_chain_score=80,
            hype_past_concepts=["元宇宙", "区块链", "AI"],
        )
        assert RiskLabel.FREQUENT_CONCEPT_CHANGE in labels

    def test_frequent_concept_change_label_by_low_score(self):
        """测试频繁概念切换标签（蹭热点评分 < 30）"""
        labels = _infer_risk_labels(
            main_business_score=80,
            evidence_score=80,
            hype_score=20,
            supply_chain_score=80,
            hype_past_concepts=[],
        )
        assert RiskLabel.FREQUENT_CONCEPT_CHANGE in labels

    def test_supply_chain_risk_label(self):
        """测试供应链风险标签"""
        labels = _infer_risk_labels(
            main_business_score=80,
            evidence_score=80,
            hype_score=90,
            supply_chain_score=20,
            hype_past_concepts=[],
        )
        assert RiskLabel.SUPPLY_CHAIN_RISK in labels


# ============================================================
# build_credibility_verification_workflow Tests
# ============================================================


class TestBuildCredibilityWorkflow:
    """工作流构建测试"""

    def test_build_workflow_returns_compiled_graph(self):
        """测试构建工作流返回编译后的图"""
        client = _make_mock_deepseek_client()
        graph = build_credibility_verification_workflow(client)
        assert graph is not None

    def test_build_workflow_with_checkpointer(self):
        """测试使用 checkpointer 构建工作流"""
        from langgraph.checkpoint.memory import MemorySaver

        client = _make_mock_deepseek_client()
        checkpointer = MemorySaver()
        graph = build_credibility_verification_workflow(client, checkpointer=checkpointer)
        assert graph is not None

    def test_build_workflow_without_checkpointer(self):
        """测试不使用 checkpointer 构建工作流"""
        client = _make_mock_deepseek_client()
        graph = build_credibility_verification_workflow(client, checkpointer=None)
        assert graph is not None


# ============================================================
# CredibilityVerificationState TypedDict Tests
# ============================================================


class TestCredibilityVerificationState:
    """CredibilityVerificationState TypedDict 测试"""

    def test_state_can_be_created(self):
        """测试可以创建状态字典"""
        state: CredibilityVerificationState = {
            "stock_code": "600519.SH",
            "concept": "AI+白酒",
            "main_business_score": 50,
            "main_business_description": "",
            "main_business_analysis": "",
            "evidence_score": 50,
            "evidence_patents": [],
            "evidence_orders": [],
            "evidence_partnerships": [],
            "evidence_analysis": "",
            "hype_score": 50,
            "hype_past_concepts": [],
            "hype_analysis": "",
            "supply_chain_score": 50,
            "supply_chain_upstream": [],
            "supply_chain_downstream": [],
            "supply_chain_analysis": "",
            "progress": 0,
            "current_agent": "",
        }
        assert state["stock_code"] == "600519.SH"
        assert state["concept"] == "AI+白酒"
        assert state["progress"] == 0

    def test_state_has_all_required_fields(self):
        """测试状态包含所有必需字段"""
        expected_fields = {
            "stock_code",
            "concept",
            "main_business_score",
            "main_business_description",
            "main_business_analysis",
            "evidence_score",
            "evidence_patents",
            "evidence_orders",
            "evidence_partnerships",
            "evidence_analysis",
            "hype_score",
            "hype_past_concepts",
            "hype_analysis",
            "supply_chain_score",
            "supply_chain_upstream",
            "supply_chain_downstream",
            "supply_chain_analysis",
            "progress",
            "current_agent",
        }
        assert set(CredibilityVerificationState.__annotations__.keys()) == expected_fields


# ============================================================
# CredibilityVerificationWorkflowService Tests
# ============================================================


class TestCredibilityVerificationWorkflowService:
    """CredibilityVerificationWorkflowService 测试"""

    def test_service_implements_interface(self):
        """测试服务实现 ICredibilityVerificationService 接口"""
        from src.backend.contexts.intelligence.domain.services.credibility_verification_service import (
            ICredibilityVerificationService,
        )

        client = _make_mock_deepseek_client()
        service = CredibilityVerificationWorkflowService(deepseek_client=client)
        assert isinstance(service, ICredibilityVerificationService)

    @pytest.mark.asyncio
    async def test_verify_credibility_returns_credibility_report(self):
        """测试 verify_credibility 返回 CredibilityReport 值对象"""
        client = _make_mock_deepseek_client()
        service = CredibilityVerificationWorkflowService(deepseek_client=client)

        stock_code = StockCode("688399.SH")
        result = await service.verify_credibility(stock_code, "固态电池")

        assert isinstance(result, CredibilityReport)
        assert result.stock_code == stock_code
        assert result.concept == "固态电池"
        assert 0 <= result.overall_score.score <= 100
        assert result.main_business_match.score == 85
        assert result.evidence.score == 70
        assert result.hype_history.score == 80
        assert result.supply_chain_logic.score == 75

    @pytest.mark.asyncio
    async def test_verify_credibility_calls_progress_callback(self):
        """测试 verify_credibility 调用进度回调"""
        client = _make_mock_deepseek_client()
        service = CredibilityVerificationWorkflowService(deepseek_client=client)

        progress_updates = []

        def on_progress(progress: int, agent_step: AgentStep):
            progress_updates.append((progress, agent_step))

        stock_code = StockCode("688399.SH")
        result = await service.verify_credibility(
            stock_code, "固态电池", progress_callback=on_progress
        )

        assert isinstance(result, CredibilityReport)
        # Should have received progress updates for agents
        assert len(progress_updates) > 0
        # Each update should have valid progress and agent_step
        for progress, step in progress_updates:
            assert 0 <= progress <= 100
            assert isinstance(step, AgentStep)
            assert step.status == AgentStepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_verify_credibility_without_callback(self):
        """测试不传入回调时正常执行"""
        client = _make_mock_deepseek_client()
        service = CredibilityVerificationWorkflowService(deepseek_client=client)

        stock_code = StockCode("600519.SH")
        result = await service.verify_credibility(stock_code, "AI+白酒")

        assert isinstance(result, CredibilityReport)
        assert result.stock_code == stock_code
        assert result.concept == "AI+白酒"

    @pytest.mark.asyncio
    async def test_verify_credibility_with_checkpointer(self):
        """测试使用 checkpointer 执行工作流"""
        from langgraph.checkpoint.memory import MemorySaver

        client = _make_mock_deepseek_client()
        checkpointer = MemorySaver()
        service = CredibilityVerificationWorkflowService(
            deepseek_client=client, checkpointer=checkpointer
        )

        stock_code = StockCode("300750.SZ")
        result = await service.verify_credibility(stock_code, "固态电池")

        assert isinstance(result, CredibilityReport)
        assert result.stock_code == stock_code

    @pytest.mark.asyncio
    async def test_verify_credibility_handles_llm_error(self):
        """测试 LLM 调用失败时的错误处理"""
        config = DeepSeekConfig(
            api_key="test-key",
            base_url="https://api.test.com/v1",
            timeout=10.0,
            max_retries=0,
        )
        client = DeepSeekClient(config)

        async def mock_chat_error(messages, **kwargs):
            raise LLMServiceError("API 调用失败")

        client.chat = mock_chat_error
        service = CredibilityVerificationWorkflowService(deepseek_client=client)

        stock_code = StockCode("600519.SH")
        # The workflow should still complete (agents handle errors gracefully)
        # but the result will have fallback values
        result = await service.verify_credibility(stock_code, "AI+白酒")
        assert isinstance(result, CredibilityReport)
        # Analysis fields should contain error indication
        assert "[分析失败" in result.main_business_match.main_business_description

    @pytest.mark.asyncio
    async def test_verify_credibility_overall_score_in_range(self):
        """测试总体评分在 0-100 范围内"""
        client = _make_mock_deepseek_client()
        service = CredibilityVerificationWorkflowService(deepseek_client=client)

        stock_code = StockCode("688399.SH")
        result = await service.verify_credibility(stock_code, "固态电池")

        assert 0 <= result.overall_score.score <= 100

    @pytest.mark.asyncio
    async def test_verify_credibility_report_has_all_dimensions(self):
        """测试报告包含所有四个分析维度"""
        client = _make_mock_deepseek_client()
        service = CredibilityVerificationWorkflowService(deepseek_client=client)

        stock_code = StockCode("688399.SH")
        result = await service.verify_credibility(stock_code, "固态电池")

        # All four dimensions should be present
        assert result.main_business_match is not None
        assert result.evidence is not None
        assert result.hype_history is not None
        assert result.supply_chain_logic is not None

        # Evidence should have patent and order data
        assert len(result.evidence.patents) == 2
        assert len(result.evidence.orders) == 1
        assert len(result.evidence.partnerships) == 1

        # Hype history should have past concepts
        assert len(result.hype_history.past_concepts) == 1

        # Supply chain should have upstream and downstream
        assert len(result.supply_chain_logic.upstream) == 2
        assert len(result.supply_chain_logic.downstream) == 2

    @pytest.mark.asyncio
    async def test_verify_credibility_conclusion_contains_stock_and_concept(self):
        """测试结论包含股票代码和概念"""
        client = _make_mock_deepseek_client()
        service = CredibilityVerificationWorkflowService(deepseek_client=client)

        stock_code = StockCode("688399.SH")
        result = await service.verify_credibility(stock_code, "固态电池")

        assert "688399.SH" in result.conclusion
        assert "固态电池" in result.conclusion

    @pytest.mark.asyncio
    async def test_verify_credibility_low_scores_produce_risk_labels(self):
        """测试低评分产生风险标签"""
        responses = [
            # Agent 1: low main business match
            json.dumps({
                "score": 10,
                "main_business_description": "白酒生产与销售",
                "match_analysis": "主营业务与AI无关联",
            }),
            # Agent 2: low evidence
            json.dumps({
                "score": 5,
                "patents": [],
                "orders": [],
                "partnerships": [],
                "analysis": "未发现AI相关证据",
            }),
            # Agent 3: low hype score (many past concepts)
            json.dumps({
                "score": 20,
                "past_concepts": ["元宇宙", "区块链", "AI"],
                "analysis": "历史上频繁蹭热点",
            }),
            # Agent 4: low supply chain
            json.dumps({
                "score": 5,
                "upstream": ["高粱", "小麦"],
                "downstream": ["经销商", "零售"],
                "analysis": "供应链与AI无逻辑关联",
            }),
        ]
        client = _make_mock_deepseek_client(responses)
        service = CredibilityVerificationWorkflowService(deepseek_client=client)

        stock_code = StockCode("600519.SH")
        result = await service.verify_credibility(stock_code, "AI+白酒")

        assert isinstance(result, CredibilityReport)
        assert result.overall_score.score < 30
        assert len(result.risk_labels) > 0
        assert RiskLabel.BUSINESS_MISMATCH in result.risk_labels
        assert RiskLabel.WEAK_EVIDENCE in result.risk_labels
        assert RiskLabel.PURE_HYPE in result.risk_labels
