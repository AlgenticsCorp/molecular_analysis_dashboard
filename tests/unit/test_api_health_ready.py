"""Unit tests for API health and readiness endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from molecular_analysis_dashboard.presentation.api.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"status": "ok"}
    assert "X-Request-ID" in resp.headers


def test_ready_endpoint_placeholder():
    resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "not_ready"
    assert "db" in data["checks"]
    assert "broker" in data["checks"]
