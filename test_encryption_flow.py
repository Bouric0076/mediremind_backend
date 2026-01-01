#!/usr/bin/env python
"""
Test end-to-end encryption/decryption flow
"""
import os
import django

# Setup Django first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

# Now import Django-dependent modules
from encryption.key_manager import key_manager

def test_encryption_flow():
    """Test the complete encryption/decryption flow"""
    
    # Test data
    test_data = {
        'phone': '+254722123456',
        'address_line1': '123 Main St',
        'allergies': 'Penicillin',
        'insurance_provider': 'AAR Insurance'
    }
    
    print("Testing encryption/decryption flow...")
    print(f"Original data: {test_data}")
    
    # Test encryption
    encrypted_data = {}
    for field, value in test_data.items():
        encrypted = key_manager.encrypt(value)
        encrypted_data[field] = encrypted
        print(f"{field}: {value} -> {encrypted[:50]}...")
    
    print(f"\nEncrypted data: {encrypted_data}")
    
    # Test decryption
    decrypted_data = {}
    for field, encrypted_value in encrypted_data.items():
        decrypted = key_manager.decrypt(encrypted_value)
        decrypted_data[field] = decrypted
        print(f"{field}: {encrypted_value[:50]}... -> {decrypted}")
    
    print(f"\nDecrypted data: {decrypted_data}")
    
    # Verify data integrity
    success = True
    for field, original_value in test_data.items():
        if decrypted_data[field] != original_value:
            print(f"ERROR: {field} mismatch!")
            success = False
    
    if success:
        print("\n✅ All encryption/decryption tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return success

def test_key_info():
    """Display current key information"""
    info = key_manager.get_key_info()
    print("\nCurrent key information:")
    for key, value in info.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_key_info()
    test_encryption_flow()