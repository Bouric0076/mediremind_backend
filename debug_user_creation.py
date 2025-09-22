#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from authentication.models import User
from accounts.models import EnhancedPatient
from django.contrib.auth.hashers import make_password
from django.db import transaction

def test_user_creation():
    print("🧪 Testing User Creation Step by Step")
    print("=" * 50)
    
    try:
        # Test 1: Check if we can create a basic user
        print("1. Testing basic user creation...")
        
        # Clean up any existing test user
        User.objects.filter(email='debug@test.com').delete()
        
        user = User.objects.create(
            email='debug@test.com',
            full_name='Debug Test User',
            role='patient',
            password=make_password('testpass123'),
            is_active=True
        )
        print(f"✅ User created: {user}")
        
        # Test 2: Check if we can create patient profile
        print("2. Testing patient profile creation...")
        patient = EnhancedPatient.objects.create(user=user)
        print(f"✅ Patient profile created: {patient}")
        
        # Test 3: Test the create_user method
        print("3. Testing create_user method...")
        User.objects.filter(email='debug2@test.com').delete()
        
        user2 = User.objects.create_user(
            email='debug2@test.com',
            password='testpass123',
            full_name='Debug Test User 2',
            role='patient'
        )
        print(f"✅ User created with create_user: {user2}")
        
        # Clean up
        user.delete()
        user2.delete()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_user_creation()