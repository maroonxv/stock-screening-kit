"""AKShare 新闻数据提供者实现

基于 AKShare 库实现 INewsDataProvider 接口，
通过东方财富股票新闻接口获取行业相关新闻数据。
异常时返回空列表并记录 WARNING 日志，确保工作流可降级运行。
"""

import logging
from datetime import datetime, timedelta
from typing import List

import akshare as ak

from contexts.intelligence.domain.repositories.news_data_provider import (
    INewsDataProvider,
    NewsItem,
)

logger = logging.getLogger(__name__)


class AKShareNewsProvider(INewsDataProvider):
    """基于 AKShare 的新闻数据提供者

    使用 AKShare 的 ``stock_news_em`` 接口（东方财富股票新闻）获取
    与查询关键词相关的近期新闻。当 AKShare 调用失败时，返回空列表
    并记录 WARNING 日志，使工作流可降级为仅依赖 LLM 知识进行分析。
    """

    def fetch_news(self, query: str, days: int = 7) -> List[NewsItem]:
        """获取与查询相关的新闻列表

        Args:
            query: 搜索查询关键词（如行业名称、股票名称）
            days: 获取最近多少天的新闻，默认 7 天

        Returns:
            NewsItem 列表，按发布时间降序排列；异常时返回空列表
        """
        try:
            logger.info(f"正在通过 AKShare 获取新闻数据，关键词: {query}, 天数: {days}")
            df = ak.stock_news_em(symbol=query)

            if df is None or df.empty:
                logger.info(f"未找到与 '{query}' 相关的新闻")
                return []

            cutoff = datetime.now() - timedelta(days=days)
            news_items: List[NewsItem] = []

            for _, row in df.iterrows():
                try:
                    published_at = self._parse_datetime(row.get("发布时间", ""))
                    if published_at and published_at < cutoff:
                        continue

                    news_items.append(
                        NewsItem(
                            title=str(row.get("新闻标题", "")),
                            source=str(row.get("新闻来源", "")),
                            published_at=published_at or datetime.now(),
                            url=str(row.get("新闻链接", "")),
                            summary=str(row.get("新闻内容", "")),
                        )
                    )
                except Exception as e:
                    logger.debug(f"解析单条新闻数据失败: {e}")
                    continue

            # 按发布时间降序排列
            news_items.sort(key=lambda item: item.published_at, reverse=True)
            logger.info(f"成功获取 {len(news_items)} 条与 '{query}' 相关的新闻")
            return news_items

        except Exception as e:
            logger.warning(f"通过 AKShare 获取新闻数据失败: {e}")
            return []

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        """安全解析日期时间字符串

        Args:
            value: 日期时间字符串

        Returns:
            解析后的 datetime 对象，解析失败返回 None
        """
        if not value:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(str(value), fmt)
            except (ValueError, TypeError):
                continue
        return None
