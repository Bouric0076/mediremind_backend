#!/usr/bin/env python3
"""
Test script to verify Django-only authentication system
"""
import os
import sys
import django
import requests
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

def test_authentication_endpoints():
    """Test authentication endpoints with Django-only authentication"""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Django-only Authentication System")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server connection failed: {e}")
        return False
    
    # Test 2: Test registration endpoint
    print("\n📝 Testing Registration...")
    test_user_data = {
        "email": "test_django_auth@example.com",
        "password": "TestPassword123!",
        "full_name": "Test Django User",
        "role": "patient"
    }
    
    try:
        response = requests.post(
            f"{base_url}/auth/register/",
            json=test_user_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ Registration successful")
            registration_data = response.json()
            print(f"   User ID: {registration_data.get('user_id')}")
            print(f"   Email: {registration_data.get('email')}")
            # Note: No more supabase_id in response
        else:
            print(f"⚠️  Registration response: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Registration failed: {e}")
    
    # Test 3: Test login endpoint
    print("\n🔐 Testing Login...")
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    
    try:
        response = requests.post(
            f"{base_url}/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        if response.status_code == 200:
            print("✅ Login successful")
            login_response = response.json()
            token = login_response.get('token')
            print(f"   Token received: {token[:20]}..." if token else "   No token received")
            
            # Test 4: Test authenticated endpoint
            if token:
                print("\n🔒 Testing Authenticated Access...")
                headers = {"Authorization": f"Token {token}"}
                
                try:
                    profile_response = requests.get(
                        f"{base_url}/auth/profile/",
                        headers=headers,
                        timeout=10
                    )
                    
                    if profile_response.status_code == 200:
                        print("✅ Authenticated access successful")
                        profile_data = profile_response.json()
                        print(f"   User: {profile_data.get('email')}")
                        print(f"   Role: {profile_data.get('role')}")
                    else:
                        print(f"⚠️  Profile access failed: {profile_response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"❌ Profile access failed: {e}")
        else:
            print(f"⚠️  Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Login failed: {e}")
    
    # Cleanup: Remove test user
    print("\n🧹 Cleaning up test user...")
    try:
        test_user = User.objects.get(email=test_user_data["email"])
        test_user.delete()
        print("✅ Test user cleaned up")
    except User.DoesNotExist:
        print("ℹ️  Test user not found (may not have been created)")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n🎉 Django-only authentication test completed!")
    return True

if __name__ == "__main__":
    test_authentication_endpoints()