"""Initial migration - Create screening context tables

This migration creates the initial database schema for the Stock Screening Context:
- screening_strategies: Stores screening strategy definitions
- screening_sessions: Records screening execution results
- watchlists: Manages user watchlists

All tables use JSONB columns for storing complex nested structures,
which requires PostgreSQL as the database backend.

Revision ID: 001_initial
Revises: None
Create Date: 2024-01-01 00:00:00.000000

Requirements: 6.1, 6.5, 6.6, 10.5
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create initial tables for Stock Screening Context.
    
    Creates three tables:
    1. screening_strategies - ScreeningStrategyPO
    2. screening_sessions - ScreeningSessionPO
    3. watchlists - WatchListPO
    
    All tables use JSONB for complex nested structures.
    """
    # Create screening_strategies table
    op.create_table(
        'screening_strategies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('filters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('scoring_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_template', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create indexes for screening_strategies
    op.create_index(
        'ix_screening_strategies_updated_at',
        'screening_strategies',
        ['updated_at'],
        unique=False
    )
    op.create_index(
        'ix_screening_strategies_is_template',
        'screening_strategies',
        ['is_template'],
        unique=False
    )
    
    # Create screening_sessions table
    op.create_table(
        'screening_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('strategy_id', sa.String(length=36), nullable=False),
        sa.Column('strategy_name', sa.String(length=200), nullable=False),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.Column('total_scanned', sa.Integer(), nullable=False),
        sa.Column('execution_time', sa.Float(), nullable=False),
        sa.Column('top_stocks', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('other_stock_codes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('filters_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('scoring_config_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for screening_sessions
    op.create_index(
        'ix_screening_sessions_strategy_id',
        'screening_sessions',
        ['strategy_id'],
        unique=False
    )
    op.create_index(
        'ix_screening_sessions_executed_at',
        'screening_sessions',
        ['executed_at'],
        unique=False
    )
    op.create_index(
        'ix_screening_sessions_strategy_executed',
        'screening_sessions',
        ['strategy_id', 'executed_at'],
        unique=False
    )
    
    # Create watchlists table
    op.create_table(
        'watchlists',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('stocks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create indexes for watchlists
    op.create_index(
        'ix_watchlists_updated_at',
        'watchlists',
        ['updated_at'],
        unique=False
    )


def downgrade():
    """Drop all tables created in this migration.
    
    Drops tables in reverse order of creation to handle any potential dependencies.
    """
    # Drop watchlists table and indexes
    op.drop_index('ix_watchlists_updated_at', table_name='watchlists')
    op.drop_table('watchlists')
    
    # Drop screening_sessions table and indexes
    op.drop_index('ix_screening_sessions_strategy_executed', table_name='screening_sessions')
    op.drop_index('ix_screening_sessions_executed_at', table_name='screening_sessions')
    op.drop_index('ix_screening_sessions_strategy_id', table_name='screening_sessions')
    op.drop_table('screening_sessions')
    
    # Drop screening_strategies table and indexes
    op.drop_index('ix_screening_strategies_is_template', table_name='screening_strategies')
    op.drop_index('ix_screening_strategies_updated_at', table_name='screening_strategies')
    op.drop_table('screening_strategies')
