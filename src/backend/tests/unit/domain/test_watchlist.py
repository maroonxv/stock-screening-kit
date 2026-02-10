"""
WatchList 聚合根单元测试

测试 WatchList 的核心功能：
- 构造验证
- add_stock() 方法
- remove_stock() 方法
- contains() 方法

Requirements:
- 2.3: WatchList 聚合根包含属性：watchlist_id、name、description、stocks、created_at、updated_at
- 2.8: 对已存在的 stock_code 调用 add_stock() 时抛出 DuplicateStockError
- 2.9: 对不存在的 stock_code 调用 remove_stock() 时抛出 StockNotFoundError
"""
import pytest
from datetime import datetime, timezone
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contexts.screening.domain.models.watchlist import WatchList
from contexts.screening.domain.value_objects.identifiers import WatchListId
from contexts.screening.domain.value_objects.watched_stock import WatchedStock
from contexts.screening.domain.exceptions import DuplicateStockError, StockNotFoundError
from shared_kernel.value_objects.stock_code import StockCode


class TestWatchListConstruction:
    """WatchList 构造测试"""
    
    def test_create_watchlist_with_valid_name(self):
        """测试使用有效名称创建 WatchList"""
        watchlist_id = WatchListId.generate()
        watchlist = WatchList(
            watchlist_id=watchlist_id,
            name="我的自选股"
        )
        
        assert watchlist.watchlist_id == watchlist_id
        assert watchlist.name == "我的自选股"
        assert watchlist.description is None
        assert watchlist.stocks == []
        assert watchlist.created_at is not None
        assert watchlist.updated_at is not None
    
    def test_create_watchlist_with_description(self):
        """测试使用描述创建 WatchList"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="价值投资组合",
            description="专注于低估值高分红股票"
        )
        
        assert watchlist.name == "价值投资组合"
        assert watchlist.description == "专注于低估值高分红股票"
    
    def test_create_watchlist_with_initial_stocks(self):
        """测试使用初始股票列表创建 WatchList"""
        stock_code = StockCode("600000.SH")
        watched_stock = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行"
        )
        
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="银行股",
            stocks=[watched_stock]
        )
        
        assert len(watchlist.stocks) == 1
        assert watchlist.stocks[0].stock_code == stock_code
    
    def test_create_watchlist_with_empty_name_raises_error(self):
        """测试使用空名称创建 WatchList 抛出错误"""
        with pytest.raises(ValueError, match="自选股列表名称不能为空"):
            WatchList(
                watchlist_id=WatchListId.generate(),
                name=""
            )
    
    def test_create_watchlist_with_whitespace_name_raises_error(self):
        """测试使用空白名称创建 WatchList 抛出错误"""
        with pytest.raises(ValueError, match="自选股列表名称不能为空"):
            WatchList(
                watchlist_id=WatchListId.generate(),
                name="   "
            )
    
    def test_create_watchlist_with_custom_timestamps(self):
        """测试使用自定义时间戳创建 WatchList"""
        created = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        updated = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表",
            created_at=created,
            updated_at=updated
        )
        
        assert watchlist.created_at == created
        assert watchlist.updated_at == updated


class TestWatchListAddStock:
    """WatchList.add_stock() 测试"""
    
    def test_add_stock_to_empty_list(self):
        """测试向空列表添加股票"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        stock_code = StockCode("600000.SH")
        
        watchlist.add_stock(
            stock_code=stock_code,
            stock_name="浦发银行"
        )
        
        assert len(watchlist.stocks) == 1
        assert watchlist.contains(stock_code)
        assert watchlist.stocks[0].stock_name == "浦发银行"
    
    def test_add_stock_with_note_and_tags(self):
        """测试添加带备注和标签的股票"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        stock_code = StockCode("000001.SZ")
        
        watchlist.add_stock(
            stock_code=stock_code,
            stock_name="平安银行",
            note="关注季报",
            tags=["银行", "金融"]
        )
        
        stock = watchlist.get_stock(stock_code)
        assert stock is not None
        assert stock.note == "关注季报"
        assert stock.tags == ["银行", "金融"]
    
    def test_add_multiple_stocks(self):
        """测试添加多只股票"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        
        watchlist.add_stock(StockCode("600000.SH"), "浦发银行")
        watchlist.add_stock(StockCode("000001.SZ"), "平安银行")
        watchlist.add_stock(StockCode("601398.SH"), "工商银行")
        
        assert len(watchlist.stocks) == 3
        assert watchlist.contains(StockCode("600000.SH"))
        assert watchlist.contains(StockCode("000001.SZ"))
        assert watchlist.contains(StockCode("601398.SH"))
    
    def test_add_duplicate_stock_raises_error(self):
        """测试添加重复股票抛出 DuplicateStockError - Validates: Requirement 2.8"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        stock_code = StockCode("600000.SH")
        
        watchlist.add_stock(stock_code, "浦发银行")
        
        with pytest.raises(DuplicateStockError, match="股票 600000.SH 已存在于列表中"):
            watchlist.add_stock(stock_code, "浦发银行")
    
    def test_add_duplicate_stock_does_not_change_count(self):
        """测试添加重复股票不改变列表数量 - Validates: Requirement 2.8"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        stock_code = StockCode("600000.SH")
        
        watchlist.add_stock(stock_code, "浦发银行")
        original_count = watchlist.stock_count()
        
        try:
            watchlist.add_stock(stock_code, "浦发银行")
        except DuplicateStockError:
            pass
        
        assert watchlist.stock_count() == original_count
    
    def test_add_stock_updates_timestamp(self):
        """测试添加股票更新时间戳"""
        created = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表",
            created_at=created,
            updated_at=created
        )
        
        original_updated = watchlist.updated_at
        watchlist.add_stock(StockCode("600000.SH"), "浦发银行")
        
        assert watchlist.updated_at > original_updated


class TestWatchListRemoveStock:
    """WatchList.remove_stock() 测试"""
    
    def test_remove_existing_stock(self):
        """测试移除存在的股票"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        stock_code = StockCode("600000.SH")
        
        watchlist.add_stock(stock_code, "浦发银行")
        assert watchlist.contains(stock_code)
        
        watchlist.remove_stock(stock_code)
        assert not watchlist.contains(stock_code)
        assert len(watchlist.stocks) == 0
    
    def test_remove_stock_from_multiple(self):
        """测试从多只股票中移除一只"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        
        code1 = StockCode("600000.SH")
        code2 = StockCode("000001.SZ")
        code3 = StockCode("601398.SH")
        
        watchlist.add_stock(code1, "浦发银行")
        watchlist.add_stock(code2, "平安银行")
        watchlist.add_stock(code3, "工商银行")
        
        watchlist.remove_stock(code2)
        
        assert len(watchlist.stocks) == 2
        assert watchlist.contains(code1)
        assert not watchlist.contains(code2)
        assert watchlist.contains(code3)
    
    def test_remove_nonexistent_stock_raises_error(self):
        """测试移除不存在的股票抛出 StockNotFoundError - Validates: Requirement 2.9"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        stock_code = StockCode("600000.SH")
        
        with pytest.raises(StockNotFoundError, match="股票 600000.SH 不在列表中"):
            watchlist.remove_stock(stock_code)
    
    def test_remove_nonexistent_stock_does_not_change_count(self):
        """测试移除不存在的股票不改变列表数量 - Validates: Requirement 2.9"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        watchlist.add_stock(StockCode("000001.SZ"), "平安银行")
        original_count = watchlist.stock_count()
        
        try:
            watchlist.remove_stock(StockCode("600000.SH"))
        except StockNotFoundError:
            pass
        
        assert watchlist.stock_count() == original_count
    
    def test_remove_stock_updates_timestamp(self):
        """测试移除股票更新时间戳"""
        created = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表",
            created_at=created,
            updated_at=created
        )
        stock_code = StockCode("600000.SH")
        watchlist.add_stock(stock_code, "浦发银行")
        
        # 重置 updated_at 以便测试
        watchlist._updated_at = created
        original_updated = watchlist.updated_at
        
        watchlist.remove_stock(stock_code)
        
        assert watchlist.updated_at > original_updated


class TestWatchListContains:
    """WatchList.contains() 测试"""
    
    def test_contains_returns_true_for_existing_stock(self):
        """测试 contains 对存在的股票返回 True"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        stock_code = StockCode("600000.SH")
        watchlist.add_stock(stock_code, "浦发银行")
        
        assert watchlist.contains(stock_code) is True
    
    def test_contains_returns_false_for_nonexistent_stock(self):
        """测试 contains 对不存在的股票返回 False"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        
        assert watchlist.contains(StockCode("600000.SH")) is False
    
    def test_contains_returns_false_for_empty_list(self):
        """测试 contains 对空列表返回 False"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        
        assert watchlist.contains(StockCode("600000.SH")) is False
    
    def test_contains_distinguishes_different_codes(self):
        """测试 contains 区分不同的股票代码"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        watchlist.add_stock(StockCode("600000.SH"), "浦发银行")
        
        assert watchlist.contains(StockCode("600000.SH")) is True
        assert watchlist.contains(StockCode("000001.SZ")) is False


class TestWatchListHelperMethods:
    """WatchList 辅助方法测试"""
    
    def test_get_stock_returns_watched_stock(self):
        """测试 get_stock 返回 WatchedStock"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        stock_code = StockCode("600000.SH")
        watchlist.add_stock(stock_code, "浦发银行", note="测试备注")
        
        stock = watchlist.get_stock(stock_code)
        
        assert stock is not None
        assert stock.stock_code == stock_code
        assert stock.stock_name == "浦发银行"
        assert stock.note == "测试备注"
    
    def test_get_stock_returns_none_for_nonexistent(self):
        """测试 get_stock 对不存在的股票返回 None"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        
        assert watchlist.get_stock(StockCode("600000.SH")) is None
    
    def test_stock_count_returns_correct_count(self):
        """测试 stock_count 返回正确数量"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        
        assert watchlist.stock_count() == 0
        
        watchlist.add_stock(StockCode("600000.SH"), "浦发银行")
        assert watchlist.stock_count() == 1
        
        watchlist.add_stock(StockCode("000001.SZ"), "平安银行")
        assert watchlist.stock_count() == 2
    
    def test_update_name_changes_name(self):
        """测试 update_name 更新名称"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="原名称"
        )
        
        watchlist.update_name("新名称")
        
        assert watchlist.name == "新名称"
    
    def test_update_name_with_empty_raises_error(self):
        """测试 update_name 使用空名称抛出错误"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="原名称"
        )
        
        with pytest.raises(ValueError, match="自选股列表名称不能为空"):
            watchlist.update_name("")
    
    def test_update_description_changes_description(self):
        """测试 update_description 更新描述"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        
        watchlist.update_description("新描述")
        
        assert watchlist.description == "新描述"
    
    def test_update_description_to_none(self):
        """测试 update_description 设置为 None"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表",
            description="原描述"
        )
        
        watchlist.update_description(None)
        
        assert watchlist.description is None


class TestWatchListEquality:
    """WatchList 相等性测试"""
    
    def test_watchlists_with_same_id_are_equal(self):
        """测试相同 ID 的 WatchList 相等"""
        watchlist_id = WatchListId.generate()
        
        watchlist1 = WatchList(watchlist_id=watchlist_id, name="列表1")
        watchlist2 = WatchList(watchlist_id=watchlist_id, name="列表2")
        
        assert watchlist1 == watchlist2
    
    def test_watchlists_with_different_ids_are_not_equal(self):
        """测试不同 ID 的 WatchList 不相等"""
        watchlist1 = WatchList(watchlist_id=WatchListId.generate(), name="列表1")
        watchlist2 = WatchList(watchlist_id=WatchListId.generate(), name="列表1")
        
        assert watchlist1 != watchlist2
    
    def test_watchlist_not_equal_to_non_watchlist(self):
        """测试 WatchList 与非 WatchList 对象不相等"""
        watchlist = WatchList(watchlist_id=WatchListId.generate(), name="测试列表")
        
        assert watchlist != "not a watchlist"
        assert watchlist != 123
        assert watchlist != None
    
    def test_watchlist_hash_based_on_id(self):
        """测试 WatchList 哈希基于 ID"""
        watchlist_id = WatchListId.generate()
        
        watchlist1 = WatchList(watchlist_id=watchlist_id, name="列表1")
        watchlist2 = WatchList(watchlist_id=watchlist_id, name="列表2")
        
        assert hash(watchlist1) == hash(watchlist2)
    
    def test_watchlist_repr(self):
        """测试 WatchList 字符串表示"""
        watchlist_id = WatchListId.generate()
        watchlist = WatchList(watchlist_id=watchlist_id, name="测试列表")
        
        repr_str = repr(watchlist)
        
        assert "WatchList" in repr_str
        assert "测试列表" in repr_str
        assert "stock_count=0" in repr_str


class TestWatchListStocksImmutability:
    """WatchList stocks 属性不可变性测试"""
    
    def test_stocks_property_returns_copy(self):
        """测试 stocks 属性返回副本"""
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表"
        )
        watchlist.add_stock(StockCode("600000.SH"), "浦发银行")
        
        stocks = watchlist.stocks
        stocks.clear()  # 修改返回的列表
        
        # 原列表不受影响
        assert len(watchlist.stocks) == 1
    
    def test_initial_stocks_are_copied(self):
        """测试初始股票列表被复制"""
        stock_code = StockCode("600000.SH")
        watched_stock = WatchedStock(stock_code=stock_code, stock_name="浦发银行")
        initial_stocks = [watched_stock]
        
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name="测试列表",
            stocks=initial_stocks
        )
        
        initial_stocks.clear()  # 修改原列表
        
        # WatchList 内部列表不受影响
        assert len(watchlist.stocks) == 1
