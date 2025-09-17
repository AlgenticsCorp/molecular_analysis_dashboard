"""Minimal tasks for smoke testing the worker."""

from __future__ import annotations

from .celery_app import celery_app


@celery_app.task(name="mad.ping")
def ping() -> str:
    """Return a simple ping response for health checks."""
    return "pong"
