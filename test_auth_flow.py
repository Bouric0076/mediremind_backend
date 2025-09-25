#!/usr/bin/env python3
"""
Comprehensive authentication flow test script
"""

import os
import django
import requests
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from authentication.models import User, LoginAttempt, UserSession
from authentication.services import AuthenticationService
from rest_framework.authtoken.models import Token

def test_authentication_flow():
    print("🔐 Testing Authentication Flow")
    print("=" * 60)
    
    # Test credentials
    email = "admin@mediremind.test"
    password = "TestAdmin123!"
    
    print(f"Testing with credentials: {email}")
    
    # 1. Test direct authentication service
    print("\n1. Testing AuthenticationService directly...")
    try:
        auth_service = AuthenticationService()
        result = auth_service.authenticate_user(
            email=email,
            password=password,
            ip_address="127.0.0.1",
            user_agent="Test Script"
        )
        print(f"✅ Direct authentication successful")
        print(f"   Token: {result.get('access_token', 'N/A')[:20]}...")
        print(f"   Session ID: {result.get('session', {}).get('id', 'N/A')}")
    except Exception as e:
        print(f"❌ Direct authentication failed: {str(e)}")
    
    # 2. Test API endpoint
    print("\n2. Testing API endpoint...")
    try:
        response = requests.post(
            'http://127.0.0.1:8000/api/auth/login/',
            json={
                'email': email,
                'password': password
            },
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API authentication successful")
            data = response.json()
            token = data.get('token')
            if token:
                print(f"   Token received: {token[:20]}...")
        else:
            print("❌ API authentication failed")
            
    except Exception as e:
        print(f"❌ API request failed: {str(e)}")
    
    # 3. Check recent login attempts
    print("\n3. Checking recent login attempts...")
    recent_attempts = LoginAttempt.objects.filter(
        email_attempted=email
    ).order_by('-timestamp')[:5]
    
    for attempt in recent_attempts:
        status = "✅ Success" if attempt.success else "❌ Failed"
        print(f"   {attempt.timestamp}: {status} - {attempt.failure_reason or 'N/A'}")
    
    # 4. Check user sessions
    print("\n4. Checking user sessions...")
    try:
        user = User.objects.get(email=email)
        sessions = UserSession.objects.filter(user=user).order_by('-created_at')[:3]
        
        for session in sessions:
            status = "Active" if session.is_active else "Inactive"
            print(f"   Session {session.id}: {status} - Created: {session.created_at}")
            
    except Exception as e:
        print(f"❌ Error checking sessions: {str(e)}")
    
    # 5. Check Django tokens
    print("\n5. Checking Django tokens...")
    try:
        user = User.objects.get(email=email)
        tokens = Token.objects.filter(user=user)
        
        if tokens.exists():
            for token in tokens:
                print(f"   Token: {token.key[:20]}... - Created: {token.created}")
        else:
            print("   No tokens found for user")
            
    except Exception as e:
        print(f"❌ Error checking tokens: {str(e)}")

if __name__ == "__main__":
    test_authentication_flow()