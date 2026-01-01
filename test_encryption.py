#!/usr/bin/env python
"""
Test script to verify encrypted field decryption is working correctly
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from accounts.models import EnhancedPatient
from authentication.models import User
from cryptography.fernet import Fernet
from django.conf import settings

def test_encrypted_fields():
    """Test that encrypted fields are properly decrypted"""
    print("Testing encrypted field decryption...")
    
    # Check if we have a valid encryption key
    print(f"FIELD_ENCRYPTION_KEY: {settings.FIELD_ENCRYPTION_KEY}")
    
    # Create a test cipher suite
    cipher_suite = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
    
    # Test encryption/decryption directly
    test_data = "+254712345678"
    encrypted = cipher_suite.encrypt(test_data.encode()).decode()
    decrypted = cipher_suite.decrypt(encrypted.encode()).decode()
    
    print(f"Test data: {test_data}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"Decryption successful: {test_data == decrypted}")
    
    # Find a patient with encrypted data
    try:
        patient = EnhancedPatient.objects.first()
        if patient:
            print(f"\nTesting with real patient data...")
            print(f"Patient ID: {patient.id}")
            print(f"Patient phone (raw from DB): {patient.phone}")
            print(f"Patient phone type: {type(patient.phone)}")
            
            # Check if the phone number looks encrypted
            phone_value = patient.phone
            if phone_value and len(phone_value) > 50:  # Fernet tokens are typically long
                print("Phone appears to be encrypted (long string)")
                try:
                    # Try to decrypt manually
                    decrypted_phone = cipher_suite.decrypt(phone_value.encode()).decode()
                    print(f"Manually decrypted phone: {decrypted_phone}")
                except Exception as e:
                    print(f"Manual decryption failed: {e}")
            else:
                print("Phone appears to be decrypted or plain text")
                
            # Check other encrypted fields
            encrypted_fields = ['address_line1', 'address_line2', 'allergies', 'medical_history', 
                              'current_medications', 'insurance_provider', 'insurance_policy_number']
            
            for field_name in encrypted_fields:
                field_value = getattr(patient, field_name, None)
                if field_value:
                    print(f"{field_name}: {field_value[:50]}... (type: {type(field_value)})")
                    if len(str(field_value)) > 50:
                        print(f"  -> Appears encrypted")
                        try:
                            decrypted = cipher_suite.decrypt(field_value.encode()).decode()
                            print(f"  -> Decrypted: {decrypted}")
                        except Exception as e:
                            print(f"  -> Decryption failed: {e}")
                    else:
                        print(f"  -> Appears decrypted or plain text")
                        
        else:
            print("No patients found in database")
            
    except Exception as e:
        print(f"Error testing patient data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_encrypted_fields()