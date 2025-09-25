#!/usr/bin/env python
"""
Test script to verify login API functionality
"""
import requests
import json

def test_login():
    """Test the login API endpoint"""
    
    # API endpoint
    login_url = "http://localhost:8000/auth/login/"
    
    # Test credentials
    credentials = {
        "email": "dr.sarah.johnson@hospital.com",
        "password": "TestDoctor123!"
    }
    
    try:
        print("Testing login API...")
        print(f"URL: {login_url}")
        print(f"Credentials: {credentials['email']}")
        
        # Make login request
        response = requests.post(
            login_url,
            json=credentials,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("Login successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Test staff API with token
            if 'token' in data:
                test_staff_api(data['token'])
                
        else:
            print("Login failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_staff_api(token):
    """Test the staff API with authentication token"""
    
    staff_url = "http://localhost:8000/accounts/staff/"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("\nTesting staff API...")
        print(f"URL: {staff_url}")
        
        response = requests.get(staff_url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Staff API successful!")
            print(f"Raw response: {json.dumps(data, indent=2)}")
            
            # Handle different response formats
            if isinstance(data, list):
                print(f"Number of staff members: {len(data)}")
                if len(data) > 0:
                    print(f"First staff member: {json.dumps(data[0], indent=2)}")
            elif isinstance(data, dict):
                if 'staff' in data:
                    staff_list = data['staff']
                    total = data.get('total', len(staff_list))
                    print(f"Number of staff members: {len(staff_list)} (total: {total})")
                    if len(staff_list) > 0:
                        print(f"First staff member: {json.dumps(staff_list[0], indent=2)}")
                elif 'results' in data:
                    staff_list = data['results']
                    print(f"Number of staff members: {len(staff_list)}")
                    if len(staff_list) > 0:
                        print(f"First staff member: {json.dumps(staff_list[0], indent=2)}")
                else:
                    print(f"Response is a dict with keys: {list(data.keys())}")
            else:
                print(f"Unexpected response type: {type(data)}")
        else:
            print("Staff API failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()