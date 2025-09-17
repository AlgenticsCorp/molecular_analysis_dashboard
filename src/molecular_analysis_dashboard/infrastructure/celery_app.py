"""Celery application wiring for background tasks (Stage 4+)."""

from __future__ import annotations

import os

from celery import Celery


def _make_celery() -> Celery:
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    backend_url = os.getenv("CELERY_RESULT_BACKEND", broker_url)
    app = Celery(
        "mad",
        broker=broker_url,
        backend=backend_url,
        include=[
            "molecular_analysis_dashboard.infrastructure.tasks",
        ],
    )
    # Basic, safe defaults; can be overridden via env/worker flags
    acks_late = os.getenv("CELERY_ACKS_LATE", "true").lower() in {"1", "true", "yes", "on"}
    app.conf.update(
        task_acks_late=acks_late,
        worker_prefetch_multiplier=int(os.getenv("CELERY_PREFETCH_MULTIPLIER", "1")),
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
    return app


celery_app = _make_celery()
