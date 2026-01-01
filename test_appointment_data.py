import os
import sys
import django
from datetime import datetime, time, date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
sys.path.append('c:/Users/bouri/Documents/Projects/mediremind_backend')
django.setup()

from appointments.models import Appointment
from appointments.serializers import AppointmentSerializer, AppointmentCreateSerializer

# Check recent appointments
appointments = Appointment.objects.all().order_by('-created_at')[:3]
print('Recent appointments:')
for appt in appointments:
    print(f'ID: {appt.id}')
    print(f'  Patient: {appt.patient.user.first_name} {appt.patient.user.last_name}')
    print(f'  Date: {appt.appointment_date}')
    print(f'  Start: {appt.start_time}')
    print(f'  End: {appt.end_time}')
    print(f'  Duration: {appt.duration}')
    print('---')

# Test serializer data
if appointments:
    first_appt = appointments[0]
    serializer = AppointmentSerializer(first_appt)
    print('\nSerialized data:')
    data = serializer.data
    print(f"Patient: {data.get('patient', {})}")
    print(f"Start time: {data.get('start_time')}")
    print(f"End time: {data.get('end_time')}")
    print(f"Duration: {data.get('duration')}")
    
    # Test what happens in template manager context
    print('\nTemplate manager context simulation:')
    appointment_context = {
        'id': str(first_appt.id),
        'patient': data.get('patient', {}),
        'start_time': data.get('start_time'),
        'end_time': data.get('end_time'),
        'duration': data.get('duration'),
        'doctor_name': f"{first_appt.provider.user.first_name} {first_appt.provider.user.last_name}",
        'location': getattr(first_appt.room, 'name', 'TBD') if first_appt.room else 'TBD'
    }
    
    print(f"Context start_time: {appointment_context['start_time']}")
    print(f"Context end_time: {appointment_context['end_time']}")
    print(f"Context duration: {appointment_context['duration']}")