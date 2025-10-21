import boto3
import logging
import os
from botocore.exceptions import ClientError

# Force local environment for development - MUST be set before importing settings
os.environ['APP_ENV'] = 'local'
os.environ['DYNAMODB_TABLE_NAME'] = 'EdTechChatbotTable'

from .config import settings, AppEnv
from .file_database import get_file_db, initialize_file_database, test_file_connection

# Configure logging
logger = logging.getLogger(__name__)


def get_dynamodb_resource():
    """
    Create and return a DynamoDB resource based on the application environment.

    Returns:
        boto3.resource or file_database: DynamoDB resource or file-based database
    """
    from .config import settings
    
    if settings.app_env == AppEnv.LOCAL:
        # For local development, try to use DynamoDB Local, fallback to file database
        try:
            # Test if DynamoDB Local is available
            test_client = boto3.client(
                'dynamodb',
                endpoint_url=settings.dynamodb_endpoint_url,
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id or "dummy",
                aws_secret_access_key=settings.aws_secret_access_key or "dummy"
            )
            test_client.list_tables()  # This will fail if DynamoDB Local is not running
            return boto3.resource(
                'dynamodb',
                endpoint_url=settings.dynamodb_endpoint_url,
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id or "dummy",
                aws_secret_access_key=settings.aws_secret_access_key or "dummy"
            )
        except Exception:
            # Fallback to file-based database if DynamoDB Local is not available
            print("DynamoDB Local not available, using file-based database")
            return None
    elif settings.app_env == AppEnv.SANDBOX:
        # Sandbox environment configuration - uses AWS DynamoDB with explicit credentials
        return boto3.resource(
            'dynamodb',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
    else:  # PRODUCTION
        # Production environment configuration - uses AWS DynamoDB with IAM role/profile
        return boto3.resource(
            'dynamodb',
            region_name=settings.aws_region
        )


# Environment variables are already set at the top of the file

# Global DynamoDB resource
dynamodb = get_dynamodb_resource()

# Global table reference - use file database if DynamoDB is not available
if dynamodb is not None:
    table = dynamodb.Table(settings.table_name)
else:
    table = get_file_db()


def create_table_if_not_exists():
    """
    Create the DynamoDB table if it doesn't exist.
    Uses a single-table design with PK and SK.

    Returns:
        bool: True if table exists or was created successfully
    """
    try:
        table_name = settings.table_name

        # If using file database, just initialize it
        if dynamodb is None:
            logger.info(f"Using file-based database for table: {table_name}")
            return initialize_file_database()

        # Check if table exists
        try:
            existing_table = dynamodb.Table(table_name)
            existing_table.load()
            logger.info(f"Table {table_name} already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise

        # Create table with single-table design
        logger.info(f"Creating DynamoDB table: {table_name}")
        new_table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},   # Partition key
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}   # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'type', 'AttributeType': 'S'},
                {'AttributeName': 'category', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'TypeIndex',
                    'KeySchema': [
                        {'AttributeName': 'type', 'KeyType': 'HASH'},
                        {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'CategoryIndex',
                    'KeySchema': [
                        {'AttributeName': 'category', 'KeyType': 'HASH'},
                        {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # Wait for table to be created
        logger.info("Waiting for table to be created...")
        new_table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        logger.info(f"Table {table_name} created successfully")

        return True

    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return False


def test_connection():
    """
    Test the DynamoDB connection.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        if dynamodb is None:
            # Test file database connection
            return test_file_connection()
        else:
            table.load()
            logger.info("DynamoDB connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def initialize_database():
    """
    Initialize the database by creating table if needed.
    Called on application startup.

    Returns:
        bool: True if initialization successful
    """
    try:
        logger.info("Initializing database...")

        # Create table if it doesn't exist
        if not create_table_if_not_exists():
            logger.error("Failed to create database table")
            return False

        # Test connection
        if not test_connection():
            logger.error("Failed to connect to database")
            return False

        logger.info("Database initialization complete")
        return True

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False


def get_db():
    """
    FastAPI dependency function to provide database access.

    Returns:
        boto3.resources.dynamodb.Table: The DynamoDB table resource
    """
    return table