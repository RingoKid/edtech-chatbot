#!/usr/bin/env python3
"""
Test script to directly test the admin API endpoint
"""
import os
import sys
import asyncio
import requests

# Set environment variables
os.environ['APP_ENV'] = 'local'
os.environ['DYNAMODB_TABLE_NAME'] = 'EdTechChatbotTable'

# Add current directory to path
sys.path.append('.')

from app.routers.admin import get_all_forms

async def test_direct():
    print("=== Testing Admin Router Directly ===")
    result = await get_all_forms()
    print(f"Direct call result: {result.total_count} forms")
    if result.forms:
        print(f"First form: {result.forms[0].title}")

def test_api():
    print("\n=== Testing API Endpoint ===")
    try:
        response = requests.get('http://localhost:8000/api/v1/forms')
        print(f"API Status Code: {response.status_code}")
        print(f"API Response: {response.json()}")
    except Exception as e:
        print(f"API Error: {e}")

async def main():
    await test_direct()
    test_api()

if __name__ == "__main__":
    asyncio.run(main())
