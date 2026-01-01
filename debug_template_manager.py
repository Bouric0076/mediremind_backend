#!/usr/bin/env python
"""
Debug script to check template manager processing
"""
import os
import sys
import django
from datetime import datetime, time, date

# Add the project directory to the path
sys.path.insert(0, 'c:/Usersouriocumentsrojectsediremind_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

def test_template_manager():
    """Test the template manager processing"""
    
    from notifications.template_manager import TemplateManager, TemplateContext, RecipientType
    
    # Test data structure from the view
    appointment_data = {
        'id': 'bf97d743-3152-42d4-a282-ea58ec71d829',
        'date': date(2026, 1, 2),
        'time': time(10, 0, 0),
        'type': 'Dental Checkup',
        'patient': 'Test patient',
        'provider': 'New Admin'
    }
    
    print("Original appointment data:")
    for key, value in appointment_data.items():
        print(f"  {key}: {value} (type: {type(value)})")
    
    # Create template context
    context = TemplateContext(
        recipient_name='Test Patient',
        recipient_email='test@example.com',
        recipient_type=RecipientType.PATIENT,
        appointment=appointment_data,
        preferences={},
        links={}
    )
    
    # Initialize template manager
    template_manager = TemplateManager()
    
    # Test personalized context generation
    personalized_context = template_manager.get_personalized_context(context)
    
    print(f"\nPersonalized context appointment data:")
    if 'appointment' in personalized_context:
        for key, value in personalized_context['appointment'].items():
            print(f"  {key}: {value} (type: {type(value)})")
    else:
        print("  No appointment data found!")
    
    # Check if time field is preserved
    if 'appointment' in personalized_context and 'time' in personalized_context['appointment']:
        original_time = appointment_data['time']
        processed_time = personalized_context['appointment']['time']
        print(f"\nTime field comparison:")
        print(f"  Original: {original_time} (type: {type(original_time)})")
        print(f"  Processed: {processed_time} (type: {type(processed_time)})")
        print(f"  Equal: {original_time == processed_time}")
        print(f"  Processed is None: {processed_time is None}")
    else:
        print(f"\nTime field missing from processed context!")
    
    # Test template rendering with processed context
    from django.template.loader import render_to_string
    
    print(f"\nTesting template with processed context...")
    html_message = render_to_string('notifications/email/appointment_confirmation_patient.html', personalized_context)
    
    # Check if TBD appears in the rendered template
    if 'TBD' in html_message:
        print("❌ Found 'TBD' in rendered template!")
        # Find the specific lines with TBD
        lines = html_message.split('\n')
        for i, line in enumerate(lines):
            if 'TBD' in line:
                print(f"  Line {i+1}: {line.strip()}")
    else:
        print("✅ No 'TBD' found in rendered template")

if __name__ == '__main__':
    test_template_manager()