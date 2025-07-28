import requests

# Test the UUID endpoint
try:
    print("Testing UUID endpoint...")
    response = requests.post("http://127.0.0.1:5002/api/get_new_uuid")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Success! UUID endpoint is working.")
        data = response.json()
        print(f"Generated UUID: {data.get('uuid')}")
    else:
        print("❌ Endpoint returned an error")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Also test a known working endpoint
try:
    print("\nTesting main page...")
    response = requests.get("http://127.0.0.1:5002/")
    print(f"Main page status: {response.status_code}")
    
except Exception as e:
    print(f"❌ Error accessing main page: {e}") 