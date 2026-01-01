#!/usr/bin/env python
import os
import django
from cryptography.fernet import Fernet

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

def test_decryption():
    # Test with the legacy key
    legacy_key = 'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
    cipher = Fernet(legacy_key.encode())
    
    # Test decrypting one of the encrypted values from the database
    test_token = 'gAAAAABo8IKkN7HXIsT8YyAbOhzN0QzHFJM55PKorkqYzZX6hFuberoyWrggX-f0Bk5HASCwrKF4kQsLYGek2DqhM5qi3R3b1A=='
    
    try:
        decrypted = cipher.decrypt(test_token.encode())
        print('Successfully decrypted:', repr(decrypted.decode('utf-8')))
        return True
    except Exception as e:
        print('Decryption failed:', e)
        return False

def test_key_validity():
    """Test if the key is a valid Fernet key"""
    try:
        legacy_key = 'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg='
        cipher = Fernet(legacy_key.encode())
        print('Key is valid Fernet key')
        
        # Test encryption/decryption round trip
        test_data = "test data"
        encrypted = cipher.encrypt(test_data.encode())
        decrypted = cipher.decrypt(encrypted)
        print(f'Round trip test: {test_data} -> encrypted -> {decrypted.decode()}')
        return True
    except Exception as e:
        print('Key validation failed:', e)
        return False

if __name__ == '__main__':
    print('Testing key validity...')
    test_key_validity()
    print('\nTesting decryption...')
    test_decryption()