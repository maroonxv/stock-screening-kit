"""Agent 失败重试机制

提供 Agent 节点级别的重试装饰器，用于 LangGraph 工作流中的 Agent 节点函数。
当 Agent 执行失败时，按配置的重试次数和延迟进行重试。
所有重试耗尽后，返回 fallback 值并记录 FAILED 状态的 AgentStep。

这与 DeepSeekClient 中的 HTTP 级别重试不同：
- DeepSeekClient 重试：针对单次 HTTP 请求的网络/服务端错误
- Agent 重试：针对整个 Agent 节点的执行失败（包括 JSON 解析失败、数据处理错误等）

Requirements: 6.6, 10.3
"""

import asyncio
import functools
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from src.backend.contexts.intelligence.domain.enums.enums import AgentStepStatus
from src.backend.contexts.intelligence.domain.value_objects.agent_step import AgentStep

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentRetryConfig:
    """Agent 重试配置

    Attributes:
        max_retries: 最大重试次数（不含首次执行）。默认 2 次。
        retry_delay: 重试间隔基础延迟（秒）。默认 1.0 秒。
        retry_backoff_factor: 退避因子，每次重试延迟乘以此因子。默认 2.0。
        retry_max_delay: 最大重试延迟（秒）。默认 10.0 秒。
    """

    max_retries: int = 2
    retry_delay: float = 1.0
    retry_backoff_factor: float = 2.0
    retry_max_delay: float = 10.0


# 默认重试配置
DEFAULT_RETRY_CONFIG = AgentRetryConfig()


def _calculate_delay(config: AgentRetryConfig, attempt: int) -> float:
    """计算第 attempt 次重试的延迟时间

    Args:
        config: 重试配置
        attempt: 重试次数（从 0 开始）

    Returns:
        延迟秒数
    """
    delay = config.retry_delay * (config.retry_backoff_factor ** attempt)
    return min(delay, config.retry_max_delay)


async def execute_agent_with_retry(
    agent_fn: Callable,
    state: Dict[str, Any],
    *,
    agent_name: str,
    fallback_state: Dict[str, Any],
    retry_config: Optional[AgentRetryConfig] = None,
    progress_callback: Optional[Callable] = None,
) -> Dict[str, Any]:
    """执行 Agent 节点函数，支持失败重试

    当 Agent 执行失败时，按配置进行重试。所有重试耗尽后：
    1. 返回 fallback_state（降级值）
    2. 如果提供了 progress_callback，通过回调报告 FAILED 状态的 AgentStep

    Args:
        agent_fn: Agent 节点的异步函数，签名为 (state) -> dict
        state: 当前工作流状态
        agent_name: Agent 显示名称（中文），用于日志和 AgentStep
        fallback_state: 所有重试耗尽后的降级返回值
        retry_config: 重试配置，为 None 时使用默认配置
        progress_callback: 可选的进度回调函数，签名为 (AgentStep) -> None
            用于在重试耗尽后报告 FAILED 状态

    Returns:
        Agent 执行结果字典，或 fallback_state
    """
    config = retry_config or DEFAULT_RETRY_CONFIG
    last_error: Optional[Exception] = None
    started_at = datetime.now(timezone.utc)

    for attempt in range(config.max_retries + 1):
        try:
            result = await agent_fn(state)
            return result
        except Exception as e:
            last_error = e
            if attempt < config.max_retries:
                delay = _calculate_delay(config, attempt)
                logger.warning(
                    "%s Agent 执行失败（第 %d/%d 次重试），等待 %.1f 秒: %s",
                    agent_name,
                    attempt + 1,
                    config.max_retries,
                    delay,
                    str(e),
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "%s Agent 执行失败（已耗尽 %d 次重试）: %s",
                    agent_name,
                    config.max_retries,
                    str(e),
                )

    # 所有重试耗尽，记录 FAILED AgentStep
    completed_at = datetime.now(timezone.utc)
    error_message = str(last_error) if last_error else "未知错误"

    if progress_callback is not None:
        failed_step = AgentStep(
            agent_name=agent_name,
            status=AgentStepStatus.FAILED,
            started_at=started_at,
            completed_at=completed_at,
            output_summary=None,
            error_message=f"重试 {config.max_retries} 次后仍失败: {error_message}",
        )
        try:
            progress_callback(failed_step)
        except Exception as cb_err:
            logger.warning("FAILED AgentStep 回调执行失败: %s", str(cb_err))

    return fallback_state


def with_agent_retry(
    *,
    agent_name: str,
    fallback_state_factory: Callable[[], Dict[str, Any]],
    retry_config: Optional[AgentRetryConfig] = None,
):
    """Agent 节点重试装饰器

    将一个 Agent 节点函数包装为支持重试的版本。
    装饰后的函数在执行失败时自动重试，所有重试耗尽后返回 fallback 值。

    注意：此装饰器用于 LangGraph 节点函数，节点函数签名为 (state) -> dict。
    装饰后的函数会在 state 中查找 '_retry_config' 和 '_failure_callback' 键
    以支持运行时配置。

    Args:
        agent_name: Agent 显示名称
        fallback_state_factory: 生成降级返回值的工厂函数
        retry_config: 重试配置，为 None 时使用默认配置

    Returns:
        装饰器函数

    Example:
        @with_agent_retry(
            agent_name="行业背景速览",
            fallback_state_factory=lambda: {"industry_summary": "[分析失败]", ...},
        )
        async def industry_overview_agent(state):
            ...
    """

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            # 允许通过 state 传入运行时配置（可选）
            config = retry_config or DEFAULT_RETRY_CONFIG
            failure_callback = state.get("_failure_callback")

            return await execute_agent_with_retry(
                agent_fn=fn,
                state=state,
                agent_name=agent_name,
                fallback_state=fallback_state_factory(),
                retry_config=config,
                progress_callback=failure_callback,
            )

        return wrapper

    return decorator
