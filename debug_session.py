#!/usr/bin/env python3
"""
Debug session creation in authentication
"""

import os
import django
import traceback

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from authentication.models import User, UserSession
from authentication.services import AuthenticationService
from rest_framework.authtoken.models import Token

def debug_session_creation():
    print("🔍 Debugging Session Creation")
    print("=" * 60)
    
    email = "admin@mediremind.test"
    
    try:
        user = User.objects.get(email=email)
        print(f"✅ User found: {user.email}")
        
        auth_service = AuthenticationService()
        
        # Test session creation directly
        print("\n1. Testing _create_session directly...")
        try:
            session = auth_service._create_session(
                user=user,
                ip_address="127.0.0.1",
                user_agent="Test Script"
            )
            print(f"✅ Session created: {session.id}")
            print(f"   Session key: {session.session_key}")
            print(f"   Expires at: {session.expires_at}")
            
            # Check if token was created
            try:
                token = Token.objects.get(user=user)
                print(f"✅ Token found: {token.key[:20]}...")
            except Token.DoesNotExist:
                print("❌ No token found")
                
        except Exception as e:
            print(f"❌ Session creation failed: {str(e)}")
            traceback.print_exc()
        
        # Test full authentication flow step by step
        print("\n2. Testing full authentication with detailed logging...")
        try:
            result = auth_service.authenticate(
                email=email,
                password="TestAdmin123!",
                ip_address="127.0.0.1",
                user_agent="Test Script"
            )
            print(f"✅ Full authentication successful")
            print(f"   Access token: {result.get('access_token', 'N/A')[:20]}...")
            print(f"   Session ID: {result.get('session', {}).get('id', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Full authentication failed: {str(e)}")
            traceback.print_exc()
            
    except User.DoesNotExist:
        print("❌ User not found")

if __name__ == "__main__":
    debug_session_creation()