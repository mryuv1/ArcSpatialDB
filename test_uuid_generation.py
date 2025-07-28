#!/usr/bin/env python3
"""
Test script for the new UUID generation endpoint
"""

import requests
import json
import time

# Configuration - update this to your server's URL
API_BASE_URL = "http://localhost:5000"  # Change to your server URL

def test_get_new_uuid():
    """Test the new UUID generation endpoint"""
    print("🧪 Testing API: Get New UUID")
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/get_new_uuid", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            new_uuid = data.get('uuid')
            message = data.get('message')
            print(f"✅ UUID generated successfully!")
            print(f"Generated UUID: {new_uuid}")
            print(f"Message: {message}")
            return new_uuid
        else:
            print("❌ Failed to generate UUID")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_multiple_uuids():
    """Test generating multiple UUIDs to ensure they're unique"""
    print("\n🧪 Testing Multiple UUID Generation")
    
    uuids = set()
    num_tests = 5
    
    for i in range(num_tests):
        print(f"\n--- Test {i+1}/{num_tests} ---")
        new_uuid = test_get_new_uuid()
        
        if new_uuid:
            if new_uuid in uuids:
                print(f"❌ Duplicate UUID detected: {new_uuid}")
                return False
            else:
                uuids.add(new_uuid)
                print(f"✅ UUID {new_uuid} is unique")
        else:
            print("❌ Failed to generate UUID")
            return False
        
        # Small delay between requests
        time.sleep(0.5)
    
    print(f"\n✅ All {num_tests} UUIDs are unique!")
    print(f"Generated UUIDs: {sorted(uuids)}")
    return True

def test_uuid_format():
    """Test that generated UUIDs have the correct format"""
    print("\n🧪 Testing UUID Format")
    
    new_uuid = test_get_new_uuid()
    
    if new_uuid:
        # Check if UUID is exactly 8 characters long
        if len(new_uuid) == 8:
            print("✅ UUID length is correct (8 characters)")
        else:
            print(f"❌ UUID length is incorrect: {len(new_uuid)} characters (expected 8)")
            return False
        
        # Check if UUID contains only hexadecimal characters
        if all(c in '0123456789abcdef' for c in new_uuid.lower()):
            print("✅ UUID contains only hexadecimal characters")
        else:
            print(f"❌ UUID contains invalid characters: {new_uuid}")
            return False
        
        print(f"✅ UUID format is valid: {new_uuid}")
        return True
    else:
        print("❌ Failed to generate UUID for format testing")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting UUID Generation Tests")
    print("=" * 50)
    
    # Test 1: Basic UUID generation
    print("\n1. Testing basic UUID generation...")
    if not test_get_new_uuid():
        print("❌ Basic UUID generation test failed")
        return
    
    # Test 2: Multiple UUID generation (uniqueness)
    print("\n2. Testing multiple UUID generation...")
    if not test_multiple_uuids():
        print("❌ Multiple UUID generation test failed")
        return
    
    # Test 3: UUID format validation
    print("\n3. Testing UUID format...")
    if not test_uuid_format():
        print("❌ UUID format test failed")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! UUID generation endpoint is working correctly.")
    print("=" * 50)

if __name__ == "__main__":
    main() 