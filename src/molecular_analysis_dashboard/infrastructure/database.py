"""Database configuration and session management.

This module provides database connectivity and session management for the application.
The actual database models and migrations are located in the /database directory
for easy external deployment and maintenance.
"""

import os
import sys
from typing import AsyncGenerator

# Add database models to path
database_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "database")
sys.path.insert(0, database_path)

try:
    from database.models import DatabaseManager, db_manager, get_database_url
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError as e:
    raise ImportError(
        f"Failed to import database models: {e}\n"
        "Make sure the database directory is properly set up and dependencies are installed."
    ) from e


async def init_databases() -> None:
    """Initialize database connections."""
    # Database manager is initialized automatically when imported
    pass


async def get_metadata_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get metadata database session."""
    async for session in db_manager.get_metadata_session():
        yield session


async def get_results_session(org_id: str) -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get results database session for organization."""
    async for session in db_manager.get_results_session(org_id):
        yield session


async def close_database() -> None:
    """Close all database connections."""
    await db_manager.close_all()


# Re-export for convenience
__all__ = [
    "DatabaseManager",
    "db_manager",
    "get_database_url",
    "init_databases",
    "get_metadata_session",
    "get_results_session",
    "close_database",
]
