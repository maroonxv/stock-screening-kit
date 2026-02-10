"""
ScreeningStrategyService 应用层服务实现

ScreeningStrategyService 编排领域对象，管理筛选策略的生命周期和执行。
负责协调 Repository、领域服务和聚合根之间的交互。

Requirements:
- 7.1: 实现 create_strategy、update_strategy、delete_strategy、get_strategy、
       list_strategies、execute_strategy 方法
- 7.3: execute_strategy 加载候选股票 → 调用 execute() → 创建 ScreeningSession → 
       持久化会话 → 返回结果
- 7.4: 使用重复名称调用 create_strategy 时抛出适当的错误
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ...domain.exceptions import (
    DuplicateNameError,
    StrategyNotFoundError,
)
from ...domain.models.filter_group import FilterGroup
from ...domain.models.screening_session import ScreeningSession
from ...domain.models.screening_strategy import ScreeningStrategy
from ...domain.value_objects.identifiers import StrategyId
from ...domain.value_objects.scoring_config import ScoringConfig
from ...domain.value_objects.screening_result import ScreeningResult

if TYPE_CHECKING:
    from ...domain.repositories.screening_strategy_repository import IScreeningStrategyRepository
    from ...domain.repositories.screening_session_repository import IScreeningSessionRepository
    from shared_kernel.interfaces.market_data_repository import IMarketDataRepository
    from ...domain.services.scoring_service import IScoringService
    from ...domain.services.indicator_calculation_service import IIndicatorCalculationService


class ScreeningStrategyService:
    """
    筛选策略应用层服务
    
    编排领域对象，管理筛选策略的生命周期和执行。
    
    职责:
    - 策略 CRUD 操作（create、update、delete、get、list）
    - 策略执行（execute_strategy）
    - 重复名称检查
    - 协调 Repository 和领域服务
    
    依赖:
    - strategy_repo: 筛选策略仓储
    - session_repo: 筛选会话仓储
    - market_data_repo: 市场数据仓储
    - scoring_service: 评分服务
    - calc_service: 指标计算服务
    """
    
    def __init__(
        self,
        strategy_repo: 'IScreeningStrategyRepository',
        session_repo: 'IScreeningSessionRepository',
        market_data_repo: 'IMarketDataRepository',
        scoring_service: 'IScoringService',
        calc_service: 'IIndicatorCalculationService'
    ):
        """
        构造筛选策略服务
        
        Args:
            strategy_repo: 筛选策略仓储
            session_repo: 筛选会话仓储
            market_data_repo: 市场数据仓储
            scoring_service: 评分服务
            calc_service: 指标计算服务
        """
        self._strategy_repo = strategy_repo
        self._session_repo = session_repo
        self._market_data_repo = market_data_repo
        self._scoring_service = scoring_service
        self._calc_service = calc_service
    
    # ==================== 创建策略 ====================
    
    def create_strategy(
        self,
        name: str,
        filters_dict: Dict[str, Any],
        scoring_config_dict: Dict[str, Any],
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ScreeningStrategy:
        """
        创建新的筛选策略
        
        Args:
            name: 策略名称（必须唯一）
            filters_dict: 筛选条件组字典（用于 FilterGroup.from_dict）
            scoring_config_dict: 评分配置字典（用于 ScoringConfig.from_dict）
            description: 策略描述（可选）
            tags: 标签列表（可选）
            
        Returns:
            创建的 ScreeningStrategy 实例
            
        Raises:
            DuplicateNameError: 如果策略名称已存在
            ValueError: 如果名称为空或 filters 不包含任何条件
        """
        # 检查名称是否重复
        if self._strategy_repo.find_by_name(name):
            raise DuplicateNameError(f"策略名称 '{name}' 已存在")
        
        # 构造领域对象
        strategy = ScreeningStrategy(
            strategy_id=StrategyId.generate(),
            name=name,
            filters=FilterGroup.from_dict(filters_dict),
            scoring_config=ScoringConfig.from_dict(scoring_config_dict),
            description=description,
            tags=tags
        )
        
        # 持久化
        self._strategy_repo.save(strategy)
        
        return strategy
    
    # ==================== 更新策略 ====================
    
    def update_strategy(
        self,
        strategy_id_str: str,
        name: Optional[str] = None,
        filters_dict: Optional[Dict[str, Any]] = None,
        scoring_config_dict: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ScreeningStrategy:
        """
        更新筛选策略
        
        只更新提供的字段，未提供的字段保持不变。
        
        Args:
            strategy_id_str: 策略ID字符串
            name: 新的策略名称（可选）
            filters_dict: 新的筛选条件组字典（可选）
            scoring_config_dict: 新的评分配置字典（可选）
            description: 新的策略描述（可选，传入空字符串可清除描述）
            tags: 新的标签列表（可选）
            
        Returns:
            更新后的 ScreeningStrategy 实例
            
        Raises:
            StrategyNotFoundError: 如果策略不存在
            DuplicateNameError: 如果新名称与其他策略重复
            ValueError: 如果新名称为空或新 filters 不包含任何条件
        """
        # 查找策略
        strategy_id = StrategyId.from_string(strategy_id_str)
        strategy = self._strategy_repo.find_by_id(strategy_id)
        
        if not strategy:
            raise StrategyNotFoundError(f"策略 {strategy_id_str} 不存在")
        
        # 更新名称（如果提供）
        if name is not None:
            # 检查新名称是否与其他策略重复
            existing = self._strategy_repo.find_by_name(name)
            if existing and existing.strategy_id != strategy_id:
                raise DuplicateNameError(f"策略名称 '{name}' 已存在")
            strategy.update_name(name)
        
        # 更新筛选条件（如果提供）
        if filters_dict is not None:
            new_filters = FilterGroup.from_dict(filters_dict)
            strategy.update_filters(new_filters)
        
        # 更新评分配置（如果提供）
        if scoring_config_dict is not None:
            new_scoring_config = ScoringConfig.from_dict(scoring_config_dict)
            strategy.update_scoring_config(new_scoring_config)
        
        # 更新描述（如果提供，包括清除描述的情况）
        # 注意：这里使用特殊标记来区分"未提供"和"清除描述"
        # 调用者可以传入空字符串来清除描述
        if description is not None:
            strategy.update_description(description if description else None)
        
        # 更新标签（如果提供）
        if tags is not None:
            strategy.update_tags(tags)
        
        # 持久化
        self._strategy_repo.save(strategy)
        
        return strategy
    
    # ==================== 删除策略 ====================
    
    def delete_strategy(self, strategy_id_str: str) -> None:
        """
        删除筛选策略
        
        Args:
            strategy_id_str: 策略ID字符串
            
        Raises:
            StrategyNotFoundError: 如果策略不存在
        """
        strategy_id = StrategyId.from_string(strategy_id_str)
        
        # 检查策略是否存在
        if not self._strategy_repo.exists(strategy_id):
            raise StrategyNotFoundError(f"策略 {strategy_id_str} 不存在")
        
        # 删除策略
        self._strategy_repo.delete(strategy_id)
    
    # ==================== 获取策略 ====================
    
    def get_strategy(self, strategy_id_str: str) -> Optional[ScreeningStrategy]:
        """
        根据ID获取筛选策略
        
        Args:
            strategy_id_str: 策略ID字符串
            
        Returns:
            ScreeningStrategy 实例，如果不存在返回 None
        """
        strategy_id = StrategyId.from_string(strategy_id_str)
        return self._strategy_repo.find_by_id(strategy_id)
    
    # ==================== 列出策略 ====================
    
    def list_strategies(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[ScreeningStrategy]:
        """
        分页列出所有筛选策略
        
        Args:
            limit: 返回的最大记录数（默认 100）
            offset: 跳过的记录数（默认 0）
            
        Returns:
            筛选策略列表，按更新时间降序排列
        """
        return self._strategy_repo.find_all(limit=limit, offset=offset)
    
    # ==================== 执行策略 ====================
    
    def execute_strategy(self, strategy_id_str: str) -> ScreeningResult:
        """
        执行筛选策略
        
        执行流程：
        1. 加载策略
        2. 获取所有候选股票
        3. 调用策略的 execute() 方法执行筛选
        4. 创建 ScreeningSession 记录执行结果
        5. 持久化会话
        6. 返回筛选结果
        
        Args:
            strategy_id_str: 策略ID字符串
            
        Returns:
            ScreeningResult 筛选结果
            
        Raises:
            StrategyNotFoundError: 如果策略不存在
        """
        # 步骤 1: 加载策略
        strategy_id = StrategyId.from_string(strategy_id_str)
        strategy = self._strategy_repo.find_by_id(strategy_id)
        
        if not strategy:
            raise StrategyNotFoundError(f"策略 {strategy_id_str} 不存在")
        
        # 步骤 2: 获取所有候选股票
        stock_codes = self._market_data_repo.get_all_stock_codes()
        stocks = self._market_data_repo.get_stocks_by_codes(stock_codes)
        
        # 步骤 3: 执行筛选策略
        result = strategy.execute(
            candidate_stocks=stocks,
            scoring_service=self._scoring_service,
            calc_service=self._calc_service
        )
        
        # 步骤 4: 创建 ScreeningSession
        session = ScreeningSession.create_from_result(
            strategy_id=strategy.strategy_id,
            strategy_name=strategy.name,
            result=result
        )
        
        # 步骤 5: 持久化会话
        self._session_repo.save(session)
        
        # 步骤 6: 返回结果
        return result

