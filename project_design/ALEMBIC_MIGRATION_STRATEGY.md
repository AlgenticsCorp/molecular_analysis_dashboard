# Alembic Migration Strategy

## Overview

The application uses **Alembic** for database schema versioning with a **dual-database migration strategy** that supports both the shared metadata database and per-organization results databases with automated provisioning and coordinated schema evolution.

## Migration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Alembic Configuration                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │ Metadata Branch │    │      Results Branch                 │  │
│  │                 │    │                                     │  │
│  │ • Organizations │    │ • Docking Jobs                      │  │
│  │ • Users         │    │ • Task Results                      │  │
│  │ • Identities    │    │ • Artifacts                         │  │
│  │ • Settings      │    │ • Input Signatures (cache)         │  │
│  │ • Audit Logs    │    │ • Job Events                        │  │
│  └─────────────────┘    └─────────────────────────────────────┘  │
│           │                            │                        │
│           ▼                            ▼                        │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │    mad (DB)     │    │  mad_results_{org_id} (Per-org)    │  │
│  │   (Shared)      │    │          (Isolated)                │  │
│  └─────────────────┘    └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
alembic/
├── alembic.ini                         # Main Alembic configuration
├── env.py                              # Environment setup and multi-database support
├── script.py.mako                      # Migration template
├── versions/
│   ├── metadata/                       # Metadata database migrations
│   │   ├── 001_initial_organizations.py
│   │   ├── 002_add_users_table.py
│   │   ├── 003_add_identity_providers.py
│   │   └── 004_add_audit_logging.py
│   └── results/                        # Results database migrations
│       ├── 001_initial_docking_schema.py
│       ├── 002_add_task_results.py
│       ├── 003_add_caching_tables.py
│       └── 004_add_job_events.py
└── utils/
    ├── __init__.py
    ├── migration_helpers.py             # Shared migration utilities
    └── org_database_provisioner.py     # Org database creation helper
```

## Alembic Configuration

### Main Configuration (`alembic.ini`)

```ini
# alembic.ini
[alembic]
# Multi-environment setup
script_location = alembic
version_locations = alembic/versions/metadata alembic/versions/results

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S

# Environment-specific configurations
[metadata]
sqlalchemy.url = postgresql+asyncpg://mad:password@postgres:5432/mad
version_table = alembic_version_metadata
version_locations = alembic/versions/metadata

[results]
sqlalchemy.url = postgresql+asyncpg://mad:password@postgres:5432/mad_results_template
version_table = alembic_version_results
version_locations = alembic/versions/results
```

### Environment Setup (`env.py`)

```python
# alembic/env.py
import asyncio
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Add src to path for model imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from infrastructure.config import get_database_settings
from domain.models.metadata import metadata as metadata_models
from domain.models.results import metadata as results_models

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url_for_branch(branch_name: str) -> str:
    """Get database URL for specific migration branch."""
    db_settings = get_database_settings()

    if branch_name == "metadata":
        return db_settings.database_url
    elif branch_name == "results":
        # Use template database for results migrations
        return db_settings.results_db_template.format(org_id="template")
    else:
        raise ValueError(f"Unknown migration branch: {branch_name}")

def get_metadata_for_branch(branch_name: str):
    """Get SQLAlchemy metadata for specific branch."""
    if branch_name == "metadata":
        return metadata_models
    elif branch_name == "results":
        return results_models
    else:
        raise ValueError(f"Unknown migration branch: {branch_name}")

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    # Determine which branch we're running
    branch_name = os.environ.get('ALEMBIC_BRANCH', 'metadata')

    url = get_url_for_branch(branch_name)
    target_metadata = get_metadata_for_branch(branch_name)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=f"alembic_version_{branch_name}",
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Run migrations with database connection."""
    branch_name = os.environ.get('ALEMBIC_BRANCH', 'metadata')
    target_metadata = get_metadata_for_branch(branch_name)

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table=f"alembic_version_{branch_name}",
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    """Run migrations in async mode."""
    branch_name = os.environ.get('ALEMBIC_BRANCH', 'metadata')
    url = get_url_for_branch(branch_name)

    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())

# Determine run mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Migration Utilities

### Migration Helpers (`alembic/utils/migration_helpers.py`)

```python
# alembic/utils/migration_helpers.py
"""Shared utilities for Alembic migrations."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from typing import List, Dict, Any

def create_enum_type(enum_name: str, values: List[str], schema: str = None):
    """Create PostgreSQL ENUM type if it doesn't exist."""
    # NOTE: PostgreSQL ENUMs require special handling in migrations
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN
                CREATE TYPE {schema + '.' if schema else ''}{enum_name} AS ENUM ({', '.join(f"'{v}'" for v in values)});
            END IF;
        END$$;
    """)

def drop_enum_type(enum_name: str, schema: str = None):
    """Drop PostgreSQL ENUM type if it exists."""
    full_name = f"{schema}.{enum_name}" if schema else enum_name
    op.execute(f"DROP TYPE IF EXISTS {full_name} CASCADE")

def add_audit_columns(table_name: str, schema: str = None):
    """Add standard audit columns to a table."""
    # RATIONALE: consistent audit trail across all tables
    op.add_column(
        table_name,
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=schema
    )
    op.add_column(
        table_name,
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema=schema
    )
    op.add_column(
        table_name,
        sa.Column('created_by', sa.String(255), nullable=True),
        schema=schema
    )
    op.add_column(
        table_name,
        sa.Column('updated_by', sa.String(255), nullable=True),
        schema=schema
    )

def create_updated_at_trigger(table_name: str, schema: str = None):
    """Create trigger to automatically update 'updated_at' column."""
    full_table_name = f"{schema}.{table_name}" if schema else table_name
    trigger_name = f"update_{table_name}_updated_at"

    # Create the trigger function if it doesn't exist
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Create the trigger
    op.execute(f"""
        CREATE TRIGGER {trigger_name}
            BEFORE UPDATE ON {full_table_name}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

def add_uuid_primary_key(table_name: str, column_name: str = 'id', schema: str = None):
    """Add UUID primary key column with default generation."""
    op.add_column(
        table_name,
        sa.Column(
            column_name,
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False
        ),
        schema=schema
    )

def create_index_if_not_exists(index_name: str, table_name: str, columns: List[str], unique: bool = False, schema: str = None):
    """Create index if it doesn't already exist."""
    full_table_name = f"{schema}.{table_name}" if schema else table_name
    unique_clause = "UNIQUE" if unique else ""
    columns_clause = ", ".join(columns)

    op.execute(f"""
        CREATE {unique_clause} INDEX IF NOT EXISTS {index_name}
        ON {full_table_name} ({columns_clause})
    """)

def add_foreign_key_with_index(
    constraint_name: str,
    source_table: str,
    source_column: str,
    target_table: str,
    target_column: str,
    ondelete: str = "CASCADE",
    schema: str = None
):
    """Add foreign key constraint and create supporting index."""
    # Add foreign key constraint
    op.create_foreign_key(
        constraint_name,
        source_table,
        target_table,
        [source_column],
        [target_column],
        ondelete=ondelete,
        source_schema=schema,
        referent_schema=schema
    )

    # Create index for foreign key (improves join performance)
    index_name = f"idx_{source_table}_{source_column}"
    create_index_if_not_exists(index_name, source_table, [source_column], schema=schema)

def create_partial_index(
    index_name: str,
    table_name: str,
    columns: List[str],
    where_clause: str,
    unique: bool = False,
    schema: str = None
):
    """Create partial index with WHERE clause."""
    full_table_name = f"{schema}.{table_name}" if schema else table_name
    unique_clause = "UNIQUE" if unique else ""
    columns_clause = ", ".join(columns)

    op.execute(f"""
        CREATE {unique_clause} INDEX IF NOT EXISTS {index_name}
        ON {full_table_name} ({columns_clause})
        WHERE {where_clause}
    """)
```

### Organization Database Provisioner (`alembic/utils/org_database_provisioner.py`)

```python
# alembic/utils/org_database_provisioner.py
"""Utility for provisioning per-organization databases."""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from alembic.config import Config
from alembic import command
import os
import tempfile

logger = logging.getLogger(__name__)

class OrgDatabaseProvisioner:
    """Provisions and migrates per-organization databases."""

    def __init__(self, admin_dsn: str, results_dsn_template: str):
        self.admin_dsn = admin_dsn
        self.results_dsn_template = results_dsn_template

    async def provision_org_database(self, org_id: str) -> bool:
        """
        Create and migrate database for organization.

        Args:
            org_id: Organization identifier

        Returns:
            True if successful, False otherwise
        """
        db_name = f"mad_results_{org_id}"

        try:
            # Step 1: Create database
            await self._create_database(db_name)

            # Step 2: Run migrations
            await self._migrate_org_database(org_id)

            logger.info(f"Successfully provisioned database for org {org_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to provision database for org {org_id}: {e}")
            return False

    async def _create_database(self, db_name: str):
        """Create PostgreSQL database if it doesn't exist."""
        # Connect to postgres database to create new database
        admin_engine = create_async_engine(
            self.admin_dsn,
            isolation_level="AUTOCOMMIT"
        )

        try:
            async with admin_engine.begin() as conn:
                # Check if database exists
                result = await conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": db_name}
                )

                if not result.fetchone():
                    # Create database
                    await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                    logger.info(f"Created database: {db_name}")
                else:
                    logger.info(f"Database already exists: {db_name}")

        finally:
            await admin_engine.dispose()

    async def _migrate_org_database(self, org_id: str):
        """Run Alembic migrations on organization database."""
        org_dsn = self.results_dsn_template.format(org_id=org_id)

        # Create temporary alembic config for this org
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_config:
            config_content = f"""
[alembic]
script_location = alembic
version_locations = alembic/versions/results

[results]
sqlalchemy.url = {org_dsn}
version_table = alembic_version_results
version_locations = alembic/versions/results
"""
            temp_config.write(config_content)
            temp_config_path = temp_config.name

        try:
            # Set environment variable for branch selection
            os.environ['ALEMBIC_BRANCH'] = 'results'

            # Run migrations
            alembic_cfg = Config(temp_config_path)
            alembic_cfg.set_section_option('results', 'sqlalchemy.url', org_dsn)

            # Upgrade to head
            command.upgrade(alembic_cfg, "head")

            logger.info(f"Completed migrations for org {org_id}")

        finally:
            # Clean up
            os.unlink(temp_config_path)
            if 'ALEMBIC_BRANCH' in os.environ:
                del os.environ['ALEMBIC_BRANCH']

    async def deprovision_org_database(self, org_id: str) -> bool:
        """
        Remove organization database (careful operation).

        Args:
            org_id: Organization identifier

        Returns:
            True if successful, False otherwise
        """
        db_name = f"mad_results_{org_id}"

        try:
            admin_engine = create_async_engine(
                self.admin_dsn,
                isolation_level="AUTOCOMMIT"
            )

            async with admin_engine.begin() as conn:
                # Terminate connections to the database
                await conn.execute(text(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
                """))

                # Drop database
                await conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))

            await admin_engine.dispose()

            logger.info(f"Deprovisioned database for org {org_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to deprovision database for org {org_id}: {e}")
            return False

    async def list_org_databases(self) -> List[str]:
        """List all organization databases."""
        admin_engine = create_async_engine(self.admin_dsn)

        try:
            async with admin_engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT datname
                    FROM pg_database
                    WHERE datname LIKE 'mad_results_%'
                    ORDER BY datname
                """))

                return [row[0] for row in result.fetchall()]

        finally:
            await admin_engine.dispose()
```

## Migration Templates

### Metadata Migration Example

```python
# alembic/versions/metadata/001_initial_organizations.py
"""Initial organizations schema

Revision ID: 001_meta
Revises:
Create Date: 2025-09-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic.utils.migration_helpers import (
    create_enum_type, add_audit_columns, create_updated_at_trigger,
    add_uuid_primary_key, create_index_if_not_exists
)

# revision identifiers
revision = '001_meta'
down_revision = None
branch_labels = ('metadata',)
depends_on = None

def upgrade():
    """Create initial organizations schema."""

    # Create enum types
    create_enum_type('organization_status', ['active', 'suspended', 'deleted'])
    create_enum_type('subscription_tier', ['free', 'professional', 'enterprise'])

    # Organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.Enum('active', 'suspended', 'deleted', name='organization_status'), nullable=False, server_default='active'),
        sa.Column('subscription_tier', sa.Enum('free', 'professional', 'enterprise', name='subscription_tier'), nullable=False, server_default='free'),
        sa.Column('max_concurrent_jobs', sa.Integer, nullable=False, server_default='5'),
        sa.Column('storage_quota_gb', sa.Integer, nullable=False, server_default='10'),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('settings', sa.JSON),
    )

    # Add audit columns and triggers
    add_audit_columns('organizations')
    create_updated_at_trigger('organizations')

    # Create indexes
    create_index_if_not_exists('idx_organizations_name', 'organizations', ['name'], unique=True)
    create_index_if_not_exists('idx_organizations_status', 'organizations', ['status'])
    create_index_if_not_exists('idx_organizations_tier', 'organizations', ['subscription_tier'])

def downgrade():
    """Drop organizations schema."""
    op.drop_table('organizations')
    op.execute('DROP TYPE IF EXISTS organization_status CASCADE')
    op.execute('DROP TYPE IF EXISTS subscription_tier CASCADE')
```

### Results Migration Example

```python
# alembic/versions/results/001_initial_docking_schema.py
"""Initial docking results schema

Revision ID: 001_results
Revises:
Create Date: 2025-09-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic.utils.migration_helpers import (
    create_enum_type, add_audit_columns, create_updated_at_trigger,
    add_uuid_primary_key, create_index_if_not_exists, create_partial_index
)

# revision identifiers
revision = '001_results'
down_revision = None
branch_labels = ('results',)
depends_on = None

def upgrade():
    """Create initial docking results schema."""

    # Create enum types
    create_enum_type('job_status', ['pending', 'running', 'completed', 'failed', 'cancelled'])
    create_enum_type('artifact_type', ['receptor', 'ligand', 'docking_result', 'execution_log', 'analysis_report'])

    # Docking jobs table
    op.create_table(
        'docking_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),  # Reference to metadata DB
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),  # Reference to metadata DB
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='job_status'), nullable=False, server_default='pending'),
        sa.Column('engine_name', sa.String(50), nullable=False),
        sa.Column('engine_version', sa.String(50)),
        sa.Column('params', sa.JSON, nullable=False),
        sa.Column('input_signature', sa.String(64), nullable=False),  # SHA256 hash for caching
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('execution_time_seconds', sa.Float),
        sa.Column('error_message', sa.Text),
        sa.Column('metadata', sa.JSON),
    )

    # Task results table (engine-agnostic results)
    op.create_table(
        'task_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('result_data', sa.JSON, nullable=False),
        sa.Column('confidence_score', sa.Float),
        sa.Column('execution_time_seconds', sa.Float),
        sa.Column('metadata', sa.JSON),
    )

    # Artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('artifact_type', sa.Enum('receptor', 'ligand', 'docking_result', 'execution_log', 'analysis_report', name='artifact_type'), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100)),
        sa.Column('size_bytes', sa.BigInteger, nullable=False),
        sa.Column('checksum_sha256', sa.String(64), nullable=False),
        sa.Column('metadata', sa.JSON),
    )

    # Add audit columns
    add_audit_columns('docking_jobs')
    add_audit_columns('task_results')
    add_audit_columns('artifacts')

    # Create triggers
    create_updated_at_trigger('docking_jobs')
    create_updated_at_trigger('task_results')
    create_updated_at_trigger('artifacts')

    # Create foreign key relationships
    op.create_foreign_key('fk_task_results_job', 'task_results', 'docking_jobs', ['job_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_artifacts_job', 'artifacts', 'docking_jobs', ['job_id'], ['id'], ondelete='CASCADE')

    # Create indexes for performance
    create_index_if_not_exists('idx_docking_jobs_org_id', 'docking_jobs', ['org_id'])
    create_index_if_not_exists('idx_docking_jobs_user_id', 'docking_jobs', ['user_id'])
    create_index_if_not_exists('idx_docking_jobs_status', 'docking_jobs', ['status'])
    create_index_if_not_exists('idx_docking_jobs_input_signature', 'docking_jobs', ['input_signature'])
    create_index_if_not_exists('idx_docking_jobs_created_at', 'docking_jobs', ['created_at'])

    # Partial indexes for active jobs
    create_partial_index('idx_active_jobs', 'docking_jobs', ['status', 'created_at'], "status IN ('pending', 'running')")

    create_index_if_not_exists('idx_task_results_job_id', 'task_results', ['job_id'])
    create_index_if_not_exists('idx_artifacts_job_id', 'artifacts', ['job_id'])
    create_index_if_not_exists('idx_artifacts_type', 'artifacts', ['artifact_type'])

def downgrade():
    """Drop docking results schema."""
    op.drop_table('artifacts')
    op.drop_table('task_results')
    op.drop_table('docking_jobs')
    op.execute('DROP TYPE IF EXISTS job_status CASCADE')
    op.execute('DROP TYPE IF EXISTS artifact_type CASCADE')
```

## Migration Commands

### Shell Scripts for Common Operations

```bash
#!/bin/bash
# scripts/migrate.sh - Migration convenience script

set -e

COMMAND=${1:-"upgrade"}
BRANCH=${2:-"all"}

case $COMMAND in
    "init")
        echo "Initializing Alembic..."
        ALEMBIC_BRANCH=metadata alembic init alembic
        ;;
    "upgrade")
        if [ "$BRANCH" = "all" ]; then
            echo "Upgrading metadata database..."
            ALEMBIC_BRANCH=metadata alembic -n metadata upgrade head

            echo "Upgrading results template database..."
            ALEMBIC_BRANCH=results alembic -n results upgrade head
        else
            echo "Upgrading $BRANCH database..."
            ALEMBIC_BRANCH=$BRANCH alembic -n $BRANCH upgrade head
        fi
        ;;
    "downgrade")
        if [ "$BRANCH" = "all" ]; then
            echo "Downgrading results template database..."
            ALEMBIC_BRANCH=results alembic -n results downgrade -1

            echo "Downgrading metadata database..."
            ALEMBIC_BRANCH=metadata alembic -n metadata downgrade -1
        else
            echo "Downgrading $BRANCH database..."
            ALEMBIC_BRANCH=$BRANCH alembic -n $BRANCH downgrade -1
        fi
        ;;
    "revision")
        BRANCH=${2:-"metadata"}
        MESSAGE=${3:-"New migration"}
        echo "Creating new $BRANCH migration: $MESSAGE"
        ALEMBIC_BRANCH=$BRANCH alembic -n $BRANCH revision --autogenerate -m "$MESSAGE"
        ;;
    "history")
        BRANCH=${2:-"metadata"}
        echo "Migration history for $BRANCH:"
        ALEMBIC_BRANCH=$BRANCH alembic -n $BRANCH history
        ;;
    "current")
        BRANCH=${2:-"metadata"}
        echo "Current migration for $BRANCH:"
        ALEMBIC_BRANCH=$BRANCH alembic -n $BRANCH current
        ;;
    *)
        echo "Usage: $0 {init|upgrade|downgrade|revision|history|current} [branch] [message]"
        echo "Branches: metadata, results, all"
        exit 1
        ;;
esac
```

## Docker Integration

### Migration Service in Docker Compose

```yaml
# docker-compose.yml (migration service)
services:
  migrate:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    environment:
      <<: *common-env
    depends_on:
      postgres:
        condition: service_healthy
    command: ["bash", "-c", "scripts/migrate.sh upgrade all"]
    restart: "no"
    networks: [appnet]

  # Optional: separate migration services for each branch
  migrate-metadata:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    environment:
      <<: *common-env
    depends_on:
      postgres:
        condition: service_healthy
    command: ["bash", "-c", "scripts/migrate.sh upgrade metadata"]
    restart: "no"
    networks: [appnet]

  migrate-results:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    environment:
      <<: *common-env
    depends_on:
      postgres:
        condition: service_healthy
    command: ["bash", "-c", "scripts/migrate.sh upgrade results"]
    restart: "no"
    networks: [appnet]
```

## Testing Migrations

```python
# tests/integration/test_migrations.py
import pytest
import tempfile
from pathlib import Path
from alembic.config import Config
from alembic import command
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.mark.integration
async def test_metadata_migrations():
    """Test metadata database migrations."""
    # Use temporary database for testing
    test_db_url = "postgresql+asyncpg://test:test@localhost/test_metadata"

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test alembic config
        config_path = Path(temp_dir) / "alembic.ini"
        config_content = f"""
[alembic]
script_location = alembic
version_locations = alembic/versions/metadata

[metadata]
sqlalchemy.url = {test_db_url}
version_table = alembic_version_metadata
"""
        config_path.write_text(config_content)

        # Run migrations
        alembic_cfg = Config(str(config_path))

        # Test upgrade
        command.upgrade(alembic_cfg, "head")

        # Test downgrade
        command.downgrade(alembic_cfg, "base")

@pytest.mark.integration
async def test_org_database_provisioning():
    """Test organization database provisioning."""
    from alembic.utils.org_database_provisioner import OrgDatabaseProvisioner

    admin_dsn = "postgresql+asyncpg://test:test@localhost/postgres"
    results_template = "postgresql+asyncpg://test:test@localhost/test_results_{org_id}"

    provisioner = OrgDatabaseProvisioner(admin_dsn, results_template)

    # Test provisioning
    success = await provisioner.provision_org_database("test_org")
    assert success

    # Test database exists
    org_dbs = await provisioner.list_org_databases()
    assert "test_results_test_org" in org_dbs

    # Test deprovisioning
    success = await provisioner.deprovision_org_database("test_org")
    assert success
```

## Integration with Application

```python
# infrastructure/database.py (enhanced with migration support)
from alembic.utils.org_database_provisioner import OrgDatabaseProvisioner

class DatabaseConnectionManager:
    """Enhanced with migration support."""

    def __init__(self, metadata_dsn: str, results_dsn_template: str):
        # ... existing code ...
        self.provisioner = OrgDatabaseProvisioner(
            admin_dsn=metadata_dsn.replace('/mad', '/postgres'),  # Admin connection
            results_dsn_template=results_dsn_template
        )

    async def _provision_org_database(self, org_id: str):
        """Use provisioner for database creation and migration."""
        success = await self.provisioner.provision_org_database(org_id)
        if not success:
            raise DatabaseProvisioningError(f"Failed to provision database for org {org_id}")

        # Continue with connection setup...
```

This comprehensive Alembic migration strategy provides:

1. **Dual-database support** with separate migration branches
2. **Automated org database provisioning** with proper schema migration
3. **Migration utilities** for common operations and consistent schema patterns
4. **Docker integration** for containerized deployments
5. **Testing strategies** for migration validation
6. **Production-ready patterns** for database lifecycle management

The strategy ensures that both shared metadata and per-organization databases evolve consistently while maintaining data isolation and migration safety.
