"""
Management command to fix encryption issues and re-encrypt data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import EnhancedPatient
from encryption.key_manager import key_manager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix encryption issues and re-encrypt patient data with current key'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to database',
        )
        parser.add_argument(
            '--patient-id',
            type=str,
            help='Re-encrypt specific patient only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        patient_id = options['patient_id']
        
        self.stdout.write(self.style.SUCCESS('Starting encryption fix...'))
        
        # Define encrypted fields
        encrypted_fields = [
            'phone', 'address_line1', 'address_line2', 'allergies',
            'medical_conditions', 'current_medications', 'insurance_provider',
            'insurance_policy_number', 'insurance_group_number'
        ]
        
        # Get patients to process
        if patient_id:
            patients = EnhancedPatient.objects.filter(id=patient_id)
            if not patients.exists():
                self.stdout.write(self.style.ERROR(f'Patient {patient_id} not found'))
                return
        else:
            patients = EnhancedPatient.objects.all()
        
        total_patients = patients.count()
        self.stdout.write(f'Processing {total_patients} patients...')
        
        fixed_count = 0
        failed_count = 0
        
        try:
            with transaction.atomic():
                for patient in patients:
                    patient_fixed = False
                    
                    for field_name in encrypted_fields:
                        field_value = getattr(patient, field_name)
                        if field_value:
                            self.stdout.write(f'Processing {field_name} for patient {patient.id}...')
                            
                            # Check if this is encrypted data
                            if key_manager.is_encrypted(field_value):
                                self.stdout.write(f'  -> Field appears encrypted, attempting decryption...')
                                
                                # Try to decrypt with current key
                                try:
                                    decrypted = key_manager.decrypt(field_value)
                                    
                                    if decrypted != field_value:
                                        # Decryption successful, now re-encrypt with current key
                                        if not dry_run:
                                            encrypted = key_manager.encrypt(decrypted)
                                            setattr(patient, field_name, encrypted)
                                            patient.save()
                                        
                                        self.stdout.write(
                                            self.style.SUCCESS(f'  ✓ Fixed {field_name}: {decrypted[:20]}...')
                                        )
                                        patient_fixed = True
                                    else:
                                        # Decryption failed, field remains encrypted
                                        self.stdout.write(
                                            self.style.WARNING(f'  ⚠ Could not decrypt {field_name}')
                                        )
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.ERROR(f'  ✗ Error processing {field_name}: {e}')
                                    )
                            else:
                                self.stdout.write(f'  -> Field appears to be plain text: {field_value[:30]}...')
                    
                    if patient_fixed:
                        fixed_count += 1
                    else:
                        failed_count += 1
                    
                    # Progress indicator
                    if (fixed_count + failed_count) % 10 == 0:
                        self.stdout.write(f'Progress: {fixed_count + failed_count}/{total_patients} processed')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Transaction failed: {e}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\nEncryption fix completed!'))
        self.stdout.write(f'  - Total patients processed: {total_patients}')
        self.stdout.write(f'  - Successfully fixed: {fixed_count}')
        self.stdout.write(f'  - Failed to fix: {failed_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('This was a dry run - no changes were made'))