# Feature Spec: JWT Authentication System with httpOnly Cookies

**Status:** Ready for Implementation
**Version:** 1.0
**Last Updated:** 2025-01-09

---

## Overview

This spec implements a production-grade JWT authentication system for the EdTech Chatbot backend. The system supports email/password authentication with role-based access control (ADMIN, USER), secure token management using httpOnly cookies, and token revocation for logout functionality.

**Problem:** The application currently has no authentication. All API endpoints are publicly accessible, and there's no way to identify users or associate conversations with specific users.

**Solution:** Implement JWT-based authentication with:

- Access tokens (30 min, stateless, stored in memory on frontend)
- Refresh tokens (7 days, stored in DynamoDB for revocation, sent as httpOnly cookies)
- Global authentication dependency at router level (no need to inject auth on every route)
- Role-based access control (ADMIN, USER)

---

## Architecture Decisions

### Decision 1: httpOnly Cookies for Refresh Tokens

**Rationale:**

- XSS-proof (JavaScript cannot access cookie)
- CSRF mitigated with SameSite=lax flag
- More secure than localStorage for long-lived tokens

### Decision 2: Two-Token System (Access + Refresh)

**Rationale:**

- Short-lived access tokens (30 min) limit attack window if stolen
- Long-lived refresh tokens (7 days) provide convenience without re-login
- Refresh tokens stored in DynamoDB enable revocation (logout, logout all devices)

### Decision 3: Two Separate DynamoDB Tables

**Rationale:**

- `EdTechChatbotTable-{env}`: Users, threads, refresh tokens (application data)
- `EdTechChatbotCheckpoints-{env}`: LangGraph checkpoints (separate lifecycle)
- Clear separation of concerns, independent scaling

### Decision 4: Global Auth Dependency at Router Level

**Rationale:**

- All routes under `/api/v1/` (except `/api/v1/auth/*`) require authentication by default
- Cleaner code (no need to add `Depends(get_current_user)` to every route)
- Works with FastAPI's dependency injection and Swagger UI

### Decision 5: User ID in JWT Token Payload

**Rationale:**

- Stateless authentication (no database lookup on every request)
- Fast (decode token → extract user_id → use immediately)
- Only lookup database when need fresh user data or token revocation check

---

## Data Schema

### DynamoDB Table: `EdTechChatbotTable-{env}`

**Primary Key:**

- `PK` (String): Partition key
- `SK` (String): Sort key

**Global Secondary Index (GSI1) - Email Lookup:**

- `GSI1PK` (String): Partition key for GSI
- `GSI1SK` (String): Sort key for GSI

**TTL Configuration:**

- Enable TTL on `expires_at` attribute (DynamoDB auto-deletes expired items)

#### Item Types

**1. User Profile**

```json
{
  "PK": "USER#user_123",
  "SK": "PROFILE",
  "GSI1PK": "EMAIL#teacher@school.edu",
  "GSI1SK": "USER#user_123",
  "user_id": "user_123",
  "email": "teacher@school.edu",
  "hashed_password": "$2b$12$KIXl234...",
  "full_name": "Jane Doe",
  "role": "USER",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

**2. Refresh Token (for revocation)**

```json
{
  "PK": "USER#user_123",
  "SK": "REFRESH_TOKEN#abc-def-123",
  "token_id": "abc-def-123",
  "device": "Chrome on Mac",
  "ip_address": "192.168.1.1",
  "created_at": "2024-01-15T10:00:00Z",
  "expires_at": 1705334400
}
```

**Note:** `expires_at` is Unix timestamp for DynamoDB TTL (auto-delete after 7 days)

**3. Thread Metadata (existing, no changes)**

```json
{
  "PK": "USER#user_123",
  "SK": "THREAD#thread_abc",
  "thread_id": "user_123_abc-def-ghi",
  "thread_name": "Handwriting Lesson - Letter A",
  "task_type": "Handwriting",
  "created_at": "2024-01-15T14:20:00Z",
  "last_message_at": "2024-01-15T14:25:00Z",
  "message_count": 12
}
```

---

## File Structure

```
backend/
├── app/
│   ├── core/
│   │   └── security.py              # NEW: JWT creation, password hashing
│   ├── services/
│   │   └── auth_service.py          # NEW: Auth business logic (DynamoDB)
│   ├── dependencies/
│   │   └── auth.py                  # NEW: FastAPI auth dependencies
│   ├── routers/
│   │   ├── auth.py                  # NEW: Auth routes (login, signup, etc.)
│   │   └── chat.py                  # EXISTING: Will be protected
│   ├── schemas/
│   │   └── auth.py                  # NEW: Pydantic models for auth
│   ├── utils/
│   │   └── thread.py                # NEW: Thread ID generation utilities
│   ├── config.py                    # UPDATE: Add auth config fields
│   ├── database.py                  # EXISTING: Already has DynamoDB utilities
│   └── main.py                      # UPDATE: Add auth router, global dependency
├── scripts/
│   └── init_db.py                   # UPDATE: Add GSI1 creation
├── tests/
│   ├── unit/
│   │   ├── test_security.py         # NEW: Test password hashing, JWT
│   │   └── test_auth_service.py     # NEW: Test auth service logic
│   └── integration/
│       └── test_auth_routes.py      # NEW: Test API endpoints
├── requirements.txt                 # UPDATE: Add new dependencies
├── .env.local                       # UPDATE: Add SECRET_KEY, auth config
└── .env.sandbox                     # UPDATE: Add SECRET_KEY, auth config
```

---

## Dependencies

### Add to `requirements.txt`:

```txt
# Authentication
python-jose[cryptography]>=3.3.0    # JWT token creation/validation
passlib[bcrypt]>=1.7.4              # Password hashing with bcrypt
python-multipart>=0.0.6             # Form data parsing for OAuth2

# Testing (if not already present)
pytest>=7.4.0
pytest-asyncio>=0.21.0
moto>=4.2.0                         # Mock AWS services for testing
```

### Installation:

```bash
# Install dependencies (Docker will pick up from requirements.txt on rebuild)
pip install -r requirements.txt

# Or add individually during development
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

**Note:** After updating `requirements.txt`, rebuild Docker container to apply changes.

---

## Configuration Changes

### Update `app/config.py`

Add these fields to the `Settings` class:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Authentication & JWT
    secret_key: SecretStr = Field(..., alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # CORS
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    @property
    def checkpoint_table_name(self) -> str:
        """Generate checkpoint table name based on environment."""
        base_name = "EdTechChatbotCheckpoints"
        if self.app_env == AppEnv.LOCAL:
            return f"{base_name}-local"
        elif self.app_env == AppEnv.SANDBOX:
            return f"{base_name}-sandbox"
        else:
            return f"{base_name}-prod"
```

### Update `.env.local`

```bash
# Generate SECRET_KEY with: openssl rand -hex 32
SECRET_KEY=8f3e9c2a1b4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
FRONTEND_URL=http://localhost:3000
```

### Update `.env.sandbox`

```bash
# Use a DIFFERENT SECRET_KEY for sandbox!
SECRET_KEY=<generate-another-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
FRONTEND_URL=<sandbox-frontend-url>  # To be provided later
```

**IMPORTANT:**

- Generate separate SECRET_KEYs for each environment
- Never commit .env files to git (should be in .gitignore)
- Command to generate: `openssl rand -hex 32`

---

## Implementation Guide

### Step 0: Setup (Generate SECRET_KEY)

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Add to .env.local and .env.sandbox (different keys!)
echo "SECRET_KEY=<generated-key>" >> .env.local
echo "SECRET_KEY=<different-generated-key>" >> .env.sandbox

# Add other auth config
echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> .env.local
echo "REFRESH_TOKEN_EXPIRE_DAYS=7" >> .env.local
echo "FRONTEND_URL=http://localhost:3000" >> .env.local
```

---

### Step 1: Update `scripts/init_db.py` - Add GSI1

**File:** `scripts/init_db.py`

**What to add:** Create GSI1 (Global Secondary Index) for email lookup.

**Modify the table creation to include:**

```python
# When creating EdTechChatbotTable-{env}, add GlobalSecondaryIndexes parameter

dynamodb.create_table(
    TableName=table_name,
    KeySchema=[
        {'AttributeName': 'PK', 'KeyType': 'HASH'},
        {'AttributeName': 'SK', 'KeyType': 'RANGE'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'PK', 'AttributeType': 'S'},
        {'AttributeName': 'SK', 'AttributeType': 'S'},
        {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},  # NEW
        {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}   # NEW
    ],
    GlobalSecondaryIndexes=[  # NEW
        {
            'IndexName': 'GSI1',
            'KeySchema': [
                {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'},
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
    ],
    BillingMode='PAY_PER_REQUEST'  # Or use ProvisionedThroughput
)

# Enable TTL for expires_at attribute
dynamodb_client.update_time_to_live(
    TableName=table_name,
    TimeToLiveSpecification={
        'Enabled': True,
        'AttributeName': 'expires_at'
    }
)
```

**DECISION POINT:** If `init_db.py` has a different structure or you're unsure how to integrate this, STOP and ask the implementer for guidance on the existing table creation pattern.

---

### Step 2: Update `app/config.py`

**File:** `app/config.py`

**What to add:** Auth configuration fields (see Configuration Changes section above)

**Implementation:**

1. Import `SecretStr` from pydantic (already imported)
2. Add three new fields to `Settings` class: `secret_key`, `access_token_expire_minutes`, `refresh_token_expire_days`, `frontend_url`
3. Add `checkpoint_table_name` property

**No complex logic needed - straightforward field additions.**

---

### Step 3: Create `app/core/security.py`

**File:** `app/core/security.py` (NEW)

**What to implement:**

- Password hashing functions using passlib/bcrypt
- JWT token creation/validation using python-jose
- Token expiration logic

**Complete implementation:**

```python
"""
Security utilities for authentication.
Handles password hashing and JWT token creation/validation.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.secret_key.get_secret_value()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password
        hashed_password: The bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password string
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing token payload (must include 'sub' for user_id)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Example:
        token = create_access_token({"sub": "user_123", "email": "user@example.com", "role": "USER"})
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token (longer-lived).

    Args:
        data: Dictionary containing token payload (must include 'sub' for user_id and 'token_id')

    Returns:
        Encoded JWT token string

    Example:
        token = create_refresh_token({"sub": "user_123", "token_id": "abc-def-123"})
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload dictionary, or None if invalid/expired

    Example:
        payload = decode_token(token)
        if payload:
            user_id = payload.get("sub")
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

**Testing note:** This module should have comprehensive unit tests (see Test Scenarios section).

---

### Step 4: Create `app/schemas/auth.py`

**File:** `app/schemas/auth.py` (NEW)

**What to implement:** Pydantic models for auth requests/responses

**Complete implementation:**

```python
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
```

**DECISION POINT:** If you need additional fields (e.g., `is_active`, `email_verified`), add them here and update the database schema accordingly. Ask the implementer if unclear about requirements.

---

### Step 5: Create `app/services/auth_service.py`

**File:** `app/services/auth_service.py` (NEW)

**What to implement:**

- Business logic for user creation, authentication
- DynamoDB operations for users and refresh tokens
- Methods: `get_user_by_email`, `get_user_by_id`, `create_user`, `authenticate_user`, `store_refresh_token`, `revoke_refresh_token`, `revoke_all_refresh_tokens`

**Complete implementation:**

```python
"""
Authentication service layer.
Handles user management and refresh token storage in DynamoDB.
"""

from datetime import datetime, timedelta
import uuid
from typing import Optional, List
from boto3.dynamodb.conditions import Key
from app.database import dynamodb
from app.config import settings
from app.schemas.auth import UserCreate, UserInDB
from app.core.security import get_password_hash, verify_password


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        self.table = dynamodb.Table(settings.table_name)

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get user by email using GSI1.

        Args:
            email: User's email address

        Returns:
            UserInDB object if found, None otherwise
        """
        response = self.table.query(
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(f'EMAIL#{email}')
        )

        if not response.get('Items'):
            return None

        item = response['Items'][0]
        return UserInDB(**item)

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Get user by user ID.

        Args:
            user_id: User's unique ID

        Returns:
            UserInDB object if found, None otherwise
        """
        response = self.table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': 'PROFILE'
            }
        )

        if 'Item' not in response:
            return None

        return UserInDB(**response['Item'])

    def create_user(self, user: UserCreate) -> UserInDB:
        """
        Create a new user.

        Args:
            user: UserCreate schema with user data

        Returns:
            UserInDB object for created user

        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        existing_user = self.get_user_by_email(user.email)
        if existing_user:
            raise ValueError("Email already registered")

        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        user_data = {
            'PK': f'USER#{user_id}',
            'SK': 'PROFILE',
            'GSI1PK': f'EMAIL#{user.email}',
            'GSI1SK': f'USER#{user_id}',
            'user_id': user_id,
            'email': user.email,
            'hashed_password': get_password_hash(user.password),
            'full_name': user.full_name,
            'role': user.role,
            'created_at': now,
            'updated_at': now
        }

        self.table.put_item(Item=user_data)
        return UserInDB(**user_data)

    def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate user by email and password.

        Args:
            email: User's email
            password: Plain text password

        Returns:
            UserInDB if authentication succeeds, None otherwise
        """
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def store_refresh_token(
        self,
        user_id: str,
        token_id: str,
        expires_in_days: int = 7,
        device: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Store refresh token in DynamoDB for revocation tracking.

        Args:
            user_id: User's ID
            token_id: Unique token ID (UUID)
            expires_in_days: Token expiration in days
            device: Optional device/user-agent string
            ip_address: Optional IP address
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(days=expires_in_days)

        token_data = {
            'PK': f'USER#{user_id}',
            'SK': f'REFRESH_TOKEN#{token_id}',
            'token_id': token_id,
            'device': device or 'Unknown',
            'ip_address': ip_address or 'Unknown',
            'created_at': now.isoformat(),
            'expires_at': int(expires_at.timestamp())  # Unix timestamp for TTL
        }

        self.table.put_item(Item=token_data)

    def is_refresh_token_valid(self, user_id: str, token_id: str) -> bool:
        """
        Check if refresh token exists (not revoked).

        Args:
            user_id: User's ID
            token_id: Token ID to check

        Returns:
            True if token exists and not revoked, False otherwise
        """
        response = self.table.get_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'REFRESH_TOKEN#{token_id}'
            }
        )

        return 'Item' in response

    def revoke_refresh_token(self, user_id: str, token_id: str) -> None:
        """
        Revoke a specific refresh token (logout).

        Args:
            user_id: User's ID
            token_id: Token ID to revoke
        """
        self.table.delete_item(
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'REFRESH_TOKEN#{token_id}'
            }
        )

    def revoke_all_refresh_tokens(self, user_id: str) -> int:
        """
        Revoke all refresh tokens for a user (logout all devices).

        Args:
            user_id: User's ID

        Returns:
            Number of tokens revoked
        """
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq(f'USER#{user_id}') & Key('SK').begins_with('REFRESH_TOKEN#')
        )

        count = 0
        for item in response.get('Items', []):
            self.table.delete_item(
                Key={'PK': item['PK'], 'SK': item['SK']}
            )
            count += 1

        return count
```

**Note:** This uses `app.db.dynamodb.get_table()` - ensure this utility function exists or create it if needed.

---

### Step 6: Create `app/dependencies/auth.py`

**File:** `app/dependencies/auth.py` (NEW)

**What to implement:**

- FastAPI dependencies for authentication
- `oauth2_scheme` (extracts token from Authorization header)
- `get_current_user` (validates token, returns user)
- `require_role` factory (role-based access control)

**Complete implementation:**

```python
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
```

---

### Step 7: Create `app/routers/auth.py`

**File:** `app/routers/auth.py` (NEW)

**What to implement:**

- POST /signup (create user)
- POST /login (authenticate, return tokens, set httpOnly cookie)
- POST /refresh (get new access token using refresh token)
- POST /logout (revoke refresh token)
- POST /logout-all (revoke all refresh tokens)
- GET /me (get current user info)

**Complete implementation:**

```python
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
        user = auth_service.create_user(user_data)
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
    user = auth_service.authenticate_user(form_data.username, form_data.password)

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

    auth_service.store_refresh_token(
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
        secure=True,  # HTTPS only (set to False in local dev if not using HTTPS)
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
    user = auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not auth_service.is_refresh_token_valid(user_id, token_id):
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
    auth_service.revoke_refresh_token(user_id, token_id)
    auth_service.store_refresh_token(
        user_id=user.user_id,
        token_id=new_token_id,
        expires_in_days=settings.refresh_token_expire_days
    )

    # Set new httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
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
            auth_service.revoke_refresh_token(current_user.user_id, token_id)

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
    count = auth_service.revoke_all_refresh_tokens(current_user.user_id)

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
```

**DECISION POINT:** If you need to handle HTTPS differently in local vs sandbox, check `settings.app_env` and set `secure` parameter accordingly. Default assumes HTTPS everywhere (set `secure=False` for local HTTP testing).

---

### Step 8: Create `app/utils/thread.py`

**File:** `app/utils/thread.py` (NEW)

**What to implement:** Utility functions for thread ID generation and parsing

**Complete implementation:**

```python
"""
Thread ID utilities.
"""

import uuid


def generate_thread_id(user_id: str) -> str:
    """
    Generate thread ID from user ID and UUID.

    Format: {user_id}_{uuid}

    Args:
        user_id: User's unique ID

    Returns:
        Thread ID string

    Example:
        >>> generate_thread_id("user_123")
        "user_123_abc-def-ghi-jkl-mno"
    """
    return f"{user_id}_{uuid.uuid4()}"


def extract_user_id_from_thread(thread_id: str) -> str:
    """
    Extract user ID from thread ID.

    Args:
        thread_id: Thread ID in format {user_id}_{uuid}

    Returns:
        User ID string

    Example:
        >>> extract_user_id_from_thread("user_123_abc-def-ghi")
        "user_123"
    """
    return thread_id.split("_")[0]
```

---

### Step 9: Update `app/main.py`

**File:** `app/main.py` (UPDATE)

**What to update:**

- Import auth router
- Add CORS middleware with credentials support (for httpOnly cookies)
- Create public router for auth endpoints
- Create protected router with global auth dependency for all other endpoints

**Implementation:**

```python
# Add these imports
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from app.dependencies.auth import get_current_user

# Create FastAPI app (existing)
app = FastAPI(
    title="EdTech Chatbot API",
    description="AI-powered chatbot for early childhood education",
    version="1.0.0"
)

# Add CORS middleware (for httpOnly cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],  # Frontend URL from config
    allow_credentials=True,  # REQUIRED for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes (no authentication required)
public_router = APIRouter(prefix="/api/v1")
public_router.include_router(auth.router)  # /api/v1/auth/*

# Protected routes (require authentication globally)
protected_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(get_current_user)]  # Applied to ALL routes in this router
)

# Include your existing routers in protected_router
# protected_router.include_router(chat.router)  # Uncomment when chat router exists
# protected_router.include_router(threads.router)  # Add other routers here

# Mount routers to app
app.include_router(public_router)
app.include_router(protected_router)

# Health check endpoint (public)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**DECISION POINT:**

- If you have existing routers (chat, threads, etc.), add them to `protected_router` instead of `app` directly.
- If you're unsure about the existing routing structure, STOP and ask where existing routes should be moved.

---

### Step 10: Verify `app/database.py` (Existing)

**File:** `app/database.py`

**What to check:** This file already exists with DynamoDB utilities.

**Current structure:**

```python
from app.database import dynamodb

# To get a table:
table = dynamodb.Table(settings.table_name)

# Or use the global table reference:
from app.database import table
```

**Used in `AuthService`:**

```python
from app.database import dynamodb

class AuthService:
    def __init__(self):
        self.table = dynamodb.Table(settings.table_name)
```

**No changes needed** - `database.py` already provides everything we need.

---

## Test Scenarios

### Unit Tests: `tests/unit/test_security.py`

```python
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
```

### Unit Tests: `tests/unit/test_auth_service.py`

```python
"""
Unit tests for auth service.
Uses moto to mock DynamoDB.
"""

import pytest
from moto import mock_dynamodb
import boto3
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate


@pytest.fixture
def dynamodb_table():
    """Create mock DynamoDB table for testing."""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Create table
        table = dynamodb.create_table(
            TableName='EdTechChatbotTable-local',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        yield table


def test_create_user(dynamodb_table):
    """Test user creation."""
    auth_service = AuthService()

    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User",
        role="USER"
    )

    user = auth_service.create_user(user_data)

    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.role == "USER"
    assert user.user_id is not None
    assert user.hashed_password != "password123"  # Should be hashed


def test_create_duplicate_email(dynamodb_table):
    """Test creating user with duplicate email raises error."""
    auth_service = AuthService()

    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User"
    )

    # First creation should succeed
    auth_service.create_user(user_data)

    # Second creation should fail
    with pytest.raises(ValueError, match="Email already registered"):
        auth_service.create_user(user_data)


def test_authenticate_user_success(dynamodb_table):
    """Test successful authentication."""
    auth_service = AuthService()

    # Create user
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User"
    )
    auth_service.create_user(user_data)

    # Authenticate
    user = auth_service.authenticate_user("test@example.com", "password123")

    assert user is not None
    assert user.email == "test@example.com"


def test_authenticate_user_wrong_password(dynamodb_table):
    """Test authentication with wrong password."""
    auth_service = AuthService()

    # Create user
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User"
    )
    auth_service.create_user(user_data)

    # Authenticate with wrong password
    user = auth_service.authenticate_user("test@example.com", "wrongpassword")

    assert user is None


def test_authenticate_user_not_found(dynamodb_table):
    """Test authentication for non-existent user."""
    auth_service = AuthService()

    user = auth_service.authenticate_user("notfound@example.com", "password123")

    assert user is None
```

### Integration Tests: `tests/integration/test_auth_routes.py`

```python
"""
Integration tests for auth routes.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_signup_success():
    """
    Given: Valid user data
    When: POST /api/v1/auth/signup
    Then: Returns 201 with user profile
    """
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
            "role": "USER"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "USER"
    assert "user_id" in data
    assert "hashed_password" not in data  # Should not expose password


def test_signup_duplicate_email():
    """
    Given: User already exists with email
    When: POST /api/v1/auth/signup with same email
    Then: Returns 409 Conflict
    """
    # First signup
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "First User"
        }
    )

    # Second signup with same email
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "password456",
            "full_name": "Second User"
        }
    )

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_login_success():
    """
    Given: User exists with correct credentials
    When: POST /api/v1/auth/login
    Then: Returns 200 with access_token and sets refresh_token cookie
    """
    # Create user first
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "loginuser@example.com",
            "password": "password123",
            "full_name": "Login User"
        }
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={  # OAuth2 uses form data, not JSON
            "username": "loginuser@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Check cookie is set
    assert "refresh_token" in response.cookies


def test_login_wrong_password():
    """
    Given: User exists
    When: POST /api/v1/auth/login with wrong password
    Then: Returns 401 Unauthorized
    """
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "testuser@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
    )

    # Login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_protected_route_without_token():
    """
    Given: No authentication token
    When: GET /api/v1/auth/me (protected route)
    Then: Returns 401 Unauthorized
    """
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_protected_route_with_valid_token():
    """
    Given: Valid access token
    When: GET /api/v1/auth/me
    Then: Returns 200 with user info
    """
    # Signup and login
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "authuser@example.com",
            "password": "password123",
            "full_name": "Auth User"
        }
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "authuser@example.com",
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
    assert data["email"] == "authuser@example.com"
    assert data["full_name"] == "Auth User"


def test_token_refresh():
    """
    Given: Valid refresh token in cookie
    When: POST /api/v1/auth/refresh
    Then: Returns 200 with new access_token and new refresh_token cookie
    """
    # Signup and login
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "refreshuser@example.com",
            "password": "password123",
            "full_name": "Refresh User"
        }
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "refreshuser@example.com",
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


def test_logout():
    """
    Given: Authenticated user
    When: POST /api/v1/auth/logout
    Then: Returns 200 and clears refresh_token cookie
    And: Refresh token is revoked in database
    """
    # Signup and login
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "logoutuser@example.com",
            "password": "password123",
            "full_name": "Logout User"
        }
    )

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "logoutuser@example.com",
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
```

---

## API Contracts

### POST /api/v1/auth/signup

**Request Body:**

```json
{
  "email": "teacher@school.edu",
  "password": "securepassword123",
  "full_name": "Jane Doe",
  "role": "USER"
}
```

**Success Response (201):**

```json
{
  "user_id": "user_123",
  "email": "teacher@school.edu",
  "full_name": "Jane Doe",
  "role": "USER",
  "created_at": "2024-01-15T10:00:00Z"
}
```

**Error Response (409) - Email exists:**

```json
{
  "detail": "Email already registered"
}
```

**Error Response (400) - Validation error:**

```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

---

### POST /api/v1/auth/login

**Request (Form Data):**

```
username=teacher@school.edu
password=securepassword123
```

**Success Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Cookie Set:**

```
refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...;
HttpOnly; Secure; SameSite=Lax; Max-Age=604800
```

**Error Response (401):**

```json
{
  "detail": "Incorrect email or password"
}
```

---

### POST /api/v1/auth/refresh

**Request:**

- Refresh token from httpOnly cookie (automatically sent by browser)

**Success Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**New Cookie Set:**

```
refresh_token=<new-token>; HttpOnly; Secure; SameSite=Lax; Max-Age=604800
```

**Error Response (401):**

```json
{
  "detail": "Invalid refresh token"
}
```

---

### POST /api/v1/auth/logout

**Request Headers:**

```
Authorization: Bearer <access_token>
```

**Success Response (200):**

```json
{
  "message": "Successfully logged out"
}
```

**Cookie Cleared:**

```
refresh_token=; Max-Age=0
```

---

### GET /api/v1/auth/me

**Request Headers:**

```
Authorization: Bearer <access_token>
```

**Success Response (200):**

```json
{
  "user_id": "user_123",
  "email": "teacher@school.edu",
  "full_name": "Jane Doe",
  "role": "USER",
  "created_at": "2024-01-15T10:00:00Z"
}
```

**Error Response (401):**

```json
{
  "detail": "Could not validate credentials"
}
```

---

## Success Criteria

Implementation is complete when:

- [ ] User can signup with email/password (POST /signup)
- [ ] User can login and receive access token + refresh token cookie (POST /login)
- [ ] Protected routes reject requests without valid token (401)
- [ ] Protected routes accept requests with valid token
- [ ] User can access their info (GET /me)
- [ ] Token refresh works (POST /refresh)
- [ ] Logout revokes refresh token (POST /logout)
- [ ] Logout all devices revokes all refresh tokens (POST /logout-all)
- [ ] Admin-only routes reject USER role (403)
- [ ] GSI1 exists for email lookup
- [ ] TTL is configured for expires_at attribute
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Swagger UI shows "Authorize" button and works

---

## Migration Notes

### For Existing Chat/Thread Routes

If you have existing routes (e.g., `/chat/message`, `/threads`):

1. **Move to protected router in main.py:**

   ```python
   protected_router.include_router(chat.router)
   ```

2. **Update thread creation to use user_id:**

   ```python
   from app.utils.thread import generate_thread_id
   from app.dependencies.auth import get_current_user

   @router.post("/message")
   async def send_message(
       message: str,
       current_user: UserInDB = Depends(get_current_user)
   ):
       thread_id = generate_thread_id(current_user.user_id)
       # ... rest of logic
   ```

3. **No need to add `Depends(get_current_user)` to every route** - it's applied globally via protected_router.

---

## Future Improvements (Out of Scope)

- [ ] MFA (multi-factor authentication) with TOTP
- [ ] OAuth2 social login (Google, Microsoft)
- [ ] Email verification on signup
- [ ] Password reset flow (forgot password)
- [ ] Rate limiting for login endpoint (prevent brute force)
- [ ] Migrate SECRET_KEY to AWS Secrets Manager
- [ ] Audit logging for security events
- [ ] Session management UI (view active devices)

---

## Questions for Implementer

**If you encounter any of these situations, STOP and ask for guidance:**

1. **Database Structure Mismatch:**

   - If `init_db.py` has a significantly different structure than shown in Step 1
   - Note: `app/database.py` already exists with DynamoDB utilities - use `from app.database import dynamodb`

2. **Routing Structure Confusion:**

   - If you're unsure where to add existing routers (chat, threads) in the public vs protected router setup
   - If there are existing middleware or dependencies that might conflict

3. **Environment Configuration:**

   - If `.env.local` or `.env.sandbox` have different naming conventions
   - If there's a different pattern for loading environment variables

4. **Testing Setup:**

   - If there's an existing test structure (fixtures, mocks) that should be reused
   - If moto doesn't work with the existing DynamoDB setup

5. **CORS/Security:**

   - If the frontend URL is different or requires special CORS handling
   - If there are existing security middleware that might conflict

6. **Docker/Deployment:**
   - If updating `requirements.txt` requires additional Docker or deployment changes
   - If there's a specific process for dependency management

**General rule:** When in doubt, ask! It's better to clarify than to make assumptions.

---

## Implementation Checklist

- [ ] Generate SECRET_KEY for .env.local and .env.sandbox
- [ ] Update requirements.txt with new dependencies
- [ ] Update config.py with auth fields
- [ ] Update init_db.py to create GSI1 and enable TTL
- [ ] Create app/core/security.py
- [ ] Create app/schemas/auth.py
- [ ] Create app/services/auth_service.py
- [ ] Create app/dependencies/auth.py
- [ ] Create app/routers/auth.py
- [ ] Create app/utils/thread.py
- [ ] Update app/main.py (CORS, routers, global auth dependency)
- [ ] Verify app/database.py exists (already present - no changes needed)
- [ ] Write unit tests for security.py
- [ ] Write unit tests for auth_service.py
- [ ] Write integration tests for auth routes
- [ ] Run all tests
- [ ] Test in Swagger UI (/docs)
- [ ] Create first admin user manually in DynamoDB
- [ ] Update existing chat/thread routes to use auth

---

**End of Spec**
