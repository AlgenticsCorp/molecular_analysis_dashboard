# Configuration & Environment Reference

This document defines configuration knobs, environment variables, and where they are used. Keep this as the definitive reference for settings.

Conventions
- Config is injected via environment variables and parsed by a Pydantic Settings module (e.g., `infrastructure/config.py`).
- Values may be different in local/dev vs production. Defaults below target local Compose.
- All configuration classes provide type safety, validation, and documentation.

---

## Implementation Architecture

The application uses **Pydantic Settings** for type-safe configuration management with automatic environment variable parsing, validation, and clear documentation.

### Configuration Classes Structure

```python
# infrastructure/config.py - Main configuration module
from pydantic import BaseSettings, Field
from typing import Optional, List
from functools import lru_cache

class AppSettings(BaseSettings):
    """Core application configuration with validation."""

    # Environment
    env: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # API Server
    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, ge=1, le=65535, description="API server port")
    workers: int = Field(default=2, ge=1, le=32, description="Gunicorn worker count")

    # Security
    secret_key: str = Field(..., min_length=32, description="Secret key for JWT signing")
    access_token_expire_minutes: int = Field(default=30, ge=1, description="JWT token expiration")

    # API Gateway Integration
    root_path: str = Field(default="", description="Root path for reverse proxy")
    trusted_hosts: List[str] = Field(default=["*"], description="Trusted host list")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")

    class Config:
        env_file = ".env"
        case_sensitive = False

class DatabaseSettings(BaseSettings):
    """Database connection configuration with validation."""

    # Metadata Database (shared)
    database_url: str = Field(..., regex=r'^postgresql\+asyncpg://.*', description="Main metadata database URL")
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, le=100, description="Max pool overflow")

    # Results Database Template
    results_db_template: str = Field(
        default="postgresql+asyncpg://user:pass@host:5432/mad_results_{org_id}",
        description="Template for per-org results databases"
    )

    # Auto-provisioning
    auto_create_org_dbs: bool = Field(default=True, description="Auto-create org databases")

    @validator('results_db_template')
    def validate_template(cls, v):
        if '{org_id}' not in v:
            raise ValueError('results_db_template must contain {org_id} placeholder')
        return v

    class Config:
        env_file = ".env"
        env_prefix = "DB_"

# Singleton accessor functions
@lru_cache()
def get_app_settings() -> AppSettings:
    return AppSettings()

@lru_cache()
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()
```

### Usage in Application Code

```python
# Example usage in FastAPI app
from infrastructure.config import get_app_settings

settings = get_app_settings()
app = FastAPI(
    title="Molecular Analysis Dashboard",
    root_path=settings.root_path,
    debug=settings.debug
)
```

---

## Core Application Settings
- `ENV` (string): runtime environment (e.g., `development`, `staging`, `production`). Default: `development`.
- `DEBUG` (bool): enable debug mode. Default: `false`.
- `LOG_LEVEL` (string): `debug|info|warning|error`. Default: `info`.
- `SECRET_KEY` (string): JWT signing/crypto; required, minimum 32 characters.

## API Server Settings (FastAPI/Gunicorn)
- `HOST` (string): bind host. Default: `0.0.0.0`.
- `PORT` (int): bind port. Default: `8000`. Range: 1-65535.
- `WEB_CONCURRENCY` (int): Gunicorn workers. Default: `2`. Range: 1-32.
- `UVICORN_WORKERS` (int): per-worker threads (if used). Default: `2`.

## Database Configuration (PostgreSQL)
- `DB_DATABASE_URL` (string): SQLAlchemy DSN for metadata DB. Required. Must start with `postgresql+asyncpg://`.
- `DB_POOL_SIZE` (int): connection pool size. Default: `10`. Range: 1-100.
- `DB_MAX_OVERFLOW` (int): max pool overflow. Default: `20`. Range: 0-100.
- `DB_RESULTS_DB_TEMPLATE` (string): template for per-org databases. Must contain `{org_id}` placeholder.
- `DB_AUTO_CREATE_ORG_DBS` (bool): auto-provision org databases. Default: `true`.

## Task Queue Configuration (Celery/Redis)
- `CELERY_BROKER_URL` (string): message broker DSN. Default: `redis://redis:6379/0`.
- `CELERY_RESULT_BACKEND` (string): result backend DSN. Defaults to broker URL.
- `CELERY_WORKER_CONCURRENCY` (int): worker concurrency. Default: `2`. Range: 1-16.
- `CELERY_PREFETCH_MULTIPLIER` (int): fair scheduling setting. Default: `1`.
- `CELERY_TASK_ACKS_LATE` (bool): acknowledge after completion. Default: `true`.

## Storage Configuration
- `STORAGE_BACKEND` (string): storage type: `local`, `s3`, `minio`. Default: `local`.
- `STORAGE_UPLOADS_DIR` (string): local uploads directory. Default: `/data/uploads`.
- `STORAGE_RESULTS_DIR` (string): local results directory. Default: `/data/results`.
- `STORAGE_FILE_PATH_TEMPLATE` (string): path organization template. Default: `{org_id}/{job_id}/{artifact_type}/{filename}`.

### S3/MinIO Storage (when STORAGE_BACKEND=s3 or minio)
- `STORAGE_S3_ENDPOINT_URL` (string): S3 endpoint URL. Required for MinIO.
- `STORAGE_S3_ACCESS_KEY` (string): S3 access key. Required.
- `STORAGE_S3_SECRET_KEY` (string): S3 secret key. Required.
- `STORAGE_S3_BUCKET_NAME` (string): S3 bucket name. Default: `mad-artifacts`.
- `STORAGE_S3_REGION` (string): AWS region. Default: `us-east-1`.

## Docking Engine Configuration
- `DOCKING_ENABLED_ENGINES` (list): comma-separated enabled engines. Default: `vina,smina`.
- `DOCKING_EXECUTION_TIMEOUT` (int): max execution time in seconds. Default: `3600`.
- `DOCKING_MAX_CONCURRENT_JOBS` (int): max concurrent jobs. Default: `5`.
- `DOCKING_USE_CONTAINERS` (bool): run engines in containers. Default: `true`.
- `DOCKING_CONTAINER_MEMORY_LIMIT` (string): container memory limit. Default: `2G`.
- `DOCKING_CONTAINER_CPU_LIMIT` (string): container CPU limit. Default: `1.0`.

### Binary Paths (when DOCKING_USE_CONTAINERS=false)
- `DOCKING_VINA_EXECUTABLE` (string): AutoDock Vina binary path. Default: `/usr/local/bin/vina`.
- `DOCKING_SMINA_EXECUTABLE` (string): Smina binary path. Default: `/usr/local/bin/smina`.
- `DOCKING_GNINA_EXECUTABLE` (string): Gnina binary path. Default: `/usr/local/bin/gnina`.

## Security Configuration
- `JWT_ISSUER` (string): token issuer. Default: `mad.local`.
- `JWT_AUDIENCE` (string): token audience. Default: `mad`.
- `JWT_ACCESS_TTL_SECONDS` (int): access token lifetime. Default: `3600`.
- `JWT_REFRESH_TTL_SECONDS` (int): refresh token lifetime. Default: `1209600` (14 days).

## API Gateway Integration
- `ROOT_PATH` (string): path prefix for reverse proxy. Default: `""`.
- `TRUSTED_HOSTS` (string): comma-separated trusted hosts. Default: `*`.
- `CORS_ALLOW_ORIGINS` (string): comma-separated CORS origins. Default: `*`.

## Feature Flags (optional)
- `ENABLE_OPENAPI` (bool): expose `/docs` and `/openapi.json`. Default: `true` in dev.
- `ENABLE_METRICS` (bool): expose `/metrics` endpoint. Default: `false`.
- `ENABLE_DEBUG_LOGGING` (bool): enhanced debug logging. Default: `false`.

---

## Where Used (logical)
- `infrastructure/config.py`: Pydantic Settings class reads env vars.
- `docker-compose.yml`: wires env to services (`api`, `worker`, `migrate`).
- `docker/gunicorn_conf.py`: uses `WEB_CONCURRENCY`, `LOG_LEVEL`.
- Adapters (storage/db): read `STORAGE_BACKEND`, `DATABASE_URL`.
- Security module: uses `SECRET_KEY`, `JWT_*`.

---

## Enhanced Example `.env`

```bash
# Core Application
ENV=development
DEBUG=false
LOG_LEVEL=info
SECRET_KEY=your-very-secure-secret-key-at-least-32-characters-long

# API Server
HOST=0.0.0.0
PORT=8000
WEB_CONCURRENCY=2
UVICORN_WORKERS=2

# Database Configuration
DB_DATABASE_URL=postgresql+asyncpg://mad:mad_password@postgres:5432/mad
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_RESULTS_DB_TEMPLATE=postgresql+asyncpg://mad:mad_password@postgres:5432/mad_results_{org_id}
DB_AUTO_CREATE_ORG_DBS=true

# Celery/Redis Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_WORKER_CONCURRENCY=2
CELERY_PREFETCH_MULTIPLIER=1
CELERY_TASK_ACKS_LATE=true

# Storage Configuration
STORAGE_BACKEND=local
STORAGE_UPLOADS_DIR=/data/uploads
STORAGE_RESULTS_DIR=/data/results
STORAGE_FILE_PATH_TEMPLATE={org_id}/{job_id}/{artifact_type}/{filename}

# S3/MinIO Configuration (when STORAGE_BACKEND=s3 or minio)
# STORAGE_S3_ENDPOINT_URL=http://minio:9000
# STORAGE_S3_ACCESS_KEY=minioadmin
# STORAGE_S3_SECRET_KEY=minioadmin
# STORAGE_S3_BUCKET_NAME=mad-artifacts
# STORAGE_S3_REGION=us-east-1

# Docking Engine Configuration
DOCKING_ENABLED_ENGINES=vina,smina
DOCKING_EXECUTION_TIMEOUT=3600
DOCKING_MAX_CONCURRENT_JOBS=5
DOCKING_USE_CONTAINERS=true
DOCKING_CONTAINER_MEMORY_LIMIT=2G
DOCKING_CONTAINER_CPU_LIMIT=1.0

# Binary Paths (when DOCKING_USE_CONTAINERS=false)
# DOCKING_VINA_EXECUTABLE=/usr/local/bin/vina
# DOCKING_SMINA_EXECUTABLE=/usr/local/bin/smina
# DOCKING_GNINA_EXECUTABLE=/usr/local/bin/gnina

# Security
JWT_ISSUER=mad.local
JWT_AUDIENCE=mad
JWT_ACCESS_TTL_SECONDS=3600
JWT_REFRESH_TTL_SECONDS=1209600

# API Gateway Integration
ROOT_PATH=""
TRUSTED_HOSTS="*"
CORS_ALLOW_ORIGINS="*"

# Feature Flags
ENABLE_OPENAPI=true
ENABLE_METRICS=false
ENABLE_DEBUG_LOGGING=false

# Legacy Docker Compose Variables (for backward compatibility)
POSTGRES_USER=mad
POSTGRES_PASSWORD=mad_password
POSTGRES_DB=mad
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0
RESULTS_DIR=/data/results
UPLOADS_DIR=/data/uploads
```

## Configuration Validation

The Pydantic Settings classes provide automatic validation:

- **Type checking**: Ensures values are correct types (int, bool, string, etc.)
- **Range validation**: Validates numeric ranges (e.g., port 1-65535)
- **Format validation**: Checks string formats (e.g., database URLs)
- **Required fields**: Ensures critical settings are provided
- **Default values**: Provides sensible defaults for optional settings

Example validation errors:
- `PORT=99999` → ValidationError: Port must be between 1 and 65535
- `SECRET_KEY=short` → ValidationError: Secret key must be at least 32 characters
- `DB_DATABASE_URL=invalid://url` → ValidationError: Must be valid PostgreSQL URL
