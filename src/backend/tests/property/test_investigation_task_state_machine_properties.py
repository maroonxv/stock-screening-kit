"""InvestigationTask 状态机属性基测试

Property 4: start() 状态机
对于任意 InvestigationTask，如果其 status 为 PENDING，则调用 start() 应将 status 转换为 RUNNING；
如果其 status 不是 PENDING（即 RUNNING、COMPLETED、FAILED、CANCELLED 中的任一），
则调用 start() 应抛出 InvalidTaskStateError，且 status 保持不变。

Property 5: complete() 状态机
对于任意 InvestigationTask，如果其 status 为 RUNNING，则调用 complete(result) 应将 status 设为
COMPLETED、progress 设为 100、result 设为传入的值、completed_at 不为 None；
如果其 status 不是 RUNNING，则调用 complete() 应抛出 InvalidTaskStateError，且 status 和 result 保持不变。

Property 6: fail/cancel 终态转换
对于任意 RUNNING 状态的 InvestigationTask，调用 fail(error_message) 应将 status 设为 FAILED
且 error_message 被保存；对于任意 PENDING 或 RUNNING 状态的 InvestigationTask，调用 cancel()
应将 status 设为 CANCELLED 且 completed_at 不为 None。
"""

import pytest
from hypothesis import given, strategies as st, settings

from contexts.intelligence.domain.models.investigation_task import InvestigationTask
from contexts.intelligence.domain.value_objects.identifiers import TaskId
from contexts.intelligence.domain.value_objects.credibility_score import CredibilityScore
from contexts.intelligence.domain.value_objects.stock_credibility import StockCredibility
from contexts.intelligence.domain.value_objects.industry_insight import IndustryInsight
from contexts.intelligence.domain.enums.enums import TaskType, TaskStatus
from contexts.intelligence.domain.exceptions import InvalidTaskStateError
from shared_kernel.value_objects.stock_code import StockCode


# === Hypothesis 自定义策略 ===

valid_task_ids = st.builds(lambda: TaskId.generate())

non_empty_queries = st.text(min_size=1, max_size=200).filter(lambda s: s.strip())

pending_tasks = st.builds(
    InvestigationTask,
    task_id=valid_task_ids,
    task_type=st.sampled_from(list(TaskType)),
    query=non_empty_queries,
)


def make_running_task(task_id, task_type, query):
    """Helper: create a PENDING task and transition it to RUNNING."""
    task = InvestigationTask(task_id=task_id, task_type=task_type, query=query)
    task.start()
    return task


running_tasks = st.builds(
    make_running_task,
    task_id=valid_task_ids,
    task_type=st.sampled_from(list(TaskType)),
    query=non_empty_queries,
)

# Strategy for building a minimal valid IndustryInsight as a result
valid_industry_insights = st.builds(
    IndustryInsight,
    industry_name=st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
    summary=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
    industry_chain=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
    technology_routes=st.lists(st.text(min_size=1, max_size=30).filter(lambda s: s.strip()), min_size=1, max_size=3),
    market_size=st.text(min_size=1, max_size=50).filter(lambda s: s.strip()),
    top_stocks=st.just([]),
    risk_alerts=st.lists(st.text(min_size=1, max_size=30).filter(lambda s: s.strip()), max_size=2),
    catalysts=st.lists(st.text(min_size=1, max_size=30).filter(lambda s: s.strip()), max_size=2),
    heat_score=st.integers(min_value=0, max_value=100),
    competitive_landscape=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
)

error_messages = st.text(min_size=1, max_size=200).filter(lambda s: s.strip())

# Non-PENDING statuses for Property 4 negative tests
non_pending_statuses = [TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]

# Non-RUNNING statuses for Property 5 negative tests
non_running_statuses = [TaskStatus.PENDING, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]


# ============================================================
# Feature: investment-intelligence-context, Property 4: start() 状态机
# **Validates: Requirements 3.1, 3.2**
# ============================================================


@settings(max_examples=100)
@given(task=pending_tasks)
def test_start_from_pending_transitions_to_running(task):
    """Property 4 (正向): PENDING 状态的任务调用 start() 应转换为 RUNNING。

    **Validates: Requirements 3.1, 3.2**
    """
    assert task.status == TaskStatus.PENDING
    task.start()
    assert task.status == TaskStatus.RUNNING


@settings(max_examples=100)
@given(
    task_id=valid_task_ids,
    task_type=st.sampled_from(list(TaskType)),
    query=non_empty_queries,
    target_status=st.sampled_from(non_pending_statuses),
)
def test_start_from_non_pending_raises_error(task_id, task_type, query, target_status):
    """Property 4 (反向): 非 PENDING 状态的任务调用 start() 应抛出 InvalidTaskStateError，
    且 status 保持不变。

    **Validates: Requirements 3.1, 3.2**
    """
    # Build a task and transition it to the target non-PENDING status
    task = InvestigationTask(task_id=task_id, task_type=task_type, query=query)

    if target_status == TaskStatus.RUNNING:
        task.start()
    elif target_status == TaskStatus.COMPLETED:
        task.start()
        result = IndustryInsight(
            industry_name="test", summary="test", industry_chain="test",
            technology_routes=["test"], market_size="test", top_stocks=[],
            risk_alerts=[], catalysts=[], heat_score=50,
            competitive_landscape="test",
        )
        task.complete(result)
    elif target_status == TaskStatus.FAILED:
        task.start()
        task.fail("test error")
    elif target_status == TaskStatus.CANCELLED:
        task.cancel()

    assert task.status == target_status
    original_status = task.status

    with pytest.raises(InvalidTaskStateError):
        task.start()

    # Status must remain unchanged after the failed call
    assert task.status == original_status


# ============================================================
# Feature: investment-intelligence-context, Property 5: complete() 状态机
# **Validates: Requirements 3.4, 3.5**
# ============================================================


@settings(max_examples=100)
@given(task=running_tasks, result=valid_industry_insights)
def test_complete_from_running_transitions_to_completed(task, result):
    """Property 5 (正向): RUNNING 状态的任务调用 complete(result) 应将 status 设为 COMPLETED，
    progress 设为 100，result 设为传入的值，completed_at 不为 None。

    **Validates: Requirements 3.4, 3.5**
    """
    assert task.status == TaskStatus.RUNNING
    task.complete(result)

    assert task.status == TaskStatus.COMPLETED
    assert task.progress == 100
    assert task.result is result
    assert task.completed_at is not None


@settings(max_examples=100)
@given(
    task_id=valid_task_ids,
    task_type=st.sampled_from(list(TaskType)),
    query=non_empty_queries,
    target_status=st.sampled_from(non_running_statuses),
    result=valid_industry_insights,
)
def test_complete_from_non_running_raises_error(task_id, task_type, query, target_status, result):
    """Property 5 (反向): 非 RUNNING 状态的任务调用 complete() 应抛出 InvalidTaskStateError，
    且 status 和 result 保持不变。

    **Validates: Requirements 3.4, 3.5**
    """
    task = InvestigationTask(task_id=task_id, task_type=task_type, query=query)

    if target_status == TaskStatus.PENDING:
        pass  # already PENDING
    elif target_status == TaskStatus.COMPLETED:
        task.start()
        dummy_result = IndustryInsight(
            industry_name="dummy", summary="dummy", industry_chain="dummy",
            technology_routes=["dummy"], market_size="dummy", top_stocks=[],
            risk_alerts=[], catalysts=[], heat_score=50,
            competitive_landscape="dummy",
        )
        task.complete(dummy_result)
    elif target_status == TaskStatus.FAILED:
        task.start()
        task.fail("test error")
    elif target_status == TaskStatus.CANCELLED:
        task.cancel()

    assert task.status == target_status
    original_status = task.status
    original_result = task.result

    with pytest.raises(InvalidTaskStateError):
        task.complete(result)

    # Status and result must remain unchanged after the failed call
    assert task.status == original_status
    assert task.result is original_result


# ============================================================
# Feature: investment-intelligence-context, Property 6: fail/cancel 终态转换
# **Validates: Requirements 3.6, 3.7**
# ============================================================


@settings(max_examples=100)
@given(task=running_tasks, error_msg=error_messages)
def test_fail_from_running_transitions_to_failed(task, error_msg):
    """Property 6 (fail): RUNNING 状态的任务调用 fail(error_message) 应将 status 设为 FAILED，
    且 error_message 被保存。

    **Validates: Requirements 3.6, 3.7**
    """
    assert task.status == TaskStatus.RUNNING
    task.fail(error_msg)

    assert task.status == TaskStatus.FAILED
    assert task.error_message == error_msg
    assert task.completed_at is not None


@settings(max_examples=100)
@given(task=pending_tasks)
def test_cancel_from_pending_transitions_to_cancelled(task):
    """Property 6 (cancel - PENDING): PENDING 状态的任务调用 cancel() 应将 status 设为 CANCELLED，
    且 completed_at 不为 None。

    **Validates: Requirements 3.6, 3.7**
    """
    assert task.status == TaskStatus.PENDING
    task.cancel()

    assert task.status == TaskStatus.CANCELLED
    assert task.completed_at is not None


@settings(max_examples=100)
@given(task=running_tasks)
def test_cancel_from_running_transitions_to_cancelled(task):
    """Property 6 (cancel - RUNNING): RUNNING 状态的任务调用 cancel() 应将 status 设为 CANCELLED，
    且 completed_at 不为 None。

    **Validates: Requirements 3.6, 3.7**
    """
    assert task.status == TaskStatus.RUNNING
    task.cancel()

    assert task.status == TaskStatus.CANCELLED
    assert task.completed_at is not None
