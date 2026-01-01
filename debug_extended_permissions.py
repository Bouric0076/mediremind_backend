#!/usr/bin/env python
"""
Extended Django Management Script to Debug API Authentication and Permission Issues

This script will help identify why the admin user gets 403 Forbidden when the
permissions appear to be correct.
"""

import os
import sys
import django
import json

# Add the project directory to the path
sys.path.append('c:\\Users\\bouri\\Documents\\Projects\\mediremind_backend')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import EnhancedStaffProfile, HospitalPatient
from appointments.models import Appointment
from django.core.exceptions import ObjectDoesNotExist
from authentication.middleware import get_request_user
from django.test import RequestFactory
from django.http import JsonResponse
import base64

User = get_user_model()

def simulate_cancel_appointment_request(admin_email, appointment_id):
    """
    Simulate the exact cancel appointment request to identify the issue
    """
    print(f"🧪 Simulating cancel appointment request...")
    print(f"Admin: {admin_email}")
    print(f"Appointment: {appointment_id}")
    print("=" * 60)
    
    try:
        # Get admin user
        admin_user = User.objects.get(email=admin_email)
        print(f"✅ Found admin user: {admin_user.email} (ID: {admin_user.id})")
        
        # Get appointment
        appointment = Appointment.objects.get(id=appointment_id)
        print(f"✅ Found appointment: {appointment.id}")
        
        # Create mock request
        factory = RequestFactory()
        request = factory.post(f'/api/appointments/{appointment_id}/cancel/')
        
        # Add authentication headers (simulate the frontend)
        # Since the frontend uses session-based auth, we'll simulate it
        request.user = admin_user
        request.authenticated_user = admin_user
        request.session = {}
        
        print(f"\n🔍 Testing authentication...")
        
        # Test get_request_user function
        authenticated_user = get_request_user(request)
        print(f"Authenticated user: {authenticated_user}")
        print(f"Authenticated user ID: {getattr(authenticated_user, 'id', 'None')}")
        print(f"Matches admin user: {authenticated_user == admin_user}")
        
        # Now let's manually check the permission logic from the view
        print(f"\n🔍 Testing permission logic...")
        
        # Get user's hospital if staff/admin
        user_role = getattr(admin_user, 'role', 'patient')
        user_hospital = None
        
        if user_role != 'patient':
            try:
                staff_profile = EnhancedStaffProfile.objects.get(user=admin_user)
                user_hospital = staff_profile.hospital
                print(f"✅ Staff profile found, hospital: {user_hospital.name}")
            except EnhancedStaffProfile.DoesNotExist:
                print("❌ No staff profile found")
                return
        
        # Check permissions (exact logic from the view)
        if user_role == 'patient' and appointment.patient.user != admin_user:
            print("❌ Patient permission denied")
            return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role == 'doctor' and appointment.provider.user != admin_user:
            print("❌ Doctor permission denied")
            return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role not in ['patient', 'doctor']:
            # For admin/staff, check hospital association
            print(f"\n🔍 Checking admin/staff permissions...")
            print(f"User hospital: {user_hospital}")
            
            if user_hospital:
                # Check patient hospital relationship
                patient_has_relationship = HospitalPatient.objects.filter(
                    patient=appointment.patient, 
                    hospital=user_hospital, 
                    status='active'
                ).exists()
                print(f"Patient has relationship: {patient_has_relationship}")
                
                # Check provider hospital
                provider_hospital = getattr(appointment.provider, 'hospital', None)
                print(f"Provider hospital: {provider_hospital}")
                print(f"Hospitals match: {provider_hospital == user_hospital}")
                
                # Final permission check
                if not patient_has_relationship and provider_hospital != user_hospital:
                    print("❌ Hospital permission denied - hospital mismatch")
                    return JsonResponse({"error": "Permission denied - hospital mismatch"}, status=403)
                else:
                    print("✅ Hospital permission granted")
            else:
                print("❌ Hospital association not found")
                return JsonResponse({"error": "Hospital association not found"}, status=403)
        
        # Check appointment status
        print(f"\n🔍 Checking appointment status...")
        print(f"Current status: {appointment.status}")
        if appointment.status in ['completed', 'cancelled']:
            print("❌ Cannot cancel completed/cancelled appointment")
            return JsonResponse({"error": "Cannot cancel completed or already cancelled appointment"}, status=400)
        
        print("\n✅ ALL CHECKS PASSED - Should be able to cancel!")
        
    except User.DoesNotExist:
        print(f"❌ Admin user not found")
    except Appointment.DoesNotExist:
        print(f"❌ Appointment not found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def check_api_request_details():
    """
    Check if there might be issues with the actual API request
    """
    print(f"\n🔍 Checking potential API request issues...")
    print("=" * 60)
    
    # Check if the appointment ID in the error matches what we're testing
    print(f"Testing appointment ID: 3f3879f6-1685-4330-ba0b-7130cd048cd6")
    print(f"This should be the same ID causing the 403 error")
    
    # Check if there are multiple appointments with similar IDs
    appointments = Appointment.objects.filter(
        id__startswith='3f3879f6'
    )[:5]
    
    if appointments:
        print(f"\nFound {appointments.count()} appointments with similar IDs:")
        for appt in appointments:
            print(f"  - {appt.id}: {appt.patient.user.get_full_name()} with {appt.provider.user.get_full_name()}")
    
    # Check if the user role might be cached or different
    admin_user = User.objects.get(email="admin@mediremind.test")
    print(f"\nUser role from database: {getattr(admin_user, 'role', 'Not set')}")
    
    # Check if there are any permission caching issues
    from django.core.cache import cache
    cache_keys = cache.keys('*permission*') + cache.keys('*auth*') + cache.keys('*user*')
    if cache_keys:
        print(f"\nFound {len(cache_keys)} cache keys related to permissions/auth:")
        for key in cache_keys[:5]:  # Show first 5
            print(f"  - {key}")
    else:
        print("\nNo permission/auth cache keys found")

def main():
    """Main function to run the extended debug"""
    print("🚀 Extended admin permission debug...")
    
    admin_email = "admin@mediremind.test"
    appointment_id = "3f3879f6-1685-4330-ba0b-7130cd048cd6"
    
    simulate_cancel_appointment_request(admin_email, appointment_id)
    check_api_request_details()
    
    print("\n" + "=" * 60)
    print("🔍 Extended debug complete!")

if __name__ == "__main__":
    main()