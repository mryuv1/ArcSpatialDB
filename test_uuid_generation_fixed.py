#!/usr/bin/env python3
"""
Test script for the updated add_project endpoint with automatic UUID generation
"""

import requests
import json
from datetime import datetime

# Configuration - update this to your server's URL
API_BASE_URL = "http://localhost:5000"  # or 5002 for backend

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
        "description": "Test project created via API with auto-generated UUID",
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

def test_get_new_uuid_endpoint():
    """Test the separate UUID generation endpoint"""
    print("\n🧪 Testing API: Get New UUID Endpoint")
    
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
    print("🚀 Starting UUID Generation Tests")
    print("=" * 50)
    
    # Test 1: Add project without UUID (should generate one automatically)
    print("\n1. Testing add project without UUID...")
    generated_uuid = test_add_project_without_uuid()
    if not generated_uuid:
        print("❌ Add project without UUID test failed")
        return
    
    # Test 2: Get project with generated UUID
    print("\n2. Testing retrieve project with generated UUID...")
    if not test_get_project_with_generated_uuid(generated_uuid):
        print("❌ Get project with generated UUID test failed")
        return
    
    # Test 3: Test separate UUID generation endpoint
    print("\n3. Testing separate UUID generation endpoint...")
    separate_uuid = test_get_new_uuid_endpoint()
    if not separate_uuid:
        print("❌ Separate UUID generation test failed")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! UUID generation is working correctly.")
    print(f"✅ Auto-generated UUID from add_project: {generated_uuid}")
    print(f"✅ Separately generated UUID: {separate_uuid}")

if __name__ == "__main__":
    main() 