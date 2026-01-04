#!/usr/bin/env python3
"""
Focused end-to-end test for notification system validation.
Tests the complete notification flow with real error handling.
"""

import os
import sys
import django
from unittest.mock import patch, MagicMock

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind.settings')
django.setup()

from notifications.email_client import EmailClient
from notifications.template_manager import template_manager, TemplateType
from notifications.error_handler import notification_error_handler

def test_appointment_creation_notification_flow():
    """Test the complete appointment creation notification flow"""
    print("Testing appointment creation notification flow...")
    
    # Mock appointment data that matches API response structure
    appointment_data = {
        'id': 123,
        'patient': {
            'id': 456,
            'name': 'John Doe',
            'email': 'john.doe@email.com',
            'phone': '+1234567890'
        },
        'doctor': {
            'id': 789,
            'name': 'Dr. Smith',
            'email': 'dr.smith@clinic.com',
            'specialization': 'Cardiology'
        },
        'appointment_date': '2024-01-15',
        'appointment_time': '14:30',
        'duration': 30,
        'appointment_type': 'Consultation',
        'location': {
            'clinic_name': 'MediRemind Clinic',
            'address': '123 Medical St, Health City',
            'room': 'Room 101'
        },
        'status': 'scheduled',
        'notes': 'Initial consultation'
    }
    
    # Test template rendering
    print("1. Testing template rendering...")
    try:
        template_result = template_manager.render_template(
            TemplateType.APPOINTMENT_CREATION,
            {
                'appointment': appointment_data,
                'patient': appointment_data['patient'],
                'doctor': appointment_data['doctor'],
                'clinic_name': appointment_data['location']['clinic_name']
            }
        )
        
        if template_result['success']:
            print("✓ Template rendering successful")
            print(f"  Subject: {template_result['subject']}")
            print(f"  Has HTML content: {'Yes' if template_result['html_content'] else 'No'}")
        else:
            print(f"✗ Template rendering failed: {template_result['error']}")
            return False
            
    except Exception as e:
        print(f"✗ Template rendering error: {e}")
        error_context = notification_error_handler.handle_template_error(
            error=e,
            template_type=TemplateType.APPOINTMENT_CREATION,
            context_data={'appointment_id': appointment_data['id']}
        )
        print(f"  Error context captured: {error_context}")
        return False
    
    # Test email sending with error handling
    print("2. Testing email sending with error handling...")
    email_client = EmailClient()
    
    # Test patient email
    try:
        success, message = email_client.send_appointment_creation_email(
            appointment_data=appointment_data,
            recipient_email=appointment_data['patient']['email'],
            recipient_type='patient'
        )
        
        if success:
            print("✓ Patient creation email sent successfully")
        else:
            print(f"✗ Patient creation email failed: {message}")
            return False
            
    except Exception as e:
        print(f"✗ Patient email error: {e}")
        error_context = notification_error_handler.handle_email_error(
            error=e,
            context_data={
                'appointment_id': appointment_data['id'],
                'recipient_email': appointment_data['patient']['email'],
                'recipient_type': 'patient'
            }
        )
        print(f"  Error context captured: {error_context}")
        return False
    
    # Test doctor email
    try:
        success, message = email_client.send_appointment_creation_email(
            appointment_data=appointment_data,
            recipient_email=appointment_data['doctor']['email'],
            recipient_type='doctor'
        )
        
        if success:
            print("✓ Doctor creation email sent successfully")
        else:
            print(f"✗ Doctor creation email failed: {message}")
            return False
            
    except Exception as e:
        print(f"✗ Doctor email error: {e}")
        error_context = notification_error_handler.handle_email_error(
            error=e,
            context_data={
                'appointment_id': appointment_data['id'],
                'recipient_email': appointment_data['doctor']['email'],
                'recipient_type': 'doctor'
            }
        )
        print(f"  Error context captured: {error_context}")
        return False
    
    print("✓ Appointment creation notification flow completed successfully!")
    return True

def test_error_handling_integration():
    """Test error handling integration in notification system"""
    print("\nTesting error handling integration...")
    
    # Test template error handling
    print("1. Testing template error handling...")
    try:
        # Try to render with invalid template type
        template_manager.render_template(
            "INVALID_TEMPLATE_TYPE",
            {}
        )
        print("✗ Should have raised an error for invalid template type")
        return False
    except Exception as e:
        error_context = notification_error_handler.handle_template_error(
            error=e,
            template_type="INVALID_TEMPLATE_TYPE",
            context_data={'test': 'error_handling'}
        )
        print(f"✓ Template error handled correctly: {type(e).__name__}")
        print(f"  Error context: {error_context}")
    
    # Test email error handling with invalid email
    print("2. Testing email error handling...")
    email_client = EmailClient()
    
    try:
        success, message = email_client.send_appointment_creation_email(
            appointment_data={'id': 999},
            recipient_email='invalid-email-format',
            recipient_type='patient'
        )
        print(f"✗ Should have failed with invalid email, got: success={success}, message={message}")
        return False
    except Exception as e:
        error_context = notification_error_handler.handle_email_error(
            error=e,
            context_data={
                'appointment_id': 999,
                'recipient_email': 'invalid-email-format',
                'recipient_type': 'patient'
            }
        )
        print(f"✓ Email error handled correctly: {type(e).__name__}")
        print(f"  Error context: {error_context}")
    
    print("✓ Error handling integration test completed!")
    return True

def main():
    """Main test function"""
    print("=== Notification System End-to-End Testing ===\n")
    
    # Test appointment creation flow
    creation_test_passed = test_appointment_creation_notification_flow()
    
    # Test error handling
    error_test_passed = test_error_handling_integration()
    
    # Summary
    print(f"\n=== Test Results ===")
    print(f"Appointment Creation Flow: {'PASSED' if creation_test_passed else 'FAILED'}")
    print(f"Error Handling Integration: {'PASSED' if error_test_passed else 'FAILED'}")
    
    if creation_test_passed and error_test_passed:
        print("\n✓ All tests passed! Notification system is working correctly.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())