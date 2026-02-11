"""Agent 失败重试机制单元测试

测试 agent_retry 模块的核心功能：
- execute_agent_with_retry 的重试逻辑
- 重试耗尽后返回 fallback 值
- FAILED AgentStep 通过回调报告
- AgentRetryConfig 配置
- 与工作流服务的集成（确保重试后 FAILED AgentStep 通过 progress_callback 传递）

Requirements: 6.6, 10.3
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from contexts.intelligence.domain.enums.enums import AgentStepStatus
from contexts.intelligence.domain.exceptions import LLMServiceError
from contexts.intelligence.domain.value_objects.agent_step import AgentStep
from contexts.intelligence.infrastructure.ai.agent_retry import (
    AgentRetryConfig,
    DEFAULT_RETRY_CONFIG,
    _calculate_delay,
    execute_agent_with_retry,
)
from contexts.intelligence.infrastructure.ai.deepseek_client import (
    ChatCompletion,
    DeepSeekClient,
    DeepSeekConfig,
)
from contexts.intelligence.infrastructure.ai.industry_research_workflow import (
    IndustryResearchWorkflowService,
)
from contexts.intelligence.infrastructure.ai.credibility_workflow import (
    CredibilityVerificationWorkflowService,
)
from contexts.intelligence.domain.value_objects.industry_insight import (
    IndustryInsight,
)
from contexts.intelligence.domain.value_objects.credibility_report import (
    CredibilityReport,
)
from shared_kernel.value_objects.stock_code import StockCode


# ============================================================
# AgentRetryConfig Tests
# ============================================================


class TestAgentRetryConfig:
    """AgentRetryConfig 配置测试"""

    def test_default_config_values(self):
        """测试默认配置值"""
        config = AgentRetryConfig()
        assert config.max_retries == 2
        assert config.retry_delay == 1.0
        assert config.retry_backoff_factor == 2.0
        assert config.retry_max_delay == 10.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = AgentRetryConfig(
            max_retries=5,
            retry_delay=0.5,
            retry_backoff_factor=3.0,
            retry_max_delay=30.0,
        )
        assert config.max_retries == 5
        assert config.retry_delay == 0.5
        assert config.retry_backoff_factor == 3.0
        assert config.retry_max_delay == 30.0

    def test_zero_retries_config(self):
        """测试零重试配置（禁用重试）"""
        config = AgentRetryConfig(max_retries=0)
        assert config.max_retries == 0

    def test_config_is_frozen(self):
        """测试配置不可变"""
        config = AgentRetryConfig()
        with pytest.raises(AttributeError):
            config.max_retries = 10


# ============================================================
# _calculate_delay Tests
# ============================================================


class TestCalculateDelay:
    """延迟计算测试"""

    def test_first_retry_delay(self):
        """测试第一次重试延迟"""
        config = AgentRetryConfig(retry_delay=1.0, retry_backoff_factor=2.0)
        assert _calculate_delay(config, 0) == 1.0

    def test_second_retry_delay(self):
        """测试第二次重试延迟（指数退避）"""
        config = AgentRetryConfig(retry_delay=1.0, retry_backoff_factor=2.0)
        assert _calculate_delay(config, 1) == 2.0

    def test_third_retry_delay(self):
        """测试第三次重试延迟"""
        config = AgentRetryConfig(retry_delay=1.0, retry_backoff_factor=2.0)
        assert _calculate_delay(config, 2) == 4.0

    def test_delay_capped_at_max(self):
        """测试延迟不超过最大值"""
        config = AgentRetryConfig(
            retry_delay=1.0, retry_backoff_factor=2.0, retry_max_delay=3.0
        )
        assert _calculate_delay(config, 5) == 3.0


# ============================================================
# execute_agent_with_retry Tests
# ============================================================


class TestExecuteAgentWithRetry:
    """execute_agent_with_retry 核心逻辑测试"""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """测试首次执行成功，不触发重试"""
        call_count = 0

        async def agent_fn(state):
            nonlocal call_count
            call_count += 1
            return {"result": "success", "current_agent": "test"}

        result = await execute_agent_with_retry(
            agent_fn=agent_fn,
            state={"query": "test"},
            agent_name="测试Agent",
            fallback_state={"result": "fallback"},
            retry_config=AgentRetryConfig(max_retries=2, retry_delay=0.01),
        )

        assert result == {"result": "success", "current_agent": "test"}
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """测试首次失败后重试成功"""
        call_count = 0

        async def agent_fn(state):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise LLMServiceError("临时错误")
            return {"result": "success"}

        result = await execute_agent_with_retry(
            agent_fn=agent_fn,
            state={"query": "test"},
            agent_name="测试Agent",
            fallback_state={"result": "fallback"},
            retry_config=AgentRetryConfig(max_retries=2, retry_delay=0.01),
        )

        assert result == {"result": "success"}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_returns_fallback(self):
        """测试所有重试耗尽后返回 fallback 值"""
        call_count = 0

        async def agent_fn(state):
            nonlocal call_count
            call_count += 1
            raise LLMServiceError("持续错误")

        fallback = {"result": "fallback", "current_agent": "test"}
        result = await execute_agent_with_retry(
            agent_fn=agent_fn,
            state={"query": "test"},
            agent_name="测试Agent",
            fallback_state=fallback,
            retry_config=AgentRetryConfig(max_retries=2, retry_delay=0.01),
        )

        assert result == fallback
        assert call_count == 3  # 1 initial + 2 retries

    @pytest.mark.asyncio
    async def test_zero_retries_fails_immediately(self):
        """测试零重试配置下立即返回 fallback"""
        call_count = 0

        async def agent_fn(state):
            nonlocal call_count
            call_count += 1
            raise LLMServiceError("错误")

        result = await execute_agent_with_retry(
            agent_fn=agent_fn,
            state={"query": "test"},
            agent_name="测试Agent",
            fallback_state={"result": "fallback"},
            retry_config=AgentRetryConfig(max_retries=0, retry_delay=0.01),
        )

        assert result == {"result": "fallback"}
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_failure_callback_called_on_exhaustion(self):
        """测试重试耗尽后调用失败回调，报告 FAILED AgentStep"""
        reported_steps = []

        def on_failure(agent_step: AgentStep):
            reported_steps.append(agent_step)

        async def agent_fn(state):
            raise LLMServiceError("API 调用失败")

        await execute_agent_with_retry(
            agent_fn=agent_fn,
            state={"query": "test"},
            agent_name="行业背景速览",
            fallback_state={"result": "fallback"},
            retry_config=AgentRetryConfig(max_retries=1, retry_delay=0.01),
            progress_callback=on_failure,
        )

        assert len(reported_steps) == 1
        step = reported_steps[0]
        assert step.agent_name == "行业背景速览"
        assert step.status == AgentStepStatus.FAILED
        assert step.error_message is not None
        assert "API 调用失败" in step.error_message
        assert step.started_at is not None
        assert step.completed_at is not None

    @pytest.mark.asyncio
    async def test_failure_callback_not_called_on_success(self):
        """测试成功时不调用失败回调"""
        reported_steps = []

        def on_failure(agent_step: AgentStep):
            reported_steps.append(agent_step)

        async def agent_fn(state):
            return {"result": "success"}

        await execute_agent_with_retry(
            agent_fn=agent_fn,
            state={"query": "test"},
            agent_name="测试Agent",
            fallback_state={"result": "fallback"},
            retry_config=AgentRetryConfig(max_retries=2, retry_delay=0.01),
            progress_callback=on_failure,
        )

        assert len(reported_steps) == 0

    @pytest.mark.asyncio
    async def test_no_callback_does_not_error(self):
        """测试不传入回调时不报错"""
        async def agent_fn(state):
            raise LLMServiceError("错误")

        result = await execute_agent_with_retry(
            agent_fn=agent_fn,
            state={"query": "test"},
            agent_name="测试Agent",
            fallback_state={"result": "fallback"},
            retry_config=AgentRetryConfig(max_retries=0, retry_delay=0.01),
            progress_callback=None,
        )

        assert result == {"result": "fallback"}

    @pytest.mark.asyncio
    async def test_uses_default_config_when_none(self):
        """测试 retry_config 为 None 时使用默认配置"""
        call_count = 0

        async def agent_fn(state):
            nonlocal call_count
            call_count += 1
            if call_count <= DEFAULT_RETRY_CONFIG.max_retries:
                raise LLMServiceError("错误")
            return {"result": "success"}

        # With default config (max_retries=2), should succeed on 3rd attempt
        # But this would be slow due to default delays, so we just verify it works
        # by using a fast-failing scenario
        call_count = 0

        async def always_fail(state):
            nonlocal call_count
            call_count += 1
            raise LLMServiceError("错误")

        # Override asyncio.sleep to avoid actual delays in test
        original_sleep = asyncio.sleep

        async def fast_sleep(delay):
            await original_sleep(0)

        asyncio.sleep = fast_sleep
        try:
            result = await execute_agent_with_retry(
                agent_fn=always_fail,
                state={"query": "test"},
                agent_name="测试Agent",
                fallback_state={"result": "fallback"},
                retry_config=None,  # Uses DEFAULT_RETRY_CONFIG
            )
            assert result == {"result": "fallback"}
            assert call_count == DEFAULT_RETRY_CONFIG.max_retries + 1
        finally:
            asyncio.sleep = original_sleep


# ============================================================
# Integration: Retry with IndustryResearchWorkflowService
# ============================================================


def _make_failing_then_success_client(fail_count: int, responses: list[str]):
    """Create a mock client that fails `fail_count` times then succeeds."""
    config = DeepSeekConfig(
        api_key="test-key",
        base_url="https://api.test.com/v1",
        timeout=10.0,
        max_retries=0,
    )
    client = DeepSeekClient(config)

    call_count = 0
    agent_call_count = 0

    async def mock_chat(messages, **kwargs):
        nonlocal call_count, agent_call_count
        call_count += 1
        # Each agent calls chat once; fail_count applies per-agent
        agent_call_count += 1
        if agent_call_count <= fail_count:
            raise LLMServiceError("临时 API 错误")
        # After failures, reset for next agent
        idx = min(call_count - fail_count - 1, len(responses) - 1)
        idx = max(0, idx)
        return ChatCompletion(
            content=responses[idx],
            model="deepseek-chat",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
        )

    client.chat = mock_chat
    return client


def _make_always_failing_client():
    """Create a mock client that always fails."""
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
    return client


class TestRetryWithIndustryResearchService:
    """重试机制与 IndustryResearchWorkflowService 集成测试"""

    @pytest.mark.asyncio
    async def test_retry_reports_failed_agent_step_via_callback(self):
        """测试重试耗尽后通过 progress_callback 报告 FAILED AgentStep"""
        client = _make_always_failing_client()
        # Use zero retries for speed
        retry_config = AgentRetryConfig(max_retries=0, retry_delay=0.01)
        service = IndustryResearchWorkflowService(
            deepseek_client=client,
            retry_config=retry_config,
        )

        progress_updates = []

        def on_progress(progress: int, agent_step: AgentStep):
            progress_updates.append((progress, agent_step))

        result = await service.execute_research("测试行业", progress_callback=on_progress)

        assert isinstance(result, IndustryInsight)
        # Should have FAILED steps reported
        failed_steps = [
            (p, s) for p, s in progress_updates if s.status == AgentStepStatus.FAILED
        ]
        assert len(failed_steps) > 0
        # Each failed step should have error_message
        for _, step in failed_steps:
            assert step.error_message is not None
            assert "API 调用失败" in step.error_message

    @pytest.mark.asyncio
    async def test_retry_with_zero_retries_still_produces_result(self):
        """测试零重试配置下仍然产生结果（使用 fallback 值）"""
        client = _make_always_failing_client()
        retry_config = AgentRetryConfig(max_retries=0, retry_delay=0.01)
        service = IndustryResearchWorkflowService(
            deepseek_client=client,
            retry_config=retry_config,
        )

        result = await service.execute_research("测试行业")

        assert isinstance(result, IndustryInsight)
        assert "[分析失败" in result.summary


class TestRetryWithCredibilityVerificationService:
    """重试机制与 CredibilityVerificationWorkflowService 集成测试"""

    @pytest.mark.asyncio
    async def test_retry_reports_failed_agent_step_via_callback(self):
        """测试重试耗尽后通过 progress_callback 报告 FAILED AgentStep"""
        client = _make_always_failing_client()
        retry_config = AgentRetryConfig(max_retries=0, retry_delay=0.01)
        service = CredibilityVerificationWorkflowService(
            deepseek_client=client,
            retry_config=retry_config,
        )

        progress_updates = []

        def on_progress(progress: int, agent_step: AgentStep):
            progress_updates.append((progress, agent_step))

        stock_code = StockCode("600519.SH")
        result = await service.verify_credibility(
            stock_code, "AI+白酒", progress_callback=on_progress
        )

        assert isinstance(result, CredibilityReport)
        # Should have FAILED steps reported
        failed_steps = [
            (p, s) for p, s in progress_updates if s.status == AgentStepStatus.FAILED
        ]
        assert len(failed_steps) > 0
        for _, step in failed_steps:
            assert step.error_message is not None

    @pytest.mark.asyncio
    async def test_retry_with_zero_retries_still_produces_report(self):
        """测试零重试配置下仍然产生报告（使用 fallback 值）"""
        client = _make_always_failing_client()
        retry_config = AgentRetryConfig(max_retries=0, retry_delay=0.01)
        service = CredibilityVerificationWorkflowService(
            deepseek_client=client,
            retry_config=retry_config,
        )

        stock_code = StockCode("600519.SH")
        result = await service.verify_credibility(stock_code, "AI+白酒")

        assert isinstance(result, CredibilityReport)
        assert "[分析失败" in result.main_business_match.main_business_description
