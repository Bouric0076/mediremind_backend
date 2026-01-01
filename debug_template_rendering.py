#!/usr/bin/env python
"""
Debug script to check appointment email data structure - focused test
"""
import os
import sys
import django
from datetime import datetime, time, date

# Add the project directory to the path
sys.path.insert(0, 'c:/Users/bouri/Documents/Projects/mediremind_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

def test_template_rendering():
    """Test the exact template rendering issue"""
    
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
    
    # Test Django template rendering
    from django.template import Context, Template
    
    # Test the specific template logic that's failing
    template_str = '{{ appointment.time|default:"TBD" }}'
    template = Template(template_str)
    context = Context({'appointment': appointment_data})
    result = template.render(context)
    print(f"\nTemplate test result: '{result}'")
    
    # Test if the time object is being treated as falsy
    print(f"\nTime object analysis:")
    print(f"  bool(appointment_data['time']): {bool(appointment_data['time'])}")
    print(f"  appointment_data['time'] is None: {appointment_data['time'] is None}")
    print(f"  str(appointment_data['time']): '{str(appointment_data['time'])}'")
    
    # Test with different time formats
    test_cases = [
        time(10, 0, 0),
        datetime(2026, 1, 2, 10, 0, 0),
        "10:00:00",
        "10:00",
        None,
        ""
    ]
    
    print(f"\nTesting different time formats:")
    for test_time in test_cases:
        test_data = {'appointment': {'time': test_time}}
        test_context = Context(test_data)
        test_result = template.render(test_context)
        print(f"  {test_time} ({type(test_time)}): '{test_result}'")
    
    # Test the actual template rendering
    from django.template.loader import render_to_string
    
    print(f"\nTesting full template rendering...")
    html_message = render_to_string('notifications/email/appointment_confirmation_patient.html', {
        'appointment': appointment_data,
        'recipient_name': 'Test Patient',
    })
    
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
    test_template_rendering()