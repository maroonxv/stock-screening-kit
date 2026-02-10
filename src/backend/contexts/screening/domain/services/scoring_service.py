"""
评分服务接口定义

IScoringService 定义了股票评分的抽象接口。
领域层定义接口，基础设施层提供实现。

Requirements:
- 4.4: IScoringService 接口，包含 score_stocks() 方法
"""
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.stock import Stock
    from ..value_objects.scoring_config import ScoringConfig
    from ..value_objects.scored_stock import ScoredStock


class IScoringService(ABC):
    """
    评分服务接口
    
    定义股票评分的抽象方法。接收股票列表、评分配置和指标计算服务，
    返回带评分的股票列表。
    
    实现类应在基础设施层提供，负责：
    - 根据 ScoringConfig 中的权重计算每只股票的综合评分
    - 使用 calc_service 获取各指标的实际值
    - 根据 normalization_method 进行归一化处理
    - 返回 ScoredStock 列表，包含评分明细
    """
    
    @abstractmethod
    def score_stocks(
        self,
        stocks: List['Stock'],
        scoring_config: 'ScoringConfig',
        calc_service: 'IIndicatorCalculationService'
    ) -> List['ScoredStock']:
        """
        对股票列表进行评分
        
        根据评分配置对每只股票计算综合评分。
        
        Args:
            stocks: 待评分的股票列表
            scoring_config: 评分配置，包含权重和归一化方法
            calc_service: 指标计算服务，用于获取各指标的实际值
            
        Returns:
            带评分的股票列表（ScoredStock），包含：
            - stock_code: 股票代码
            - stock_name: 股票名称
            - score: 综合评分
            - score_breakdown: 每个指标的得分贡献
            - indicator_values: 实际指标值
            - matched_conditions: 匹配的筛选条件（可选）
            
        Note:
            - 评分计算应考虑数据缺失的情况
            - 归一化方法由 scoring_config.normalization_method 指定
            - 返回的列表顺序不保证，调用方需自行排序
        """
        pass


# 为了避免循环导入，在这里声明类型别名
# 实际的 IIndicatorCalculationService 定义在 indicator_calculation_service.py 中
from typing import Protocol, Any, Optional


class IIndicatorCalculationService(Protocol):
    """指标计算服务协议（用于类型提示）"""
    
    def calculate_indicator(
        self,
        field: Any,
        stock: Any
    ) -> Optional[Any]:
        """计算指定指标的值"""
        ...
