# Docker Deployment and Scaling Guide

This guide provides a practical blueprint to run the Molecular Analysis Dashboard locally with Docker Compose and outlines how to scale services. It complements the architectural and workflow docs by focusing on deployability, operability, and horizontal scaling.

## Objectives
- Reproducible, one-command local environment
- Stateless API containers with horizontal scaling
- Background workers for long-running jobs (Celery)
- Externalized state: Postgres, Redis, and persistent volumes
- Health checks, structured logs, and graceful startup (migrations)

---

## Directory Structure

```
project-root/
├─ docker/
│  ├─ Dockerfile.api
│  ├─ Dockerfile.worker
│  └─ gunicorn_conf.py
├─ docker-compose.yml
├─ .env
└─ src/molecular_analysis_dashboard/
```

---

## .env (Environment Variables)
Create a `.env` file at the repo root (values are examples; change in real deployments):

```
# Core
ENV=development
SECRET_KEY=change-me
LOG_LEVEL=info

# API
HOST=0.0.0.0
PORT=8000
WEB_CONCURRENCY=2
UVICORN_WORKERS=2

# Database
POSTGRES_USER=mad
POSTGRES_PASSWORD=mad_password
POSTGRES_DB=mad
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Redis / Celery
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
CELERY_WORKER_CONCURRENCY=2
CELERY_PREFETCH_MULTIPLIER=1
CELERY_ACKS_LATE=true

# Files/Results storage (local volume by default)
RESULTS_DIR=/data/results
UPLOADS_DIR=/data/uploads
```

---

## docker-compose.yml (Services Topology)

Create a `docker-compose.yml` at the repo root:

```yaml
version: "3.9"

x-common-env: &common-env
  ENV: ${ENV}
  LOG_LEVEL: ${LOG_LEVEL}
  SECRET_KEY: ${SECRET_KEY}
  DATABASE_URL: ${DATABASE_URL}
  CELERY_BROKER_URL: ${CELERY_BROKER_URL}
  CELERY_RESULT_BACKEND: ${CELERY_RESULT_BACKEND}
  RESULTS_DIR: ${RESULTS_DIR}
  UPLOADS_DIR: ${UPLOADS_DIR}

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks: [appnet]

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks: [appnet]

  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    environment:
      <<: *common-env
      HOST: ${HOST}
      PORT: ${PORT}
      WEB_CONCURRENCY: ${WEB_CONCURRENCY}
      UVICORN_WORKERS: ${UVICORN_WORKERS}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - results:${RESULTS_DIR}
      - uploads:${UPLOADS_DIR}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 15s
      timeout: 5s
      retries: 5
    networks: [appnet]

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    environment:
      <<: *common-env
      CELERY_WORKER_CONCURRENCY: ${CELERY_WORKER_CONCURRENCY}
      CELERY_PREFETCH_MULTIPLIER: ${CELERY_PREFETCH_MULTIPLIER}
      CELERY_ACKS_LATE: ${CELERY_ACKS_LATE}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - results:${RESULTS_DIR}
      - uploads:${UPLOADS_DIR}
    networks: [appnet]

  migrate:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    environment:
      <<: *common-env
    depends_on:
      postgres:
        condition: service_healthy
    command: ["bash", "-lc", "alembic upgrade head"]
    restart: "no"
    networks: [appnet]

  flower:
    image: mher/flower:1.2.0
    environment:
      - FLOWER_PORT=5555
      - FLOWER_BASIC_AUTH=user:password
    command: ["flower", "--broker=${CELERY_BROKER_URL}"]
    ports:
      - "5555:5555"
    depends_on:
      redis:
        condition: service_healthy
    networks: [appnet]

volumes:
  pgdata:
  redisdata:
  results:
  uploads:

networks:
  appnet:
```

Notes:
- `api` is stateless and can be horizontally scaled. For local Compose: `docker compose up --scale api=2`.
- `worker` can be scaled independently: `docker compose up --scale worker=3`.
- `migrate` runs Alembic migrations once; run it manually when schema changes.

---

## docker/Dockerfile.api (Multi-stage, Non-root, Gunicorn/Uvicorn)

```Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps (curl for healthcheck, build tools as needed)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Optional: install AutoDock Vina if packaged in your base distro
# RUN apt-get update && apt-get install -y --no-install-recommends autodock-vina && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
# If using Poetry, install here; otherwise use pip
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Copy source (editable installs can be used instead during dev)
COPY src ./src

# Create non-root user
RUN useradd -m appuser
USER appuser

EXPOSE 8000

# Gunicorn config (uses Uvicorn workers)
# You can provide a docker/gunicorn_conf.py file to tune workers/timeouts
CMD ["bash", "-lc", \
     "gunicorn --config docker/gunicorn_conf.py \
      --workers=${WEB_CONCURRENCY:-2} \
      -k uvicorn.workers.UvicornWorker \
      'molecular_analysis_dashboard.presentation.api.main:app'"]
```

---

## docker/Dockerfile.worker (Celery Worker)

```Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY src ./src

RUN useradd -m appuser
USER appuser

CMD ["bash", "-lc", \
     "celery -A molecular_analysis_dashboard.infrastructure.celery_app.celery_app \
      worker --loglevel=${LOG_LEVEL:-info} \
      --concurrency=${CELERY_WORKER_CONCURRENCY:-2} \
      --prefetch-multiplier=${CELERY_PREFETCH_MULTIPLIER:-1}"]
```

---

## docker/gunicorn_conf.py (Example)

```python
import multiprocessing

bind = "0.0.0.0:8000"
workers = int(getattr(__import__('os'), 'environ').get('WEB_CONCURRENCY', multiprocessing.cpu_count()))
worker_class = "uvicorn.workers.UvicornWorker"
threads = 1
keepalive = 30
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = getattr(__import__('os'), 'environ').get('LOG_LEVEL', 'info')
```

---

## Health, Readiness, and Observability

- API should expose:
  - `GET /health` (liveness)
  - `GET /ready` (readiness: DB + broker checks)
- Structured logs (e.g., `structlog` or JSON logs) for API and workers
- Optional: metrics endpoint (Prometheus) and traces (OpenTelemetry)

---

## Scaling

- Horizontal scaling with Compose:
  - API: `docker compose up --scale api=3`
  - Workers: `docker compose up --scale worker=5`
- Ensure idempotency and retries in Celery tasks (use Tenacity or Celery retry policies)
- Set `CELERY_ACKS_LATE=true` and use durable queues; prefer `prefetch-multiplier=1` for fair scheduling

---

## Security & Production Notes

- Do not run processes as root (already enforced in Dockerfiles)
- Store secrets outside the image; prefer Docker/Swarm/K8s secrets over `.env` for production
- Enable TLS termination at a reverse proxy/load balancer (e.g., Nginx, Traefik) in front of API
- Backups for Postgres and mounted volumes
- Pin image versions and regularly rebuild to pick up security fixes

---

## Usage (Local)

```bash
# 1) Build images
docker compose build

# 2) Start infra (db/broker), run migrations, and start services
docker compose up -d postgres redis
# Wait for healthchecks, then run migrations
docker compose run --rm migrate
# Start app and worker
docker compose up -d api worker

# 3) Check health
curl -f http://localhost:8000/health

# 4) Scale
docker compose up -d --scale api=2 --scale worker=3

# 5) View Celery dashboard (Flower)
open http://localhost:5555
```

This deployment blueprint is intentionally minimal for local development and CI; for production consider Kubernetes manifests with HPA, PodDisruptionBudgets, and external managed Postgres/Redis.
