from appointments.models import AppointmentType
from accounts.models import Hospital

def create_default_appointment_types():
    hospitals = Hospital.objects.all()
    
    default_types = [
        {'name': 'General Consultation', 'code': 'CONSULT', 'duration': 30, 'cost': '1500.00', 'color': '#007bff'},
        {'name': 'Follow-up Visit', 'code': 'FOLLOWUP', 'duration': 20, 'cost': '1000.00', 'color': '#28a745'},
        {'name': 'Emergency Consultation', 'code': 'EMERGENCY', 'duration': 45, 'cost': '3000.00', 'color': '#dc3545'},
        {'name': 'Vaccination', 'code': 'VACCINE', 'duration': 15, 'cost': '800.00', 'color': '#ffc107'},
        {'name': 'Laboratory Test', 'code': 'LABTEST', 'duration': 25, 'cost': '1200.00', 'color': '#6f42c1'},
        {'name': 'Physical Therapy', 'code': 'PHYSTHER', 'duration': 45, 'cost': '2500.00', 'color': '#fd7e14'},
        {'name': 'Dental Checkup', 'code': 'DENTAL', 'duration': 40, 'cost': '2000.00', 'color': '#20c997'},
        {'name': 'Specialist Consultation', 'code': 'SPECIALIST', 'duration': 45, 'cost': '3500.00', 'color': '#e83e8c'}
    ]
    
    created = 0
    for hospital in hospitals:
        for type_config in default_types:
            if not AppointmentType.objects.filter(hospital=hospital, code=type_config['code']).exists():
                AppointmentType.objects.create(
                    hospital=hospital,
                    name=type_config['name'],
                    description=f'{type_config["name"]} appointment',
                    code=type_config['code'],
                    default_duration=type_config['duration'],
                    buffer_time=10,
                    base_cost=type_config['cost'],
                    color_code=type_config['color'],
                    is_active=True
                )
                created += 1
    
    print(f"Created {created} appointment types")
    print(f"Total types now: {AppointmentType.objects.count()}")

if __name__ == "__main__":
    create_default_appointment_types()