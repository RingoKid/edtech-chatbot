"""
Integration tests for chat history API routes.
Tests GET /chat/history and GET /chat/{thread_id}/messages endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import unique_email


@pytest.fixture(scope="module")
def client():
    """Create test client. DynamoDB tables are managed by session-scoped fixture in conftest.py."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    """
    Create a test user and get auth headers.
    Returns auth headers for authenticated requests.
    """
    email = unique_email("chathistory")

    # Create test user
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "testpassword123",
            "full_name": "Chat History User"
        }
    )
    assert signup_response.status_code == 201

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "testpassword123"
        }
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestGetHistory:
    """Tests for GET /chat/history endpoint."""

    def test_requires_authentication(self, client):
        """
        Given: No authentication token
        When: GET /api/v1/chat/history
        Then: Returns 401 Unauthorized
        """
        response = client.get("/api/v1/chat/history")
        assert response.status_code == 401

    def test_returns_empty_list_for_new_user(self, client):
        """
        Given: A new user with no conversations
        When: GET /api/v1/chat/history
        Then: Returns empty conversation list
        """
        email = unique_email("newuser_history")

        # Create new user
        client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": "password123",
                "full_name": "New User"
            }
        )

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": email,
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/chat/history", headers=headers)

        assert response.status_code == 200
        assert response.json()["conversations"] == []

    def test_returns_conversation_list(self, client, auth_headers):
        """
        Given: User has created conversations via /chat/init
        When: GET /api/v1/chat/history
        Then: Returns list of conversation summaries
        """
        # Create some conversations
        init_response1 = client.get("/api/v1/chat/init", headers=auth_headers)
        assert init_response1.status_code == 200
        thread_id1 = init_response1.json()["thread_id"]

        init_response2 = client.get("/api/v1/chat/init", headers=auth_headers)
        assert init_response2.status_code == 200
        thread_id2 = init_response2.json()["thread_id"]

        # Get history
        response = client.get("/api/v1/chat/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert len(data["conversations"]) >= 2

        # Verify conversation structure
        thread_ids = [c["thread_id"] for c in data["conversations"]]
        assert thread_id1 in thread_ids
        assert thread_id2 in thread_ids

        # Verify fields
        for conv in data["conversations"]:
            assert "thread_id" in conv
            assert "title" in conv
            assert "created_at" in conv
            assert "updated_at" in conv

    def test_does_not_return_other_users_conversations(self, client, auth_headers):
        """
        Given: Multiple users with conversations
        When: GET /api/v1/chat/history
        Then: User only sees their own conversations
        """
        # Create conversation as first user
        init_response = client.get("/api/v1/chat/init", headers=auth_headers)
        first_user_thread = init_response.json()["thread_id"]

        # Create second user
        other_email = unique_email("otheruser_history")
        client.post(
            "/api/v1/auth/signup",
            json={
                "email": other_email,
                "password": "password123",
                "full_name": "Other User"
            }
        )

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": other_email,
                "password": "password123"
            }
        )
        other_token = login_response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Create conversation as second user
        other_init = client.get("/api/v1/chat/init", headers=other_headers)
        other_user_thread = other_init.json()["thread_id"]

        # Get second user's history
        response = client.get("/api/v1/chat/history", headers=other_headers)

        assert response.status_code == 200
        thread_ids = [c["thread_id"] for c in response.json()["conversations"]]

        # Should see own thread but not first user's
        assert other_user_thread in thread_ids
        assert first_user_thread not in thread_ids


class TestGetMessages:
    """Tests for GET /chat/{thread_id}/messages endpoint."""

    def test_requires_authentication(self, client):
        """
        Given: No authentication token
        When: GET /api/v1/chat/{thread_id}/messages
        Then: Returns 401 Unauthorized
        """
        response = client.get("/api/v1/chat/some-thread-id/messages")
        assert response.status_code == 401

    def test_returns_messages_for_own_thread(self, client, auth_headers):
        """
        Given: User owns a thread and has sent messages
        When: GET /api/v1/chat/{thread_id}/messages
        Then: Returns message history
        """
        # Create conversation
        init_response = client.get("/api/v1/chat/init", headers=auth_headers)
        thread_id = init_response.json()["thread_id"]

        # Send a message
        message_response = client.post(
            "/api/v1/chat/message",
            headers=auth_headers,
            json={
                "thread_id": thread_id,
                "message": "Hello, I want to practice handwriting"
            }
        )
        assert message_response.status_code == 200

        # Get messages
        response = client.get(
            f"/api/v1/chat/{thread_id}/messages",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == thread_id
        assert "messages" in data
        assert len(data["messages"]) > 0

        # Verify message structure
        for msg in data["messages"]:
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["user", "assistant"]

    def test_returns_403_for_other_users_thread(self, client, auth_headers):
        """
        Given: User tries to access another user's thread
        When: GET /api/v1/chat/{thread_id}/messages
        Then: Returns 403 Forbidden
        """
        # Create conversation as first user
        init_response = client.get("/api/v1/chat/init", headers=auth_headers)
        first_user_thread = init_response.json()["thread_id"]

        # Create second user
        other_email = unique_email("otheruser_messages")
        client.post(
            "/api/v1/auth/signup",
            json={
                "email": other_email,
                "password": "password123",
                "full_name": "Other User"
            }
        )

        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": other_email,
                "password": "password123"
            }
        )
        other_token = login_response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access first user's thread
        response = client.get(
            f"/api/v1/chat/{first_user_thread}/messages",
            headers=other_headers
        )

        assert response.status_code == 403
        assert "access" in response.json()["detail"].lower()

    def test_returns_403_for_nonexistent_thread(self, client, auth_headers):
        """
        Given: Thread does not exist
        When: GET /api/v1/chat/{thread_id}/messages
        Then: Returns 403 (not 404 to prevent enumeration)
        """
        response = client.get(
            "/api/v1/chat/nonexistent-thread-xyz/messages",
            headers=auth_headers
        )

        # Returns 403 to prevent thread ID enumeration
        assert response.status_code == 403


class TestChatInit:
    """Tests for authenticated chat initialization."""

    def test_init_requires_authentication(self, client):
        """
        Given: No authentication token
        When: GET /api/v1/chat/init
        Then: Returns 401 Unauthorized
        """
        response = client.get("/api/v1/chat/init")
        assert response.status_code == 401

    def test_init_creates_conversation_record(self, client, auth_headers):
        """
        Given: Authenticated user
        When: GET /api/v1/chat/init
        Then: Creates conversation and returns greeting
        """
        response = client.get("/api/v1/chat/init", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "thread_id" in data
        assert "reply" in data
        assert len(data["thread_id"]) > 0  # UUID format

        # Verify conversation appears in history
        history_response = client.get("/api/v1/chat/history", headers=auth_headers)
        thread_ids = [c["thread_id"] for c in history_response.json()["conversations"]]
        assert data["thread_id"] in thread_ids


class TestChatMessage:
    """Tests for authenticated chat messaging."""

    def test_message_requires_authentication(self, client):
        """
        Given: No authentication token
        When: POST /api/v1/chat/message
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            "/api/v1/chat/message",
            json={"message": "Hello"}
        )
        assert response.status_code == 401

    def test_message_updates_conversation_preview(self, client, auth_headers):
        """
        Given: Authenticated user with a conversation
        When: POST /api/v1/chat/message
        Then: Updates last_message_preview in conversation
        """
        # Create conversation
        init_response = client.get("/api/v1/chat/init", headers=auth_headers)
        thread_id = init_response.json()["thread_id"]

        # Send message
        client.post(
            "/api/v1/chat/message",
            headers=auth_headers,
            json={
                "thread_id": thread_id,
                "message": "I want to practice vocabulary"
            }
        )

        # Check history for updated preview
        history_response = client.get("/api/v1/chat/history", headers=auth_headers)
        conversations = history_response.json()["conversations"]

        # Find our conversation
        our_conv = next(
            (c for c in conversations if c["thread_id"] == thread_id),
            None
        )
        assert our_conv is not None
        assert our_conv["last_message_preview"] is not None
        assert len(our_conv["last_message_preview"]) > 0
