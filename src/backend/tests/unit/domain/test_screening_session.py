"""
单元测试：ScreeningSession 聚合根

测试 ScreeningSession 的所有属性、工厂方法和序列化功能。

Requirements:
- 2.2: ScreeningSession 聚合根包含所有属性
"""
import pytest
from datetime import datetime, timezone

from contexts.screening.domain.models.screening_session import ScreeningSession
from contexts.screening.domain.models.filter_group import FilterGroup
from contexts.screening.domain.value_objects.identifiers import SessionId, StrategyId
from contexts.screening.domain.value_objects.scored_stock import ScoredStock
from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
from contexts.screening.domain.value_objects.screening_result import ScreeningResult
from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import NumericValue
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from contexts.screening.domain.enums.enums import LogicalOperator
from shared_kernel.value_objects.stock_code import StockCode


class TestScreeningSession:
    """ScreeningSession 单元测试"""
    
    @pytest.fixture
    def sample_session_id(self):
        """创建示例 SessionId"""
        return SessionId.generate()
    
    @pytest.fixture
    def sample_strategy_id(self):
        """创建示例 StrategyId"""
        return StrategyId.generate()
    
    @pytest.fixture
    def sample_filter_group(self):
        """创建示例 FilterGroup"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        return FilterGroup(
            group_id="test-group-1",
            operator=LogicalOperator.AND,
            conditions=[condition]
        )

    @pytest.fixture
    def sample_scoring_config(self):
        """创建示例 ScoringConfig"""
        return ScoringConfig(
            weights={IndicatorField.ROE: 1.0}
        )
    
    @pytest.fixture
    def sample_scored_stock(self):
        """创建示例 ScoredStock"""
        return ScoredStock(
            stock_code=StockCode("600000.SH"),
            stock_name="浦发银行",
            score=85.5
        )
    
    @pytest.fixture
    def sample_scored_stock_2(self):
        """创建第二个示例 ScoredStock"""
        return ScoredStock(
            stock_code=StockCode("000001.SZ"),
            stock_name="平安银行",
            score=90.0
        )
    
    @pytest.fixture
    def sample_executed_at(self):
        """创建示例执行时间"""
        return datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    
    # ==================== 构造测试 ====================
    
    def test_valid_construction_minimal(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试使用最小参数构造"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        assert session.session_id == sample_session_id
        assert session.strategy_id == sample_strategy_id
        assert session.strategy_name == "测试策略"
        assert session.executed_at == sample_executed_at
        assert session.total_scanned == 100
        assert session.execution_time == 0.5
        assert session.top_stocks == []
        assert session.other_stock_codes == []
        assert session.filters_snapshot == sample_filter_group
        assert session.scoring_config_snapshot == sample_scoring_config

    def test_valid_construction_with_stocks(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at, sample_scored_stock
    ):
        """测试使用股票列表构造"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[sample_scored_stock],
            other_stock_codes=["000002.SZ", "600001.SH"],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        assert len(session.top_stocks) == 1
        assert session.top_stocks[0] == sample_scored_stock
        assert len(session.other_stock_codes) == 2
        assert "000002.SZ" in session.other_stock_codes
    
    def test_empty_strategy_name_raises_error(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试空策略名称抛出错误"""
        with pytest.raises(ValueError, match="策略名称不能为空"):
            ScreeningSession(
                session_id=sample_session_id,
                strategy_id=sample_strategy_id,
                strategy_name="",
                executed_at=sample_executed_at,
                total_scanned=100,
                execution_time=0.5,
                top_stocks=[],
                other_stock_codes=[],
                filters_snapshot=sample_filter_group,
                scoring_config_snapshot=sample_scoring_config
            )
    
    def test_whitespace_strategy_name_raises_error(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试空白策略名称抛出错误"""
        with pytest.raises(ValueError, match="策略名称不能为空"):
            ScreeningSession(
                session_id=sample_session_id,
                strategy_id=sample_strategy_id,
                strategy_name="   ",
                executed_at=sample_executed_at,
                total_scanned=100,
                execution_time=0.5,
                top_stocks=[],
                other_stock_codes=[],
                filters_snapshot=sample_filter_group,
                scoring_config_snapshot=sample_scoring_config
            )

    def test_negative_total_scanned_raises_error(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试负数扫描总数抛出错误"""
        with pytest.raises(ValueError, match="扫描总数不能为负数"):
            ScreeningSession(
                session_id=sample_session_id,
                strategy_id=sample_strategy_id,
                strategy_name="测试策略",
                executed_at=sample_executed_at,
                total_scanned=-1,
                execution_time=0.5,
                top_stocks=[],
                other_stock_codes=[],
                filters_snapshot=sample_filter_group,
                scoring_config_snapshot=sample_scoring_config
            )
    
    def test_negative_execution_time_raises_error(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试负数执行时间抛出错误"""
        with pytest.raises(ValueError, match="执行时间不能为负数"):
            ScreeningSession(
                session_id=sample_session_id,
                strategy_id=sample_strategy_id,
                strategy_name="测试策略",
                executed_at=sample_executed_at,
                total_scanned=100,
                execution_time=-0.5,
                top_stocks=[],
                other_stock_codes=[],
                filters_snapshot=sample_filter_group,
                scoring_config_snapshot=sample_scoring_config
            )
    
    # ==================== 计算属性测试 ====================
    
    def test_matched_count(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at, sample_scored_stock
    ):
        """测试 matched_count 属性"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[sample_scored_stock],
            other_stock_codes=["000002.SZ", "600001.SH"],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        assert session.matched_count == 3  # 1 top_stock + 2 other_stock_codes

    def test_match_rate(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at, sample_scored_stock
    ):
        """测试 match_rate 属性"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[sample_scored_stock] * 10,
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        assert session.match_rate == 0.1
    
    def test_match_rate_zero_scanned(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试扫描总数为零时的匹配率"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=0,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        assert session.match_rate == 0.0
    
    def test_top_stocks_count(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at, sample_scored_stock
    ):
        """测试 top_stocks_count 属性"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[sample_scored_stock, sample_scored_stock],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        assert session.top_stocks_count == 2

    def test_other_stocks_count(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试 other_stocks_count 属性"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=["000001.SZ", "000002.SZ", "600000.SH"],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        assert session.other_stocks_count == 3
    
    # ==================== 工厂方法测试 ====================
    
    def test_create_from_result_basic(
        self, sample_strategy_id, sample_filter_group, sample_scoring_config,
        sample_scored_stock
    ):
        """测试 create_from_result 工厂方法基本功能"""
        result = ScreeningResult(
            matched_stocks=[sample_scored_stock],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config
        )
        
        session = ScreeningSession.create_from_result(
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            result=result
        )
        
        assert session.strategy_id == sample_strategy_id
        assert session.strategy_name == "测试策略"
        assert session.total_scanned == 100
        assert session.execution_time == 0.5
        assert len(session.top_stocks) == 1
        assert session.top_stocks[0] == sample_scored_stock
        assert session.other_stock_codes == []
        assert session.filters_snapshot.to_dict() == sample_filter_group.to_dict()
        assert session.scoring_config_snapshot == sample_scoring_config

    def test_create_from_result_with_top_n(
        self, sample_strategy_id, sample_filter_group, sample_scoring_config
    ):
        """测试 create_from_result 工厂方法的 top_n 参数"""
        # 创建多个股票
        stocks = []
        for i in range(10):
            code = f"60000{i}.SH"
            stocks.append(ScoredStock(
                stock_code=StockCode(code),
                stock_name=f"股票{i}",
                score=100 - i
            ))
        
        result = ScreeningResult(
            matched_stocks=stocks,
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config
        )
        
        # 只保留前3名
        session = ScreeningSession.create_from_result(
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            result=result,
            top_n=3
        )
        
        assert len(session.top_stocks) == 3
        assert len(session.other_stock_codes) == 7
        # 验证 top_stocks 是前3名
        assert session.top_stocks[0].score == 100
        assert session.top_stocks[1].score == 99
        assert session.top_stocks[2].score == 98
        # 验证 other_stock_codes 包含剩余股票代码
        assert "600003.SH" in session.other_stock_codes
    
    def test_create_from_result_generates_session_id(
        self, sample_strategy_id, sample_filter_group, sample_scoring_config,
        sample_scored_stock
    ):
        """测试 create_from_result 自动生成 session_id"""
        result = ScreeningResult(
            matched_stocks=[sample_scored_stock],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config
        )
        
        session1 = ScreeningSession.create_from_result(
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            result=result
        )
        session2 = ScreeningSession.create_from_result(
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            result=result
        )
        
        # 每次调用应生成不同的 session_id
        assert session1.session_id != session2.session_id

    def test_create_from_result_uses_result_timestamp(
        self, sample_strategy_id, sample_filter_group, sample_scoring_config,
        sample_scored_stock
    ):
        """测试 create_from_result 使用 result 的 timestamp"""
        timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = ScreeningResult(
            matched_stocks=[sample_scored_stock],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config,
            timestamp=timestamp
        )
        
        session = ScreeningSession.create_from_result(
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            result=result
        )
        
        assert session.executed_at == timestamp
    
    # ==================== 序列化测试 ====================
    
    def test_to_dict(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at, sample_scored_stock
    ):
        """测试序列化为字典"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[sample_scored_stock],
            other_stock_codes=["000002.SZ"],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        data = session.to_dict()
        
        assert data['session_id'] == sample_session_id.value
        assert data['strategy_id'] == sample_strategy_id.value
        assert data['strategy_name'] == "测试策略"
        assert data['total_scanned'] == 100
        assert data['execution_time'] == 0.5
        assert len(data['top_stocks']) == 1
        assert data['other_stock_codes'] == ["000002.SZ"]
        assert 'filters_snapshot' in data
        assert 'scoring_config_snapshot' in data

    def test_from_dict(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at, sample_scored_stock
    ):
        """测试从字典反序列化"""
        original = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[sample_scored_stock],
            other_stock_codes=["000002.SZ"],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        data = original.to_dict()
        restored = ScreeningSession.from_dict(data)
        
        assert restored.session_id == original.session_id
        assert restored.strategy_id == original.strategy_id
        assert restored.strategy_name == original.strategy_name
        assert restored.total_scanned == original.total_scanned
        assert restored.execution_time == original.execution_time
        assert len(restored.top_stocks) == len(original.top_stocks)
        assert restored.other_stock_codes == original.other_stock_codes
    
    def test_serialization_round_trip(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at, sample_scored_stock
    ):
        """测试序列化往返一致性"""
        original = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[sample_scored_stock],
            other_stock_codes=["000002.SZ", "600001.SH"],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        data = original.to_dict()
        restored = ScreeningSession.from_dict(data)
        
        # 聚合根相等性基于 session_id
        assert restored == original
        # 验证所有属性
        assert restored.to_dict() == original.to_dict()

    # ==================== 相等性和哈希测试 ====================
    
    def test_equality_same_session_id(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试相同 session_id 的相等性"""
        session1 = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="策略1",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        session2 = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="策略2",  # 不同名称
            executed_at=sample_executed_at,
            total_scanned=200,  # 不同扫描数
            execution_time=1.0,  # 不同执行时间
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        # 聚合根相等性基于 session_id
        assert session1 == session2
    
    def test_inequality_different_session_id(
        self, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试不同 session_id 的不相等"""
        session1 = ScreeningSession(
            session_id=SessionId.generate(),
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        session2 = ScreeningSession(
            session_id=SessionId.generate(),
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        assert session1 != session2

    def test_inequality_with_non_session(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试与非 ScreeningSession 对象的不相等"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        assert session != "not a session"
        assert session != 123
        assert session != None
    
    def test_hash_consistency(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试哈希一致性"""
        session1 = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        session2 = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        assert hash(session1) == hash(session2)
    
    def test_can_be_used_in_set(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试可以在集合中使用"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        session_set = {session}
        assert session in session_set

    # ==================== 不可变性测试 ====================
    
    def test_immutability_top_stocks(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at, sample_scored_stock
    ):
        """测试 top_stocks 不可变性"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[sample_scored_stock],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        # 修改返回的列表不应影响原对象
        returned_stocks = session.top_stocks
        new_stock = ScoredStock(
            stock_code=StockCode("000001.SZ"),
            stock_name="平安银行",
            score=90.0
        )
        returned_stocks.append(new_stock)
        
        assert len(session.top_stocks) == 1
    
    def test_immutability_other_stock_codes(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试 other_stock_codes 不可变性"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=["000001.SZ"],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        # 修改返回的列表不应影响原对象
        returned_codes = session.other_stock_codes
        returned_codes.append("000002.SZ")
        
        assert len(session.other_stock_codes) == 1
    
    # ==================== repr 测试 ====================
    
    def test_repr(
        self, sample_session_id, sample_strategy_id, sample_filter_group,
        sample_scoring_config, sample_executed_at
    ):
        """测试字符串表示"""
        session = ScreeningSession(
            session_id=sample_session_id,
            strategy_id=sample_strategy_id,
            strategy_name="测试策略",
            executed_at=sample_executed_at,
            total_scanned=100,
            execution_time=0.5,
            top_stocks=[],
            other_stock_codes=[],
            filters_snapshot=sample_filter_group,
            scoring_config_snapshot=sample_scoring_config
        )
        
        repr_str = repr(session)
        assert "ScreeningSession" in repr_str
        assert "测试策略" in repr_str
        assert "matched_count=0" in repr_str
