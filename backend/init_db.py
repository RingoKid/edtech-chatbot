#!/usr/bin/env python3
"""
Database initialization script for DynamoDB Local.
Creates the required DynamoDB table for LangGraph checkpoint storage.

This script can be run manually or imported by tests to set up the database.
It uses the existing configuration from app.config to ensure consistency.
"""

import sys
import boto3
from app.config import settings, AppEnv
from app.database import get_dynamodb_resource


def create_checkpoint_table():
    """
    Create the DynamoDB table for LangGraph checkpoint storage.

    The table uses the schema required by langgraph_dynamodb_checkpoint:
    - Partition key (pk): String - stores the thread/namespace identifier
    - Sort key (sk): String - stores the checkpoint identifier

    Table name is generated based on APP_ENV from settings.table_name:
    - LOCAL: EdTechChatbotTable-local
    - SANDBOX: EdTechChatbotTable-sandbox
    - PRODUCTION: EdTechChatbotTable-prod

    Returns:
        bool: True if table was created, False if it already exists
    """
    print("=" * 60)
    print("DYNAMODB TABLE INITIALIZATION")
    print("=" * 60)

    # Get the table name from settings (environment-aware)
    table_name = settings.table_name
    print(f"Environment: {settings.app_env}")
    print(f"Table name: {table_name}")

    # Get DynamoDB resource using existing configuration
    dynamodb = get_dynamodb_resource()
    client = dynamodb.meta.client

    # Check if table already exists by trying to describe it
    try:
        table_description = client.describe_table(TableName=table_name)
        table_status = table_description['Table']['TableStatus']
        print(f"✓ Table '{table_name}' already exists")
        print(f"  Status: {table_status}")
        return False
    except client.exceptions.ResourceNotFoundException:
        # Table doesn't exist, continue to create it
        pass
    except Exception as e:
        print(f"Warning: Could not check table existence: {e}")

    # Create the table with LangGraph checkpoint schema
    print(f"\nCreating table '{table_name}'...")

    try:
        client.create_table(
            TableName=table_name,
            # LangGraph DynamoDB checkpoint schema
            KeySchema=[
                {'AttributeName': 'pk', 'KeyType': 'HASH'},   # Partition key
                {'AttributeName': 'sk', 'KeyType': 'RANGE'}   # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'pk', 'AttributeType': 'S'},  # String
                {'AttributeName': 'sk', 'AttributeType': 'S'}   # String
            ],
            # Use on-demand billing for local development
            BillingMode='PAY_PER_REQUEST'
        )

        print(f"✓ Table '{table_name}' created successfully!")

        # Wait for table to be active (important for local DynamoDB)
        if settings.app_env == AppEnv.LOCAL:
            print("Waiting for table to be active...")
            waiter = client.get_waiter('table_exists')
            waiter.wait(
                TableName=table_name,
                WaiterConfig={'Delay': 1, 'MaxAttempts': 10}
            )
            print("✓ Table is now active")

        return True

    except client.exceptions.ResourceInUseException:
        print(f"✓ Table '{table_name}' already exists (created by another process)")
        return False
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        raise


def delete_checkpoint_table():
    """
    Delete the DynamoDB checkpoint table.
    Use with caution - this will delete all checkpoint data!

    Returns:
        bool: True if table was deleted, False if it didn't exist
    """
    table_name = settings.table_name
    print(f"\nDeleting table '{table_name}'...")

    dynamodb = get_dynamodb_resource()
    client = dynamodb.meta.client

    try:
        client.delete_table(TableName=table_name)
        print(f"✓ Table '{table_name}' deleted successfully!")
        return True
    except client.exceptions.ResourceNotFoundException:
        print(f"✓ Table '{table_name}' does not exist")
        return False
    except Exception as e:
        print(f"✗ Error deleting table: {e}")
        raise


def reset_checkpoint_table():
    """
    Reset the checkpoint table by deleting and recreating it.
    This is useful for testing or starting fresh.

    Returns:
        bool: True if successful
    """
    print("=" * 60)
    print("RESETTING DYNAMODB TABLE")
    print("=" * 60)

    delete_checkpoint_table()
    create_checkpoint_table()

    print("\n" + "=" * 60)
    print("RESET COMPLETE")
    print("=" * 60)
    return True


def main():
    """
    Main entry point for the script.
    Supports command-line arguments for different operations.
    """
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "create":
            create_checkpoint_table()
        elif command == "delete":
            delete_checkpoint_table()
        elif command == "reset":
            reset_checkpoint_table()
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python init_db.py create  - Create the checkpoint table")
            print("  python init_db.py delete  - Delete the checkpoint table")
            print("  python init_db.py reset   - Delete and recreate the table")
            sys.exit(1)
    else:
        # Default action: create table
        create_checkpoint_table()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
