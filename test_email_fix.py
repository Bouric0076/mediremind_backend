#!/usr/bin/env python
"""
Test script to verify email functionality fix
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to the path
sys.path.append('c:\\Users\\bouri\\Documents\\Projects\\mediremind_backend')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from notifications.appointment_reminders import AppointmentReminderService, ReminderType
from appointments.models import Appointment
from accounts.models import EnhancedPatient, EnhancedStaffProfile
from authentication.models import User
from django.utils import timezone

def test_email_sending():
    """Test the fixed email sending functionality"""
    print("Testing email functionality fix...")
    
    try:
        # Create test data
        # First, get or create a test user (admin user)
        try:
            admin_user = User.objects.get(email='admin@mediremind.test')
            print(f"Found existing admin user: {admin_user.email}")
        except User.DoesNotExist:
            admin_user = User.objects.create_user(
                email='admin@mediremind.test',
                full_name='Admin Test',
                first_name='Admin',
                last_name='Test',
                role='admin',
                username='admin_test'
            )
            print(f"Created new admin user: {admin_user.email}")
        
        # Get or create a test patient with the email you want to test
        try:
            patient_user = User.objects.get(email='bouricenos0@gmail.com')
            print(f"Found existing patient user: {patient_user.email}")
        except User.DoesNotExist:
            patient_user = User.objects.create_user(
                email='bouricenos0@gmail.com',
                full_name='Test Patient',
                first_name='Test',
                last_name='Patient',
                role='patient',
                username='bouricenos_test'
            )
            print(f"Created new patient user: {patient_user.email}")
        
        # Create or get patient profile
        try:
            patient = EnhancedPatient.objects.get(user=patient_user)
            print(f"Found existing patient profile: {patient.id}")
        except EnhancedPatient.DoesNotExist:
            patient = EnhancedPatient.objects.create(
                user=patient_user,
                phone='+254743721952',  # Using the phone from the logs
                date_of_birth='1990-01-01',
                emergency_contact_name='Emergency Contact',
                emergency_contact_phone='+254700000000'
            )
            print(f"Created new patient profile: {patient.id}")
        
        # Create or get provider profile
        try:
            provider = EnhancedStaffProfile.objects.get(user=admin_user)
            print(f"Found existing provider profile: {provider.id}")
        except EnhancedStaffProfile.DoesNotExist:
            provider = EnhancedStaffProfile.objects.create(
                user=admin_user,
                specialization='General Practice',
                license_number='TEST123',
                phone='+254700123456'
            )
            print(f"Created new provider profile: {provider.id}")
        
        # Create a test appointment
        # First, get or create an appointment type
        from accounts.models import Hospital
        try:
            hospital = Hospital.objects.first()
            if not hospital:
                hospital = Hospital.objects.create(
                    name='Test Hospital',
                    hospital_type='clinic'
                )
        except Hospital.DoesNotExist:
            hospital = Hospital.objects.create(
                name='Test Hospital',
                hospital_type='clinic'
            )
        
        from appointments.models import AppointmentType
        try:
            appointment_type = AppointmentType.objects.filter(hospital=hospital).first()
            if not appointment_type:
                appointment_type = AppointmentType.objects.create(
                    hospital=hospital,
                    name='Consultation',
                    code='CONSULT',
                    default_duration=30
                )
        except AppointmentType.DoesNotExist:
            appointment_type = AppointmentType.objects.create(
                hospital=hospital,
                name='Consultation',
                code='CONSULT',
                default_duration=30
            )
        
        appointment_datetime = timezone.now() + timedelta(hours=2)
        appointment = Appointment.objects.create(
            patient=patient,
            provider=provider,
            appointment_type=appointment_type,
            hospital=hospital,
            appointment_date=appointment_datetime.date(),
            start_time=appointment_datetime.time(),
            end_time=(appointment_datetime + timedelta(minutes=30)).time(),
            status='confirmed',
            notes='Test appointment for email functionality'
        )
        
        print(f"Created test appointment: {appointment.id}")
        print(f"Patient email: {patient.user.email}")
        print(f"Provider email: {provider.user.email}")
        
        # Test the appointment reminder service
        reminder_service = AppointmentReminderService()
        
        print("\nTesting immediate confirmation email...")
        
        # Test sending confirmation email directly
        appointment_data = reminder_service._prepare_appointment_data(appointment)
        
        # Debug: Print the appointment data structure
        print(f"DEBUG: Appointment data structure:")
        print(f"  patient_name: {appointment_data.get('patient_name', 'MISSING')}")
        print(f"  provider_name: {appointment_data.get('provider_name', 'MISSING')}")
        print(f"  appointment_date: {appointment_data.get('appointment_date', 'MISSING')}")
        print(f"  location: {appointment_data.get('location', 'MISSING')}")
        print(f"  hospital_name: {appointment_data.get('hospital_name', 'MISSING')}")
        
        # Import the email client
        from notifications.email_client import EmailClient
        
        # Test the email client directly first
        print("Testing email client directly...")
        success, response = EmailClient.send_appointment_confirmation_email(
            appointment_data=appointment_data,
            recipient_email='bouricenos0@gmail.com',
            is_patient=True
        )
        
        if success:
            print(f"✅ Email sent successfully! Response: {response}")
        else:
            print(f"❌ Email failed: {response}")
        
        # Test the full reminder scheduling
        print("\nTesting full reminder scheduling...")
        result = reminder_service.schedule_appointment_reminders(appointment)
        
        if result:
            print("✅ Reminders scheduled successfully!")
        else:
            print("❌ Reminder scheduling failed!")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_email_sending()
    if success:
        print("\n🎉 Email functionality test completed successfully!")
    else:
        print("\n💥 Email functionality test failed!")
        sys.exit(1)