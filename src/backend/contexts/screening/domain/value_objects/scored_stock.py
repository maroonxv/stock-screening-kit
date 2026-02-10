"""
带评分股票值对象定义

ScoredStock 是一个不可变的值对象，表示经过筛选和评分后的股票。
包含股票代码、名称、评分、评分明细、指标值和匹配的条件。

Requirements:
- 3.5: ScoredStock 值对象，包含 stock_code、stock_name、score、score_breakdown、indicator_values、matched_conditions
"""
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .filter_condition import FilterCondition
    from ..enums.indicator_field import IndicatorField

# 导入 StockCode
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from shared_kernel.value_objects.stock_code import StockCode


class ScoredStock:
    """
    带评分股票值对象
    
    表示经过筛选和评分后的股票，包含：
    - stock_code: 股票代码（StockCode）
    - stock_name: 股票名称
    - score: 综合评分
    - score_breakdown: 每个指标的得分贡献（IndicatorField → float）
    - indicator_values: 实际指标值（IndicatorField → Any）
    - matched_conditions: 匹配的筛选条件列表
    """
    
    def __init__(
        self,
        stock_code: StockCode,
        stock_name: str,
        score: float,
        score_breakdown: Optional[Dict['IndicatorField', float]] = None,
        indicator_values: Optional[Dict['IndicatorField', Any]] = None,
        matched_conditions: Optional[List['FilterCondition']] = None
    ):
        """
        构造带评分股票
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            score: 综合评分
            score_breakdown: 每个指标的得分贡献
            indicator_values: 实际指标值
            matched_conditions: 匹配的筛选条件列表
            
        Raises:
            ValueError: 如果股票名称为空
        """
        if not stock_name or not stock_name.strip():
            raise ValueError("股票名称不能为空")
        
        self._stock_code = stock_code
        self._stock_name = stock_name
        self._score = score
        self._score_breakdown = dict(score_breakdown) if score_breakdown else {}
        self._indicator_values = dict(indicator_values) if indicator_values else {}
        self._matched_conditions = list(matched_conditions) if matched_conditions else []
    
    @property
    def stock_code(self) -> StockCode:
        """获取股票代码"""
        return self._stock_code
    
    @property
    def stock_name(self) -> str:
        """获取股票名称"""
        return self._stock_name
    
    @property
    def score(self) -> float:
        """获取综合评分"""
        return self._score
    
    @property
    def score_breakdown(self) -> Dict['IndicatorField', float]:
        """获取评分明细（返回副本以保证不可变性）"""
        return dict(self._score_breakdown)
    
    @property
    def indicator_values(self) -> Dict['IndicatorField', Any]:
        """获取指标值（返回副本以保证不可变性）"""
        return dict(self._indicator_values)
    
    @property
    def matched_conditions(self) -> List['FilterCondition']:
        """获取匹配的条件（返回副本以保证不可变性）"""
        return list(self._matched_conditions)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        from ..enums.indicator_field import IndicatorField
        
        return {
            'stock_code': self._stock_code.code,
            'stock_name': self._stock_name,
            'score': self._score,
            'score_breakdown': {
                field.name: value 
                for field, value in self._score_breakdown.items()
            },
            'indicator_values': {
                field.name: value 
                for field, value in self._indicator_values.items()
            },
            'matched_conditions': [
                cond.to_dict() for cond in self._matched_conditions
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoredStock':
        """
        从字典反序列化
        
        Args:
            data: 包含所有属性的字典
            
        Returns:
            ScoredStock 实例
        """
        from ..enums.indicator_field import IndicatorField
        from .filter_condition import FilterCondition
        
        stock_code = StockCode(data['stock_code'])
        
        score_breakdown = {
            IndicatorField[field_name]: value
            for field_name, value in data.get('score_breakdown', {}).items()
        }
        
        indicator_values = {
            IndicatorField[field_name]: value
            for field_name, value in data.get('indicator_values', {}).items()
        }
        
        matched_conditions = [
            FilterCondition.from_dict(cond_data)
            for cond_data in data.get('matched_conditions', [])
        ]
        
        return cls(
            stock_code=stock_code,
            stock_name=data['stock_name'],
            score=data['score'],
            score_breakdown=score_breakdown,
            indicator_values=indicator_values,
            matched_conditions=matched_conditions
        )
    
    def __eq__(self, other: object) -> bool:
        """判断两个 ScoredStock 是否相等"""
        if not isinstance(other, ScoredStock):
            return False
        return (
            self._stock_code == other._stock_code and
            self._stock_name == other._stock_name and
            self._score == other._score and
            self._score_breakdown == other._score_breakdown and
            self._indicator_values == other._indicator_values and
            len(self._matched_conditions) == len(other._matched_conditions) and
            all(c1 == c2 for c1, c2 in zip(self._matched_conditions, other._matched_conditions))
        )
    
    def __hash__(self) -> int:
        """计算哈希值"""
        return hash((
            self._stock_code,
            self._stock_name,
            self._score
        ))
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return (
            f"ScoredStock(stock_code={self._stock_code}, "
            f"stock_name='{self._stock_name}', "
            f"score={self._score})"
        )
