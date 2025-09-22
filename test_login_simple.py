#!/usr/bin/env python
import requests
import json

def test_login():
    print("🔐 Testing Django Login")
    print("=" * 30)
    
    # First register a user
    register_data = {
        'email': 'login_test@example.com',
        'password': 'testpass123',
        'full_name': 'Login Test User',
        'role': 'patient'
    }
    
    try:
        # Register
        print("1. Registering test user...")
        register_response = requests.post(
            'http://127.0.0.1:8000/auth/register/',
            json=register_data,
            timeout=5
        )
        print(f"   Registration: {register_response.status_code}")
        
        if register_response.status_code == 200:
            print("   ✅ Registration successful")
            
            # Login
            print("2. Testing login...")
            login_data = {
                'email': 'login_test@example.com',
                'password': 'testpass123'
            }
            
            login_response = requests.post(
                'http://127.0.0.1:8000/auth/login/',
                json=login_data,
                timeout=5
            )
            
            print(f"   Login: {login_response.status_code}")
            if login_response.status_code == 200:
                print("   ✅ Login successful")
                response_data = login_response.json()
                print(f"   Token received: {bool(response_data.get('token'))}")
            else:
                print(f"   ❌ Login failed: {login_response.text}")
        else:
            print(f"   ❌ Registration failed: {register_response.text}")
            
    except requests.exceptions.Timeout:
        print("   ⚠️ Request timed out")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Cleanup
    try:
        import os
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
        django.setup()
        from authentication.models import User
        User.objects.filter(email='login_test@example.com').delete()
        print("3. ✅ Test user cleaned up")
    except:
        print("3. ⚠️ Cleanup failed")

if __name__ == '__main__':
    test_login()