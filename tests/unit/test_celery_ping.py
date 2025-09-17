"""Unit tests for Celery wiring and the ping task."""

from __future__ import annotations

from molecular_analysis_dashboard.infrastructure.celery_app import celery_app
from molecular_analysis_dashboard.infrastructure.tasks import ping


def test_ping_task_registered():
    assert "mad.ping" in celery_app.tasks


def test_ping_task_direct_call():
    # Direct call without broker to validate function behavior
    assert ping() == "pong"
