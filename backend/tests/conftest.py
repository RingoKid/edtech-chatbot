"""
Shared pytest fixtures and utilities for all tests.
"""
import pytest
import boto3
import uuid
from botocore.exceptions import ClientError

from app.schemas.auth import UserInDB
from app.config import settings
from app.db_schema import MAIN_TABLE_SCHEMA, CHECKPOINT_TABLE_SCHEMA


def unique_email(prefix: str = "test") -> str:
    """Generate a unique email address for test isolation."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture(scope="session", autouse=True)
def dynamodb_tables():
    """
    Session-scoped fixture that ensures DynamoDB tables exist for all tests.
    Creates tables if they don't exist, does NOT delete them after tests.
    This runs once at the start of the test session.
    """
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=settings.dynamodb_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or 'dummy',
        aws_secret_access_key=settings.aws_secret_access_key or 'dummy'
    )

    # Create main table if it doesn't exist
    main_table_name = settings.table_name
    try:
        table = dynamodb.Table(main_table_name)
        table.load()  # Check if exists
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            main_table = dynamodb.create_table(
                TableName=main_table_name,
                BillingMode='PAY_PER_REQUEST',
                **MAIN_TABLE_SCHEMA
            )
            main_table.wait_until_exists()

    # Create checkpoint table if it doesn't exist
    checkpoint_table_name = settings.checkpoint_table_name
    try:
        table = dynamodb.Table(checkpoint_table_name)
        table.load()  # Check if exists
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            checkpoint_table = dynamodb.create_table(
                TableName=checkpoint_table_name,
                BillingMode='PAY_PER_REQUEST',
                **CHECKPOINT_TABLE_SCHEMA
            )
            checkpoint_table.wait_until_exists()

    yield {
        "main": dynamodb.Table(main_table_name),
        "checkpoint": dynamodb.Table(checkpoint_table_name)
    }

    # No cleanup - tables persist for faster subsequent test runs


def get_test_user() -> UserInDB:
    """
    Mock user for bypassing authentication in tests.
    Returns a UserInDB instance (not a dict) to match production behavior.
    """
    return UserInDB(
        user_id="test-user-123",
        email="test@example.com",
        full_name="Test User",
        role="USER",
        created_at="2024-01-01T00:00:00Z",
        hashed_password="fake-hashed-password"
    )
