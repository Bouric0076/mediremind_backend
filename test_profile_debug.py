#!/usr/bin/env python3
"""
Simple profile endpoint test to debug issues
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_profile_endpoint():
    print("🧪 Testing Profile Endpoint")
    print("=" * 50)
    
    # Test data with timestamp to ensure uniqueness
    import time
    timestamp = int(time.time())
    test_user = {
        "email": f"profile_test_{timestamp}@example.com",
        "password": "TestPassword123!",
        "full_name": "Profile Test User",
        "role": "patient"
    }
    
    try:
        # 1. Register user
        print("📝 Registering test user...")
        register_response = requests.post(
            f"{BASE_URL}/auth/register/",
            json=test_user,
            timeout=15
        )
        print(f"   Registration status: {register_response.status_code}")
        
        if register_response.status_code != 200:
            print(f"   Registration failed: {register_response.text}")
            return
        
        # 2. Login
        print("🔐 Logging in...")
        login_response = requests.post(
            f"{BASE_URL}/auth/login/",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            },
            timeout=25
        )
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"   Login failed: {login_response.text}")
            return
        
        login_data = login_response.json()
        token = login_data.get('token')
        print(f"   Token received: {token[:20]}...")
        
        # 3. Test profile endpoint
        print("👤 Testing profile endpoint...")
        headers = {'Authorization': f'Token {token}'}
        
        profile_response = requests.get(
            f"{BASE_URL}/auth/profile/",
            headers={"Authorization": f"Token {token}"},
            timeout=15
        )
        print(f"   Profile status: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            print("✅ Profile endpoint working!")
            profile_data = profile_response.json()
            if profile_data and profile_data.get('success'):
                user_data = profile_data.get('user', {})
                profile_info = user_data.get('profile', {})
                print(f"   User ID: {user_data.get('id')}")
                print(f"   Email: {user_data.get('email')}")
                print(f"   Role: {user_data.get('role')}")
                print(f"   Profile ID: {profile_info.get('id')}")
                print(f"   Phone: {profile_info.get('phone_number')}")
                print(f"   Permissions: {len(user_data.get('permissions', []))} permissions")
                print(f"   Active Sessions: {user_data.get('active_sessions', 0)}")
            else:
                print("❌ Profile data is None or missing")
        else:
            print(f"❌ Profile failed: {profile_response.text}")
            return
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        try:
            cleanup_response = requests.delete(
                f"{BASE_URL}/auth/test-cleanup/",
                json={"email": test_user["email"]},
                timeout=10
            )
            print(f"   Cleanup status: {cleanup_response.status_code}")
        except:
            print("   Cleanup failed (user may not exist)")

if __name__ == "__main__":
    test_profile_endpoint()