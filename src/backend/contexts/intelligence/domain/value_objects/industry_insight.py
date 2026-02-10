"""行业认知值对象模块

包含 IndustryInsight 值对象，用于快速行业认知工作流的输出结果。
封装行业名称、总结、产业链结构、技术路线、市场规模、核心标的、
风险提示、催化剂、市场热度评分和竞争格局等信息。
"""

from typing import List

from .stock_credibility import StockCredibility


class IndustryInsight:
    """快速行业认知工作流的输出结果

    不可变值对象，封装快速行业认知工作流的完整输出，包括：
    - 行业名称和一页纸总结
    - 产业链结构描述和技术路线列表
    - 市场规模描述
    - 核心标的列表（5-10 只，含可信度评分）
    - 风险提示和催化剂列表
    - 市场热度评分（0-100）
    - 竞争格局描述
    """

    def __init__(
        self,
        industry_name: str,
        summary: str,
        industry_chain: str,
        technology_routes: List[str],
        market_size: str,
        top_stocks: List[StockCredibility],
        risk_alerts: List[str],
        catalysts: List[str],
        heat_score: int,
        competitive_landscape: str,
    ):
        """初始化 IndustryInsight

        Args:
            industry_name: 行业名称
            summary: 行业一页纸总结
            industry_chain: 产业链结构描述
            technology_routes: 技术路线列表
            market_size: 市场规模描述
            top_stocks: 核心标的列表（List[StockCredibility]）
            risk_alerts: 风险提示列表
            catalysts: 催化剂列表
            heat_score: 市场热度评分，0-100 整数
            competitive_landscape: 竞争格局描述
        """
        self._industry_name = industry_name
        self._summary = summary
        self._industry_chain = industry_chain
        self._technology_routes = list(technology_routes)
        self._market_size = market_size
        self._top_stocks = list(top_stocks)
        self._risk_alerts = list(risk_alerts)
        self._catalysts = list(catalysts)
        self._heat_score = heat_score
        self._competitive_landscape = competitive_landscape

    @property
    def industry_name(self) -> str:
        """获取行业名称"""
        return self._industry_name

    @property
    def summary(self) -> str:
        """获取行业一页纸总结"""
        return self._summary

    @property
    def industry_chain(self) -> str:
        """获取产业链结构描述"""
        return self._industry_chain

    @property
    def technology_routes(self) -> List[str]:
        """获取技术路线列表（防御性拷贝）"""
        return list(self._technology_routes)

    @property
    def market_size(self) -> str:
        """获取市场规模描述"""
        return self._market_size

    @property
    def top_stocks(self) -> List[StockCredibility]:
        """获取核心标的列表（防御性拷贝）"""
        return list(self._top_stocks)

    @property
    def risk_alerts(self) -> List[str]:
        """获取风险提示列表（防御性拷贝）"""
        return list(self._risk_alerts)

    @property
    def catalysts(self) -> List[str]:
        """获取催化剂列表（防御性拷贝）"""
        return list(self._catalysts)

    @property
    def heat_score(self) -> int:
        """获取市场热度评分（0-100）"""
        return self._heat_score

    @property
    def competitive_landscape(self) -> str:
        """获取竞争格局描述"""
        return self._competitive_landscape

    def to_dict(self) -> dict:
        """序列化为字典

        Returns:
            包含所有属性的字典，top_stocks 使用 StockCredibility.to_dict 序列化
        """
        return {
            "industry_name": self._industry_name,
            "summary": self._summary,
            "industry_chain": self._industry_chain,
            "technology_routes": self._technology_routes,
            "market_size": self._market_size,
            "top_stocks": [s.to_dict() for s in self._top_stocks],
            "risk_alerts": self._risk_alerts,
            "catalysts": self._catalysts,
            "heat_score": self._heat_score,
            "competitive_landscape": self._competitive_landscape,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IndustryInsight":
        """从字典反序列化创建 IndustryInsight

        Args:
            data: 包含所有属性的字典，top_stocks 为 StockCredibility 字典列表

        Returns:
            IndustryInsight 实例

        Raises:
            ValueError: 如果数据无效
            KeyError: 如果字典缺少必要的键
        """
        return cls(
            industry_name=data["industry_name"],
            summary=data["summary"],
            industry_chain=data["industry_chain"],
            technology_routes=data["technology_routes"],
            market_size=data["market_size"],
            top_stocks=[StockCredibility.from_dict(s) for s in data["top_stocks"]],
            risk_alerts=data["risk_alerts"],
            catalysts=data["catalysts"],
            heat_score=data["heat_score"],
            competitive_landscape=data["competitive_landscape"],
        )

    def __eq__(self, other):
        """判断两个 IndustryInsight 是否相等"""
        return (
            isinstance(other, IndustryInsight)
            and self._industry_name == other._industry_name
            and self._summary == other._summary
            and self._industry_chain == other._industry_chain
            and self._technology_routes == other._technology_routes
            and self._market_size == other._market_size
            and self._top_stocks == other._top_stocks
            and self._risk_alerts == other._risk_alerts
            and self._catalysts == other._catalysts
            and self._heat_score == other._heat_score
            and self._competitive_landscape == other._competitive_landscape
        )

    def __hash__(self):
        """返回哈希值，支持在集合和字典中使用"""
        return hash((
            self._industry_name,
            self._summary,
            self._industry_chain,
            tuple(self._technology_routes),
            self._market_size,
            tuple(self._top_stocks),
            tuple(self._risk_alerts),
            tuple(self._catalysts),
            self._heat_score,
            self._competitive_landscape,
        ))

    def __repr__(self):
        """返回字符串表示"""
        return (
            f"IndustryInsight(industry_name='{self._industry_name}', "
            f"heat_score={self._heat_score}, "
            f"top_stocks={len(self._top_stocks)}, "
            f"risk_alerts={len(self._risk_alerts)}, "
            f"catalysts={len(self._catalysts)})"
        )
