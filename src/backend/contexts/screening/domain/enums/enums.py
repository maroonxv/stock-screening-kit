"""
基础枚举类型定义
"""
from enum import Enum


class LogicalOperator(Enum):
    """逻辑运算符枚举"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class IndicatorCategory(Enum):
    """指标分类枚举"""
    BASIC = "基础指标"
    TIME_SERIES = "时间序列指标"
    DERIVED = "衍生指标"


class ValueType(Enum):
    """值类型枚举"""
    NUMERIC = "数值型"
    TEXT = "文本型"
    LIST = "列表型"
    RANGE = "区间型"
    TIME_SERIES = "时间序列型"


class NormalizationMethod(Enum):
    """归一化方法枚举"""
    MIN_MAX = "min_max"
    Z_SCORE = "z_score"
    NONE = "none"
