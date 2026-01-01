import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
sys.path.append('c:/Users/bouri/Documents/Projects/mediremind_backend')
django.setup()

from accounts.models import EnhancedPatient, EnhancedStaffProfile, HospitalPatient, User
from appointments.models import AppointmentType
from appointments.serializers import AppointmentCreateSerializer

# Test appointment creation serializer with proper context
print('Testing AppointmentCreateSerializer with proper context:')

# Get test data
patient = EnhancedPatient.objects.first()
provider = EnhancedStaffProfile.objects.first()

# Get the patient's hospital
hospital_patient = HospitalPatient.objects.filter(patient=patient).first()
if hospital_patient:
    target_hospital = hospital_patient.hospital
    print(f'Target hospital: {target_hospital.name}')
    
    # Find appointment types for this hospital
    compatible_types = AppointmentType.objects.filter(hospital=target_hospital)
    print(f'Found {compatible_types.count()} compatible appointment types')
    
    if compatible_types.exists():
        appt_type = compatible_types.first()
        print(f'Using appointment type: {appt_type.name}')
        
        print(f'Using patient: {patient.user.full_name} ({patient.user.email})')
        print(f'Using provider: {provider.user.full_name} (Role: {provider.user.role})')
        
        # Test data (without hospital_id - it's set in context)
        test_data = {
            'patient_id': str(patient.id),
            'provider_id': str(provider.id),
            'appointment_type_id': str(appt_type.id),
            'appointment_date': '2026-01-02',
            'start_time': '10:00:00',
            'duration': 30,
            'reason': 'Test appointment',
            'title': 'Test appointment title'
        }
        
        print(f'\nTest data: {test_data}')
        
        # Use a real user for the context (the provider)
        context = {
            'user': provider.user,  # Use the provider's user object
            'hospital': target_hospital
        }
        
        serializer = AppointmentCreateSerializer(data=test_data, context=context)
        if serializer.is_valid():
            print('✅ Serializer validation passed!')
            print(f'Validated data: {serializer.validated_data}')
            
            # Test saving
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
                print(f'Created by: {appointment.created_by.full_name}')
            except Exception as e:
                print(f'❌ Error creating appointment: {e}')
        else:
            print('❌ Serializer validation failed!')
            print(f'Errors: {serializer.errors}')
    else:
        print('❌ No compatible appointment types found')
else:
    print('❌ Patient has no hospital association')