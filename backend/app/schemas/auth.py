"""
Pydantic schemas for authentication.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    """Schema for user signup request."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=1)
    role: str = Field(default="USER", pattern="^(USER|ADMIN)$")


class UserLogin(BaseModel):
    """Schema for user login request (alternative to OAuth2PasswordRequestForm)."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    """Schema for user response (public fields only)."""
    user_id: str
    email: EmailStr
    full_name: str
    role: str
    created_at: str


class UserInDB(User):
    """Schema for user data from database (includes password)."""
    hashed_password: str
