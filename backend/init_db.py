"""
Initialize DynamoDB tables for the EdTech Chatbot application.
Creates main application table and checkpoint table with proper indexes and TTL.
"""
import sys
import os

# Add the current directory to the path so we can import app modules
# Works both locally (backend/) and in Docker container (/app/)
sys.path.insert(0, os.path.dirname(__file__))

import boto3
from botocore.exceptions import ClientError
from app.config import settings, AppEnv


def create_main_table(dynamodb_client, table_name):
    """
    Create the main EdTechChatbot table with GSI1 for email lookup.

    Args:
        dynamodb_client: Boto3 DynamoDB client
        table_name: Name of the table to create
    """
    # Check if table already exists
    try:
        table_description = dynamodb_client.describe_table(TableName=table_name)
        table_status = table_description['Table']['TableStatus']
        print(f"⚠️  Table {table_name} already exists (Status: {table_status})")
        return False
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            print(f"❌ Error checking table existence: {e}")
            raise
        # Table doesn't exist, continue to create it

    try:
        dynamodb_client.create_table(
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
            BillingMode='PAY_PER_REQUEST'
        )

        # Wait for table to be created
        print(f"⏳ Creating table {table_name}...")
        waiter = dynamodb_client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)

        # Enable TTL for expires_at attribute (for refresh token auto-deletion)
        dynamodb_client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'expires_at'
            }
        )

        print(f"✅ Table {table_name} created successfully with GSI1 and TTL enabled")
        return True

    except ClientError as e:
        print(f"❌ Error creating table {table_name}: {e}")
        raise


def create_checkpoint_table(dynamodb_client, table_name):
    """
    Create the LangGraph checkpoint table.

    Args:
        dynamodb_client: Boto3 DynamoDB client
        table_name: Name of the checkpoint table to create
    """
    # Check if table already exists
    try:
        table_description = dynamodb_client.describe_table(TableName=table_name)
        table_status = table_description['Table']['TableStatus']
        print(f"⚠️  Checkpoint table {table_name} already exists (Status: {table_status})")
        return False
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            print(f"❌ Error checking checkpoint table existence: {e}")
            raise
        # Table doesn't exist, continue to create it

    try:
        dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Wait for table to be created
        print(f"⏳ Creating checkpoint table {table_name}...")
        waiter = dynamodb_client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)

        print(f"✅ Checkpoint table {table_name} created successfully")
        return True

    except ClientError as e:
        print(f"❌ Error creating checkpoint table {table_name}: {e}")
        raise


def delete_table(dynamodb_client, table_name):
    """
    Delete a DynamoDB table.

    Args:
        dynamodb_client: Boto3 DynamoDB client
        table_name: Name of the table to delete
    """
    try:
        dynamodb_client.delete_table(TableName=table_name)
        print(f"⏳ Deleting table {table_name}...")
        waiter = dynamodb_client.get_waiter('table_not_exists')
        waiter.wait(TableName=table_name)
        print(f"✅ Table {table_name} deleted successfully")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"⚠️  Table {table_name} does not exist")
            return False
        print(f"❌ Error deleting table {table_name}: {e}")
        raise


def get_dynamodb_client():
    """Get DynamoDB client based on environment."""
    if settings.app_env == AppEnv.LOCAL:
        return boto3.client(
            'dynamodb',
            endpoint_url=settings.dynamodb_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or "dummy",
            aws_secret_access_key=settings.aws_secret_access_key or "dummy"
        )
    elif settings.app_env == AppEnv.SANDBOX:
        return boto3.client(
            'dynamodb',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
    else:  # PRODUCTION
        return boto3.client(
            'dynamodb',
            region_name=settings.aws_region
        )


def main():
    """Initialize all DynamoDB tables."""
    print(f"🚀 Initializing DynamoDB tables for environment: {settings.app_env}")

    dynamodb_client = get_dynamodb_client()

    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "reset":
            print("=" * 60)
            print("RESETTING DYNAMODB TABLES")
            print("=" * 60)
            # Delete tables first
            delete_table(dynamodb_client, settings.table_name)
            delete_table(dynamodb_client, settings.checkpoint_table_name)
            # Then create them
            create_main_table(dynamodb_client, settings.table_name)
            create_checkpoint_table(dynamodb_client, settings.checkpoint_table_name)
            print("\n" + "=" * 60)
            print("RESET COMPLETE")
            print("=" * 60)
            return

        elif command == "delete":
            delete_table(dynamodb_client, settings.table_name)
            delete_table(dynamodb_client, settings.checkpoint_table_name)
            return

        elif command != "create":
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python init_db.py          - Create tables (default)")
            print("  python init_db.py create   - Create tables")
            print("  python init_db.py delete   - Delete tables")
            print("  python init_db.py reset    - Delete and recreate tables")
            sys.exit(1)

    # Default: create tables
    main_table_name = settings.table_name
    create_main_table(dynamodb_client, main_table_name)

    checkpoint_table_name = settings.checkpoint_table_name
    create_checkpoint_table(dynamodb_client, checkpoint_table_name)

    print("\n✨ Database initialization complete!")
    print(f"📊 Main table: {main_table_name}")
    print(f"📊 Checkpoint table: {checkpoint_table_name}")


if __name__ == "__main__":
    main()
