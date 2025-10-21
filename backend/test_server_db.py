#!/usr/bin/env python3
"""
Test script to check what database the server is actually using.
"""
import os
import sys
import asyncio

# Set environment variables first
os.environ['APP_ENV'] = 'local'
os.environ['DYNAMODB_TABLE_NAME'] = 'EdTechChatbotTable'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db, test_connection
from app.service.form_retrieval_service import form_retrieval_service

async def test_server_database():
    print("=== Server Database Test ===")
    
    # Test 1: Environment variables
    print(f"APP_ENV: {os.environ.get('APP_ENV')}")
    print(f"DYNAMODB_TABLE_NAME: {os.environ.get('DYNAMODB_TABLE_NAME')}")
    
    # Test 2: Database connection
    print(f"\nDatabase connection test: {test_connection()}")
    
    # Test 3: Get database table
    table = get_db()
    print(f"Table type: {type(table).__name__}")
    
    if hasattr(table, 'items'):
        print(f"Items count: {len(table.items)}")
        if hasattr(table, 'indexes') and 'CategoryIndex' in table.indexes:
            print(f"CategoryIndex keys: {list(table.indexes['CategoryIndex'].keys())}")
    else:
        print("Table does not have 'items' attribute")
    
    # Test 4: Form retrieval service
    print(f"\n--- Form Retrieval Service ---")
    try:
        forms_from_service = await form_retrieval_service.get_forms_by_domain("all")
        print(f"Forms from service: {len(forms_from_service)}")
        if forms_from_service:
            print(f"First form title: {forms_from_service[0].get('title')}")
    except Exception as e:
        print(f"Error in form retrieval service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_server_database())
