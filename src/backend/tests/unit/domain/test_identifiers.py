"""
单元测试：标识符值对象
"""
import pytest
import uuid

from contexts.screening.domain.value_objects.identifiers import (
    StrategyId, SessionId, WatchListId
)


class TestStrategyId:
    """StrategyId 单元测试"""
    
    def test_valid_uuid_construction(self):
        """测试使用有效 UUID 构造"""
        valid_uuid = str(uuid.uuid4())
        strategy_id = StrategyId(valid_uuid)
        assert strategy_id.value == valid_uuid
    
    def test_invalid_uuid_raises_error(self):
        """测试使用无效 UUID 抛出错误"""
        with pytest.raises(ValueError, match="无效的 UUID 格式"):
            StrategyId("not-a-uuid")
    
    def test_generate_creates_valid_id(self):
        """测试 generate() 创建有效标识符"""
        strategy_id = StrategyId.generate()
        # 应该能够解析为 UUID
        uuid.UUID(strategy_id.value)
    
    def test_from_string(self):
        """测试 from_string() 方法"""
        valid_uuid = str(uuid.uuid4())
        strategy_id = StrategyId.from_string(valid_uuid)
        assert strategy_id.value == valid_uuid
    
    def test_equality(self):
        """测试相等性"""
        uuid_str = str(uuid.uuid4())
        id1 = StrategyId(uuid_str)
        id2 = StrategyId(uuid_str)
        assert id1 == id2
    
    def test_inequality(self):
        """测试不相等"""
        id1 = StrategyId.generate()
        id2 = StrategyId.generate()
        assert id1 != id2
    
    def test_hash_consistency(self):
        """测试哈希一致性"""
        uuid_str = str(uuid.uuid4())
        id1 = StrategyId(uuid_str)
        id2 = StrategyId(uuid_str)
        assert hash(id1) == hash(id2)
    
    def test_can_be_used_in_set(self):
        """测试可用于集合"""
        uuid_str = str(uuid.uuid4())
        id1 = StrategyId(uuid_str)
        id2 = StrategyId(uuid_str)
        id_set = {id1, id2}
        assert len(id_set) == 1


class TestSessionId:
    """SessionId 单元测试"""
    
    def test_valid_uuid_construction(self):
        """测试使用有效 UUID 构造"""
        valid_uuid = str(uuid.uuid4())
        session_id = SessionId(valid_uuid)
        assert session_id.value == valid_uuid
    
    def test_invalid_uuid_raises_error(self):
        """测试使用无效 UUID 抛出错误"""
        with pytest.raises(ValueError, match="无效的 UUID 格式"):
            SessionId("invalid")
    
    def test_generate_creates_valid_id(self):
        """测试 generate() 创建有效标识符"""
        session_id = SessionId.generate()
        uuid.UUID(session_id.value)
    
    def test_from_string(self):
        """测试 from_string() 方法"""
        valid_uuid = str(uuid.uuid4())
        session_id = SessionId.from_string(valid_uuid)
        assert session_id.value == valid_uuid


class TestWatchListId:
    """WatchListId 单元测试"""
    
    def test_valid_uuid_construction(self):
        """测试使用有效 UUID 构造"""
        valid_uuid = str(uuid.uuid4())
        watchlist_id = WatchListId(valid_uuid)
        assert watchlist_id.value == valid_uuid
    
    def test_invalid_uuid_raises_error(self):
        """测试使用无效 UUID 抛出错误"""
        with pytest.raises(ValueError, match="无效的 UUID 格式"):
            WatchListId("bad-uuid")
    
    def test_generate_creates_valid_id(self):
        """测试 generate() 创建有效标识符"""
        watchlist_id = WatchListId.generate()
        uuid.UUID(watchlist_id.value)
    
    def test_from_string(self):
        """测试 from_string() 方法"""
        valid_uuid = str(uuid.uuid4())
        watchlist_id = WatchListId.from_string(valid_uuid)
        assert watchlist_id.value == valid_uuid
