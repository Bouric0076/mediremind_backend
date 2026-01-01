#!/usr/bin/env python
"""
Fix legacy encryption issues by identifying and re-encrypting data with the current key
"""
import os
import django
from django.core.management.base import BaseCommand
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from accounts.models import EnhancedPatient
from encryption.key_manager import key_manager
from cryptography.fernet import Fernet

class Command(BaseCommand):
    help = 'Fix legacy encryption issues and re-encrypt patient data with current key'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making any changes',
        )
        parser.add_argument(
            '--patient-id',
            type=str,
            help='Process specific patient by ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        patient_id = options['patient_id']
        
        self.stdout.write(self.style.SUCCESS('Starting encryption fix...'))
        
        # Get patients to process
        if patient_id:
            patients = EnhancedPatient.objects.filter(id=patient_id)
        else:
            patients = EnhancedPatient.objects.all()
        
        self.stdout.write(f'Processing {patients.count()} patients...')
        
        # Define encrypted fields
        encrypted_fields = [
            'phone', 'address_line1', 'address_line2', 'allergies',
            'medical_conditions', 'current_medications', 'insurance_provider',
            'insurance_policy_number', 'insurance_group_number'
        ]
        
        success_count = 0
        failed_count = 0
        
        try:
            with transaction.atomic():
                for patient in patients:
                    patient_updated = False
                    
                    for field_name in encrypted_fields:
                        field_value = getattr(patient, field_name)
                        if field_value and key_manager.is_encrypted(field_value):
                            self.stdout.write(f'Processing {field_name} for patient {patient.id}...')
                            
                            # Try to decrypt with current key first
                            try:
                                decrypted = key_manager.decrypt(field_value)
                                if decrypted != field_value:  # Decryption was successful
                                    self.stdout.write(f'  ✓ Successfully decrypted {field_name}')
                                    
                                    # Re-encrypt with current key (this will add version prefix)
                                    if not dry_run:
                                        encrypted = key_manager.encrypt(decrypted)
                                        setattr(patient, field_name, encrypted)
                                        patient_updated = True
                                        self.stdout.write(f'  ✓ Re-encrypted {field_name} with current key')
                                    else:
                                        self.stdout.write(f'  → Would re-encrypt {field_name} (dry run)')
                                else:
                                    self.stdout.write(f'  → {field_name} appears to be plaintext')
                            except Exception as e:
                                self.stdout.write(f'  ⚠ Could not decrypt {field_name}: {e}')
                                
                                # Try to decrypt as legacy data (without version prefix)
                                try:
                                    # Try with the current key directly
                                    from cryptography.fernet import Fernet
                                    from django.conf import settings
                                    
                                    cipher = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
                                    decrypted = cipher.decrypt(field_value.encode()).decode('utf-8')
                                    
                                    self.stdout.write(f'  ✓ Successfully decrypted {field_name} as legacy data')
                                    
                                    # Re-encrypt with current key
                                    if not dry_run:
                                        encrypted = key_manager.encrypt(decrypted)
                                        setattr(patient, field_name, encrypted)
                                        patient_updated = True
                                        self.stdout.write(f'  ✓ Re-encrypted {field_name} with current key')
                                    else:
                                        self.stdout.write(f'  → Would re-encrypt {field_name} (dry run)')
                                        
                                except Exception as legacy_error:
                                    self.stdout.write(f'  ⚠ Could not decrypt {field_name} as legacy data: {legacy_error}')
                    
                    if patient_updated and not dry_run:
                        patient.save()
                        success_count += 1
                        self.stdout.write(f'✅ Updated patient {patient.id}')
                    elif not patient_updated:
                        self.stdout.write(f'→ No changes needed for patient {patient.id}')
                        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during processing: {e}'))
            raise
        
        self.stdout.write(self.style.SUCCESS(f'\nEncryption fix completed!'))
        self.stdout.write(f'  - Successfully fixed: {success_count}')
        self.stdout.write(f'  - Failed to fix: {failed_count}')
        if dry_run:
            self.stdout.write(self.style.WARNING('This was a dry run - no changes were made'))