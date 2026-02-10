"""
单元测试：ScoredStock 值对象
"""
import pytest

from contexts.screening.domain.value_objects.scored_stock import ScoredStock
from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import NumericValue
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from shared_kernel.value_objects.stock_code import StockCode


class TestScoredStock:
    """ScoredStock 单元测试"""
    
    def test_valid_construction_minimal(self):
        """测试使用最小参数构造"""
        stock_code = StockCode("600000.SH")
        scored = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5
        )
        assert scored.stock_code == stock_code
        assert scored.stock_name == "浦发银行"
        assert scored.score == 85.5
        assert scored.score_breakdown == {}
        assert scored.indicator_values == {}
        assert scored.matched_conditions == []
    
    def test_valid_construction_full(self):
        """测试使用完整参数构造"""
        stock_code = StockCode("000001.SZ")
        score_breakdown = {
            IndicatorField.ROE: 30.0,
            IndicatorField.PE: 20.0
        }
        indicator_values = {
            IndicatorField.ROE: 0.15,
            IndicatorField.PE: 12.5
        }
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.1)
        )
        
        scored = ScoredStock(
            stock_code=stock_code,
            stock_name="平安银行",
            score=90.0,
            score_breakdown=score_breakdown,
            indicator_values=indicator_values,
            matched_conditions=[condition]
        )
        
        assert scored.stock_code == stock_code
        assert scored.stock_name == "平安银行"
        assert scored.score == 90.0
        assert scored.score_breakdown == score_breakdown
        assert scored.indicator_values == indicator_values
        assert len(scored.matched_conditions) == 1
        assert scored.matched_conditions[0] == condition
    
    def test_empty_stock_name_raises_error(self):
        """测试空股票名称抛出错误"""
        stock_code = StockCode("600000.SH")
        with pytest.raises(ValueError, match="股票名称不能为空"):
            ScoredStock(
                stock_code=stock_code,
                stock_name="",
                score=85.5
            )
    
    def test_whitespace_stock_name_raises_error(self):
        """测试空白股票名称抛出错误"""
        stock_code = StockCode("600000.SH")
        with pytest.raises(ValueError, match="股票名称不能为空"):
            ScoredStock(
                stock_code=stock_code,
                stock_name="   ",
                score=85.5
            )
    
    def test_to_dict(self):
        """测试序列化为字典"""
        stock_code = StockCode("600000.SH")
        score_breakdown = {IndicatorField.ROE: 50.0}
        indicator_values = {IndicatorField.ROE: 0.15}
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.1)
        )
        
        scored = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5,
            score_breakdown=score_breakdown,
            indicator_values=indicator_values,
            matched_conditions=[condition]
        )
        
        data = scored.to_dict()
        
        assert data['stock_code'] == "600000.SH"
        assert data['stock_name'] == "浦发银行"
        assert data['score'] == 85.5
        assert data['score_breakdown'] == {'ROE': 50.0}
        assert data['indicator_values'] == {'ROE': 0.15}
        assert len(data['matched_conditions']) == 1
        assert data['matched_conditions'][0]['field'] == 'ROE'
    
    def test_from_dict(self):
        """测试从字典反序列化"""
        data = {
            'stock_code': '600000.SH',
            'stock_name': '浦发银行',
            'score': 85.5,
            'score_breakdown': {'ROE': 50.0},
            'indicator_values': {'ROE': 0.15},
            'matched_conditions': [
                {
                    'field': 'ROE',
                    'operator': '>',
                    'value': {'type': 'numeric', 'value': 0.1, 'unit': None}
                }
            ]
        }
        
        scored = ScoredStock.from_dict(data)
        
        assert scored.stock_code.code == "600000.SH"
        assert scored.stock_name == "浦发银行"
        assert scored.score == 85.5
        assert scored.score_breakdown[IndicatorField.ROE] == 50.0
        assert scored.indicator_values[IndicatorField.ROE] == 0.15
        assert len(scored.matched_conditions) == 1
    
    def test_serialization_round_trip(self):
        """测试序列化往返"""
        stock_code = StockCode("000001.SZ")
        score_breakdown = {
            IndicatorField.ROE: 30.0,
            IndicatorField.PE: 20.0
        }
        indicator_values = {
            IndicatorField.ROE: 0.15,
            IndicatorField.PE: 12.5
        }
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.1)
        )
        
        scored1 = ScoredStock(
            stock_code=stock_code,
            stock_name="平安银行",
            score=90.0,
            score_breakdown=score_breakdown,
            indicator_values=indicator_values,
            matched_conditions=[condition]
        )
        
        data = scored1.to_dict()
        scored2 = ScoredStock.from_dict(data)
        
        assert scored1 == scored2
    
    def test_equality(self):
        """测试相等性"""
        stock_code = StockCode("600000.SH")
        scored1 = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5
        )
        scored2 = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5
        )
        assert scored1 == scored2
    
    def test_inequality_different_score(self):
        """测试不同评分的不相等"""
        stock_code = StockCode("600000.SH")
        scored1 = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5
        )
        scored2 = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=90.0
        )
        assert scored1 != scored2
    
    def test_inequality_different_stock_code(self):
        """测试不同股票代码的不相等"""
        scored1 = ScoredStock(
            stock_code=StockCode("600000.SH"),
            stock_name="浦发银行",
            score=85.5
        )
        scored2 = ScoredStock(
            stock_code=StockCode("000001.SZ"),
            stock_name="浦发银行",
            score=85.5
        )
        assert scored1 != scored2
    
    def test_hash_consistency(self):
        """测试哈希一致性"""
        stock_code = StockCode("600000.SH")
        scored1 = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5
        )
        scored2 = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5
        )
        assert hash(scored1) == hash(scored2)
    
    def test_repr(self):
        """测试字符串表示"""
        stock_code = StockCode("600000.SH")
        scored = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5
        )
        repr_str = repr(scored)
        assert "ScoredStock" in repr_str
        assert "600000.SH" in repr_str
        assert "浦发银行" in repr_str
        assert "85.5" in repr_str
    
    def test_immutability_score_breakdown(self):
        """测试 score_breakdown 不可变性"""
        stock_code = StockCode("600000.SH")
        score_breakdown = {IndicatorField.ROE: 50.0}
        scored = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5,
            score_breakdown=score_breakdown
        )
        
        # 修改返回的字典不应影响原对象
        returned_breakdown = scored.score_breakdown
        returned_breakdown[IndicatorField.PE] = 30.0
        
        assert IndicatorField.PE not in scored.score_breakdown
    
    def test_immutability_indicator_values(self):
        """测试 indicator_values 不可变性"""
        stock_code = StockCode("600000.SH")
        indicator_values = {IndicatorField.ROE: 0.15}
        scored = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5,
            indicator_values=indicator_values
        )
        
        # 修改返回的字典不应影响原对象
        returned_values = scored.indicator_values
        returned_values[IndicatorField.PE] = 12.5
        
        assert IndicatorField.PE not in scored.indicator_values
    
    def test_immutability_matched_conditions(self):
        """测试 matched_conditions 不可变性"""
        stock_code = StockCode("600000.SH")
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.1)
        )
        scored = ScoredStock(
            stock_code=stock_code,
            stock_name="浦发银行",
            score=85.5,
            matched_conditions=[condition]
        )
        
        # 修改返回的列表不应影响原对象
        returned_conditions = scored.matched_conditions
        new_condition = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(20.0)
        )
        returned_conditions.append(new_condition)
        
        assert len(scored.matched_conditions) == 1
