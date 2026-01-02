#!/usr/bin/env python3
"""
Test script for the new Resend service with TemplateManager integration.
"""
import os
import sys
import django
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from notifications.resend_service import resend_service

# Use Resend's test domain for development
FROM_EMAIL = "onboarding@resend.dev"

def test_resend_service():
    """Test all Resend service methods with TemplateManager integration."""
    
    print("🧪 Testing Resend Service with TemplateManager Integration")
    print("=" * 60)
    
    # Test data - use real email address for Resend testing
    test_email = "bouricenos0@gmail.com"  # Your actual email for testing
    test_patient_name = "John Doe"
    
    # Test basic email sending first
    print("\n1. Testing Basic Email Sending")
    try:
        success, message = resend_service.send_email(
            to_email=test_email,
            subject="Test Email from Resend",
            html_content="<h1>Hello from MediRemind!</h1><p>This is a test email.</p>",
            from_email=FROM_EMAIL  # Use Resend's test domain
        )
        
        if success:
            print(f"   ✅ Basic email sent successfully: {message}")
        else:
            print(f"   ❌ Failed to send basic email: {message}")
            
    except Exception as e:
        print(f"   ❌ Error testing basic email: {e}")
    
    # Test appointment confirmation
    print("\n1. Testing Appointment Confirmation Email")
    try:
        appointment_details = {
            'date': '2024-01-15',
            'time': '10:00 AM',
            'doctor_name': 'Dr. Smith',
            'location': 'Main Clinic, Room 101',
            'appointment_type': 'Consultation',
            'id': 123,
            'patient_id': 456
        }
        
        success, message = resend_service.send_appointment_confirmation_email(
            to_email=test_email,
            patient_name=test_patient_name,
            appointment_details=appointment_details,
            from_email=FROM_EMAIL  # Use Resend's test domain
        )
        
        if success:
            print(f"   ✅ Appointment confirmation email sent successfully: {message}")
        else:
            print(f"   ❌ Failed to send appointment confirmation: {message}")
            
    except Exception as e:
        print(f"   ❌ Error testing appointment confirmation: {e}")
    
    # Test appointment reminder
    print("\n2. Testing Appointment Reminder Email")
    try:
        appointment_details = {
            'date': '2024-01-16',
            'time': '2:00 PM',
            'doctor_name': 'Dr. Johnson',
            'location': 'Main Clinic, Room 205',
            'appointment_type': 'Follow-up',
            'id': 124,
            'patient_id': 456
        }
        
        success, message = resend_service.send_appointment_reminder_email(
            to_email=test_email,
            patient_name=test_patient_name,
            appointment_details=appointment_details,
            from_email=FROM_EMAIL  # Use Resend's test domain
        )
        
        if success:
            print(f"   ✅ Appointment reminder email sent successfully: {message}")
        else:
            print(f"   ❌ Failed to send appointment reminder: {message}")
            
    except Exception as e:
        print(f"   ❌ Error testing appointment reminder: {e}")
    
    # Test medication reminder
    print("\n3. Testing Medication Reminder Email")
    try:
        success, message = resend_service.send_medication_reminder_email(
            to_email=test_email,
            patient_name=test_patient_name,
            medication_name="Metformin",
            dosage="500mg",
            time="8:00 AM",
            medication_id=789,
            from_email=FROM_EMAIL  # Use Resend's test domain
        )
        
        if success:
            print(f"   ✅ Medication reminder email sent successfully: {message}")
        else:
            print(f"   ❌ Failed to send medication reminder: {message}")
            
    except Exception as e:
        print(f"   ❌ Error testing medication reminder: {e}")
    
    # Test emergency alert
    print("\n4. Testing Emergency Alert Email")
    try:
        success, message = resend_service.send_emergency_alert_email(
            to_email=test_email,
            patient_name=test_patient_name,
            alert_message="Critical blood pressure reading detected",
            severity="critical",
            from_email=FROM_EMAIL  # Use Resend's test domain
        )
        
        if success:
            print(f"   ✅ Emergency alert email sent successfully: {message}")
        else:
            print(f"   ❌ Failed to send emergency alert: {message}")
            
    except Exception as e:
        print(f"   ❌ Error testing emergency alert: {e}")
    
    # Test welcome email
    print("\n5. Testing Welcome Email")
    try:
        success, message = resend_service.send_welcome_email(
            to_email=test_email,
            patient_name=test_patient_name,
            clinic_name="MediRemind Health Center",
            from_email=FROM_EMAIL  # Use Resend's test domain
        )
        
        if success:
            print(f"   ✅ Welcome email sent successfully: {message}")
        else:
            print(f"   ❌ Failed to send welcome email: {message}")
            
    except Exception as e:
        print(f"   ❌ Error testing welcome email: {e}")
    
    # Test appointment update (rescheduled)
    print("\n6. Testing Appointment Update Email (Rescheduled)")
    try:
        appointment_details = {
            'date': '2024-01-17',
            'time': '3:00 PM',
            'doctor_name': 'Dr. Brown',
            'location': 'Main Clinic, Room 103',
            'appointment_type': 'Consultation',
            'id': 125,
            'patient_id': 456,
            'reason': 'Doctor availability changed'
        }
        
        success, message = resend_service.send_appointment_update_email(
            to_email=test_email,
            patient_name=test_patient_name,
            appointment_details=appointment_details,
            update_type='rescheduled',
            from_email=FROM_EMAIL  # Use Resend's test domain
        )
        
        if success:
            print(f"   ✅ Appointment rescheduled email sent successfully: {message}")
        else:
            print(f"   ❌ Failed to send appointment rescheduled email: {message}")
            
    except Exception as e:
        print(f"   ❌ Error testing appointment rescheduled email: {e}")
    
    # Test appointment update (cancelled)
    print("\n7. Testing Appointment Update Email (Cancelled)")
    try:
        appointment_details = {
            'date': '2024-01-18',
            'time': '4:00 PM',
            'doctor_name': 'Dr. Davis',
            'location': 'Main Clinic, Room 107',
            'appointment_type': 'Follow-up',
            'id': 126,
            'patient_id': 456,
            'reason': 'Patient request'
        }
        
        success, message = resend_service.send_appointment_update_email(
            to_email=test_email,
            patient_name=test_patient_name,
            appointment_details=appointment_details,
            update_type='cancelled',
            from_email=FROM_EMAIL  # Use Resend's test domain
        )
        
        if success:
            print(f"   ✅ Appointment cancelled email sent successfully: {message}")
        else:
            print(f"   ❌ Failed to send appointment cancelled email: {message}")
            
    except Exception as e:
        print(f"   ❌ Error testing appointment cancelled email: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Resend Service Testing Complete!")
    print("Note: Check your Resend dashboard for actual email delivery status")

if __name__ == "__main__":
    test_resend_service()