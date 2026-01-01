#!/usr/bin/env python
"""
Test script to verify that AuthenticatedUser has proper role access
"""

import os
import sys
import django

# Add the project directory to the path
sys.path.append('c:\\Users\\bouri\\Documents\\Projects\\mediremind_backend')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication.utils import get_authenticated_user

User = get_user_model()

def test_authenticated_user_role():
    """Test that AuthenticatedUser properly exposes the role"""
    try:
        # Get the admin user
        admin_user = User.objects.get(email='admin@mediremind.test')
        print(f"✅ Found admin user: {admin_user.email}")
        print(f"   Direct role from User model: {admin_user.role}")
        
        # Test with a mock token (we'll create a simple test)
        # Since we can't easily create a real token, let's test the AuthenticatedUser directly
        from authentication.utils import AuthenticatedUser
        
        auth_user = AuthenticatedUser(admin_user)
        print(f"   AuthenticatedUser role via property: {auth_user.role}")
        print(f"   AuthenticatedUser role via getattr: {getattr(auth_user, 'role', 'patient')}")
        print(f"   Profile role: {auth_user.profile.get('role', 'Not found')}")
        
        # Test the permission logic that would be used in cancel_appointment
        user_role = getattr(auth_user, 'role', 'patient')
        print(f"   Permission check would use role: {user_role}")
        
        if user_role == 'admin':
            print("✅ Admin role properly detected!")
        else:
            print(f"❌ Expected 'admin', got '{user_role}'")
            
    except User.DoesNotExist:
        print("❌ Admin user not found!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_authenticated_user_role()