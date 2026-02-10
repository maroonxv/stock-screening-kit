"""
单元测试：ScreeningResult 值对象

注意：ScreeningResult 依赖 FilterGroup，该实体将在 Task 3.1 中实现。
本测试文件中的部分测试需要 FilterGroup 实现后才能运行。
"""
import pytest
from datetime import datetime

from contexts.screening.domain.value_objects.screening_result import ScreeningResult
from contexts.screening.domain.value_objects.scored_stock import ScoredStock
from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
from contexts.screening.domain.enums.indicator_field import IndicatorField
from shared_kernel.value_objects.stock_code import StockCode


# 创建一个简单的 FilterGroup mock 用于测试
class MockFilterGroup:
    """FilterGroup 的简单 mock，用于测试 ScreeningResult"""
    
    def __init__(self, group_id: str = "test-group"):
        self._group_id = group_id
    
    def to_dict(self):
        return {
            'group_id': self._group_id,
            'operator': 'AND',
            'conditions': [],
            'sub_groups': []
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(group_id=data.get('group_id', 'test-group'))


class TestScreeningResult:
    """ScreeningResult 单元测试"""
    
    @pytest.fixture
    def sample_scored_stock(self):
        """创建示例 ScoredStock"""
        return ScoredStock(
            stock_code=StockCode("600000.SH"),
            stock_name="浦发银行",
            score=85.5
        )
    
    @pytest.fixture
    def sample_scoring_config(self):
        """创建示例 ScoringConfig"""
        return ScoringConfig(
            weights={IndicatorField.ROE: 1.0}
        )
    
    @pytest.fixture
    def sample_filter_group(self):
        """创建示例 FilterGroup mock"""
        return MockFilterGroup()
    
    def test_valid_construction_minimal(
        self, sample_filter_group, sample_scoring_config
    ):
        """测试使用最小参数构造"""
        result = ScreeningResult(
            matched_stocks=[],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config
        )
        
        assert result.matched_stocks == []
        assert result.total_scanned == 100
        assert result.execution_time == 0.5
        assert result.filters_applied == sample_filter_group
        assert result.scoring_config == sample_scoring_config
        assert result.timestamp is not None
    
    def test_valid_construction_with_stocks(
        self, sample_scored_stock, sample_filter_group, sample_scoring_config
    ):
        """测试使用股票列表构造"""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        result = ScreeningResult(
            matched_stocks=[sample_scored_stock],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config,
            timestamp=timestamp
        )
        
        assert len(result.matched_stocks) == 1
        assert result.matched_stocks[0] == sample_scored_stock
        assert result.timestamp == timestamp
    
    def test_negative_total_scanned_raises_error(
        self, sample_filter_group, sample_scoring_config
    ):
        """测试负数扫描总数抛出错误"""
        with pytest.raises(ValueError, match="扫描总数不能为负数"):
            ScreeningResult(
                matched_stocks=[],
                total_scanned=-1,
                execution_time=0.5,
                filters_applied=sample_filter_group,
                scoring_config=sample_scoring_config
            )
    
    def test_negative_execution_time_raises_error(
        self, sample_filter_group, sample_scoring_config
    ):
        """测试负数执行时间抛出错误"""
        with pytest.raises(ValueError, match="执行时间不能为负数"):
            ScreeningResult(
                matched_stocks=[],
                total_scanned=100,
                execution_time=-0.5,
                filters_applied=sample_filter_group,
                scoring_config=sample_scoring_config
            )
    
    def test_matched_count(
        self, sample_scored_stock, sample_filter_group, sample_scoring_config
    ):
        """测试 matched_count 属性"""
        result = ScreeningResult(
            matched_stocks=[sample_scored_stock, sample_scored_stock],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config
        )
        
        assert result.matched_count == 2
    
    def test_match_rate(
        self, sample_scored_stock, sample_filter_group, sample_scoring_config
    ):
        """测试 match_rate 属性"""
        result = ScreeningResult(
            matched_stocks=[sample_scored_stock] * 10,
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config
        )
        
        assert result.match_rate == 0.1
    
    def test_match_rate_zero_scanned(
        self, sample_filter_group, sample_scoring_config
    ):
        """测试扫描总数为零时的匹配率"""
        result = ScreeningResult(
            matched_stocks=[],
            total_scanned=0,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config
        )
        
        assert result.match_rate == 0.0
    
    def test_to_dict(
        self, sample_scored_stock, sample_filter_group, sample_scoring_config
    ):
        """测试序列化为字典"""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        result = ScreeningResult(
            matched_stocks=[sample_scored_stock],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config,
            timestamp=timestamp
        )
        
        data = result.to_dict()
        
        assert len(data['matched_stocks']) == 1
        assert data['total_scanned'] == 100
        assert data['execution_time'] == 0.5
        assert 'filters_applied' in data
        assert 'scoring_config' in data
        assert data['timestamp'] == "2024-01-15T10:30:00"
    
    def test_equality(
        self, sample_scored_stock, sample_filter_group, sample_scoring_config
    ):
        """测试相等性"""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        result1 = ScreeningResult(
            matched_stocks=[sample_scored_stock],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config,
            timestamp=timestamp
        )
        result2 = ScreeningResult(
            matched_stocks=[sample_scored_stock],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config,
            timestamp=timestamp
        )
        
        assert result1 == result2
    
    def test_inequality_different_total_scanned(
        self, sample_filter_group, sample_scoring_config
    ):
        """测试不同扫描总数的不相等"""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        result1 = ScreeningResult(
            matched_stocks=[],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config,
            timestamp=timestamp
        )
        result2 = ScreeningResult(
            matched_stocks=[],
            total_scanned=200,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config,
            timestamp=timestamp
        )
        
        assert result1 != result2
    
    def test_hash_consistency(
        self, sample_filter_group, sample_scoring_config
    ):
        """测试哈希一致性"""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        result1 = ScreeningResult(
            matched_stocks=[],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config,
            timestamp=timestamp
        )
        result2 = ScreeningResult(
            matched_stocks=[],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config,
            timestamp=timestamp
        )
        
        assert hash(result1) == hash(result2)
    
    def test_repr(
        self, sample_filter_group, sample_scoring_config
    ):
        """测试字符串表示"""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        result = ScreeningResult(
            matched_stocks=[],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config,
            timestamp=timestamp
        )
        
        repr_str = repr(result)
        assert "ScreeningResult" in repr_str
        assert "matched_count=0" in repr_str
        assert "total_scanned=100" in repr_str
    
    def test_immutability_matched_stocks(
        self, sample_scored_stock, sample_filter_group, sample_scoring_config
    ):
        """测试 matched_stocks 不可变性"""
        result = ScreeningResult(
            matched_stocks=[sample_scored_stock],
            total_scanned=100,
            execution_time=0.5,
            filters_applied=sample_filter_group,
            scoring_config=sample_scoring_config
        )
        
        # 修改返回的列表不应影响原对象
        returned_stocks = result.matched_stocks
        new_stock = ScoredStock(
            stock_code=StockCode("000001.SZ"),
            stock_name="平安银行",
            score=90.0
        )
        returned_stocks.append(new_stock)
        
        assert len(result.matched_stocks) == 1
