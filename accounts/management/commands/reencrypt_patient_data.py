from django.core.management.base import BaseCommand
from accounts.models import EnhancedPatient
from django.db import transaction

class Command(BaseCommand):
    help = 'Re-encrypt patient data with fresh sample data'

    def handle(self, *args, **options):
        self.stdout.write('Re-encrypting patient data...')
        
        # Sample data for re-encryption
        sample_data = [
            {
                'email': 'patient1@test.com',
                'address_line1': '123 Main Street',
                'address_line2': 'Apt 4B',
                'city': 'New York',
                'state': 'NY',
                'zip_code': '10001',
                'emergency_contact_name': 'Jane Smith',
                'emergency_contact_phone': '+1234567891',
                'emergency_contact_email': 'jane.smith@email.com',
                'allergies': 'Penicillin, Shellfish',
                'current_medications': 'Lisinopril 10mg daily',
                'insurance_provider': 'Blue Cross',
                'insurance_policy_number': 'BCBS123456',
            },
            {
                'email': 'patient2@test.com',
                'address_line1': '456 Oak Avenue',
                'address_line2': '',
                'city': 'Los Angeles',
                'state': 'CA',
                'zip_code': '90210',
                'emergency_contact_name': 'Mike Johnson',
                'emergency_contact_phone': '+1987654321',
                'emergency_contact_email': 'mike.johnson@email.com',
                'allergies': 'Peanuts, Latex',
                'current_medications': 'Metformin 500mg twice daily',
                'insurance_provider': 'Aetna',
                'insurance_policy_number': 'AET987654',
            },
            {
                'email': 'patient3@test.com',
                'address_line1': '789 Pine Street',
                'address_line2': 'Unit 12',
                'city': 'Chicago',
                'state': 'IL',
                'zip_code': '60601',
                'emergency_contact_name': 'Lisa Brown',
                'emergency_contact_phone': '+1555123456',
                'emergency_contact_email': 'lisa.brown@email.com',
                'allergies': 'Aspirin, Sulfa drugs',
                'current_medications': 'Atorvastatin 20mg daily',
                'insurance_provider': 'Cigna',
                'insurance_policy_number': 'CIG456789',
            },
            {
                'email': 'patient4@test.com',
                'address_line1': '321 Elm Drive',
                'address_line2': '',
                'city': 'Houston',
                'state': 'TX',
                'zip_code': '77001',
                'emergency_contact_name': 'Robert Davis',
                'emergency_contact_phone': '+1444555666',
                'emergency_contact_email': 'robert.davis@email.com',
                'allergies': 'Codeine, Iodine',
                'current_medications': 'Levothyroxine 75mcg daily',
                'insurance_provider': 'UnitedHealth',
                'insurance_policy_number': 'UHC789123',
            },
            {
                'email': 'patient5@test.com',
                'address_line1': '654 Maple Lane',
                'address_line2': 'Suite 8',
                'city': 'Phoenix',
                'state': 'AZ',
                'zip_code': '85001',
                'emergency_contact_name': 'Maria Wilson',
                'emergency_contact_phone': '+1333444555',
                'emergency_contact_email': 'maria.wilson@email.com',
                'allergies': 'Morphine, Contrast dye',
                'current_medications': 'Amlodipine 5mg daily',
                'insurance_provider': 'Humana',
                'insurance_policy_number': 'HUM123789',
            }
        ]
        
        for data in sample_data:
            try:
                patient = EnhancedPatient.objects.select_related('user').get(
                    user__email=data['email']
                )
                
                # Update encrypted fields
                patient.address_line1 = data['address_line1']
                patient.address_line2 = data['address_line2']
                patient.city = data['city']
                patient.state = data['state']
                patient.zip_code = data['zip_code']
                patient.emergency_contact_name = data['emergency_contact_name']
                patient.emergency_contact_phone = data['emergency_contact_phone']
                patient.emergency_contact_email = data['emergency_contact_email']
                patient.allergies = data['allergies']
                patient.current_medications = data['current_medications']
                patient.insurance_provider = data['insurance_provider']
                patient.insurance_policy_number = data['insurance_policy_number']
                
                patient.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Updated patient: {patient.user.full_name}')
                )
                
            except EnhancedPatient.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Patient not found: {data["email"]}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error updating {data["email"]}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Patient data re-encryption completed!')
        )