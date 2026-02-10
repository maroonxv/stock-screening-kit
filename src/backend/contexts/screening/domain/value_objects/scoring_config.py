"""
评分配置值对象定义
"""
from typing import Dict, Any
from ..enums.indicator_field import IndicatorField
from ..enums.enums import NormalizationMethod


class ScoringConfig:
    """
    评分配置值对象
    
    包含权重映射和归一化方法
    """
    
    # 浮点数比较的容差
    TOLERANCE = 1e-6
    
    def __init__(self, weights: Dict[IndicatorField, float], 
                 normalization_method: NormalizationMethod = NormalizationMethod.MIN_MAX):
        """
        Args:
            weights: 指标字段到权重的映射
            normalization_method: 归一化方法
            
        Raises:
            ValueError: 如果权重之和不等于 1.0（在容差范围内）
        """
        if not weights:
            raise ValueError("权重映射不能为空")
        
        # 验证权重之和等于 1.0（在容差范围内）
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > self.TOLERANCE:
            raise ValueError(
                f"权重之和必须等于 1.0，当前为 {total_weight}"
            )
        
        # 验证所有权重都是非负数
        for field, weight in weights.items():
            if weight < 0:
                raise ValueError(f"权重不能为负数: {field.name} = {weight}")
        
        self._weights = dict(weights)  # 创建副本以保证不可变性
        self._normalization_method = normalization_method
    
    @property
    def weights(self) -> Dict[IndicatorField, float]:
        """获取权重映射（返回副本以保证不可变性）"""
        return dict(self._weights)
    
    @property
    def normalization_method(self) -> NormalizationMethod:
        """获取归一化方法"""
        return self._normalization_method
    
    def get_weight(self, field: IndicatorField) -> float:
        """
        获取指定字段的权重
        
        Args:
            field: 指标字段
            
        Returns:
            权重值，如果字段不存在则返回 0.0
        """
        return self._weights.get(field, 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'weights': {field.name: weight for field, weight in self._weights.items()},
            'normalization_method': self._normalization_method.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoringConfig':
        """
        从字典反序列化
        
        Args:
            data: 包含 weights 和 normalization_method 的字典
            
        Returns:
            ScoringConfig 实例
        """
        weights = {
            IndicatorField[field_name]: weight 
            for field_name, weight in data['weights'].items()
        }
        normalization_method = NormalizationMethod(data['normalization_method'])
        return cls(weights=weights, normalization_method=normalization_method)
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ScoringConfig):
            return False
        return (self._weights == other._weights and 
                self._normalization_method == other._normalization_method)
    
    def __hash__(self) -> int:
        # 将字典转换为可哈希的元组
        weights_tuple = tuple(sorted(
            (field.name, weight) for field, weight in self._weights.items()
        ))
        return hash((weights_tuple, self._normalization_method))
    
    def __repr__(self) -> str:
        weights_str = ', '.join(
            f"{field.name}: {weight}" 
            for field, weight in self._weights.items()
        )
        return f"ScoringConfig(weights={{{weights_str}}}, normalization_method={self._normalization_method.value})"
