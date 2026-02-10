"""ScreeningSession 持久化对象 (PO)

SQLAlchemy ORM model for persisting ScreeningSession aggregate root.
Uses JSONB for storing complex nested structures (top_stocks, other_stock_codes,
filters_snapshot, scoring_config_snapshot).

Requirements: 6.1, 6.6
"""

from sqlalchemy import Column, String, DateTime, Integer, Float, Index
from sqlalchemy.dialects.postgresql import JSONB

from app import db


class ScreeningSessionPO(db.Model):
    """筛选会话持久化对象
    
    Maps to the 'screening_sessions' table in PostgreSQL.
    Records the execution result of a screening strategy.
    
    Attributes:
        id: UUID string (36 chars) as primary key
        strategy_id: Reference to the strategy that was executed
        strategy_name: Snapshot of strategy name at execution time
        executed_at: Timestamp when the screening was executed
        total_scanned: Total number of stocks scanned
        execution_time: Time taken to execute the screening (in seconds)
        top_stocks: JSONB storing list of ScoredStock serialized structures
        other_stock_codes: JSONB storing list of stock codes not in top results
        filters_snapshot: JSONB storing FilterGroup snapshot at execution time
        scoring_config_snapshot: JSONB storing ScoringConfig snapshot at execution time
    """
    
    __tablename__ = 'screening_sessions'
    
    # Primary key
    id = Column(String(36), primary_key=True)
    
    # Strategy reference (not a foreign key to allow strategy deletion)
    strategy_id = Column(String(36), nullable=False, index=True)
    strategy_name = Column(String(200), nullable=False)
    
    # Execution metadata
    executed_at = Column(DateTime, nullable=False, index=True)
    total_scanned = Column(Integer, nullable=False)
    execution_time = Column(Float, nullable=False)
    
    # JSONB fields for complex nested structures
    top_stocks = Column(JSONB, nullable=False)
    other_stock_codes = Column(JSONB, default=list)
    
    # Snapshots of strategy configuration at execution time
    filters_snapshot = Column(JSONB, nullable=False)
    scoring_config_snapshot = Column(JSONB, nullable=False)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('ix_screening_sessions_strategy_executed', 'strategy_id', 'executed_at'),
    )
    
    def __repr__(self) -> str:
        """Debug representation of the PO object."""
        return (
            f"<ScreeningSessionPO("
            f"id='{self.id}', "
            f"strategy_id='{self.strategy_id}', "
            f"strategy_name='{self.strategy_name}', "
            f"executed_at={self.executed_at}, "
            f"total_scanned={self.total_scanned}"
            f")>"
        )
