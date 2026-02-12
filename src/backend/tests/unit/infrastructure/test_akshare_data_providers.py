"""AKShare 数据提供者和工作流增强单元测试

测试 AKShareNewsProvider、AKShareAnnouncementProvider 的接口实现，
以及工作流 Agent 注入外部数据上下文的正确性。

Feature: real-service-integration
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import json
import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from contexts.intelligence.domain.repositories.announcement_data_provider import (
    Announcement,
    IAnnouncementDataProvider,
)
from contexts.intelligence.domain.repositories.news_data_provider import (
    INewsDataProvider,
    NewsItem,
)
from contexts.intelligence.infrastructure.data.akshare_announcement_provider import (
    AKShareAnnouncementProvider,
)
from contexts.intelligence.infrastructure.data.akshare_news_provider import (
    AKShareNewsProvider,
)
from shared_kernel.value_objects.stock_code import StockCode


# ============================================================
# AKShareNewsProvider Tests
# ============================================================


class TestAKShareNewsProvider:
    """AKShareNewsProvider 单元测试"""

    def test_implements_interface(self):
        """测试实现 INewsDataProvider 接口"""
        provider = AKShareNewsProvider()
        assert isinstance(provider, INewsDataProvider)

    @patch("contexts.intelligence.infrastructure.data.akshare_news_provider.ak")
    def test_fetch_news_returns_news_items(self, mock_ak):
        """测试正常获取新闻数据"""
        import pandas as pd

        mock_ak.stock_news_em.return_value = pd.DataFrame([
            {
                "新闻标题": "行业利好消息",
                "新闻来源": "财联社",
                "发布时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "新闻链接": "https://example.com/1",
                "新闻内容": "这是一条测试新闻",
            }
        ])

        provider = AKShareNewsProvider()
        result = provider.fetch_news("人工智能", days=7)

        assert len(result) == 1
        assert isinstance(result[0], NewsItem)
        assert result[0].title == "行业利好消息"
        assert result[0].source == "财联社"

    @patch("contexts.intelligence.infrastructure.data.akshare_news_provider.ak")
    def test_fetch_news_returns_empty_on_exception(self, mock_ak):
        """测试异常时返回空列表"""
        mock_ak.stock_news_em.side_effect = Exception("API 错误")

        provider = AKShareNewsProvider()
        result = provider.fetch_news("测试")

        assert result == []

    @patch("contexts.intelligence.infrastructure.data.akshare_news_provider.ak")
    def test_fetch_news_returns_empty_on_none_dataframe(self, mock_ak):
        """测试返回 None DataFrame 时返回空列表"""
        mock_ak.stock_news_em.return_value = None

        provider = AKShareNewsProvider()
        result = provider.fetch_news("测试")

        assert result == []

    @patch("contexts.intelligence.infrastructure.data.akshare_news_provider.ak")
    def test_fetch_news_filters_by_days(self, mock_ak):
        """测试按天数过滤新闻"""
        import pandas as pd

        now = datetime.now()
        mock_ak.stock_news_em.return_value = pd.DataFrame([
            {
                "新闻标题": "近期新闻",
                "新闻来源": "来源A",
                "发布时间": now.strftime("%Y-%m-%d %H:%M:%S"),
                "新闻链接": "https://example.com/1",
                "新闻内容": "近期内容",
            },
            {
                "新闻标题": "过期新闻",
                "新闻来源": "来源B",
                "发布时间": (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
                "新闻链接": "https://example.com/2",
                "新闻内容": "过期内容",
            },
        ])

        provider = AKShareNewsProvider()
        result = provider.fetch_news("测试", days=7)

        assert len(result) == 1
        assert result[0].title == "近期新闻"

    @patch("contexts.intelligence.infrastructure.data.akshare_news_provider.ak")
    def test_fetch_news_logs_warning_on_exception(self, mock_ak, caplog):
        """测试异常时记录 WARNING 日志"""
        mock_ak.stock_news_em.side_effect = Exception("连接超时")

        provider = AKShareNewsProvider()
        with caplog.at_level(logging.WARNING):
            provider.fetch_news("测试")

        assert "获取新闻数据失败" in caplog.text


# ============================================================
# AKShareAnnouncementProvider Tests
# ============================================================


class TestAKShareAnnouncementProvider:
    """AKShareAnnouncementProvider 单元测试"""

    def test_implements_interface(self):
        """测试实现 IAnnouncementDataProvider 接口"""
        provider = AKShareAnnouncementProvider()
        assert isinstance(provider, IAnnouncementDataProvider)

    @patch("contexts.intelligence.infrastructure.data.akshare_announcement_provider.ak")
    def test_fetch_announcements_returns_announcements(self, mock_ak):
        """测试正常获取公告数据"""
        import pandas as pd

        mock_ak.stock_notice_report.return_value = pd.DataFrame([
            {
                "公告标题": "年度报告",
                "公告日期": datetime.now().strftime("%Y-%m-%d"),
                "公告内容": "公司年度经营情况",
                "公告类型": "定期报告",
            }
        ])

        provider = AKShareAnnouncementProvider()
        stock_code = StockCode("600519.SH")
        result = provider.fetch_announcements(stock_code, days=30)

        assert len(result) == 1
        assert isinstance(result[0], Announcement)
        assert result[0].title == "年度报告"
        assert result[0].announcement_type == "定期报告"

    @patch("contexts.intelligence.infrastructure.data.akshare_announcement_provider.ak")
    def test_fetch_announcements_returns_empty_on_exception(self, mock_ak):
        """测试异常时返回空列表"""
        mock_ak.stock_notice_report.side_effect = Exception("API 错误")

        provider = AKShareAnnouncementProvider()
        stock_code = StockCode("600519.SH")
        result = provider.fetch_announcements(stock_code)

        assert result == []

    @patch("contexts.intelligence.infrastructure.data.akshare_announcement_provider.ak")
    def test_fetch_announcements_uses_numeric_code(self, mock_ak):
        """测试使用数字代码调用 AKShare API"""
        import pandas as pd

        mock_ak.stock_notice_report.return_value = pd.DataFrame()

        provider = AKShareAnnouncementProvider()
        stock_code = StockCode("600519.SH")
        provider.fetch_announcements(stock_code)

        mock_ak.stock_notice_report.assert_called_once_with(symbol="600519")

    @patch("contexts.intelligence.infrastructure.data.akshare_announcement_provider.ak")
    def test_fetch_announcements_logs_warning_on_exception(self, mock_ak, caplog):
        """测试异常时记录 WARNING 日志"""
        mock_ak.stock_notice_report.side_effect = Exception("连接超时")

        provider = AKShareAnnouncementProvider()
        stock_code = StockCode("600519.SH")
        with caplog.at_level(logging.WARNING):
            provider.fetch_announcements(stock_code)

        assert "获取公告数据失败" in caplog.text


# ============================================================
# Property 7: 外部数据上下文注入
# Feature: real-service-integration, Property 7: 外部数据上下文注入
# ============================================================


# Property tests require langgraph (only available in Docker)
try:
    import langgraph  # noqa: F401
    _has_langgraph = True
except ImportError:
    _has_langgraph = False


@pytest.mark.skipif(not _has_langgraph, reason="langgraph not installed locally, runs in Docker")
class TestProperty7ExternalDataContextInjection:
    """Property 7: 外部数据上下文注入

    *For any* 工作流 Agent 执行，当外部数据提供者返回非空数据时，
    Agent 构建的 LLM prompt 应包含该外部数据作为上下文信息。

    **Validates: Requirements 5.3, 5.4**
    """

    @given(
        news_titles=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("L", "N", "P")),
                min_size=1,
                max_size=50,
            ),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=100)
    def test_news_data_injected_into_market_heat_prompt(self, news_titles):
        """Property 7a: 新闻数据注入市场热度分析 prompt

        For any non-empty list of news items, the market heat agent's prompt
        should contain the news data as context.

        Feature: real-service-integration, Property 7: 外部数据上下文注入
        **Validates: Requirements 5.3**
        """
        from contexts.intelligence.infrastructure.ai.industry_research_workflow import (
            _build_market_heat_node,
        )
        from contexts.intelligence.infrastructure.ai.deepseek_client import (
            ChatCompletion,
            DeepSeekClient,
            DeepSeekConfig,
        )

        # Create mock news provider that returns generated news items
        mock_provider = MagicMock(spec=INewsDataProvider)
        news_items = [
            NewsItem(
                title=title,
                source="测试来源",
                published_at=datetime.now(),
                url="https://example.com",
                summary=f"摘要: {title}",
            )
            for title in news_titles
        ]
        mock_provider.fetch_news.return_value = news_items

        # Create mock DeepSeek client that captures the prompt
        captured_messages = []
        config = DeepSeekConfig(api_key="test", base_url="https://test.com/v1")
        client = DeepSeekClient(config)

        async def mock_chat(messages, **kwargs):
            captured_messages.extend(messages)
            return ChatCompletion(
                content=json.dumps({
                    "heat_score": 50,
                    "news_summary": "测试",
                    "risk_alerts": [],
                    "catalysts": [],
                }),
                model="test",
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                finish_reason="stop",
            )

        client.chat = mock_chat

        # Build the node with news provider
        node_fn = _build_market_heat_node(
            deepseek_client=client,
            news_provider=mock_provider,
        )

        # Execute the node
        import asyncio

        state = {
            "query": "测试行业",
            "industry_summary": "测试摘要",
        }

        asyncio.get_event_loop().run_until_complete(node_fn(state))

        # Verify: the prompt should contain news context
        assert len(captured_messages) >= 2
        user_prompt = captured_messages[1].content
        assert "近期相关新闻数据" in user_prompt
        for title in news_titles:
            assert title in user_prompt

    @given(
        announcement_titles=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("L", "N", "P")),
                min_size=1,
                max_size=50,
            ),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=100)
    def test_announcement_data_injected_into_evidence_prompt(self, announcement_titles):
        """Property 7b: 公告数据注入证据收集 prompt

        For any non-empty list of announcements, the evidence collection agent's
        prompt should contain the announcement data as context.

        Feature: real-service-integration, Property 7: 外部数据上下文注入
        **Validates: Requirements 5.4**
        """
        from contexts.intelligence.infrastructure.ai.credibility_workflow import (
            _build_evidence_collection_node,
        )
        from contexts.intelligence.infrastructure.ai.deepseek_client import (
            ChatCompletion,
            DeepSeekClient,
            DeepSeekConfig,
        )

        # Create mock announcement provider
        mock_provider = MagicMock(spec=IAnnouncementDataProvider)
        announcements = [
            Announcement(
                title=title,
                published_at=datetime.now(),
                content=f"内容: {title}",
                announcement_type="临时公告",
            )
            for title in announcement_titles
        ]
        mock_provider.fetch_announcements.return_value = announcements

        # Create mock DeepSeek client that captures the prompt
        captured_messages = []
        config = DeepSeekConfig(api_key="test", base_url="https://test.com/v1")
        client = DeepSeekClient(config)

        async def mock_chat(messages, **kwargs):
            captured_messages.extend(messages)
            return ChatCompletion(
                content=json.dumps({
                    "score": 50,
                    "patents": [],
                    "orders": [],
                    "partnerships": [],
                    "analysis": "测试分析",
                }),
                model="test",
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                finish_reason="stop",
            )

        client.chat = mock_chat

        # Build the node with announcement provider
        node_fn = _build_evidence_collection_node(
            deepseek_client=client,
            announcement_provider=mock_provider,
        )

        # Execute the node
        import asyncio

        state = {
            "stock_code": "600519.SH",
            "concept": "固态电池",
            "main_business_description": "测试主营业务",
        }

        asyncio.get_event_loop().run_until_complete(node_fn(state))

        # Verify: the prompt should contain announcement context
        assert len(captured_messages) >= 2
        user_prompt = captured_messages[1].content
        assert "近期公告数据" in user_prompt
        for title in announcement_titles:
            assert title in user_prompt

    def test_no_data_provider_no_context_in_prompt(self):
        """测试不提供数据提供者时 prompt 不包含外部数据上下文"""
        from contexts.intelligence.infrastructure.ai.industry_research_workflow import (
            _build_market_heat_node,
        )
        from contexts.intelligence.infrastructure.ai.deepseek_client import (
            ChatCompletion,
            DeepSeekClient,
            DeepSeekConfig,
        )

        captured_messages = []
        config = DeepSeekConfig(api_key="test", base_url="https://test.com/v1")
        client = DeepSeekClient(config)

        async def mock_chat(messages, **kwargs):
            captured_messages.extend(messages)
            return ChatCompletion(
                content=json.dumps({
                    "heat_score": 50,
                    "news_summary": "测试",
                    "risk_alerts": [],
                    "catalysts": [],
                }),
                model="test",
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                finish_reason="stop",
            )

        client.chat = mock_chat

        # Build without news provider
        node_fn = _build_market_heat_node(deepseek_client=client)

        import asyncio

        state = {"query": "测试", "industry_summary": "摘要"}
        asyncio.get_event_loop().run_until_complete(node_fn(state))

        user_prompt = captured_messages[1].content
        assert "近期相关新闻数据" not in user_prompt

    def test_data_provider_failure_degrades_gracefully(self):
        """测试数据提供者失败时降级为无外部数据"""
        from contexts.intelligence.infrastructure.ai.industry_research_workflow import (
            _build_market_heat_node,
        )
        from contexts.intelligence.infrastructure.ai.deepseek_client import (
            ChatCompletion,
            DeepSeekClient,
            DeepSeekConfig,
        )

        # Provider that raises exception
        mock_provider = MagicMock(spec=INewsDataProvider)
        mock_provider.fetch_news.side_effect = Exception("网络错误")

        captured_messages = []
        config = DeepSeekConfig(api_key="test", base_url="https://test.com/v1")
        client = DeepSeekClient(config)

        async def mock_chat(messages, **kwargs):
            captured_messages.extend(messages)
            return ChatCompletion(
                content=json.dumps({
                    "heat_score": 50,
                    "news_summary": "测试",
                    "risk_alerts": [],
                    "catalysts": [],
                }),
                model="test",
                usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                finish_reason="stop",
            )

        client.chat = mock_chat

        node_fn = _build_market_heat_node(
            deepseek_client=client,
            news_provider=mock_provider,
        )

        import asyncio

        state = {"query": "测试", "industry_summary": "摘要"}
        # Should not raise, should degrade gracefully
        asyncio.get_event_loop().run_until_complete(node_fn(state))

        user_prompt = captured_messages[1].content
        assert "近期相关新闻数据" not in user_prompt
