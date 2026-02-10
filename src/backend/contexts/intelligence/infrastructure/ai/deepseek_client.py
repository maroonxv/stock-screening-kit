"""DeepSeek LLM 客户端

封装 DeepSeek API 调用（OpenAI 兼容格式），支持超时控制和指数退避重试机制。
通过环境变量配置 API 密钥、基础 URL、模型名称和超时时间。

Requirements: 6.4, 10.5
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from src.backend.contexts.intelligence.domain.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeepSeekConfig:
    """DeepSeek API 配置"""

    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    timeout: float = 60.0
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    temperature: float = 0.7
    max_tokens: int = 4096

    @classmethod
    def from_env(cls) -> "DeepSeekConfig":
        """从环境变量创建配置

        环境变量:
            DEEPSEEK_API_KEY: API 密钥（必填）
            DEEPSEEK_BASE_URL: API 基础 URL（默认 https://api.deepseek.com/v1）
            DEEPSEEK_MODEL: 模型名称（默认 deepseek-chat）
            DEEPSEEK_TIMEOUT: 请求超时秒数（默认 60）
            DEEPSEEK_MAX_RETRIES: 最大重试次数（默认 3）
        """
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise LLMServiceError("DEEPSEEK_API_KEY 环境变量未设置")

        return cls(
            api_key=api_key,
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            timeout=float(os.environ.get("DEEPSEEK_TIMEOUT", "60")),
            max_retries=int(os.environ.get("DEEPSEEK_MAX_RETRIES", "3")),
        )


@dataclass
class ChatMessage:
    """聊天消息"""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class ChatCompletion:
    """聊天补全响应"""

    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""


class DeepSeekClient:
    """DeepSeek LLM 客户端

    封装 DeepSeek API（OpenAI 兼容格式），提供：
    - 超时控制
    - 指数退避重试机制
    - 优雅的错误处理（抛出 LLMServiceError）
    """

    def __init__(self, config: Optional[DeepSeekConfig] = None):
        """初始化 DeepSeek 客户端

        Args:
            config: DeepSeek 配置，为 None 时从环境变量读取
        """
        self._config = config or DeepSeekConfig.from_env()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def config(self) -> DeepSeekConfig:
        return self._config

    def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端（惰性初始化）"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._config.base_url,
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self._config.timeout),
            )
        return self._client

    async def close(self) -> None:
        """关闭 HTTP 客户端连接"""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _calculate_retry_delay(self, attempt: int) -> float:
        """计算指数退避延迟时间

        Args:
            attempt: 当前重试次数（从 0 开始）

        Returns:
            延迟秒数
        """
        delay = self._config.retry_base_delay * (2 ** attempt)
        return min(delay, self._config.retry_max_delay)

    def _is_retryable_status(self, status_code: int) -> bool:
        """判断 HTTP 状态码是否可重试

        可重试状态码：429（限流）、500、502、503、504（服务端错误）
        """
        return status_code in (429, 500, 502, 503, 504)

    async def chat(
        self,
        messages: List[ChatMessage],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> ChatCompletion:
        """发送聊天补全请求

        Args:
            messages: 聊天消息列表
            temperature: 温度参数（覆盖默认值）
            max_tokens: 最大 token 数（覆盖默认值）
            model: 模型名称（覆盖默认值）

        Returns:
            ChatCompletion 响应

        Raises:
            LLMServiceError: API 调用失败（超时、网络错误、API 错误等）
        """
        payload = {
            "model": model or self._config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature if temperature is not None else self._config.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self._config.max_tokens,
        }

        last_exception: Optional[Exception] = None

        for attempt in range(self._config.max_retries + 1):
            try:
                client = self._get_client()
                response = await client.post("/chat/completions", json=payload)

                if response.status_code == 200:
                    return self._parse_response(response.json())

                # 非 200 响应
                if self._is_retryable_status(response.status_code) and attempt < self._config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "DeepSeek API 返回 %d，第 %d 次重试，等待 %.1f 秒",
                        response.status_code,
                        attempt + 1,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                # 不可重试的错误或已用尽重试次数
                self._raise_api_error(response)

            except LLMServiceError:
                raise

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < self._config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "DeepSeek API 请求超时，第 %d 次重试，等待 %.1f 秒",
                        attempt + 1,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                raise LLMServiceError(
                    f"DeepSeek API 请求超时（已重试 {self._config.max_retries} 次）: {e}"
                ) from e

            except httpx.HTTPError as e:
                last_exception = e
                if attempt < self._config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "DeepSeek API 网络错误: %s，第 %d 次重试，等待 %.1f 秒",
                        str(e),
                        attempt + 1,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                raise LLMServiceError(
                    f"DeepSeek API 网络错误（已重试 {self._config.max_retries} 次）: {e}"
                ) from e

            except Exception as e:
                raise LLMServiceError(f"DeepSeek API 调用异常: {e}") from e

        # 理论上不应到达这里，但作为安全保障
        raise LLMServiceError(
            f"DeepSeek API 调用失败（已重试 {self._config.max_retries} 次）"
        )

    def _parse_response(self, data: Dict[str, Any]) -> ChatCompletion:
        """解析 API 响应

        Args:
            data: API 响应 JSON 数据

        Returns:
            ChatCompletion 对象

        Raises:
            LLMServiceError: 响应格式异常
        """
        try:
            choices = data.get("choices", [])
            if not choices:
                raise LLMServiceError("DeepSeek API 响应中没有 choices")

            message = choices[0].get("message", {})
            content = message.get("content", "")
            finish_reason = choices[0].get("finish_reason", "")

            usage = data.get("usage", {})

            return ChatCompletion(
                content=content,
                model=data.get("model", ""),
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                finish_reason=finish_reason,
            )
        except LLMServiceError:
            raise
        except Exception as e:
            raise LLMServiceError(f"DeepSeek API 响应解析失败: {e}") from e

    def _raise_api_error(self, response: httpx.Response) -> None:
        """根据 HTTP 响应抛出 LLMServiceError

        Args:
            response: HTTP 响应

        Raises:
            LLMServiceError: 包含状态码和错误信息
        """
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", response.text)
        except Exception:
            error_msg = response.text

        raise LLMServiceError(
            f"DeepSeek API 错误 (HTTP {response.status_code}): {error_msg}"
        )

    async def __aenter__(self) -> "DeepSeekClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
