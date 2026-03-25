"""
Authentication routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import uuid
from app.schemas.auth import UserCreate, User, Token
from app.services.auth_service import AuthService
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.dependencies.auth import get_current_user
from app.schemas.auth import UserInDB
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    """
    Register a new user.

    - **email**: Valid email address (must be unique)
    - **password**: Minimum 8 characters
    - **full_name**: User's full name
    - **role**: USER or ADMIN (defaults to USER)

    Returns user profile (without password).
    """
    auth_service = AuthService()

    try:
        user = await auth_service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

    # Return user without password
    return User(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        created_at=user.created_at
    )


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible login endpoint.

    Authenticates user and returns access token.
    Sets refresh token as httpOnly cookie.

    **Note:** OAuth2 spec uses "username" field, but we accept email.
    """
    auth_service = AuthService()

    # OAuth2 spec uses "username", but we use email
    user = await auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    token_id = str(uuid.uuid4())
    access_token = create_access_token(
        data={"sub": user.user_id, "email": user.email, "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.user_id, "token_id": token_id}
    )

    # Store refresh token in DynamoDB
    client_host = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown")

    await auth_service.store_refresh_token(
        user_id=user.user_id,
        token_id=token_id,
        expires_in_days=settings.refresh_token_expire_days,
        device=user_agent,
        ip_address=client_host
    )

    # Set httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60  # seconds
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    response: Response,
    refresh_token: str = Cookie(None)
):
    """
    Get new access token using refresh token from httpOnly cookie.

    Implements refresh token rotation (returns new refresh token).
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided"
        )

    # Decode refresh token
    payload = decode_token(refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    token_id = payload.get("token_id")

    # Verify user exists and token is not revoked
    auth_service = AuthService()
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not await auth_service.is_refresh_token_valid(user_id, token_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired"
        )

    # Create new tokens (token rotation)
    new_token_id = str(uuid.uuid4())
    access_token = create_access_token(
        data={"sub": user.user_id, "email": user.email, "role": user.role}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": user.user_id, "token_id": new_token_id}
    )

    # Revoke old refresh token, store new one
    await auth_service.revoke_refresh_token(user_id, token_id)
    await auth_service.store_refresh_token(
        user_id=user.user_id,
        token_id=new_token_id,
        expires_in_days=settings.refresh_token_expire_days
    )

    # Set new httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str = Cookie(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Logout current user by revoking refresh token.
    Clears httpOnly cookie.
    """
    auth_service = AuthService()

    if refresh_token:
        payload = decode_token(refresh_token)
        if payload and payload.get("token_id"):
            token_id = payload["token_id"]
            await auth_service.revoke_refresh_token(current_user.user_id, token_id)

    # Clear cookie
    response.delete_cookie(key="refresh_token")

    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all_devices(current_user: UserInDB = Depends(get_current_user)):
    """
    Logout from all devices by revoking all refresh tokens.
    Useful after password change or security concern.
    """
    auth_service = AuthService()
    count = await auth_service.revoke_all_refresh_tokens(current_user.user_id)

    return {"message": f"Logged out from {count} device(s)"}


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    Requires valid JWT token in Authorization header.
    """
    return User(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        created_at=current_user.created_at
    )
