"""值对象序列化 round-trip 属性基测试

# Feature: investment-intelligence-context, Property 9: 值对象序列化 round-trip

对于任意有效的 AgentStep、IndustryInsight、CredibilityReport、CredibilityScore、
StockCredibility、MainBusinessMatch、EvidenceAnalysis、HypeHistory、SupplyChainLogic
值对象，调用 to_dict() 然后 from_dict() 应产生与原始对象等价的值对象。

**Validates: Requirements 5.3, 5.4**
"""

from hypothesis import given, strategies as st, settings

from contexts.intelligence.domain.value_objects.credibility_score import CredibilityScore
from contexts.intelligence.domain.value_objects.agent_step import AgentStep
from contexts.intelligence.domain.value_objects.stock_credibility import StockCredibility
from contexts.intelligence.domain.value_objects.industry_insight import IndustryInsight
from contexts.intelligence.domain.value_objects.credibility_report import (
    MainBusinessMatch,
    EvidenceAnalysis,
    HypeHistory,
    SupplyChainLogic,
    CredibilityReport,
)
from contexts.intelligence.domain.enums.enums import AgentStepStatus, RiskLabel
from shared_kernel.value_objects.stock_code import StockCode


# === Hypothesis 自定义策略 ===

# CredibilityScore 生成器
valid_credibility_scores = st.builds(
    CredibilityScore, score=st.integers(min_value=0, max_value=100)
)

# 有效的 StockCode 生成器（遵循 A 股代码前缀规则）
valid_stock_codes = st.one_of(
    st.from_regex(r"(600|601|603|688)\d{3}\.SH", fullmatch=True),
    st.from_regex(r"(000|001|002|300)\d{3}\.SZ", fullmatch=True),
).map(StockCode)

# AgentStep 生成器
agent_steps = st.builds(
    AgentStep,
    agent_name=st.text(min_size=1, max_size=50),
    status=st.sampled_from(list(AgentStepStatus)),
    started_at=st.one_of(st.none(), st.datetimes()),
    completed_at=st.one_of(st.none(), st.datetimes()),
    output_summary=st.one_of(st.none(), st.text(max_size=200)),
    error_message=st.one_of(st.none(), st.text(max_size=200)),
)

# StockCredibility 生成器
stock_credibilities = st.builds(
    StockCredibility,
    stock_code=valid_stock_codes,
    stock_name=st.text(min_size=1, max_size=20),
    credibility_score=valid_credibility_scores,
    relevance_summary=st.text(min_size=1, max_size=200),
)

# 0-100 分数生成器
valid_scores = st.integers(min_value=0, max_value=100)

# MainBusinessMatch 生成器
main_business_matches = st.builds(
    MainBusinessMatch,
    score=valid_scores,
    main_business_description=st.text(min_size=1, max_size=200),
    match_analysis=st.text(min_size=1, max_size=200),
)

# EvidenceAnalysis 生成器
evidence_analyses = st.builds(
    EvidenceAnalysis,
    score=valid_scores,
    patents=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    orders=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    partnerships=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    analysis=st.text(min_size=1, max_size=200),
)

# HypeHistory 生成器
hype_histories = st.builds(
    HypeHistory,
    score=valid_scores,
    past_concepts=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    analysis=st.text(min_size=1, max_size=200),
)

# SupplyChainLogic 生成器
supply_chain_logics = st.builds(
    SupplyChainLogic,
    score=valid_scores,
    upstream=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    downstream=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    analysis=st.text(min_size=1, max_size=200),
)

# IndustryInsight 生成器
industry_insights = st.builds(
    IndustryInsight,
    industry_name=st.text(min_size=1, max_size=50),
    summary=st.text(min_size=1, max_size=200),
    industry_chain=st.text(min_size=1, max_size=200),
    technology_routes=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    market_size=st.text(min_size=1, max_size=100),
    top_stocks=st.lists(stock_credibilities, max_size=3),
    risk_alerts=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    catalysts=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    heat_score=st.integers(min_value=0, max_value=100),
    competitive_landscape=st.text(min_size=1, max_size=200),
)

# CredibilityReport 生成器
credibility_reports = st.builds(
    CredibilityReport,
    stock_code=valid_stock_codes,
    stock_name=st.text(min_size=1, max_size=20),
    concept=st.text(min_size=1, max_size=50),
    overall_score=valid_credibility_scores,
    main_business_match=main_business_matches,
    evidence=evidence_analyses,
    hype_history=hype_histories,
    supply_chain_logic=supply_chain_logics,
    risk_labels=st.lists(st.sampled_from(list(RiskLabel)), max_size=4),
    conclusion=st.text(min_size=1, max_size=200),
)


# === Property 9: 值对象序列化 round-trip 测试 ===


@settings(max_examples=100)
@given(cs=valid_credibility_scores)
def test_credibility_score_round_trip(cs):
    """CredibilityScore to_dict/from_dict round-trip 应产生等价对象。

    **Validates: Requirements 5.3, 5.4**
    """
    reconstructed = CredibilityScore.from_dict(cs.to_dict())
    assert reconstructed == cs


@settings(max_examples=100)
@given(step=agent_steps)
def test_agent_step_round_trip(step):
    """AgentStep to_dict/from_dict round-trip 应产生等价对象。

    **Validates: Requirements 5.3, 5.4**
    """
    reconstructed = AgentStep.from_dict(step.to_dict())
    assert reconstructed == step


@settings(max_examples=100)
@given(sc=stock_credibilities)
def test_stock_credibility_round_trip(sc):
    """StockCredibility to_dict/from_dict round-trip 应产生等价对象。

    **Validates: Requirements 5.3, 5.4**
    """
    reconstructed = StockCredibility.from_dict(sc.to_dict())
    assert reconstructed == sc


@settings(max_examples=100)
@given(mbm=main_business_matches)
def test_main_business_match_round_trip(mbm):
    """MainBusinessMatch to_dict/from_dict round-trip 应产生等价对象。

    **Validates: Requirements 5.3, 5.4**
    """
    reconstructed = MainBusinessMatch.from_dict(mbm.to_dict())
    assert reconstructed == mbm


@settings(max_examples=100)
@given(ea=evidence_analyses)
def test_evidence_analysis_round_trip(ea):
    """EvidenceAnalysis to_dict/from_dict round-trip 应产生等价对象。

    **Validates: Requirements 5.3, 5.4**
    """
    reconstructed = EvidenceAnalysis.from_dict(ea.to_dict())
    assert reconstructed == ea


@settings(max_examples=100)
@given(hh=hype_histories)
def test_hype_history_round_trip(hh):
    """HypeHistory to_dict/from_dict round-trip 应产生等价对象。

    **Validates: Requirements 5.3, 5.4**
    """
    reconstructed = HypeHistory.from_dict(hh.to_dict())
    assert reconstructed == hh


@settings(max_examples=100)
@given(scl=supply_chain_logics)
def test_supply_chain_logic_round_trip(scl):
    """SupplyChainLogic to_dict/from_dict round-trip 应产生等价对象。

    **Validates: Requirements 5.3, 5.4**
    """
    reconstructed = SupplyChainLogic.from_dict(scl.to_dict())
    assert reconstructed == scl


@settings(max_examples=100)
@given(insight=industry_insights)
def test_industry_insight_round_trip(insight):
    """IndustryInsight to_dict/from_dict round-trip 应产生等价对象。

    **Validates: Requirements 5.3, 5.4**
    """
    reconstructed = IndustryInsight.from_dict(insight.to_dict())
    assert reconstructed == insight


@settings(max_examples=100)
@given(report=credibility_reports)
def test_credibility_report_round_trip(report):
    """CredibilityReport to_dict/from_dict round-trip 应产生等价对象。

    **Validates: Requirements 5.3, 5.4**
    """
    reconstructed = CredibilityReport.from_dict(report.to_dict())
    assert reconstructed == report
