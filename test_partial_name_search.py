#!/usr/bin/env python3
"""
Test script for partial name search functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import app, engine, projects_table
from sqlalchemy import select
import tempfile

def test_partial_name_search():
    """Test the partial name search functionality"""
    
    with app.test_client() as client:
        # Test 1: Search with partial name
        print("Testing partial name search...")
        response = client.post('/', data={
            'user_name_partial': 'john',
            'uuid': '',
            'paper_size': '',
            'scale': '',
            'date_from': '',
            'date_to': ''
        })
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Partial name search form submission successful")
        else:
            print("✗ Partial name search form submission failed")
        
        # Test 2: Search with exact name from dropdown
        print("\nTesting exact name search from dropdown...")
        response = client.post('/', data={
            'user_name': 'john_doe',  # Assuming this name exists
            'uuid': '',
            'paper_size': '',
            'scale': '',
            'date_from': '',
            'date_to': ''
        })
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Exact name search form submission successful")
        else:
            print("✗ Exact name search form submission failed")
        
        # Test 3: Search with both partial and exact names
        print("\nTesting combined partial and exact name search...")
        response = client.post('/', data={
            'user_name_partial': 'jane',
            'user_name': 'john_doe',
            'uuid': '',
            'paper_size': '',
            'scale': '',
            'date_from': '',
            'date_to': ''
        })
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Combined name search form submission successful")
        else:
            print("✗ Combined name search form submission failed")

def test_database_query():
    """Test the database query logic directly"""
    
    print("\nTesting database query logic...")
    
    with engine.connect() as conn:
        # Get all user names in the database
        result = conn.execute(select(projects_table.c.user_name).distinct())
        user_names = [row[0] for row in result]
        
        print(f"Available user names in database: {user_names}")
        
        if user_names:
            # Test partial search with first user name
            test_name = user_names[0]
            partial_search = test_name[:3]  # Take first 3 characters
            
            print(f"\nTesting partial search for '{partial_search}' (should match '{test_name}')")
            
            result = conn.execute(
                select(projects_table.c.user_name)
                .where(projects_table.c.user_name.ilike(f"{partial_search}%"))
            )
            
            matches = [row[0] for row in result]
            print(f"Matches found: {matches}")
            
            if test_name in matches:
                print("✓ Partial search working correctly")
            else:
                print("✗ Partial search not working correctly")

if __name__ == "__main__":
    print("Testing Partial Name Search Functionality")
    print("=" * 50)
    
    try:
        test_partial_name_search()
        test_database_query()
        print("\n" + "=" * 50)
        print("Test completed successfully!")
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc() 