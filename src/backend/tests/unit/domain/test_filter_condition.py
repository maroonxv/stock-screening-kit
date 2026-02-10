"""
FilterCondition 值对象单元测试

测试覆盖：
- 3.1: FilterCondition 值对象，包含 field、operator 和 value
- 3.9: 类型不匹配时抛出 TypeError
- 3.11: 支持 to_dict() 和 from_dict() 序列化
- 5.1: evaluate() 方法计算指标值并应用比较运算符
- 5.2: evaluate() 遇到 None 指标值时返回 False
"""
import pytest
from unittest.mock import Mock

from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import (
    NumericValue, TextValue, ListValue, RangeValue, TimeSeriesValue
)
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator


class TestFilterConditionConstruction:
    """测试 FilterCondition 构造 (Requirement 3.1)"""
    
    def test_create_with_numeric_field_and_numeric_value(self):
        """测试使用数值字段和数值值创建条件"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        assert condition.field == IndicatorField.ROE
        assert condition.operator == ComparisonOperator.GREATER_THAN
        assert isinstance(condition.value, NumericValue)
        assert condition.value.value == 0.15
    
    def test_create_with_numeric_field_and_range_value(self):
        """测试使用数值字段和区间值创建条件"""
        condition = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.BETWEEN,
            value=RangeValue(10.0, 30.0)
        )
        
        assert condition.field == IndicatorField.PE
        assert condition.operator == ComparisonOperator.BETWEEN
        assert isinstance(condition.value, RangeValue)
    
    def test_create_with_numeric_field_and_time_series_value(self):
        """测试使用数值字段和时间序列值创建条件"""
        condition = FilterCondition(
            field=IndicatorField.ROE_CONTINUOUS_GROWTH_YEARS,
            operator=ComparisonOperator.GREATER_OR_EQUAL,
            value=TimeSeriesValue(years=3, threshold=0.1)
        )
        
        assert condition.field == IndicatorField.ROE_CONTINUOUS_GROWTH_YEARS
        assert isinstance(condition.value, TimeSeriesValue)
    
    def test_create_with_text_field_and_text_value(self):
        """测试使用文本字段和文本值创建条件"""
        condition = FilterCondition(
            field=IndicatorField.INDUSTRY,
            operator=ComparisonOperator.EQUALS,
            value=TextValue("科技")
        )
        
        assert condition.field == IndicatorField.INDUSTRY
        assert condition.operator == ComparisonOperator.EQUALS
        assert isinstance(condition.value, TextValue)
    
    def test_create_with_text_field_and_list_value(self):
        """测试使用文本字段和列表值创建条件"""
        condition = FilterCondition(
            field=IndicatorField.INDUSTRY,
            operator=ComparisonOperator.IN,
            value=ListValue(["科技", "医药", "消费"])
        )
        
        assert condition.field == IndicatorField.INDUSTRY
        assert condition.operator == ComparisonOperator.IN
        assert isinstance(condition.value, ListValue)


class TestFilterConditionTypeValidation:
    """测试 FilterCondition 类型验证 (Requirement 3.9)"""
    
    def test_numeric_field_with_text_value_raises_type_error(self):
        """测试数值字段使用文本值时抛出 TypeError"""
        with pytest.raises(TypeError) as exc_info:
            FilterCondition(
                field=IndicatorField.ROE,
                operator=ComparisonOperator.EQUALS,
                value=TextValue("高")
            )
        assert "字段 ROE 需要数值类型的值" in str(exc_info.value)
    
    def test_numeric_field_with_list_value_raises_type_error(self):
        """测试数值字段使用列表值时抛出 TypeError"""
        with pytest.raises(TypeError) as exc_info:
            FilterCondition(
                field=IndicatorField.PE,
                operator=ComparisonOperator.IN,
                value=ListValue([10, 20, 30])
            )
        assert "字段 PE 需要数值类型的值" in str(exc_info.value)
    
    def test_text_field_with_numeric_value_raises_type_error(self):
        """测试文本字段使用数值值时抛出 TypeError"""
        with pytest.raises(TypeError) as exc_info:
            FilterCondition(
                field=IndicatorField.INDUSTRY,
                operator=ComparisonOperator.EQUALS,
                value=NumericValue(100.0)
            )
        assert "字段 INDUSTRY 需要文本类型的值" in str(exc_info.value)
    
    def test_text_field_with_range_value_raises_type_error(self):
        """测试文本字段使用区间值时抛出 TypeError"""
        with pytest.raises(TypeError) as exc_info:
            FilterCondition(
                field=IndicatorField.INDUSTRY,
                operator=ComparisonOperator.BETWEEN,
                value=RangeValue(0.0, 100.0)
            )
        assert "字段 INDUSTRY 需要文本类型的值" in str(exc_info.value)
    
    def test_in_operator_without_list_value_raises_value_error(self):
        """测试 IN 运算符使用非列表值时抛出 ValueError"""
        with pytest.raises(ValueError) as exc_info:
            FilterCondition(
                field=IndicatorField.INDUSTRY,
                operator=ComparisonOperator.IN,
                value=TextValue("科技")
            )
        assert "运算符 in 需要 ListValue" in str(exc_info.value)
    
    def test_not_in_operator_without_list_value_raises_value_error(self):
        """测试 NOT_IN 运算符使用非列表值时抛出 ValueError"""
        with pytest.raises(ValueError) as exc_info:
            FilterCondition(
                field=IndicatorField.INDUSTRY,
                operator=ComparisonOperator.NOT_IN,
                value=TextValue("科技")
            )
        assert "运算符 not_in 需要 ListValue" in str(exc_info.value)
    
    def test_between_operator_without_range_value_raises_value_error(self):
        """测试 BETWEEN 运算符使用非区间值时抛出 ValueError"""
        with pytest.raises(ValueError) as exc_info:
            FilterCondition(
                field=IndicatorField.ROE,
                operator=ComparisonOperator.BETWEEN,
                value=NumericValue(0.15)
            )
        assert "运算符 between 需要 RangeValue" in str(exc_info.value)
    
    def test_not_between_operator_without_range_value_raises_value_error(self):
        """测试 NOT_BETWEEN 运算符使用非区间值时抛出 ValueError"""
        with pytest.raises(ValueError) as exc_info:
            FilterCondition(
                field=IndicatorField.PE,
                operator=ComparisonOperator.NOT_BETWEEN,
                value=NumericValue(20.0)
            )
        assert "运算符 not_between 需要 RangeValue" in str(exc_info.value)


class TestFilterConditionSerialization:
    """测试 FilterCondition 序列化 (Requirement 3.11)"""
    
    def test_to_dict_with_numeric_value(self):
        """测试数值条件序列化"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15, unit="%")
        )
        
        result = condition.to_dict()
        
        assert result == {
            'field': 'ROE',
            'operator': '>',
            'value': {'type': 'numeric', 'value': 0.15, 'unit': '%'}
        }
    
    def test_to_dict_with_range_value(self):
        """测试区间条件序列化"""
        condition = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.BETWEEN,
            value=RangeValue(10.0, 30.0)
        )
        
        result = condition.to_dict()
        
        assert result == {
            'field': 'PE',
            'operator': 'between',
            'value': {'type': 'range', 'min': 10.0, 'max': 30.0}
        }
    
    def test_to_dict_with_text_value(self):
        """测试文本条件序列化"""
        condition = FilterCondition(
            field=IndicatorField.INDUSTRY,
            operator=ComparisonOperator.EQUALS,
            value=TextValue("科技")
        )
        
        result = condition.to_dict()
        
        assert result == {
            'field': 'INDUSTRY',
            'operator': '=',
            'value': {'type': 'text', 'value': '科技'}
        }
    
    def test_to_dict_with_list_value(self):
        """测试列表条件序列化"""
        condition = FilterCondition(
            field=IndicatorField.INDUSTRY,
            operator=ComparisonOperator.IN,
            value=ListValue(["科技", "医药"])
        )
        
        result = condition.to_dict()
        
        assert result == {
            'field': 'INDUSTRY',
            'operator': 'in',
            'value': {'type': 'list', 'values': ['科技', '医药']}
        }
    
    def test_from_dict_with_numeric_value(self):
        """测试从字典反序列化数值条件"""
        data = {
            'field': 'ROE',
            'operator': '>',
            'value': {'type': 'numeric', 'value': 0.15, 'unit': '%'}
        }
        
        condition = FilterCondition.from_dict(data)
        
        assert condition.field == IndicatorField.ROE
        assert condition.operator == ComparisonOperator.GREATER_THAN
        assert isinstance(condition.value, NumericValue)
        assert condition.value.value == 0.15
    
    def test_from_dict_with_range_value(self):
        """测试从字典反序列化区间条件"""
        data = {
            'field': 'PE',
            'operator': 'between',
            'value': {'type': 'range', 'min': 10.0, 'max': 30.0}
        }
        
        condition = FilterCondition.from_dict(data)
        
        assert condition.field == IndicatorField.PE
        assert condition.operator == ComparisonOperator.BETWEEN
        assert isinstance(condition.value, RangeValue)
    
    def test_from_dict_with_text_value(self):
        """测试从字典反序列化文本条件"""
        data = {
            'field': 'INDUSTRY',
            'operator': '=',
            'value': {'type': 'text', 'value': '科技'}
        }
        
        condition = FilterCondition.from_dict(data)
        
        assert condition.field == IndicatorField.INDUSTRY
        assert condition.operator == ComparisonOperator.EQUALS
        assert isinstance(condition.value, TextValue)
    
    def test_serialization_round_trip(self):
        """测试序列化往返"""
        original = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        serialized = original.to_dict()
        restored = FilterCondition.from_dict(serialized)
        
        assert original == restored


class TestFilterConditionEvaluate:
    """测试 FilterCondition.evaluate() 方法 (Requirements 5.1, 5.2)"""
    
    def test_evaluate_greater_than_returns_true(self):
        """测试 GREATER_THAN 运算符返回 True"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        stock = Mock()
        calc_service = Mock()
        calc_service.calculate_indicator.return_value = 0.20  # 大于 0.15
        
        result = condition.evaluate(stock, calc_service)
        
        assert result is True
        calc_service.calculate_indicator.assert_called_once_with(
            IndicatorField.ROE, stock
        )
    
    def test_evaluate_greater_than_returns_false(self):
        """测试 GREATER_THAN 运算符返回 False"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        stock = Mock()
        calc_service = Mock()
        calc_service.calculate_indicator.return_value = 0.10  # 小于 0.15
        
        result = condition.evaluate(stock, calc_service)
        
        assert result is False
    
    def test_evaluate_between_returns_true(self):
        """测试 BETWEEN 运算符返回 True"""
        condition = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.BETWEEN,
            value=RangeValue(10.0, 30.0)
        )
        
        stock = Mock()
        calc_service = Mock()
        calc_service.calculate_indicator.return_value = 20.0  # 在区间内
        
        result = condition.evaluate(stock, calc_service)
        
        assert result is True
    
    def test_evaluate_between_returns_false(self):
        """测试 BETWEEN 运算符返回 False"""
        condition = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.BETWEEN,
            value=RangeValue(10.0, 30.0)
        )
        
        stock = Mock()
        calc_service = Mock()
        calc_service.calculate_indicator.return_value = 50.0  # 不在区间内
        
        result = condition.evaluate(stock, calc_service)
        
        assert result is False
    
    def test_evaluate_in_returns_true(self):
        """测试 IN 运算符返回 True"""
        condition = FilterCondition(
            field=IndicatorField.INDUSTRY,
            operator=ComparisonOperator.IN,
            value=ListValue(["科技", "医药", "消费"])
        )
        
        stock = Mock()
        calc_service = Mock()
        calc_service.calculate_indicator.return_value = "科技"  # 在列表中
        
        result = condition.evaluate(stock, calc_service)
        
        assert result is True
    
    def test_evaluate_in_returns_false(self):
        """测试 IN 运算符返回 False"""
        condition = FilterCondition(
            field=IndicatorField.INDUSTRY,
            operator=ComparisonOperator.IN,
            value=ListValue(["科技", "医药", "消费"])
        )
        
        stock = Mock()
        calc_service = Mock()
        calc_service.calculate_indicator.return_value = "金融"  # 不在列表中
        
        result = condition.evaluate(stock, calc_service)
        
        assert result is False
    
    def test_evaluate_returns_false_when_indicator_is_none(self):
        """测试指标值为 None 时返回 False (Requirement 5.2)"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        stock = Mock()
        calc_service = Mock()
        calc_service.calculate_indicator.return_value = None  # 数据缺失
        
        result = condition.evaluate(stock, calc_service)
        
        assert result is False
    
    def test_evaluate_equals_returns_true(self):
        """测试 EQUALS 运算符返回 True"""
        condition = FilterCondition(
            field=IndicatorField.INDUSTRY,
            operator=ComparisonOperator.EQUALS,
            value=TextValue("科技")
        )
        
        stock = Mock()
        calc_service = Mock()
        calc_service.calculate_indicator.return_value = "科技"
        
        result = condition.evaluate(stock, calc_service)
        
        assert result is True
    
    def test_evaluate_less_than_returns_true(self):
        """测试 LESS_THAN 运算符返回 True"""
        condition = FilterCondition(
            field=IndicatorField.DEBT_RATIO,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(0.5)
        )
        
        stock = Mock()
        calc_service = Mock()
        calc_service.calculate_indicator.return_value = 0.3
        
        result = condition.evaluate(stock, calc_service)
        
        assert result is True


class TestFilterConditionEquality:
    """测试 FilterCondition 相等性和哈希"""
    
    def test_equal_conditions(self):
        """测试相等的条件"""
        condition1 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        condition2 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        assert condition1 == condition2
        assert hash(condition1) == hash(condition2)
    
    def test_different_field(self):
        """测试不同字段的条件不相等"""
        condition1 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        condition2 = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        assert condition1 != condition2
    
    def test_different_operator(self):
        """测试不同运算符的条件不相等"""
        condition1 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        condition2 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(0.15)
        )
        
        assert condition1 != condition2
    
    def test_different_value(self):
        """测试不同值的条件不相等"""
        condition1 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        condition2 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.20)
        )
        
        assert condition1 != condition2
    
    def test_not_equal_to_non_filter_condition(self):
        """测试与非 FilterCondition 对象不相等"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        assert condition != "not a filter condition"
        assert condition != 123
        assert condition != None


class TestFilterConditionRepr:
    """测试 FilterCondition 字符串表示"""
    
    def test_repr(self):
        """测试 __repr__ 方法"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        repr_str = repr(condition)
        
        assert "FilterCondition" in repr_str
        assert "ROE" in repr_str
        assert ">" in repr_str
