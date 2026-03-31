"""
Authentication service layer.
Handles user management and refresh token storage in DynamoDB.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional, List
from boto3.dynamodb.conditions import Key
from app.database import get_db
from app.config import settings
from app.schemas.auth import UserCreate, UserInDB
from app.core.security import get_password_hash, verify_password


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        self.table = get_db()

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get user by email using GSI1.

        Args:
            email: User's email address

        Returns:
            UserInDB object if found, None otherwise
        """
        response = await asyncio.to_thread(
            self.table.query,
            IndexName='GSI1',
            KeyConditionExpression=Key('GSI1PK').eq(f'EMAIL#{email}')
        )

        if not response.get('Items'):
            return None

        item = response['Items'][0]
        return UserInDB(**item)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Get user by user ID.

        Args:
            user_id: User's unique ID

        Returns:
            UserInDB object if found, None otherwise
        """
        response = await asyncio.to_thread(
            self.table.get_item,
            Key={
                'PK': f'USER#{user_id}',
                'SK': 'PROFILE'
            }
        )

        if 'Item' not in response:
            return None

        return UserInDB(**response['Item'])

    async def create_user(self, user: UserCreate) -> UserInDB:
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
        existing_user = await self.get_user_by_email(user.email)
        if existing_user:
            raise ValueError("Email already registered")

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        user_data = {
            'PK': f'USER#{user_id}',
            'SK': 'PROFILE',
            'GSI1PK': f'EMAIL#{user.email}',
            'GSI1SK': f'USER#{user_id}',
            'user_id': user_id,
            'email': user.email,
            'hashed_password': await asyncio.to_thread(get_password_hash, user.password),
            'full_name': user.full_name,
            'role': user.role,
            'created_at': now,
            'updated_at': now
        }

        await asyncio.to_thread(self.table.put_item, Item=user_data)
        return UserInDB(**user_data)

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate user by email and password.

        Args:
            email: User's email
            password: Plain text password

        Returns:
            UserInDB if authentication succeeds, None otherwise
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not await asyncio.to_thread(verify_password, password, user.hashed_password):
            return None
        return user

    async def store_refresh_token(
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
        now = datetime.now(timezone.utc)
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

        await asyncio.to_thread(self.table.put_item, Item=token_data)

    async def is_refresh_token_valid(self, user_id: str, token_id: str) -> bool:
        """
        Check if refresh token exists (not revoked).

        Args:
            user_id: User's ID
            token_id: Token ID to check

        Returns:
            True if token exists and not revoked, False otherwise
        """
        response = await asyncio.to_thread(
            self.table.get_item,
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'REFRESH_TOKEN#{token_id}'
            }
        )

        return 'Item' in response

    async def revoke_refresh_token(self, user_id: str, token_id: str) -> None:
        """
        Revoke a specific refresh token (logout).

        Args:
            user_id: User's ID
            token_id: Token ID to revoke
        """
        await asyncio.to_thread(
            self.table.delete_item,
            Key={
                'PK': f'USER#{user_id}',
                'SK': f'REFRESH_TOKEN#{token_id}'
            }
        )

    async def revoke_all_refresh_tokens(self, user_id: str) -> int:
        """
        Revoke all refresh tokens for a user (logout all devices).

        Args:
            user_id: User's ID

        Returns:
            Number of tokens revoked
        """
        response = await asyncio.to_thread(
            self.table.query,
            KeyConditionExpression=Key('PK').eq(f'USER#{user_id}') & Key('SK').begins_with('REFRESH_TOKEN#')
        )

        count = 0
        for item in response.get('Items', []):
            await asyncio.to_thread(
                self.table.delete_item,
                Key={'PK': item['PK'], 'SK': item['SK']}
            )
            count += 1

        return count
