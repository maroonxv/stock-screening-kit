"""
自选股列表相关 DTO 类

包含自选股列表的请求和响应 DTO：
- CreateWatchlistRequest: 创建自选股列表请求
- AddStockRequest: 添加股票请求
- WatchlistResponse: 自选股列表响应

Requirements:
- 8.10: 实现 DTO 类用于请求验证和响应格式化
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.models.watchlist import WatchList


@dataclass
class CreateWatchlistRequest:
    """
    创建自选股列表请求 DTO
    
    用于解析和验证创建自选股列表的 API 请求数据。
    
    Attributes:
        name: 列表名称（必填）
        description: 列表描述（可选）
    """
    name: str
    description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CreateWatchlistRequest':
        """
        从字典解析请求数据
        
        Args:
            data: 请求 JSON 数据
            
        Returns:
            CreateWatchlistRequest 实例
            
        Raises:
            ValueError: 如果必填字段缺失或数据无效
        """
        # 验证必填字段
        if not data:
            raise ValueError("请求数据不能为空")
        
        if 'name' not in data:
            raise ValueError("缺少必填字段: name")
        if not data['name'] or not str(data['name']).strip():
            raise ValueError("自选股列表名称不能为空")
        
        return cls(
            name=str(data['name']).strip(),
            description=data.get('description')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        result = {'name': self.name}
        if self.description is not None:
            result['description'] = self.description
        return result


@dataclass
class UpdateWatchlistRequest:
    """
    更新自选股列表请求 DTO
    
    用于解析和验证更新自选股列表的 API 请求数据。
    所有字段都是可选的，只更新提供的字段。
    
    Attributes:
        name: 列表名称（可选）
        description: 列表描述（可选）
    """
    name: Optional[str] = None
    description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateWatchlistRequest':
        """
        从字典解析请求数据
        
        Args:
            data: 请求 JSON 数据
            
        Returns:
            UpdateWatchlistRequest 实例
            
        Raises:
            ValueError: 如果数据无效
        """
        if not data:
            raise ValueError("请求数据不能为空")
        
        # 验证 name（如果提供）
        name = data.get('name')
        if name is not None:
            if not str(name).strip():
                raise ValueError("自选股列表名称不能为空")
            name = str(name).strip()
        
        return cls(
            name=name,
            description=data.get('description')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典（只包含非 None 的字段）
        
        Returns:
            包含非 None 属性的字典
        """
        result = {}
        if self.name is not None:
            result['name'] = self.name
        if self.description is not None:
            result['description'] = self.description
        return result
    
    def has_updates(self) -> bool:
        """
        检查是否有任何更新字段
        
        Returns:
            如果有任何非 None 字段返回 True
        """
        return self.name is not None or self.description is not None


@dataclass
class AddStockRequest:
    """
    添加股票请求 DTO
    
    用于解析和验证添加股票到自选股列表的 API 请求数据。
    
    Attributes:
        stock_code: 股票代码（必填）
        stock_name: 股票名称（必填）
        note: 备注（可选）
        tags: 标签列表（可选）
    """
    stock_code: str
    stock_name: str
    note: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AddStockRequest':
        """
        从字典解析请求数据
        
        Args:
            data: 请求 JSON 数据
            
        Returns:
            AddStockRequest 实例
            
        Raises:
            ValueError: 如果必填字段缺失或数据无效
        """
        # 验证必填字段
        if not data:
            raise ValueError("请求数据不能为空")
        
        if 'stock_code' not in data:
            raise ValueError("缺少必填字段: stock_code")
        if not data['stock_code'] or not str(data['stock_code']).strip():
            raise ValueError("股票代码不能为空")
        
        if 'stock_name' not in data:
            raise ValueError("缺少必填字段: stock_name")
        if not data['stock_name'] or not str(data['stock_name']).strip():
            raise ValueError("股票名称不能为空")
        
        # 验证 tags 类型
        tags = data.get('tags')
        if tags is not None and not isinstance(tags, list):
            raise ValueError("tags 必须是数组类型")
        
        return cls(
            stock_code=str(data['stock_code']).strip(),
            stock_name=str(data['stock_name']).strip(),
            note=data.get('note'),
            tags=tags
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        result = {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name
        }
        if self.note is not None:
            result['note'] = self.note
        if self.tags is not None:
            result['tags'] = self.tags
        return result


@dataclass
class WatchedStockResponse:
    """
    自选股响应 DTO
    
    用于将 WatchedStock 值对象转换为 API 响应格式。
    """
    stock_code: str
    stock_name: str
    added_at: str
    note: Optional[str]
    tags: Optional[List[str]]
    
    @classmethod
    def from_domain(cls, watched_stock: Any) -> 'WatchedStockResponse':
        """
        从领域对象创建响应 DTO
        
        Args:
            watched_stock: WatchedStock 值对象
            
        Returns:
            WatchedStockResponse 实例
        """
        return cls(
            stock_code=watched_stock.stock_code.code,
            stock_name=watched_stock.stock_name,
            added_at=watched_stock.added_at.isoformat(),
            note=watched_stock.note,
            tags=watched_stock.tags
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'added_at': self.added_at,
            'note': self.note,
            'tags': self.tags
        }


@dataclass
class WatchlistResponse:
    """
    自选股列表响应 DTO
    
    用于将 WatchList 领域对象转换为 API 响应格式。
    
    Attributes:
        watchlist_id: 列表唯一标识符
        name: 列表名称
        description: 列表描述
        stocks: 股票列表
        stock_count: 股票数量
        created_at: 创建时间
        updated_at: 更新时间
    """
    watchlist_id: str
    name: str
    description: Optional[str]
    stocks: List[WatchedStockResponse]
    stock_count: int
    created_at: str
    updated_at: str
    
    @classmethod
    def from_domain(cls, watchlist: 'WatchList') -> 'WatchlistResponse':
        """
        从领域对象创建响应 DTO
        
        Args:
            watchlist: WatchList 领域对象
            
        Returns:
            WatchlistResponse 实例
        """
        stocks = [
            WatchedStockResponse.from_domain(stock)
            for stock in watchlist.stocks
        ]
        
        return cls(
            watchlist_id=watchlist.watchlist_id.value,
            name=watchlist.name,
            description=watchlist.description,
            stocks=stocks,
            stock_count=watchlist.stock_count(),
            created_at=watchlist.created_at.isoformat(),
            updated_at=watchlist.updated_at.isoformat()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'watchlist_id': self.watchlist_id,
            'name': self.name,
            'description': self.description,
            'stocks': [stock.to_dict() for stock in self.stocks],
            'stock_count': self.stock_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class WatchlistSummaryResponse:
    """
    自选股列表摘要响应 DTO
    
    用于列表展示时的简化自选股列表信息。
    
    Attributes:
        watchlist_id: 列表唯一标识符
        name: 列表名称
        description: 列表描述
        stock_count: 股票数量
        created_at: 创建时间
        updated_at: 更新时间
    """
    watchlist_id: str
    name: str
    description: Optional[str]
    stock_count: int
    created_at: str
    updated_at: str
    
    @classmethod
    def from_domain(cls, watchlist: 'WatchList') -> 'WatchlistSummaryResponse':
        """
        从领域对象创建响应 DTO
        
        Args:
            watchlist: WatchList 领域对象
            
        Returns:
            WatchlistSummaryResponse 实例
        """
        return cls(
            watchlist_id=watchlist.watchlist_id.value,
            name=watchlist.name,
            description=watchlist.description,
            stock_count=watchlist.stock_count(),
            created_at=watchlist.created_at.isoformat(),
            updated_at=watchlist.updated_at.isoformat()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'watchlist_id': self.watchlist_id,
            'name': self.name,
            'description': self.description,
            'stock_count': self.stock_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
