"""响应 DTO - 用于格式化 API 响应数据

实现 TaskResponseDTO，将 InvestigationTask 领域对象转换为 API 响应字典。
支持序列化所有嵌套的值对象（AgentStep、IndustryInsight、CredibilityReport）。

**Validates: Requirements 8.8**
"""
from typing import Any, Dict, List, Optional, Union

from ...domain.models.investigation_task import InvestigationTask
from ...domain.value_objects.industry_insight import IndustryInsight
from ...domain.value_objects.credibility_report import CredibilityReport


class TaskResponseDTO:
    """任务响应 DTO
    
    用于将 InvestigationTask 领域对象转换为 API 响应格式。
    支持序列化所有嵌套的值对象，包括 AgentStep、IndustryInsight 和 CredibilityReport。
    
    响应字段：
    - task_id: 任务唯一标识符
    - task_type: 任务类型（枚举值字符串）
    - query: 用户查询文本
    - status: 任务状态（枚举值字符串）
    - progress: 进度百分比（0-100）
    - agent_steps: Agent 执行步骤列表
    - result: 任务结果（IndustryInsight 或 CredibilityReport 序列化后的字典，或 None）
    - error_message: 错误信息（或 None）
    - created_at: 创建时间（ISO 格式字符串）
    - updated_at: 更新时间（ISO 格式字符串）
    - completed_at: 完成时间（ISO 格式字符串或 None）
    - duration: 执行时长（秒，或 None）
    """
    
    def __init__(
        self,
        task_id: str,
        task_type: str,
        query: str,
        status: str,
        progress: int,
        agent_steps: List[Dict[str, Any]],
        result: Optional[Dict[str, Any]],
        error_message: Optional[str],
        created_at: str,
        updated_at: str,
        completed_at: Optional[str],
        duration: Optional[float],
    ):
        """初始化 TaskResponseDTO
        
        Args:
            task_id: 任务唯一标识符
            task_type: 任务类型（枚举值字符串）
            query: 用户查询文本
            status: 任务状态（枚举值字符串）
            progress: 进度百分比（0-100）
            agent_steps: Agent 执行步骤列表（已序列化）
            result: 任务结果字典（或 None）
            error_message: 错误信息（或 None）
            created_at: 创建时间（ISO 格式字符串）
            updated_at: 更新时间（ISO 格式字符串）
            completed_at: 完成时间（ISO 格式字符串或 None）
            duration: 执行时长（秒，或 None）
        """
        self._task_id = task_id
        self._task_type = task_type
        self._query = query
        self._status = status
        self._progress = progress
        self._agent_steps = agent_steps
        self._result = result
        self._error_message = error_message
        self._created_at = created_at
        self._updated_at = updated_at
        self._completed_at = completed_at
        self._duration = duration
    
    @classmethod
    def from_domain(cls, task: InvestigationTask) -> 'TaskResponseDTO':
        """从领域对象创建响应 DTO
        
        将 InvestigationTask 聚合根转换为 TaskResponseDTO，
        序列化所有嵌套的值对象。
        
        Args:
            task: InvestigationTask 领域对象
            
        Returns:
            TaskResponseDTO 实例
        """
        # 序列化 agent_steps
        agent_steps = [step.to_dict() for step in task.agent_steps]
        
        # 序列化 result（IndustryInsight 或 CredibilityReport）
        result: Optional[Dict[str, Any]] = None
        if task.result is not None:
            result = task.result.to_dict()
        
        # 序列化时间字段
        created_at = task.created_at.isoformat()
        updated_at = task.updated_at.isoformat()
        completed_at = task.completed_at.isoformat() if task.completed_at else None
        
        return cls(
            task_id=task.task_id.value,
            task_type=task.task_type.value,
            query=task.query,
            status=task.status.value,
            progress=task.progress,
            agent_steps=agent_steps,
            result=result,
            error_message=task.error_message,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
            duration=task.duration,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为响应字典
        
        Returns:
            包含所有响应字段的字典
        """
        return {
            "task_id": self._task_id,
            "task_type": self._task_type,
            "query": self._query,
            "status": self._status,
            "progress": self._progress,
            "agent_steps": self._agent_steps,
            "result": self._result,
            "error_message": self._error_message,
            "created_at": self._created_at,
            "updated_at": self._updated_at,
            "completed_at": self._completed_at,
            "duration": self._duration,
        }
    
    # === 属性访问器 ===
    
    @property
    def task_id(self) -> str:
        """获取任务唯一标识符"""
        return self._task_id
    
    @property
    def task_type(self) -> str:
        """获取任务类型"""
        return self._task_type
    
    @property
    def query(self) -> str:
        """获取查询文本"""
        return self._query
    
    @property
    def status(self) -> str:
        """获取任务状态"""
        return self._status
    
    @property
    def progress(self) -> int:
        """获取进度百分比"""
        return self._progress
    
    @property
    def agent_steps(self) -> List[Dict[str, Any]]:
        """获取 Agent 执行步骤列表"""
        return self._agent_steps
    
    @property
    def result(self) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        return self._result
    
    @property
    def error_message(self) -> Optional[str]:
        """获取错误信息"""
        return self._error_message
    
    @property
    def created_at(self) -> str:
        """获取创建时间"""
        return self._created_at
    
    @property
    def updated_at(self) -> str:
        """获取更新时间"""
        return self._updated_at
    
    @property
    def completed_at(self) -> Optional[str]:
        """获取完成时间"""
        return self._completed_at
    
    @property
    def duration(self) -> Optional[float]:
        """获取执行时长"""
        return self._duration
    
    def __repr__(self) -> str:
        """返回字符串表示"""
        return (
            f"TaskResponseDTO(task_id='{self._task_id}', "
            f"task_type='{self._task_type}', "
            f"status='{self._status}', "
            f"progress={self._progress})"
        )
