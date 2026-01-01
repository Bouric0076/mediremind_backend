#!/usr/bin/env python
"""
Test script to verify the specific encryption key works with the patient data
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
from cryptography.fernet import Fernet
from django.conf import settings

def test_specific_key():
    """Test the specific key from the frontend"""
    print("Testing the specific key from frontend...")
    
    # The key from the frontend
    frontend_key = 'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
    
    # Create cipher suite with this key
    cipher_suite = Fernet(frontend_key.encode())
    
    # Get a patient with encrypted data
    try:
        patient = EnhancedPatient.objects.first()
        if patient:
            print(f"\nTesting with patient: {patient.id}")
            
            # Test phone decryption
            phone_value = patient.phone
            print(f"Encrypted phone: {phone_value}")
            
            if phone_value:
                try:
                    decrypted_phone = cipher_suite.decrypt(phone_value.encode()).decode()
                    print(f"Decrypted phone: {decrypted_phone}")
                except Exception as e:
                    print(f"Phone decryption failed: {e}")
                    
                    # Try to understand why it failed
                    print(f"\nDebugging decryption failure...")
                    print(f"Phone value length: {len(phone_value)}")
                    print(f"Phone value starts with: {phone_value[:20]}...")
                    
                    # Check if it's a valid Fernet token format
                    try:
                        # Fernet tokens should be base64 encoded
                        import base64
                        decoded = base64.urlsafe_b64decode(phone_value)
                        print(f"Successfully decoded base64, length: {len(decoded)}")
                        
                        # Fernet tokens have a specific structure
                        if len(decoded) >= 57:  # Minimum Fernet token size
                            version = decoded[0]
                            print(f"Version byte: {version} (should be 128)")
                            
                            if version == 128:
                                print("Valid Fernet token format detected")
                                
                                # Try to decrypt with different keys
                                print("\nTrying with different keys...")
                                
                                # Try with current settings key
                                settings_key = settings.FIELD_ENCRYPTION_KEY.encode()
                                try:
                                    decrypted = Fernet(settings_key).decrypt(phone_value.encode()).decode()
                                    print(f"Decrypted with settings key: {decrypted}")
                                except Exception as e2:
                                    print(f"Settings key failed: {e2}")
                                
                                # Try with frontend key
                                try:
                                    decrypted = cipher_suite.decrypt(phone_value.encode()).decode()
                                    print(f"Decrypted with frontend key: {decrypted}")
                                except Exception as e3:
                                    print(f"Frontend key failed: {e3}")
                            else:
                                print(f"Invalid version: {version}")
                        else:
                            print(f"Token too short: {len(decoded)} bytes")
                            
                    except Exception as e4:
                        print(f"Not a valid base64 token: {e4}")
                        
        else:
            print("No patients found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_key()