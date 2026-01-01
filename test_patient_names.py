import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
sys.path.append('c:/Users/bouri/Documents/Projects/mediremind_backend')
django.setup()

from appointments.models import Appointment
from accounts.models import EnhancedPatient

# Check patient data more thoroughly
appointments = Appointment.objects.all().order_by('-created_at')[:3]
print('Patient data investigation:')
for appt in appointments:
    print(f'\nAppointment ID: {appt.id}')
    print(f'Patient ID: {appt.patient.id}')
    print(f'Patient User ID: {appt.patient.user.id}')
    print(f'Patient User first_name: "{appt.patient.user.first_name}"')
    print(f'Patient User last_name: "{appt.patient.user.last_name}"')
    print(f'Patient User email: "{appt.patient.user.email}"')
    
    # Check if patient has encrypted data
    try:
        print(f'Patient phone: "{appt.patient.phone}"')
        print(f'Patient emergency_contact_name: "{appt.patient.emergency_contact_name}"')
        print(f'Patient emergency_contact_phone: "{appt.patient.emergency_contact_phone}"')
    except Exception as e:
        print(f'Error accessing patient encrypted fields: {e}')

# Check if there are patients with proper names
print('\n\nChecking all patients for proper names:')
patients = EnhancedPatient.objects.all()[:5]
for patient in patients:
    print(f'Patient ID: {patient.id}')
    print(f'  Name: "{patient.user.first_name}" "{patient.user.last_name}"')
    print(f'  Email: "{patient.user.email}"')
    print(f'  Full name method: "{patient.user.get_full_name()}"')
    print('---')