"""
Authentication schemas for request/response models.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class SignupRequest(BaseModel):
    """Schema for user signup request."""
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, max_length=100, description="User's password (min 6 characters)")


class LoginRequest(BaseModel):
    """Schema for user login request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: "UserResponse" = Field(..., description="User information")


class UserResponse(BaseModel):
    """Schema for user information response."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User's email")
    name: str = Field(..., description="User's name")
    created_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str = Field(..., description="Error message")


# Update forward references
TokenResponse.model_rebuild()

