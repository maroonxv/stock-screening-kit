"""
WatchListService 应用层服务实现

WatchListService 编排领域对象，管理自选股列表的生命周期。
负责协调 Repository 和聚合根之间的交互。

Requirements:
- 7.2: 实现 create_watchlist、add_stock、remove_stock、get_watchlist、list_watchlists 方法
"""
from typing import List, Optional, TYPE_CHECKING

from ...domain.exceptions import (
    DuplicateNameError,
    WatchListNotFoundError,
)
from ...domain.models.watchlist import WatchList
from ...domain.value_objects.identifiers import WatchListId

if TYPE_CHECKING:
    from ...domain.repositories.watchlist_repository import IWatchListRepository
    from shared_kernel.value_objects.stock_code import StockCode


class WatchListService:
    """
    自选股列表应用层服务
    
    编排领域对象，管理自选股列表的生命周期。
    
    职责:
    - 列表 CRUD 操作（create、get、list、delete）
    - 股票管理（add_stock、remove_stock）
    - 重复名称检查
    - 协调 Repository 和聚合根
    
    依赖:
    - watchlist_repo: 自选股列表仓储
    """
    
    def __init__(self, watchlist_repo: 'IWatchListRepository'):
        """
        构造自选股列表服务
        
        Args:
            watchlist_repo: 自选股列表仓储
        """
        self._watchlist_repo = watchlist_repo
    
    # ==================== 创建列表 ====================
    
    def create_watchlist(
        self,
        name: str,
        description: Optional[str] = None
    ) -> WatchList:
        """
        创建新的自选股列表
        
        Args:
            name: 列表名称（必须唯一）
            description: 列表描述（可选）
            
        Returns:
            创建的 WatchList 实例
            
        Raises:
            DuplicateNameError: 如果列表名称已存在
            ValueError: 如果名称为空
        """
        # 检查名称是否重复
        if self._watchlist_repo.find_by_name(name):
            raise DuplicateNameError(f"自选股列表 '{name}' 已存在")
        
        # 构造领域对象
        watchlist = WatchList(
            watchlist_id=WatchListId.generate(),
            name=name,
            description=description
        )
        
        # 持久化
        self._watchlist_repo.save(watchlist)
        
        return watchlist
    
    # ==================== 添加股票 ====================
    
    def add_stock(
        self,
        watchlist_id_str: str,
        stock_code_str: str,
        stock_name: str,
        note: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> WatchList:
        """
        向自选股列表添加股票
        
        Args:
            watchlist_id_str: 列表ID字符串
            stock_code_str: 股票代码字符串（如 "600000.SH"）
            stock_name: 股票名称
            note: 备注（可选）
            tags: 标签列表（可选）
            
        Returns:
            更新后的 WatchList 实例
            
        Raises:
            WatchListNotFoundError: 如果列表不存在
            DuplicateStockError: 如果股票已存在于列表中
            ValueError: 如果股票代码格式无效
        """
        # 导入 StockCode（延迟导入避免循环依赖）
        from shared_kernel.value_objects.stock_code import StockCode
        
        # 查找列表
        watchlist_id = WatchListId.from_string(watchlist_id_str)
        watchlist = self._watchlist_repo.find_by_id(watchlist_id)
        
        if not watchlist:
            raise WatchListNotFoundError(f"自选股列表 {watchlist_id_str} 不存在")
        
        # 构造股票代码值对象（会验证格式）
        stock_code = StockCode(stock_code_str)
        
        # 添加股票（领域对象会检查重复）
        watchlist.add_stock(stock_code, stock_name, note, tags)
        
        # 持久化
        self._watchlist_repo.save(watchlist)
        
        return watchlist
    
    # ==================== 移除股票 ====================
    
    def remove_stock(
        self,
        watchlist_id_str: str,
        stock_code_str: str
    ) -> WatchList:
        """
        从自选股列表移除股票
        
        Args:
            watchlist_id_str: 列表ID字符串
            stock_code_str: 股票代码字符串（如 "600000.SH"）
            
        Returns:
            更新后的 WatchList 实例
            
        Raises:
            WatchListNotFoundError: 如果列表不存在
            StockNotFoundError: 如果股票不在列表中
            ValueError: 如果股票代码格式无效
        """
        # 导入 StockCode（延迟导入避免循环依赖）
        from shared_kernel.value_objects.stock_code import StockCode
        
        # 查找列表
        watchlist_id = WatchListId.from_string(watchlist_id_str)
        watchlist = self._watchlist_repo.find_by_id(watchlist_id)
        
        if not watchlist:
            raise WatchListNotFoundError(f"自选股列表 {watchlist_id_str} 不存在")
        
        # 构造股票代码值对象（会验证格式）
        stock_code = StockCode(stock_code_str)
        
        # 移除股票（领域对象会检查是否存在）
        watchlist.remove_stock(stock_code)
        
        # 持久化
        self._watchlist_repo.save(watchlist)
        
        return watchlist
    
    # ==================== 获取列表 ====================
    
    def get_watchlist(self, watchlist_id_str: str) -> Optional[WatchList]:
        """
        根据ID获取自选股列表
        
        Args:
            watchlist_id_str: 列表ID字符串
            
        Returns:
            WatchList 实例，如果不存在返回 None
        """
        watchlist_id = WatchListId.from_string(watchlist_id_str)
        return self._watchlist_repo.find_by_id(watchlist_id)
    
    # ==================== 列出所有列表 ====================
    
    def list_watchlists(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[WatchList]:
        """
        分页列出所有自选股列表
        
        Args:
            limit: 返回的最大记录数（默认 100）
            offset: 跳过的记录数（默认 0）
            
        Returns:
            自选股列表，按更新时间降序排列
        """
        return self._watchlist_repo.find_all(limit=limit, offset=offset)
    
    # ==================== 删除列表 ====================
    
    def delete_watchlist(self, watchlist_id_str: str) -> None:
        """
        删除自选股列表
        
        Args:
            watchlist_id_str: 列表ID字符串
            
        Raises:
            WatchListNotFoundError: 如果列表不存在
        """
        watchlist_id = WatchListId.from_string(watchlist_id_str)
        
        # 检查列表是否存在
        if not self._watchlist_repo.exists(watchlist_id):
            raise WatchListNotFoundError(f"自选股列表 {watchlist_id_str} 不存在")
        
        # 删除列表
        self._watchlist_repo.delete(watchlist_id)
    
    # ==================== 更新列表 ====================
    
    def update_watchlist(
        self,
        watchlist_id_str: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> WatchList:
        """
        更新自选股列表
        
        只更新提供的字段，未提供的字段保持不变。
        
        Args:
            watchlist_id_str: 列表ID字符串
            name: 新的列表名称（可选）
            description: 新的列表描述（可选，传入空字符串可清除描述）
            
        Returns:
            更新后的 WatchList 实例
            
        Raises:
            WatchListNotFoundError: 如果列表不存在
            DuplicateNameError: 如果新名称与其他列表重复
            ValueError: 如果新名称为空
        """
        # 查找列表
        watchlist_id = WatchListId.from_string(watchlist_id_str)
        watchlist = self._watchlist_repo.find_by_id(watchlist_id)
        
        if not watchlist:
            raise WatchListNotFoundError(f"自选股列表 {watchlist_id_str} 不存在")
        
        # 更新名称（如果提供）
        if name is not None:
            # 检查新名称是否与其他列表重复
            existing = self._watchlist_repo.find_by_name(name)
            if existing and existing.watchlist_id != watchlist_id:
                raise DuplicateNameError(f"自选股列表 '{name}' 已存在")
            watchlist.update_name(name)
        
        # 更新描述（如果提供，包括清除描述的情况）
        if description is not None:
            watchlist.update_description(description if description else None)
        
        # 持久化
        self._watchlist_repo.save(watchlist)
        
        return watchlist
