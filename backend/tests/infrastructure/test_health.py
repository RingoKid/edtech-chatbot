"""
Tests for the health endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """
    Pytest fixture that creates a TestClient instance for testing.

    Returns:
        TestClient: A test client wrapping the FastAPI app
    """
    with TestClient(app) as c:
        yield c


def test_health_check_returns_ok(client):
    """
    Test that the health endpoint returns a 200 status code and correct response body.

    Args:
        client: The TestClient fixture
    """
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
