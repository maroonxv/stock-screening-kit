"""
筛选条件组实体实现

FilterGroup 是一个实体，支持 AND/OR/NOT 逻辑运算符的递归嵌套结构。
用于构建复杂的筛选条件组合。

Requirements:
- 2.4: FilterGroup 实体，支持 AND/OR/NOT 逻辑运算符的递归结构
- 5.3: AND 运算符 - 所有条件和子组都匹配时返回 True
- 5.4: OR 运算符 - 至少一个条件或子组匹配时返回 True
- 5.5: NOT 运算符 - 对单个子元素的结果取反
- 3.12: 支持 to_dict() 和 from_dict() 序列化
"""
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..enums.enums import LogicalOperator
from ..value_objects.filter_condition import FilterCondition

if TYPE_CHECKING:
    pass


class FilterGroup:
    """
    筛选条件组实体
    
    支持 AND/OR/NOT 逻辑运算符的递归嵌套结构。
    
    属性:
    - group_id: 组唯一标识符
    - operator: 逻辑运算符（AND/OR/NOT）
    - conditions: 直接包含的筛选条件列表
    - sub_groups: 嵌套的子条件组列表
    
    逻辑语义:
    - AND: 所有条件和子组都匹配时返回 True
    - OR: 至少一个条件或子组匹配时返回 True
    - NOT: 对第一个子元素（条件或子组）的结果取反
    
    空组行为:
    - AND 空组返回 True（空集的全称量化为真）
    - OR 空组返回 False（空集的存在量化为假）
    - NOT 空组返回 True（无元素可取反，默认为真）
    """
    
    def __init__(self, group_id: str, operator: LogicalOperator,
                 conditions: Optional[List[FilterCondition]] = None,
                 sub_groups: Optional[List['FilterGroup']] = None):
        """
        构造筛选条件组
        
        Args:
            group_id: 组唯一标识符
            operator: 逻辑运算符（AND/OR/NOT）
            conditions: 直接包含的筛选条件列表
            sub_groups: 嵌套的子条件组列表
        """
        self._group_id = group_id
        self._operator = operator
        self._conditions = conditions or []
        self._sub_groups = sub_groups or []
    
    @property
    def group_id(self) -> str:
        """获取组唯一标识符"""
        return self._group_id
    
    @property
    def operator(self) -> LogicalOperator:
        """获取逻辑运算符"""
        return self._operator
    
    @property
    def conditions(self) -> List[FilterCondition]:
        """获取直接包含的筛选条件列表"""
        return self._conditions.copy()
    
    @property
    def sub_groups(self) -> List['FilterGroup']:
        """获取嵌套的子条件组列表"""
        return self._sub_groups.copy()
    
    def match(self, stock: Any, calc_service: Any) -> bool:
        """
        评估股票是否匹配此条件组
        
        根据逻辑运算符对所有条件和子组的结果进行组合。
        
        Args:
            stock: 股票实体
            calc_service: 指标计算服务（IIndicatorCalculationService）
            
        Returns:
            如果股票匹配条件组返回 True，否则返回 False
            
        逻辑语义:
        - AND: 所有结果都为 True 时返回 True
        - OR: 至少一个结果为 True 时返回 True
        - NOT: 对第一个结果取反
        
        空组行为:
        - AND 空组返回 True
        - OR 空组返回 False
        - NOT 空组返回 True
        """
        # 收集所有条件和子组的评估结果
        results: List[bool] = []
        
        # 评估直接条件
        for cond in self._conditions:
            results.append(cond.evaluate(stock, calc_service))
        
        # 递归评估子组
        for group in self._sub_groups:
            results.append(group.match(stock, calc_service))
        
        # 处理空组情况
        if not results:
            # AND 空组返回 True（空集的全称量化为真）
            # OR 空组返回 False（空集的存在量化为假）
            # NOT 空组返回 True（无元素可取反）
            return self._operator != LogicalOperator.OR
        
        # 根据运算符组合结果
        if self._operator == LogicalOperator.AND:
            return all(results)
        elif self._operator == LogicalOperator.OR:
            return any(results)
        elif self._operator == LogicalOperator.NOT:
            # NOT 只对第一个结果取反
            return not results[0]
        
        # 默认返回 False（不应该到达这里）
        return False
    
    def has_any_condition(self) -> bool:
        """
        检查是否包含任何条件
        
        递归检查此组及所有子组是否包含至少一个筛选条件。
        
        Returns:
            如果包含至少一个条件返回 True，否则返回 False
        """
        # 检查直接条件
        if self._conditions:
            return True
        
        # 递归检查子组
        return any(g.has_any_condition() for g in self._sub_groups)
    
    def count_total_conditions(self) -> int:
        """
        统计总条件数
        
        递归统计此组及所有子组中的筛选条件总数。
        
        Returns:
            条件总数
        """
        # 统计直接条件
        count = len(self._conditions)
        
        # 递归统计子组条件
        for g in self._sub_groups:
            count += g.count_total_conditions()
        
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            包含 group_id、operator、conditions 和 sub_groups 的字典
        """
        return {
            'group_id': self._group_id,
            'operator': self._operator.value,
            'conditions': [c.to_dict() for c in self._conditions],
            'sub_groups': [g.to_dict() for g in self._sub_groups]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterGroup':
        """
        从字典反序列化
        
        Args:
            data: 包含 group_id、operator、conditions 和 sub_groups 的字典
            
        Returns:
            FilterGroup 实例
            
        Note:
            如果 group_id 不存在，会自动生成一个新的 UUID
        """
        return cls(
            group_id=data.get('group_id', str(uuid.uuid4())),
            operator=LogicalOperator(data['operator']),
            conditions=[FilterCondition.from_dict(c) for c in data.get('conditions', [])],
            sub_groups=[FilterGroup.from_dict(g) for g in data.get('sub_groups', [])]
        )
    
    def __eq__(self, other: object) -> bool:
        """判断两个 FilterGroup 是否相等"""
        if not isinstance(other, FilterGroup):
            return False
        return (self._group_id == other._group_id and
                self._operator == other._operator and
                len(self._conditions) == len(other._conditions) and
                all(c1 == c2 for c1, c2 in zip(self._conditions, other._conditions)) and
                len(self._sub_groups) == len(other._sub_groups) and
                all(g1 == g2 for g1, g2 in zip(self._sub_groups, other._sub_groups)))
    
    def __hash__(self) -> int:
        """计算哈希值"""
        return hash((self._group_id, self._operator))
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return (f"FilterGroup(group_id='{self._group_id}', "
                f"operator={self._operator.value}, "
                f"conditions={len(self._conditions)}, "
                f"sub_groups={len(self._sub_groups)})")
