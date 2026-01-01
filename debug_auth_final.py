#!/usr/bin/env python
"""
Final Diagnostic Script to Identify Authentication Issues

This script will check if there are any authentication or session issues
that might cause 403 errors despite correct permissions.
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
from django.test import RequestFactory
from django.http import JsonResponse
from authentication.middleware import get_request_user
import json

User = get_user_model()

def check_authentication_flow():
    """
    Check the complete authentication flow for the admin user
    """
    print("🔐 Checking authentication flow...")
    print("=" * 60)
    
    try:
        # Get the admin user
        admin_user = User.objects.get(email="admin@mediremind.test")
        print(f"✅ Found admin user: {admin_user.email}")
        print(f"   ID: {admin_user.id}")
        print(f"   Username: {admin_user.username}")
        print(f"   Role: {getattr(admin_user, 'role', 'Not set')}")
        print(f"   Is active: {admin_user.is_active}")
        print()
        
        # Check different authentication methods
        print("🔍 Testing different authentication methods...")
        
        # Method 1: Session-based authentication (what frontend uses)
        factory = RequestFactory()
        
        # Create a request with session
        request = factory.post('/api/appointments/3f3879f6-1685-4330-ba0b-7130cd048cd6/cancel/')
        request.user = admin_user
        request.session = {}
        request.authenticated_user = admin_user
        
        # Test get_request_user
        auth_user = get_request_user(request)
        print(f"Session auth result: {auth_user}")
        print(f"Session auth matches: {auth_user == admin_user}")
        
        # Method 2: Token authentication (backup method)
        request2 = factory.post('/api/appointments/3f3879f6-1685-4330-ba0b-7130cd048cd6/cancel/')
        request2.META['HTTP_AUTHORIZATION'] = 'Token some_token_here'
        request2.session = {}
        
        auth_user2 = get_request_user(request2)
        print(f"Token auth result: {auth_user2}")
        
        # Check if there might be user role caching issues
        print(f"\n🔍 Checking user role and permissions...")
        
        # Check the actual role attribute
        user_role = getattr(admin_user, 'role', 'patient')
        print(f"User role: {user_role}")
        
        # Check if role is properly set
        if user_role not in ['admin', 'staff', 'doctor', 'patient']:
            print(f"⚠️  WARNING: User role '{user_role}' is not a standard role!")
        
        # Check for any user profile issues
        try:
            from accounts.models import EnhancedStaffProfile
            staff_profile = EnhancedStaffProfile.objects.get(user=admin_user)
            print(f"Staff profile hospital: {staff_profile.hospital}")
            print(f"Staff profile employment: {staff_profile.employment_status}")
        except EnhancedStaffProfile.DoesNotExist:
            print("❌ No staff profile found")
        
        # Check if the user might be getting a different role during API calls
        print(f"\n🔍 Checking for role override issues...")
        
        # Simulate what happens in the view
        user_from_request = auth_user or admin_user
        request_role = getattr(user_from_request, 'role', 'patient')
        print(f"Role from request: {request_role}")
        
        if request_role != user_role:
            print(f"⚠️  ROLE MISMATCH: Database role '{user_role}' != Request role '{request_role}'")
        
    except User.DoesNotExist:
        print("❌ Admin user not found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def check_actual_api_request():
    """
    Try to simulate the exact API request that might be failing
    """
    print(f"\n🧪 Simulating actual API request...")
    print("=" * 60)
    
    try:
        from django.test import Client
        from appointments.models import Appointment
        
        # Get the appointment
        appointment = Appointment.objects.get(id="3f3879f6-1685-4330-ba0b-7130cd048cd6")
        
        # Create a test client
        client = Client()
        
        # Try to make the API call as the admin user
        admin_user = User.objects.get(email="admin@mediremind.test")
        
        # Force login (session-based)
        client.force_login(admin_user)
        
        # Make the cancel request
        response = client.post(
            f'/api/appointments/{appointment.id}/cancel/',
            data=json.dumps({"reason": "Test cancellation"}),
            content_type='application/json'
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")
        
        if response.status_code == 403:
            print("❌ Got 403 Forbidden as expected")
            # Let's see what the response says
            try:
                error_data = json.loads(response.content)
                print(f"Error message: {error_data.get('error', 'No error message')}")
            except:
                print("Could not parse error response")
        elif response.status_code == 200:
            print("✅ Request succeeded - this is unexpected!")
        else:
            print(f"Got unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error in API simulation: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("🚀 Final authentication diagnostic...")
    
    check_authentication_flow()
    check_actual_api_request()
    
    print("\n" + "=" * 60)
    print("🔍 Final diagnostic complete!")

if __name__ == "__main__":
    main()