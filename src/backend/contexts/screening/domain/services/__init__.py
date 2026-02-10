"""
领域服务接口

本模块定义领域服务的抽象接口。
领域层定义接口，基础设施层提供实现。

包含：
- IScoringService: 评分服务接口
- IIndicatorCalculationService: 指标计算服务接口
"""
from .scoring_service import IScoringService
from .indicator_calculation_service import IIndicatorCalculationService

__all__ = [
    'IScoringService',
    'IIndicatorCalculationService',
]
