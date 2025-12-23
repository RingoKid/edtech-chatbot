"""
Test that DynamoDB table structure matches expected schema.
Uses DynamoDB Local for testing.
"""

import pytest
import boto3
from botocore.exceptions import ClientError
from app.db_schema import MAIN_TABLE_SCHEMA, CHECKPOINT_TABLE_SCHEMA
from app.config import settings


@pytest.fixture(scope="module")
def dynamodb_client():
    """Connect to DynamoDB Local."""
    return boto3.client(
        'dynamodb',
        endpoint_url=settings.dynamodb_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )


class TestMainTableSchema:
    """Tests for main table schema validation."""

    def test_main_table_exists(self, dynamodb_client):
        """Verify main table exists in DynamoDB Local."""
        try:
            response = dynamodb_client.describe_table(TableName=settings.table_name)
            assert response['Table']['TableStatus'] == 'ACTIVE'
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip(f"Table {settings.table_name} not found. Run init_db.py first.")
            raise

    def test_main_table_key_schema_matches(self, dynamodb_client):
        """Verify main table KeySchema matches expected schema."""
        try:
            response = dynamodb_client.describe_table(TableName=settings.table_name)
            actual_key_schema = response['Table']['KeySchema']

            assert actual_key_schema == MAIN_TABLE_SCHEMA['KeySchema'], \
                f"KeySchema mismatch. Expected: {MAIN_TABLE_SCHEMA['KeySchema']}, Got: {actual_key_schema}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip(f"Table {settings.table_name} not found. Run init_db.py first.")
            raise

    def test_main_table_has_gsi1(self, dynamodb_client):
        """Verify main table has GSI1 index."""
        try:
            response = dynamodb_client.describe_table(TableName=settings.table_name)
            gsi_list = response['Table'].get('GlobalSecondaryIndexes', [])
            gsi_names = [gsi['IndexName'] for gsi in gsi_list]

            assert 'GSI1' in gsi_names, f"GSI1 not found. Available GSIs: {gsi_names}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip(f"Table {settings.table_name} not found. Run init_db.py first.")
            raise

    def test_main_table_gsi1_key_schema_matches(self, dynamodb_client):
        """Verify GSI1 KeySchema matches expected schema."""
        try:
            response = dynamodb_client.describe_table(TableName=settings.table_name)
            gsi_list = response['Table'].get('GlobalSecondaryIndexes', [])

            gsi1 = next((gsi for gsi in gsi_list if gsi['IndexName'] == 'GSI1'), None)
            assert gsi1 is not None, "GSI1 not found"

            expected_gsi1_key_schema = MAIN_TABLE_SCHEMA['GlobalSecondaryIndexes'][0]['KeySchema']
            assert gsi1['KeySchema'] == expected_gsi1_key_schema, \
                f"GSI1 KeySchema mismatch. Expected: {expected_gsi1_key_schema}, Got: {gsi1['KeySchema']}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip(f"Table {settings.table_name} not found. Run init_db.py first.")
            raise


class TestCheckpointTableSchema:
    """Tests for checkpoint table schema validation."""

    def test_checkpoint_table_exists(self, dynamodb_client):
        """Verify checkpoint table exists in DynamoDB Local."""
        try:
            response = dynamodb_client.describe_table(TableName=settings.checkpoint_table_name)
            assert response['Table']['TableStatus'] == 'ACTIVE'
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip(f"Table {settings.checkpoint_table_name} not found. Run init_db.py first.")
            raise

    def test_checkpoint_table_key_schema_matches(self, dynamodb_client):
        """Verify checkpoint table KeySchema matches expected schema."""
        try:
            response = dynamodb_client.describe_table(TableName=settings.checkpoint_table_name)
            actual_key_schema = response['Table']['KeySchema']

            assert actual_key_schema == CHECKPOINT_TABLE_SCHEMA['KeySchema'], \
                f"KeySchema mismatch. Expected: {CHECKPOINT_TABLE_SCHEMA['KeySchema']}, Got: {actual_key_schema}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip(f"Table {settings.checkpoint_table_name} not found. Run init_db.py first.")
            raise

    def test_checkpoint_table_has_no_gsi(self, dynamodb_client):
        """Verify checkpoint table has no GSI (simple table)."""
        try:
            response = dynamodb_client.describe_table(TableName=settings.checkpoint_table_name)
            gsi_list = response['Table'].get('GlobalSecondaryIndexes', [])

            assert len(gsi_list) == 0, f"Checkpoint table should have no GSI, found: {gsi_list}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip(f"Table {settings.checkpoint_table_name} not found. Run init_db.py first.")
            raise


class TestSchemaConsistency:
    """Tests for schema consistency between db_schema.py and actual tables."""

    def test_main_table_attribute_definitions_match(self, dynamodb_client):
        """Verify all attribute definitions are present."""
        try:
            response = dynamodb_client.describe_table(TableName=settings.table_name)
            actual_attrs = {attr['AttributeName']: attr['AttributeType']
                          for attr in response['Table']['AttributeDefinitions']}
            expected_attrs = {attr['AttributeName']: attr['AttributeType']
                            for attr in MAIN_TABLE_SCHEMA['AttributeDefinitions']}

            # Check all expected attributes exist
            for attr_name, attr_type in expected_attrs.items():
                assert attr_name in actual_attrs, f"Missing attribute: {attr_name}"
                assert actual_attrs[attr_name] == attr_type, \
                    f"Type mismatch for {attr_name}. Expected: {attr_type}, Got: {actual_attrs[attr_name]}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip(f"Table {settings.table_name} not found. Run init_db.py first.")
            raise

    def test_checkpoint_table_attribute_definitions_match(self, dynamodb_client):
        """Verify checkpoint table attribute definitions match."""
        try:
            response = dynamodb_client.describe_table(TableName=settings.checkpoint_table_name)
            actual_attrs = {attr['AttributeName']: attr['AttributeType']
                          for attr in response['Table']['AttributeDefinitions']}
            expected_attrs = {attr['AttributeName']: attr['AttributeType']
                            for attr in CHECKPOINT_TABLE_SCHEMA['AttributeDefinitions']}

            # Check all expected attributes exist
            for attr_name, attr_type in expected_attrs.items():
                assert attr_name in actual_attrs, f"Missing attribute: {attr_name}"
                assert actual_attrs[attr_name] == attr_type, \
                    f"Type mismatch for {attr_name}. Expected: {attr_type}, Got: {actual_attrs[attr_name]}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pytest.skip(f"Table {settings.checkpoint_table_name} not found. Run init_db.py first.")
            raise
