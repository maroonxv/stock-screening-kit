"""InvestigationTask Repository round-trip 属性基测试

# Feature: investment-intelligence-context, Property 10: InvestigationTask 持久化 round-trip

对于任意有效的 InvestigationTask（包含 IndustryInsight 或 CredibilityReport 类型的 result），
通过 Repository 保存后按 ID 检索，应返回与原始对象等价的领域对象，包含所有嵌套的值对象。

**Validates: Requirements 5.3**

这是一个集成测试，使用 SQLite 内存数据库进行测试。
通过 SQLAlchemy 编译器扩展将 JSONB 类型映射为 JSON，使 SQLite 兼容。
"""

import json
from datetime import datetime

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from flask import Flask
from sqlalchemy import JSON, event, types
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

from app import db
from contexts.intelligence.domain.models.investigation_task import InvestigationTask
from contexts.intelligence.domain.value_objects.identifiers import TaskId
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
from contexts.intelligence.domain.enums.enums import (
    TaskType,
    TaskStatus,
    AgentStepStatus,
    RiskLabel,
)
from contexts.intelligence.infrastructure.persistence.repositories.investigation_task_repository_impl import (
    InvestigationTaskRepositoryImpl,
)
from contexts.intelligence.infrastructure.persistence.models.investigation_task_po import (
    InvestigationTaskPO,
)
from shared_kernel.value_objects.stock_code import StockCode


# === SQLite 兼容：将 JSONB 编译为 JSON（仅在 SQLite 方言下生效） ===
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


# === 测试用 Flask 应用 ===
def _create_test_app():
    """创建测试用 Flask 应用，使用 SQLite 内存数据库"""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True
    db.init_app(app)
    return app


_test_app = _create_test_app()


# === Hypothesis 自定义策略 ===

# 不含 NUL 字符的安全文本（SQLite/JSON 兼容），且不能为纯空白字符
safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip())
safe_text_optional = st.one_of(
    st.none(),
    st.text(
        alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
        max_size=100,
    ),
)

# 固定精度 datetime（SQLite 存储精度有限，截断微秒）
safe_datetimes = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
).map(lambda dt: dt.replace(microsecond=0))

# 有效的 StockCode 生成器
valid_stock_codes = st.one_of(
    st.from_regex(r"(600|601|603|688)\d{3}\.SH", fullmatch=True),
    st.from_regex(r"(000|001|002|300)\d{3}\.SZ", fullmatch=True),
).map(StockCode)

# CredibilityScore 生成器
valid_credibility_scores = st.builds(
    CredibilityScore, score=st.integers(min_value=0, max_value=100)
)

# 0-100 分数生成器
valid_scores = st.integers(min_value=0, max_value=100)

# AgentStep 生成器
agent_steps_strategy = st.builds(
    AgentStep,
    agent_name=safe_text,
    status=st.sampled_from(list(AgentStepStatus)),
    started_at=st.one_of(st.none(), safe_datetimes),
    completed_at=st.one_of(st.none(), safe_datetimes),
    output_summary=safe_text_optional,
    error_message=safe_text_optional,
)

# StockCredibility 生成器
stock_credibilities = st.builds(
    StockCredibility,
    stock_code=valid_stock_codes,
    stock_name=safe_text,
    credibility_score=valid_credibility_scores,
    relevance_summary=safe_text,
)

# MainBusinessMatch 生成器
main_business_matches = st.builds(
    MainBusinessMatch,
    score=valid_scores,
    main_business_description=safe_text,
    match_analysis=safe_text,
)

# EvidenceAnalysis 生成器
evidence_analyses = st.builds(
    EvidenceAnalysis,
    score=valid_scores,
    patents=st.lists(safe_text, max_size=3),
    orders=st.lists(safe_text, max_size=3),
    partnerships=st.lists(safe_text, max_size=3),
    analysis=safe_text,
)

# HypeHistory 生成器
hype_histories = st.builds(
    HypeHistory,
    score=valid_scores,
    past_concepts=st.lists(safe_text, max_size=3),
    analysis=safe_text,
)

# SupplyChainLogic 生成器
supply_chain_logics = st.builds(
    SupplyChainLogic,
    score=valid_scores,
    upstream=st.lists(safe_text, max_size=3),
    downstream=st.lists(safe_text, max_size=3),
    analysis=safe_text,
)

# IndustryInsight 生成器
industry_insights = st.builds(
    IndustryInsight,
    industry_name=safe_text,
    summary=safe_text,
    industry_chain=safe_text,
    technology_routes=st.lists(safe_text, max_size=3),
    market_size=safe_text,
    top_stocks=st.lists(stock_credibilities, max_size=2),
    risk_alerts=st.lists(safe_text, max_size=3),
    catalysts=st.lists(safe_text, max_size=3),
    heat_score=st.integers(min_value=0, max_value=100),
    competitive_landscape=safe_text,
)

# CredibilityReport 生成器
credibility_reports = st.builds(
    CredibilityReport,
    stock_code=valid_stock_codes,
    stock_name=safe_text,
    concept=safe_text,
    overall_score=valid_credibility_scores,
    main_business_match=main_business_matches,
    evidence=evidence_analyses,
    hype_history=hype_histories,
    supply_chain_logic=supply_chain_logics,
    risk_labels=st.lists(st.sampled_from(list(RiskLabel)), max_size=3),
    conclusion=safe_text,
)


# === 辅助函数 ===

def _make_completed_task_with_result(task_type, result):
    """创建一个 COMPLETED 状态的 InvestigationTask，包含指定的 result。

    手动构造已完成的任务，避免调用 start()/complete() 引入的时间不确定性。
    """
    now = datetime(2025, 6, 15, 12, 0, 0)
    completed = datetime(2025, 6, 15, 12, 30, 0)
    query = "test query for round-trip"
    if task_type == TaskType.CREDIBILITY_VERIFICATION and isinstance(result, CredibilityReport):
        query = f"{result.stock_code.code}:{result.concept}"

    return InvestigationTask(
        task_id=TaskId.generate(),
        task_type=task_type,
        query=query,
        status=TaskStatus.COMPLETED,
        progress=100,
        agent_steps=[],
        result=result,
        error_message=None,
        created_at=now,
        updated_at=completed,
        completed_at=completed,
    )


def _assert_tasks_equivalent(original: InvestigationTask, loaded: InvestigationTask):
    """断言两个 InvestigationTask 在领域层语义上等价。

    比较所有标量属性、嵌套值对象（agent_steps、result）。
    datetime 比较截断到秒级精度（SQLite 存储限制）。
    """
    assert loaded.task_id == original.task_id
    assert loaded.task_type == original.task_type
    assert loaded.query == original.query
    assert loaded.status == original.status
    assert loaded.progress == original.progress
    assert loaded.error_message == original.error_message

    # datetime 比较 - 截断到秒级精度
    assert loaded.created_at.replace(microsecond=0) == original.created_at.replace(microsecond=0)
    assert loaded.updated_at.replace(microsecond=0) == original.updated_at.replace(microsecond=0)
    if original.completed_at is not None:
        assert loaded.completed_at is not None
        assert loaded.completed_at.replace(microsecond=0) == original.completed_at.replace(microsecond=0)
    else:
        assert loaded.completed_at is None

    # agent_steps 比较
    assert len(loaded.agent_steps) == len(original.agent_steps)
    for loaded_step, orig_step in zip(loaded.agent_steps, original.agent_steps):
        assert loaded_step == orig_step

    # result 比较 - 使用 to_dict 进行深度比较
    if original.result is None:
        assert loaded.result is None
    else:
        assert type(loaded.result) == type(original.result)
        assert loaded.result.to_dict() == original.result.to_dict()


# === Fixtures ===

@pytest.fixture
def db_session():
    """提供一个干净的数据库会话用于每个测试。

    每次测试前创建所有表，测试后删除所有表，确保隔离性。
    """
    with _test_app.app_context():
        db.create_all()
        session = db.session
        yield session
        session.rollback()
        db.drop_all()


@pytest.fixture
def repository(db_session):
    """提供一个 InvestigationTaskRepositoryImpl 实例。"""
    return InvestigationTaskRepositoryImpl(db_session)


# === Property 10: InvestigationTask 持久化 round-trip 测试 ===


@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(insight=industry_insights)
def test_roundtrip_with_industry_insight(db_session, repository, insight):
    """对于任意有效的 InvestigationTask（包含 IndustryInsight result），
    通过 Repository 保存后按 ID 检索，应返回等价的领域对象。

    **Validates: Requirements 5.3**
    """
    task = _make_completed_task_with_result(TaskType.INDUSTRY_RESEARCH, insight)

    # Save
    repository.save(task)
    db_session.commit()

    # Retrieve
    loaded = repository.find_by_id(task.task_id)

    # Assert equivalence
    assert loaded is not None
    _assert_tasks_equivalent(task, loaded)

    # Cleanup for next hypothesis iteration
    repository.delete(task.task_id)
    db_session.commit()


@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(report=credibility_reports)
def test_roundtrip_with_credibility_report(db_session, repository, report):
    """对于任意有效的 InvestigationTask（包含 CredibilityReport result），
    通过 Repository 保存后按 ID 检索，应返回等价的领域对象。

    **Validates: Requirements 5.3**
    """
    task = _make_completed_task_with_result(TaskType.CREDIBILITY_VERIFICATION, report)

    # Save
    repository.save(task)
    db_session.commit()

    # Retrieve
    loaded = repository.find_by_id(task.task_id)

    # Assert equivalence
    assert loaded is not None
    _assert_tasks_equivalent(task, loaded)

    # Cleanup for next hypothesis iteration
    repository.delete(task.task_id)
    db_session.commit()


@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(
    insight=industry_insights,
    steps=st.lists(agent_steps_strategy, min_size=1, max_size=3),
)
def test_roundtrip_with_agent_steps(db_session, repository, insight, steps):
    """对于任意有效的 InvestigationTask（包含 agent_steps 和 IndustryInsight result），
    通过 Repository 保存后按 ID 检索，应返回等价的领域对象，包含所有嵌套的 AgentStep。

    **Validates: Requirements 5.3**
    """
    now = datetime(2025, 6, 15, 12, 0, 0)
    completed = datetime(2025, 6, 15, 12, 30, 0)

    task = InvestigationTask(
        task_id=TaskId.generate(),
        task_type=TaskType.INDUSTRY_RESEARCH,
        query="test query with agent steps",
        status=TaskStatus.COMPLETED,
        progress=100,
        agent_steps=steps,
        result=insight,
        error_message=None,
        created_at=now,
        updated_at=completed,
        completed_at=completed,
    )

    # Save
    repository.save(task)
    db_session.commit()

    # Retrieve
    loaded = repository.find_by_id(task.task_id)

    # Assert equivalence
    assert loaded is not None
    _assert_tasks_equivalent(task, loaded)

    # Cleanup
    repository.delete(task.task_id)
    db_session.commit()


@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
@given(data=st.data())
def test_roundtrip_pending_task_without_result(db_session, repository, data):
    """对于任意有效的 PENDING 状态 InvestigationTask（无 result），
    通过 Repository 保存后按 ID 检索，应返回等价的领域对象。

    **Validates: Requirements 5.3**
    """
    task_type = data.draw(st.sampled_from(list(TaskType)))
    query = data.draw(safe_text)

    now = datetime(2025, 6, 15, 12, 0, 0)

    task = InvestigationTask(
        task_id=TaskId.generate(),
        task_type=task_type,
        query=query,
        status=TaskStatus.PENDING,
        progress=0,
        agent_steps=[],
        result=None,
        error_message=None,
        created_at=now,
        updated_at=now,
        completed_at=None,
    )

    # Save
    repository.save(task)
    db_session.commit()

    # Retrieve
    loaded = repository.find_by_id(task.task_id)

    # Assert equivalence
    assert loaded is not None
    _assert_tasks_equivalent(task, loaded)

    # Cleanup
    repository.delete(task.task_id)
    db_session.commit()
