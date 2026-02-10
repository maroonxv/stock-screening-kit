"""快速行业认知 LangGraph 工作流单元测试

测试 IndustryResearchState、Agent 节点函数、工作流构建、
JSON 解析辅助函数和 IndustryResearchWorkflowService。

Requirements: 6.1, 6.2, 6.5, 6.7
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backend.contexts.intelligence.domain.enums.enums import AgentStepStatus
from src.backend.contexts.intelligence.domain.exceptions import LLMServiceError
from src.backend.contexts.intelligence.domain.value_objects.agent_step import AgentStep
from src.backend.contexts.intelligence.domain.value_objects.industry_insight import (
    IndustryInsight,
)
from src.backend.contexts.intelligence.infrastructure.ai.deepseek_client import (
    ChatCompletion,
    ChatMessage,
    DeepSeekClient,
    DeepSeekConfig,
)
from src.backend.contexts.intelligence.infrastructure.ai.industry_research_workflow import (
    AGENT_NAMES,
    AGENT_PROGRESS,
    IndustryResearchState,
    IndustryResearchWorkflowService,
    _parse_json_response,
    build_industry_research_workflow,
)


# ============================================================
# Helper: Create a mock DeepSeek client
# ============================================================


def _make_mock_deepseek_client(responses: list[str] | None = None):
    """Create a mock DeepSeekClient that returns predefined responses.

    Args:
        responses: List of JSON string responses for sequential calls.
                   If None, uses default responses for all 5 agents.
    """
    if responses is None:
        responses = [
            # Agent 1: industry_overview
            json.dumps({
                "industry_summary": "合成生物学是一个新兴行业",
                "industry_chain": "上游基因合成→中游菌株构建→下游产品应用",
                "technology_routes": ["基因编辑", "代谢工程"],
                "market_size": "全球约500亿美元",
            }),
            # Agent 2: market_heat
            json.dumps({
                "heat_score": 75,
                "news_summary": "近期政策利好频出",
                "risk_alerts": ["行业早期风险", "商业化不确定"],
                "catalysts": ["政策支持", "技术突破"],
            }),
            # Agent 3: stock_screening
            json.dumps({
                "candidate_stocks": [
                    {
                        "stock_code": "688399.SH",
                        "stock_name": "硕世生物",
                        "relevance_summary": "主营业务与合成生物学相关",
                    },
                    {
                        "stock_code": "300601.SZ",
                        "stock_name": "康泰生物",
                        "relevance_summary": "疫苗研发涉及合成生物技术",
                    },
                ]
            }),
            # Agent 4: credibility_batch
            json.dumps({
                "verified_stocks": [
                    {
                        "stock_code": "688399.SH",
                        "stock_name": "硕世生物",
                        "credibility_score": 85,
                        "relevance_summary": "高度相关，主营业务匹配",
                    },
                    {
                        "stock_code": "300601.SZ",
                        "stock_name": "康泰生物",
                        "credibility_score": 60,
                        "relevance_summary": "部分相关，疫苗领域有交叉",
                    },
                ]
            }),
            # Agent 5: competitive_landscape
            json.dumps({
                "competitive_landscape": "行业集中度低，竞争格局分散，多家企业处于早期布局阶段",
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
# _parse_json_response Tests
# ============================================================


class TestParseJsonResponse:
    """JSON 解析辅助函数测试"""

    def test_parse_plain_json(self):
        """测试解析纯 JSON 字符串"""
        content = '{"key": "value", "number": 42}'
        result = _parse_json_response(content)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_in_markdown_code_block(self):
        """测试从 markdown ```json 代码块中提取 JSON"""
        content = '这是一些说明文字\n```json\n{"key": "value"}\n```\n后续文字'
        result = _parse_json_response(content)
        assert result == {"key": "value"}

    def test_parse_json_in_plain_code_block(self):
        """测试从 markdown ``` 代码块中提取 JSON"""
        content = '说明\n```\n{"key": "value"}\n```'
        result = _parse_json_response(content)
        assert result == {"key": "value"}

    def test_parse_json_with_surrounding_text(self):
        """测试从包含额外文字的内容中提取 JSON"""
        content = '这是分析结果：\n{"key": "value"}\n以上是结果。'
        result = _parse_json_response(content)
        assert result == {"key": "value"}

    def test_parse_invalid_json_raises(self):
        """测试无效 JSON 抛出 LLMServiceError"""
        content = "这不是 JSON 内容"
        with pytest.raises(LLMServiceError, match="无法解析"):
            _parse_json_response(content)

    def test_parse_json_with_whitespace(self):
        """测试带空白字符的 JSON"""
        content = '  \n  {"key": "value"}  \n  '
        result = _parse_json_response(content)
        assert result == {"key": "value"}


# ============================================================
# AGENT_NAMES and AGENT_PROGRESS Tests
# ============================================================


class TestAgentConstants:
    """Agent 常量测试"""

    def test_agent_names_has_all_five_agents(self):
        """测试 AGENT_NAMES 包含所有 5 个 Agent"""
        expected_keys = {
            "industry_overview",
            "market_heat",
            "stock_screening",
            "credibility_batch",
            "competitive_landscape",
        }
        assert set(AGENT_NAMES.keys()) == expected_keys

    def test_agent_names_are_chinese(self):
        """测试 Agent 显示名称为中文"""
        assert AGENT_NAMES["industry_overview"] == "行业背景速览"
        assert AGENT_NAMES["market_heat"] == "市场热度分析"
        assert AGENT_NAMES["stock_screening"] == "标的快速筛选"
        assert AGENT_NAMES["credibility_batch"] == "真实性批量验证"
        assert AGENT_NAMES["competitive_landscape"] == "竞争格局速览"

    def test_agent_progress_values_are_increasing(self):
        """测试 Agent 进度值递增"""
        ordered_agents = [
            "industry_overview",
            "market_heat",
            "stock_screening",
            "credibility_batch",
            "competitive_landscape",
        ]
        progress_values = [AGENT_PROGRESS[a] for a in ordered_agents]
        assert progress_values == sorted(progress_values)
        assert all(0 < p <= 100 for p in progress_values)


# ============================================================
# build_industry_research_workflow Tests
# ============================================================


class TestBuildWorkflow:
    """工作流构建测试"""

    def test_build_workflow_returns_compiled_graph(self):
        """测试构建工作流返回编译后的图"""
        client = _make_mock_deepseek_client()
        graph = build_industry_research_workflow(client)
        assert graph is not None

    def test_build_workflow_with_checkpointer(self):
        """测试使用 checkpointer 构建工作流"""
        from langgraph.checkpoint.memory import MemorySaver

        client = _make_mock_deepseek_client()
        checkpointer = MemorySaver()
        graph = build_industry_research_workflow(client, checkpointer=checkpointer)
        assert graph is not None

    def test_build_workflow_without_checkpointer(self):
        """测试不使用 checkpointer 构建工作流"""
        client = _make_mock_deepseek_client()
        graph = build_industry_research_workflow(client, checkpointer=None)
        assert graph is not None


# ============================================================
# IndustryResearchWorkflowService Tests
# ============================================================


class TestIndustryResearchWorkflowService:
    """IndustryResearchWorkflowService 测试"""

    def test_service_implements_interface(self):
        """测试服务实现 IIndustryResearchService 接口"""
        from src.backend.contexts.intelligence.domain.services.industry_research_service import (
            IIndustryResearchService,
        )

        client = _make_mock_deepseek_client()
        service = IndustryResearchWorkflowService(deepseek_client=client)
        assert isinstance(service, IIndustryResearchService)

    @pytest.mark.asyncio
    async def test_execute_research_returns_industry_insight(self):
        """测试 execute_research 返回 IndustryInsight 值对象"""
        client = _make_mock_deepseek_client()
        service = IndustryResearchWorkflowService(deepseek_client=client)

        result = await service.execute_research("合成生物学")

        assert isinstance(result, IndustryInsight)
        assert result.industry_name == "合成生物学"
        assert "合成生物学" in result.summary
        assert result.heat_score == 75
        assert len(result.top_stocks) == 2
        assert len(result.risk_alerts) == 2
        assert len(result.catalysts) == 2
        assert result.competitive_landscape != ""

    @pytest.mark.asyncio
    async def test_execute_research_calls_progress_callback(self):
        """测试 execute_research 调用进度回调"""
        client = _make_mock_deepseek_client()
        service = IndustryResearchWorkflowService(deepseek_client=client)

        progress_updates = []

        def on_progress(progress: int, agent_step: AgentStep):
            progress_updates.append((progress, agent_step))

        result = await service.execute_research("合成生物学", progress_callback=on_progress)

        assert isinstance(result, IndustryInsight)
        # Should have received progress updates for agents
        assert len(progress_updates) > 0
        # Each update should have valid progress and agent_step
        for progress, step in progress_updates:
            assert 0 <= progress <= 100
            assert isinstance(step, AgentStep)
            assert step.status == AgentStepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_research_without_callback(self):
        """测试不传入回调时正常执行"""
        client = _make_mock_deepseek_client()
        service = IndustryResearchWorkflowService(deepseek_client=client)

        result = await service.execute_research("人工智能")

        assert isinstance(result, IndustryInsight)
        assert result.industry_name == "人工智能"

    @pytest.mark.asyncio
    async def test_execute_research_with_checkpointer(self):
        """测试使用 checkpointer 执行工作流"""
        from langgraph.checkpoint.memory import MemorySaver

        client = _make_mock_deepseek_client()
        checkpointer = MemorySaver()
        service = IndustryResearchWorkflowService(
            deepseek_client=client, checkpointer=checkpointer
        )

        result = await service.execute_research("新能源")

        assert isinstance(result, IndustryInsight)
        assert result.industry_name == "新能源"

    @pytest.mark.asyncio
    async def test_execute_research_handles_llm_error(self):
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
        service = IndustryResearchWorkflowService(deepseek_client=client)

        # The workflow should still complete (agents handle errors gracefully)
        # but the result will have fallback values
        result = await service.execute_research("测试行业")
        assert isinstance(result, IndustryInsight)
        # Summary should contain error indication
        assert "[分析失败" in result.summary

    @pytest.mark.asyncio
    async def test_execute_research_top_stocks_have_valid_scores(self):
        """测试返回的 top_stocks 有有效的可信度评分"""
        client = _make_mock_deepseek_client()
        service = IndustryResearchWorkflowService(deepseek_client=client)

        result = await service.execute_research("合成生物学")

        for stock in result.top_stocks:
            assert 0 <= stock.credibility_score.score <= 100
            assert stock.stock_name != ""
            assert stock.stock_code is not None

    @pytest.mark.asyncio
    async def test_execute_research_heat_score_in_range(self):
        """测试 heat_score 在 0-100 范围内"""
        client = _make_mock_deepseek_client()
        service = IndustryResearchWorkflowService(deepseek_client=client)

        result = await service.execute_research("合成生物学")

        assert 0 <= result.heat_score <= 100


# ============================================================
# IndustryResearchState TypedDict Tests
# ============================================================


class TestIndustryResearchState:
    """IndustryResearchState TypedDict 测试"""

    def test_state_can_be_created(self):
        """测试可以创建状态字典"""
        state: IndustryResearchState = {
            "query": "测试查询",
            "industry_summary": "",
            "industry_chain": "",
            "technology_routes": [],
            "market_size": "",
            "heat_score": 0,
            "news_summary": "",
            "candidate_stocks": [],
            "verified_stocks": [],
            "competitive_landscape": "",
            "risk_alerts": [],
            "catalysts": [],
            "progress": 0,
            "current_agent": "",
        }
        assert state["query"] == "测试查询"
        assert state["progress"] == 0

    def test_state_has_all_required_fields(self):
        """测试状态包含所有必需字段"""
        expected_fields = {
            "query",
            "industry_summary",
            "industry_chain",
            "technology_routes",
            "market_size",
            "heat_score",
            "news_summary",
            "candidate_stocks",
            "verified_stocks",
            "competitive_landscape",
            "risk_alerts",
            "catalysts",
            "progress",
            "current_agent",
        }
        # TypedDict annotations contain the field names
        assert set(IndustryResearchState.__annotations__.keys()) == expected_fields
