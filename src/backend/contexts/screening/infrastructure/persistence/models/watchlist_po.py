"""WatchList 持久化对象 (PO)

SQLAlchemy ORM model for persisting WatchList aggregate root.
Uses JSONB for storing the stocks list (WatchedStock serialized structures).

Requirements: 6.1, 6.5
"""

from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB

from app import db


class WatchListPO(db.Model):
    """自选股列表持久化对象
    
    Maps to the 'watchlists' table in PostgreSQL.
    
    Attributes:
        id: UUID string (36 chars) as primary key
        name: Watchlist name, unique constraint
        description: Optional description text
        stocks: JSONB storing list of WatchedStock serialized structures
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = 'watchlists'
    
    # Primary key
    id = Column(String(36), primary_key=True)
    
    # Basic fields
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # JSONB field for stocks list
    stocks = Column(JSONB, default=list)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Indexes for query performance
    __table_args__ = (
        Index('ix_watchlists_updated_at', 'updated_at'),
    )
    
    def __repr__(self) -> str:
        """Debug representation of the PO object."""
        stock_count = len(self.stocks) if self.stocks else 0
        return (
            f"<WatchListPO("
            f"id='{self.id}', "
            f"name='{self.name}', "
            f"stocks_count={stock_count}"
            f")>"
        )
