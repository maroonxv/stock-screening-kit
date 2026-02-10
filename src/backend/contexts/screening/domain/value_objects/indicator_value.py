"""
指标值 Tagged Union 实现
"""
from abc import ABC, abstractmethod
import math
from typing import Any, Dict, List, Tuple, Optional


class IndicatorValue(ABC):
    """指标值抽象基类（Tagged Union）"""
    
    @abstractmethod
    def to_comparable(self) -> Any:
        """转换为可比较的值"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        pass
    
    @classmethod
    def factory_from_dict(cls, data: Dict[str, Any]) -> 'IndicatorValue':
        """从字典反序列化工厂方法"""
        type_map = {
            'numeric': NumericValue,
            'text': TextValue,
            'list': ListValue,
            'range': RangeValue,
            'time_series': TimeSeriesValue,
        }
        value_type = data.get('type')
        if value_type not in type_map:
            raise ValueError(f"未知的指标值类型: {value_type}")
        return type_map[value_type].from_dict(data)


class NumericValue(IndicatorValue):
    """数值型指标值"""
    
    def __init__(self, value: float, unit: Optional[str] = None):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("值不能是 NaN 或 Infinity")
        self._value = value
        self._unit = unit
    
    @property
    def value(self) -> float:
        return self._value
    
    @property
    def unit(self) -> Optional[str]:
        return self._unit
    
    def to_comparable(self) -> float:
        return self._value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'numeric',
            'value': self._value,
            'unit': self._unit
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NumericValue':
        return cls(value=data['value'], unit=data.get('unit'))
    
    def __eq__(self, other):
        return (isinstance(other, NumericValue) and 
                self._value == other._value and 
                self._unit == other._unit)
    
    def __hash__(self):
        return hash((self._value, self._unit))
    
    def __repr__(self):
        if self._unit:
            return f"NumericValue({self._value}, unit='{self._unit}')"
        return f"NumericValue({self._value})"


class TextValue(IndicatorValue):
    """文本型指标值"""
    
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise TypeError("值必须是字符串类型")
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value
    
    def to_comparable(self) -> str:
        return self._value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'text',
            'value': self._value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextValue':
        return cls(value=data['value'])
    
    def __eq__(self, other):
        return isinstance(other, TextValue) and self._value == other._value
    
    def __hash__(self):
        return hash(self._value)
    
    def __repr__(self):
        return f"TextValue('{self._value}')"


class ListValue(IndicatorValue):
    """列表型指标值"""
    
    def __init__(self, values: List[Any]):
        if not isinstance(values, list):
            raise TypeError("值必须是列表类型")
        self._values = values
    
    @property
    def values(self) -> List[Any]:
        return self._values
    
    def to_comparable(self) -> List[Any]:
        return self._values
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'list',
            'values': self._values
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ListValue':
        return cls(values=data['values'])
    
    def __eq__(self, other):
        return isinstance(other, ListValue) and self._values == other._values
    
    def __hash__(self):
        return hash(tuple(self._values))
    
    def __repr__(self):
        return f"ListValue({self._values})"


class RangeValue(IndicatorValue):
    """区间型指标值"""
    
    def __init__(self, min_val: float, max_val: float):
        if min_val > max_val:
            raise ValueError("min 不能大于 max")
        self._min = min_val
        self._max = max_val
    
    @property
    def min_val(self) -> float:
        return self._min
    
    @property
    def max_val(self) -> float:
        return self._max
    
    def to_comparable(self) -> Tuple[float, float]:
        return (self._min, self._max)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'range',
            'min': self._min,
            'max': self._max
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RangeValue':
        return cls(min_val=data['min'], max_val=data['max'])
    
    def __eq__(self, other):
        return (isinstance(other, RangeValue) and 
                self._min == other._min and 
                self._max == other._max)
    
    def __hash__(self):
        return hash((self._min, self._max))
    
    def __repr__(self):
        return f"RangeValue({self._min}, {self._max})"


class TimeSeriesValue(IndicatorValue):
    """时间序列型指标值"""
    
    def __init__(self, years: int, threshold: Optional[float] = None):
        if not isinstance(years, int) or years <= 0:
            raise ValueError("years 必须是正整数")
        self._years = years
        self._threshold = threshold
    
    @property
    def years(self) -> int:
        return self._years
    
    @property
    def threshold(self) -> Optional[float]:
        return self._threshold
    
    def to_comparable(self) -> Dict[str, Any]:
        return {
            'years': self._years,
            'threshold': self._threshold
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'time_series',
            'years': self._years,
            'threshold': self._threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeSeriesValue':
        return cls(years=data['years'], threshold=data.get('threshold'))
    
    def __eq__(self, other):
        return (isinstance(other, TimeSeriesValue) and 
                self._years == other._years and 
                self._threshold == other._threshold)
    
    def __hash__(self):
        return hash((self._years, self._threshold))
    
    def __repr__(self):
        if self._threshold is not None:
            return f"TimeSeriesValue(years={self._years}, threshold={self._threshold})"
        return f"TimeSeriesValue(years={self._years})"
