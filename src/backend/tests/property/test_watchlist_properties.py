"""
Property-based tests for WatchList aggregate root

Feature: stock-screening-platform
Property 2: WatchList 不允许重复添加
Property 3: WatchList 移除不存在的股票应报错

**Validates: Requirements 2.8, 2.9**

Property Descriptions:
- Property 2: 对于任意 WatchList 和任意 StockCode，如果该 StockCode 已存在于 WatchList 中，
  则再次调用 add_stock() 应抛出 DuplicateStockError，且 WatchList 的股票数量保持不变。
  
- Property 3: 对于任意 WatchList 和任意 StockCode，如果该 StockCode 不在 WatchList 中，
  则调用 remove_stock() 应抛出 StockNotFoundError，且 WatchList 的股票数量保持不变。
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

from shared_kernel.value_objects.stock_code import StockCode
from contexts.screening.domain.models.watchlist import WatchList
from contexts.screening.domain.value_objects.identifiers import WatchListId
from contexts.screening.domain.exceptions import DuplicateStockError, StockNotFoundError


# =============================================================================
# Custom Strategies (Generators)
# =============================================================================

# Valid stock code generator
valid_stock_codes = st.from_regex(r'^\d{6}\.(SH|SZ)$', fullmatch=True).map(StockCode)

# Stock name generator
stock_names = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-'),
    min_size=1,
    max_size=20
).filter(lambda s: s.strip())

# WatchList name generator
watchlist_names = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_- '),
    min_size=1,
    max_size=50
).filter(lambda s: s.strip())


@composite
def empty_watchlist_strategy(draw):
    """
    生成一个空的 WatchList
    """
    name = draw(watchlist_names)
    return WatchList(
        watchlist_id=WatchListId.generate(),
        name=name,
        description=None,
        stocks=None
    )


@composite
def watchlist_with_stocks_strategy(draw, min_stocks=1, max_stocks=5):
    """
    生成一个包含若干股票的 WatchList
    
    Args:
        min_stocks: 最少股票数量
        max_stocks: 最多股票数量
    """
    name = draw(watchlist_names)
    watchlist = WatchList(
        watchlist_id=WatchListId.generate(),
        name=name,
        description=None,
        stocks=None
    )
    
    # 生成不重复的股票代码
    num_stocks = draw(st.integers(min_value=min_stocks, max_value=max_stocks))
    stock_codes_set = set()
    
    while len(stock_codes_set) < num_stocks:
        code_str = draw(st.from_regex(r'^\d{6}\.(SH|SZ)$', fullmatch=True))
        stock_codes_set.add(code_str)
    
    # 添加股票到 WatchList
    for code_str in stock_codes_set:
        stock_code = StockCode(code_str)
        stock_name = draw(stock_names)
        watchlist.add_stock(stock_code, stock_name)
    
    return watchlist


@composite
def watchlist_and_existing_stock_strategy(draw):
    """
    生成一个 WatchList 和其中已存在的一个 StockCode
    """
    watchlist = draw(watchlist_with_stocks_strategy(min_stocks=1, max_stocks=5))
    
    # 从已有股票中选择一个
    existing_stocks = watchlist.stocks
    selected_stock = draw(st.sampled_from(existing_stocks))
    
    return watchlist, selected_stock.stock_code


@composite
def watchlist_and_non_existing_stock_strategy(draw):
    """
    生成一个 WatchList 和一个不在其中的 StockCode
    """
    watchlist = draw(watchlist_with_stocks_strategy(min_stocks=0, max_stocks=5))
    
    # 获取已有股票代码集合
    existing_codes = {s.stock_code.code for s in watchlist.stocks}
    
    # 生成一个不在列表中的股票代码
    new_code_str = draw(st.from_regex(r'^\d{6}\.(SH|SZ)$', fullmatch=True))
    assume(new_code_str not in existing_codes)
    
    return watchlist, StockCode(new_code_str)


# =============================================================================
# Property 2: WatchList 不允许重复添加
# **Validates: Requirements 2.8**
# =============================================================================

@settings(max_examples=100)
@given(data=watchlist_and_existing_stock_strategy())
def test_duplicate_add_raises_error(data):
    """
    Property 2.1: 重复添加已存在的股票应抛出 DuplicateStockError
    
    **Validates: Requirements 2.8**
    
    对于任意 WatchList 和任意 StockCode，如果该 StockCode 已存在于 WatchList 中，
    则再次调用 add_stock() 应抛出 DuplicateStockError
    """
    watchlist, existing_stock_code = data
    
    # 验证股票确实存在
    assert watchlist.contains(existing_stock_code), \
        f"股票 {existing_stock_code.code} 应该已存在于列表中"
    
    # 尝试重复添加应抛出 DuplicateStockError
    with pytest.raises(DuplicateStockError):
        watchlist.add_stock(existing_stock_code, "重复股票名称")


@settings(max_examples=100)
@given(data=watchlist_and_existing_stock_strategy())
def test_duplicate_add_preserves_stock_count(data):
    """
    Property 2.2: 重复添加失败后股票数量保持不变
    
    **Validates: Requirements 2.8**
    
    对于任意 WatchList 和任意 StockCode，如果该 StockCode 已存在于 WatchList 中，
    则再次调用 add_stock() 后，WatchList 的股票数量应保持不变
    """
    watchlist, existing_stock_code = data
    
    # 记录添加前的股票数量
    count_before = watchlist.stock_count()
    
    # 尝试重复添加（应该失败）
    try:
        watchlist.add_stock(existing_stock_code, "重复股票名称")
    except DuplicateStockError:
        pass
    
    # 股票数量应保持不变
    count_after = watchlist.stock_count()
    assert count_after == count_before, \
        f"股票数量应保持不变，期望 {count_before}，实际 {count_after}"


@settings(max_examples=100)
@given(
    watchlist=empty_watchlist_strategy(),
    stock_code=valid_stock_codes,
    stock_name=stock_names
)
def test_add_then_duplicate_add_raises_error(watchlist, stock_code, stock_name):
    """
    Property 2.3: 先添加再重复添加应抛出 DuplicateStockError
    
    **Validates: Requirements 2.8**
    
    对于任意空 WatchList，先添加一个股票，然后再次添加同一股票，
    第二次添加应抛出 DuplicateStockError
    """
    # 第一次添加应成功
    watchlist.add_stock(stock_code, stock_name)
    assert watchlist.contains(stock_code)
    assert watchlist.stock_count() == 1
    
    # 第二次添加应失败
    with pytest.raises(DuplicateStockError):
        watchlist.add_stock(stock_code, "另一个名称")
    
    # 股票数量仍为 1
    assert watchlist.stock_count() == 1


@settings(max_examples=100)
@given(data=watchlist_and_existing_stock_strategy())
def test_duplicate_add_does_not_modify_existing_stock(data):
    """
    Property 2.4: 重复添加失败后不应修改已存在的股票信息
    
    **Validates: Requirements 2.8**
    
    对于任意 WatchList 和任意已存在的 StockCode，重复添加失败后，
    原有股票的信息应保持不变
    """
    watchlist, existing_stock_code = data
    
    # 获取原有股票信息
    original_stock = watchlist.get_stock(existing_stock_code)
    original_name = original_stock.stock_name
    original_added_at = original_stock.added_at
    
    # 尝试重复添加（应该失败）
    try:
        watchlist.add_stock(existing_stock_code, "新名称", note="新备注")
    except DuplicateStockError:
        pass
    
    # 原有股票信息应保持不变
    current_stock = watchlist.get_stock(existing_stock_code)
    assert current_stock.stock_name == original_name, \
        "股票名称不应被修改"
    assert current_stock.added_at == original_added_at, \
        "添加时间不应被修改"


# =============================================================================
# Property 3: WatchList 移除不存在的股票应报错
# **Validates: Requirements 2.9**
# =============================================================================

@settings(max_examples=100)
@given(data=watchlist_and_non_existing_stock_strategy())
def test_remove_non_existing_raises_error(data):
    """
    Property 3.1: 移除不存在的股票应抛出 StockNotFoundError
    
    **Validates: Requirements 2.9**
    
    对于任意 WatchList 和任意 StockCode，如果该 StockCode 不在 WatchList 中，
    则调用 remove_stock() 应抛出 StockNotFoundError
    """
    watchlist, non_existing_stock_code = data
    
    # 验证股票确实不存在
    assert not watchlist.contains(non_existing_stock_code), \
        f"股票 {non_existing_stock_code.code} 不应存在于列表中"
    
    # 尝试移除不存在的股票应抛出 StockNotFoundError
    with pytest.raises(StockNotFoundError):
        watchlist.remove_stock(non_existing_stock_code)


@settings(max_examples=100)
@given(data=watchlist_and_non_existing_stock_strategy())
def test_remove_non_existing_preserves_stock_count(data):
    """
    Property 3.2: 移除不存在的股票失败后股票数量保持不变
    
    **Validates: Requirements 2.9**
    
    对于任意 WatchList 和任意 StockCode，如果该 StockCode 不在 WatchList 中，
    则调用 remove_stock() 后，WatchList 的股票数量应保持不变
    """
    watchlist, non_existing_stock_code = data
    
    # 记录移除前的股票数量
    count_before = watchlist.stock_count()
    
    # 尝试移除不存在的股票（应该失败）
    try:
        watchlist.remove_stock(non_existing_stock_code)
    except StockNotFoundError:
        pass
    
    # 股票数量应保持不变
    count_after = watchlist.stock_count()
    assert count_after == count_before, \
        f"股票数量应保持不变，期望 {count_before}，实际 {count_after}"


@settings(max_examples=100)
@given(watchlist=empty_watchlist_strategy(), stock_code=valid_stock_codes)
def test_remove_from_empty_watchlist_raises_error(watchlist, stock_code):
    """
    Property 3.3: 从空列表移除任意股票应抛出 StockNotFoundError
    
    **Validates: Requirements 2.9**
    
    对于任意空 WatchList 和任意 StockCode，调用 remove_stock() 应抛出 StockNotFoundError
    """
    # 验证列表为空
    assert watchlist.stock_count() == 0
    
    # 尝试移除应抛出 StockNotFoundError
    with pytest.raises(StockNotFoundError):
        watchlist.remove_stock(stock_code)
    
    # 列表仍为空
    assert watchlist.stock_count() == 0


@settings(max_examples=100)
@given(data=watchlist_and_non_existing_stock_strategy())
def test_remove_non_existing_does_not_modify_existing_stocks(data):
    """
    Property 3.4: 移除不存在的股票失败后不应修改已存在的股票
    
    **Validates: Requirements 2.9**
    
    对于任意 WatchList 和任意不存在的 StockCode，移除失败后，
    列表中已存在的股票应保持不变
    """
    watchlist, non_existing_stock_code = data
    
    # 获取原有股票列表的快照
    original_stocks = [(s.stock_code.code, s.stock_name) for s in watchlist.stocks]
    
    # 尝试移除不存在的股票（应该失败）
    try:
        watchlist.remove_stock(non_existing_stock_code)
    except StockNotFoundError:
        pass
    
    # 原有股票应保持不变
    current_stocks = [(s.stock_code.code, s.stock_name) for s in watchlist.stocks]
    assert current_stocks == original_stocks, \
        "已存在的股票不应被修改"


@settings(max_examples=100)
@given(
    watchlist=empty_watchlist_strategy(),
    stock_code=valid_stock_codes,
    stock_name=stock_names
)
def test_add_remove_then_remove_again_raises_error(watchlist, stock_code, stock_name):
    """
    Property 3.5: 添加后移除，再次移除应抛出 StockNotFoundError
    
    **Validates: Requirements 2.9**
    
    对于任意 WatchList，先添加一个股票，然后移除它，
    再次移除同一股票应抛出 StockNotFoundError
    """
    # 添加股票
    watchlist.add_stock(stock_code, stock_name)
    assert watchlist.stock_count() == 1
    
    # 移除股票
    watchlist.remove_stock(stock_code)
    assert watchlist.stock_count() == 0
    assert not watchlist.contains(stock_code)
    
    # 再次移除应失败
    with pytest.raises(StockNotFoundError):
        watchlist.remove_stock(stock_code)
    
    # 列表仍为空
    assert watchlist.stock_count() == 0


# =============================================================================
# Combined Properties: 验证 add 和 remove 的交互行为
# =============================================================================

@settings(max_examples=100)
@given(
    watchlist=empty_watchlist_strategy(),
    stock_code=valid_stock_codes,
    stock_name=stock_names
)
def test_add_then_remove_then_add_succeeds(watchlist, stock_code, stock_name):
    """
    Combined Property: 添加-移除-再添加应成功
    
    **Validates: Requirements 2.8, 2.9**
    
    对于任意 WatchList，添加一个股票后移除它，然后再次添加应该成功
    """
    # 添加股票
    watchlist.add_stock(stock_code, stock_name)
    assert watchlist.stock_count() == 1
    
    # 移除股票
    watchlist.remove_stock(stock_code)
    assert watchlist.stock_count() == 0
    
    # 再次添加应成功
    watchlist.add_stock(stock_code, stock_name)
    assert watchlist.stock_count() == 1
    assert watchlist.contains(stock_code)


@settings(max_examples=100)
@given(data=watchlist_and_existing_stock_strategy())
def test_remove_existing_then_add_same_succeeds(data):
    """
    Combined Property: 移除已存在的股票后再添加应成功
    
    **Validates: Requirements 2.8, 2.9**
    
    对于任意 WatchList 和其中已存在的 StockCode，移除后再添加应该成功
    """
    watchlist, existing_stock_code = data
    
    count_before = watchlist.stock_count()
    
    # 移除股票
    watchlist.remove_stock(existing_stock_code)
    assert watchlist.stock_count() == count_before - 1
    assert not watchlist.contains(existing_stock_code)
    
    # 再次添加应成功
    watchlist.add_stock(existing_stock_code, "新添加的股票")
    assert watchlist.stock_count() == count_before
    assert watchlist.contains(existing_stock_code)

