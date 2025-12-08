import pytest
from app.config import settings
from app.database import get_dynamodb_resource


@pytest.mark.asyncio
async def test_dynamodb_connection_and_table_presence():
    """
    Test that DynamoDB connection works and the configured table exists.
    """
    # Get DynamoDB resource
    dynamodb_resource = get_dynamodb_resource()

    # List all tables - this should succeed without raising an exception
    try:
        # Get the DynamoDB client from the resource to list tables
        client = dynamodb_resource.meta.client
        response = client.list_tables()
        table_names = response['TableNames']
    except Exception as e:
        pytest.fail(f"Failed to connect to DynamoDB or list tables: {e}")

    # Assert that the configured table name exists in the list of tables
    expected_table_name = settings.table_name
    assert expected_table_name in table_names, f"Table '{expected_table_name}' not found in DynamoDB. Available tables: {table_names}"
