"""
WatchListRepository 实现

实现 IWatchListRepository 接口，负责 WatchList 聚合根的持久化。
处理 PO ↔ 领域对象映射，包含 stocks 列表的 JSONB 序列化/反序列化。

Requirements:
- 6.4: 实现 WatchListRepository，在 WatchList 领域对象和 PO 模型之间进行映射
"""
from typing import List, Optional

from ..models.watchlist_po import WatchListPO
from ....domain.repositories.watchlist_repository import IWatchListRepository
from ....domain.models.watchlist import WatchList
from ....domain.value_objects.watched_stock import WatchedStock
from ....domain.value_objects.identifiers import WatchListId


class WatchListRepositoryImpl(IWatchListRepository):
    """
    自选股列表仓储实现
    
    使用 SQLAlchemy session 进行数据库操作。
    负责 WatchList 领域对象与 WatchListPO 持久化对象之间的映射。
    
    映射说明:
    - watchlist_id (WatchListId) <-> id (String)
    - stocks (List[WatchedStock]) <-> stocks (JSONB) - 使用 to_dict/from_dict 序列化
    """
    
    def __init__(self, session):
        """
        初始化仓储
        
        Args:
            session: SQLAlchemy 数据库会话
        """
        self._session = session
    
    def save(self, watchlist: WatchList) -> None:
        """
        保存自选股列表
        
        如果列表已存在（相同 ID），则更新；否则创建新记录。
        使用 merge 实现 upsert 语义。
        
        Args:
            watchlist: 要保存的自选股列表
        """
        po = self._to_po(watchlist)
        self._session.merge(po)
        self._session.flush()
    
    def find_by_id(self, watchlist_id: WatchListId) -> Optional[WatchList]:
        """
        根据 ID 查找自选股列表
        
        Args:
            watchlist_id: 列表唯一标识符
            
        Returns:
            如果找到返回 WatchList，否则返回 None
        """
        po = self._session.query(WatchListPO).get(watchlist_id.value)
        return self._to_domain(po) if po else None
    
    def find_by_name(self, name: str) -> Optional[WatchList]:
        """
        根据名称查找自选股列表
        
        Args:
            name: 列表名称
            
        Returns:
            如果找到返回 WatchList，否则返回 None
        """
        po = self._session.query(WatchListPO).filter_by(name=name).first()
        return self._to_domain(po) if po else None
    
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[WatchList]:
        """
        分页查询所有自选股列表
        
        Args:
            limit: 返回的最大记录数（默认 100）
            offset: 跳过的记录数（默认 0）
            
        Returns:
            自选股列表，按更新时间降序排列
        """
        pos = (
            self._session.query(WatchListPO)
            .order_by(WatchListPO.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_domain(po) for po in pos]
    
    def delete(self, watchlist_id: WatchListId) -> None:
        """
        删除自选股列表
        
        Args:
            watchlist_id: 要删除的列表 ID
            
        Note:
            如果列表不存在，静默处理（不抛出异常）
        """
        po = self._session.query(WatchListPO).get(watchlist_id.value)
        if po:
            self._session.delete(po)
            self._session.flush()
    
    def exists(self, watchlist_id: WatchListId) -> bool:
        """
        检查列表是否存在
        
        Args:
            watchlist_id: 列表唯一标识符
            
        Returns:
            如果存在返回 True，否则返回 False
        """
        count = (
            self._session.query(WatchListPO)
            .filter(WatchListPO.id == watchlist_id.value)
            .count()
        )
        return count > 0
    
    def count(self) -> int:
        """
        获取列表总数
        
        Returns:
            列表总数
        """
        return self._session.query(WatchListPO).count()
    
    # ==================== 私有映射方法 ====================
    
    def _to_po(self, watchlist: WatchList) -> WatchListPO:
        """
        将领域对象转换为持久化对象
        
        Args:
            watchlist: WatchList 领域对象
            
        Returns:
            WatchListPO 持久化对象
            
        Note:
            - stocks 使用 to_dict() 序列化为 JSONB
        """
        return WatchListPO(
            id=watchlist.watchlist_id.value,
            name=watchlist.name,
            description=watchlist.description,
            stocks=[stock.to_dict() for stock in watchlist.stocks],
            created_at=watchlist.created_at,
            updated_at=watchlist.updated_at
        )
    
    def _to_domain(self, po: WatchListPO) -> WatchList:
        """
        将持久化对象转换为领域对象
        
        Args:
            po: WatchListPO 持久化对象
            
        Returns:
            WatchList 领域对象
            
        Note:
            - stocks JSONB 使用 WatchedStock.from_dict() 反序列化
        """
        stocks = [
            WatchedStock.from_dict(stock_data)
            for stock_data in (po.stocks or [])
        ]
        
        return WatchList(
            watchlist_id=WatchListId.from_string(po.id),
            name=po.name,
            description=po.description,
            stocks=stocks,
            created_at=po.created_at,
            updated_at=po.updated_at
        )
