import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
sys.path.append('c:/Users/bouri/Documents/Projects/mediremind_backend')
django.setup()

from accounts.models import EnhancedPatient, EnhancedStaffProfile, HospitalPatient
from appointments.models import AppointmentType

# Find compatible appointment types
print('Finding compatible appointment types for New Test Hospital:')

# Get patient and provider data
patient = EnhancedPatient.objects.first()
provider = EnhancedStaffProfile.objects.first()

if patient and provider:
    # Get patient's hospital
    hospital_patient = HospitalPatient.objects.filter(patient=patient).first()
    if hospital_patient:
        target_hospital = hospital_patient.hospital
        print(f'Target hospital: {target_hospital.name}')
        
        # Find appointment types for this hospital
        compatible_types = AppointmentType.objects.filter(hospital=target_hospital)
        print(f'Found {compatible_types.count()} compatible appointment types:')
        for apt in compatible_types:
            print(f'  - {apt.name} (ID: {apt.id})')
        
        if compatible_types.exists():
            # Test appointment creation
            from appointments.serializers import AppointmentCreateSerializer
            
            appt_type = compatible_types.first()
            print(f'\nTesting with appointment type: {appt_type.name}')
            
            test_data = {
                'patient_id': str(patient.id),
                'provider_id': str(provider.id),
                'appointment_type_id': str(appt_type.id),
                'hospital_id': str(target_hospital.id),
                'appointment_date': '2026-01-02',
                'start_time': '10:00:00',
                'duration': 30,
                'reason': 'Test appointment',
                'title': 'Test appointment title'
            }
            
            print(f'Test data: {test_data}')
            
            serializer = AppointmentCreateSerializer(data=test_data)
            if serializer.is_valid():
                print('✅ Serializer validation passed!')
                try:
                    appointment = serializer.save()
                    print(f'✅ Appointment created successfully!')
                    print(f'Appointment ID: {appointment.id}')
                    print(f'Start time: {appointment.start_time}')
                    print(f'End time: {appointment.end_time}')
                    print(f'Duration: {appointment.duration}')
                    print(f'Patient: {appointment.patient.user.full_name}')
                    print(f'Provider: {appointment.provider.user.full_name}')
                    print(f'Hospital: {appointment.hospital.name}')
                except Exception as e:
                    print(f'❌ Error creating appointment: {e}')
            else:
                print('❌ Serializer validation failed!')
                print(f'Errors: {serializer.errors}')
        else:
            print('❌ No compatible appointment types found for this hospital')
    else:
        print('❌ Patient has no hospital association')
else:
    print('❌ Missing patient or provider data')