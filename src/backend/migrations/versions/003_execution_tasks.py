"""Create execution_tasks table

Revision ID: 003_execution_tasks
Revises: 002_intelligence
Create Date: 2026-02-12 00:00:00.000000

Requirements: 8.2
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_execution_tasks'
down_revision = '002_intelligence'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'execution_tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('strategy_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress', sa.Integer(), server_default='0'),
        sa.Column('current_step', sa.String(length=200), server_default=''),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_execution_tasks_strategy_id', 'execution_tasks', ['strategy_id'])
    op.create_index('ix_execution_tasks_status', 'execution_tasks', ['status'])
    op.create_index('ix_execution_tasks_created_at', 'execution_tasks', ['created_at'])


def downgrade():
    op.drop_index('ix_execution_tasks_created_at', table_name='execution_tasks')
    op.drop_index('ix_execution_tasks_status', table_name='execution_tasks')
    op.drop_index('ix_execution_tasks_strategy_id', table_name='execution_tasks')
    op.drop_table('execution_tasks')
