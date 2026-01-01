import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
sys.path.append('c:/Users/bouri/Documents/Projects/mediremind_backend')
django.setup()

from accounts.models import EnhancedPatient, EnhancedStaffProfile, HospitalPatient
from appointments.models import AppointmentType

# Test appointment creation serializer
print('Testing AppointmentCreateSerializer:')

# Get test data - use any available staff member
patient = EnhancedPatient.objects.first()
provider = EnhancedStaffProfile.objects.first()  # Use any available staff
appt_type = AppointmentType.objects.first()

if patient and provider and appt_type:
    print(f'Using patient: {patient.user.full_name} ({patient.user.email})')
    
    # Get the hospital patient relationship
    hospital_patient = HospitalPatient.objects.filter(patient=patient).first()
    if hospital_patient:
        print(f'  Patient hospital: {hospital_patient.hospital.name}')
    else:
        print('  Patient has no hospital association')
    
    print(f'Using provider: {provider.user.full_name} (Role: {provider.user.role})')
    print(f'  Provider hospital: {provider.hospital.name if provider.hospital else "None"}')
    print(f'Using appointment type: {appt_type.name}')
    print(f'  Appointment type hospital: {appt_type.hospital.name if appt_type.hospital else "None"}')
    
    if hospital_patient and provider.hospital and appt_type.hospital:
        # Check if they all belong to the same hospital
        same_hospital = (hospital_patient.hospital == provider.hospital == appt_type.hospital)
        print(f'\nAll belong to same hospital: {same_hospital}')
        
        if same_hospital:
            # Test data - include hospital_id
            test_data = {
                'patient_id': str(patient.id),
                'provider_id': str(provider.id),
                'appointment_type_id': str(appt_type.id),
                'hospital_id': str(provider.hospital.id),  # Use provider's hospital
                'appointment_date': '2026-01-02',
                'start_time': '10:00:00',
                'duration': 30,
                'reason': 'Test appointment',
                'title': 'Test appointment title'
            }
            
            print(f'\nTest data: {test_data}')
            
            # Test serializer validation
            from appointments.serializers import AppointmentCreateSerializer
            serializer = AppointmentCreateSerializer(data=test_data)
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
                except Exception as e:
                    print(f'❌ Error creating appointment: {e}')
            else:
                print('❌ Serializer validation failed!')
                print(f'Errors: {serializer.errors}')
        else:
            print('❌ Cannot create appointment - patient, provider, and appointment type must belong to the same hospital')
    else:
        print('❌ Missing hospital associations')
else:
    print('❌ Missing required test data (patient, provider, or appointment type)')
    print(f'Patient: {patient}')
    print(f'Provider: {provider}')
    print(f'Appointment type: {appt_type}')