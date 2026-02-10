"""Create intelligence context tables

This migration creates the database schema for the Investment Intelligence Context:
- investigation_tasks: Stores AI-driven investigation task definitions and results

The investigation_tasks table uses JSONB columns for storing complex nested structures
(agent_steps, result), which requires PostgreSQL as the database backend.
The result_type column discriminates between IndustryInsight and CredibilityReport
result types stored in the result JSONB column.

Revision ID: 002_intelligence
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000

Requirements: 5.1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_intelligence'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    """Create tables for Investment Intelligence Context.

    Creates one table:
    1. investigation_tasks - InvestigationTaskPO

    Uses JSONB for agent_steps and result fields.
    """
    # Create investigation_tasks table
    op.create_table(
        'investigation_tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('agent_steps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result_type', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for investigation_tasks
    op.create_index(
        'ix_investigation_tasks_status',
        'investigation_tasks',
        ['status'],
        unique=False,
    )
    op.create_index(
        'ix_investigation_tasks_created_at',
        'investigation_tasks',
        ['created_at'],
        unique=False,
    )


def downgrade():
    """Drop all tables created in this migration."""
    # Drop investigation_tasks table and indexes
    op.drop_index('ix_investigation_tasks_created_at', table_name='investigation_tasks')
    op.drop_index('ix_investigation_tasks_status', table_name='investigation_tasks')
    op.drop_table('investigation_tasks')
