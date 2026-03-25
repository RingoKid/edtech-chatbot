"""
Unit tests for auth service.
Uses DynamoDB Local container for testing.
"""

import pytest
import boto3
from botocore.exceptions import ClientError
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate
from app.config import settings


@pytest.fixture(scope="module")
def dynamodb_table():
    """Use real DynamoDB Local container for testing."""
    # Connect to DynamoDB Local
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=settings.dynamodb_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )

    table_name = settings.table_name

    # Try to delete table if it exists from previous test run
    try:
        table = dynamodb.Table(table_name)
        table.delete()
        table.wait_until_not_exists()
    except ClientError:
        pass  # Table doesn't exist, which is fine

    # Create fresh table
    table = dynamodb.create_table(
        TableName=table_name,
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

    # Wait for table to be ready
    table.wait_until_exists()

    yield table

    # Cleanup after all tests
    try:
        table.delete()
    except ClientError:
        pass


@pytest.mark.asyncio
async def test_create_user(dynamodb_table):
    """Test user creation."""
    auth_service = AuthService()

    user_data = UserCreate(
        email="test1@example.com",
        password="password123",
        full_name="Test User",
        role="USER"
    )

    user = await auth_service.create_user(user_data)

    assert user.email == "test1@example.com"
    assert user.full_name == "Test User"
    assert user.role == "USER"
    assert user.user_id is not None
    assert user.hashed_password != "password123"  # Should be hashed


@pytest.mark.asyncio
async def test_create_duplicate_email(dynamodb_table):
    """Test creating user with duplicate email raises error."""
    auth_service = AuthService()

    user_data = UserCreate(
        email="test2@example.com",
        password="password123",
        full_name="Test User"
    )

    # First creation should succeed
    await auth_service.create_user(user_data)

    # Second creation should fail
    with pytest.raises(ValueError, match="Email already registered"):
        await auth_service.create_user(user_data)


@pytest.mark.asyncio
async def test_authenticate_user_success(dynamodb_table):
    """Test successful authentication."""
    auth_service = AuthService()

    # Create user
    user_data = UserCreate(
        email="test3@example.com",
        password="password123",
        full_name="Test User"
    )
    await auth_service.create_user(user_data)

    # Authenticate
    user = await auth_service.authenticate_user("test3@example.com", "password123")

    assert user is not None
    assert user.email == "test3@example.com"


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(dynamodb_table):
    """Test authentication with wrong password."""
    auth_service = AuthService()

    # Create user
    user_data = UserCreate(
        email="test4@example.com",
        password="password123",
        full_name="Test User"
    )
    await auth_service.create_user(user_data)

    # Authenticate with wrong password
    user = await auth_service.authenticate_user("test4@example.com", "wrongpassword")

    assert user is None


@pytest.mark.asyncio
async def test_authenticate_user_not_found(dynamodb_table):
    """Test authentication for non-existent user."""
    auth_service = AuthService()

    user = await auth_service.authenticate_user("notfound@example.com", "password123")

    assert user is None
