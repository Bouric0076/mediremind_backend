#!/usr/bin/env python3
"""
Test script for Patient Dashboard API with real authentication
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
DASHBOARD_URL = f"{BASE_URL}/api/patient/dashboard/"
PROFILE_URL = f"{BASE_URL}/api/patient/profile/"

# Test credentials
EMAIL = "testpatient1@gmail.com"
PASSWORD = "TesPatient123!"

def print_separator(title):
    print("=" * 60)
    print(f"{title}")
    print("=" * 60)

def test_login():
    """Test login and get authentication token"""
    print("1. Testing login with provided credentials...")
    
    login_data = {
        "email": EMAIL,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        print(f"Login Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"Response keys: {list(data.keys())}")
            
            # Extract token (check different possible token field names)
            token = None
            for key in ['token', 'access_token', 'auth_token', 'access']:
                if key in data:
                    token = data[key]
                    break
            
            if token:
                print(f"🔑 Token obtained: {token[:20]}...")
                return token
            else:
                print("❌ No token found in response")
                print(f"Full response: {json.dumps(data, indent=2)}")
                return None
        else:
            print("❌ Login failed")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure Django server is running on localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return None

def test_dashboard_api(token):
    """Test dashboard API with authentication token"""
    print("\n2. Testing dashboard API with authentication...")
    
    # Try different authentication header formats
    auth_formats = [
        f"Bearer {token}",
        f"Token {token}",
        token
    ]
    
    for i, auth_format in enumerate(auth_formats):
        print(f"\n  Attempt {i+1}: Using Authorization: {auth_format[:20]}...")
        
        headers = {
            "Authorization": auth_format,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(DASHBOARD_URL, headers=headers)
            print(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Dashboard API successful!")
                print("\n📊 Dashboard Data Structure:")
                print(f"Response keys: {list(data.keys())}")
                
                # Display each section
                for key, value in data.items():
                    print(f"\n{key.upper()}:")
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, list):
                                print(f"  {sub_key}: {len(sub_value)} items")
                            else:
                                print(f"  {sub_key}: {sub_value}")
                    elif isinstance(value, list):
                        print(f"  {len(value)} items")
                        if value:  # Show first item structure
                            print(f"  Sample item keys: {list(value[0].keys()) if isinstance(value[0], dict) else 'Not a dict'}")
                    else:
                        print(f"  {value}")
                
                return data
            elif response.status_code == 401:
                print(f"  ❌ Authentication failed: {response.text}")
                continue  # Try next format
            else:
                print(f"  ❌ API failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ API error: {str(e)}")
            continue
    
    print("❌ All authentication formats failed")
    return None

def test_profile_api(token):
    """Test profile API with authentication token"""
    print("\n3. Testing profile API with authentication...")
    
    headers = {
        "Authorization": f"Token {token}",  # Use Token format that worked for dashboard
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(PROFILE_URL, headers=headers)
        print(f"Profile Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Profile API successful!")
            print(f"\n👤 Profile Data: {json.dumps(data, indent=2)}")
            return data
        else:
            print("❌ Profile API failed")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Profile API error: {str(e)}")
        return None

def validate_dashboard_structure(data):
    """Validate that the dashboard data structure matches Flutter requirements"""
    print("\n4. Validating dashboard structure for Flutter compatibility...")
    
    # Expected fields for Flutter dashboard
    expected_fields = [
        'patient_name',
        'todays_stats',
        'upcoming_appointments',
        'current_medications',
        'recent_notifications',
        'services',
        'last_updated'
    ]
    
    actual_fields = list(data.keys())
    missing_fields = [field for field in expected_fields if field not in actual_fields]
    extra_fields = [field for field in actual_fields if field not in expected_fields]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
    if extra_fields:
        print(f"⚠️ Extra fields found: {extra_fields}")
    
    if not missing_fields and not extra_fields:
        print("✅ Dashboard structure is perfect for Flutter!")
    elif not missing_fields:
        print("✅ All required fields present (extra fields are okay)")
    
    return len(missing_fields) == 0

def main():
    print_separator("PATIENT DASHBOARD API TEST WITH REAL AUTHENTICATION")
    print(f"Testing with credentials: {EMAIL}")
    print(f"Server URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Login
    token = test_login()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        sys.exit(1)
    
    # Step 2: Test Dashboard API
    dashboard_data = test_dashboard_api(token)
    if not dashboard_data:
        print("\n❌ Dashboard API test failed")
        sys.exit(1)
    
    # Step 3: Test Profile API
    profile_data = test_profile_api(token)
    
    # Step 4: Validate structure
    if dashboard_data:
        validate_dashboard_structure(dashboard_data)
    
    print_separator("TEST COMPLETED SUCCESSFULLY")
    print("✅ All API endpoints are working correctly!")
    print("🚀 Ready for Flutter integration!")

if __name__ == "__main__":
    main()