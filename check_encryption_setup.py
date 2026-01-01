#!/usr/bin/env python
"""
Test script to check what key is actually being used by Django
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.conf import settings
from cryptography.fernet import Fernet

def check_encryption_setup():
    """Check the current encryption setup"""
    print("Checking encryption setup...")
    
    # Check the current key from settings
    print(f"Settings FIELD_ENCRYPTION_KEY: {settings.FIELD_ENCRYPTION_KEY}")
    
    # Check environment variable
    env_key = os.getenv('FIELD_ENCRYPTION_KEY')
    print(f"Environment FIELD_ENCRYPTION_KEY: {env_key}")
    
    # Test if the key is valid
    try:
        Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        print("✓ Settings key is valid Fernet key")
    except Exception as e:
        print(f"✗ Settings key is invalid: {e}")
    
    if env_key:
        try:
            Fernet(env_key.encode())
            print("✓ Environment key is valid Fernet key")
        except Exception as e:
            print(f"✗ Environment key is invalid: {e}")
    
    # Now let's check what key is actually being used by the EncryptedCharField
    from authentication.models import EncryptedCharField
    
    # Create a test field to see what key it uses
    test_field = EncryptedCharField(max_length=255)
    print(f"Test field cipher suite key: {test_field.cipher_suite._signing_key[:20]}...")
    
    # Test encryption with current setup
    test_data = "+254712345678"
    encrypted = test_field.get_prep_value(test_data)
    print(f"Test encryption result: {encrypted}")
    
    # Test decryption with current setup
    decrypted = test_field.from_db_value(encrypted, None, None)
    print(f"Test decryption result: {decrypted}")
    
    # Compare with existing patient data
    from accounts.models import EnhancedPatient
    patient = EnhancedPatient.objects.first()
    if patient:
        print(f"\nExisting patient phone: {patient.phone}")
        print(f"Length: {len(patient.phone) if patient.phone else 0}")
        
        # Try to decrypt existing data with current key
        if patient.phone:
            try:
                decrypted_existing = test_field.from_db_value(patient.phone, None, None)
                print(f"Decrypted existing phone: {decrypted_existing}")
            except Exception as e:
                print(f"Failed to decrypt existing data: {e}")

if __name__ == "__main__":
    check_encryption_setup()