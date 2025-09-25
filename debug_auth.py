#!/usr/bin/env python3
"""
Debug authentication failure in detail
"""

import os
import django
import traceback

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from authentication.models import User
from authentication.services import AuthenticationService
from django.contrib.auth import authenticate

def debug_authentication():
    print("🔍 Debugging Authentication Failure")
    print("=" * 60)
    
    email = "admin@mediremind.test"
    password = "TestAdmin123!"
    
    # 1. Check user exists
    print("1. Checking user existence...")
    try:
        user = User.objects.get(email=email)
        print(f"✅ User found: {user.email}")
        print(f"   Active: {user.is_active}")
        print(f"   Failed attempts: {user.failed_login_attempts}")
        print(f"   Locked until: {user.account_locked_until}")
    except User.DoesNotExist:
        print("❌ User not found")
        return
    
    # 2. Test Django authenticate directly
    print("\n2. Testing Django authenticate...")
    try:
        django_user = authenticate(username=email, password=password)
        if django_user:
            print(f"✅ Django authenticate successful: {django_user.email}")
        else:
            print("❌ Django authenticate failed")
            
            # Test with different username formats
            print("   Trying with username field...")
            django_user = authenticate(username=user.username, password=password)
            if django_user:
                print(f"✅ Django authenticate with username successful: {django_user.email}")
            else:
                print("❌ Django authenticate with username also failed")
                
    except Exception as e:
        print(f"❌ Django authenticate error: {str(e)}")
        traceback.print_exc()
    
    # 3. Test password verification directly
    print("\n3. Testing password verification...")
    try:
        password_valid = user.check_password(password)
        print(f"Password valid: {password_valid}")
        
        # Check password hash
        print(f"Password hash: {user.password[:50]}...")
        
    except Exception as e:
        print(f"❌ Password check error: {str(e)}")
        traceback.print_exc()
    
    # 4. Test each step of authentication service
    print("\n4. Testing AuthenticationService steps...")
    auth_service = AuthenticationService()
    
    try:
        # Step 1: Get user
        print("   Step 1: Getting user...")
        service_user = auth_service._get_user_by_email(email)
        if service_user:
            print(f"   ✅ User found: {service_user.email}")
        else:
            print("   ❌ User not found by service")
            return
        
        # Step 2: Check account status
        print("   Step 2: Checking account status...")
        auth_service._check_account_status(service_user)
        print("   ✅ Account status OK")
        
        # Step 3: Check rate limiting
        print("   Step 3: Checking rate limiting...")
        auth_service._check_rate_limiting(service_user, "127.0.0.1")
        print("   ✅ Rate limiting OK")
        
        # Step 4: Django authenticate
        print("   Step 4: Django authenticate...")
        django_user = authenticate(username=email, password=password)
        if django_user:
            print(f"   ✅ Django authenticate successful")
        else:
            print("   ❌ Django authenticate failed - THIS IS THE ISSUE")
            
            # Check authentication backends
            from django.conf import settings
            print(f"   Authentication backends: {settings.AUTHENTICATION_BACKENDS}")
            
    except Exception as e:
        print(f"   ❌ Authentication service step failed: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_authentication()