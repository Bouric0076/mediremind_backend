#!/usr/bin/env python3

import requests
import json
import time
import sys

def test_login_debug():
    """Test login with detailed debugging"""
    base_url = "http://127.0.0.1:8000"
    
    print("🔍 Debugging Django Login")
    print("=" * 40)
    
    # Test data
    test_user = {
        "email": "debug_test@example.com",
        "password": "TestPass123!",
        "full_name": "Debug Test User",
        "role": "patient"
    }
    
    try:
        # 1. Register test user
        print("1. Registering test user...")
        register_response = requests.post(
            f"{base_url}/auth/register/",
            json=test_user,
            timeout=10
        )
        print(f"   Registration: {register_response.status_code}")
        if register_response.status_code != 200:
            print(f"   Registration failed: {register_response.text}")
            return
        
        # 2. Test login with detailed timing
        print("2. Testing login with timing...")
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        print(f"   Sending login request to {base_url}/auth/login/")
        print(f"   Data: {json.dumps(login_data, indent=2)}")
        
        start_time = time.time()
        try:
            login_response = requests.post(
                f"{base_url}/auth/login/",
                json=login_data,
                timeout=30  # Increased timeout
            )
            end_time = time.time()
            
            print(f"   ✅ Login completed in {end_time - start_time:.2f} seconds")
            print(f"   Status: {login_response.status_code}")
            print(f"   Headers: {dict(login_response.headers)}")
            
            if login_response.status_code == 200:
                response_data = login_response.json()
                print(f"   Response: {json.dumps(response_data, indent=2)}")
            else:
                print(f"   Error response: {login_response.text}")
                
        except requests.exceptions.Timeout:
            end_time = time.time()
            print(f"   ⚠️ Login timed out after {end_time - start_time:.2f} seconds")
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ Connection error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        # 3. Cleanup
        print("3. Cleaning up...")
        try:
            # Try to delete the test user
            import os
            import django
            
            # Setup Django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
            django.setup()
            
            from authentication.models import User
            User.objects.filter(email=test_user["email"]).delete()
            print("   ✅ Test user cleaned up")
        except Exception as cleanup_error:
            print(f"   ⚠️ Cleanup error: {cleanup_error}")

if __name__ == "__main__":
    test_login_debug()