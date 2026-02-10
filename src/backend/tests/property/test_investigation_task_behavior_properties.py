"""InvestigationTask 行为属性基测试

Property 2: 空查询文本拒绝
对于任意仅由空白字符组成的字符串 s（包括空字符串），使用 s 作为 query 创建
InvestigationTask 应抛出 ValueError，且不会创建任何任务对象。

Property 7: update_progress 追加步骤不变量
对于任意 InvestigationTask 和任意 AgentStep 序列，每次调用
update_progress(progress, agent_step) 后，agent_steps 列表的长度应增加 1，
且最后一个元素应等于传入的 agent_step。

Property 8: duration 计算一致性
对于任意已完成（COMPLETED/FAILED/CANCELLED）的 InvestigationTask，duration 属性应等于
(completed_at - created_at).total_seconds()；对于任意未完成（PENDING/RUNNING）的
InvestigationTask，duration 应为 None。
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings

from contexts.intelligence.domain.models.investigation_task import InvestigationTask
from contexts.intelligence.domain.value_objects.identifiers import TaskId
from contexts.intelligence.domain.value_objects.agent_step import AgentStep
from contexts.intelligence.domain.value_objects.industry_insight import IndustryInsight
from contexts.intelligence.domain.enums.enums import TaskType, TaskStatus, AgentStepStatus


# === Hypothesis 自定义策略 ===

valid_task_ids = st.builds(lambda: TaskId.generate())

non_empty_queries = st.text(min_size=1, max_size=200).filter(lambda s: s.strip())

pending_tasks = st.builds(
    InvestigationTask,
    task_id=valid_task_ids,
    task_type=st.sampled_from(list(TaskType)),
    query=non_empty_queries,
)

# 空白字符查询策略：空字符串或仅由空白字符组成的字符串
whitespace_queries = st.one_of(
    st.just(""),
    st.text(
        alphabet=st.sampled_from([" ", "\t", "\n", "\r"]),
        min_size=0,
        max_size=20,
    ),
)

# AgentStep 策略
agent_steps = st.builds(
    AgentStep,
    agent_name=st.text(min_size=1, max_size=50),
    status=st.sampled_from(list(AgentStepStatus)),
    started_at=st.one_of(st.none(), st.datetimes()),
    completed_at=st.one_of(st.none(), st.datetimes()),
    output_summary=st.one_of(st.none(), st.text(max_size=200)),
    error_message=st.one_of(st.none(), st.text(max_size=200)),
)

# 进度值策略
progress_values = st.integers(min_value=0, max_value=100)

# 用于 complete() 的最小有效 IndustryInsight
valid_industry_insights = st.builds(
    IndustryInsight,
    industry_name=st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
    summary=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
    industry_chain=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
    technology_routes=st.lists(
        st.text(min_size=1, max_size=30).filter(lambda s: s.strip()),
        min_size=1,
        max_size=3,
    ),
    market_size=st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
    top_stocks=st.just([]),
    risk_alerts=st.lists(
        st.text(min_size=1, max_size=30).filter(lambda s: s.strip()),
        max_size=2,
    ),
    catalysts=st.lists(
        st.text(min_size=1, max_size=30).filter(lambda s: s.strip()),
        max_size=2,
    ),
    heat_score=st.integers(min_value=0, max_value=100),
    competitive_landscape=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
)

# 正的时间差策略（用于 duration 测试）
positive_timedeltas = st.timedeltas(
    min_value=timedelta(seconds=1),
    max_value=timedelta(days=30),
)


# ============================================================
# Feature: investment-intelligence-context, Property 2: 空查询文本拒绝
# **Validates: Requirements 1.11**
# ============================================================


@settings(max_examples=100)
@given(
    task_id=valid_task_ids,
    task_type=st.sampled_from(list(TaskType)),
    query=whitespace_queries,
)
def test_empty_or_whitespace_query_raises_value_error(task_id, task_type, query):
    """Property 2: 对于任意仅由空白字符组成的字符串（包括空字符串），
    使用其作为 query 创建 InvestigationTask 应抛出 ValueError。

    **Validates: Requirements 1.11**
    """
    with pytest.raises(ValueError):
        InvestigationTask(task_id=task_id, task_type=task_type, query=query)


# ============================================================
# Feature: investment-intelligence-context, Property 7: update_progress 追加步骤不变量
# **Validates: Requirements 3.3**
# ============================================================


@settings(max_examples=100)
@given(
    task=pending_tasks,
    step=agent_steps,
    progress=progress_values,
)
def test_update_progress_appends_single_step(task, step, progress):
    """Property 7 (单步): 调用 update_progress 后，agent_steps 长度增加 1，
    且最后一个元素等于传入的 agent_step。

    **Validates: Requirements 3.3**
    """
    original_length = len(task.agent_steps)

    task.update_progress(progress, step)

    assert len(task.agent_steps) == original_length + 1
    assert task.agent_steps[-1] == step


@settings(max_examples=100)
@given(
    task=pending_tasks,
    steps=st.lists(agent_steps, min_size=1, max_size=10),
    progresses=st.lists(progress_values, min_size=1, max_size=10),
)
def test_update_progress_appends_sequence_of_steps(task, steps, progresses):
    """Property 7 (序列): 对于任意 AgentStep 序列，每次调用 update_progress 后，
    agent_steps 列表的长度应增加 1，且最后一个元素应等于传入的 agent_step。

    **Validates: Requirements 3.3**
    """
    # Use the shorter of the two lists to pair them
    pairs = list(zip(progresses, steps))

    for i, (prog, step) in enumerate(pairs):
        length_before = len(task.agent_steps)

        task.update_progress(prog, step)

        assert len(task.agent_steps) == length_before + 1
        assert task.agent_steps[-1] == step


# ============================================================
# Feature: investment-intelligence-context, Property 8: duration 计算一致性
# **Validates: Requirements 3.8**
# ============================================================


@settings(max_examples=100)
@given(task=pending_tasks)
def test_duration_is_none_for_pending_task(task):
    """Property 8 (PENDING): 未完成的 PENDING 任务，duration 应为 None。

    **Validates: Requirements 3.8**
    """
    assert task.status == TaskStatus.PENDING
    assert task.duration is None


@settings(max_examples=100)
@given(task=pending_tasks)
def test_duration_is_none_for_running_task(task):
    """Property 8 (RUNNING): 未完成的 RUNNING 任务，duration 应为 None。

    **Validates: Requirements 3.8**
    """
    task.start()
    assert task.status == TaskStatus.RUNNING
    assert task.duration is None


@settings(max_examples=100)
@given(
    task_id=valid_task_ids,
    task_type=st.sampled_from(list(TaskType)),
    query=non_empty_queries,
    created_at=st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 1, 1),
    ),
    delta=positive_timedeltas,
    result=valid_industry_insights,
)
def test_duration_equals_time_diff_for_completed_task(
    task_id, task_type, query, created_at, delta, result
):
    """Property 8 (COMPLETED): 已完成任务的 duration 应等于
    (completed_at - created_at).total_seconds()。

    **Validates: Requirements 3.8**
    """
    completed_at = created_at + delta

    task = InvestigationTask(
        task_id=task_id,
        task_type=task_type,
        query=query,
        status=TaskStatus.COMPLETED,
        progress=100,
        result=result,
        created_at=created_at,
        completed_at=completed_at,
    )

    expected_duration = (completed_at - created_at).total_seconds()
    assert task.duration == expected_duration


@settings(max_examples=100)
@given(
    task_id=valid_task_ids,
    task_type=st.sampled_from(list(TaskType)),
    query=non_empty_queries,
    created_at=st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 1, 1),
    ),
    delta=positive_timedeltas,
    error_msg=st.text(min_size=1, max_size=200).filter(lambda s: s.strip()),
)
def test_duration_equals_time_diff_for_failed_task(
    task_id, task_type, query, created_at, delta, error_msg
):
    """Property 8 (FAILED): 失败任务的 duration 应等于
    (completed_at - created_at).total_seconds()。

    **Validates: Requirements 3.8**
    """
    completed_at = created_at + delta

    task = InvestigationTask(
        task_id=task_id,
        task_type=task_type,
        query=query,
        status=TaskStatus.FAILED,
        error_message=error_msg,
        created_at=created_at,
        completed_at=completed_at,
    )

    expected_duration = (completed_at - created_at).total_seconds()
    assert task.duration == expected_duration


@settings(max_examples=100)
@given(
    task_id=valid_task_ids,
    task_type=st.sampled_from(list(TaskType)),
    query=non_empty_queries,
    created_at=st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 1, 1),
    ),
    delta=positive_timedeltas,
)
def test_duration_equals_time_diff_for_cancelled_task(
    task_id, task_type, query, created_at, delta
):
    """Property 8 (CANCELLED): 已取消任务的 duration 应等于
    (completed_at - created_at).total_seconds()。

    **Validates: Requirements 3.8**
    """
    completed_at = created_at + delta

    task = InvestigationTask(
        task_id=task_id,
        task_type=task_type,
        query=query,
        status=TaskStatus.CANCELLED,
        created_at=created_at,
        completed_at=completed_at,
    )

    expected_duration = (completed_at - created_at).total_seconds()
    assert task.duration == expected_duration
