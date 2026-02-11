"""快速行业认知 LangGraph 工作流

实现 5-Agent 协作工作流，按顺序执行：
1. 行业背景速览 (industry_overview)
2. 市场热度分析 (market_heat)
3. 标的快速筛选 (stock_screening)
4. 真实性批量验证 (credibility_batch)
5. 竞争格局速览 (competitive_landscape)

工作流使用 LangGraph StateGraph 编排，支持 Redis checkpointer 持久化状态。
实现 IIndustryResearchService 接口，供应用层调用。

Agent 节点支持失败重试机制（Requirements 6.6, 10.3）：
- 每个 Agent 节点在执行失败时自动重试（可配置次数和延迟）
- 所有重试耗尽后返回降级值，并记录 FAILED 状态的 AgentStep
- Redis checkpoint 支持从失败点恢复工作流

Requirements: 6.1, 6.2, 6.5, 6.6, 6.7, 10.3
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from contexts.intelligence.domain.enums.enums import AgentStepStatus
from contexts.intelligence.domain.exceptions import (
    AnalysisTimeoutError,
    LLMServiceError,
)
from contexts.intelligence.domain.services.industry_research_service import (
    IIndustryResearchService,
)
from contexts.intelligence.domain.value_objects.agent_step import AgentStep
from contexts.intelligence.domain.value_objects.credibility_score import (
    CredibilityScore,
)
from contexts.intelligence.domain.value_objects.industry_insight import (
    IndustryInsight,
)
from contexts.intelligence.domain.value_objects.stock_credibility import (
    StockCredibility,
)
from contexts.intelligence.infrastructure.ai.agent_retry import (
    AgentRetryConfig,
    DEFAULT_RETRY_CONFIG,
    execute_agent_with_retry,
)
from contexts.intelligence.infrastructure.ai.deepseek_client import (
    ChatMessage,
    DeepSeekClient,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LangGraph 工作流状态定义
# ---------------------------------------------------------------------------

class IndustryResearchState(TypedDict):
    """快速行业认知工作流状态

    LangGraph StateGraph 使用的状态字典，各 Agent 节点读写此状态。
    """

    query: str  # 用户查询
    # Agent 1: 行业背景速览 输出
    industry_summary: str
    industry_chain: str
    technology_routes: list
    market_size: str
    # Agent 2: 市场热度分析 输出
    heat_score: int
    news_summary: str
    # Agent 3: 标的快速筛选 输出
    candidate_stocks: list
    # Agent 4: 真实性批量验证 输出
    verified_stocks: list  # List[dict] with stock credibility info
    # Agent 5: 竞争格局速览 输出
    competitive_landscape: str
    # 汇总
    risk_alerts: list
    catalysts: list
    # 进度跟踪
    progress: int
    current_agent: str


# ---------------------------------------------------------------------------
# Agent 节点名称与进度映射
# ---------------------------------------------------------------------------

AGENT_NAMES = {
    "industry_overview": "行业背景速览",
    "market_heat": "市场热度分析",
    "stock_screening": "标的快速筛选",
    "credibility_batch": "真实性批量验证",
    "competitive_landscape": "竞争格局速览",
}

AGENT_PROGRESS = {
    "industry_overview": 20,
    "market_heat": 40,
    "stock_screening": 60,
    "credibility_batch": 80,
    "competitive_landscape": 95,
}


# ---------------------------------------------------------------------------
# Agent 节点函数工厂
# ---------------------------------------------------------------------------

def _build_industry_overview_node(
    deepseek_client: DeepSeekClient,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建 Agent 1: 行业背景速览 节点函数（支持失败重试）"""

    async def _industry_overview_core(state: IndustryResearchState) -> dict:
        """Agent 1 核心逻辑：调用 LLM 分析行业基本面"""
        query = state["query"]
        prompt = (
            f"你是一位资深行业分析师。请对以下行业/赛道进行快速背景分析：\n\n"
            f"查询：{query}\n\n"
            f"请以 JSON 格式返回以下信息：\n"
            f'{{\n'
            f'  "industry_summary": "行业一页纸总结（200-500字）",\n'
            f'  "industry_chain": "产业链结构描述（上游→中游→下游）",\n'
            f'  "technology_routes": ["技术路线1", "技术路线2", ...],\n'
            f'  "market_size": "市场规模描述"\n'
            f'}}\n\n'
            f"请确保返回有效的 JSON 格式。"
        )

        messages = [
            ChatMessage(role="system", content="你是专业的行业研究分析师，擅长快速梳理行业全景。请始终以 JSON 格式返回结果。"),
            ChatMessage(role="user", content=prompt),
        ]

        completion = await deepseek_client.chat(messages, temperature=0.3)
        data = _parse_json_response(completion.content)
        return {
            "industry_summary": data.get("industry_summary", ""),
            "industry_chain": data.get("industry_chain", ""),
            "technology_routes": data.get("technology_routes", []),
            "market_size": data.get("market_size", ""),
            "current_agent": "industry_overview",
            "progress": AGENT_PROGRESS["industry_overview"],
        }

    async def industry_overview_agent(state: IndustryResearchState) -> dict:
        """Agent 1: 行业背景速览（带重试）"""
        cb = failure_callback_holder[0] if failure_callback_holder else None
        fallback = {
            "industry_summary": "[分析失败]",
            "industry_chain": "",
            "technology_routes": [],
            "market_size": "",
            "current_agent": "industry_overview",
            "progress": AGENT_PROGRESS["industry_overview"],
        }
        return await execute_agent_with_retry(
            agent_fn=_industry_overview_core,
            state=state,
            agent_name=AGENT_NAMES["industry_overview"],
            fallback_state=fallback,
            retry_config=retry_config,
            progress_callback=cb,
        )

    return industry_overview_agent


def _build_market_heat_node(
    deepseek_client: DeepSeekClient,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建 Agent 2: 市场热度分析 节点函数（支持失败重试）"""

    async def _market_heat_core(state: IndustryResearchState) -> dict:
        """Agent 2 核心逻辑：分析行业市场热度"""
        query = state["query"]
        industry_summary = state.get("industry_summary", "")

        prompt = (
            f"你是一位市场热度分析专家。请分析以下行业的当前市场热度：\n\n"
            f"查询：{query}\n"
            f"行业背景：{industry_summary[:500]}\n\n"
            f"请以 JSON 格式返回以下信息：\n"
            f'{{\n'
            f'  "heat_score": 0到100的整数（市场热度评分）,\n'
            f'  "news_summary": "近期相关新闻和市场动态摘要",\n'
            f'  "risk_alerts": ["风险提示1", "风险提示2", ...],\n'
            f'  "catalysts": ["催化剂1", "催化剂2", ...]\n'
            f'}}\n\n'
            f"请确保 heat_score 是 0-100 的整数，返回有效的 JSON 格式。"
        )

        messages = [
            ChatMessage(role="system", content="你是专业的市场热度分析师，擅长评估行业关注度和市场情绪。请始终以 JSON 格式返回结果。"),
            ChatMessage(role="user", content=prompt),
        ]

        completion = await deepseek_client.chat(messages, temperature=0.3)
        data = _parse_json_response(completion.content)
        heat_score = data.get("heat_score", 50)
        heat_score = max(0, min(100, int(heat_score)))
        return {
            "heat_score": heat_score,
            "news_summary": data.get("news_summary", ""),
            "risk_alerts": data.get("risk_alerts", []),
            "catalysts": data.get("catalysts", []),
            "current_agent": "market_heat",
            "progress": AGENT_PROGRESS["market_heat"],
        }

    async def market_heat_agent(state: IndustryResearchState) -> dict:
        """Agent 2: 市场热度分析（带重试）"""
        cb = failure_callback_holder[0] if failure_callback_holder else None
        fallback = {
            "heat_score": 50,
            "news_summary": "[分析失败]",
            "risk_alerts": [],
            "catalysts": [],
            "current_agent": "market_heat",
            "progress": AGENT_PROGRESS["market_heat"],
        }
        return await execute_agent_with_retry(
            agent_fn=_market_heat_core,
            state=state,
            agent_name=AGENT_NAMES["market_heat"],
            fallback_state=fallback,
            retry_config=retry_config,
            progress_callback=cb,
        )

    return market_heat_agent


def _build_stock_screening_node(
    deepseek_client: DeepSeekClient,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建 Agent 3: 标的快速筛选 节点函数（支持失败重试）"""

    async def _stock_screening_core(state: IndustryResearchState) -> dict:
        """Agent 3 核心逻辑：基于行业分析筛选候选标的"""
        query = state["query"]
        industry_summary = state.get("industry_summary", "")
        industry_chain = state.get("industry_chain", "")

        prompt = (
            f"你是一位股票筛选专家。请基于以下行业分析，筛选 5-10 只核心标的：\n\n"
            f"查询：{query}\n"
            f"行业总结：{industry_summary[:300]}\n"
            f"产业链：{industry_chain[:300]}\n\n"
            f"请以 JSON 格式返回候选标的列表：\n"
            f'{{\n'
            f'  "candidate_stocks": [\n'
            f'    {{\n'
            f'      "stock_code": "600XXX.SH 或 000XXX.SZ 格式",\n'
            f'      "stock_name": "股票名称",\n'
            f'      "relevance_summary": "与该行业的相关性说明"\n'
            f'    }}\n'
            f'  ]\n'
            f'}}\n\n'
            f"请确保 stock_code 使用 A 股代码格式（如 600519.SH、000001.SZ），返回有效的 JSON 格式。"
        )

        messages = [
            ChatMessage(role="system", content="你是专业的 A 股标的筛选分析师，擅长从行业视角筛选核心标的。请始终以 JSON 格式返回结果。"),
            ChatMessage(role="user", content=prompt),
        ]

        completion = await deepseek_client.chat(messages, temperature=0.3)
        data = _parse_json_response(completion.content)
        return {
            "candidate_stocks": data.get("candidate_stocks", []),
            "current_agent": "stock_screening",
            "progress": AGENT_PROGRESS["stock_screening"],
        }

    async def stock_screening_agent(state: IndustryResearchState) -> dict:
        """Agent 3: 标的快速筛选（带重试）"""
        cb = failure_callback_holder[0] if failure_callback_holder else None
        fallback = {
            "candidate_stocks": [],
            "current_agent": "stock_screening",
            "progress": AGENT_PROGRESS["stock_screening"],
        }
        return await execute_agent_with_retry(
            agent_fn=_stock_screening_core,
            state=state,
            agent_name=AGENT_NAMES["stock_screening"],
            fallback_state=fallback,
            retry_config=retry_config,
            progress_callback=cb,
        )

    return stock_screening_agent


def _build_credibility_batch_node(
    deepseek_client: DeepSeekClient,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建 Agent 4: 真实性批量验证 节点函数（支持失败重试）"""

    async def _credibility_batch_core(state: IndustryResearchState) -> dict:
        """Agent 4 核心逻辑：对候选标的进行批量可信度验证"""
        query = state["query"]
        candidate_stocks = state.get("candidate_stocks", [])

        if not candidate_stocks:
            return {
                "verified_stocks": [],
                "current_agent": "credibility_batch",
                "progress": AGENT_PROGRESS["credibility_batch"],
            }

        stocks_text = "\n".join(
            f"- {s.get('stock_code', 'N/A')} {s.get('stock_name', 'N/A')}: {s.get('relevance_summary', '')}"
            for s in candidate_stocks
        )

        prompt = (
            f"你是一位可信度验证专家。请对以下候选标的进行批量可信度评估：\n\n"
            f"行业/概念：{query}\n"
            f"候选标的：\n{stocks_text}\n\n"
            f"请对每只股票评估其与该行业/概念的真实关联度，以 JSON 格式返回：\n"
            f'{{\n'
            f'  "verified_stocks": [\n'
            f'    {{\n'
            f'      "stock_code": "股票代码",\n'
            f'      "stock_name": "股票名称",\n'
            f'      "credibility_score": 0到100的整数,\n'
            f'      "relevance_summary": "可信度分析说明"\n'
            f'    }}\n'
            f'  ]\n'
            f'}}\n\n'
            f"credibility_score 评分标准：80-100 高可信度，50-79 中可信度，0-49 低可信度。"
            f"请确保返回有效的 JSON 格式。"
        )

        messages = [
            ChatMessage(role="system", content="你是专业的概念可信度验证分析师，擅长辨别上市公司与热门概念的真实关联度。请始终以 JSON 格式返回结果。"),
            ChatMessage(role="user", content=prompt),
        ]

        completion = await deepseek_client.chat(messages, temperature=0.3)
        data = _parse_json_response(completion.content)
        verified = data.get("verified_stocks", [])
        # Clamp credibility scores to valid range
        for stock in verified:
            score = stock.get("credibility_score", 50)
            stock["credibility_score"] = max(0, min(100, int(score)))
        return {
            "verified_stocks": verified,
            "current_agent": "credibility_batch",
            "progress": AGENT_PROGRESS["credibility_batch"],
        }

    async def credibility_batch_agent(state: IndustryResearchState) -> dict:
        """Agent 4: 真实性批量验证（带重试）"""
        cb = failure_callback_holder[0] if failure_callback_holder else None
        fallback = {
            "verified_stocks": [],
            "current_agent": "credibility_batch",
            "progress": AGENT_PROGRESS["credibility_batch"],
        }
        return await execute_agent_with_retry(
            agent_fn=_credibility_batch_core,
            state=state,
            agent_name=AGENT_NAMES["credibility_batch"],
            fallback_state=fallback,
            retry_config=retry_config,
            progress_callback=cb,
        )

    return credibility_batch_agent


def _build_competitive_landscape_node(
    deepseek_client: DeepSeekClient,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建 Agent 5: 竞争格局速览 节点函数（支持失败重试）"""

    async def _competitive_landscape_core(state: IndustryResearchState) -> dict:
        """Agent 5 核心逻辑：分析行业竞争格局"""
        query = state["query"]
        industry_summary = state.get("industry_summary", "")
        verified_stocks = state.get("verified_stocks", [])

        stocks_text = ", ".join(
            f"{s.get('stock_name', 'N/A')}({s.get('stock_code', 'N/A')})"
            for s in verified_stocks[:10]
        )

        prompt = (
            f"你是一位竞争格局分析专家。请分析以下行业的竞争格局：\n\n"
            f"查询：{query}\n"
            f"行业背景：{industry_summary[:300]}\n"
            f"核心标的：{stocks_text}\n\n"
            f"请以 JSON 格式返回：\n"
            f'{{\n'
            f'  "competitive_landscape": "竞争格局分析（300-500字，包括行业集中度、主要玩家、竞争壁垒等）"\n'
            f'}}\n\n'
            f"请确保返回有效的 JSON 格式。"
        )

        messages = [
            ChatMessage(role="system", content="你是专业的行业竞争格局分析师，擅长分析行业竞争态势和企业竞争优势。请始终以 JSON 格式返回结果。"),
            ChatMessage(role="user", content=prompt),
        ]

        completion = await deepseek_client.chat(messages, temperature=0.3)
        data = _parse_json_response(completion.content)
        return {
            "competitive_landscape": data.get("competitive_landscape", ""),
            "current_agent": "competitive_landscape",
            "progress": AGENT_PROGRESS["competitive_landscape"],
        }

    async def competitive_landscape_agent(state: IndustryResearchState) -> dict:
        """Agent 5: 竞争格局速览（带重试）"""
        cb = failure_callback_holder[0] if failure_callback_holder else None
        fallback = {
            "competitive_landscape": "[分析失败]",
            "current_agent": "competitive_landscape",
            "progress": AGENT_PROGRESS["competitive_landscape"],
        }
        return await execute_agent_with_retry(
            agent_fn=_competitive_landscape_core,
            state=state,
            agent_name=AGENT_NAMES["competitive_landscape"],
            fallback_state=fallback,
            retry_config=retry_config,
            progress_callback=cb,
        )

    return competitive_landscape_agent


# ---------------------------------------------------------------------------
# JSON 解析辅助函数
# ---------------------------------------------------------------------------

def _parse_json_response(content: str) -> dict:
    """解析 LLM 返回的 JSON 内容

    支持从 markdown 代码块中提取 JSON，以及直接解析 JSON 字符串。

    Args:
        content: LLM 返回的文本内容

    Returns:
        解析后的字典

    Raises:
        LLMServiceError: JSON 解析失败
    """
    text = content.strip()

    # 尝试从 markdown 代码块中提取 JSON
    if "```json" in text:
        start = text.index("```json") + len("```json")
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + len("```")
        end = text.index("```", start)
        text = text[start:end].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("JSON 解析失败，尝试修复: %s", str(e))
        # 尝试找到第一个 { 和最后一个 } 之间的内容
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            try:
                return json.loads(text[brace_start : brace_end + 1])
            except json.JSONDecodeError:
                pass
        raise LLMServiceError(f"无法解析 LLM 返回的 JSON: {str(e)}")


# ---------------------------------------------------------------------------
# 结果聚合节点
# ---------------------------------------------------------------------------

def _build_aggregate_results_node():
    """构建结果聚合节点"""

    async def aggregate_results(state: IndustryResearchState) -> dict:
        """聚合所有 Agent 输出，不做额外 LLM 调用"""
        return {
            "progress": 100,
            "current_agent": "aggregate_results",
        }

    return aggregate_results


# ---------------------------------------------------------------------------
# 工作流构建函数
# ---------------------------------------------------------------------------

def build_industry_research_workflow(
    deepseek_client: DeepSeekClient,
    checkpointer=None,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建快速行业认知 LangGraph 工作流

    Args:
        deepseek_client: DeepSeek LLM 客户端
        checkpointer: LangGraph checkpointer（Redis 或 Memory），
                      为 None 时不使用 checkpointer
        retry_config: Agent 重试配置，为 None 时使用默认配置
        failure_callback_holder: 可变列表 [callback]，用于在运行时注入失败回调。
                                 Agent 节点通过闭包捕获此列表，在执行时读取 [0] 元素。

    Returns:
        编译后的 LangGraph 工作流（CompiledGraph）
    """
    workflow = StateGraph(IndustryResearchState)

    # 添加 Agent 节点（每个节点支持失败重试）
    workflow.add_node("industry_overview", _build_industry_overview_node(deepseek_client, retry_config, failure_callback_holder))
    workflow.add_node("market_heat", _build_market_heat_node(deepseek_client, retry_config, failure_callback_holder))
    workflow.add_node("stock_screening", _build_stock_screening_node(deepseek_client, retry_config, failure_callback_holder))
    workflow.add_node("credibility_batch", _build_credibility_batch_node(deepseek_client, retry_config, failure_callback_holder))
    workflow.add_node("competitive_landscape", _build_competitive_landscape_node(deepseek_client, retry_config, failure_callback_holder))
    workflow.add_node("aggregate_results", _build_aggregate_results_node())

    # 配置顺序执行边
    workflow.add_edge(START, "industry_overview")
    workflow.add_edge("industry_overview", "market_heat")
    workflow.add_edge("market_heat", "stock_screening")
    workflow.add_edge("stock_screening", "credibility_batch")
    workflow.add_edge("credibility_batch", "competitive_landscape")
    workflow.add_edge("competitive_landscape", "aggregate_results")
    workflow.add_edge("aggregate_results", END)

    # 编译工作流
    compile_kwargs = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer

    return workflow.compile(**compile_kwargs)


# ---------------------------------------------------------------------------
# Redis Checkpointer 工厂
# ---------------------------------------------------------------------------

def create_redis_checkpointer():
    """创建 Redis checkpointer 用于 LangGraph 状态持久化

    从环境变量 REDIS_URL 读取 Redis 连接地址。
    如果 Redis 不可用，返回 None（降级为无 checkpoint 模式）。

    Returns:
        Redis checkpointer 实例，或 None
    """
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        from langgraph.checkpoint.memory import MemorySaver

        # 注意：langgraph 的 Redis checkpointer 需要额外安装 langgraph-checkpoint-redis
        # 如果未安装，降级使用 MemorySaver
        try:
            from langgraph.checkpoint.redis import RedisSaver

            return RedisSaver(redis_url)
        except ImportError:
            logger.warning(
                "langgraph-checkpoint-redis 未安装，降级使用 MemorySaver。"
                "如需 Redis 持久化，请安装: pip install langgraph-checkpoint-redis"
            )
            return MemorySaver()
    except Exception as e:
        logger.warning("创建 checkpointer 失败，将不使用 checkpoint: %s", str(e))
        return None


# ---------------------------------------------------------------------------
# IIndustryResearchService 实现
# ---------------------------------------------------------------------------

class IndustryResearchWorkflowService(IIndustryResearchService):
    """快速行业认知服务实现

    使用 LangGraph 5-Agent 工作流实现 IIndustryResearchService 接口。
    工作流按顺序执行 5 个 Agent，每个 Agent 完成后通过回调更新进度。
    Agent 节点支持失败重试机制，所有重试耗尽后返回降级值并记录 FAILED AgentStep。

    Requirements: 6.1, 6.2, 6.5, 6.6, 6.7, 10.3
    """

    def __init__(
        self,
        deepseek_client: DeepSeekClient,
        checkpointer=None,
        retry_config: Optional[AgentRetryConfig] = None,
    ):
        """初始化工作流服务

        Args:
            deepseek_client: DeepSeek LLM 客户端
            checkpointer: LangGraph checkpointer（Redis 或 Memory）
            retry_config: Agent 重试配置，为 None 时使用默认配置
        """
        self._deepseek_client = deepseek_client
        self._checkpointer = checkpointer
        self._retry_config = retry_config
        # Mutable holder for failure callback — set before each execution.
        # Agent nodes capture this list via closure and read [0] at runtime.
        self._failure_callback_holder: List = [None]
        self._compiled_workflow = build_industry_research_workflow(
            deepseek_client=deepseek_client,
            checkpointer=checkpointer,
            retry_config=retry_config,
            failure_callback_holder=self._failure_callback_holder,
        )

    async def execute_research(
        self, query: str, progress_callback=None
    ) -> IndustryInsight:
        """执行快速行业认知工作流

        按顺序执行 5 个 Agent，每个 Agent 完成后通过 progress_callback 更新进度。
        最终将所有 Agent 输出聚合为 IndustryInsight 值对象。

        Args:
            query: 用户查询（如"快速了解合成生物学赛道"）
            progress_callback: 进度回调函数
                签名: (progress: int, agent_step: AgentStep) -> None

        Returns:
            IndustryInsight 值对象

        Raises:
            LLMServiceError: LLM 调用失败
            AnalysisTimeoutError: 分析超时
        """
        # 初始化工作流状态
        initial_state: IndustryResearchState = {
            "query": query,
            "industry_summary": "",
            "industry_chain": "",
            "technology_routes": [],
            "market_size": "",
            "heat_score": 50,
            "news_summary": "",
            "candidate_stocks": [],
            "verified_stocks": [],
            "competitive_landscape": "",
            "risk_alerts": [],
            "catalysts": [],
            "progress": 0,
            "current_agent": "",
        }

        # 设置失败回调：当 Agent 重试耗尽时，通过此回调报告 FAILED AgentStep
        failed_steps: List[AgentStep] = []

        def _on_agent_failure(agent_step: AgentStep):
            """Agent 重试耗尽后的失败回调"""
            failed_steps.append(agent_step)
            if progress_callback is not None:
                # 通过进度回调报告 FAILED 步骤
                progress_value = AGENT_PROGRESS.get(
                    next(
                        (k for k, v in AGENT_NAMES.items() if v == agent_step.agent_name),
                        "",
                    ),
                    0,
                )
                progress_callback(progress_value, agent_step)

        # 注入失败回调到 holder（Agent 节点通过闭包读取）
        self._failure_callback_holder[0] = _on_agent_failure

        # 配置执行参数
        config: Dict[str, Any] = {}
        if self._checkpointer is not None:
            # 使用唯一 thread_id 以支持 checkpoint
            import uuid

            config["configurable"] = {"thread_id": str(uuid.uuid4())}

        # 执行工作流，逐步收集状态更新
        last_agent = ""
        final_state = initial_state.copy()

        try:
            async for event in self._compiled_workflow.astream(
                initial_state, config=config
            ):
                # LangGraph astream 返回 {node_name: state_update} 格式
                for node_name, state_update in event.items():
                    if isinstance(state_update, dict):
                        final_state.update(state_update)

                    current_agent = final_state.get("current_agent", "")
                    if current_agent and current_agent != last_agent:
                        last_agent = current_agent
                        # 通过回调通知进度
                        if progress_callback is not None:
                            agent_display_name = AGENT_NAMES.get(
                                current_agent, current_agent
                            )
                            progress = final_state.get("progress", 0)
                            now = datetime.now(timezone.utc)
                            agent_step = AgentStep(
                                agent_name=agent_display_name,
                                status=AgentStepStatus.COMPLETED,
                                started_at=now,
                                completed_at=now,
                                output_summary=f"{agent_display_name} 已完成",
                            )
                            progress_callback(progress, agent_step)

        except Exception as e:
            logger.error("工作流执行失败: %s", str(e))
            raise LLMServiceError(f"行业认知工作流执行失败: {str(e)}") from e

        # 将最终状态转换为 IndustryInsight 值对象
        return self._build_industry_insight(query, final_state)

    def _build_industry_insight(
        self, query: str, state: dict
    ) -> IndustryInsight:
        """将工作流最终状态转换为 IndustryInsight 值对象

        Args:
            query: 用户查询
            state: 工作流最终状态

        Returns:
            IndustryInsight 值对象
        """
        # 从 query 中提取行业名称（简单处理：使用 query 本身）
        industry_name = query.strip()

        # 构建 top_stocks 列表
        top_stocks: List[StockCredibility] = []
        for stock_data in state.get("verified_stocks", []):
            try:
                from shared_kernel.value_objects.stock_code import StockCode

                stock_code_str = stock_data.get("stock_code", "")
                stock_name = stock_data.get("stock_name", "未知")
                score_val = stock_data.get("credibility_score", 50)
                score_val = max(0, min(100, int(score_val)))
                relevance = stock_data.get("relevance_summary", "")

                stock_code = StockCode(stock_code_str)
                credibility_score = CredibilityScore(score_val)
                top_stocks.append(
                    StockCredibility(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        credibility_score=credibility_score,
                        relevance_summary=relevance,
                    )
                )
            except (ValueError, Exception) as e:
                logger.warning(
                    "构建 StockCredibility 失败，跳过: %s, 错误: %s",
                    stock_data,
                    str(e),
                )
                continue

        # 确保 heat_score 在有效范围内
        heat_score = state.get("heat_score", 50)
        heat_score = max(0, min(100, int(heat_score)))

        return IndustryInsight(
            industry_name=industry_name,
            summary=state.get("industry_summary", ""),
            industry_chain=state.get("industry_chain", ""),
            technology_routes=state.get("technology_routes", []),
            market_size=state.get("market_size", ""),
            top_stocks=top_stocks,
            risk_alerts=state.get("risk_alerts", []),
            catalysts=state.get("catalysts", []),
            heat_score=heat_score,
            competitive_landscape=state.get("competitive_landscape", ""),
        )
