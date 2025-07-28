#!/usr/bin/env python3
"""
Test script for the db_manager.pyt download functionality
"""

import requests
import os

# Configuration - update this to your server's URL
API_BASE_URL = "http://localhost:5000"  # or 5002 for backend

def test_download_db_manager():
    """Test downloading the db_manager.pyt file"""
    print("🧪 Testing API: Download db_manager.pyt")
    
    try:
        response = requests.get(f"{API_BASE_URL}/download/db_manager.pyt", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Check if the response has the correct content type
            content_type = response.headers.get('content-type', '')
            print(f"Content-Type: {content_type}")
            
            # Check if the response has the correct content disposition
            content_disposition = response.headers.get('content-disposition', '')
            print(f"Content-Disposition: {content_disposition}")
            
            # Check the file size
            content_length = len(response.content)
            print(f"File Size: {content_length} bytes")
            
            # Save the file locally for testing
            test_filename = "test_downloaded_db_manager.pyt"
            with open(test_filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Download successful!")
            print(f"✅ File saved as: {test_filename}")
            print(f"✅ File size: {content_length} bytes")
            
            # Check if the file contains expected content
            with open(test_filename, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'class ExportLayoutTool' in content:
                    print("✅ File contains expected ArcGIS Pro tool content")
                else:
                    print("⚠️  File content may not be as expected")
            
            # Clean up test file
            os.remove(test_filename)
            print(f"✅ Test file cleaned up: {test_filename}")
            
            return True
        else:
            print(f"❌ Download failed with status code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_download_endpoint_availability():
    """Test if the download endpoint is available"""
    print("\n🧪 Testing API: Download endpoint availability")
    
    try:
        response = requests.head(f"{API_BASE_URL}/download/db_manager.pyt", timeout=5)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 405]:  # 405 is OK for HEAD request
            print("✅ Download endpoint is available")
            return True
        else:
            print(f"❌ Download endpoint returned status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    print("🚀 Starting Download Functionality Tests")
    print("=" * 50)
    
    # Test 1: Check if endpoint is available
    print("\n1. Testing download endpoint availability...")
    if not test_download_endpoint_availability():
        print("❌ Download endpoint availability test failed")
        return
    
    # Test 2: Download the file
    print("\n2. Testing file download...")
    if not test_download_db_manager():
        print("❌ File download test failed")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All download tests passed! The download functionality is working correctly.")

if __name__ == "__main__":
    main() 