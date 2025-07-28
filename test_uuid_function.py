#!/usr/bin/env python3
"""
Test script for the reusable UUID generation function
"""

import requests
import json
from datetime import datetime

# Configuration - update this to your server's URL
API_BASE_URL = "http://localhost:5000"

def test_uuid_generation_function():
    """Test the reusable UUID generation function via the API endpoint"""
    print("🧪 Testing UUID Generation Function")
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/get_new_uuid", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            generated_uuid = data.get('uuid')
            print(f"✅ UUID generated successfully!")
            print(f"Generated UUID: {generated_uuid}")
            return generated_uuid
        else:
            print("❌ Failed to generate UUID")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_add_project_with_uuid_function():
    """Test adding a project using the UUID generation function"""
    print("\n🧪 Testing Add Project with UUID Generation Function")
    
    # Test data (without UUID - it should be generated automatically)
    test_project_name = f"Test Project UUID Function {datetime.now().strftime('%H:%M:%S')}"
    
    payload = {
        "project_name": test_project_name,
        "user_name": "test_user_uuid_function",
        "date": datetime.now().strftime("%d-%m-%y"),
        "file_location": f"sampleDataset/{test_project_name}",
        "paper_size": "A3 (Portrait)",
        "description": "Test project created using the reusable UUID generation function",
        "areas": [
            {
                "xmin": 100000,
                "ymin": 200000,
                "xmax": 110000,
                "ymax": 210000,
                "scale": "Scale: 1:50000"
            }
        ]
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/add_project", json=payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            data = response.json()
            generated_uuid = data.get('uuid')
            message = data.get('message')
            print(f"✅ Project added successfully!")
            print(f"Generated UUID: {generated_uuid}")
            print(f"Message: {message}")
            return generated_uuid
        else:
            print("❌ Failed to add project")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_multiple_uuid_generation():
    """Test generating multiple UUIDs to ensure they're unique"""
    print("\n🧪 Testing Multiple UUID Generation (Uniqueness)")
    
    uuids = set()
    num_tests = 5
    
    for i in range(num_tests):
        print(f"\nGenerating UUID {i+1}/{num_tests}...")
        uuid = test_uuid_generation_function()
        
        if uuid:
            if uuid in uuids:
                print(f"❌ Duplicate UUID detected: {uuid}")
                return False
            else:
                uuids.add(uuid)
                print(f"✅ UUID {uuid} is unique")
        else:
            print("❌ Failed to generate UUID")
            return False
    
    print(f"\n✅ All {num_tests} UUIDs are unique!")
    print(f"Generated UUIDs: {sorted(uuids)}")
    return True

def test_uuid_format():
    """Test that generated UUIDs have the correct format"""
    print("\n🧪 Testing UUID Format")
    
    uuid = test_uuid_generation_function()
    
    if uuid:
        # Check if UUID follows the standard UUID v4 format
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        
        if re.match(uuid_pattern, uuid.lower()):
            print("✅ UUID format is valid (UUID v4)")
            print(f"UUID: {uuid}")
            return True
        else:
            print(f"❌ UUID format is invalid: {uuid}")
            return False
    else:
        print("❌ Failed to generate UUID for format testing")
        return False

def main():
    print("🚀 Starting UUID Function Tests")
    print("=" * 50)
    
    # Test 1: Basic UUID generation function
    print("\n1. Testing basic UUID generation function...")
    if not test_uuid_generation_function():
        print("❌ Basic UUID generation function test failed")
        return
    
    # Test 2: Add project using UUID generation function
    print("\n2. Testing add project with UUID generation function...")
    project_uuid = test_add_project_with_uuid_function()
    if not project_uuid:
        print("❌ Add project with UUID generation function test failed")
        return
    
    # Test 3: Multiple UUID generation (uniqueness)
    print("\n3. Testing multiple UUID generation...")
    if not test_multiple_uuid_generation():
        print("❌ Multiple UUID generation test failed")
        return
    
    # Test 4: UUID format validation
    print("\n4. Testing UUID format...")
    if not test_uuid_format():
        print("❌ UUID format test failed")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! The reusable UUID generation function is working correctly.")
    print(f"✅ Project UUID from add_project: {project_uuid}")

if __name__ == "__main__":
    main() 