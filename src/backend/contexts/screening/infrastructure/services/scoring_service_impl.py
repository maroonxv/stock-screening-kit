"""
评分服务实现

ScoringServiceImpl 实现 IScoringService 接口。
使用 min-max 归一化方法对股票进行评分。

Requirements:
- 4.4: IScoringService 接口实现
"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from contexts.screening.domain.services.scoring_service import IScoringService
from contexts.screening.domain.value_objects.scored_stock import ScoredStock
from contexts.screening.domain.enums.enums import NormalizationMethod

if TYPE_CHECKING:
    from contexts.screening.domain.models.stock import Stock
    from contexts.screening.domain.value_objects.scoring_config import ScoringConfig
    from contexts.screening.domain.services.indicator_calculation_service import IIndicatorCalculationService
    from contexts.screening.domain.enums.indicator_field import IndicatorField


class ScoringServiceImpl(IScoringService):
    """
    评分服务实现
    
    实现 IScoringService 接口，负责：
    - 根据 ScoringConfig 中的权重计算每只股票的综合评分
    - 使用 calc_service 获取各指标的实际值
    - 根据 normalization_method 进行归一化处理（支持 min-max、z-score）
    - 返回 ScoredStock 列表，包含评分明细
    """
    
    def score_stocks(
        self,
        stocks: List['Stock'],
        scoring_config: 'ScoringConfig',
        calc_service: 'IIndicatorCalculationService'
    ) -> List[ScoredStock]:
        """
        对股票列表进行评分
        
        根据评分配置对每只股票计算综合评分。
        
        Args:
            stocks: 待评分的股票列表
            scoring_config: 评分配置，包含权重和归一化方法
            calc_service: 指标计算服务，用于获取各指标的实际值
            
        Returns:
            带评分的股票列表（ScoredStock）
        """
        if not stocks:
            return []
        
        weights = scoring_config.weights
        normalization_method = scoring_config.normalization_method
        
        # 获取所有需要评分的指标字段
        indicator_fields = list(weights.keys())
        
        # 收集所有股票的指标值
        stock_indicator_values: List[Dict['IndicatorField', Optional[Any]]] = []
        for stock in stocks:
            values = calc_service.calculate_batch(indicator_fields, stock)
            stock_indicator_values.append(values)
        
        # 计算每个指标的统计信息（用于归一化）
        indicator_stats = self._calculate_indicator_stats(
            indicator_fields, stock_indicator_values
        )
        
        # 对每只股票进行评分
        scored_stocks = []
        for i, stock in enumerate(stocks):
            indicator_values = stock_indicator_values[i]
            
            # 归一化指标值
            normalized_values = self._normalize_values(
                indicator_values, indicator_stats, normalization_method
            )
            
            # 计算评分明细和综合评分
            score_breakdown, total_score = self._calculate_score(
                normalized_values, weights
            )
            
            # 创建 ScoredStock
            scored_stock = ScoredStock(
                stock_code=stock.stock_code,
                stock_name=stock.stock_name,
                score=total_score,
                score_breakdown=score_breakdown,
                indicator_values=indicator_values,
                matched_conditions=[]  # 匹配条件由调用方设置
            )
            scored_stocks.append(scored_stock)
        
        return scored_stocks
    
    def _calculate_indicator_stats(
        self,
        indicator_fields: List['IndicatorField'],
        stock_indicator_values: List[Dict['IndicatorField', Optional[Any]]]
    ) -> Dict['IndicatorField', Dict[str, float]]:
        """
        计算每个指标的统计信息
        
        用于归一化处理。
        
        Args:
            indicator_fields: 指标字段列表
            stock_indicator_values: 所有股票的指标值列表
            
        Returns:
            每个指标的统计信息（min、max、mean、std）
        """
        stats = {}
        
        for field in indicator_fields:
            # 收集该指标的所有有效值
            values = []
            for stock_values in stock_indicator_values:
                value = stock_values.get(field)
                if value is not None and isinstance(value, (int, float)):
                    values.append(float(value))
            
            if not values:
                # 没有有效值，使用默认统计信息
                stats[field] = {
                    'min': 0.0,
                    'max': 1.0,
                    'mean': 0.5,
                    'std': 1.0,
                    'count': 0
                }
            else:
                min_val = min(values)
                max_val = max(values)
                mean_val = sum(values) / len(values)
                
                # 计算标准差
                if len(values) > 1:
                    variance = sum((v - mean_val) ** 2 for v in values) / len(values)
                    std_val = variance ** 0.5
                else:
                    std_val = 1.0
                
                stats[field] = {
                    'min': min_val,
                    'max': max_val,
                    'mean': mean_val,
                    'std': std_val if std_val > 0 else 1.0,  # 避免除零
                    'count': len(values)
                }
        
        return stats
    
    def _normalize_values(
        self,
        indicator_values: Dict['IndicatorField', Optional[Any]],
        indicator_stats: Dict['IndicatorField', Dict[str, float]],
        normalization_method: NormalizationMethod
    ) -> Dict['IndicatorField', Optional[float]]:
        """
        归一化指标值
        
        Args:
            indicator_values: 原始指标值
            indicator_stats: 指标统计信息
            normalization_method: 归一化方法
            
        Returns:
            归一化后的指标值
        """
        normalized = {}
        
        for field, value in indicator_values.items():
            if value is None or not isinstance(value, (int, float)):
                normalized[field] = None
                continue
            
            stats = indicator_stats.get(field, {})
            
            if normalization_method == NormalizationMethod.MIN_MAX:
                normalized[field] = self._min_max_normalize(
                    float(value), stats.get('min', 0), stats.get('max', 1)
                )
            elif normalization_method == NormalizationMethod.Z_SCORE:
                normalized[field] = self._z_score_normalize(
                    float(value), stats.get('mean', 0), stats.get('std', 1)
                )
            else:  # NormalizationMethod.NONE
                normalized[field] = float(value)
        
        return normalized
    
    def _min_max_normalize(
        self,
        value: float,
        min_val: float,
        max_val: float
    ) -> float:
        """
        Min-Max 归一化
        
        公式: (value - min) / (max - min)
        
        Args:
            value: 原始值
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            归一化后的值（0-1 范围）
        """
        if max_val == min_val:
            # 所有值相同，返回 0.5
            return 0.5
        
        normalized = (value - min_val) / (max_val - min_val)
        
        # 确保结果在 [0, 1] 范围内
        return max(0.0, min(1.0, normalized))
    
    def _z_score_normalize(
        self,
        value: float,
        mean: float,
        std: float
    ) -> float:
        """
        Z-Score 归一化
        
        公式: (value - mean) / std
        
        Args:
            value: 原始值
            mean: 均值
            std: 标准差
            
        Returns:
            归一化后的值
        """
        if std == 0:
            return 0.0
        
        return (value - mean) / std
    
    def _calculate_score(
        self,
        normalized_values: Dict['IndicatorField', Optional[float]],
        weights: Dict['IndicatorField', float]
    ) -> tuple[Dict['IndicatorField', float], float]:
        """
        计算评分明细和综合评分
        
        Args:
            normalized_values: 归一化后的指标值
            weights: 权重配置
            
        Returns:
            (评分明细, 综合评分) 元组
        """
        score_breakdown = {}
        total_score = 0.0
        total_weight_used = 0.0
        
        for field, weight in weights.items():
            normalized_value = normalized_values.get(field)
            
            if normalized_value is not None:
                # 计算该指标的得分贡献
                contribution = normalized_value * weight
                score_breakdown[field] = contribution
                total_score += contribution
                total_weight_used += weight
            else:
                # 指标值缺失，得分贡献为 0
                score_breakdown[field] = 0.0
        
        # 如果有缺失的指标，按比例调整总分
        # 这样可以公平比较有不同数据完整度的股票
        if total_weight_used > 0 and total_weight_used < 1.0:
            # 将得分按实际使用的权重比例放大
            total_score = total_score / total_weight_used
        
        return score_breakdown, total_score
