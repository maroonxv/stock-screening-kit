"""
ScreeningStrategy 聚合根实现

ScreeningStrategy 是筛选上下文的核心聚合根，定义筛选条件和评分配置。
负责执行筛选策略：过滤候选股票 → 评分 → 排序 → 返回结果。

Requirements:
- 2.1: ScreeningStrategy 聚合根包含所有属性（strategy_id、name、description、filters、
       scoring_config、tags、is_template、created_at、updated_at）
- 2.6: 空名称创建时抛出验证错误
- 2.7: 不包含任何条件的 filters 创建时抛出验证错误
- 5.6: execute() 返回按 score 降序排列的结果
"""
import time as time_module
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .filter_group import FilterGroup
from ..value_objects.identifiers import StrategyId
from ..value_objects.scoring_config import ScoringConfig
from ..value_objects.screening_result import ScreeningResult

if TYPE_CHECKING:
    from .stock import Stock


class ScreeningStrategy:
    """
    筛选策略聚合根
    
    定义筛选条件和评分配置，负责执行筛选策略。
    
    属性:
    - strategy_id: 策略唯一标识符（StrategyId）
    - name: 策略名称（非空）
    - description: 策略描述（可选）
    - filters: 筛选条件组（FilterGroup，必须包含至少一个条件）
    - scoring_config: 评分配置（ScoringConfig）
    - tags: 标签列表
    - is_template: 是否为模板
    - created_at: 创建时间
    - updated_at: 更新时间
    
    核心行为:
    - execute(): 执行筛选策略，过滤 → 评分 → 排序 → 返回 ScreeningResult
    """
    
    def __init__(
        self,
        strategy_id: StrategyId,
        name: str,
        filters: FilterGroup,
        scoring_config: ScoringConfig,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_template: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        构造筛选策略
        
        Args:
            strategy_id: 策略唯一标识符
            name: 策略名称（不能为空）
            filters: 筛选条件组（必须包含至少一个条件）
            scoring_config: 评分配置
            description: 策略描述（可选）
            tags: 标签列表（可选）
            is_template: 是否为模板（默认 False）
            created_at: 创建时间（默认当前时间）
            updated_at: 更新时间（默认当前时间）
            
        Raises:
            ValueError: 如果名称为空或 filters 不包含任何条件
        """
        # 验证名称非空
        if not name or not name.strip():
            raise ValueError("策略名称不能为空")
        
        # 验证 filters 包含至少一个条件
        if not filters.has_any_condition():
            raise ValueError("筛选条件不能为空")
        
        self._strategy_id = strategy_id
        self._name = name.strip()
        self._description = description
        self._filters = filters
        self._scoring_config = scoring_config
        self._tags = list(tags) if tags else []
        self._is_template = is_template
        self._created_at = created_at or datetime.now(timezone.utc)
        self._updated_at = updated_at or datetime.now(timezone.utc)
    
    # ==================== 属性访问器 ====================
    
    @property
    def strategy_id(self) -> StrategyId:
        """获取策略唯一标识符"""
        return self._strategy_id
    
    @property
    def name(self) -> str:
        """获取策略名称"""
        return self._name
    
    @property
    def description(self) -> Optional[str]:
        """获取策略描述"""
        return self._description
    
    @property
    def filters(self) -> FilterGroup:
        """获取筛选条件组"""
        return self._filters
    
    @property
    def scoring_config(self) -> ScoringConfig:
        """获取评分配置"""
        return self._scoring_config
    
    @property
    def tags(self) -> List[str]:
        """获取标签列表（返回副本以保证不可变性）"""
        return list(self._tags)
    
    @property
    def is_template(self) -> bool:
        """获取是否为模板"""
        return self._is_template
    
    @property
    def created_at(self) -> datetime:
        """获取创建时间"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """获取更新时间"""
        return self._updated_at
    
    # ==================== 核心业务方法 ====================
    
    def execute(
        self,
        candidate_stocks: List['Stock'],
        scoring_service: Any,
        calc_service: Any
    ) -> ScreeningResult:
        """
        执行筛选策略
        
        执行流程：
        1. 过滤：使用 filters 筛选匹配的股票
        2. 评分：使用 scoring_service 对匹配股票评分
        3. 排序：按 score 降序排列
        4. 返回：构造并返回 ScreeningResult
        
        Args:
            candidate_stocks: 候选股票列表
            scoring_service: 评分服务（IScoringService）
            calc_service: 指标计算服务（IIndicatorCalculationService）
            
        Returns:
            ScreeningResult 包含筛选结果
            
        Note:
            - 结果中的 matched_stocks 按 score 降序排列
            - execution_time 记录整个执行过程的耗时
        """
        start = time_module.time()
        
        # 步骤 1: 过滤 - 使用 filters 筛选匹配的股票
        matched = [
            stock for stock in candidate_stocks
            if self._filters.match(stock, calc_service)
        ]
        
        # 步骤 2: 评分 - 使用 scoring_service 对匹配股票评分
        scored = scoring_service.score_stocks(
            matched, self._scoring_config, calc_service
        )
        
        # 步骤 3: 排序 - 按 score 降序排列
        scored.sort(key=lambda s: s.score, reverse=True)
        
        # 计算执行时间
        execution_time = time_module.time() - start
        
        # 步骤 4: 返回 - 构造并返回 ScreeningResult
        return ScreeningResult(
            matched_stocks=scored,
            total_scanned=len(candidate_stocks),
            execution_time=execution_time,
            filters_applied=self._filters,
            scoring_config=self._scoring_config
        )
    
    # ==================== 修改方法 ====================
    
    def update_name(self, new_name: str) -> None:
        """
        更新策略名称
        
        Args:
            new_name: 新的策略名称
            
        Raises:
            ValueError: 如果新名称为空
        """
        if not new_name or not new_name.strip():
            raise ValueError("策略名称不能为空")
        self._name = new_name.strip()
        self._updated_at = datetime.now(timezone.utc)
    
    def update_description(self, new_description: Optional[str]) -> None:
        """
        更新策略描述
        
        Args:
            new_description: 新的策略描述
        """
        self._description = new_description
        self._updated_at = datetime.now(timezone.utc)
    
    def update_filters(self, new_filters: FilterGroup) -> None:
        """
        更新筛选条件组
        
        Args:
            new_filters: 新的筛选条件组
            
        Raises:
            ValueError: 如果新的 filters 不包含任何条件
        """
        if not new_filters.has_any_condition():
            raise ValueError("筛选条件不能为空")
        self._filters = new_filters
        self._updated_at = datetime.now(timezone.utc)
    
    def update_scoring_config(self, new_scoring_config: ScoringConfig) -> None:
        """
        更新评分配置
        
        Args:
            new_scoring_config: 新的评分配置
        """
        self._scoring_config = new_scoring_config
        self._updated_at = datetime.now(timezone.utc)
    
    def update_tags(self, new_tags: List[str]) -> None:
        """
        更新标签列表
        
        Args:
            new_tags: 新的标签列表
        """
        self._tags = list(new_tags) if new_tags else []
        self._updated_at = datetime.now(timezone.utc)
    
    def set_as_template(self, is_template: bool) -> None:
        """
        设置是否为模板
        
        Args:
            is_template: 是否为模板
        """
        self._is_template = is_template
        self._updated_at = datetime.now(timezone.utc)
    
    # ==================== 序列化方法 ====================
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            'strategy_id': self._strategy_id.value,
            'name': self._name,
            'description': self._description,
            'filters': self._filters.to_dict(),
            'scoring_config': self._scoring_config.to_dict(),
            'tags': self._tags,
            'is_template': self._is_template,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScreeningStrategy':
        """
        从字典反序列化
        
        Args:
            data: 包含所有属性的字典
            
        Returns:
            ScreeningStrategy 实例
        """
        strategy_id = StrategyId.from_string(data['strategy_id'])
        filters = FilterGroup.from_dict(data['filters'])
        scoring_config = ScoringConfig.from_dict(data['scoring_config'])
        
        created_at_str = data.get('created_at')
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else None
        
        updated_at_str = data.get('updated_at')
        updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None
        
        return cls(
            strategy_id=strategy_id,
            name=data['name'],
            filters=filters,
            scoring_config=scoring_config,
            description=data.get('description'),
            tags=data.get('tags'),
            is_template=data.get('is_template', False),
            created_at=created_at,
            updated_at=updated_at
        )
    
    # ==================== 特殊方法 ====================
    
    def __eq__(self, other: object) -> bool:
        """
        判断两个 ScreeningStrategy 是否相等
        
        基于 strategy_id 判断相等性（聚合根标识）
        """
        if not isinstance(other, ScreeningStrategy):
            return False
        return self._strategy_id == other._strategy_id
    
    def __hash__(self) -> int:
        """
        计算哈希值
        
        基于 strategy_id 计算哈希值
        """
        return hash(self._strategy_id)
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return (
            f"ScreeningStrategy(strategy_id={self._strategy_id!r}, "
            f"name='{self._name}', "
            f"is_template={self._is_template})"
        )
