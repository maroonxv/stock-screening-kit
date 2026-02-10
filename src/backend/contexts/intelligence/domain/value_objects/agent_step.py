"""AgentStep 值对象

LangGraph 工作流中单个 Agent 的执行记录，包含 Agent 名称、执行状态、
开始/完成时间、输出摘要和错误信息。
"""

from datetime import datetime
from typing import Optional

from ..enums.enums import AgentStepStatus


class AgentStep:
    """LangGraph 工作流中单个 Agent 的执行记录"""

    def __init__(
        self,
        agent_name: str,
        status: AgentStepStatus,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        output_summary: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        self._agent_name = agent_name
        self._status = status
        self._started_at = started_at
        self._completed_at = completed_at
        self._output_summary = output_summary
        self._error_message = error_message

    @property
    def agent_name(self) -> str:
        return self._agent_name

    @property
    def status(self) -> AgentStepStatus:
        return self._status

    @property
    def started_at(self) -> Optional[datetime]:
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        return self._completed_at

    @property
    def output_summary(self) -> Optional[str]:
        return self._output_summary

    @property
    def error_message(self) -> Optional[str]:
        return self._error_message

    def to_dict(self) -> dict:
        """序列化为字典，datetime 使用 isoformat"""
        return {
            "agent_name": self._agent_name,
            "status": self._status.value,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "output_summary": self._output_summary,
            "error_message": self._error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentStep":
        """从字典反序列化，datetime 使用 fromisoformat"""
        return cls(
            agent_name=data["agent_name"],
            status=AgentStepStatus(data["status"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            output_summary=data.get("output_summary"),
            error_message=data.get("error_message"),
        )

    def __eq__(self, other):
        """判断两个 AgentStep 是否相等"""
        return (
            isinstance(other, AgentStep)
            and self._agent_name == other._agent_name
            and self._status == other._status
            and self._started_at == other._started_at
            and self._completed_at == other._completed_at
            and self._output_summary == other._output_summary
            and self._error_message == other._error_message
        )

    def __hash__(self):
        """返回哈希值"""
        return hash((
            self._agent_name,
            self._status,
            self._started_at,
            self._completed_at,
            self._output_summary,
            self._error_message,
        ))

    def __eq__(self, other):
        """判断两个 AgentStep 是否相等"""
        return (
            isinstance(other, AgentStep)
            and self._agent_name == other._agent_name
            and self._status == other._status
            and self._started_at == other._started_at
            and self._completed_at == other._completed_at
            and self._output_summary == other._output_summary
            and self._error_message == other._error_message
        )

    def __hash__(self):
        """返回哈希值"""
        return hash((
            self._agent_name,
            self._status,
            self._started_at,
            self._completed_at,
            self._output_summary,
            self._error_message,
        ))

