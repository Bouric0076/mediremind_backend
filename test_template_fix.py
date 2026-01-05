#!/usr/bin/env python
"""
Test script to verify template field mapping fix
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from notifications.template_manager import TemplateManager
from notifications.types import TemplateContext, TemplateType

def test_template_field_mapping():
    """Test that template field mapping works correctly with API response fields"""
    
    # Sample appointment data from API response (using correct field names)
    appointment_data = {
        'id': 1,
        'appointment_date': '2025-01-05',
        'start_time': '14:00:00',
        'appointment_type_name': 'General Consultation',
        'provider_name': 'Test Admin',  # This should appear in the email
        'patient_name': 'John Doe',
        'location': 'Main Hospital',
        'hospital_name': 'MediRemind Partner Clinic'
    }
    
    # Create template context
    context = TemplateContext(
        recipient_name='John Doe',
        appointment=appointment_data,
        template_type=TemplateType.APPOINTMENT_CONFIRMATION_PATIENT,
        links={
            'support': 'https://support.mediremind.com',
            'portal': 'https://portal.mediremind.com',
            'unsubscribe': 'https://unsubscribe.mediremind.com',
            'privacy': 'https://privacy.mediremind.com'
        },
        preferences={
            'include_weather': False,
            'include_preparation_tips': True
        }
    )
    
    # Initialize template manager
    template_manager = TemplateManager()
    
    # Get personalized context
    personalized_context = template_manager.get_personalized_context(context)
    
    print("=== Template Field Mapping Test ===")
    print(f"Original appointment data keys: {list(appointment_data.keys())}")
    print(f"Mapped appointment data keys: {list(personalized_context['appointment'].keys())}")
    print()
    
    # Check if API response field names are available
    appointment = personalized_context['appointment']
    
    print("=== Field Mapping Results ===")
    print(f"✓ provider_name: {appointment.get('provider_name', 'MISSING')}")
    print(f"✓ appointment_date: {appointment.get('appointment_date', 'MISSING')}")
    print(f"✓ start_time: {appointment.get('start_time', 'MISSING')}")
    print()
    
    # Check if legacy fields are also available for backward compatibility
    print("=== Backward Compatibility Check ===")
    print(f"✓ doctor_name: {appointment.get('doctor_name', 'MISSING')}")
    print(f"✓ date: {appointment.get('date', 'MISSING')}")
    print(f"✓ time: {appointment.get('time', 'MISSING')}")
    print()
    
    # Test template rendering
    print("=== Template Rendering Test ===")
    try:
        # Get the template content
        template_content = template_manager.get_template_content(TemplateType.APPOINTMENT_CONFIRMATION_PATIENT)
        
        # Render with context
        rendered = template_manager.render_template(
            template_content,
            personalized_context,
            TemplateType.APPOINTMENT_CONFIRMATION_PATIENT
        )
        
        # Check if correct values appear in rendered content
        if 'Test Admin' in rendered:
            print("✓ Correct provider name (Test Admin) found in rendered template")
        else:
            print("✗ Correct provider name (Test Admin) NOT found in rendered template")
            
        if '2025-01-05' in rendered:
            print("✓ Correct date (2025-01-05) found in rendered template")
        else:
            print("✗ Correct date (2025-01-05) NOT found in rendered template")
            
        if '14:00:00' in rendered:
            print("✓ Correct time (14:00:00) found in rendered template")
        else:
            print("✗ Correct time (14:00:00) NOT found in rendered template")
            
        # Check that defaults are not being used
        if 'Dr. Smith' not in rendered:
            print("✓ Default 'Dr. Smith' not found (good - using actual provider name)")
        else:
            print("✗ Default 'Dr. Smith' still found (template might be using wrong field)")
            
        if 'TBD' not in rendered:
            print("✓ Default 'TBD' not found (good - using actual date/time)")
        else:
            print("✗ Default 'TBD' still found (template might be using wrong field)")
            
    except Exception as e:
        print(f"✗ Template rendering failed: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == '__main__':
    test_template_field_mapping()