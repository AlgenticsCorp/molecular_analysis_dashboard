"""Domain entities for the metadata database (shared across organizations)."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, Boolean, Text, JSON, ForeignKey, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Organization(Base):
    """Organization entity - multi-tenant root."""

    __tablename__ = "organizations"

    # Primary key
    org_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    # Configuration
    quotas: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    settings: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    users: Mapped[List["User"]] = relationship("User", secondary="memberships", back_populates="organizations")
    task_definitions: Mapped[List["TaskDefinition"]] = relationship("TaskDefinition", back_populates="organization")
    pipeline_templates: Mapped[List["PipelineTemplate"]] = relationship("PipelineTemplate", back_populates="organization")


class User(Base):
    """User entity."""

    __tablename__ = "users"

    # Primary key
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Identity
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Metadata
    profile: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organizations: Mapped[List[Organization]] = relationship("Organization", secondary="memberships", back_populates="users")


class Membership(Base):
    """User-Organization membership."""

    __tablename__ = "memberships"

    # Composite primary key
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    org_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"), primary_key=True)

    # Membership details
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    member_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Role(Base):
    """Role definition within an organization."""

    __tablename__ = "roles"

    # Primary key
    role_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Role definition
    org_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RolePermission(Base):
    """Permissions assigned to roles."""

    __tablename__ = "role_permissions"

    # Composite primary key
    role_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)
    permission: Mapped[str] = mapped_column(String(100), primary_key=True)


class MembershipRole(Base):
    """Roles assigned to user memberships."""

    __tablename__ = "membership_roles"

    # Composite primary key and foreign keys
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    org_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)

    # Timestamps
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Foreign key constraint to membership
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "org_id"], ["memberships.user_id", "memberships.org_id"], ondelete="CASCADE"),
    )


class TaskDefinition(Base):
    """Dynamic task definitions with OpenAPI specifications."""

    __tablename__ = "task_definitions"

    # Primary key
    task_definition_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Task identification
    org_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")

    # Task definition
    task_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    interface_spec: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)  # OpenAPI 3.0 spec
    service_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Ownership
    created_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="task_definitions")
    services: Mapped[List["TaskService"]] = relationship("TaskService", back_populates="task_definition")


class TaskService(Base):
    """Running task service instances (service discovery)."""

    __tablename__ = "task_services"

    # Primary key
    service_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Service identification
    task_definition_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("task_definitions.task_definition_id", ondelete="CASCADE"), nullable=False)
    service_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Container/Pod info
    pod_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    node_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Health status
    health_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")  # healthy, unhealthy, starting, unknown
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Resource usage
    resources_used: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    task_definition: Mapped[TaskDefinition] = relationship("TaskDefinition", back_populates="services")


class PipelineTemplate(Base):
    """Pipeline templates for composable workflows."""

    __tablename__ = "pipeline_templates"

    # Primary key
    template_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Template identification
    org_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Template definition
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    workflow_definition: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    default_parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Visibility and status
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")

    # Ownership
    created_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    organization: Mapped[Organization] = relationship("Organization", back_populates="pipeline_templates")
    task_steps: Mapped[List["PipelineTaskStep"]] = relationship("PipelineTaskStep", back_populates="template")


class PipelineTaskStep(Base):
    """Task steps within a pipeline template."""

    __tablename__ = "pipeline_task_steps"

    # Primary key
    step_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Step identification
    template_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("pipeline_templates.template_id", ondelete="CASCADE"), nullable=False)
    task_definition_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("task_definitions.task_definition_id", ondelete="CASCADE"), nullable=False)

    # Step definition
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    step_order: Mapped[int] = mapped_column(nullable=False)
    depends_on: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    parameter_overrides: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    template: Mapped[PipelineTemplate] = relationship("PipelineTemplate", back_populates="task_steps")


class Molecule(Base):
    """Molecular structure catalog."""

    __tablename__ = "molecules"

    # Primary key
    molecule_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Molecule identification
    org_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # File info
    format: Mapped[str] = mapped_column(String(10), nullable=False)  # pdb, sdf, mol2, etc.
    uri: Mapped[str] = mapped_column(String(500), nullable=False)  # Storage URI
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA256
    size_bytes: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Metadata
    properties: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    tags: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")

    # Ownership and visibility
    uploaded_by: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="private")  # private, org, public

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AuditLog(Base):
    """Audit log for security and compliance."""

    __tablename__ = "audit_logs"

    # Primary key
    audit_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid()
    )

    # Event identification
    org_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)

    # Event details
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # Event data
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamp
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
