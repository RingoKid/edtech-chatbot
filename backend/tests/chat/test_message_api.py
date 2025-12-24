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
from app.dependencies.auth import get_current_user
from tests.conftest import get_test_user


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
    Overrides get_current_user to bypass authentication.

    Returns:
        TestClient: A test client wrapping the FastAPI app
    """
    app.dependency_overrides[get_chat_service] = get_test_chat_service
    app.dependency_overrides[get_current_user] = get_test_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_chat_message_with_new_thread(client):
    """
    Test sending a message without a thread_id (new conversation).

    The API should:
    - Accept the message
    - Generate a new thread_id
    - Return a valid response with thread_id and reply
    """
    request_payload = {
        "message": "Hello, I need help with lesson planning"
    }

    response = client.post("/api/v1/chat/message", json=request_payload)

    # Check status code
    assert response.status_code == 200

    # Check response structure
    data = response.json()
    assert "thread_id" in data
    assert "reply" in data

    # Verify thread_id was generated
    assert data["thread_id"] is not None
    assert len(data["thread_id"]) > 0

    # Verify reply is not empty
    assert data["reply"] is not None
    assert len(data["reply"]) > 0


def test_chat_message_with_existing_thread(client):
    """
    Test sending a message with an existing thread_id (continuing conversation).

    The API should:
    - Accept the message with thread_id
    - Return the same thread_id in response
    - Provide a contextually appropriate reply
    """
    # First message to create a thread
    first_request = {
        "message": "Hello"
    }
    first_response = client.post("/api/v1/chat/message", json=first_request)
    assert first_response.status_code == 200
    thread_id = first_response.json()["thread_id"]

    # Second message using the same thread
    second_request = {
        "message": "I want to work on handwriting",
        "thread_id": thread_id
    }
    second_response = client.post("/api/v1/chat/message", json=second_request)

    # Check status code
    assert second_response.status_code == 200

    # Check that the same thread_id is returned
    data = second_response.json()
    assert data["thread_id"] == thread_id

    # Verify reply exists
    assert data["reply"] is not None
    assert len(data["reply"]) > 0


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


def test_chat_message_empty_message(client):
    """
    Test that API handles empty message string appropriately.
    """
    request_payload = {
        "message": ""
    }

    response = client.post("/api/v1/chat/message", json=request_payload)

    # Should still accept the request (200) but may handle it differently
    # The service layer can decide how to handle empty messages
    assert response.status_code in [200, 400, 422]


def test_chat_message_response_schema(client):
    """
    Test that the response adheres to the ChatMessageResponse schema.

    Response should have:
    - thread_id (string)
    - reply (string)
    """
    request_payload = {
        "message": "Tell me about vocabulary lessons"
    }

    response = client.post("/api/v1/chat/message", json=request_payload)

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields exist
    assert "thread_id" in data
    assert "reply" in data

    # Verify field types
    assert isinstance(data["thread_id"], str)
    assert isinstance(data["reply"], str)

    # Verify no extra fields (strict schema)
    assert set(data.keys()) == {"thread_id", "reply"}


def test_chat_message_with_custom_thread_id(client):
    """
    Test that API accepts and uses a custom thread_id provided by the client.
    """
    custom_thread_id = "custom-test-thread-456"

    request_payload = {
        "message": "Hello with custom thread",
        "thread_id": custom_thread_id
    }

    response = client.post("/api/v1/chat/message", json=request_payload)

    assert response.status_code == 200
    data = response.json()

    # Verify the custom thread_id is used
    assert data["thread_id"] == custom_thread_id


def test_chat_message_handles_long_message(client):
    """
    Test that API can handle longer message content.
    """
    long_message = "I need help planning a lesson. " * 50  # Create a longer message

    request_payload = {
        "message": long_message
    }

    response = client.post("/api/v1/chat/message", json=request_payload)

    assert response.status_code == 200
    data = response.json()
    assert "thread_id" in data
    assert "reply" in data


def test_chat_message_special_characters(client):
    """
    Test that API handles messages with special characters and unicode.
    """
    request_payload = {
        "message": "Hello! How do I teach émojis 😊 and symbols like @#$%?"
    }

    response = client.post("/api/v1/chat/message", json=request_payload)

    assert response.status_code == 200
    data = response.json()
    assert "thread_id" in data
    assert "reply" in data

