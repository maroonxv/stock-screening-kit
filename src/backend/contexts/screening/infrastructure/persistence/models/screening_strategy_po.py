"""ScreeningStrategy 持久化对象 (PO)

SQLAlchemy ORM model for persisting ScreeningStrategy aggregate root.
Uses JSONB for storing complex nested structures (filters, scoring_config, tags).

Requirements: 6.1, 6.5
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB

from extensions import db


class ScreeningStrategyPO(db.Model):
    """筛选策略持久化对象
    
    Maps to the 'screening_strategies' table in PostgreSQL.
    
    Attributes:
        id: UUID string (36 chars) as primary key
        name: Strategy name, unique constraint
        description: Optional description text
        filters: JSONB storing FilterGroup serialized structure
        scoring_config: JSONB storing ScoringConfig serialized structure
        tags: JSONB storing list of tag strings
        is_template: Boolean flag for template strategies
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'screening_strategies'
    
    # Primary key
    id = Column(String(36), primary_key=True)
    
    # Basic fields
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # JSONB fields for complex nested structures
    filters = Column(JSONB, nullable=False)
    scoring_config = Column(JSONB, nullable=False)
    tags = Column(JSONB, default=list)
    
    # Flags
    is_template = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Indexes for query performance
    __table_args__ = (
        Index('ix_screening_strategies_updated_at', 'updated_at'),
        Index('ix_screening_strategies_is_template', 'is_template'),
    )
    
    def __repr__(self) -> str:
        """Debug representation of the PO object."""
        return (
            f"<ScreeningStrategyPO("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"is_template={self.is_template}"
            f")>"
        )
