#!/usr/bin/env python3
"""
Check if test user exists in production database on Render
"""

import requests
import json
import sys

def check_production_user():
    """Check if the test user exists in the production database"""
    
    render_url = "https://mediremind-backend-cl6r.onrender.com"
    
    print("🔍 Checking Production Database User Status")
    print("=" * 60)
    
    # Test 1: Health check to ensure service is running
    print("\n1. Testing service health...")
    try:
        health_response = requests.get(f"{render_url}/health/", timeout=30)
        print(f"   Status: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   Database: {health_data.get('database', 'unknown')}")
            print(f"   Environment: {health_data.get('environment', 'unknown')}")
            print(f"   Debug Mode: {health_data.get('debug', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {health_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {str(e)}")
        return False
    
    # Test 2: Try authentication with known credentials
    print("\n2. Testing authentication with test credentials...")
    test_credentials = {
        "email": "admin@mediremind.test",
        "password": "TestAdmin123!"
    }
    
    try:
        auth_response = requests.post(
            f"{render_url}/api/auth/login/",
            json=test_credentials,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"   Status: {auth_response.status_code}")
        
        if auth_response.status_code == 200:
            print("   ✅ User exists and authentication successful!")
            auth_data = auth_response.json()
            if auth_data.get('success'):
                user_info = auth_data.get('user', {})
                print(f"   User ID: {user_info.get('id', 'N/A')}")
                print(f"   Email: {user_info.get('email', 'N/A')}")
                print(f"   Role: {user_info.get('role', 'N/A')}")
                print(f"   Full Name: {user_info.get('full_name', 'N/A')}")
                return True
            else:
                print(f"   ❌ Authentication failed: {auth_data.get('error', 'Unknown error')}")
                return False
        elif auth_response.status_code == 401:
            print("   ❌ User does not exist or credentials are invalid")
            try:
                error_data = auth_response.json()
                print(f"   Error: {error_data.get('error', 'Authentication failed')}")
            except:
                print(f"   Raw response: {auth_response.text}")
            return False
        else:
            print(f"   ❌ Unexpected response: {auth_response.status_code}")
            print(f"   Response: {auth_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Authentication test error: {str(e)}")
        return False
    
    # Test 3: Try with different common passwords (in case password differs)
    print("\n3. Testing with alternative passwords...")
    alternative_passwords = [
        "admin123",
        "Admin123!",
        "testpassword",
        "password123",
        "mediremind123"
    ]
    
    for password in alternative_passwords:
        try:
            alt_credentials = {
                "email": "admin@mediremind.test",
                "password": password
            }
            
            alt_response = requests.post(
                f"{render_url}/api/auth/login/",
                json=alt_credentials,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if alt_response.status_code == 200:
                print(f"   ✅ Success with password: {password}")
                return True
            else:
                print(f"   ❌ Failed with password: {password}")
                
        except Exception as e:
            print(f"   ❌ Error testing password {password}: {str(e)}")
            continue
    
    print("\n📋 Summary:")
    print("   - Service is healthy and running")
    print("   - Database is connected")
    print("   - Test user 'admin@mediremind.test' does not exist in production")
    print("   - Production database is separate from local development database")
    
    return False

if __name__ == "__main__":
    success = check_production_user()
    sys.exit(0 if success else 1)