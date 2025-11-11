"""Create task framework execution tracking table

Revision ID: 20241217_001_task_framework_execution
Revises: 20241119_add_task_definitions
Create Date: 2024-12-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision = "20241217_001_task_framework_execution"
down_revision = "20241119_add_task_definitions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create task_framework_executions table"""
    op.create_table(
        'task_framework_executions',
        sa.Column('execution_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('org_id', UUID(as_uuid=True), sa.ForeignKey('organizations.org_id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_id', sa.String(100), nullable=False, comment='Task framework task identifier'),
        sa.Column('display_name', sa.String(200), nullable=False, comment='Display name for the task'),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('external_job_id', sa.String(255), nullable=True, comment='External system job ID (e.g., NeuroSnap job ID)'),
        sa.Column('input_data', sa.JSON, nullable=True, comment='Task input parameters'),
        sa.Column('output_data', sa.JSON, nullable=True, comment='Task output results'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('progress_percentage', sa.Integer, nullable=True, default=0),
        sa.Column('estimated_duration_seconds', sa.Integer, nullable=True),
        sa.Column('actual_duration_seconds', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_metadata', sa.JSON, nullable=True, comment='Additional execution metadata'),
    )

    # Create indexes for performance
    op.create_index('idx_task_framework_executions_org_id', 'task_framework_executions', ['org_id'])
    op.create_index('idx_task_framework_executions_user_id', 'task_framework_executions', ['user_id'])
    op.create_index('idx_task_framework_executions_status', 'task_framework_executions', ['status'])
    op.create_index('idx_task_framework_executions_external_job_id', 'task_framework_executions', ['external_job_id'])
    op.create_index('idx_task_framework_executions_created_at', 'task_framework_executions', ['created_at'])


def downgrade() -> None:
    """Drop task_framework_executions table"""
    op.drop_index('idx_task_framework_executions_created_at', 'task_framework_executions')
    op.drop_index('idx_task_framework_executions_external_job_id', 'task_framework_executions')
    op.drop_index('idx_task_framework_executions_status', 'task_framework_executions')
    op.drop_index('idx_task_framework_executions_user_id', 'task_framework_executions')
    op.drop_index('idx_task_framework_executions_org_id', 'task_framework_executions')
    op.drop_table('task_framework_executions')