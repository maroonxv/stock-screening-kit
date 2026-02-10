"""
自选股列表聚合根

WatchList 是管理用户关注股票的聚合根。
支持添加、移除和查询股票操作。

Requirements:
- 2.3: WatchList 聚合根包含属性：watchlist_id、name、description、stocks、created_at、updated_at
- 2.8: 对已存在的 stock_code 调用 add_stock() 时抛出 DuplicateStockError
- 2.9: 对不存在的 stock_code 调用 remove_stock() 时抛出 StockNotFoundError
"""
from datetime import datetime, timezone
from typing import List, Optional, Any

# 导入依赖
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared_kernel.value_objects.stock_code import StockCode
from contexts.screening.domain.value_objects.watched_stock import WatchedStock
from contexts.screening.domain.value_objects.identifiers import WatchListId
from contexts.screening.domain.exceptions import DuplicateStockError, StockNotFoundError


class WatchList:
    """
    自选股列表聚合根
    
    管理用户关注的股票列表，支持：
    - 添加股票（不允许重复）
    - 移除股票（必须存在）
    - 查询股票是否存在
    
    Attributes:
        watchlist_id: 列表唯一标识符
        name: 列表名称
        description: 列表描述（可选）
        stocks: 关注的股票列表
        created_at: 创建时间
        updated_at: 最后更新时间
    """
    
    def __init__(
        self,
        watchlist_id: WatchListId,
        name: str,
        description: Optional[str] = None,
        stocks: Optional[List[WatchedStock]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        构造自选股列表
        
        Args:
            watchlist_id: 列表唯一标识符
            name: 列表名称（不能为空）
            description: 列表描述
            stocks: 初始股票列表
            created_at: 创建时间（默认为当前时间）
            updated_at: 更新时间（默认为当前时间）
            
        Raises:
            ValueError: 如果名称为空
        """
        if not name or not name.strip():
            raise ValueError("自选股列表名称不能为空")
        
        self._watchlist_id = watchlist_id
        self._name = name
        self._description = description
        self._stocks = list(stocks) if stocks else []
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)
    
    @property
    def watchlist_id(self) -> WatchListId:
        """获取列表标识符"""
        return self._watchlist_id
    
    @property
    def name(self) -> str:
        """获取列表名称"""
        return self._name
    
    @property
    def description(self) -> Optional[str]:
        """获取列表描述"""
        return self._description
    
    @property
    def stocks(self) -> List[WatchedStock]:
        """获取股票列表（返回副本以保证不可变性）"""
        return list(self._stocks)
    
    @property
    def created_at(self) -> datetime:
        """获取创建时间"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """获取最后更新时间"""
        return self._updated_at
    
    def add_stock(
        self,
        stock_code: StockCode,
        stock_name: str,
        note: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """
        添加股票到列表
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            note: 备注（可选）
            tags: 标签列表（可选）
            
        Raises:
            DuplicateStockError: 如果股票已存在于列表中
        """
        if self.contains(stock_code):
            raise DuplicateStockError(f"股票 {stock_code.code} 已存在于列表中")
        
        watched = WatchedStock(
            stock_code=stock_code,
            stock_name=stock_name,
            added_at=datetime.now(timezone.utc),
            note=note,
            tags=tags
        )
        self._stocks.append(watched)
        self._updated_at = datetime.now(timezone.utc)
    
    def remove_stock(self, stock_code: StockCode) -> None:
        """
        从列表中移除股票
        
        Args:
            stock_code: 要移除的股票代码
            
        Raises:
            StockNotFoundError: 如果股票不在列表中
        """
        if not self.contains(stock_code):
            raise StockNotFoundError(f"股票 {stock_code.code} 不在列表中")
        
        self._stocks = [s for s in self._stocks if s.stock_code != stock_code]
        self._updated_at = datetime.now(timezone.utc)
    
    def contains(self, stock_code: StockCode) -> bool:
        """
        检查股票是否在列表中
        
        Args:
            stock_code: 要检查的股票代码
            
        Returns:
            如果股票在列表中返回 True，否则返回 False
        """
        return any(s.stock_code == stock_code for s in self._stocks)
    
    def get_stock(self, stock_code: StockCode) -> Optional[WatchedStock]:
        """
        获取指定股票的详细信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            如果找到返回 WatchedStock，否则返回 None
        """
        for stock in self._stocks:
            if stock.stock_code == stock_code:
                return stock
        return None
    
    def stock_count(self) -> int:
        """
        获取列表中的股票数量
        
        Returns:
            股票数量
        """
        return len(self._stocks)
    
    def update_name(self, name: str) -> None:
        """
        更新列表名称
        
        Args:
            name: 新名称
            
        Raises:
            ValueError: 如果名称为空
        """
        if not name or not name.strip():
            raise ValueError("自选股列表名称不能为空")
        self._name = name
        self._updated_at = datetime.now(timezone.utc)
    
    def update_description(self, description: Optional[str]) -> None:
        """
        更新列表描述
        
        Args:
            description: 新描述
        """
        self._description = description
        self._updated_at = datetime.now(timezone.utc)
    
    def __eq__(self, other: Any) -> bool:
        """判断两个 WatchList 是否相等（基于 ID）"""
        if not isinstance(other, WatchList):
            return False
        return self._watchlist_id == other._watchlist_id
    
    def __hash__(self) -> int:
        """计算哈希值"""
        return hash(self._watchlist_id)
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return (
            f"WatchList(watchlist_id={self._watchlist_id}, "
            f"name='{self._name}', "
            f"stock_count={len(self._stocks)})"
        )
