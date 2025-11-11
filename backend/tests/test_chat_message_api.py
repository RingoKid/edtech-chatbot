"""
Unit tests for the chat message API endpoint.

Tests the /api/v1/chat/message endpoint to ensure:
1. API accepts valid requests and returns proper responses
2. Request/response structure matches the schema
3. Thread ID handling works correctly
4. Error handling is appropriate
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.chat import get_chat_service
from app.services.chat_service import ChatService


def get_test_chat_service() -> ChatService:
    """
    Creates a fresh ChatService instance for each test.
    This avoids event loop conflicts when the singleton is reused across tests.
    """
    return ChatService()


@pytest.fixture
def client():
    """
    Pytest fixture that creates a TestClient instance for testing.
    Overrides the get_chat_service dependency to provide fresh instances per test.

    Returns:
        TestClient: A test client wrapping the FastAPI app
    """
    app.dependency_overrides[get_chat_service] = get_test_chat_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_chat_message_missing_message_field(client):
    """
    Test that API returns an error when the required 'message' field is missing.
    """
    request_payload = {
        "thread_id": "test-thread-123"
        # Missing 'message' field
    }

    response = client.post("/api/v1/chat/message", json=request_payload)

    # Should return validation error (422)
    assert response.status_code == 422

