"""IMarketDataRepository 抽象接口"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional
from datetime import datetime

from shared_kernel.value_objects.stock_code import StockCode


TStock = TypeVar('TStock')


class IMarketDataRepository(ABC, Generic[TStock]):
    """市场数据仓储抽象接口
    
    定义获取股票市场数据的标准接口，由基础设施层实现。
    使用泛型 TStock 以支持不同的股票实体类型。
    """
    
    @abstractmethod
    def get_all_stock_codes(self) -> List[StockCode]:
        """获取所有股票代码
        
        Returns:
            所有可用股票代码的列表
        """
        ...
    
    @abstractmethod
    def get_stock(self, stock_code: StockCode) -> Optional[TStock]:
        """根据股票代码获取单只股票
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票实体，如果不存在则返回 None
        """
        ...
    
    @abstractmethod
    def get_stocks_by_codes(self, stock_codes: List[StockCode]) -> List[TStock]:
        """批量获取股票
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            股票实体列表（仅包含存在的股票）
        """
        ...
    
    @abstractmethod
    def get_last_update_time(self) -> datetime:
        """获取数据最后更新时间
        
        Returns:
            最后更新时间
        """
        ...
    
    @abstractmethod
    def get_available_industries(self) -> List[str]:
        """获取所有可用的行业分类
        
        Returns:
            行业名称列表
        """
        ...
