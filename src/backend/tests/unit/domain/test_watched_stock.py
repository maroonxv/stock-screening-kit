"""
单元测试：WatchedStock 值对象
"""
import pytest
from datetime import datetime

from contexts.screening.domain.value_objects.watched_stock import WatchedStock
from shared_kernel.value_objects.stock_code import StockCode


class TestWatchedStock:
    """WatchedStock 单元测试"""
    
    def test_valid_construction_minimal(self):
        """测试使用最小参数构造"""
        stock_code = StockCode("600000.SH")
        watched = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行"
        )
        assert watched.stock_code == stock_code
        assert watched.stock_name == "浦发银行"
        assert watched.added_at is not None
        assert watched.note is None
        assert watched.tags is None
    
    def test_valid_construction_full(self):
        """测试使用完整参数构造"""
        stock_code = StockCode("000001.SZ")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        tags = ["银行", "蓝筹"]
        
        watched = WatchedStock(
            stock_code=stock_code,
            stock_name="平安银行",
            added_at=added_at,
            note="关注银行股",
            tags=tags
        )
        
        assert watched.stock_code == stock_code
        assert watched.stock_name == "平安银行"
        assert watched.added_at == added_at
        assert watched.note == "关注银行股"
        assert watched.tags == tags
    
    def test_empty_stock_name_raises_error(self):
        """测试空股票名称抛出错误"""
        stock_code = StockCode("600000.SH")
        with pytest.raises(ValueError, match="股票名称不能为空"):
            WatchedStock(
                stock_code=stock_code,
                stock_name=""
            )
    
    def test_whitespace_stock_name_raises_error(self):
        """测试空白股票名称抛出错误"""
        stock_code = StockCode("600000.SH")
        with pytest.raises(ValueError, match="股票名称不能为空"):
            WatchedStock(
                stock_code=stock_code,
                stock_name="   "
            )
    
    def test_to_dict(self):
        """测试序列化为字典"""
        stock_code = StockCode("600000.SH")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at,
            note="关注银行股",
            tags=["银行", "蓝筹"]
        )
        
        data = watched.to_dict()
        
        assert data['stock_code'] == "600000.SH"
        assert data['stock_name'] == "浦发银行"
        assert data['added_at'] == "2024-01-15T10:30:00"
        assert data['note'] == "关注银行股"
        assert data['tags'] == ["银行", "蓝筹"]
    
    def test_to_dict_with_none_values(self):
        """测试序列化包含 None 值"""
        stock_code = StockCode("600000.SH")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at
        )
        
        data = watched.to_dict()
        
        assert data['note'] is None
        assert data['tags'] is None
    
    def test_from_dict(self):
        """测试从字典反序列化"""
        data = {
            'stock_code': '600000.SH',
            'stock_name': '浦发银行',
            'added_at': '2024-01-15T10:30:00',
            'note': '关注银行股',
            'tags': ['银行', '蓝筹']
        }
        
        watched = WatchedStock.from_dict(data)
        
        assert watched.stock_code.code == "600000.SH"
        assert watched.stock_name == "浦发银行"
        assert watched.added_at == datetime(2024, 1, 15, 10, 30, 0)
        assert watched.note == "关注银行股"
        assert watched.tags == ["银行", "蓝筹"]
    
    def test_from_dict_with_none_values(self):
        """测试从字典反序列化包含 None 值"""
        data = {
            'stock_code': '600000.SH',
            'stock_name': '浦发银行',
            'added_at': '2024-01-15T10:30:00',
            'note': None,
            'tags': None
        }
        
        watched = WatchedStock.from_dict(data)
        
        assert watched.note is None
        assert watched.tags is None
    
    def test_serialization_round_trip(self):
        """测试序列化往返"""
        stock_code = StockCode("000001.SZ")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched1 = WatchedStock(
            stock_code=stock_code,
            stock_name="平安银行",
            added_at=added_at,
            note="关注银行股",
            tags=["银行", "蓝筹"]
        )
        
        data = watched1.to_dict()
        watched2 = WatchedStock.from_dict(data)
        
        assert watched1 == watched2
    
    def test_with_note(self):
        """测试 with_note 方法"""
        stock_code = StockCode("600000.SH")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched1 = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at,
            note="原始备注"
        )
        
        watched2 = watched1.with_note("新备注")
        
        # 原对象不变
        assert watched1.note == "原始备注"
        # 新对象有新备注
        assert watched2.note == "新备注"
        # 其他属性相同
        assert watched2.stock_code == watched1.stock_code
        assert watched2.stock_name == watched1.stock_name
        assert watched2.added_at == watched1.added_at
    
    def test_with_tags(self):
        """测试 with_tags 方法"""
        stock_code = StockCode("600000.SH")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched1 = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at,
            tags=["银行"]
        )
        
        watched2 = watched1.with_tags(["银行", "蓝筹", "金融"])
        
        # 原对象不变
        assert watched1.tags == ["银行"]
        # 新对象有新标签
        assert watched2.tags == ["银行", "蓝筹", "金融"]
        # 其他属性相同
        assert watched2.stock_code == watched1.stock_code
        assert watched2.stock_name == watched1.stock_name
        assert watched2.added_at == watched1.added_at
    
    def test_equality(self):
        """测试相等性"""
        stock_code = StockCode("600000.SH")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched1 = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at,
            note="备注",
            tags=["银行"]
        )
        watched2 = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at,
            note="备注",
            tags=["银行"]
        )
        assert watched1 == watched2
    
    def test_inequality_different_stock_code(self):
        """测试不同股票代码的不相等"""
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched1 = WatchedStock(
            stock_code=StockCode("600000.SH"),
            stock_name="浦发银行",
            added_at=added_at
        )
        watched2 = WatchedStock(
            stock_code=StockCode("000001.SZ"),
            stock_name="浦发银行",
            added_at=added_at
        )
        assert watched1 != watched2
    
    def test_inequality_different_note(self):
        """测试不同备注的不相等"""
        stock_code = StockCode("600000.SH")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched1 = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at,
            note="备注1"
        )
        watched2 = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at,
            note="备注2"
        )
        assert watched1 != watched2
    
    def test_inequality_different_tags(self):
        """测试不同标签的不相等"""
        stock_code = StockCode("600000.SH")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched1 = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at,
            tags=["银行"]
        )
        watched2 = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at,
            tags=["银行", "蓝筹"]
        )
        assert watched1 != watched2
    
    def test_hash_consistency(self):
        """测试哈希一致性"""
        stock_code = StockCode("600000.SH")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched1 = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at
        )
        watched2 = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at
        )
        assert hash(watched1) == hash(watched2)
    
    def test_repr(self):
        """测试字符串表示"""
        stock_code = StockCode("600000.SH")
        added_at = datetime(2024, 1, 15, 10, 30, 0)
        
        watched = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            added_at=added_at
        )
        
        repr_str = repr(watched)
        assert "WatchedStock" in repr_str
        assert "600000.SH" in repr_str
        assert "浦发银行" in repr_str
    
    def test_immutability_tags(self):
        """测试 tags 不可变性"""
        stock_code = StockCode("600000.SH")
        tags = ["银行", "蓝筹"]
        
        watched = WatchedStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            tags=tags
        )
        
        # 修改返回的列表不应影响原对象
        returned_tags = watched.tags
        returned_tags.append("金融")
        
        assert len(watched.tags) == 2
        assert "金融" not in watched.tags
