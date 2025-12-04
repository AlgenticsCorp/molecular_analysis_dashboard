"""Entrypoint for running the GNINA docking microservice with FastAPI."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI

from .routes import router

# Configure logging based on environment variable for consistency with other services.
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())

app = FastAPI(title="GNINA Docking Service", version="0.1.0")
app.include_router(router)


@app.get("/healthz", tags=["System"])
async def health_check() -> dict[str, str]:
    """Expose a lightweight health probe for orchestration."""

    return {"status": "ok"}
