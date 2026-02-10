"""
ScreeningStrategyRepository 实现

实现 IScreeningStrategyRepository 接口，负责 ScreeningStrategy 聚合根的持久化。
处理 PO ↔ 领域对象映射，包含 FilterGroup 和 ScoringConfig 的 JSONB 序列化/反序列化。

Requirements:
- 6.2: 实现 ScreeningStrategyRepository，在 ScreeningStrategy 领域对象和 PO 模型之间进行映射
- 6.7: 保存 ScreeningStrategy 后按 ID 检索时，返回等价的领域对象，包含所有嵌套的 FilterGroup
"""
from typing import List, Optional

from ..models.screening_strategy_po import ScreeningStrategyPO
from ....domain.repositories.screening_strategy_repository import IScreeningStrategyRepository
from ....domain.models.screening_strategy import ScreeningStrategy
from ....domain.models.filter_group import FilterGroup
from ....domain.value_objects.scoring_config import ScoringConfig
from ....domain.value_objects.identifiers import StrategyId


class ScreeningStrategyRepositoryImpl(IScreeningStrategyRepository):
    """
    筛选策略仓储实现
    
    使用 SQLAlchemy session 进行数据库操作。
    负责 ScreeningStrategy 领域对象与 ScreeningStrategyPO 持久化对象之间的映射。
    
    映射说明:
    - strategy_id (StrategyId) <-> id (String)
    - filters (FilterGroup) <-> filters (JSONB) - 使用 to_dict/from_dict 序列化
    - scoring_config (ScoringConfig) <-> scoring_config (JSONB) - 使用 to_dict/from_dict 序列化
    - tags (List[str]) <-> tags (JSONB)
    """
    
    def __init__(self, session):
        """
        初始化仓储
        
        Args:
            session: SQLAlchemy 数据库会话
        """
        self._session = session
    
    def save(self, strategy: ScreeningStrategy) -> None:
        """
        保存筛选策略
        
        如果策略已存在（相同 ID），则更新；否则创建新记录。
        使用 merge 实现 upsert 语义。
        
        Args:
            strategy: 要保存的筛选策略
        """
        po = self._to_po(strategy)
        self._session.merge(po)
        self._session.flush()
    
    def find_by_id(self, strategy_id: StrategyId) -> Optional[ScreeningStrategy]:
        """
        根据 ID 查找筛选策略
        
        Args:
            strategy_id: 策略唯一标识符
            
        Returns:
            如果找到返回 ScreeningStrategy，否则返回 None
        """
        po = self._session.query(ScreeningStrategyPO).get(strategy_id.value)
        return self._to_domain(po) if po else None
    
    def find_by_name(self, name: str) -> Optional[ScreeningStrategy]:
        """
        根据名称查找筛选策略
        
        Args:
            name: 策略名称
            
        Returns:
            如果找到返回 ScreeningStrategy，否则返回 None
        """
        po = self._session.query(ScreeningStrategyPO).filter_by(name=name).first()
        return self._to_domain(po) if po else None
    
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[ScreeningStrategy]:
        """
        分页查询所有筛选策略
        
        Args:
            limit: 返回的最大记录数（默认 100）
            offset: 跳过的记录数（默认 0）
            
        Returns:
            筛选策略列表，按更新时间降序排列
        """
        pos = (
            self._session.query(ScreeningStrategyPO)
            .order_by(ScreeningStrategyPO.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_domain(po) for po in pos]
    
    def delete(self, strategy_id: StrategyId) -> None:
        """
        删除筛选策略
        
        Args:
            strategy_id: 要删除的策略 ID
            
        Note:
            如果策略不存在，静默处理（不抛出异常）
        """
        po = self._session.query(ScreeningStrategyPO).get(strategy_id.value)
        if po:
            self._session.delete(po)
            self._session.flush()
    
    def exists(self, strategy_id: StrategyId) -> bool:
        """
        检查策略是否存在
        
        Args:
            strategy_id: 策略唯一标识符
            
        Returns:
            如果存在返回 True，否则返回 False
        """
        count = (
            self._session.query(ScreeningStrategyPO)
            .filter(ScreeningStrategyPO.id == strategy_id.value)
            .count()
        )
        return count > 0
    
    def count(self) -> int:
        """
        获取策略总数
        
        Returns:
            策略总数
        """
        return self._session.query(ScreeningStrategyPO).count()
    
    # ==================== 私有映射方法 ====================
    
    def _to_po(self, strategy: ScreeningStrategy) -> ScreeningStrategyPO:
        """
        将领域对象转换为持久化对象
        
        Args:
            strategy: ScreeningStrategy 领域对象
            
        Returns:
            ScreeningStrategyPO 持久化对象
            
        Note:
            - FilterGroup 使用 to_dict() 序列化为 JSONB
            - ScoringConfig 使用 to_dict() 序列化为 JSONB
            - tags 直接存储为 JSONB 数组
        """
        return ScreeningStrategyPO(
            id=strategy.strategy_id.value,
            name=strategy.name,
            description=strategy.description,
            filters=strategy.filters.to_dict(),
            scoring_config=strategy.scoring_config.to_dict(),
            tags=strategy.tags,
            is_template=strategy.is_template,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )
    
    def _to_domain(self, po: ScreeningStrategyPO) -> ScreeningStrategy:
        """
        将持久化对象转换为领域对象
        
        Args:
            po: ScreeningStrategyPO 持久化对象
            
        Returns:
            ScreeningStrategy 领域对象
            
        Note:
            - filters JSONB 使用 FilterGroup.from_dict() 反序列化
            - scoring_config JSONB 使用 ScoringConfig.from_dict() 反序列化
            - tags 从 JSONB 数组直接读取，如果为 None 则使用空列表
        """
        return ScreeningStrategy(
            strategy_id=StrategyId.from_string(po.id),
            name=po.name,
            description=po.description,
            filters=FilterGroup.from_dict(po.filters),
            scoring_config=ScoringConfig.from_dict(po.scoring_config),
            tags=po.tags or [],
            is_template=po.is_template,
            created_at=po.created_at,
            updated_at=po.updated_at
        )
