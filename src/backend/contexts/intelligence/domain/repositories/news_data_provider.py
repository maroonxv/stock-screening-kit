"""新闻数据提供者接口

定义 INewsDataProvider 抽象接口和 NewsItem 数据类，用于获取新闻数据。
领域层定义接口，基础设施层（新闻爬虫/API）提供具体实现。
通过接口抽象实现对外部数据源的依赖倒置。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


class NewsItem:
    """新闻数据项

    封装单条新闻的基本信息，包括标题、来源、发布时间、URL 和摘要。
    """

    def __init__(
        self,
        title: str,
        source: str,
        published_at: datetime,
        url: str,
        summary: str,
    ):
        """初始化 NewsItem

        Args:
            title: 新闻标题
            source: 新闻来源（如"财联社"、"东方财富"）
            published_at: 发布时间
            url: 新闻链接
            summary: 新闻摘要
        """
        self.title = title
        self.source = source
        self.published_at = published_at
        self.url = url
        self.summary = summary


class INewsDataProvider(ABC):
    """新闻数据提供者接口

    定义新闻数据获取的契约。基础设施层通过新闻爬虫或第三方 API
    实现此接口，为行业认知和可信度验证工作流提供新闻数据支持。
    """

    @abstractmethod
    def fetch_news(self, query: str, days: int = 7) -> List[NewsItem]:
        """获取与查询相关的新闻列表

        Args:
            query: 搜索查询关键词
            days: 获取最近多少天的新闻，默认 7 天

        Returns:
            NewsItem 列表，按发布时间降序排列
        """
        ...
