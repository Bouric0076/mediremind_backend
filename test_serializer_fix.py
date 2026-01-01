import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
sys.path.append('c:/Users/bouri/Documents/Projects/mediremind_backend')
django.setup()

from appointments.serializers import UserBasicSerializer
from authentication.models import User

# Test the fixed serializer
print('Testing UserBasicSerializer fix:')
users = User.objects.all()[:3]
for user in users:
    print(f'\nUser: {user.email}')
    print(f'  full_name: "{user.full_name}"')
    print(f'  get_full_name(): "{user.get_full_name()}"')
    
    serializer = UserBasicSerializer(user)
    data = serializer.data
    print(f'  Serialized first_name: "{data.get("first_name")}"')
    print(f'  Serialized last_name: "{data.get("last_name")}"')
    print(f'  Serialized full_name: "{data.get("full_name")}"')

# Test with the appointment serializer
from appointments.models import Appointment
appointments = Appointment.objects.all().order_by('-created_at')[:2]
print('\n\nTesting AppointmentSerializer with patient data:')
for appt in appointments:
    print(f'\nAppointment ID: {appt.id}')
    serializer = AppointmentSerializer(appt)
    data = serializer.data
    patient_data = data.get('patient', {})
    user_data = patient_data.get('user', {})
    print(f'  Patient user first_name: "{user_data.get("first_name")}"')
    print(f'  Patient user last_name: "{user_data.get("last_name")}"')
    print(f'  Patient user full_name: "{user_data.get("full_name")}"')