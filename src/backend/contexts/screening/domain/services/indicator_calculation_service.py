"""
指标计算服务接口定义

IIndicatorCalculationService 定义了指标计算的抽象接口。
领域层定义接口，基础设施层提供实现。

Requirements:
- 4.5: IIndicatorCalculationService 接口，包含 calculate_indicator()、
       validate_derived_indicator() 和 calculate_batch() 方法
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..enums.indicator_field import IndicatorField
    from ..models.stock import Stock


class IIndicatorCalculationService(ABC):
    """
    指标计算服务接口
    
    定义指标计算的抽象方法。负责：
    - 计算单个指标的值（基础指标、时间序列指标、衍生指标）
    - 验证衍生指标的计算是否可行
    - 批量计算多个指标的值
    
    实现类应在基础设施层提供，负责：
    - 从 Stock 实体中提取基础指标值
    - 计算时间序列指标（如连续增长年数、复合增长率）
    - 计算衍生指标（如 PE/PB 比率、PEG）
    - 处理数据缺失的情况
    """
    
    @abstractmethod
    def calculate_indicator(
        self,
        field: 'IndicatorField',
        stock: 'Stock'
    ) -> Optional[Any]:
        """
        计算指定指标的值
        
        根据指标类型（基础、时间序列、衍生）计算对应的值。
        
        Args:
            field: 指标字段（IndicatorField 枚举）
            stock: 股票实体，包含基础财务数据
            
        Returns:
            指标值，类型取决于 field.value_type：
            - NUMERIC: float
            - TEXT: str
            如果数据缺失或无法计算，返回 None
            
        Note:
            - 基础指标直接从 Stock 实体属性获取
            - 时间序列指标可能需要历史数据（通过 IHistoricalDataProvider）
            - 衍生指标通过其他指标计算得出
            - 计算过程中遇到除零等异常应返回 None
        """
        pass
    
    @abstractmethod
    def validate_derived_indicator(
        self,
        field: 'IndicatorField',
        stock: 'Stock'
    ) -> bool:
        """
        验证衍生指标是否可以计算
        
        检查计算衍生指标所需的基础数据是否完整。
        
        Args:
            field: 衍生指标字段
            stock: 股票实体
            
        Returns:
            如果可以计算返回 True，否则返回 False
            
        Note:
            - 仅对 DERIVED 类别的指标有意义
            - 检查所有依赖的基础指标是否存在且有效
            - 例如 PEG 需要 PE 和盈利增长率都存在
        """
        pass
    
    @abstractmethod
    def calculate_batch(
        self,
        fields: List['IndicatorField'],
        stock: 'Stock'
    ) -> Dict['IndicatorField', Optional[Any]]:
        """
        批量计算多个指标的值
        
        一次性计算多个指标，提高效率。
        
        Args:
            fields: 指标字段列表
            stock: 股票实体
            
        Returns:
            指标字段到值的映射，值可能为 None（数据缺失）
            
        Note:
            - 实现可以优化重复计算（如多个衍生指标依赖同一基础指标）
            - 返回的字典包含所有请求的字段，即使值为 None
        """
        pass
