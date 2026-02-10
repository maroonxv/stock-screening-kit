"""概念可信度验证 LangGraph 工作流

实现 4-Agent 协作工作流，按顺序执行：
1. 主营业务匹配分析 (main_business_match)
2. 实质证据收集 (evidence_collection)
3. 历史蹭热点检测 (hype_history_detection)
4. 供应链逻辑分析 (supply_chain_logic)

工作流使用 LangGraph StateGraph 编排，支持 Redis checkpointer 持久化状态。
实现 ICredibilityVerificationService 接口，供应用层调用。

Agent 节点支持失败重试机制（Requirements 6.6, 10.3）：
- 每个 Agent 节点在执行失败时自动重试（可配置次数和延迟）
- 所有重试耗尽后返回降级值，并记录 FAILED 状态的 AgentStep
- Redis checkpoint 支持从失败点恢复工作流

Requirements: 6.3, 6.6, 6.7, 10.3
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from src.backend.contexts.intelligence.domain.enums.enums import (
    AgentStepStatus,
    RiskLabel,
)
from src.backend.contexts.intelligence.domain.exceptions import (
    LLMServiceError,
)
from src.backend.contexts.intelligence.domain.services.credibility_verification_service import (
    ICredibilityVerificationService,
)
from src.backend.contexts.intelligence.domain.value_objects.agent_step import AgentStep
from src.backend.contexts.intelligence.domain.value_objects.credibility_report import (
    CredibilityReport,
    EvidenceAnalysis,
    HypeHistory,
    MainBusinessMatch,
    SupplyChainLogic,
)
from src.backend.contexts.intelligence.domain.value_objects.credibility_score import (
    CredibilityScore,
)
from src.backend.contexts.intelligence.infrastructure.ai.agent_retry import (
    AgentRetryConfig,
    DEFAULT_RETRY_CONFIG,
    execute_agent_with_retry,
)
from src.backend.contexts.intelligence.infrastructure.ai.deepseek_client import (
    ChatMessage,
    DeepSeekClient,
)
from src.backend.contexts.intelligence.infrastructure.ai.industry_research_workflow import (
    _parse_json_response,
)
from shared_kernel.value_objects.stock_code import StockCode

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LangGraph 工作流状态定义
# ---------------------------------------------------------------------------

class CredibilityVerificationState(TypedDict):
    """概念可信度验证工作流状态

    LangGraph StateGraph 使用的状态字典，各 Agent 节点读写此状态。
    """

    stock_code: str  # 股票代码字符串
    concept: str  # 被验证的概念
    # Agent 1: 主营业务匹配分析 输出
    main_business_score: int
    main_business_description: str
    main_business_analysis: str
    # Agent 2: 实质证据收集 输出
    evidence_score: int
    evidence_patents: list
    evidence_orders: list
    evidence_partnerships: list
    evidence_analysis: str
    # Agent 3: 历史蹭热点检测 输出
    hype_score: int
    hype_past_concepts: list
    hype_analysis: str
    # Agent 4: 供应链逻辑分析 输出
    supply_chain_score: int
    supply_chain_upstream: list
    supply_chain_downstream: list
    supply_chain_analysis: str
    # 进度跟踪
    progress: int
    current_agent: str


# ---------------------------------------------------------------------------
# Agent 节点名称与进度映射
# ---------------------------------------------------------------------------

CREDIBILITY_AGENT_NAMES = {
    "main_business_match": "主营业务匹配分析",
    "evidence_collection": "实质证据收集",
    "hype_history_detection": "历史蹭热点检测",
    "supply_chain_logic": "供应链逻辑分析",
}

CREDIBILITY_AGENT_PROGRESS = {
    "main_business_match": 25,
    "evidence_collection": 50,
    "hype_history_detection": 75,
    "supply_chain_logic": 90,
}


# ---------------------------------------------------------------------------
# Agent 节点函数工厂
# ---------------------------------------------------------------------------

def _build_main_business_match_node(
    deepseek_client: DeepSeekClient,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建 Agent 1: 主营业务匹配分析 节点函数（支持失败重试）"""

    async def _main_business_match_core(state: CredibilityVerificationState) -> dict:
        """Agent 1 核心逻辑：分析股票主营业务与概念的匹配度"""
        stock_code = state["stock_code"]
        concept = state["concept"]

        prompt = (
            f"你是一位资深证券分析师。请分析以下股票的主营业务与概念的匹配度：\n\n"
            f"股票代码：{stock_code}\n"
            f"概念：{concept}\n\n"
            f"请以 JSON 格式返回以下信息：\n"
            f'{{\n'
            f'  "score": 0到100的整数（主营业务与概念的匹配度评分），\n'
            f'  "main_business_description": "该公司的主营业务描述",\n'
            f'  "match_analysis": "主营业务与概念的匹配分析"\n'
            f'}}\n\n'
            f"评分标准：80-100 高度匹配，50-79 部分匹配，0-49 匹配度低。\n"
            f"请确保返回有效的 JSON 格式。"
        )

        messages = [
            ChatMessage(
                role="system",
                content="你是专业的证券分析师，擅长分析上市公司主营业务与热门概念的关联度。请始终以 JSON 格式返回结果。",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        completion = await deepseek_client.chat(messages, temperature=0.3)
        data = _parse_json_response(completion.content)
        score = max(0, min(100, int(data.get("score", 50))))
        return {
            "main_business_score": score,
            "main_business_description": data.get("main_business_description", ""),
            "main_business_analysis": data.get("match_analysis", ""),
            "current_agent": "main_business_match",
            "progress": CREDIBILITY_AGENT_PROGRESS["main_business_match"],
        }

    async def main_business_match_agent(state: CredibilityVerificationState) -> dict:
        """Agent 1: 主营业务匹配分析（带重试）"""
        cb = failure_callback_holder[0] if failure_callback_holder else None
        fallback = {
            "main_business_score": 50,
            "main_business_description": "[分析失败]",
            "main_business_analysis": "[分析失败]",
            "current_agent": "main_business_match",
            "progress": CREDIBILITY_AGENT_PROGRESS["main_business_match"],
        }
        return await execute_agent_with_retry(
            agent_fn=_main_business_match_core,
            state=state,
            agent_name=CREDIBILITY_AGENT_NAMES["main_business_match"],
            fallback_state=fallback,
            retry_config=retry_config,
            progress_callback=cb,
        )

    return main_business_match_agent


def _build_evidence_collection_node(
    deepseek_client: DeepSeekClient,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建 Agent 2: 实质证据收集 节点函数（支持失败重试）"""

    async def _evidence_collection_core(state: CredibilityVerificationState) -> dict:
        """Agent 2 核心逻辑：收集股票与概念相关的实质证据"""
        stock_code = state["stock_code"]
        concept = state["concept"]
        main_business = state.get("main_business_description", "")

        prompt = (
            f"你是一位证据收集专家。请分析以下股票与概念相关的实质证据：\n\n"
            f"股票代码：{stock_code}\n"
            f"概念：{concept}\n"
            f"主营业务：{main_business[:300]}\n\n"
            f"请从以下维度收集证据，以 JSON 格式返回：\n"
            f'{{\n'
            f'  "score": 0到100的整数（证据充分度评分），\n'
            f'  "patents": ["相关专利1", "相关专利2", ...],\n'
            f'  "orders": ["相关订单1", "相关订单2", ...],\n'
            f'  "partnerships": ["合作伙伴1", "合作伙伴2", ...],\n'
            f'  "analysis": "证据分析总结"\n'
            f'}}\n\n'
            f"如果没有找到相关证据，对应列表返回空数组。\n"
            f"请确保返回有效的 JSON 格式。"
        )

        messages = [
            ChatMessage(
                role="system",
                content="你是专业的上市公司证据收集分析师，擅长查找公司与概念相关的专利、订单和合作关系。请始终以 JSON 格式返回结果。",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        completion = await deepseek_client.chat(messages, temperature=0.3)
        data = _parse_json_response(completion.content)
        score = max(0, min(100, int(data.get("score", 50))))
        return {
            "evidence_score": score,
            "evidence_patents": data.get("patents", []),
            "evidence_orders": data.get("orders", []),
            "evidence_partnerships": data.get("partnerships", []),
            "evidence_analysis": data.get("analysis", ""),
            "current_agent": "evidence_collection",
            "progress": CREDIBILITY_AGENT_PROGRESS["evidence_collection"],
        }

    async def evidence_collection_agent(state: CredibilityVerificationState) -> dict:
        """Agent 2: 实质证据收集（带重试）"""
        cb = failure_callback_holder[0] if failure_callback_holder else None
        fallback = {
            "evidence_score": 50,
            "evidence_patents": [],
            "evidence_orders": [],
            "evidence_partnerships": [],
            "evidence_analysis": "[分析失败]",
            "current_agent": "evidence_collection",
            "progress": CREDIBILITY_AGENT_PROGRESS["evidence_collection"],
        }
        return await execute_agent_with_retry(
            agent_fn=_evidence_collection_core,
            state=state,
            agent_name=CREDIBILITY_AGENT_NAMES["evidence_collection"],
            fallback_state=fallback,
            retry_config=retry_config,
            progress_callback=cb,
        )

    return evidence_collection_agent


def _build_hype_history_detection_node(
    deepseek_client: DeepSeekClient,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建 Agent 3: 历史蹭热点检测 节点函数（支持失败重试）"""

    async def _hype_history_detection_core(state: CredibilityVerificationState) -> dict:
        """Agent 3 核心逻辑：检测股票历史上蹭热点的记录"""
        stock_code = state["stock_code"]
        concept = state["concept"]

        prompt = (
            f"你是一位蹭热点检测专家。请分析以下股票的历史蹭热点记录：\n\n"
            f"股票代码：{stock_code}\n"
            f"当前概念：{concept}\n\n"
            f"请以 JSON 格式返回以下信息：\n"
            f'{{\n'
            f'  "score": 0到100的整数（越高越可信，即历史蹭热点越少），\n'
            f'  "past_concepts": ["历史蹭过的概念1", "历史蹭过的概念2", ...],\n'
            f'  "analysis": "蹭热点历史分析"\n'
            f'}}\n\n'
            f"评分标准：80-100 历史记录良好（很少蹭热点），50-79 有一些蹭热点记录，"
            f"0-49 频繁蹭热点。\n"
            f"如果没有蹭热点记录，past_concepts 返回空数组。\n"
            f"请确保返回有效的 JSON 格式。"
        )

        messages = [
            ChatMessage(
                role="system",
                content="你是专业的上市公司蹭热点检测分析师，擅长识别公司是否有频繁蹭热点的历史。请始终以 JSON 格式返回结果。",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        completion = await deepseek_client.chat(messages, temperature=0.3)
        data = _parse_json_response(completion.content)
        score = max(0, min(100, int(data.get("score", 50))))
        return {
            "hype_score": score,
            "hype_past_concepts": data.get("past_concepts", []),
            "hype_analysis": data.get("analysis", ""),
            "current_agent": "hype_history_detection",
            "progress": CREDIBILITY_AGENT_PROGRESS["hype_history_detection"],
        }

    async def hype_history_detection_agent(state: CredibilityVerificationState) -> dict:
        """Agent 3: 历史蹭热点检测（带重试）"""
        cb = failure_callback_holder[0] if failure_callback_holder else None
        fallback = {
            "hype_score": 50,
            "hype_past_concepts": [],
            "hype_analysis": "[分析失败]",
            "current_agent": "hype_history_detection",
            "progress": CREDIBILITY_AGENT_PROGRESS["hype_history_detection"],
        }
        return await execute_agent_with_retry(
            agent_fn=_hype_history_detection_core,
            state=state,
            agent_name=CREDIBILITY_AGENT_NAMES["hype_history_detection"],
            fallback_state=fallback,
            retry_config=retry_config,
            progress_callback=cb,
        )

    return hype_history_detection_agent


def _build_supply_chain_logic_node(
    deepseek_client: DeepSeekClient,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建 Agent 4: 供应链逻辑分析 节点函数（支持失败重试）"""

    async def _supply_chain_logic_core(state: CredibilityVerificationState) -> dict:
        """Agent 4 核心逻辑：分析股票供应链与概念的逻辑合理性"""
        stock_code = state["stock_code"]
        concept = state["concept"]
        main_business = state.get("main_business_description", "")

        prompt = (
            f"你是一位供应链分析专家。请分析以下股票的供应链与概念的逻辑合理性：\n\n"
            f"股票代码：{stock_code}\n"
            f"概念：{concept}\n"
            f"主营业务：{main_business[:300]}\n\n"
            f"请以 JSON 格式返回以下信息：\n"
            f'{{\n'
            f'  "score": 0到100的整数（供应链逻辑合理性评分），\n'
            f'  "upstream": ["上游环节1", "上游环节2", ...],\n'
            f'  "downstream": ["下游环节1", "下游环节2", ...],\n'
            f'  "analysis": "供应链逻辑分析"\n'
            f'}}\n\n'
            f"评分标准：80-100 供应链逻辑高度合理，50-79 部分合理，0-49 逻辑不合理。\n"
            f"请确保返回有效的 JSON 格式。"
        )

        messages = [
            ChatMessage(
                role="system",
                content="你是专业的供应链分析师，擅长分析上市公司供应链与概念的逻辑关联性。请始终以 JSON 格式返回结果。",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        completion = await deepseek_client.chat(messages, temperature=0.3)
        data = _parse_json_response(completion.content)
        score = max(0, min(100, int(data.get("score", 50))))
        return {
            "supply_chain_score": score,
            "supply_chain_upstream": data.get("upstream", []),
            "supply_chain_downstream": data.get("downstream", []),
            "supply_chain_analysis": data.get("analysis", ""),
            "current_agent": "supply_chain_logic",
            "progress": CREDIBILITY_AGENT_PROGRESS["supply_chain_logic"],
        }

    async def supply_chain_logic_agent(state: CredibilityVerificationState) -> dict:
        """Agent 4: 供应链逻辑分析（带重试）"""
        cb = failure_callback_holder[0] if failure_callback_holder else None
        fallback = {
            "supply_chain_score": 50,
            "supply_chain_upstream": [],
            "supply_chain_downstream": [],
            "supply_chain_analysis": "[分析失败]",
            "current_agent": "supply_chain_logic",
            "progress": CREDIBILITY_AGENT_PROGRESS["supply_chain_logic"],
        }
        return await execute_agent_with_retry(
            agent_fn=_supply_chain_logic_core,
            state=state,
            agent_name=CREDIBILITY_AGENT_NAMES["supply_chain_logic"],
            fallback_state=fallback,
            retry_config=retry_config,
            progress_callback=cb,
        )

    return supply_chain_logic_agent


# ---------------------------------------------------------------------------
# 结果聚合节点
# ---------------------------------------------------------------------------

def _build_credibility_aggregate_node():
    """构建结果聚合节点"""

    async def aggregate_credibility_results(state: CredibilityVerificationState) -> dict:
        """聚合所有 Agent 输出，不做额外 LLM 调用"""
        return {
            "progress": 100,
            "current_agent": "aggregate_results",
        }

    return aggregate_credibility_results


# ---------------------------------------------------------------------------
# 工作流构建函数
# ---------------------------------------------------------------------------

def build_credibility_verification_workflow(
    deepseek_client: DeepSeekClient,
    checkpointer=None,
    retry_config: Optional[AgentRetryConfig] = None,
    failure_callback_holder: Optional[List] = None,
):
    """构建概念可信度验证 LangGraph 工作流

    Args:
        deepseek_client: DeepSeek LLM 客户端
        checkpointer: LangGraph checkpointer（Redis 或 Memory），
                      为 None 时不使用 checkpointer
        retry_config: Agent 重试配置，为 None 时使用默认配置
        failure_callback_holder: 可变列表 [callback]，用于在运行时注入失败回调

    Returns:
        编译后的 LangGraph 工作流（CompiledGraph）
    """
    workflow = StateGraph(CredibilityVerificationState)

    # 添加 Agent 节点（每个节点支持失败重试）
    workflow.add_node(
        "main_business_match",
        _build_main_business_match_node(deepseek_client, retry_config, failure_callback_holder),
    )
    workflow.add_node(
        "evidence_collection",
        _build_evidence_collection_node(deepseek_client, retry_config, failure_callback_holder),
    )
    workflow.add_node(
        "hype_history_detection",
        _build_hype_history_detection_node(deepseek_client, retry_config, failure_callback_holder),
    )
    workflow.add_node(
        "supply_chain_logic",
        _build_supply_chain_logic_node(deepseek_client, retry_config, failure_callback_holder),
    )
    workflow.add_node(
        "aggregate_results",
        _build_credibility_aggregate_node(),
    )

    # 配置顺序执行边
    workflow.add_edge(START, "main_business_match")
    workflow.add_edge("main_business_match", "evidence_collection")
    workflow.add_edge("evidence_collection", "hype_history_detection")
    workflow.add_edge("hype_history_detection", "supply_chain_logic")
    workflow.add_edge("supply_chain_logic", "aggregate_results")
    workflow.add_edge("aggregate_results", END)

    # 编译工作流
    compile_kwargs = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer

    return workflow.compile(**compile_kwargs)


# ---------------------------------------------------------------------------
# 风险标签推断辅助函数
# ---------------------------------------------------------------------------

def _infer_risk_labels(
    main_business_score: int,
    evidence_score: int,
    hype_score: int,
    supply_chain_score: int,
    hype_past_concepts: list,
) -> List[RiskLabel]:
    """根据各维度评分推断风险标签

    Args:
        main_business_score: 主营业务匹配度评分
        evidence_score: 证据充分度评分
        hype_score: 蹭热点评分（越高越可信）
        supply_chain_score: 供应链逻辑评分
        hype_past_concepts: 历史蹭过的概念列表

    Returns:
        风险标签列表
    """
    labels: List[RiskLabel] = []

    # 主营业务不匹配
    if main_business_score < 30:
        labels.append(RiskLabel.BUSINESS_MISMATCH)

    # 证据不足
    if evidence_score < 30:
        labels.append(RiskLabel.WEAK_EVIDENCE)

    # 纯蹭热点：主营业务不匹配 + 证据不足 + 蹭热点历史差
    if main_business_score < 30 and evidence_score < 30 and hype_score < 50:
        labels.append(RiskLabel.PURE_HYPE)

    # 频繁概念切换
    if len(hype_past_concepts) >= 3 or hype_score < 30:
        labels.append(RiskLabel.FREQUENT_CONCEPT_CHANGE)

    # 供应链风险
    if supply_chain_score < 30:
        labels.append(RiskLabel.SUPPLY_CHAIN_RISK)

    return labels


# ---------------------------------------------------------------------------
# ICredibilityVerificationService 实现
# ---------------------------------------------------------------------------

class CredibilityVerificationWorkflowService(ICredibilityVerificationService):
    """概念可信度验证服务实现

    使用 LangGraph 4-Agent 工作流实现 ICredibilityVerificationService 接口。
    工作流按顺序执行 4 个 Agent（主营业务匹配、证据收集、蹭热点检测、供应链逻辑），
    每个 Agent 完成后通过回调更新进度，最终聚合为 CredibilityReport。
    Agent 节点支持失败重试机制，所有重试耗尽后返回降级值并记录 FAILED AgentStep。

    Requirements: 6.3, 6.6, 6.7, 10.3
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
        self._failure_callback_holder: List = [None]
        self._compiled_workflow = build_credibility_verification_workflow(
            deepseek_client=deepseek_client,
            checkpointer=checkpointer,
            retry_config=retry_config,
            failure_callback_holder=self._failure_callback_holder,
        )

    async def verify_credibility(
        self,
        stock_code: StockCode,
        concept: str,
        progress_callback=None,
    ) -> CredibilityReport:
        """执行概念可信度验证工作流

        按顺序执行 4 个 Agent，每个 Agent 完成后通过 progress_callback 更新进度。
        最终将所有 Agent 输出聚合为 CredibilityReport 值对象。

        Args:
            stock_code: 股票代码值对象
            concept: 被验证的概念（如"固态电池"）
            progress_callback: 进度回调函数
                签名: (progress: int, agent_step: AgentStep) -> None

        Returns:
            CredibilityReport 值对象

        Raises:
            LLMServiceError: LLM 调用失败
        """
        # 初始化工作流状态
        initial_state: CredibilityVerificationState = {
            "stock_code": stock_code.code,
            "concept": concept,
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

        # 设置失败回调：当 Agent 重试耗尽时，通过此回调报告 FAILED AgentStep
        failed_steps: List[AgentStep] = []

        def _on_agent_failure(agent_step: AgentStep):
            """Agent 重试耗尽后的失败回调"""
            failed_steps.append(agent_step)
            if progress_callback is not None:
                progress_value = CREDIBILITY_AGENT_PROGRESS.get(
                    next(
                        (k for k, v in CREDIBILITY_AGENT_NAMES.items() if v == agent_step.agent_name),
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
            import uuid
            config["configurable"] = {"thread_id": str(uuid.uuid4())}

        # 执行工作流，逐步收集状态更新
        last_agent = ""
        final_state = initial_state.copy()

        try:
            async for event in self._compiled_workflow.astream(
                initial_state, config=config
            ):
                for node_name, state_update in event.items():
                    if isinstance(state_update, dict):
                        final_state.update(state_update)

                    current_agent = final_state.get("current_agent", "")
                    if current_agent and current_agent != last_agent:
                        last_agent = current_agent
                        if progress_callback is not None:
                            agent_display_name = CREDIBILITY_AGENT_NAMES.get(
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
            logger.error("可信度验证工作流执行失败: %s", str(e))
            raise LLMServiceError(f"可信度验证工作流执行失败: {str(e)}") from e

        # 将最终状态转换为 CredibilityReport 值对象
        return self._build_credibility_report(stock_code, concept, final_state)

    def _build_credibility_report(
        self,
        stock_code: StockCode,
        concept: str,
        state: dict,
    ) -> CredibilityReport:
        """将工作流最终状态转换为 CredibilityReport 值对象

        Args:
            stock_code: 股票代码值对象
            concept: 被验证的概念
            state: 工作流最终状态

        Returns:
            CredibilityReport 值对象
        """
        # 提取各维度评分
        main_business_score = max(0, min(100, int(state.get("main_business_score", 50))))
        evidence_score = max(0, min(100, int(state.get("evidence_score", 50))))
        hype_score = max(0, min(100, int(state.get("hype_score", 50))))
        supply_chain_score = max(0, min(100, int(state.get("supply_chain_score", 50))))

        # 计算总体评分（四个维度加权平均）
        overall_score_value = int(
            main_business_score * 0.3
            + evidence_score * 0.25
            + hype_score * 0.2
            + supply_chain_score * 0.25
        )
        overall_score_value = max(0, min(100, overall_score_value))

        # 构建子值对象
        main_business_match = MainBusinessMatch(
            score=main_business_score,
            main_business_description=state.get("main_business_description", ""),
            match_analysis=state.get("main_business_analysis", ""),
        )

        evidence = EvidenceAnalysis(
            score=evidence_score,
            patents=state.get("evidence_patents", []),
            orders=state.get("evidence_orders", []),
            partnerships=state.get("evidence_partnerships", []),
            analysis=state.get("evidence_analysis", ""),
        )

        hype_history = HypeHistory(
            score=hype_score,
            past_concepts=state.get("hype_past_concepts", []),
            analysis=state.get("hype_analysis", ""),
        )

        supply_chain = SupplyChainLogic(
            score=supply_chain_score,
            upstream=state.get("supply_chain_upstream", []),
            downstream=state.get("supply_chain_downstream", []),
            analysis=state.get("supply_chain_analysis", ""),
        )

        # 推断风险标签
        risk_labels = _infer_risk_labels(
            main_business_score=main_business_score,
            evidence_score=evidence_score,
            hype_score=hype_score,
            supply_chain_score=supply_chain_score,
            hype_past_concepts=state.get("hype_past_concepts", []),
        )

        # 生成结论
        overall_score = CredibilityScore(overall_score_value)
        conclusion = self._generate_conclusion(
            stock_code=stock_code,
            concept=concept,
            overall_score=overall_score,
            risk_labels=risk_labels,
        )

        # 从股票代码推断股票名称（简化处理，使用代码作为名称）
        stock_name = stock_code.code

        return CredibilityReport(
            stock_code=stock_code,
            stock_name=stock_name,
            concept=concept,
            overall_score=overall_score,
            main_business_match=main_business_match,
            evidence=evidence,
            hype_history=hype_history,
            supply_chain_logic=supply_chain,
            risk_labels=risk_labels,
            conclusion=conclusion,
        )

    def _generate_conclusion(
        self,
        stock_code: StockCode,
        concept: str,
        overall_score: CredibilityScore,
        risk_labels: List[RiskLabel],
    ) -> str:
        """生成可信度验证结论文本

        Args:
            stock_code: 股票代码
            concept: 被验证的概念
            overall_score: 总体可信度评分
            risk_labels: 风险标签列表

        Returns:
            结论文本
        """
        level = overall_score.level
        score = overall_score.score

        if not risk_labels:
            return (
                f"股票 {stock_code.code} 与概念「{concept}」的可信度评分为 {score} 分"
                f"（{level}），未发现明显风险。"
            )

        risk_descriptions = {
            RiskLabel.PURE_HYPE: "纯蹭热点",
            RiskLabel.WEAK_EVIDENCE: "证据不足",
            RiskLabel.BUSINESS_MISMATCH: "主业不匹配",
            RiskLabel.HIGH_DEBT: "高负债风险",
            RiskLabel.FREQUENT_CONCEPT_CHANGE: "频繁概念切换",
            RiskLabel.SUPPLY_CHAIN_RISK: "供应链风险",
        }

        risk_text = "、".join(
            risk_descriptions.get(r, r.value) for r in risk_labels
        )

        return (
            f"股票 {stock_code.code} 与概念「{concept}」的可信度评分为 {score} 分"
            f"（{level}），存在以下风险：{risk_text}。"
        )
