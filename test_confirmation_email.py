#!/usr/bin/env python
"""
Test script for appointment confirmation/update emails
"""
import os
import django
import sys
from datetime import datetime, timedelta

# Add the project directory to the path
sys.path.append('c:\\Users\\bouri\\Documents\\Projects\\mediremind_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

def test_confirmation_email():
    """Test the new send_appointment_update_email method"""
    try:
        from notifications.email_client import EmailClient
        
        # Sample appointment data (similar to what would come from the API)
        appointment_data = {
            'appointment_id': 'test-12345',
            'patient_name': 'Bouric Enos',
            'doctor_name': 'Dr. Test Admin',
            'provider_name': 'Dr. Test Admin',
            'appointment_date': '2026-01-06',
            'appointment_time': '14:30',
            'start_time': datetime.now() + timedelta(days=1),
            'end_time': datetime.now() + timedelta(days=1, hours=1),
            'appointment_type': 'Consultation',
            'duration': 60,
            'location': 'Greenville Health, Room 101',
            'hospital_name': 'Greenville Health',
            'notes': 'Test appointment for confirmation email',
            'status': 'confirmed',
            'specialization': 'General Practice'
        }
        
        print("🧪 Testing appointment confirmation email...")
        
        # Test confirmation email
        success, response = EmailClient.send_appointment_update_email(
            appointment_data=appointment_data,
            update_type='created',
            recipient_email='bouricenos0@gmail.com',
            is_patient=True
        )
        
        if success:
            print(f"✅ Confirmation email sent successfully!")
            print(f"Response: {response}")
        else:
            print(f"❌ Confirmation email failed: {response}")
            return False
            
        print("\n🧪 Testing appointment rescheduled email...")
        
        # Test rescheduled email
        success, response = EmailClient.send_appointment_update_email(
            appointment_data=appointment_data,
            update_type='rescheduled',
            recipient_email='bouricenos0@gmail.com',
            is_patient=True
        )
        
        if success:
            print(f"✅ Rescheduled email sent successfully!")
            print(f"Response: {response}")
        else:
            print(f"❌ Rescheduled email failed: {response}")
            return False
            
        print("\n🧪 Testing appointment cancellation email...")
        
        # Test cancellation email
        success, response = EmailClient.send_appointment_update_email(
            appointment_data=appointment_data,
            update_type='cancellation',
            recipient_email='bouricenos0@gmail.com',
            is_patient=True
        )
        
        if success:
            print(f"✅ Cancellation email sent successfully!")
            print(f"Response: {response}")
        else:
            print(f"❌ Cancellation email failed: {response}")
            return False
            
        print("\n🧪 Testing no-show alert email (to doctor)...")
        
        # Test no-show alert to doctor
        success, response = EmailClient.send_appointment_update_email(
            appointment_data=appointment_data,
            update_type='no-show',
            recipient_email='admin@mediremind.test',
            is_patient=False  # Send to doctor
        )
        
        if success:
            print(f"✅ No-show alert sent successfully!")
            print(f"Response: {response}")
        else:
            print(f"❌ No-show alert failed: {response}")
            return False
            
        print("\n🎉 All appointment update email tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_confirmation_email()
    sys.exit(0 if success else 1)