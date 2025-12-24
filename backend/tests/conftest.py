"""
Shared pytest fixtures and utilities for all tests.
"""
from app.schemas.auth import UserInDB


def get_test_user() -> UserInDB:
    """
    Mock user for bypassing authentication in tests.
    Returns a UserInDB instance (not a dict) to match production behavior.
    """
    return UserInDB(
        user_id="test-user-123",
        email="test@example.com",
        full_name="Test User",
        role="USER",
        created_at="2024-01-01T00:00:00Z",
        hashed_password="fake-hashed-password"
    )
