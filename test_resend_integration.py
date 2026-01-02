#!/usr/bin/env python
"""
Test script to verify Resend service integration with TemplateManager
"""
import os
import django
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from notifications.resend_service import resend_service
from notifications.models import NotificationLog

def test_appointment_confirmation():
    """Test appointment confirmation email"""
    print("Testing appointment confirmation email...")
    try:
        appointment_details = {
            'date': '2024-01-15',
            'time': '14:30',
            'doctor_name': 'Dr. Smith',
            'location': 'MediRemind Clinic',
            'appointment_type': 'Consultation',
            'id': 'APT123'
        }
        success, message = resend_service.send_appointment_confirmation_email(
            to_email="test@example.com",
            patient_name="John Doe",
            appointment_details=appointment_details
        )
        print(f"✅ Appointment confirmation: {'Success' if success else 'Failed'} - {message}")
        return success
    except Exception as e:
        print(f"❌ Appointment confirmation error: {e}")
        return False

def test_medication_reminder():
    """Test medication reminder email"""
    print("Testing medication reminder email...")
    try:
        success, message = resend_service.send_medication_reminder_email(
            to_email="test@example.com",
            patient_name="John Doe",
            medication_name="Aspirin",
            dosage="100mg",
            time="08:00 AM",
            medication_id=123
        )
        print(f"✅ Medication reminder: {'Success' if success else 'Failed'} - {message}")
        return success
    except Exception as e:
        print(f"❌ Medication reminder error: {e}")
        return False

def test_emergency_alert():
    """Test emergency alert email"""
    print("Testing emergency alert email...")
    try:
        success, message = resend_service.send_emergency_alert_email(
            to_email="test@example.com",
            patient_name="John Doe",
            alert_message="Patient has missed critical medication for 3 consecutive days",
            severity="high"
        )
        print(f"✅ Emergency alert: {'Success' if success else 'Failed'} - {message}")
        return success
    except Exception as e:
        print(f"❌ Emergency alert error: {e}")
        return False

def test_welcome_email():
    """Test welcome email"""
    print("Testing welcome email...")
    try:
        success, message = resend_service.send_welcome_email(
            to_email="test@example.com",
            patient_name="John Doe",
            clinic_name="MediRemind Clinic"
        )
        print(f"✅ Welcome email: {'Success' if success else 'Failed'} - {message}")
        return success
    except Exception as e:
        print(f"❌ Welcome email error: {e}")
        return False

def test_appointment_reminder():
    """Test appointment reminder email"""
    print("Testing appointment reminder email...")
    try:
        appointment_details = {
            'date': '2024-01-15',
            'time': '14:30',
            'doctor_name': 'Dr. Smith',
            'location': 'MediRemind Clinic',
            'appointment_type': 'Consultation',
            'id': 'APT123'
        }
        success, message = resend_service.send_appointment_reminder_email(
            to_email="test@example.com",
            patient_name="John Doe",
            appointment_details=appointment_details
        )
        print(f"✅ Appointment reminder: {'Success' if success else 'Failed'} - {message}")
        return success
    except Exception as e:
        print(f"❌ Appointment reminder error: {e}")
        return False

def test_appointment_update():
    """Test appointment update email"""
    print("Testing appointment update email...")
    try:
        appointment_details = {
            'date': '2024-01-15',
            'time': '14:30',
            'doctor_name': 'Dr. Smith',
            'location': 'MediRemind Clinic',
            'appointment_type': 'Consultation',
            'id': 'APT123',
            'old_date': '2024-01-14',
            'old_time': '15:00'
        }
        success, message = resend_service.send_appointment_update_email(
            to_email="test@example.com",
            patient_name="John Doe",
            appointment_details=appointment_details,
            update_type='rescheduled'
        )
        print(f"✅ Appointment update: {'Success' if success else 'Failed'} - {message}")
        return success
    except Exception as e:
        print(f"❌ Appointment update error: {e}")
        return False

def check_notification_logs():
    """Check recent notification logs"""
    print("\n📊 Recent Notification Logs:")
    recent_logs = NotificationLog.objects.filter(
        delivery_method='email'
    ).order_by('-created_at')[:10]
    
    if recent_logs:
        for log in recent_logs:
            print(f"  - {log.created_at}: {log.delivery_method} to patient {log.patient_id} - {'✅ Success' if log.status == 'sent' else '❌ Failed'}")
    else:
        print("  No recent email notification logs found.")

def main():
    """Run all tests"""
    print("🧪 Testing Resend Service Integration with TemplateManager")
    print("=" * 60)
    
    # Test all email methods
    tests = [
        test_appointment_confirmation,
        test_medication_reminder,
        test_emergency_alert,
        test_welcome_email,
        test_appointment_reminder,
        test_appointment_update
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()  # Add spacing between tests
    
    # Summary
    passed = sum(results)
    total = len(results)
    print(f"📈 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Resend service integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    # Check notification logs
    check_notification_logs()

if __name__ == "__main__":
    main()