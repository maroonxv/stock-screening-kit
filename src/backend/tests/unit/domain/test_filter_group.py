"""
FilterGroup 实体单元测试

测试 FilterGroup 的核心功能：
- 构造和属性访问
- match() 方法的逻辑运算（AND/OR/NOT）
- has_any_condition() 辅助方法
- count_total_conditions() 辅助方法
- to_dict() / from_dict() 序列化

Requirements:
- 2.4: FilterGroup 实体，支持 AND/OR/NOT 逻辑运算符的递归结构
- 5.3: AND 运算符 - 所有条件和子组都匹配时返回 True
- 5.4: OR 运算符 - 至少一个条件或子组匹配时返回 True
- 5.5: NOT 运算符 - 对单个子元素的结果取反
- 3.12: 支持 to_dict() 和 from_dict() 序列化
"""
import pytest
import uuid
from unittest.mock import Mock, MagicMock

from contexts.screening.domain.models.filter_group import FilterGroup
from contexts.screening.domain.enums.enums import LogicalOperator
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.comparison_operator import ComparisonOperator
from contexts.screening.domain.value_objects.filter_condition import FilterCondition
from contexts.screening.domain.value_objects.indicator_value import NumericValue


class TestFilterGroupConstruction:
    """FilterGroup 构造测试"""
    
    def test_create_with_required_params(self):
        """测试使用必需参数创建 FilterGroup"""
        group_id = str(uuid.uuid4())
        group = FilterGroup(
            group_id=group_id,
            operator=LogicalOperator.AND
        )
        
        assert group.group_id == group_id
        assert group.operator == LogicalOperator.AND
        assert group.conditions == []
        assert group.sub_groups == []
    
    def test_create_with_conditions(self):
        """测试使用条件创建 FilterGroup"""
        group_id = str(uuid.uuid4())
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        group = FilterGroup(
            group_id=group_id,
            operator=LogicalOperator.AND,
            conditions=[condition]
        )
        
        assert len(group.conditions) == 1
        assert group.conditions[0] == condition
    
    def test_create_with_sub_groups(self):
        """测试使用子组创建 FilterGroup"""
        parent_id = str(uuid.uuid4())
        child_id = str(uuid.uuid4())
        
        child_group = FilterGroup(
            group_id=child_id,
            operator=LogicalOperator.OR
        )
        
        parent_group = FilterGroup(
            group_id=parent_id,
            operator=LogicalOperator.AND,
            sub_groups=[child_group]
        )
        
        assert len(parent_group.sub_groups) == 1
        assert parent_group.sub_groups[0].group_id == child_id
    
    def test_conditions_property_returns_copy(self):
        """测试 conditions 属性返回副本"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition]
        )
        
        # 修改返回的列表不应影响原始数据
        conditions = group.conditions
        conditions.clear()
        
        assert len(group.conditions) == 1
    
    def test_sub_groups_property_returns_copy(self):
        """测试 sub_groups 属性返回副本"""
        child_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR
        )
        
        parent_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            sub_groups=[child_group]
        )
        
        # 修改返回的列表不应影响原始数据
        sub_groups = parent_group.sub_groups
        sub_groups.clear()
        
        assert len(parent_group.sub_groups) == 1


class TestFilterGroupMatch:
    """FilterGroup.match() 方法测试"""
    
    def _create_mock_calc_service(self, indicator_values: dict):
        """创建模拟的指标计算服务"""
        calc_service = Mock()
        calc_service.calculate_indicator = Mock(
            side_effect=lambda field, stock: indicator_values.get(field)
        )
        return calc_service
    
    def _create_mock_stock(self):
        """创建模拟的股票实体"""
        return Mock()
    
    def test_and_empty_group_returns_true(self):
        """测试 AND 空组返回 True"""
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND
        )
        
        stock = self._create_mock_stock()
        calc_service = self._create_mock_calc_service({})
        
        assert group.match(stock, calc_service) is True
    
    def test_or_empty_group_returns_false(self):
        """测试 OR 空组返回 False"""
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR
        )
        
        stock = self._create_mock_stock()
        calc_service = self._create_mock_calc_service({})
        
        assert group.match(stock, calc_service) is False
    
    def test_not_empty_group_returns_true(self):
        """测试 NOT 空组返回 True"""
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.NOT
        )
        
        stock = self._create_mock_stock()
        calc_service = self._create_mock_calc_service({})
        
        assert group.match(stock, calc_service) is True
    
    def test_and_all_conditions_true(self):
        """测试 AND 运算符 - 所有条件为真时返回 True"""
        condition1 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.10)
        )
        condition2 = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(30.0)
        )
        
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition1, condition2]
        )
        
        stock = self._create_mock_stock()
        calc_service = self._create_mock_calc_service({
            IndicatorField.ROE: 0.20,  # > 0.10, True
            IndicatorField.PE: 20.0    # < 30.0, True
        })
        
        assert group.match(stock, calc_service) is True
    
    def test_and_one_condition_false(self):
        """测试 AND 运算符 - 一个条件为假时返回 False"""
        condition1 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.10)
        )
        condition2 = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(30.0)
        )
        
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition1, condition2]
        )
        
        stock = self._create_mock_stock()
        calc_service = self._create_mock_calc_service({
            IndicatorField.ROE: 0.05,  # > 0.10, False
            IndicatorField.PE: 20.0    # < 30.0, True
        })
        
        assert group.match(stock, calc_service) is False
    
    def test_or_one_condition_true(self):
        """测试 OR 运算符 - 一个条件为真时返回 True"""
        condition1 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.10)
        )
        condition2 = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(30.0)
        )
        
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR,
            conditions=[condition1, condition2]
        )
        
        stock = self._create_mock_stock()
        calc_service = self._create_mock_calc_service({
            IndicatorField.ROE: 0.05,  # > 0.10, False
            IndicatorField.PE: 20.0    # < 30.0, True
        })
        
        assert group.match(stock, calc_service) is True
    
    def test_or_all_conditions_false(self):
        """测试 OR 运算符 - 所有条件为假时返回 False"""
        condition1 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.10)
        )
        condition2 = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(30.0)
        )
        
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR,
            conditions=[condition1, condition2]
        )
        
        stock = self._create_mock_stock()
        calc_service = self._create_mock_calc_service({
            IndicatorField.ROE: 0.05,  # > 0.10, False
            IndicatorField.PE: 40.0    # < 30.0, False
        })
        
        assert group.match(stock, calc_service) is False
    
    def test_not_negates_true_condition(self):
        """测试 NOT 运算符 - 对真条件取反返回 False"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.10)
        )
        
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.NOT,
            conditions=[condition]
        )
        
        stock = self._create_mock_stock()
        calc_service = self._create_mock_calc_service({
            IndicatorField.ROE: 0.20  # > 0.10, True -> NOT -> False
        })
        
        assert group.match(stock, calc_service) is False
    
    def test_not_negates_false_condition(self):
        """测试 NOT 运算符 - 对假条件取反返回 True"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.10)
        )
        
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.NOT,
            conditions=[condition]
        )
        
        stock = self._create_mock_stock()
        calc_service = self._create_mock_calc_service({
            IndicatorField.ROE: 0.05  # > 0.10, False -> NOT -> True
        })
        
        assert group.match(stock, calc_service) is True
    
    def test_nested_groups(self):
        """测试嵌套条件组"""
        # 构建: (ROE > 0.10 AND PE < 30) OR (PB < 2)
        condition_roe = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.10)
        )
        condition_pe = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(30.0)
        )
        condition_pb = FilterCondition(
            field=IndicatorField.PB,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(2.0)
        )
        
        # AND 子组: ROE > 0.10 AND PE < 30
        and_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition_roe, condition_pe]
        )
        
        # OR 子组: PB < 2
        pb_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition_pb]
        )
        
        # 根组: (AND子组) OR (PB子组)
        root_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR,
            sub_groups=[and_group, pb_group]
        )
        
        stock = self._create_mock_stock()
        
        # 测试1: AND子组为真 (ROE=0.20 > 0.10, PE=20 < 30)
        calc_service1 = self._create_mock_calc_service({
            IndicatorField.ROE: 0.20,
            IndicatorField.PE: 20.0,
            IndicatorField.PB: 3.0  # PB子组为假
        })
        assert root_group.match(stock, calc_service1) is True
        
        # 测试2: PB子组为真 (PB=1.5 < 2)
        calc_service2 = self._create_mock_calc_service({
            IndicatorField.ROE: 0.05,  # AND子组为假
            IndicatorField.PE: 40.0,
            IndicatorField.PB: 1.5
        })
        assert root_group.match(stock, calc_service2) is True
        
        # 测试3: 两个子组都为假
        calc_service3 = self._create_mock_calc_service({
            IndicatorField.ROE: 0.05,
            IndicatorField.PE: 40.0,
            IndicatorField.PB: 3.0
        })
        assert root_group.match(stock, calc_service3) is False


class TestFilterGroupHelperMethods:
    """FilterGroup 辅助方法测试"""
    
    def test_has_any_condition_empty_group(self):
        """测试空组没有条件"""
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND
        )
        
        assert group.has_any_condition() is False
    
    def test_has_any_condition_with_direct_condition(self):
        """测试有直接条件"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition]
        )
        
        assert group.has_any_condition() is True
    
    def test_has_any_condition_with_nested_condition(self):
        """测试嵌套子组中有条件"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        child_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition]
        )
        
        parent_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR,
            sub_groups=[child_group]
        )
        
        assert parent_group.has_any_condition() is True
    
    def test_has_any_condition_empty_nested_groups(self):
        """测试嵌套空子组"""
        child_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND
        )
        
        parent_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR,
            sub_groups=[child_group]
        )
        
        assert parent_group.has_any_condition() is False
    
    def test_count_total_conditions_empty_group(self):
        """测试空组条件数为0"""
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND
        )
        
        assert group.count_total_conditions() == 0
    
    def test_count_total_conditions_with_direct_conditions(self):
        """测试直接条件计数"""
        condition1 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        condition2 = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(30.0)
        )
        
        group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition1, condition2]
        )
        
        assert group.count_total_conditions() == 2
    
    def test_count_total_conditions_with_nested_groups(self):
        """测试嵌套组条件计数"""
        condition1 = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        condition2 = FilterCondition(
            field=IndicatorField.PE,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(30.0)
        )
        condition3 = FilterCondition(
            field=IndicatorField.PB,
            operator=ComparisonOperator.LESS_THAN,
            value=NumericValue(2.0)
        )
        
        child_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            conditions=[condition2, condition3]
        )
        
        parent_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR,
            conditions=[condition1],
            sub_groups=[child_group]
        )
        
        assert parent_group.count_total_conditions() == 3


class TestFilterGroupSerialization:
    """FilterGroup 序列化测试"""
    
    def test_to_dict_empty_group(self):
        """测试空组序列化"""
        group_id = str(uuid.uuid4())
        group = FilterGroup(
            group_id=group_id,
            operator=LogicalOperator.AND
        )
        
        result = group.to_dict()
        
        assert result['group_id'] == group_id
        assert result['operator'] == 'AND'
        assert result['conditions'] == []
        assert result['sub_groups'] == []
    
    def test_to_dict_with_conditions(self):
        """测试带条件的组序列化"""
        group_id = str(uuid.uuid4())
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        group = FilterGroup(
            group_id=group_id,
            operator=LogicalOperator.AND,
            conditions=[condition]
        )
        
        result = group.to_dict()
        
        assert len(result['conditions']) == 1
        assert result['conditions'][0]['field'] == 'ROE'
        assert result['conditions'][0]['operator'] == '>'
    
    def test_to_dict_with_nested_groups(self):
        """测试带嵌套组的序列化"""
        parent_id = str(uuid.uuid4())
        child_id = str(uuid.uuid4())
        
        child_group = FilterGroup(
            group_id=child_id,
            operator=LogicalOperator.OR
        )
        
        parent_group = FilterGroup(
            group_id=parent_id,
            operator=LogicalOperator.AND,
            sub_groups=[child_group]
        )
        
        result = parent_group.to_dict()
        
        assert len(result['sub_groups']) == 1
        assert result['sub_groups'][0]['group_id'] == child_id
        assert result['sub_groups'][0]['operator'] == 'OR'
    
    def test_from_dict_empty_group(self):
        """测试空组反序列化"""
        group_id = str(uuid.uuid4())
        data = {
            'group_id': group_id,
            'operator': 'AND',
            'conditions': [],
            'sub_groups': []
        }
        
        group = FilterGroup.from_dict(data)
        
        assert group.group_id == group_id
        assert group.operator == LogicalOperator.AND
        assert group.conditions == []
        assert group.sub_groups == []
    
    def test_from_dict_with_conditions(self):
        """测试带条件的组反序列化"""
        group_id = str(uuid.uuid4())
        data = {
            'group_id': group_id,
            'operator': 'AND',
            'conditions': [
                {
                    'field': 'ROE',
                    'operator': '>',
                    'value': {'type': 'numeric', 'value': 0.15}
                }
            ],
            'sub_groups': []
        }
        
        group = FilterGroup.from_dict(data)
        
        assert len(group.conditions) == 1
        assert group.conditions[0].field == IndicatorField.ROE
        assert group.conditions[0].operator == ComparisonOperator.GREATER_THAN
    
    def test_from_dict_with_nested_groups(self):
        """测试带嵌套组的反序列化"""
        parent_id = str(uuid.uuid4())
        child_id = str(uuid.uuid4())
        data = {
            'group_id': parent_id,
            'operator': 'AND',
            'conditions': [],
            'sub_groups': [
                {
                    'group_id': child_id,
                    'operator': 'OR',
                    'conditions': [],
                    'sub_groups': []
                }
            ]
        }
        
        group = FilterGroup.from_dict(data)
        
        assert len(group.sub_groups) == 1
        assert group.sub_groups[0].group_id == child_id
        assert group.sub_groups[0].operator == LogicalOperator.OR
    
    def test_from_dict_generates_group_id_if_missing(self):
        """测试缺少 group_id 时自动生成"""
        data = {
            'operator': 'AND',
            'conditions': [],
            'sub_groups': []
        }
        
        group = FilterGroup.from_dict(data)
        
        # 应该生成一个有效的 UUID
        assert group.group_id is not None
        uuid.UUID(group.group_id)  # 验证是有效的 UUID
    
    def test_serialization_round_trip(self):
        """测试序列化往返"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        
        child_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR,
            conditions=[condition]
        )
        
        original = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.AND,
            sub_groups=[child_group]
        )
        
        # 序列化然后反序列化
        data = original.to_dict()
        restored = FilterGroup.from_dict(data)
        
        # 验证相等
        assert restored == original


class TestFilterGroupEquality:
    """FilterGroup 相等性测试"""
    
    def test_equal_empty_groups(self):
        """测试相等的空组"""
        group_id = str(uuid.uuid4())
        group1 = FilterGroup(group_id=group_id, operator=LogicalOperator.AND)
        group2 = FilterGroup(group_id=group_id, operator=LogicalOperator.AND)
        
        assert group1 == group2
    
    def test_not_equal_different_ids(self):
        """测试不同 ID 的组不相等"""
        group1 = FilterGroup(group_id=str(uuid.uuid4()), operator=LogicalOperator.AND)
        group2 = FilterGroup(group_id=str(uuid.uuid4()), operator=LogicalOperator.AND)
        
        assert group1 != group2
    
    def test_not_equal_different_operators(self):
        """测试不同运算符的组不相等"""
        group_id = str(uuid.uuid4())
        group1 = FilterGroup(group_id=group_id, operator=LogicalOperator.AND)
        group2 = FilterGroup(group_id=group_id, operator=LogicalOperator.OR)
        
        assert group1 != group2
    
    def test_not_equal_to_non_filter_group(self):
        """测试与非 FilterGroup 对象不相等"""
        group = FilterGroup(group_id=str(uuid.uuid4()), operator=LogicalOperator.AND)
        
        assert group != "not a filter group"
        assert group != 123
        assert group != None


class TestFilterGroupRepr:
    """FilterGroup __repr__ 测试"""
    
    def test_repr_empty_group(self):
        """测试空组的字符串表示"""
        group_id = "test-id"
        group = FilterGroup(group_id=group_id, operator=LogicalOperator.AND)
        
        repr_str = repr(group)
        
        assert "FilterGroup" in repr_str
        assert "test-id" in repr_str
        assert "AND" in repr_str
        assert "conditions=0" in repr_str
        assert "sub_groups=0" in repr_str
    
    def test_repr_with_conditions_and_sub_groups(self):
        """测试带条件和子组的字符串表示"""
        condition = FilterCondition(
            field=IndicatorField.ROE,
            operator=ComparisonOperator.GREATER_THAN,
            value=NumericValue(0.15)
        )
        child_group = FilterGroup(
            group_id=str(uuid.uuid4()),
            operator=LogicalOperator.OR
        )
        
        group = FilterGroup(
            group_id="parent-id",
            operator=LogicalOperator.AND,
            conditions=[condition],
            sub_groups=[child_group]
        )
        
        repr_str = repr(group)
        
        assert "conditions=1" in repr_str
        assert "sub_groups=1" in repr_str
