#!/usr/bin/env python
"""
Test script to verify appointment cancellation works for admin user
"""

import os
import sys
import django
import json
import requests

# Add the project directory to the path
sys.path.append('c:\\Users\\bouri\\Documents\\Projects\\mediremind_backend')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

def test_appointment_cancellation():
    """Test appointment cancellation with admin user"""
    try:
        # Get the admin user and token
        admin_user = User.objects.get(email='admin@mediremind.test')
        token = Token.objects.get(user=admin_user)
        
        print(f"✅ Found admin user: {admin_user.email}")
        print(f"✅ Found token: {token.key[:10]}...")
        
        # Test the API endpoint
        appointment_id = "3f3879f6-1685-4330-ba0b-7130cd048cd6"
        url = f"http://localhost:8000/api/appointments/{appointment_id}/cancel/"
        
        headers = {
            'Authorization': f'Token {token.key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'reason': 'Testing cancellation from debug script'
        }
        
        print(f"🚀 Testing POST to: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        print(f"📊 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Appointment cancellation successful!")
        elif response.status_code == 403:
            print("❌ Permission denied - still getting 403!")
            print("This suggests there might be another issue...")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except User.DoesNotExist:
        print("❌ Admin user not found!")
    except Token.DoesNotExist:
        print("❌ Token not found for admin user!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_appointment_cancellation()