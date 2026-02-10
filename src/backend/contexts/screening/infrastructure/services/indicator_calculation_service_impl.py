"""
指标计算服务实现

IndicatorCalculationServiceImpl 实现 IIndicatorCalculationService 接口。
负责计算基础指标、时间序列指标和衍生指标。

Requirements:
- 4.5: IIndicatorCalculationService 接口实现
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from contexts.screening.domain.services.indicator_calculation_service import IIndicatorCalculationService
from contexts.screening.domain.enums.indicator_field import IndicatorField
from contexts.screening.domain.enums.enums import IndicatorCategory

if TYPE_CHECKING:
    from contexts.screening.domain.models.stock import Stock
    from contexts.screening.domain.repositories.historical_data_provider import IHistoricalDataProvider


class IndicatorCalculationServiceImpl(IIndicatorCalculationService):
    """
    指标计算服务实现
    
    实现 IIndicatorCalculationService 接口，负责：
    - 从 Stock 实体中提取基础指标值
    - 计算衍生指标（如 PE/PB 比率、PEG）
    - 时间序列指标（MVP 阶段返回 None，需要 IHistoricalDataProvider）
    """
    
    # 基础指标到 Stock 属性的映射
    BASIC_INDICATOR_MAPPING = {
        IndicatorField.ROE: 'roe',
        IndicatorField.PE: 'pe',
        IndicatorField.PB: 'pb',
        IndicatorField.EPS: 'eps',
        IndicatorField.REVENUE: 'revenue',
        IndicatorField.NET_PROFIT: 'net_profit',
        IndicatorField.DEBT_RATIO: 'debt_ratio',
        IndicatorField.MARKET_CAP: 'market_cap',
        IndicatorField.INDUSTRY: 'industry',
        IndicatorField.STOCK_NAME: 'stock_name',
    }
    
    # 衍生指标的依赖关系
    DERIVED_INDICATOR_DEPENDENCIES = {
        IndicatorField.PE_PB_RATIO: [IndicatorField.PE, IndicatorField.PB],
        IndicatorField.PEG: [IndicatorField.PE, IndicatorField.EPS_GROWTH_RATE],
        IndicatorField.ROE_PE_PRODUCT: [IndicatorField.ROE, IndicatorField.PE],
        IndicatorField.DEBT_TO_EQUITY: [IndicatorField.DEBT_RATIO],
    }
    
    def __init__(self, historical_data_provider: Optional['IHistoricalDataProvider'] = None):
        """
        构造指标计算服务
        
        Args:
            historical_data_provider: 历史数据提供者（可选，用于时间序列指标）
        """
        self._historical_data_provider = historical_data_provider
    
    def calculate_indicator(
        self,
        field: IndicatorField,
        stock: 'Stock'
    ) -> Optional[Any]:
        """
        计算指定指标的值
        
        根据指标类型（基础、时间序列、衍生）计算对应的值。
        
        Args:
            field: 指标字段（IndicatorField 枚举）
            stock: 股票实体，包含基础财务数据
            
        Returns:
            指标值，如果数据缺失或无法计算，返回 None
        """
        if field.category == IndicatorCategory.BASIC:
            return self._calculate_basic_indicator(field, stock)
        elif field.category == IndicatorCategory.DERIVED:
            return self._calculate_derived_indicator(field, stock)
        elif field.category == IndicatorCategory.TIME_SERIES:
            return self._calculate_time_series_indicator(field, stock)
        else:
            return None
    
    def validate_derived_indicator(
        self,
        field: IndicatorField,
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
        """
        if field.category != IndicatorCategory.DERIVED:
            return True
        
        dependencies = self.DERIVED_INDICATOR_DEPENDENCIES.get(field, [])
        for dep_field in dependencies:
            value = self.calculate_indicator(dep_field, stock)
            if value is None:
                return False
        
        return True
    
    def calculate_batch(
        self,
        fields: List[IndicatorField],
        stock: 'Stock'
    ) -> Dict[IndicatorField, Optional[Any]]:
        """
        批量计算多个指标的值
        
        一次性计算多个指标，提高效率。
        
        Args:
            fields: 指标字段列表
            stock: 股票实体
            
        Returns:
            指标字段到值的映射，值可能为 None（数据缺失）
        """
        result = {}
        for field in fields:
            result[field] = self.calculate_indicator(field, stock)
        return result
    
    def _calculate_basic_indicator(
        self,
        field: IndicatorField,
        stock: 'Stock'
    ) -> Optional[Any]:
        """
        计算基础指标值
        
        直接从 Stock 实体属性获取值。
        
        Args:
            field: 基础指标字段
            stock: 股票实体
            
        Returns:
            指标值，如果属性不存在或为 None，返回 None
        """
        attr_name = self.BASIC_INDICATOR_MAPPING.get(field)
        if attr_name is None:
            return None
        
        return getattr(stock, attr_name, None)
    
    def _calculate_derived_indicator(
        self,
        field: IndicatorField,
        stock: 'Stock'
    ) -> Optional[Any]:
        """
        计算衍生指标值
        
        通过其他指标计算得出。
        
        Args:
            field: 衍生指标字段
            stock: 股票实体
            
        Returns:
            计算结果，如果依赖数据缺失或计算异常，返回 None
        """
        try:
            if field == IndicatorField.PE_PB_RATIO:
                return self._calculate_pe_pb_ratio(stock)
            elif field == IndicatorField.PEG:
                return self._calculate_peg(stock)
            elif field == IndicatorField.ROE_PE_PRODUCT:
                return self._calculate_roe_pe_product(stock)
            elif field == IndicatorField.DEBT_TO_EQUITY:
                return self._calculate_debt_to_equity(stock)
            else:
                return None
        except (ZeroDivisionError, TypeError):
            return None
    
    def _calculate_time_series_indicator(
        self,
        field: IndicatorField,
        stock: 'Stock'
    ) -> Optional[Any]:
        """
        计算时间序列指标值
        
        MVP 阶段：如果没有历史数据提供者，返回 None。
        如果有历史数据提供者，尝试从 Stock 实体获取预计算的值。
        
        Args:
            field: 时间序列指标字段
            stock: 股票实体
            
        Returns:
            指标值，MVP 阶段可能返回 None
        """
        # MVP 阶段：尝试从 Stock 实体获取预计算的时间序列指标
        # 这些指标可能在数据导入时已经计算好
        time_series_mapping = {
            IndicatorField.EPS_GROWTH_RATE: 'profit_growth',  # 使用 profit_growth 作为近似
            IndicatorField.REVENUE_CAGR_3Y: 'revenue_growth',  # 使用 revenue_growth 作为近似
        }
        
        attr_name = time_series_mapping.get(field)
        if attr_name:
            return getattr(stock, attr_name, None)
        
        # 其他时间序列指标需要历史数据，MVP 阶段返回 None
        return None
    
    def _calculate_pe_pb_ratio(self, stock: 'Stock') -> Optional[float]:
        """计算 PE/PB 比率"""
        pe = stock.pe
        pb = stock.pb
        
        if pe is None or pb is None:
            return None
        if pb == 0:
            return None
        
        return pe / pb
    
    def _calculate_peg(self, stock: 'Stock') -> Optional[float]:
        """
        计算 PEG 比率
        
        PEG = PE / EPS增长率
        """
        pe = stock.pe
        eps_growth = self._calculate_time_series_indicator(
            IndicatorField.EPS_GROWTH_RATE, stock
        )
        
        if pe is None or eps_growth is None:
            return None
        if eps_growth == 0:
            return None
        
        # EPS 增长率通常以百分比表示，需要转换
        # 如果增长率是 0.15 表示 15%，则 PEG = PE / 15
        # 如果增长率已经是 15，则 PEG = PE / 15
        # 这里假设增长率是小数形式（如 0.15 表示 15%）
        eps_growth_percent = eps_growth * 100 if abs(eps_growth) < 1 else eps_growth
        
        if eps_growth_percent == 0:
            return None
        
        return pe / eps_growth_percent
    
    def _calculate_roe_pe_product(self, stock: 'Stock') -> Optional[float]:
        """计算 ROE × PE"""
        roe = stock.roe
        pe = stock.pe
        
        if roe is None or pe is None:
            return None
        
        return roe * pe
    
    def _calculate_debt_to_equity(self, stock: 'Stock') -> Optional[float]:
        """
        计算负债权益比
        
        负债权益比 = 资产负债率 / (1 - 资产负债率)
        """
        debt_ratio = stock.debt_ratio
        
        if debt_ratio is None:
            return None
        if debt_ratio >= 1:
            return None  # 资产负债率 >= 100% 时无法计算
        
        return debt_ratio / (1 - debt_ratio)
