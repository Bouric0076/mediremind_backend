#!/usr/bin/env python
"""
Debug script to check appointment email data structure
"""
import os
import sys
import django
from datetime import datetime, time, date

# Add the project directory to the path
sys.path.insert(0, 'c:/Users/bouri/Documents/Projects/mediremind_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from appointments.models import Appointment
from notifications.email_client import EmailClient

def debug_appointment_email():
    """Debug the appointment email data structure"""
    
    # Get the most recent appointment
    try:
        appointment = Appointment.objects.latest('created_at')
        print(f"Found appointment: {appointment.id}")
        print(f"  Date: {appointment.appointment_date}")
        print(f"  Time: {appointment.start_time}")
        print(f"  Type: {appointment.appointment_type.name}")
        print(f"  Patient: {appointment.patient.user.get_full_name()}")
        print(f"  Provider: {appointment.provider.user.get_full_name()}")
        
        # Recreate the appointment_data structure from the view
        appointment_data = {
            'id': appointment.id,
            'date': appointment.appointment_date,
            'time': appointment.start_time,
            'type': appointment.appointment_type.name,
            'patient': appointment.patient.user.get_full_name(),
            'provider': appointment.provider.user.get_full_name()
        }
        
        print(f"\nAppointment data structure:")
        for key, value in appointment_data.items():
            print(f"  {key}: {value} (type: {type(value)})")
        
        # Test template rendering
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        print(f"\nTesting template rendering...")
        html_message = render_to_string('notifications/email/appointment_confirmation_patient.html', {
            'appointment': appointment_data,
            'recipient_name': appointment.patient.user.get_full_name(),
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
            
        # Check what the time field actually contains
        print(f"\nTime field analysis:")
        print(f"  appointment_data['time']: {appointment_data['time']}")
        print(f"  type: {type(appointment_data['time'])}")
        print(f"  bool(appointment_data['time']): {bool(appointment_data['time'])}")
        
        # Test the Django template rendering
        from django.template import Context, Template
        
        # Test the specific template logic
        template_str = '{{ appointment.time|default:"TBD" }}'
        template = Template(template_str)
        context = Context({'appointment': appointment_data})
        result = template.render(context)
        print(f"\nTemplate test result: '{result}'")
        
    except Appointment.DoesNotExist:
        print("No appointments found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_appointment_email()