import boto3
import logging
from botocore.exceptions import ClientError
from .config import settings, AppEnv

# Configure logging
logger = logging.getLogger(__name__)


def get_dynamodb_resource():
    """
    Create and return a DynamoDB resource based on the application environment.

    Returns:
        boto3.resource: DynamoDB resource configured for local, sandbox, or production environment
    """
    if settings.app_env == AppEnv.LOCAL:
        # Local environment configuration - uses local DynamoDB endpoint
        return boto3.resource(
            'dynamodb',
            endpoint_url=settings.dynamodb_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or "dummy",
            aws_secret_access_key=settings.aws_secret_access_key or "dummy"
        )
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


# Global DynamoDB resource
dynamodb = get_dynamodb_resource()

# Global table reference
table = dynamodb.Table(settings.table_name)


def create_table_if_not_exists():
    """
    Create the DynamoDB table if it doesn't exist.
    Uses a single-table design with PK and SK.

    Returns:
        bool: True if table exists or was created successfully
    """
    try:
        table_name = settings.table_name

        # Check if table exists
        try:
            existing_table = dynamodb.Table(table_name)
            existing_table.load()
            logger.info(f"✅ Table {table_name} already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise

        # Create table with single-table design
        logger.info(f"📊 Creating DynamoDB table: {table_name}")
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
        logger.info("⏳ Waiting for table to be created...")
        new_table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        logger.info(f"✅ Table {table_name} created successfully")

        return True

    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        return False


def test_connection():
    """
    Test the DynamoDB connection.
    Tests the DynamoDB SERVICE connection, not whether a specific table exists.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        # Test DynamoDB service connection by listing tables
        # This works even if no tables exist yet
        dynamodb.meta.client.list_tables()
        logger.info("✅ DynamoDB connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ DynamoDB connection test failed: {e}")
        return False


def initialize_database():
    """
    Initialize the database by creating table if needed.
    Called on application startup.

    Returns:
        bool: True if initialization successful
    """
    try:
        logger.info("🚀 Initializing DynamoDB...")

        # Create table if it doesn't exist
        if not create_table_if_not_exists():
            logger.error("❌ Failed to create DynamoDB table")
            return False

        # Test connection
        if not test_connection():
            logger.error("❌ Failed to connect to DynamoDB")
            return False

        logger.info("✅ DynamoDB initialization complete")
        return True

    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False


def get_db():
    """
    FastAPI dependency function to provide database access.

    Returns:
        boto3.resources.dynamodb.Table: The DynamoDB table resource
    """
    return table