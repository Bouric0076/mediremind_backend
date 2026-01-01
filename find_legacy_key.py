from cryptography.fernet import Fernet
import base64
import os

def try_decrypt_token(token, key):
    """Try to decrypt a token with a given key"""
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        decrypted = f.decrypt(token.encode() if isinstance(token, str) else token)
        return decrypted.decode('utf-8')
    except Exception as e:
        return None

def main():
    # Sample encrypted data from the database
    sample_tokens = [
        'gAAAAABo8IKkN7HXIsT8YyAbOhzN0QzHFJM55PKorkqYzZX6hFuberoyWrggX-f0Bk5HASCwrKF4kQsLYGek2DqhM5qi3R3b1A==',
        'gAAAAABo8IKk_rMrNJF1vFFhQlVI7wWpI3UZlufom-W2V2vn6eRWAftcP8qrTF9imSi-WA8HOay35uFMb-LpMVCDdxDyPpwmng==',
        'gAAAAABo8IKkZBgyuI6b7B_zSZlJp51Rb7tkubLuBjinJShAzhE4RBS_vIEnfK8FSYFmnBKS4ra6o1ULqfyf7-02d43yGnrOLg=='
    ]
    
    # Common keys that might have been used
    potential_keys = [
        # Current key
        'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=',
        
        # Simple/development keys
        'your-secret-encryption-key-here',
        'development-key-123456789',
        'test-key-123456789',
        'secret-key-123456789',
        
        # Base64 encoded simple keys
        base64.b64encode(b'your-secret-encryption-key-here').decode(),
        base64.b64encode(b'development-key-123456789').decode(),
        base64.b64encode(b'test-key-123456789').decode(),
        base64.b64encode(b'secret-key-123456789').decode(),
        
        # Django SECRET_KEY variations
        'wJr-gJ1Yge5Su2uUd44LDR2Hj9WvbBohrrLU0egWzSRNZ_wUo3-c1UdCdewXnCdvasw',
        base64.b64encode(b'wJr-gJ1Yge5Su2uUd44LDR2Hj9WvbBohrrLU0egWzSRNZ_wUo3-c1UdCdewXnCdvasw').decode(),
        
        # JWT secret variations
        '8lxsOWaMuaGbg69s7i2WoHQ7xGTAV4NcGj37llJVIRzBfO0PKUFQYSTGgYs_QWd4iFM',
        base64.b64encode(b'8lxsOWaMuaGbg69s7i2WoHQ7xGTAV4NcGj37llJVIRzBfO0PKUFQYSTGgYs_QWd4iFM').decode(),
    ]
    
    print("Trying to decrypt sample tokens with various keys...")
    print("=" * 60)
    
    for i, token in enumerate(sample_tokens):
        print(f"\nToken {i+1}: {token[:50]}...")
        
        for key in potential_keys:
            result = try_decrypt_token(token, key)
            if result:
                print(f"  ✓ SUCCESS with key: {key}")
                print(f"    Decrypted: {result}")
                return key
            else:
                print(f"  ✗ Failed with key: {key[:30]}...")
    
    print("\n" + "=" * 60)
    print("No working key found. The data may be encrypted with a different key.")
    print("You may need to:")
    print("1. Check if the data was encrypted with a different key")
    print("2. Restore the original encryption key")
    print("3. Re-encrypt the data manually")

if __name__ == '__main__':
    main()