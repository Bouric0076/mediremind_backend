from django.core.management.base import BaseCommand
from django.conf import settings
from encryption.key_manager import EncryptionKeyManager
import json


class Command(BaseCommand):
    help = 'Add a legacy encryption key as backup to decrypt existing data'

    def add_arguments(self, parser):
        parser.add_argument('legacy_key', type=str, help='The legacy encryption key to add as backup')
        parser.add_argument('--version-name', type=str, default='legacy', help='Name for the legacy key version')

    def handle(self, *args, **options):
        legacy_key = options['legacy_key']
        version_name = options['version_name']
        
        # Get current backup keys
        backup_keys = getattr(settings, 'ENCRYPTION_BACKUP_KEYS', {})
        
        # Add the legacy key
        if version_name in backup_keys:
            self.stdout.write(self.style.WARNING(f"Key version '{version_name}' already exists. Overwriting..."))
        
        backup_keys[version_name] = legacy_key
        
        # Update settings
        settings.ENCRYPTION_BACKUP_KEYS = backup_keys
        
        self.stdout.write(self.style.SUCCESS(f"Successfully added legacy key as '{version_name}'"))
        self.stdout.write(f"Current backup keys: {list(backup_keys.keys())}")
        
        # Test decryption with the new key
        key_manager = EncryptionKeyManager()
        self.stdout.write(f"Available keys: {list(key_manager.keys.keys())}")