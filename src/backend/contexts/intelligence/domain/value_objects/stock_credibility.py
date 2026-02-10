"""个股可信度值对象模块

包含 StockCredibility 值对象，用于行业认知结果中的核心标的列表。
每只股票包含股票代码、名称、可信度评分和相关性摘要。
"""

from shared_kernel.value_objects.stock_code import StockCode
from .credibility_score import CredibilityScore


class StockCredibility:
    """个股可信度（用于行业认知结果中的核心标的列表）

    不可变值对象，封装单只股票的可信度分析结果，包括：
    - 股票代码（StockCode）
    - 股票名称
    - 可信度评分（CredibilityScore）
    - 相关性摘要
    """

    def __init__(
        self,
        stock_code: StockCode,
        stock_name: str,
        credibility_score: CredibilityScore,
        relevance_summary: str,
    ):
        """初始化 StockCredibility

        Args:
            stock_code: 股票代码值对象
            stock_name: 股票名称
            credibility_score: 可信度评分值对象
            relevance_summary: 相关性摘要文本
        """
        self._stock_code = stock_code
        self._stock_name = stock_name
        self._credibility_score = credibility_score
        self._relevance_summary = relevance_summary

    @property
    def stock_code(self) -> StockCode:
        """获取股票代码"""
        return self._stock_code

    @property
    def stock_name(self) -> str:
        """获取股票名称"""
        return self._stock_name

    @property
    def credibility_score(self) -> CredibilityScore:
        """获取可信度评分"""
        return self._credibility_score

    @property
    def relevance_summary(self) -> str:
        """获取相关性摘要"""
        return self._relevance_summary

    def to_dict(self) -> dict:
        """序列化为字典

        Returns:
            包含 stock_code、stock_name、credibility_score 和 relevance_summary 的字典
        """
        return {
            "stock_code": self._stock_code.code,
            "stock_name": self._stock_name,
            "credibility_score": self._credibility_score.to_dict(),
            "relevance_summary": self._relevance_summary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StockCredibility":
        """从字典反序列化创建 StockCredibility

        Args:
            data: 包含 stock_code、stock_name、credibility_score 和 relevance_summary 的字典

        Returns:
            StockCredibility 实例

        Raises:
            ValueError: 如果数据无效
            KeyError: 如果字典缺少必要的键
        """
        return cls(
            stock_code=StockCode(data["stock_code"]),
            stock_name=data["stock_name"],
            credibility_score=CredibilityScore.from_dict(data["credibility_score"]),
            relevance_summary=data["relevance_summary"],
        )

    def __eq__(self, other):
        """判断两个 StockCredibility 是否相等"""
        return (
            isinstance(other, StockCredibility)
            and self._stock_code == other._stock_code
            and self._stock_name == other._stock_name
            and self._credibility_score == other._credibility_score
            and self._relevance_summary == other._relevance_summary
        )

    def __hash__(self):
        """返回哈希值，支持在集合和字典中使用"""
        return hash(
            (self._stock_code, self._stock_name, self._credibility_score, self._relevance_summary)
        )

    def __repr__(self):
        """返回字符串表示"""
        return (
            f"StockCredibility(stock_code={self._stock_code!r}, "
            f"stock_name='{self._stock_name}', "
            f"credibility_score={self._credibility_score!r}, "
            f"relevance_summary='{self._relevance_summary[:30]}...')"
        )
