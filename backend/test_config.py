#!/usr/bin/env python3
"""
Test script to verify the environment-aware configuration is working correctly.
"""

import os
import sys
sys.path.append('/Users/rifat/Documents/Work/edtech/edtech-chatbot/backend')

from app.config import settings, AppEnv

def test_configuration():
    """Test the configuration loading for different environments."""
    
    print("=" * 60)
    print("ENVIRONMENT-AWARE CONFIGURATION TEST")
    print("=" * 60)
    
    print(f"Current APP_ENV from OS: {os.getenv('APP_ENV', 'not set')}")
    print(f"Loaded app_env setting: {settings.app_env}")
    print(f"AWS Access Key ID: {settings.aws_access_key_id}")
    print(f"AWS Secret Access Key: {settings.aws_secret_access_key[:10] + '...' if settings.aws_secret_access_key else 'None'}")
    print(f"AWS Region: {settings.aws_region}")
    print(f"DynamoDB Table Name: {settings.dynamodb_table_name}")
    print(f"DynamoDB Endpoint URL: {settings.dynamodb_endpoint_url}")
    print(f"Generated Table Name: {settings.table_name}")
    
    print("\n" + "=" * 60)
    print("ENVIRONMENT-SPECIFIC BEHAVIOR")
    print("=" * 60)
    
    if settings.app_env == AppEnv.LOCAL:
        print("✓ LOCAL environment detected")
        print(f"  - Will use endpoint URL: {settings.dynamodb_endpoint_url}")
        print(f"  - Will use dummy credentials: {settings.aws_access_key_id}")
    elif settings.app_env == AppEnv.SANDBOX:
        print("✓ SANDBOX environment detected")
        print("  - Will use AWS DynamoDB (no endpoint URL)")
        print(f"  - Will use provided credentials: {settings.aws_access_key_id}")
    else:
        print("✓ PRODUCTION environment detected")
        print("  - Will use AWS DynamoDB with IAM role/profile")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_configuration()