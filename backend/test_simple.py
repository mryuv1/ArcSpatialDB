#!/usr/bin/env python
"""
Simple manual test using urllib (built-in)
"""
import urllib.request
import urllib.error
import json

def test_backend():
    try:
        print("🔍 Testing backend API at http://localhost:5000...")
        
        # Test health endpoint
        with urllib.request.urlopen('http://localhost:5000/api/health') as response:
            data = json.loads(response.read().decode())
            print(f"✅ Health Check Success: {data}")
            
        # Test user names
        with urllib.request.urlopen('http://localhost:5000/api/user_names') as response:
            data = json.loads(response.read().decode())
            print(f"✅ User Names Success: Found {len(data.get('user_names', []))} users")
            
        print("\n🎉 Backend API is working correctly!")
        print("📡 You can now refresh your frontend at http://localhost:8000")
        
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {e}")
        print("   Make sure backend server is running on port 5000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_backend()
