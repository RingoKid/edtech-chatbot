#!/usr/bin/env python3
"""
Setup script to configure AWS DynamoDB for the EdTech Chatbot.
This script will help you set up AWS credentials and create the DynamoDB table.
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import sys

def setup_aws_credentials():
    """Setup AWS credentials interactively."""
    print("AWS DynamoDB Setup for EdTech Chatbot")
    print("=" * 50)
    
    # Check if credentials are already configured
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials:
            print("✅ AWS credentials found!")
            return True
    except NoCredentialsError:
        pass
    
    print("\nTo use AWS DynamoDB, you need to configure AWS credentials.")
    print("You can do this in several ways:")
    print("\n1. AWS CLI: Run 'aws configure' and enter your credentials")
    print("2. Environment Variables: Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
    print("3. AWS Credentials File: ~/.aws/credentials")
    print("4. IAM Role: If running on EC2")
    
    print("\nFor this setup, we'll use environment variables.")
    
    access_key = input("\nEnter your AWS Access Key ID: ").strip()
    secret_key = input("Enter your AWS Secret Access Key: ").strip()
    region = input("Enter your AWS Region (default: us-east-1): ").strip() or "us-east-1"
    
    if not access_key or not secret_key:
        print("❌ Access key and secret key are required!")
        return False
    
    # Set environment variables
    os.environ['AWS_ACCESS_KEY_ID'] = access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
    os.environ['AWS_REGION'] = region
    os.environ['APP_ENV'] = 'sandbox'
    os.environ['DYNAMODB_TABLE_NAME'] = 'EdTechChatbotTable'
    
    print(f"\n✅ Environment variables set for region: {region}")
    return True

def test_dynamodb_connection():
    """Test DynamoDB connection."""
    try:
        dynamodb = boto3.resource('dynamodb')
        # Try to list tables to test connection
        client = boto3.client('dynamodb')
        response = client.list_tables()
        print("✅ DynamoDB connection successful!")
        print(f"Found {len(response['TableNames'])} existing tables")
        return True
    except NoCredentialsError:
        print("❌ AWS credentials not found!")
        return False
    except ClientError as e:
        print(f"❌ AWS DynamoDB error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def create_dynamodb_table():
    """Create the DynamoDB table if it doesn't exist."""
    try:
        table_name = 'EdTechChatbotTable-sandbox'
        dynamodb = boto3.resource('dynamodb')
        
        # Check if table exists
        try:
            table = dynamodb.Table(table_name)
            table.load()
            print(f"✅ Table {table_name} already exists!")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        
        # Create table
        print(f"Creating table: {table_name}")
        table = dynamodb.create_table(
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
        print("Waiting for table to be created...")
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"✅ Table {table_name} created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def main():
    """Main setup function."""
    print("Setting up AWS DynamoDB for EdTech Chatbot...")
    
    # Setup credentials
    if not setup_aws_credentials():
        print("\n❌ Setup failed. Please configure AWS credentials and try again.")
        sys.exit(1)
    
    # Test connection
    if not test_dynamodb_connection():
        print("\n❌ Setup failed. Please check your AWS credentials and try again.")
        sys.exit(1)
    
    # Create table
    if not create_dynamodb_table():
        print("\n❌ Setup failed. Could not create DynamoDB table.")
        sys.exit(1)
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Run: cd backend && python load_forms.py")
    print("2. Run: cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("3. Run: cd frontend && npm run dev")
    print("4. Visit: http://localhost:3000/admin")

if __name__ == '__main__':
    main()


