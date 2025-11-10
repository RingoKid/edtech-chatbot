"""
FastAPI authentication dependencies.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Callable
from app.core.security import decode_token
from app.services.auth_service import AuthService
from app.schemas.auth import UserInDB

# OAuth2 scheme - FastAPI extracts token from Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Dependency to get current authenticated user from JWT token.

    FastAPI automatically:
    1. Extracts token from Authorization header
    2. Calls this function
    3. Injects user into route handler

    Args:
        token: JWT access token from Authorization header

    Returns:
        UserInDB object for authenticated user

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # Verify token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    auth_service = AuthService()
    user = auth_service.get_user_by_id(user_id)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Dependency to ensure user is active.
    Can add additional checks here (e.g., is_active, email_verified).

    Currently just passes through, but provides extension point.
    """
    # Future: Add is_active check
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_role: str) -> Callable:
    """
    Factory function to create role-checking dependency.

    Args:
        required_role: Required role (e.g., "ADMIN")

    Returns:
        Dependency function that checks user role

    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_role("ADMIN"))])
        async def list_all_users():
            ...
    """
    async def role_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    return role_checker


# Convenience dependency for admin-only routes
require_admin = require_role("ADMIN")
