#!/usr/bin/env python3
"""
Debug script to test form retrieval and admin API
"""
import os
import sys
import asyncio

# Set environment variables
os.environ['APP_ENV'] = 'local'
os.environ['DYNAMODB_TABLE_NAME'] = 'EdTechChatbotTable'

# Add current directory to path
sys.path.append('.')

from app.database import get_db, test_connection
from app.service.form_retrieval_service import form_retrieval_service
from app.routers.admin import get_all_forms

async def main():
    print("=== Debug Form Retrieval ===")
    
    # Test database connection
    print(f"Database connection test: {test_connection()}")
    
    # Get database table
    table = get_db()
    print(f"Table type: {type(table).__name__}")
    
    if hasattr(table, 'items'):
        print(f"Total items in table: {len(table.items)}")
        print(f"CategoryIndex keys: {list(table.indexes['CategoryIndex'].keys())}")
        
        # Test CategoryIndex for 'A'
        category_a_items = table.indexes['CategoryIndex'].get('A', [])
        print(f"Category A items: {len(category_a_items)}")
        if category_a_items:
            print(f"First A item: {category_a_items[0].get('title', 'No title')}")
    
    # Test form retrieval service
    print("\n=== Testing Form Retrieval Service ===")
    forms = await form_retrieval_service.get_forms_by_domain('all')
    print(f"Forms found by service: {len(forms)}")
    if forms:
        print(f"First form title: {forms[0].get('title', 'No title')}")
    
    # Test admin router
    print("\n=== Testing Admin Router ===")
    admin_result = await get_all_forms()
    print(f"Admin router forms count: {admin_result.total_count}")
    if admin_result.forms:
        print(f"First admin form title: {admin_result.forms[0].title}")

if __name__ == "__main__":
    asyncio.run(main())
