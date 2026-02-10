"""可信度报告值对象模块

包含 CredibilityReport 及其子值对象，用于概念可信度验证的完整分析结果。
子值对象包括：
- MainBusinessMatch: 主营业务匹配度分析
- EvidenceAnalysis: 实质证据分析（专利/订单/合作伙伴）
- HypeHistory: 历史蹭热点记录分析
- SupplyChainLogic: 供应链逻辑合理性分析
"""

from typing import List

from shared_kernel.value_objects.stock_code import StockCode
from .credibility_score import CredibilityScore
from ..enums.enums import RiskLabel


class MainBusinessMatch:
    """主营业务匹配度分析

    不可变值对象，封装股票主营业务与概念的匹配度分析结果。
    包含匹配度评分（0-100）、主营业务描述和匹配分析文本。
    """

    def __init__(self, score: int, main_business_description: str, match_analysis: str):
        """初始化 MainBusinessMatch

        Args:
            score: 匹配度评分，0-100 整数
            main_business_description: 主营业务描述
            match_analysis: 匹配分析文本
        """
        self._score = score
        self._main_business_description = main_business_description
        self._match_analysis = match_analysis

    @property
    def score(self) -> int:
        """获取匹配度评分"""
        return self._score

    @property
    def main_business_description(self) -> str:
        """获取主营业务描述"""
        return self._main_business_description

    @property
    def match_analysis(self) -> str:
        """获取匹配分析文本"""
        return self._match_analysis

    def to_dict(self) -> dict:
        """序列化为字典

        Returns:
            包含 score、main_business_description 和 match_analysis 的字典
        """
        return {
            "score": self._score,
            "main_business_description": self._main_business_description,
            "match_analysis": self._match_analysis,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MainBusinessMatch":
        """从字典反序列化创建 MainBusinessMatch

        Args:
            data: 包含 score、main_business_description 和 match_analysis 的字典

        Returns:
            MainBusinessMatch 实例
        """
        return cls(
            score=data["score"],
            main_business_description=data["main_business_description"],
            match_analysis=data["match_analysis"],
        )

    def __eq__(self, other):
        """判断两个 MainBusinessMatch 是否相等"""
        return (
            isinstance(other, MainBusinessMatch)
            and self._score == other._score
            and self._main_business_description == other._main_business_description
            and self._match_analysis == other._match_analysis
        )

    def __hash__(self):
        """返回哈希值"""
        return hash((self._score, self._main_business_description, self._match_analysis))

    def __repr__(self):
        """返回字符串表示"""
        return (
            f"MainBusinessMatch(score={self._score}, "
            f"main_business_description='{self._main_business_description[:30]}...', "
            f"match_analysis='{self._match_analysis[:30]}...')"
        )


class EvidenceAnalysis:
    """实质证据分析（专利/订单/合作伙伴）

    不可变值对象，封装概念相关的实质证据分析结果。
    包含证据评分（0-100）、专利列表、订单列表、合作伙伴列表和分析文本。
    """

    def __init__(
        self,
        score: int,
        patents: List[str],
        orders: List[str],
        partnerships: List[str],
        analysis: str,
    ):
        """初始化 EvidenceAnalysis

        Args:
            score: 证据评分，0-100 整数
            patents: 专利列表
            orders: 订单列表
            partnerships: 合作伙伴列表
            analysis: 分析文本
        """
        self._score = score
        self._patents = list(patents)
        self._orders = list(orders)
        self._partnerships = list(partnerships)
        self._analysis = analysis

    @property
    def score(self) -> int:
        """获取证据评分"""
        return self._score

    @property
    def patents(self) -> List[str]:
        """获取专利列表"""
        return list(self._patents)

    @property
    def orders(self) -> List[str]:
        """获取订单列表"""
        return list(self._orders)

    @property
    def partnerships(self) -> List[str]:
        """获取合作伙伴列表"""
        return list(self._partnerships)

    @property
    def analysis(self) -> str:
        """获取分析文本"""
        return self._analysis

    def to_dict(self) -> dict:
        """序列化为字典

        Returns:
            包含 score、patents、orders、partnerships 和 analysis 的字典
        """
        return {
            "score": self._score,
            "patents": self._patents,
            "orders": self._orders,
            "partnerships": self._partnerships,
            "analysis": self._analysis,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EvidenceAnalysis":
        """从字典反序列化创建 EvidenceAnalysis

        Args:
            data: 包含 score、patents、orders、partnerships 和 analysis 的字典

        Returns:
            EvidenceAnalysis 实例
        """
        return cls(
            score=data["score"],
            patents=data["patents"],
            orders=data["orders"],
            partnerships=data["partnerships"],
            analysis=data["analysis"],
        )

    def __eq__(self, other):
        """判断两个 EvidenceAnalysis 是否相等"""
        return (
            isinstance(other, EvidenceAnalysis)
            and self._score == other._score
            and self._patents == other._patents
            and self._orders == other._orders
            and self._partnerships == other._partnerships
            and self._analysis == other._analysis
        )

    def __hash__(self):
        """返回哈希值"""
        return hash((
            self._score,
            tuple(self._patents),
            tuple(self._orders),
            tuple(self._partnerships),
            self._analysis,
        ))

    def __repr__(self):
        """返回字符串表示"""
        return (
            f"EvidenceAnalysis(score={self._score}, "
            f"patents={len(self._patents)}, orders={len(self._orders)}, "
            f"partnerships={len(self._partnerships)})"
        )


class HypeHistory:
    """历史蹭热点记录分析

    不可变值对象，封装股票历史蹭热点的分析结果。
    评分越高越可信（即历史蹭热点越少）。
    包含评分（0-100）、历史蹭过的概念列表和分析文本。
    """

    def __init__(self, score: int, past_concepts: List[str], analysis: str):
        """初始化 HypeHistory

        Args:
            score: 评分，0-100 整数（越高越可信，历史蹭热点越少）
            past_concepts: 历史蹭过的概念列表
            analysis: 分析文本
        """
        self._score = score
        self._past_concepts = list(past_concepts)
        self._analysis = analysis

    @property
    def score(self) -> int:
        """获取评分"""
        return self._score

    @property
    def past_concepts(self) -> List[str]:
        """获取历史蹭过的概念列表"""
        return list(self._past_concepts)

    @property
    def analysis(self) -> str:
        """获取分析文本"""
        return self._analysis

    def to_dict(self) -> dict:
        """序列化为字典

        Returns:
            包含 score、past_concepts 和 analysis 的字典
        """
        return {
            "score": self._score,
            "past_concepts": self._past_concepts,
            "analysis": self._analysis,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HypeHistory":
        """从字典反序列化创建 HypeHistory

        Args:
            data: 包含 score、past_concepts 和 analysis 的字典

        Returns:
            HypeHistory 实例
        """
        return cls(
            score=data["score"],
            past_concepts=data["past_concepts"],
            analysis=data["analysis"],
        )

    def __eq__(self, other):
        """判断两个 HypeHistory 是否相等"""
        return (
            isinstance(other, HypeHistory)
            and self._score == other._score
            and self._past_concepts == other._past_concepts
            and self._analysis == other._analysis
        )

    def __hash__(self):
        """返回哈希值"""
        return hash((self._score, tuple(self._past_concepts), self._analysis))

    def __repr__(self):
        """返回字符串表示"""
        return (
            f"HypeHistory(score={self._score}, "
            f"past_concepts={len(self._past_concepts)})"
        )


class SupplyChainLogic:
    """供应链逻辑合理性分析

    不可变值对象，封装概念与股票供应链的逻辑合理性分析结果。
    包含评分（0-100）、上游环节列表、下游环节列表和分析文本。
    """

    def __init__(
        self,
        score: int,
        upstream: List[str],
        downstream: List[str],
        analysis: str,
    ):
        """初始化 SupplyChainLogic

        Args:
            score: 评分，0-100 整数
            upstream: 上游环节列表
            downstream: 下游环节列表
            analysis: 分析文本
        """
        self._score = score
        self._upstream = list(upstream)
        self._downstream = list(downstream)
        self._analysis = analysis

    @property
    def score(self) -> int:
        """获取评分"""
        return self._score

    @property
    def upstream(self) -> List[str]:
        """获取上游环节列表"""
        return list(self._upstream)

    @property
    def downstream(self) -> List[str]:
        """获取下游环节列表"""
        return list(self._downstream)

    @property
    def analysis(self) -> str:
        """获取分析文本"""
        return self._analysis

    def to_dict(self) -> dict:
        """序列化为字典

        Returns:
            包含 score、upstream、downstream 和 analysis 的字典
        """
        return {
            "score": self._score,
            "upstream": self._upstream,
            "downstream": self._downstream,
            "analysis": self._analysis,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SupplyChainLogic":
        """从字典反序列化创建 SupplyChainLogic

        Args:
            data: 包含 score、upstream、downstream 和 analysis 的字典

        Returns:
            SupplyChainLogic 实例
        """
        return cls(
            score=data["score"],
            upstream=data["upstream"],
            downstream=data["downstream"],
            analysis=data["analysis"],
        )

    def __eq__(self, other):
        """判断两个 SupplyChainLogic 是否相等"""
        return (
            isinstance(other, SupplyChainLogic)
            and self._score == other._score
            and self._upstream == other._upstream
            and self._downstream == other._downstream
            and self._analysis == other._analysis
        )

    def __hash__(self):
        """返回哈希值"""
        return hash((
            self._score,
            tuple(self._upstream),
            tuple(self._downstream),
            self._analysis,
        ))

    def __repr__(self):
        """返回字符串表示"""
        return (
            f"SupplyChainLogic(score={self._score}, "
            f"upstream={len(self._upstream)}, downstream={len(self._downstream)})"
        )


class CredibilityReport:
    """概念可信度验证的完整报告

    不可变值对象，封装概念可信度验证的完整分析结果。
    包含股票信息、总体评分、四个维度的分析（主营业务匹配度、实质证据、
    历史蹭热点记录、供应链逻辑）、风险标签和总结文本。
    """

    def __init__(
        self,
        stock_code: StockCode,
        stock_name: str,
        concept: str,
        overall_score: CredibilityScore,
        main_business_match: MainBusinessMatch,
        evidence: EvidenceAnalysis,
        hype_history: HypeHistory,
        supply_chain_logic: SupplyChainLogic,
        risk_labels: List[RiskLabel],
        conclusion: str,
    ):
        """初始化 CredibilityReport

        Args:
            stock_code: 股票代码值对象
            stock_name: 股票名称
            concept: 被验证的概念
            overall_score: 总体可信度评分
            main_business_match: 主营业务匹配度分析
            evidence: 实质证据分析
            hype_history: 历史蹭热点记录分析
            supply_chain_logic: 供应链逻辑合理性分析
            risk_labels: 风险标签列表
            conclusion: 总结文本
        """
        self._stock_code = stock_code
        self._stock_name = stock_name
        self._concept = concept
        self._overall_score = overall_score
        self._main_business_match = main_business_match
        self._evidence = evidence
        self._hype_history = hype_history
        self._supply_chain_logic = supply_chain_logic
        self._risk_labels = list(risk_labels)
        self._conclusion = conclusion

    @property
    def stock_code(self) -> StockCode:
        """获取股票代码"""
        return self._stock_code

    @property
    def stock_name(self) -> str:
        """获取股票名称"""
        return self._stock_name

    @property
    def concept(self) -> str:
        """获取被验证的概念"""
        return self._concept

    @property
    def overall_score(self) -> CredibilityScore:
        """获取总体可信度评分"""
        return self._overall_score

    @property
    def main_business_match(self) -> MainBusinessMatch:
        """获取主营业务匹配度分析"""
        return self._main_business_match

    @property
    def evidence(self) -> EvidenceAnalysis:
        """获取实质证据分析"""
        return self._evidence

    @property
    def hype_history(self) -> HypeHistory:
        """获取历史蹭热点记录分析"""
        return self._hype_history

    @property
    def supply_chain_logic(self) -> SupplyChainLogic:
        """获取供应链逻辑合理性分析"""
        return self._supply_chain_logic

    @property
    def risk_labels(self) -> List[RiskLabel]:
        """获取风险标签列表"""
        return list(self._risk_labels)

    @property
    def conclusion(self) -> str:
        """获取总结文本"""
        return self._conclusion

    def to_dict(self) -> dict:
        """序列化为字典

        Returns:
            包含所有属性的字典，risk_labels 序列化为枚举值字符串列表
        """
        return {
            "stock_code": self._stock_code.code,
            "stock_name": self._stock_name,
            "concept": self._concept,
            "overall_score": self._overall_score.to_dict(),
            "main_business_match": self._main_business_match.to_dict(),
            "evidence": self._evidence.to_dict(),
            "hype_history": self._hype_history.to_dict(),
            "supply_chain_logic": self._supply_chain_logic.to_dict(),
            "risk_labels": [r.value for r in self._risk_labels],
            "conclusion": self._conclusion,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CredibilityReport":
        """从字典反序列化创建 CredibilityReport

        Args:
            data: 包含所有属性的字典

        Returns:
            CredibilityReport 实例

        Raises:
            ValueError: 如果数据无效
            KeyError: 如果字典缺少必要的键
        """
        return cls(
            stock_code=StockCode(data["stock_code"]),
            stock_name=data["stock_name"],
            concept=data["concept"],
            overall_score=CredibilityScore.from_dict(data["overall_score"]),
            main_business_match=MainBusinessMatch.from_dict(data["main_business_match"]),
            evidence=EvidenceAnalysis.from_dict(data["evidence"]),
            hype_history=HypeHistory.from_dict(data["hype_history"]),
            supply_chain_logic=SupplyChainLogic.from_dict(data["supply_chain_logic"]),
            risk_labels=[RiskLabel(r) for r in data["risk_labels"]],
            conclusion=data["conclusion"],
        )

    def __eq__(self, other):
        """判断两个 CredibilityReport 是否相等"""
        return (
            isinstance(other, CredibilityReport)
            and self._stock_code == other._stock_code
            and self._stock_name == other._stock_name
            and self._concept == other._concept
            and self._overall_score == other._overall_score
            and self._main_business_match == other._main_business_match
            and self._evidence == other._evidence
            and self._hype_history == other._hype_history
            and self._supply_chain_logic == other._supply_chain_logic
            and self._risk_labels == other._risk_labels
            and self._conclusion == other._conclusion
        )

    def __hash__(self):
        """返回哈希值"""
        return hash((
            self._stock_code,
            self._stock_name,
            self._concept,
            self._overall_score,
            self._main_business_match,
            self._evidence,
            self._hype_history,
            self._supply_chain_logic,
            tuple(self._risk_labels),
            self._conclusion,
        ))

    def __repr__(self):
        """返回字符串表示"""
        return (
            f"CredibilityReport(stock_code={self._stock_code!r}, "
            f"stock_name='{self._stock_name}', "
            f"concept='{self._concept}', "
            f"overall_score={self._overall_score!r})"
        )
