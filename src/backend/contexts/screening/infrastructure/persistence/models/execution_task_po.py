"""ExecutionTask 持久化对象 (PO)

Requirements: 8.2
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB

from extensions import db


class ExecutionTaskPO(db.Model):
    """执行任务持久化对象"""
    __tablename__ = 'execution_tasks'

    id = Column(String(36), primary_key=True)
    strategy_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    progress = Column(Integer, default=0)
    current_step = Column(String(200), default="")
    result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('ix_execution_tasks_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        return (
            f"<ExecutionTaskPO(id='{self.id}', "
            f"strategy_id='{self.strategy_id}', "
            f"status='{self.status}')>"
        )
