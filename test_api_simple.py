#!/usr/bin/env python3
"""
Simple API test using urllib to avoid SSL issues
"""

import urllib.request
import urllib.parse
import json

def test_api_simple():
    print("🌐 Testing API Endpoint with urllib")
    print("=" * 50)
    
    # Test credentials
    email = "admin@mediremind.test"
    password = "TestAdmin123!"
    
    # Test with HTTP
    url = "http://127.0.0.1:8000/api/auth/login/"
    
    print(f"Testing URL: {url}")
    print(f"Credentials: {email}")
    
    try:
        # Prepare data
        data = {
            'email': email,
            'password': password
        }
        
        # Convert to JSON and encode
        json_data = json.dumps(data).encode('utf-8')
        
        # Create request
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Test Script'
            },
            method='POST'
        )
        
        # Make request
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            response_data = response.read().decode('utf-8')
            
            print(f"\nResponse Status: {status_code}")
            print(f"Response Content: {response_data}")
            
            if status_code == 200:
                print("✅ Authentication successful!")
                try:
                    data = json.loads(response_data)
                    if 'token' in data:
                        print(f"Token: {data['token'][:20]}...")
                        print(f"User: {data.get('user', {}).get('email', 'N/A')}")
                except json.JSONDecodeError:
                    print("Could not parse JSON response")
            else:
                print(f"❌ Authentication failed ({status_code})")
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        try:
            error_response = e.read().decode('utf-8')
            print(f"Error response: {error_response}")
        except:
            print("Could not read error response")
            
    except urllib.error.URLError as e:
        print(f"❌ URL Error: {e.reason}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_api_simple()