#!/usr/bin/env python3
"""
Test the API endpoint directly to debug the 401 error
"""

import requests
import json

def test_api_endpoint():
    print("🌐 Testing API Endpoint")
    print("=" * 50)
    
    # Test credentials
    email = "admin@mediremind.test"
    password = "TestAdmin123!"
    
    # Test with HTTP (not HTTPS)
    url = "http://127.0.0.1:8000/api/auth/login/"
    
    print(f"Testing URL: {url}")
    print(f"Credentials: {email}")
    
    try:
        response = requests.post(
            url,
            json={
                'email': email,
                'password': password
            },
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Test Script'
            },
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            print("✅ Authentication successful!")
            data = response.json()
            if 'token' in data:
                print(f"Token: {data['token'][:20]}...")
        elif response.status_code == 401:
            print("❌ Authentication failed (401 Unauthorized)")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print("No JSON error details available")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_api_endpoint()