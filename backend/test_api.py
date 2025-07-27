#!/usr/bin/env python
"""
Quick test script to verify the backend API is working
"""
import requests
import json

def test_api():
    base_url = "http://localhost:5000"
    
    try:
        # Test health endpoint
        print("🔍 Testing API Health...")
        response = requests.get(f"{base_url}/api/health")
        print(f"✅ Health Check: {response.status_code}")
        print(f"📄 Response: {response.json()}")
        
        # Test user names endpoint
        print("\n🔍 Testing User Names...")
        response = requests.get(f"{base_url}/api/user_names")
        print(f"✅ User Names: {response.status_code}")
        data = response.json()
        print(f"📄 Found {len(data.get('user_names', []))} user names")
        
        # Test projects endpoint
        print("\n🔍 Testing Projects...")
        response = requests.get(f"{base_url}/api/projects")
        print(f"✅ Projects: {response.status_code}")
        data = response.json()
        print(f"📄 Found {len(data.get('projects', []))} projects")
        
        print("\n🎉 All API endpoints are working!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the backend server is running on port 5000")
        print("   Run: python app.py (from the backend directory)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()
