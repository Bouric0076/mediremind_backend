#!/usr/bin/env python
"""
Test script to decrypt legacy encrypted data
"""
import os
import django
from cryptography.fernet import Fernet

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

def test_decryption():
    # Test with the legacy key from settings
    from django.conf import settings
    
    print(f"Current FIELD_ENCRYPTION_KEY: {settings.FIELD_ENCRYPTION_KEY}")
    
    # Test tokens from the database
    test_tokens = [
        'gAAAAABo8IKkN7HXIsT8YyAbOhzN0QzHFJM55PKorkqYzZX6hFuberoyWrggX-f0Bk5HASCwrKF4kQsLYGek2DqhM5qi3R3b1A==',
        'gAAAAABo8IKk_rMrNJF1vFFhQlVI7wWpI3UZlufom-W2V2vn6eRWAftcP8qrTF9imSi-WA8HOay35uFMb-LpMVCDdxDyPpwmng==',
        'gAAAAABo8IKkZBgyuI6b7B_zSZlJp51Rb7tkubLuBjinJShAzhE4RBS_vIEnfK8FSYFmnBKS4ra6o1ULqfyf7-02d43yGnrOLg==',
        'gAAAAABo8IKk-imQEWc4yKQk_QgZJOPmPh4GV1y9F9ULFUtkb0yp0IhATM3A_ogPuL2fBD3kz-OsGW7jyYvikhw162Lhx7cZqg=='
    ]
    
    # Test with current key
    try:
        cipher = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        print("\nTesting with current key:")
        for i, token in enumerate(test_tokens):
            try:
                decrypted = cipher.decrypt(token.encode())
                print(f"  Token {i+1}: SUCCESS - {decrypted.decode('utf-8')}")
            except Exception as e:
                print(f"  Token {i+1}: FAILED - {e}")
    except Exception as e:
        print(f"Failed to create cipher with current key: {e}")
    
    # Test with other potential keys
    potential_keys = [
        'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=',  # Default from settings
        'your-fernet-key-here',  # Placeholder
        'another-fernet-key-here',  # Placeholder
    ]
    
    print("\nTesting with other potential keys:")
    for key in potential_keys:
        print(f"\nTesting with key: {key}")
        try:
            cipher = Fernet(key.encode())
            success_count = 0
            for i, token in enumerate(test_tokens):
                try:
                    decrypted = cipher.decrypt(token.encode())
                    print(f"  Token {i+1}: SUCCESS - {decrypted.decode('utf-8')}")
                    success_count += 1
                except Exception as e:
                    print(f"  Token {i+1}: FAILED - {e}")
            if success_count > 0:
                print(f"  *** This key successfully decrypted {success_count} tokens! ***")
        except Exception as e:
            print(f"  Failed to create cipher: {e}")

if __name__ == "__main__":
    test_decryption()