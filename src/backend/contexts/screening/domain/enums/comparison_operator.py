"""
比较运算符枚举定义
"""
from enum import Enum
from typing import Any


class ComparisonOperator(Enum):
    """
    比较运算符枚举，带 apply() 方法执行实际值与期望值的比较
    """
    GREATER_THAN = ">"
    LESS_THAN = "<"
    EQUALS = "="
    GREATER_OR_EQUAL = ">="
    LESS_OR_EQUAL = "<="
    NOT_EQUALS = "!="
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"
    
    def apply(self, actual: Any, expected: 'IndicatorValue') -> bool:
        """
        应用比较运算符
        
        Args:
            actual: 实际值
            expected: 期望值（IndicatorValue 对象）
            
        Returns:
            比较结果
        """
        # 导入放在方法内部以避免循环导入
        from ..value_objects.indicator_value import (
            NumericValue, TextValue, ListValue, RangeValue, TimeSeriesValue
        )
        
        comparable = expected.to_comparable()
        
        if self == ComparisonOperator.GREATER_THAN:
            return actual > comparable
        elif self == ComparisonOperator.LESS_THAN:
            return actual < comparable
        elif self == ComparisonOperator.EQUALS:
            return actual == comparable
        elif self == ComparisonOperator.GREATER_OR_EQUAL:
            return actual >= comparable
        elif self == ComparisonOperator.LESS_OR_EQUAL:
            return actual <= comparable
        elif self == ComparisonOperator.NOT_EQUALS:
            return actual != comparable
        elif self == ComparisonOperator.IN:
            # comparable 应该是一个列表
            return actual in comparable
        elif self == ComparisonOperator.NOT_IN:
            # comparable 应该是一个列表
            return actual not in comparable
        elif self == ComparisonOperator.BETWEEN:
            # comparable 应该是一个元组 (min, max)
            min_val, max_val = comparable
            return min_val <= actual <= max_val
        elif self == ComparisonOperator.NOT_BETWEEN:
            # comparable 应该是一个元组 (min, max)
            min_val, max_val = comparable
            return not (min_val <= actual <= max_val)
        else:
            raise ValueError(f"未知的比较运算符: {self}")
