"""
Authentication router for the FastAPI application.
Contains endpoints for user authentication, login, logout, and token management.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse, ErrorResponse
from app.services.user_service import create_user, verify_user_credentials
from app.utils.auth import create_access_token
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/auth/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    """
    Create a new user account.
    
    Args:
        request: Signup request containing name, email, and password
        
    Returns:
        TokenResponse with JWT token and user information
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    try:
        # Create user (will raise ValueError if email exists)
        user_data = create_user(
            name=request.name,
            email=request.email,
            password=request.password
        )
        
        # Generate JWT token
        token = create_access_token(data={"sub": user_data["id"]})
        
        # Parse created_at if it's a string
        created_at = None
        if user_data.get("created_at"):
            if isinstance(user_data["created_at"], str):
                try:
                    created_at = datetime.fromisoformat(user_data["created_at"].replace('Z', '+00:00'))
                except:
                    created_at = datetime.fromisoformat(user_data["created_at"])
            else:
                created_at = user_data["created_at"]
        
        # Return token and user info
        return TokenResponse(
            token=token,
            token_type="bearer",
            user=UserResponse(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data["name"],
                created_at=created_at
            )
        )
        
    except ValueError as e:
        # Email already exists or validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    Args:
        request: Login request containing email and password
        
    Returns:
        TokenResponse with JWT token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Verify credentials
    user_data = verify_user_credentials(request.email, request.password)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    token = create_access_token(data={"sub": user_data["id"]})
    
    # Parse created_at if it's a string
    created_at = None
    if user_data.get("created_at"):
        if isinstance(user_data["created_at"], str):
            try:
                created_at = datetime.fromisoformat(user_data["created_at"].replace('Z', '+00:00'))
            except:
                created_at = datetime.fromisoformat(user_data["created_at"])
        else:
            created_at = user_data["created_at"]
    
    # Return token and user info
    return TokenResponse(
        token=token,
        token_type="bearer",
        user=UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"],
            created_at=created_at
        )
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    This is a protected route that requires valid JWT token.
    
    Args:
        current_user: Current authenticated user (from middleware)
        
    Returns:
        UserResponse with user information
    """
    # Parse created_at if it's a string
    created_at = None
    if current_user.get("created_at"):
        if isinstance(current_user["created_at"], str):
            try:
                created_at = datetime.fromisoformat(current_user["created_at"].replace('Z', '+00:00'))
            except:
                created_at = datetime.fromisoformat(current_user["created_at"])
        else:
            created_at = current_user["created_at"]
    
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        created_at=created_at
    )


@router.get("/auth", tags=["Authentication"])
def get_auth_status():
    """
    Placeholder endpoint for authentication functionality.
    """
    return {"router": "auth", "status": "active", "message": "Authentication router is working"}
