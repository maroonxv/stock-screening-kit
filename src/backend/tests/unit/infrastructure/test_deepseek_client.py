"""DeepSeek LLM 客户端单元测试

测试超时控制、重试机制、错误处理和配置管理。
Requirements: 6.4, 10.5
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from contexts.intelligence.domain.exceptions import LLMServiceError
from contexts.intelligence.infrastructure.ai.deepseek_client import (
    ChatCompletion,
    ChatMessage,
    DeepSeekClient,
    DeepSeekConfig,
)


# ============================================================
# DeepSeekConfig Tests
# ============================================================


class TestDeepSeekConfig:
    """DeepSeek 配置测试"""

    def test_default_config(self):
        """测试默认配置值"""
        config = DeepSeekConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.deepseek.com/v1"
        assert config.model == "deepseek-chat"
        assert config.timeout == 60.0
        assert config.max_retries == 3
        assert config.retry_base_delay == 1.0
        assert config.retry_max_delay == 30.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = DeepSeekConfig(
            api_key="custom-key",
            base_url="https://custom.api.com/v1",
            model="deepseek-coder",
            timeout=120.0,
            max_retries=5,
        )
        assert config.api_key == "custom-key"
        assert config.base_url == "https://custom.api.com/v1"
        assert config.model == "deepseek-coder"
        assert config.timeout == 120.0
        assert config.max_retries == 5

    def test_from_env_success(self):
        """测试从环境变量创建配置"""
        env_vars = {
            "DEEPSEEK_API_KEY": "env-key",
            "DEEPSEEK_BASE_URL": "https://env.api.com/v1",
            "DEEPSEEK_MODEL": "deepseek-v2",
            "DEEPSEEK_TIMEOUT": "90",
            "DEEPSEEK_MAX_RETRIES": "5",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            config = DeepSeekConfig.from_env()
            assert config.api_key == "env-key"
            assert config.base_url == "https://env.api.com/v1"
            assert config.model == "deepseek-v2"
            assert config.timeout == 90.0
            assert config.max_retries == 5

    def test_from_env_defaults(self):
        """测试环境变量缺失时使用默认值"""
        env_vars = {"DEEPSEEK_API_KEY": "env-key"}
        with patch.dict(os.environ, env_vars, clear=False):
            # Remove other env vars if they exist
            for key in ["DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL", "DEEPSEEK_TIMEOUT", "DEEPSEEK_MAX_RETRIES"]:
                os.environ.pop(key, None)
            config = DeepSeekConfig.from_env()
            assert config.api_key == "env-key"
            assert config.base_url == "https://api.deepseek.com/v1"
            assert config.model == "deepseek-chat"
            assert config.timeout == 60.0
            assert config.max_retries == 3

    def test_from_env_missing_api_key(self):
        """测试缺少 API 密钥时抛出 LLMServiceError"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DEEPSEEK_API_KEY", None)
            with pytest.raises(LLMServiceError, match="DEEPSEEK_API_KEY"):
                DeepSeekConfig.from_env()

    def test_config_is_frozen(self):
        """测试配置不可变"""
        config = DeepSeekConfig(api_key="test-key")
        with pytest.raises(AttributeError):
            config.api_key = "new-key"


# ============================================================
# DeepSeekClient Tests
# ============================================================


def _make_success_response() -> dict:
    """创建成功的 API 响应数据"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "model": "deepseek-chat",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }


def _make_config(**overrides) -> DeepSeekConfig:
    """创建测试配置"""
    defaults = {
        "api_key": "test-key",
        "base_url": "https://api.test.com/v1",
        "timeout": 10.0,
        "max_retries": 2,
        "retry_base_delay": 0.01,  # 测试中使用极短延迟
        "retry_max_delay": 0.1,
    }
    defaults.update(overrides)
    return DeepSeekConfig(**defaults)


class TestDeepSeekClientChat:
    """DeepSeek 客户端聊天补全测试"""

    @pytest.mark.asyncio
    async def test_chat_success(self):
        """测试成功的聊天补全请求"""
        config = _make_config()
        client = DeepSeekClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _make_success_response()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            result = await client.chat(messages)

            assert isinstance(result, ChatCompletion)
            assert result.content == "Hello!"
            assert result.model == "deepseek-chat"
            assert result.usage["total_tokens"] == 15
            assert result.finish_reason == "stop"

            # 验证请求参数
            mock_http_client.post.assert_called_once()
            call_args = mock_http_client.post.call_args
            assert call_args[0][0] == "/chat/completions"
            payload = call_args[1]["json"]
            assert payload["model"] == "deepseek-chat"
            assert payload["messages"] == [{"role": "user", "content": "Hi"}]

    @pytest.mark.asyncio
    async def test_chat_custom_parameters(self):
        """测试自定义温度和 max_tokens 参数"""
        config = _make_config()
        client = DeepSeekClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _make_success_response()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            await client.chat(messages, temperature=0.3, max_tokens=2048, model="deepseek-v2")

            payload = mock_http_client.post.call_args[1]["json"]
            assert payload["temperature"] == 0.3
            assert payload["max_tokens"] == 2048
            assert payload["model"] == "deepseek-v2"

    @pytest.mark.asyncio
    async def test_chat_timeout_with_retry(self):
        """测试超时后重试机制"""
        config = _make_config(max_retries=2)
        client = DeepSeekClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _make_success_response()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            # 前两次超时，第三次成功
            mock_http_client.post.side_effect = [
                httpx.TimeoutException("timeout"),
                httpx.TimeoutException("timeout"),
                mock_response,
            ]
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            result = await client.chat(messages)

            assert result.content == "Hello!"
            assert mock_http_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_chat_timeout_exhausted(self):
        """测试超时重试耗尽后抛出 LLMServiceError"""
        config = _make_config(max_retries=1)
        client = DeepSeekClient(config)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.side_effect = httpx.TimeoutException("timeout")
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            with pytest.raises(LLMServiceError, match="超时"):
                await client.chat(messages)

            # 1 initial + 1 retry = 2 calls
            assert mock_http_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_chat_retryable_status_code(self):
        """测试可重试的 HTTP 状态码（429, 500, 502, 503, 504）"""
        config = _make_config(max_retries=1)
        client = DeepSeekClient(config)

        mock_error_response = MagicMock()
        mock_error_response.status_code = 429
        mock_error_response.json.return_value = {"error": {"message": "Rate limited"}}
        mock_error_response.text = "Rate limited"

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = _make_success_response()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.side_effect = [mock_error_response, mock_success_response]
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            result = await client.chat(messages)

            assert result.content == "Hello!"
            assert mock_http_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_chat_non_retryable_status_code(self):
        """测试不可重试的 HTTP 状态码（如 401, 403）"""
        config = _make_config(max_retries=2)
        client = DeepSeekClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Unauthorized"}}
        mock_response.text = "Unauthorized"

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            with pytest.raises(LLMServiceError, match="401"):
                await client.chat(messages)

            # 不可重试，只调用一次
            assert mock_http_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_chat_network_error_with_retry(self):
        """测试网络错误后重试"""
        config = _make_config(max_retries=1)
        client = DeepSeekClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _make_success_response()

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.side_effect = [
                httpx.ConnectError("Connection refused"),
                mock_response,
            ]
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            result = await client.chat(messages)

            assert result.content == "Hello!"
            assert mock_http_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_chat_network_error_exhausted(self):
        """测试网络错误重试耗尽"""
        config = _make_config(max_retries=1)
        client = DeepSeekClient(config)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            with pytest.raises(LLMServiceError, match="网络错误"):
                await client.chat(messages)

    @pytest.mark.asyncio
    async def test_chat_empty_choices(self):
        """测试 API 返回空 choices"""
        config = _make_config()
        client = DeepSeekClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [], "model": "deepseek-chat"}

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            with pytest.raises(LLMServiceError, match="没有 choices"):
                await client.chat(messages)

    @pytest.mark.asyncio
    async def test_chat_unexpected_exception(self):
        """测试意外异常被包装为 LLMServiceError"""
        config = _make_config(max_retries=0)
        client = DeepSeekClient(config)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.side_effect = RuntimeError("Unexpected error")
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            with pytest.raises(LLMServiceError, match="调用异常"):
                await client.chat(messages)


class TestDeepSeekClientRetryDelay:
    """重试延迟计算测试"""

    def test_exponential_backoff(self):
        """测试指数退避延迟"""
        config = _make_config(retry_base_delay=1.0, retry_max_delay=30.0)
        client = DeepSeekClient(config)

        assert client._calculate_retry_delay(0) == 1.0   # 1 * 2^0
        assert client._calculate_retry_delay(1) == 2.0   # 1 * 2^1
        assert client._calculate_retry_delay(2) == 4.0   # 1 * 2^2
        assert client._calculate_retry_delay(3) == 8.0   # 1 * 2^3
        assert client._calculate_retry_delay(4) == 16.0  # 1 * 2^4

    def test_max_delay_cap(self):
        """测试延迟上限"""
        config = _make_config(retry_base_delay=1.0, retry_max_delay=10.0)
        client = DeepSeekClient(config)

        assert client._calculate_retry_delay(5) == 10.0  # min(32, 10) = 10
        assert client._calculate_retry_delay(10) == 10.0


class TestDeepSeekClientRetryableStatus:
    """可重试状态码判断测试"""

    def test_retryable_status_codes(self):
        """测试可重试的状态码"""
        config = _make_config()
        client = DeepSeekClient(config)

        for code in [429, 500, 502, 503, 504]:
            assert client._is_retryable_status(code) is True

    def test_non_retryable_status_codes(self):
        """测试不可重试的状态码"""
        config = _make_config()
        client = DeepSeekClient(config)

        for code in [400, 401, 403, 404, 405, 422]:
            assert client._is_retryable_status(code) is False


class TestDeepSeekClientParseResponse:
    """响应解析测试"""

    def test_parse_valid_response(self):
        """测试解析有效响应"""
        config = _make_config()
        client = DeepSeekClient(config)

        data = _make_success_response()
        result = client._parse_response(data)

        assert result.content == "Hello!"
        assert result.model == "deepseek-chat"
        assert result.usage["prompt_tokens"] == 10
        assert result.usage["completion_tokens"] == 5
        assert result.usage["total_tokens"] == 15
        assert result.finish_reason == "stop"

    def test_parse_response_missing_usage(self):
        """测试解析缺少 usage 的响应"""
        config = _make_config()
        client = DeepSeekClient(config)

        data = {
            "choices": [{"message": {"content": "Hi"}, "finish_reason": "stop"}],
            "model": "deepseek-chat",
        }
        result = client._parse_response(data)

        assert result.content == "Hi"
        assert result.usage["total_tokens"] == 0

    def test_parse_response_empty_choices_raises(self):
        """测试空 choices 抛出异常"""
        config = _make_config()
        client = DeepSeekClient(config)

        with pytest.raises(LLMServiceError, match="没有 choices"):
            client._parse_response({"choices": []})


class TestDeepSeekClientContextManager:
    """上下文管理器测试"""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """测试异步上下文管理器"""
        config = _make_config()
        async with DeepSeekClient(config) as client:
            assert isinstance(client, DeepSeekClient)

    @pytest.mark.asyncio
    async def test_close_client(self):
        """测试关闭客户端"""
        config = _make_config()
        client = DeepSeekClient(config)
        # 触发客户端创建
        _ = client._get_client()
        assert client._client is not None
        await client.close()
        assert client._client is None


class TestDeepSeekClientRetryCount:
    """重试次数验证测试"""

    @pytest.mark.asyncio
    async def test_zero_retries(self):
        """测试 max_retries=0 时不重试"""
        config = _make_config(max_retries=0)
        client = DeepSeekClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": {"message": "Server error"}}
        mock_response.text = "Server error"

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            with pytest.raises(LLMServiceError, match="500"):
                await client.chat(messages)

            assert mock_http_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_retryable_status_exhausted(self):
        """测试可重试状态码重试耗尽"""
        config = _make_config(max_retries=2)
        client = DeepSeekClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.json.return_value = {"error": {"message": "Service unavailable"}}
        mock_response.text = "Service unavailable"

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http_client = AsyncMock()
            mock_http_client.post.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            messages = [ChatMessage(role="user", content="Hi")]
            with pytest.raises(LLMServiceError, match="503"):
                await client.chat(messages)

            # 1 initial + 2 retries = 3 calls
            assert mock_http_client.post.call_count == 3
