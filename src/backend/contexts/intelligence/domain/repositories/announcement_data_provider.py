"""公司公告数据提供者接口

定义 IAnnouncementDataProvider 抽象接口和 Announcement 数据类，用于获取公司公告数据。
领域层定义接口，基础设施层（公告 API/爬虫）提供具体实现。
通过接口抽象实现对外部数据源的依赖倒置。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from shared_kernel.value_objects.stock_code import StockCode


class Announcement:
    """公司公告数据项

    封装单条公司公告的基本信息，包括标题、发布时间、内容和公告类型。
    """

    def __init__(
        self,
        title: str,
        published_at: datetime,
        content: str,
        announcement_type: str,
    ):
        """初始化 Announcement

        Args:
            title: 公告标题
            published_at: 发布时间
            content: 公告内容
            announcement_type: 公告类型（如"定期报告"、"临时公告"、"重大事项"）
        """
        self.title = title
        self.published_at = published_at
        self.content = content
        self.announcement_type = announcement_type


class IAnnouncementDataProvider(ABC):
    """公司公告数据提供者接口

    定义公司公告数据获取的契约。基础设施层通过公告 API 或爬虫
    实现此接口，为可信度验证工作流提供公告数据支持。
    """

    @abstractmethod
    def fetch_announcements(
        self, stock_code: StockCode, days: int = 30
    ) -> List[Announcement]:
        """获取指定股票的公司公告列表

        Args:
            stock_code: 股票代码值对象
            days: 获取最近多少天的公告，默认 30 天

        Returns:
            Announcement 列表，按发布时间降序排列
        """
        ...
