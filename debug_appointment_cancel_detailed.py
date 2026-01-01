#!/usr/bin/env python
"""
Test script to debug the exact error in appointment cancellation
"""

import os
import sys
import django
import json
import requests
import logging

# Add the project directory to the path
sys.path.append('c:\\Users\\bouri\\Documents\\Projects\\mediremind_backend')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from appointments.models import Appointment
from accounts.models import EnhancedStaffProfile

User = get_user_model()

# Set up logging to see detailed errors
logging.basicConfig(level=logging.DEBUG)

def debug_appointment_cancellation():
    """Debug appointment cancellation step by step"""
    try:
        # Get the admin user and token
        admin_user = User.objects.get(email='admin@mediremind.test')
        token = Token.objects.get(user=admin_user)
        
        print(f"✅ Found admin user: {admin_user.email}")
        print(f"✅ Found token: {token.key[:10]}...")
        
        # Get the appointment
        appointment_id = "3f3879f6-1685-4330-ba0b-7130cd048cd6"
        appointment = Appointment.objects.get(id=appointment_id)
        
        print(f"✅ Found appointment:")
        print(f"   Patient: {appointment.patient.user.get_full_name()}")
        print(f"   Provider: {appointment.provider.user.get_full_name()}")
        print(f"   Status: {appointment.status}")
        print(f"   Date: {appointment.appointment_date}")
        print(f"   Time: {appointment.start_time}")
        
        # Check if appointment can be cancelled
        if appointment.status in ['completed', 'cancelled']:
            print(f"❌ Appointment cannot be cancelled - status is {appointment.status}")
            return
        
        # Check admin's staff profile
        try:
            staff_profile = EnhancedStaffProfile.objects.get(user=admin_user)
            print(f"✅ Admin staff profile found:")
            print(f"   Hospital: {staff_profile.hospital}")
            print(f"   Department: {staff_profile.department}")
        except EnhancedStaffProfile.DoesNotExist:
            print("❌ Admin has no staff profile!")
            return
        
        # Check permissions manually
        user_role = admin_user.role
        print(f"✅ Admin role: {user_role}")
        
        # Test the API endpoint with more detailed error handling
        url = f"http://localhost:8000/api/appointments/{appointment_id}/cancel/"
        
        headers = {
            'Authorization': f'Token {token.key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'reason': 'Testing cancellation from debug script - detailed test'
        }
        
        print(f"\n🚀 Testing POST to: {url}")
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
            
            print(f"\n📊 Response Status: {response.status_code}")
            print(f"📊 Response Body: {response.text}")
            
            if response.status_code == 200:
                print("✅ Appointment cancellation successful!")
            elif response.status_code == 403:
                print("❌ Permission denied")
            elif response.status_code == 500:
                print("❌ Internal server error - check server logs")
                # Try to get more details from response
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print("Could not parse error response")
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            
    except User.DoesNotExist:
        print("❌ Admin user not found!")
    except Token.DoesNotExist:
        print("❌ Token not found for admin user!")
    except Appointment.DoesNotExist:
        print("❌ Appointment not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_appointment_cancellation()