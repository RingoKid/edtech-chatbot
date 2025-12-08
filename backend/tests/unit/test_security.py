"""
Unit tests for security utilities.
"""

import pytest
from datetime import datetime, timedelta
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "securepassword123"
    hashed = get_password_hash(password)

    # Should verify correct password
    assert verify_password(password, hashed) is True

    # Should reject wrong password
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    """Test access token creation and decoding."""
    data = {"sub": "user_123", "email": "test@example.com", "role": "USER"}
    token = create_access_token(data)

    # Should decode successfully
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user_123"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "USER"
    assert payload["type"] == "access"


def test_create_refresh_token():
    """Test refresh token creation and decoding."""
    data = {"sub": "user_123", "token_id": "abc-123"}
    token = create_refresh_token(data)

    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user_123"
    assert payload["token_id"] == "abc-123"
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    """Test decoding invalid token."""
    invalid_token = "invalid.token.here"
    payload = decode_token(invalid_token)

    assert payload is None


def test_decode_expired_token():
    """Test decoding expired token."""
    # Create token that expires immediately
    data = {"sub": "user_123"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))

    # Should return None for expired token
    payload = decode_token(token)
    assert payload is None
