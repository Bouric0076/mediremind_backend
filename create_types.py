import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')

import django
django.setup()

from appointments.models import AppointmentType
from accounts.models import Hospital

hospitals = Hospital.objects.all()
print(f'Found {hospitals.count()} hospitals')

types_data = [
    ('General Consultation', 'CONSULT', 30, '1500.00', '#007bff'),
    ('Follow-up Visit', 'FOLLOWUP', 20, '1000.00', '#28a745'),
    ('Emergency Consultation', 'EMERGENCY', 45, '3000.00', '#dc3545'),
    ('Vaccination', 'VACCINE', 15, '800.00', '#ffc107'),
    ('Laboratory Test', 'LABTEST', 25, '1200.00', '#6f42c1'),
    ('Physical Therapy', 'PHYSTHER', 45, '2500.00', '#fd7e14'),
    ('Dental Checkup', 'DENTAL', 40, '2000.00', '#20c997'),
    ('Specialist Consultation', 'SPECIALIST', 45, '3500.00', '#e83e8c')
]

created = 0
for hospital in hospitals:
    for name, code, duration, cost, color in types_data:
        if not AppointmentType.objects.filter(hospital=hospital, code=code).exists():
            AppointmentType.objects.create(
                hospital=hospital,
                name=name,
                description=f'{name} appointment',
                code=code,
                default_duration=duration,
                buffer_time=10,
                base_cost=cost,
                color_code=color,
                is_active=True
            )
            created += 1
            print(f'Created {name} for {hospital.name}')

print(f'Total appointment types created: {created}')
print(f'Total appointment types in database: {AppointmentType.objects.count()}')