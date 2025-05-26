from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64
import json

def generate_vapid_keys():
    # Generate a new EC key pair
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Get the private key in PEM format
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Get the public key in PEM format
    pem_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Convert to base64url format
    private_key_b64 = base64.urlsafe_b64encode(pem_private).decode('utf-8').rstrip('=')
    public_key_b64 = base64.urlsafe_b64encode(pem_public).decode('utf-8').rstrip('=')
    
    # Save to a JSON file
    keys = {
        'VAPID_PRIVATE_KEY': private_key_b64,
        'VAPID_PUBLIC_KEY': public_key_b64
    }
    
    with open('vapid_keys.json', 'w') as f:
        json.dump(keys, f, indent=2)
    
    print("VAPID keys have been generated and saved to vapid_keys.json")
    print("\nVAPID_PUBLIC_KEY:", public_key_b64)
    print("VAPID_PRIVATE_KEY:", private_key_b64)

if __name__ == '__main__':
    generate_vapid_keys() 