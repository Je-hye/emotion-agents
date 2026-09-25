import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from api.main import app


def test_simulate_already_running():
    """두 번째 POST /api/simulate는 409를 반환한다."""
    from api.routes.ws import manager
    manager._running = True
    client = TestClient(app)
    response = client.post("/api/simulate", json={"ticks": 1})
    assert response.status_code == 409
    manager._running = False


def test_simulate_invalid_ticks():
    """ticks가 1 미만이면 422를 반환한다."""
    client = TestClient(app)
    response = client.post("/api/simulate", json={"ticks": 0})
    assert response.status_code == 422
