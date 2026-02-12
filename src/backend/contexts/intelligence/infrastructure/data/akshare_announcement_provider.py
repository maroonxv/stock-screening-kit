"""AKShare 公告数据提供者实现

基于 AKShare 库实现 IAnnouncementDataProvider 接口，
通过股票公告接口获取指定股票的近期公司公告数据。
异常时返回空列表并记录 WARNING 日志，确保工作流可降级运行。
"""

import logging
from datetime import datetime, timedelta
from typing import List

import akshare as ak

from contexts.intelligence.domain.repositories.announcement_data_provider import (
    Announcement,
    IAnnouncementDataProvider,
)
from shared_kernel.value_objects.stock_code import StockCode

logger = logging.getLogger(__name__)


class AKShareAnnouncementProvider(IAnnouncementDataProvider):
    """基于 AKShare 的公告数据提供者

    使用 AKShare 的 ``stock_notice_report`` 接口获取指定股票的近期公司公告。
    当 AKShare 调用失败时，返回空列表并记录 WARNING 日志，
    使工作流可降级为仅依赖 LLM 知识进行分析。
    """

    def fetch_announcements(
        self, stock_code: StockCode, days: int = 30
    ) -> List[Announcement]:
        """获取指定股票的公司公告列表

        Args:
            stock_code: 股票代码值对象
            days: 获取最近多少天的公告，默认 30 天

        Returns:
            Announcement 列表，按发布时间降序排列；异常时返回空列表
        """
        try:
            symbol = stock_code.numeric_code
            logger.info(
                f"正在通过 AKShare 获取公告数据，股票代码: {symbol}, 天数: {days}"
            )
            df = ak.stock_notice_report(symbol=symbol)

            if df is None or df.empty:
                logger.info(f"未找到股票 '{symbol}' 的公告数据")
                return []

            cutoff = datetime.now() - timedelta(days=days)
            announcements: List[Announcement] = []

            for _, row in df.iterrows():
                try:
                    published_at = self._parse_datetime(
                        row.get("公告日期", "")
                    )
                    if published_at and published_at < cutoff:
                        continue

                    announcements.append(
                        Announcement(
                            title=str(row.get("公告标题", "")),
                            published_at=published_at or datetime.now(),
                            content=str(row.get("公告内容", "")),
                            announcement_type=str(row.get("公告类型", "")),
                        )
                    )
                except Exception as e:
                    logger.debug(f"解析单条公告数据失败: {e}")
                    continue

            # 按发布时间降序排列
            announcements.sort(
                key=lambda item: item.published_at, reverse=True
            )
            logger.info(
                f"成功获取 {len(announcements)} 条股票 '{symbol}' 的公告"
            )
            return announcements

        except Exception as e:
            logger.warning(f"通过 AKShare 获取公告数据失败: {e}")
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
