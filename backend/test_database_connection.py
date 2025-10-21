#!/usr/bin/env python3
"""
Test script to debug database connection and form retrieval issues.
"""
import os
import sys
import asyncio

# Set environment variables first
os.environ['APP_ENV'] = 'local'
os.environ['DYNAMODB_TABLE_NAME'] = 'EdTechChatbotTable'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db, test_connection, initialize_database
from app.service.form_retrieval_service import form_retrieval_service
from app.routers.admin import get_all_forms

async def test_database_and_forms():
    print("=== Database and Forms Debug Test ===")
    
    # Test 1: Environment variables
    print(f"APP_ENV: {os.environ.get('APP_ENV')}")
    print(f"DYNAMODB_TABLE_NAME: {os.environ.get('DYNAMODB_TABLE_NAME')}")
    
    # Test 2: Database initialization
    print("\n--- Database Initialization ---")
    init_result = initialize_database()
    print(f"Database initialization result: {init_result}")
    
    # Test 3: Database connection
    print("\n--- Database Connection ---")
    connection_test = test_connection()
    print(f"Database connection test: {connection_test}")
    
    # Test 4: Get database table
    print("\n--- Database Table ---")
    table = get_db()
    print(f"Table type: {type(table).__name__}")
    
    if hasattr(table, 'items'):
        print(f"Items count: {len(table.items)}")
        if hasattr(table, 'indexes') and 'CategoryIndex' in table.indexes:
            print(f"CategoryIndex keys: {list(table.indexes['CategoryIndex'].keys())}")
            if 'A' in table.indexes['CategoryIndex']:
                print(f"Category A items: {len(table.indexes['CategoryIndex']['A'])}")
                if table.indexes['CategoryIndex']['A']:
                    print(f"First A item title: {table.indexes['CategoryIndex']['A'][0].get('title')}")
    else:
        print("Table does not have 'items' attribute")
    
    # Test 5: Form retrieval service
    print("\n--- Form Retrieval Service ---")
    try:
        forms_from_service = await form_retrieval_service.get_forms_by_domain("all")
        print(f"Forms from service: {len(forms_from_service)}")
        if forms_from_service:
            print(f"First form title: {forms_from_service[0].get('title')}")
    except Exception as e:
        print(f"Error in form retrieval service: {e}")
    
    # Test 6: Admin router
    print("\n--- Admin Router ---")
    try:
        admin_response = await get_all_forms()
        print(f"Admin router forms count: {len(admin_response.forms)}")
        if admin_response.forms:
            print(f"First admin form title: {admin_response.forms[0].title}")
    except Exception as e:
        print(f"Error in admin router: {e}")

if __name__ == "__main__":
    asyncio.run(test_database_and_forms())
