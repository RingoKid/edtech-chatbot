"""
Integration tests for auth routes.
Uses DynamoDB Local container for testing.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import unique_email


@pytest.fixture(scope="module")
def client():
    """Create test client. DynamoDB tables are managed by session-scoped fixture in conftest.py."""
    return TestClient(app)


def test_signup_success(client):
    """
    Given: Valid user data
    When: POST /api/v1/auth/signup
    Then: Returns 201 with user profile
    """
    email = unique_email("newuser")
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "full_name": "New User",
            "role": "USER"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == "New User"
    assert data["role"] == "USER"
    assert "user_id" in data
    assert "hashed_password" not in data  # Should not expose password


def test_signup_duplicate_email(client):
    """
    Given: User already exists with email
    When: POST /api/v1/auth/signup with same email
    Then: Returns 409 Conflict
    """
    email = unique_email("duplicate")

    # First signup
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "full_name": "First User"
        }
    )

    # Second signup with same email
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "password456",
            "full_name": "Second User"
        }
    )

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_login_success(client):
    """
    Given: User exists with correct credentials
    When: POST /api/v1/auth/login
    Then: Returns 200 with access_token and sets refresh_token cookie
    """
    email = unique_email("loginuser")

    # Create user first
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Login User"
        }
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={  # OAuth2 uses form data, not JSON
            "username": email,
            "password": "password123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Check cookie is set
    assert "refresh_token" in response.cookies


def test_login_wrong_password(client):
    """
    Given: User exists
    When: POST /api/v1/auth/login with wrong password
    Then: Returns 401 Unauthorized
    """
    email = unique_email("testuser")

    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Test User"
        }
    )

    # Login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_protected_route_without_token(client):
    """
    Given: No authentication token
    When: GET /api/v1/auth/me (protected route)
    Then: Returns 401 Unauthorized
    """
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_protected_route_with_valid_token(client):
    """
    Given: Valid access token
    When: GET /api/v1/auth/me
    Then: Returns 200 with user info
    """
    email = unique_email("authuser")

    # Signup and login
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Auth User"
        }
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "password123"
        }
    )
    access_token = login_response.json()["access_token"]

    # Access protected route
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == "Auth User"


def test_token_refresh(client):
    """
    Given: Valid refresh token in cookie
    When: POST /api/v1/auth/refresh
    Then: Returns 200 with new access_token and new refresh_token cookie
    """
    email = unique_email("refreshuser")

    # Signup and login
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Refresh User"
        }
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "password123"
        }
    )

    # Refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        cookies=login_response.cookies
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in response.cookies


def test_logout(client):
    """
    Given: Authenticated user
    When: POST /api/v1/auth/logout
    Then: Returns 200 and clears refresh_token cookie
    And: Refresh token is revoked in database
    """
    email = unique_email("logoutuser")

    # Signup and login
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Logout User"
        }
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "password123"
        }
    )
    access_token = login_response.json()["access_token"]

    # Logout
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies=login_response.cookies
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"

    # Try to refresh with old token (should fail)
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        cookies=login_response.cookies
    )
    assert refresh_response.status_code == 401
