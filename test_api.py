#!/usr/bin/env python3
"""
Test script for ArcSpatialDB API endpoints
Run this script to test the API functionality
"""

import requests
import json
import uuid
from datetime import datetime

# Configuration - update this to your VM's URL
API_BASE_URL = "http://localhost:5000"  # Change to your VM URL

def test_add_project():
    """Test adding a project via API"""
    print("🧪 Testing API: Add Project")
    
    # Generate test data
    test_uuid = str(uuid.uuid4())[:8]
    test_project_name = f"Test Project {datetime.now().strftime('%H:%M:%S')}"
    
    payload = {
        "uuid": test_uuid,
        "project_name": test_project_name,
        "user_name": "test_user",
        "date": datetime.now().strftime("%d-%m-%y"),
        "file_location": f"sampleDataset/{test_project_name}",
        "paper_size": "A3 (Portrait)",
        "description": "Test project created via API",
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
            print("✅ Project added successfully!")
            return test_uuid
        else:
            print("❌ Failed to add project")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_get_project(uuid):
    """Test retrieving a project via API"""
    if not uuid:
        print("❌ No UUID provided for get test")
        return
    
    print(f"\n🧪 Testing API: Get Project {uuid}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/get_project/{uuid}", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            project_data = response.json()
            print("✅ Project retrieved successfully!")
            print(f"Project Name: {project_data.get('project_name')}")
            print(f"User: {project_data.get('user_name')}")
            print(f"Areas: {len(project_data.get('areas', []))}")
        else:
            print(f"❌ Failed to get project: {response.json()}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_invalid_request():
    """Test API with invalid data"""
    print("\n🧪 Testing API: Invalid Request")
    
    # Missing required fields
    invalid_payload = {
        "project_name": "Invalid Project"
        # Missing uuid, user_name, etc.
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/add_project", json=invalid_payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400:
            print("✅ API correctly rejected invalid request!")
        else:
            print("❌ API should have rejected invalid request")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def main():
    """Run all API tests"""
    print("🚀 Starting ArcSpatialDB API Tests")
    print(f"API Base URL: {API_BASE_URL}")
    print("=" * 50)
    
    # Test 1: Add project
    test_uuid = test_add_project()
    
    # Test 2: Get project
    test_get_project(test_uuid)
    
    # Test 3: Invalid request
    test_invalid_request()
    
    print("\n" + "=" * 50)
    print("🏁 API Tests Complete")

if __name__ == "__main__":
    main() 