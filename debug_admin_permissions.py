#!/usr/bin/env python
"""
Django Management Script to Debug Admin User Permissions for Appointment Operations

This script will help identify why the admin user gets 403 Forbidden when trying to
cancel appointments despite having admin privileges.
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
from accounts.models import EnhancedStaffProfile, HospitalPatient
from appointments.models import Appointment
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()

def debug_admin_permissions(admin_email, appointment_id):
    """
    Debug admin user permissions for appointment operations
    """
    print(f"🔍 Debugging admin permissions for: {admin_email}")
    print(f"📅 Appointment ID: {appointment_id}")
    print("=" * 60)
    
    try:
        # 1. Find the admin user
        admin_user = User.objects.get(email=admin_email)
        print(f"✅ Found admin user: {admin_user.email}")
        print(f"   Username: {admin_user.username}")
        print(f"   Role: {getattr(admin_user, 'role', 'Not set')}")
        print(f"   Is staff: {admin_user.is_staff}")
        print(f"   Is superuser: {admin_user.is_superuser}")
        print()
        
        # 2. Check staff profile
        try:
            staff_profile = EnhancedStaffProfile.objects.get(user=admin_user)
            print(f"✅ Found staff profile:")
            print(f"   Hospital: {staff_profile.hospital}")
            print(f"   Hospital ID: {staff_profile.hospital.id}")
            print(f"   Hospital name: {staff_profile.hospital.name}")
            print(f"   Employment status: {staff_profile.employment_status}")
            print()
            admin_hospital = staff_profile.hospital
        except EnhancedStaffProfile.DoesNotExist:
            print("❌ No staff profile found for admin user!")
            print("   This is likely the issue - admin needs a staff profile with hospital association")
            return
            
    except User.DoesNotExist:
        print(f"❌ Admin user with email '{admin_email}' not found!")
        return
    
    try:
        # 3. Find the appointment
        appointment = Appointment.objects.get(id=appointment_id)
        print(f"✅ Found appointment:")
        print(f"   Patient: {appointment.patient.user.get_full_name()}")
        print(f"   Patient ID: {appointment.patient.id}")
        print(f"   Provider: {appointment.provider.user.get_full_name()}")
        print(f"   Provider ID: {appointment.provider.id}")
        print(f"   Current status: {appointment.status}")
        print(f"   Appointment date: {appointment.appointment_date}")
        print(f"   Start time: {appointment.start_time}")
        print()
        
        # 4. Check patient hospital relationship
        patient_relationships = HospitalPatient.objects.filter(
            patient=appointment.patient,
            hospital=admin_hospital,
            status='active'
        )
        print(f"📋 Patient hospital relationship check:")
        print(f"   Patient has active relationship with admin's hospital: {patient_relationships.exists()}")
        if patient_relationships.exists():
            relationship = patient_relationships.first()
            print(f"   Relationship status: {relationship.status}")
            print(f"   Relationship created: {relationship.created_at}")
        print()
        
        # 5. Check provider hospital
        provider_hospital = getattr(appointment.provider, 'hospital', None)
        print(f"🏥 Provider hospital check:")
        print(f"   Provider's hospital: {provider_hospital}")
        print(f"   Admin's hospital: {admin_hospital}")
        print(f"   Hospitals match: {provider_hospital == admin_hospital}")
        print()
        
        # 6. Permission analysis
        print("🔐 Permission Analysis:")
        patient_has_relationship = patient_relationships.exists()
        provider_hospital_match = provider_hospital == admin_hospital
        
        print(f"   Patient has relationship: {patient_has_relationship}")
        print(f"   Provider hospital matches: {provider_hospital_match}")
        print(f"   Overall permission (OR logic): {patient_has_relationship or provider_hospital_match}")
        
        if not (patient_has_relationship or provider_hospital_match):
            print("\n❌ PERMISSION DENIED - Neither condition met!")
            print("   The admin cannot cancel this appointment because:")
            if not patient_has_relationship:
                print("   - Patient has no active relationship with admin's hospital")
            if not provider_hospital_match:
                print("   - Provider works at a different hospital")
            print("\n🔧 Possible solutions:")
            print("   1. Add patient to admin's hospital")
            print("   2. Ensure provider works at admin's hospital")
            print("   3. Check if appointment belongs to a different hospital")
        else:
            print("\n✅ PERMISSION SHOULD BE GRANTED")
            print("   Admin should be able to cancel this appointment")
            
        # 7. Additional checks
        print(f"\n🔍 Additional checks:")
        print(f"   Appointment can be cancelled (status not completed/cancelled): {appointment.status not in ['completed', 'cancelled']}")
        
        # Check all patient relationships
        all_patient_relationships = HospitalPatient.objects.filter(patient=appointment.patient)
        print(f"   Patient has relationships with {all_patient_relationships.count()} hospitals:")
        for rel in all_patient_relationships:
            print(f"     - {rel.hospital.name} (status: {rel.status})")
            
        # Check all provider relationships
        all_provider_appointments = Appointment.objects.filter(provider=appointment.provider).order_by('-appointment_date')[:5]
        print(f"   Provider's recent appointments:")
        for appt in all_provider_appointments:
            print(f"     - {appt.appointment_date} at {getattr(appt, 'hospital', 'Unknown')}")
            
    except Appointment.DoesNotExist:
        print(f"❌ Appointment with ID '{appointment_id}' not found!")
        return
    
    print("\n" + "=" * 60)
    print("🔍 Debug complete!")

def main():
    """Main function to run the debug script"""
    print("🚀 Starting admin permission debug...")
    
    # Use the provided credentials
    admin_email = "admin@mediremind.test"
    appointment_id = "3f3879f6-1685-4330-ba0b-7130cd048cd6"  # From the error logs
    
    debug_admin_permissions(admin_email, appointment_id)

if __name__ == "__main__":
    main()