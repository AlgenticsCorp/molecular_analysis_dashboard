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

# Import the docking router
try:
    from .routes.docking import router as docking_router

    DOCKING_ROUTER_AVAILABLE = True
except ImportError:
    DOCKING_ROUTER_AVAILABLE = False

# Import the folding router
try:
    from .routes.folding import router as folding_router

    FOLDING_ROUTER_AVAILABLE = True
except ImportError:
    FOLDING_ROUTER_AVAILABLE = False

# Import the unified NeuroSnap router
try:
    from .routes.neurosnap_unified import router as neurosnap_unified_router

    NEUROSNAP_UNIFIED_ROUTER_AVAILABLE = True
except ImportError:
    NEUROSNAP_UNIFIED_ROUTER_AVAILABLE = False

# Import the molecular dynamics router
try:
    from .routes.molecular_dynamics import router as molecular_dynamics_router

    MOLECULAR_DYNAMICS_ROUTER_AVAILABLE = True
except ImportError:
    MOLECULAR_DYNAMICS_ROUTER_AVAILABLE = False

# Import the task framework router
try:
    from .routes.task_framework import task_framework_router

    TASK_FRAMEWORK_ROUTER_AVAILABLE = True
except ImportError:
    TASK_FRAMEWORK_ROUTER_AVAILABLE = False

# Import the unified tasks router
try:
    from .routes.unified_tasks import router as unified_tasks_router

    UNIFIED_TASKS_ROUTER_AVAILABLE = True
except ImportError:
    UNIFIED_TASKS_ROUTER_AVAILABLE = False

# Import the files router
try:
    from .routes.files import router as files_router

    FILES_ROUTER_AVAILABLE = True
except ImportError:
    FILES_ROUTER_AVAILABLE = False

root_path = os.getenv("ROOT_PATH", "")

# Define comprehensive tags metadata for Swagger UI organization
tags_metadata = [
    # Service Categories (Primary Organization)
    {
        "name": "🧬 Structure Folding",
        "description": "Protein structure prediction services from multiple providers"
    },
    {
        "name": "🔬 Molecular Dynamics",
        "description": "Molecular dynamics simulation and optimization services"
    },
    {
        "name": "🎯 Molecular Docking",
        "description": "Protein-ligand binding prediction and analysis services"
    },
    
    # Provider Categories (Secondary Organization)
    {
        "name": "☁️ NeuroSnap Cloud",
        "description": "Cloud-based computational services via NeuroSnap API"
    },
    {
        "name": "🏠 Domestic Services", 
        "description": "Local computational tools and services (Future)"
    },
    
    # Cross-cutting Services
    {
        "name": "⚙️ Job Management",
        "description": "Universal job tracking, status monitoring, and result retrieval",
    },
    {
        "name": "🔄 Task Framework",
        "description": "Generic task execution system for all computational services",
    },
    {
        "name": "File Management",
        "description": "Upload, manage, and organize molecular structure files",
    },
    {
        "name": "System Health",
        "description": "Health checks, readiness probes, and system status monitoring",
    }
]

app = FastAPI(
    title="Molecular Analysis Dashboard API", 
    version="0.1.0", 
    root_path=root_path,
    description="""**Comprehensive molecular analysis platform** with multi-provider support.
    
🧬 **Structure Folding**: Protein structure prediction (IntelliFold, Boltz-2)
🔬 **Molecular Dynamics**: AMBER relaxation and optimization  
🎯 **Molecular Docking**: GNINA neural network-guided binding analysis
⚙️ **Job Management**: Universal tracking across all services
🔄 **Task Framework**: Generic computational workflow interface
    
Supports both **☁️ NeuroSnap Cloud** services and future **🏠 Domestic Services**.
    """,
    openapi_tags=tags_metadata,
    contact={
        "name": "Molecular Analysis Dashboard Team",
        "email": "support@molecular-analysis.com",
    },
    license_info={
        "name": "MIT",
    },
)

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

if DOCKING_ROUTER_AVAILABLE:
    app.include_router(docking_router)

if FOLDING_ROUTER_AVAILABLE:
    app.include_router(folding_router)

if NEUROSNAP_UNIFIED_ROUTER_AVAILABLE:
    app.include_router(neurosnap_unified_router)

if MOLECULAR_DYNAMICS_ROUTER_AVAILABLE:
    app.include_router(molecular_dynamics_router)

if TASK_FRAMEWORK_ROUTER_AVAILABLE:
    app.include_router(task_framework_router)

if UNIFIED_TASKS_ROUTER_AVAILABLE:
    app.include_router(unified_tasks_router)

if FILES_ROUTER_AVAILABLE:
    app.include_router(files_router)


@app.middleware("http")
async def add_request_id_header(request: Request, call_next: Callable[[Request], Any]) -> Response:
    """Add request ID header to all responses."""
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


@app.get("/health", tags=["System Health"])
def health() -> dict[str, str]:
    """Liveness probe: Basic application health check.
    
    Returns a simple health status indicating the application is running.
    Used by container orchestration systems (Kubernetes, Docker Swarm) 
    to determine if the container should be restarted.
    
    Returns:
        dict: Health status with timestamp
    """
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "molecular-analysis-dashboard"
    }


@app.get("/ready", tags=["System Health"])
def ready() -> dict[str, Any]:
    """Readiness probe: Comprehensive service availability check.
    
    Checks availability of all computational services and dependencies.
    Used by load balancers and container orchestration to determine
    if the application is ready to receive traffic.
    
    Returns:
        dict: Detailed readiness status with service breakdown
    """
    from datetime import datetime
    
    # Check service availability
    service_checks = {
        "task_execution_api": "ready" if TASK_EXECUTION_ROUTER_AVAILABLE else "not_available",
        "task_registry_api": "ready" if TASKS_ROUTER_AVAILABLE else "not_available", 
        "docking_services": "ready" if DOCKING_ROUTER_AVAILABLE else "not_available",
        "folding_services": "ready" if FOLDING_ROUTER_AVAILABLE else "not_available",
        "dynamics_services": "ready" if MOLECULAR_DYNAMICS_ROUTER_AVAILABLE else "not_available",
        "neurosnap_unified": "ready" if NEUROSNAP_UNIFIED_ROUTER_AVAILABLE else "not_available",
        "task_framework": "ready" if TASK_FRAMEWORK_ROUTER_AVAILABLE else "not_available",
        "file_management": "ready" if FILES_ROUTER_AVAILABLE else "not_available",
    }
    
    # Overall readiness assessment
    ready_services = sum(1 for status in service_checks.values() if status == "ready")
    total_services = len(service_checks)
    
    overall_status = "ready" if ready_services >= 3 else "not_ready"  # At least 3 services needed
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services_ready": f"{ready_services}/{total_services}",
        "service_details": service_checks,
        "molecular_analysis_capabilities": {
            "structure_folding": service_checks["folding_services"] == "ready",
            "molecular_dynamics": service_checks["dynamics_services"] == "ready", 
            "molecular_docking": service_checks["docking_services"] == "ready",
            "job_management": service_checks["neurosnap_unified"] == "ready",
            "task_framework": service_checks["task_framework"] == "ready",
            "task_execution_api": service_checks["task_execution_api"] == "ready",
            "file_management": service_checks["file_management"] == "ready",
        }
    }
