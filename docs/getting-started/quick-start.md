# Quick Start

Follow these steps to run the API locally with Docker:

1) Copy env and build
```bash
cp .env.example .env
docker compose build
```

2) Run Postgres and Redis, then migrations and API
```bash
docker compose up -d postgres redis
docker compose run --rm migrate
docker compose up -d api
```

3) Smoke test
```bash
curl -f http://localhost:8000/health
```

Next: try running the worker (even without tasks yet)
```bash
docker compose up -d worker
```
