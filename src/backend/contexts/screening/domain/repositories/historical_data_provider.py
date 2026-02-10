"""
历史数据提供者接口定义

IHistoricalDataProvider 定义了获取股票历史数据的抽象接口。
领域层定义接口，基础设施层提供实现。

用于支持时间序列指标的计算，如：
- ROE 连续增长年数
- 营收复合增长率
- 净利润复合增长率

Requirements:
- 4.4, 4.5: 领域层定义接口，支持时间序列指标计算
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from shared_kernel.value_objects.stock_code import StockCode


class IHistoricalDataProvider(ABC):
    """
    历史数据提供者接口
    
    定义获取股票历史财务数据的抽象方法。
    用于支持时间序列指标的计算。
    
    实现类应在基础设施层提供，负责：
    - 从数据源获取历史财务数据
    - 缓存常用数据以提高性能
    - 处理数据缺失的情况
    """
    
    @abstractmethod
    def get_historical_roe(
        self,
        stock_code: 'StockCode',
        years: int
    ) -> List[Optional[float]]:
        """
        获取历史 ROE 数据
        
        Args:
            stock_code: 股票代码
            years: 需要的年数
            
        Returns:
            ROE 列表，按年份从近到远排列。
            如果某年数据缺失，对应位置为 None。
            列表长度等于 years。
        """
        pass
    
    @abstractmethod
    def get_historical_revenue(
        self,
        stock_code: 'StockCode',
        years: int
    ) -> List[Optional[float]]:
        """
        获取历史营业收入数据
        
        Args:
            stock_code: 股票代码
            years: 需要的年数
            
        Returns:
            营业收入列表，按年份从近到远排列。
            如果某年数据缺失，对应位置为 None。
            列表长度等于 years。
        """
        pass
    
    @abstractmethod
    def get_historical_net_profit(
        self,
        stock_code: 'StockCode',
        years: int
    ) -> List[Optional[float]]:
        """
        获取历史净利润数据
        
        Args:
            stock_code: 股票代码
            years: 需要的年数
            
        Returns:
            净利润列表，按年份从近到远排列。
            如果某年数据缺失，对应位置为 None。
            列表长度等于 years。
        """
        pass
    
    @abstractmethod
    def get_historical_eps(
        self,
        stock_code: 'StockCode',
        years: int
    ) -> List[Optional[float]]:
        """
        获取历史每股收益数据
        
        Args:
            stock_code: 股票代码
            years: 需要的年数
            
        Returns:
            EPS 列表，按年份从近到远排列。
            如果某年数据缺失，对应位置为 None。
            列表长度等于 years。
        """
        pass
    
    @abstractmethod
    def get_historical_indicator(
        self,
        stock_code: 'StockCode',
        indicator_name: str,
        years: int
    ) -> List[Optional[float]]:
        """
        获取指定指标的历史数据
        
        通用方法，用于获取任意指标的历史数据。
        
        Args:
            stock_code: 股票代码
            indicator_name: 指标名称（如 'roe', 'revenue', 'net_profit'）
            years: 需要的年数
            
        Returns:
            指标值列表，按年份从近到远排列。
            如果某年数据缺失，对应位置为 None。
            列表长度等于 years。
        """
        pass
    
    @abstractmethod
    def get_available_years(
        self,
        stock_code: 'StockCode'
    ) -> int:
        """
        获取可用的历史数据年数
        
        Args:
            stock_code: 股票代码
            
        Returns:
            可用的历史数据年数
        """
        pass
    
    @abstractmethod
    def get_financial_data_by_year(
        self,
        stock_code: 'StockCode',
        year: int
    ) -> Optional[Dict[str, Optional[float]]]:
        """
        获取指定年份的财务数据
        
        Args:
            stock_code: 股票代码
            year: 年份
            
        Returns:
            财务数据字典，包含各项指标。
            如果该年份无数据，返回 None。
        """
        pass
