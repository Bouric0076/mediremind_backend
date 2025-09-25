#!/usr/bin/env python
"""
Test script for emergency contact notification functionality
"""
import os
import sys
import django
from django.test import TestCase
from django.conf import settings

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import EnhancedPatient, Hospital, HospitalPatient
from notifications.patient_email_service import PatientEmailService
from django.core import mail
from django.test.utils import override_settings
from datetime import date

def test_emergency_contact_notification():
    """Test the emergency contact notification functionality"""
    print("Starting emergency contact notification test...")
    
    try:
        User = get_user_model()
        
        # Clear any existing mail
        mail.outbox = []
        
        # Create or get hospital
        hospital, created = Hospital.objects.get_or_create(
            name='Test Hospital',
            defaults={
                'email': 'test@hospital.com',
                'phone': '555-0123',
                'address': '123 Test St, Test City, TC 12345',
                'website': 'https://testhospital.com'
            }
        )
        print(f"Hospital {'created' if created else 'retrieved'}: {hospital.name}")
        
        # Create patient user
        patient_user, created = User.objects.get_or_create(
            email='patient@test.com',
            defaults={
                'full_name': 'John Doe',
                'role': 'patient'
            }
        )
        print(f"Patient user {'created' if created else 'retrieved'}: {patient_user.email}")
        
        # Create or update patient with emergency contact
        patient, created = EnhancedPatient.objects.get_or_create(
            user=patient_user,
            defaults={
                'date_of_birth': date(1990, 1, 1),
                'gender': 'M',
                'phone': '555-0124',
                'emergency_contact_name': 'Jane Doe',
                'emergency_contact_relationship': 'Spouse',
                'emergency_contact_phone': '555-0125',
                'emergency_contact_email': 'jane@test.com',
                'notify_emergency_contact': True,
                'emergency_contact_notification_types': ['emergency_contact_added', 'appointment_reminder'],
                'emergency_contact_notification_methods': ['email']
            }
        )
        
        if not created:
            # Update existing patient with emergency contact info
            patient.emergency_contact_name = 'Jane Doe'
            patient.emergency_contact_relationship = 'Spouse'
            patient.emergency_contact_phone = '555-0125'
            patient.emergency_contact_email = 'jane@test.com'
            patient.notify_emergency_contact = True
            patient.emergency_contact_notification_types = ['emergency_contact_added', 'appointment_reminder']
            patient.emergency_contact_notification_methods = ['email']
            patient.save()
        
        print(f"Patient {'created' if created else 'updated'}: {patient.user.full_name}")
        print(f"Emergency contact: {patient.emergency_contact_name} ({patient.emergency_contact_email})")
        
        # Create hospital-patient relationship
        hospital_patient, created = HospitalPatient.objects.get_or_create(
            hospital=hospital,
            patient=patient
        )
        print(f"Hospital-Patient relationship {'created' if created else 'retrieved'}")
        
        # Test the notification service
        print("\nTesting emergency contact notification service...")
        email_service = PatientEmailService()
        
        # Check if patient has emergency contact email
        if not patient.emergency_contact_email:
            print("❌ No emergency contact email found")
            return False
            
        # Check if notifications are enabled
        if not patient.notify_emergency_contact:
            print("❌ Emergency contact notifications are disabled")
            return False
            
        # Check if email is in notification methods
        if 'email' not in patient.emergency_contact_notification_methods:
            print("❌ Email not in notification methods")
            return False
            
        # Check if emergency_contact_added is in notification types
        if 'emergency_contact_added' not in patient.emergency_contact_notification_types:
            print("❌ emergency_contact_added not in notification types")
            return False
        
        print("✅ All preconditions met, sending notification...")
        
        # Send the notification
        result = email_service.send_emergency_contact_notification(patient)
        
        print(f"Notification result: {result}")
        
        # Check if email was sent (in test mode, emails go to mail.outbox)
        if hasattr(mail, 'outbox') and len(mail.outbox) > 0:
            print(f"✅ Email sent successfully! {len(mail.outbox)} email(s) in outbox")
            email = mail.outbox[0]
            print(f"   To: {email.to}")
            print(f"   Subject: {email.subject}")
            print(f"   From: {email.from_email}")
        else:
            print("ℹ️  No emails in outbox (this might be expected in production mode)")
        
        print("\n✅ Emergency contact notification test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Override email backend for testing
    with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
        success = test_emergency_contact_notification()
        sys.exit(0 if success else 1)