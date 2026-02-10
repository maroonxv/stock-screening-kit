"""InvestigationTask 持久化对象 (PO)

SQLAlchemy ORM model for persisting InvestigationTask aggregate root.
Uses JSONB for storing complex nested structures (agent_steps, result).
The result_type field distinguishes between IndustryInsight and CredibilityReport.

Requirements: 5.1
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB

from app import db


class InvestigationTaskPO(db.Model):
    """调研任务持久化对象

    Maps to the 'investigation_tasks' table in PostgreSQL.

    Attributes:
        id: UUID string (36 chars) as primary key
        task_type: Task type (industry_research or credibility_verification)
        query: User query text
        status: Task status (pending, running, completed, failed, cancelled)
        progress: Progress percentage (0-100)
        agent_steps: JSONB storing list of AgentStep serialized structures
        result: JSONB storing IndustryInsight or CredibilityReport serialized structure
        result_type: Discriminator for result type (industry_insight or credibility_report)
        error_message: Optional error message text
        created_at: Creation timestamp
        updated_at: Last update timestamp
        completed_at: Optional completion timestamp
    """

    __tablename__ = 'investigation_tasks'

    # Primary key
    id = Column(String(36), primary_key=True)

    # Basic fields
    task_type = Column(String(50), nullable=False)
    query = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    progress = Column(Integer, nullable=False, default=0)

    # JSONB fields for complex nested structures
    agent_steps = Column(JSONB, default=[])
    result = Column(JSONB, nullable=True)
    result_type = Column(String(50), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Indexes for query performance
    __table_args__ = (
        Index('ix_investigation_tasks_status', 'status'),
        Index('ix_investigation_tasks_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        """Debug representation of the PO object."""
        return (
            f"<InvestigationTaskPO("
            f"id='{self.id}', "
            f"task_type='{self.task_type}', "
            f"status='{self.status}', "
            f"progress={self.progress}"
            f")>"
        )
