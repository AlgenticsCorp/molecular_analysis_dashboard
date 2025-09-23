"""Alembic environment configuration with multi-database support."""

import asyncio
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Add database models to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.metadata import Base as MetadataBase
from models.results import Base as ResultsBase

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url_for_branch(branch_name: str) -> str:
    """Get database URL for specific migration branch."""
    # Check environment variable first
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        if branch_name == "metadata":
            return env_url
        elif branch_name == "results":
            # Replace database name for results template
            base_db = os.getenv("POSTGRES_DB", "mad")
            return env_url.replace(f"/{base_db}", f"/{base_db}_results_template")

    # Fall back to config file
    return config.get_section_option(branch_name, "sqlalchemy.url")


def get_metadata_for_branch(branch_name: str):
    """Get SQLAlchemy metadata for specific branch."""
    if branch_name == "metadata":
        return MetadataBase.metadata
    elif branch_name == "results":
        return ResultsBase.metadata
    else:
        raise ValueError(f"Unknown branch: {branch_name}")


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    branch_name = os.environ.get('ALEMBIC_BRANCH', 'metadata')
    url = get_url_for_branch(branch_name)

    context.configure(
        url=url,
        target_metadata=get_metadata_for_branch(branch_name),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=config.get_section_option(branch_name, "version_table", "alembic_version"),
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations with database connection."""
    branch_name = os.environ.get('ALEMBIC_BRANCH', 'metadata')

    context.configure(
        connection=connection,
        target_metadata=get_metadata_for_branch(branch_name),
        version_table=config.get_section_option(branch_name, "version_table", "alembic_version"),
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
