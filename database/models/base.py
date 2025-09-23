"""Database base configuration and utilities."""

import os
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy import MetaData, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )


class DatabaseConfig:
    """Database configuration settings."""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://mad:mad_password@localhost:5432/mad")
        self.results_template = os.getenv("RESULTS_DB_TEMPLATE", "postgresql+asyncpg://mad:mad_password@localhost:5432/mad_results_{org_id}")
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"

    def get_metadata_url(self) -> str:
        """Get metadata database URL."""
        return self.database_url

    def get_results_url(self, org_id: str) -> str:
        """Get results database URL for organization."""
        return self.results_template.format(org_id=org_id)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._metadata_engine = None
        self._metadata_session_factory = None
        self._results_engines: Dict[str, Any] = {}
        self._results_session_factories: Dict[str, Any] = {}

    @property
    def metadata_engine(self):
        """Get or create metadata database engine."""
        if self._metadata_engine is None:
            self._metadata_engine = create_async_engine(
                self.config.get_metadata_url(),
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.config.echo
            )
        return self._metadata_engine

    @property
    def metadata_session_factory(self):
        """Get or create metadata session factory."""
        if self._metadata_session_factory is None:
            self._metadata_session_factory = async_sessionmaker(
                self.metadata_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._metadata_session_factory

    def get_results_engine(self, org_id: str):
        """Get or create results database engine for organization."""
        if org_id not in self._results_engines:
            self._results_engines[org_id] = create_async_engine(
                self.config.get_results_url(org_id),
                pool_size=max(2, self.config.pool_size // 2),  # Smaller pool for results DBs
                max_overflow=self.config.max_overflow // 2,
                pool_timeout=self.config.pool_timeout,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.config.echo
            )
        return self._results_engines[org_id]

    def get_results_session_factory(self, org_id: str):
        """Get or create results session factory for organization."""
        if org_id not in self._results_session_factories:
            engine = self.get_results_engine(org_id)
            self._results_session_factories[org_id] = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._results_session_factories[org_id]

    async def get_metadata_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a session for the metadata database."""
        session_factory = self.metadata_session_factory
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_results_session(self, org_id: str) -> AsyncGenerator[AsyncSession, None]:
        """Get a session for an organization's results database."""
        session_factory = self.get_results_session_factory(org_id)
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_metadata_tables(self):
        """Create all metadata tables."""
        from .metadata import Base as MetadataBase
        async with self.metadata_engine.begin() as conn:
            await conn.run_sync(MetadataBase.metadata.create_all)

    async def create_results_tables(self, org_id: str):
        """Create all results tables for organization."""
        from .results import Base as ResultsBase
        engine = self.get_results_engine(org_id)
        async with engine.begin() as conn:
            await conn.run_sync(ResultsBase.metadata.create_all)

    async def close_all(self):
        """Close all database connections."""
        if self._metadata_engine:
            await self._metadata_engine.dispose()

        for engine in self._results_engines.values():
            await engine.dispose()

        self._results_engines.clear()
        self._results_session_factories.clear()


# Global database manager instance
db_manager = DatabaseManager()


# Dependency functions for FastAPI
async def get_metadata_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get metadata database session."""
    async for session in db_manager.get_metadata_session():
        yield session


async def get_results_session(org_id: str) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get results database session."""
    async for session in db_manager.get_results_session(org_id):
        yield session


# Utility functions
def get_database_url(db_type: str = "metadata", org_id: Optional[str] = None) -> str:
    """Get database URL for specified database type."""
    config = DatabaseConfig()

    if db_type == "metadata":
        return config.get_metadata_url()
    elif db_type == "results" and org_id:
        return config.get_results_url(org_id)
    else:
        raise ValueError(f"Invalid database type '{db_type}' or missing org_id")


async def init_database():
    """Initialize database connections."""
    # Just ensure the metadata engine is created
    _ = db_manager.metadata_engine


async def close_database():
    """Close all database connections."""
    await db_manager.close_all()
