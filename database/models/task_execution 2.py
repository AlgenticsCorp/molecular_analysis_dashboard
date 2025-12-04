"""Task framework execution tracking model."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, Integer, JSON, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TaskFrameworkExecution(Base):
    """Track executions of task framework tasks."""

    __tablename__ = 'task_framework_executions'

    # Primary key
    execution_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Organization and user
    org_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey('organizations.org_id', ondelete='CASCADE'),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False
    )

    # Task identification
    task_id: Mapped[str] = mapped_column(String(100), nullable=False, comment='Task framework task identifier')
    display_name: Mapped[str] = mapped_column(String(200), nullable=False, comment='Display name for the task')

    # Execution status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='pending')
    external_job_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment='External system job ID (e.g., NeuroSnap job ID)')

    # Data
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment='Task input parameters')
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment='Task output results')
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Progress tracking
    progress_percentage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    estimated_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Additional metadata
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment='Additional execution metadata')

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'execution_id': str(self.execution_id),
            'org_id': str(self.org_id),
            'user_id': str(self.user_id),
            'task_id': self.task_id,
            'display_name': self.display_name,
            'status': self.status,
            'external_job_id': self.external_job_id,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_message': self.error_message,
            'progress_percentage': self.progress_percentage,
            'estimated_duration_seconds': self.estimated_duration_seconds,
            'actual_duration_seconds': self.actual_duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.extra_metadata,
        }

    def update_status(self, status: str, **kwargs):
        """Update execution status and optional additional fields."""
        self.status = status
        self.updated_at = func.now()
        
        # Update specific fields if provided
        if 'error_message' in kwargs:
            self.error_message = kwargs['error_message']
        if 'output_data' in kwargs:
            self.output_data = kwargs['output_data']
        if 'progress_percentage' in kwargs:
            self.progress_percentage = kwargs['progress_percentage']
        if 'external_job_id' in kwargs:
            self.external_job_id = kwargs['external_job_id']
        
        # Set timestamps based on status
        if status == 'running' and not self.started_at:
            self.started_at = func.now()
        elif status in ['completed', 'failed', 'cancelled'] and not self.completed_at:
            self.completed_at = func.now()
            if self.started_at:
                # Calculate actual duration if we have both start and completion times
                duration = (datetime.utcnow() - self.started_at.replace(tzinfo=None)).total_seconds()
                self.actual_duration_seconds = int(duration)

    @property
    def is_complete(self) -> bool:
        """Check if execution is in a terminal state."""
        return self.status in ['completed', 'failed', 'cancelled']

    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self.status in ['pending', 'running', 'submitted']