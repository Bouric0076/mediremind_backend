#!/usr/bin/env python
"""
Debug script to check Django template rendering issue with datetime.time
"""
import os
import sys
import django
from datetime import datetime, time, date

# Add the project directory to the path
sys.path.insert(0, 'c:/Users/bouri/Documents/Projects/mediremind_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

def test_django_template_issue():
    """Test Django template rendering with datetime.time objects"""
    
    from django.template import Context, Template
    
    # Test data structure from the view
    appointment_data = {
        'id': 'bf97d743-3152-42d4-a282-ea58ec71d829',
        'date': date(2026, 1, 2),
        'time': time(10, 0, 0),
        'type': 'Dental Checkup',
        'patient': 'Test patient',
        'provider': 'New Admin'
    }
    
    print("Testing Django template filters with datetime.time objects:")
    print(f"  Original time: {appointment_data['time']}")
    print(f"  Type: {type(appointment_data['time'])}")
    print(f"  Bool value: {bool(appointment_data['time'])}")
    print(f"  String representation: '{str(appointment_data['time'])}'")
    
    # Test different template filters
    test_templates = [
        '{{ appointment.time|default:"TBD" }}',
        '{{ appointment.time }}',
        '{{ appointment.time|time:"g:i A" }}',
        '{% if appointment.time %}{{ appointment.time }}{% else %}TBD{% endif %}',
        '{{ appointment.time|safe }}',
        '{{ appointment.time|stringformat:"s" }}',
    ]
    
    context = Context({'appointment': appointment_data})
    
    for template_str in test_templates:
        template = Template(template_str)
        result = template.render(context)
        print(f"\n  Template: {template_str}")
        print(f"  Result: '{result}'")
    
    # Test if the issue is with the default filter specifically
    print(f"\n" + "="*60)
    print("Testing if datetime.time is treated as falsy by default filter:")
    
    # Test with different values
    test_values = [
        time(10, 0, 0),
        time(0, 0, 0),  # Midnight
        date(2026, 1, 2),
        datetime(2026, 1, 2, 10, 0, 0),
        None,
        "",
        0,
        "10:00:00"
    ]
    
    default_template = Template('{{ value|default:"TBD" }}')
    
    for test_value in test_values:
        context = Context({'value': test_value})
        result = default_template.render(context)
        print(f"  {test_value} ({type(test_value).__name__}): '{result}'")
    
    # Test the actual issue - maybe the appointment object is being modified
    print(f"\n" + "="*60)
    print("Testing if appointment.time is being accessed correctly:")
    
    # Create a simple test that mimics the template exactly
    exact_template = Template('{{ appointment.time|default:"TBD" }}')
    exact_context = Context({'appointment': appointment_data})
    exact_result = exact_template.render(exact_context)
    print(f"  Direct template test: '{exact_result}'")
    
    # Check if there's any issue with the key access
    print(f"  appointment.get('time'): {appointment_data.get('time')}")
    print(f"  appointment['time']: {appointment_data['time']}")
    print(f"  'time' in appointment: {'time' in appointment_data}")

if __name__ == '__main__':
    test_django_template_issue()