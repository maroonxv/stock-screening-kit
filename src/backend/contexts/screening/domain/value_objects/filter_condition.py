"""
筛选条件值对象实现

FilterCondition 是一个不可变的值对象，描述单个筛选规则。
包含字段（IndicatorField）、运算符（ComparisonOperator）和值（IndicatorValue）。

Requirements:
- 3.1: FilterCondition 值对象，包含 field、operator 和 value
- 3.9: 类型不匹配时抛出 TypeError
- 3.11: 支持 to_dict() 和 from_dict() 序列化
- 5.1: evaluate() 方法计算指标值并应用比较运算符
- 5.2: evaluate() 遇到 None 指标值时返回 False
"""
from typing import Any, Dict, TYPE_CHECKING

from ..enums.indicator_field import IndicatorField
from ..enums.comparison_operator import ComparisonOperator
from ..enums.enums import ValueType
from .indicator_value import (
    IndicatorValue,
    NumericValue,
    TextValue,
    ListValue,
    RangeValue,
    TimeSeriesValue
)

if TYPE_CHECKING:
    # 避免循环导入，仅用于类型提示
    pass


class FilterCondition:
    """
    筛选条件值对象
    
    描述单个筛选规则，包含：
    - field: 指标字段（IndicatorField）
    - operator: 比较运算符（ComparisonOperator）
    - value: 期望值（IndicatorValue）
    
    构造时会验证类型匹配：
    - NUMERIC 类型字段需要 NumericValue、RangeValue 或 TimeSeriesValue
    - TEXT 类型字段需要 TextValue 或 ListValue
    - IN/NOT_IN 运算符需要 ListValue
    - BETWEEN/NOT_BETWEEN 运算符需要 RangeValue
    """
    
    def __init__(self, field: IndicatorField, operator: ComparisonOperator,
                 value: IndicatorValue):
        """
        构造筛选条件
        
        Args:
            field: 指标字段
            operator: 比较运算符
            value: 期望值
            
        Raises:
            TypeError: 字段类型与值类型不匹配
            ValueError: 运算符与值类型不匹配
        """
        self._validate_type_match(field, operator, value)
        self._field = field
        self._operator = operator
        self._value = value
    
    def _validate_type_match(self, field: IndicatorField, 
                             operator: ComparisonOperator,
                             value: IndicatorValue) -> None:
        """
        验证类型匹配
        
        Args:
            field: 指标字段
            operator: 比较运算符
            value: 期望值
            
        Raises:
            TypeError: 字段类型与值类型不匹配
            ValueError: 运算符与值类型不匹配
        """
        # 验证字段类型与值类型匹配
        if field.value_type == ValueType.NUMERIC:
            if not isinstance(value, (NumericValue, RangeValue, TimeSeriesValue)):
                raise TypeError(f"字段 {field.name} 需要数值类型的值")
        
        if field.value_type == ValueType.TEXT:
            if not isinstance(value, (TextValue, ListValue)):
                raise TypeError(f"字段 {field.name} 需要文本类型的值")
        
        # 验证运算符与值类型匹配
        if operator in (ComparisonOperator.IN, ComparisonOperator.NOT_IN):
            if not isinstance(value, ListValue):
                raise ValueError(f"运算符 {operator.value} 需要 ListValue")
        
        if operator in (ComparisonOperator.BETWEEN, ComparisonOperator.NOT_BETWEEN):
            if not isinstance(value, RangeValue):
                raise ValueError(f"运算符 {operator.value} 需要 RangeValue")
    
    @property
    def field(self) -> IndicatorField:
        """获取指标字段"""
        return self._field
    
    @property
    def operator(self) -> ComparisonOperator:
        """获取比较运算符"""
        return self._operator
    
    @property
    def value(self) -> IndicatorValue:
        """获取期望值"""
        return self._value
    
    def evaluate(self, stock: Any, calc_service: Any) -> bool:
        """
        评估筛选条件
        
        使用 calc_service 计算股票的指标值，然后应用比较运算符。
        
        Args:
            stock: 股票实体
            calc_service: 指标计算服务（IIndicatorCalculationService）
            
        Returns:
            如果股票满足条件返回 True，否则返回 False
            如果指标值为 None（数据缺失），返回 False
        """
        # 计算实际指标值
        actual = calc_service.calculate_indicator(self._field, stock)
        
        # 如果指标值为 None（数据缺失），返回 False
        if actual is None:
            return False
        
        # 应用比较运算符
        return self._operator.apply(actual, self._value)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含 field、operator 和 value 的字典
        """
        return {
            'field': self._field.name,
            'operator': self._operator.value,
            'value': self._value.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterCondition':
        """
        从字典反序列化
        
        Args:
            data: 包含 field、operator 和 value 的字典
            
        Returns:
            FilterCondition 实例
            
        Raises:
            KeyError: 缺少必要字段
            ValueError: 无效的枚举值
        """
        field = IndicatorField[data['field']]
        operator = ComparisonOperator(data['operator'])
        value = IndicatorValue.factory_from_dict(data['value'])
        return cls(field=field, operator=operator, value=value)
    
    def __eq__(self, other: object) -> bool:
        """判断两个 FilterCondition 是否相等"""
        if not isinstance(other, FilterCondition):
            return False
        return (self._field == other._field and
                self._operator == other._operator and
                self._value.to_dict() == other._value.to_dict())
    
    def __hash__(self) -> int:
        """计算哈希值"""
        return hash((self._field, self._operator, str(self._value.to_dict())))
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return (f"FilterCondition(field={self._field.name}, "
                f"operator={self._operator.value}, "
                f"value={self._value})")
