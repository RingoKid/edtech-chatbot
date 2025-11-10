"""
Unit tests for auth service.
Uses moto to mock DynamoDB.
"""

import pytest
from moto import mock_aws
import boto3
import os
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate


@pytest.fixture
def mock_dynamodb_table():
    """Create mock DynamoDB table for testing."""
    # Set environment variables for testing
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:8000'
    os.environ['APP_ENV'] = 'local'

    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id='testing',
            aws_secret_access_key='testing'
        )

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


def test_create_user(mock_dynamodb_table):
    """Test user creation."""
    # Reload the module to pick up the mocked AWS
    import importlib
    import app.database
    importlib.reload(app.database)

    from app.services.auth_service import AuthService

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


def test_create_duplicate_email(mock_dynamodb_table):
    """Test creating user with duplicate email raises error."""
    import importlib
    import app.database
    importlib.reload(app.database)

    from app.services.auth_service import AuthService

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


def test_authenticate_user_success(mock_dynamodb_table):
    """Test successful authentication."""
    import importlib
    import app.database
    importlib.reload(app.database)

    from app.services.auth_service import AuthService

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


def test_authenticate_user_wrong_password(mock_dynamodb_table):
    """Test authentication with wrong password."""
    import importlib
    import app.database
    importlib.reload(app.database)

    from app.services.auth_service import AuthService

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


def test_authenticate_user_not_found(mock_dynamodb_table):
    """Test authentication for non-existent user."""
    import importlib
    import app.database
    importlib.reload(app.database)

    from app.services.auth_service import AuthService

    auth_service = AuthService()

    user = auth_service.authenticate_user("notfound@example.com", "password123")

    assert user is None
