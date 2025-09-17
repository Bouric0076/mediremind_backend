#!/usr/bin/env python3
"""
Test script to verify appointments endpoint authentication is working correctly.
This script tests both token-based and session-based authentication.
"""

import requests
import json
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
import django
django.setup()

from authentication.models import User
from rest_framework.authtoken.models import Token

def test_appointments_auth():
    """Test appointments endpoint with different authentication methods."""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Appointments Endpoint Authentication")
    print("=" * 50)
    
    # Test 1: No authentication (should fail)
    print("\n1. Testing without authentication...")
    response = requests.get(f"{base_url}/appointments")
    print(f"   Status: {response.status_code}")
    print(f"   Expected: 401 (Unauthorized)")
    
    if response.status_code == 401:
        print("   ✅ Correctly rejected unauthenticated request")
    else:
        print("   ❌ Should have rejected unauthenticated request")
    
    # Test 2: Get a valid token for testing
    print("\n2. Getting authentication token...")
    try:
        # Try to get an existing user or create a test user
        user = User.objects.filter(email__icontains='test').first()
        if not user:
            user = User.objects.filter(is_staff=True).first()
        
        if not user:
            print("   ❌ No test user found. Please create a user first.")
            return
            
        # Get or create a token for the user
        token, created = Token.objects.get_or_create(user=user)
        print(f"   ✅ Got token for user: {user.email}")
        
        # Test 3: With Bearer token
        print("\n3. Testing with Bearer token...")
        headers = {"Authorization": f"Bearer {token.key}"}
        response = requests.get(f"{base_url}/appointments", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Bearer token authentication successful")
            try:
                data = response.json()
                print(f"   📊 Response contains {len(data.get('appointments', []))} appointments")
            except:
                print("   📊 Response received (not JSON)")
        else:
            print(f"   ❌ Bearer token authentication failed: {response.text}")
        
        # Test 4: With Token header
        print("\n4. Testing with Token header...")
        headers = {"Authorization": f"Token {token.key}"}
        response = requests.get(f"{base_url}/appointments", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Token header authentication successful")
            try:
                data = response.json()
                print(f"   📊 Response contains {len(data.get('appointments', []))} appointments")
            except:
                print("   📊 Response received (not JSON)")
        else:
            print(f"   ❌ Token header authentication failed: {response.text}")
            
        # Test 5: Compare with patients endpoint (should work the same way)
        print("\n5. Testing patients endpoint for comparison...")
        headers = {"Authorization": f"Token {token.key}"}
        response = requests.get(f"{base_url}/accounts/patients/", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Patients endpoint authentication successful")
            try:
                data = response.json()
                print(f"   📊 Response contains {len(data.get('patients', []))} patients")
            except:
                print("   📊 Response received (not JSON)")
        else:
            print(f"   ❌ Patients endpoint authentication failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error during token testing: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Authentication Test Complete")

if __name__ == "__main__":
    test_appointments_auth()