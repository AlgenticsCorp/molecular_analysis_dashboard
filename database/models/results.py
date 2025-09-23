"""Domain entities for results databases (per-organization)."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, Boolean, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Job(Base):
    """Main job execution entity."""

    __tablename__ = "jobs"

    # Primary key
    job_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Job identification
    pipeline_version: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED, CANCELED

    # Input signature for caching
    input_signature: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA256 hash

    # Job metadata
    job_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Execution tracking
    submitted_by: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)  # User ID from metadata DB
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Relationships
    inputs: Mapped[List["JobInput"]] = relationship("JobInput", back_populates="job", cascade="all, delete-orphan")
    outputs: Mapped[List["JobOutput"]] = relationship("JobOutput", back_populates="job", cascade="all, delete-orphan")
    task_executions: Mapped[List["TaskExecution"]] = relationship("TaskExecution", back_populates="job", cascade="all, delete-orphan")
    events: Mapped[List["JobEvent"]] = relationship("JobEvent", back_populates="job", cascade="all, delete-orphan")


class JobInput(Base):
    """Job input parameters and files."""

    __tablename__ = "job_inputs"

    # Composite primary key
    job_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True)
    key: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Input data
    value: Mapped[str] = mapped_column(Text, nullable=False)  # URI, parameter value, etc.
    input_type: Mapped[str] = mapped_column(String(20), nullable=False)  # file, parameter, molecule_id
    input_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Relationships
    job: Mapped[Job] = relationship("Job", back_populates="inputs")


class JobOutput(Base):
    """Job output files and artifacts."""

    __tablename__ = "job_outputs"

    # Composite primary key
    job_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True)
    key: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Output data
    uri: Mapped[str] = mapped_column(String(500), nullable=False)  # Storage URI
    output_type: Mapped[str] = mapped_column(String(20), nullable=False)  # result_file, log_file, visualization
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Metadata
    output_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    job: Mapped[Job] = relationship("Job", back_populates="outputs")


class TaskExecution(Base):
    """Individual task execution within a job."""

    __tablename__ = "task_executions"

    # Primary key
    exec_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Job relationship
    job_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False)

    # Task identification
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)
    task_definition_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # For dynamic tasks
    service_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Which service executed this

    # Execution status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")

    # Parameters and results
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    execution_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Logs
    logs_uri: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    job: Mapped[Job] = relationship("Job", back_populates="task_executions")
    dynamic_results: Mapped[List["DynamicTaskResult"]] = relationship("DynamicTaskResult", back_populates="execution", cascade="all, delete-orphan")


class DynamicTaskResult(Base):
    """Results from dynamic task executions."""

    __tablename__ = "dynamic_task_results"

    # Primary key
    result_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Execution relationship
    exec_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("task_executions.exec_id", ondelete="CASCADE"), nullable=False)

    # Result data
    result_schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    result_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    validation_errors: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Quality metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    execution: Mapped[TaskExecution] = relationship("TaskExecution", back_populates="dynamic_results")


class DockingResult(Base):
    """Specific docking analysis results."""

    __tablename__ = "docking_results"

    # Composite primary key
    job_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True)
    pose_rank: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Docking scores
    affinity: Mapped[float] = mapped_column(Float, nullable=False)  # Binding affinity (kcal/mol)
    rmsd_lb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # RMSD lower bound
    rmsd_ub: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # RMSD upper bound

    # Pose data
    pose_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Quality metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class TaskResult(Base):
    """Generic task-level results with confidence scoring."""

    __tablename__ = "task_results"

    # Composite primary key
    job_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True)
    task_name: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Result data
    result_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1")

    # Quality and confidence
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    validation_errors: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Service info
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ResultCache(Base):
    """Cache for reusing computation results."""

    __tablename__ = "result_cache"

    # Primary key
    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)  # SHA256 hash

    # Cache data
    job_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(100), nullable=False)
    task_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Cache metadata
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class JobEvent(Base):
    """Job execution events timeline."""

    __tablename__ = "job_events"

    # Composite primary key
    job_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True)
    seq_no: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Event data
    event: Mapped[str] = mapped_column(String(50), nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Timestamp
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    job: Mapped[Job] = relationship("Job", back_populates="events")
