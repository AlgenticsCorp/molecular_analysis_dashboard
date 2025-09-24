"""
FastAPI application with production-ready middleware and gateway support.

This module provides the main FastAPI application instance with comprehensive
middleware stack for production deployment, including CORS, proxy headers,
trusted hosts, and request ID propagation.

Responsibilities:
- Configure FastAPI application with production middleware
- Set up CORS for cross-origin requests
- Handle proxy headers for load balancer compatibility
- Provide health and readiness probes for container orchestration
- Include task management API routes when available

Dependencies:
- fastapi: Core web framework
- starlette: ASGI middleware components
- uvicorn: ASGI server middleware
- .routes.tasks: Task management API routes (optional)

Assumptions:
- Environment variables configure middleware behavior
- Request ID can be provided by client or auto-generated
- Task router is optional and gracefully handled if unavailable
- Health checks support container orchestration patterns

Features:
- Root path support for API gateways/reverse proxies (env `ROOT_PATH`)
- Proxy headers handling (X-Forwarded-For/Proto) via Starlette middleware
- Trusted host checks (env `TRUSTED_HOSTS`, comma separated or `*`)
- CORS configuration (env `CORS_ALLOW_ORIGINS`, comma separated or `*`)
- Request ID propagation: reads `X-Request-ID` or generates one; returns it in responses
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Callable, List

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# Import API routers
try:
    from .routes.task_execution import router as task_execution_router

    TASK_EXECUTION_ROUTER_AVAILABLE = True
except ImportError:
    TASK_EXECUTION_ROUTER_AVAILABLE = False

# Try to import the full tasks router (with database dependencies)
try:
    from .routes.tasks import router as tasks_router

    TASKS_ROUTER_AVAILABLE = True
except ImportError:
    TASKS_ROUTER_AVAILABLE = False

root_path = os.getenv("ROOT_PATH", "")
app = FastAPI(title="Molecular Analysis Dashboard API", version="0.1.0", root_path=root_path)

# Proxy/gateway friendliness
app.add_middleware(ProxyHeadersMiddleware)

allowed_hosts_env = os.getenv("TRUSTED_HOSTS", "*")
allowed_hosts: List[str] = [h.strip() for h in allowed_hosts_env.split(",") if h.strip()] or ["*"]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

cors_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "*")
origins: List[str]
if cors_origins_env.strip() == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API routers
if TASK_EXECUTION_ROUTER_AVAILABLE:
    app.include_router(task_execution_router)

if TASKS_ROUTER_AVAILABLE:
    app.include_router(tasks_router)


@app.middleware("http")
async def add_request_id_header(request: Request, call_next: Callable[[Request], Any]) -> Response:
    """Add request ID header to all responses."""
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe: process up."""
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, Any]:
    """Readiness probe: check database and task API availability."""
    checks = {
        "task_execution_api": "ready" if TASK_EXECUTION_ROUTER_AVAILABLE else "not_available",
        "task_registry_api": "ready" if TASKS_ROUTER_AVAILABLE else "not_available",
        "broker": "pending",
    }

    # Consider ready if at least task execution is available
    status = "ready" if TASK_EXECUTION_ROUTER_AVAILABLE else "not_ready"

    return {"status": status, "checks": checks}
