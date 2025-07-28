#!/usr/bin/env python3
"""
Test script for the modified add_project endpoint (without UUID)
"""

import requests
import json
from datetime import datetime

# Configuration - update this to your server's URL
API_BASE_URL = "http://localhost:5002"

def test_add_project_without_uuid():
    """Test adding a project without providing a UUID"""
    print("🧪 Testing API: Add Project (without UUID)")
    
    # Test data (without UUID)
    test_project_name = f"Test Project {datetime.now().strftime('%H:%M:%S')}"
    
    payload = {
        "project_name": test_project_name,
        "user_name": "test_user",
        "date": datetime.now().strftime("%d-%m-%y"),
        "file_location": f"sampleDataset/{test_project_name}",
        "paper_size": "A3 (Portrait)",
        "description": "Test project created via API without UUID",
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

def test_add_project_missing_fields():
    """Test adding a project with missing required fields"""
    print("\n🧪 Testing API: Add Project (missing required fields)")
    
    # Test data missing required fields
    payload = {
        "project_name": "Test Project Missing Fields",
        # Missing user_name, date, etc.
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/add_project", json=payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400:
            print("✅ Correctly rejected request with missing fields")
            return True
        else:
            print("❌ Should have rejected request with missing fields")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_get_project_with_generated_uuid(uuid):
    """Test retrieving a project using the generated UUID"""
    if not uuid:
        print("❌ No UUID provided for get test")
        return False
    
    print(f"\n🧪 Testing API: Get Project with Generated UUID {uuid}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/get_project/{uuid}", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            project_data = response.json()
            print("✅ Project retrieved successfully!")
            print(f"Project Name: {project_data.get('project_name')}")
            print(f"User: {project_data.get('user_name')}")
            print(f"UUID: {project_data.get('uuid')}")
            print(f"Areas: {len(project_data.get('areas', []))}")
            return True
        else:
            print(f"❌ Failed to get project: {response.json()}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Modified Add Project Tests")
    print("=" * 60)
    
    # Test 1: Add project without UUID
    print("\n1. Testing add project without UUID...")
    generated_uuid = test_add_project_without_uuid()
    if not generated_uuid:
        print("❌ Add project without UUID test failed")
        return
    
    # Test 2: Test missing fields validation
    print("\n2. Testing missing fields validation...")
    if not test_add_project_missing_fields():
        print("❌ Missing fields validation test failed")
        return
    
    # Test 3: Retrieve project with generated UUID
    print("\n3. Testing retrieve project with generated UUID...")
    if not test_get_project_with_generated_uuid(generated_uuid):
        print("❌ Retrieve project test failed")
        return
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed! Modified add_project endpoint is working correctly.")
    print("=" * 60)

if __name__ == "__main__":
    main() 