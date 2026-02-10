"""
策略相关 DTO 类

包含筛选策略的请求和响应 DTO：
- CreateStrategyRequest: 创建策略请求
- UpdateStrategyRequest: 更新策略请求
- StrategyResponse: 策略响应
- ScreeningResultResponse: 筛选结果响应

Requirements:
- 8.10: 实现 DTO 类用于请求验证和响应格式化
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.models.screening_strategy import ScreeningStrategy
    from ...domain.value_objects.screening_result import ScreeningResult


@dataclass
class CreateStrategyRequest:
    """
    创建策略请求 DTO
    
    用于解析和验证创建策略的 API 请求数据。
    
    Attributes:
        name: 策略名称（必填）
        filters: 筛选条件组配置（必填）
        scoring_config: 评分配置（必填）
        description: 策略描述（可选）
        tags: 标签列表（可选）
    """
    name: str
    filters: Dict[str, Any]
    scoring_config: Dict[str, Any]
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CreateStrategyRequest':
        """
        从字典解析请求数据
        
        Args:
            data: 请求 JSON 数据
            
        Returns:
            CreateStrategyRequest 实例
            
        Raises:
            ValueError: 如果必填字段缺失或数据无效
        """
        # 验证必填字段
        if not data:
            raise ValueError("请求数据不能为空")
        
        if 'name' not in data:
            raise ValueError("缺少必填字段: name")
        if not data['name'] or not str(data['name']).strip():
            raise ValueError("策略名称不能为空")
        
        if 'filters' not in data:
            raise ValueError("缺少必填字段: filters")
        if not isinstance(data['filters'], dict):
            raise ValueError("filters 必须是对象类型")
        
        if 'scoring_config' not in data:
            raise ValueError("缺少必填字段: scoring_config")
        if not isinstance(data['scoring_config'], dict):
            raise ValueError("scoring_config 必须是对象类型")
        
        # 验证 tags 类型
        tags = data.get('tags')
        if tags is not None and not isinstance(tags, list):
            raise ValueError("tags 必须是数组类型")
        
        return cls(
            name=str(data['name']).strip(),
            filters=data['filters'],
            scoring_config=data['scoring_config'],
            description=data.get('description'),
            tags=tags
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        result = {
            'name': self.name,
            'filters': self.filters,
            'scoring_config': self.scoring_config
        }
        if self.description is not None:
            result['description'] = self.description
        if self.tags is not None:
            result['tags'] = self.tags
        return result


@dataclass
class UpdateStrategyRequest:
    """
    更新策略请求 DTO
    
    用于解析和验证更新策略的 API 请求数据。
    所有字段都是可选的，只更新提供的字段。
    
    Attributes:
        name: 策略名称（可选）
        filters: 筛选条件组配置（可选）
        scoring_config: 评分配置（可选）
        description: 策略描述（可选）
        tags: 标签列表（可选）
    """
    name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    scoring_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateStrategyRequest':
        """
        从字典解析请求数据
        
        Args:
            data: 请求 JSON 数据
            
        Returns:
            UpdateStrategyRequest 实例
            
        Raises:
            ValueError: 如果数据无效
        """
        if data is None:
            raise ValueError("请求数据不能为空")
        
        # 验证 name（如果提供）
        name = data.get('name')
        if name is not None:
            if not str(name).strip():
                raise ValueError("策略名称不能为空")
            name = str(name).strip()
        
        # 验证 filters（如果提供）
        filters = data.get('filters')
        if filters is not None and not isinstance(filters, dict):
            raise ValueError("filters 必须是对象类型")
        
        # 验证 scoring_config（如果提供）
        scoring_config = data.get('scoring_config')
        if scoring_config is not None and not isinstance(scoring_config, dict):
            raise ValueError("scoring_config 必须是对象类型")
        
        # 验证 tags（如果提供）
        tags = data.get('tags')
        if tags is not None and not isinstance(tags, list):
            raise ValueError("tags 必须是数组类型")
        
        return cls(
            name=name,
            filters=filters,
            scoring_config=scoring_config,
            description=data.get('description'),
            tags=tags
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
        if self.filters is not None:
            result['filters'] = self.filters
        if self.scoring_config is not None:
            result['scoring_config'] = self.scoring_config
        if self.description is not None:
            result['description'] = self.description
        if self.tags is not None:
            result['tags'] = self.tags
        return result
    
    def has_updates(self) -> bool:
        """
        检查是否有任何更新字段
        
        Returns:
            如果有任何非 None 字段返回 True
        """
        return any([
            self.name is not None,
            self.filters is not None,
            self.scoring_config is not None,
            self.description is not None,
            self.tags is not None
        ])


@dataclass
class StrategyResponse:
    """
    策略响应 DTO
    
    用于将 ScreeningStrategy 领域对象转换为 API 响应格式。
    
    Attributes:
        strategy_id: 策略唯一标识符
        name: 策略名称
        description: 策略描述
        filters: 筛选条件组配置
        scoring_config: 评分配置
        tags: 标签列表
        is_template: 是否为模板
        created_at: 创建时间
        updated_at: 更新时间
    """
    strategy_id: str
    name: str
    description: Optional[str]
    filters: Dict[str, Any]
    scoring_config: Dict[str, Any]
    tags: List[str]
    is_template: bool
    created_at: str
    updated_at: str
    
    @classmethod
    def from_domain(cls, strategy: 'ScreeningStrategy') -> 'StrategyResponse':
        """
        从领域对象创建响应 DTO
        
        Args:
            strategy: ScreeningStrategy 领域对象
            
        Returns:
            StrategyResponse 实例
        """
        return cls(
            strategy_id=strategy.strategy_id.value,
            name=strategy.name,
            description=strategy.description,
            filters=strategy.filters.to_dict(),
            scoring_config=strategy.scoring_config.to_dict(),
            tags=strategy.tags,
            is_template=strategy.is_template,
            created_at=strategy.created_at.isoformat(),
            updated_at=strategy.updated_at.isoformat()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'description': self.description,
            'filters': self.filters,
            'scoring_config': self.scoring_config,
            'tags': self.tags,
            'is_template': self.is_template,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class ScoredStockResponse:
    """
    带评分股票响应 DTO
    
    用于将 ScoredStock 值对象转换为 API 响应格式。
    """
    stock_code: str
    stock_name: str
    score: float
    score_breakdown: Dict[str, float]
    indicator_values: Dict[str, Any]
    matched_conditions: List[Dict[str, Any]]
    
    @classmethod
    def from_domain(cls, scored_stock: Any) -> 'ScoredStockResponse':
        """
        从领域对象创建响应 DTO
        
        Args:
            scored_stock: ScoredStock 值对象
            
        Returns:
            ScoredStockResponse 实例
        """
        return cls(
            stock_code=scored_stock.stock_code.code,
            stock_name=scored_stock.stock_name,
            score=scored_stock.score,
            score_breakdown={
                field.name: value 
                for field, value in scored_stock.score_breakdown.items()
            },
            indicator_values={
                field.name: value 
                for field, value in scored_stock.indicator_values.items()
            },
            matched_conditions=[
                cond.to_dict() for cond in scored_stock.matched_conditions
            ]
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
            'score': self.score,
            'score_breakdown': self.score_breakdown,
            'indicator_values': self.indicator_values,
            'matched_conditions': self.matched_conditions
        }


@dataclass
class ScreeningResultResponse:
    """
    筛选结果响应 DTO
    
    用于将 ScreeningResult 值对象转换为 API 响应格式。
    
    Attributes:
        matched_stocks: 匹配的股票列表
        total_scanned: 扫描的股票总数
        matched_count: 匹配的股票数量
        match_rate: 匹配率
        execution_time: 执行时间（秒）
        filters_applied: 应用的筛选条件
        scoring_config: 评分配置
        timestamp: 执行时间戳
    """
    matched_stocks: List[ScoredStockResponse]
    total_scanned: int
    matched_count: int
    match_rate: float
    execution_time: float
    filters_applied: Dict[str, Any]
    scoring_config: Dict[str, Any]
    timestamp: str
    
    @classmethod
    def from_domain(cls, result: 'ScreeningResult') -> 'ScreeningResultResponse':
        """
        从领域对象创建响应 DTO
        
        Args:
            result: ScreeningResult 值对象
            
        Returns:
            ScreeningResultResponse 实例
        """
        matched_stocks = [
            ScoredStockResponse.from_domain(stock)
            for stock in result.matched_stocks
        ]
        
        return cls(
            matched_stocks=matched_stocks,
            total_scanned=result.total_scanned,
            matched_count=result.matched_count,
            match_rate=result.match_rate,
            execution_time=result.execution_time,
            filters_applied=result.filters_applied.to_dict(),
            scoring_config=result.scoring_config.to_dict(),
            timestamp=result.timestamp.isoformat()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'matched_stocks': [stock.to_dict() for stock in self.matched_stocks],
            'total_scanned': self.total_scanned,
            'matched_count': self.matched_count,
            'match_rate': self.match_rate,
            'execution_time': self.execution_time,
            'filters_applied': self.filters_applied,
            'scoring_config': self.scoring_config,
            'timestamp': self.timestamp
        }
