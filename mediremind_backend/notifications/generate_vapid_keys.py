from py_vapid import Vapid
import os
from pathlib import Path
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_vapid_keys():
    """Generate VAPID keys and save them to .env file"""
    # Generate a new EC key pair
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Get the private key in raw bytes
    private_numbers = private_key.private_numbers()
    private_key_raw = private_numbers.private_value.to_bytes(32, byteorder='big')
    
    # Get the public key in raw bytes
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    public_key_raw = (public_numbers.x.to_bytes(32, byteorder='big') + 
                     public_numbers.y.to_bytes(32, byteorder='big'))
    
    # Convert to URL-safe base64
    private_key_b64 = base64.urlsafe_b64encode(private_key_raw).decode('utf-8').rstrip('=')
    public_key_b64 = base64.urlsafe_b64encode(public_key_raw).decode('utf-8').rstrip('=')
    
    # Path to .env file
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    
    # Read existing .env content
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Filter out existing VAPID keys
    lines = [line for line in lines if not line.startswith(('VAPID_PUBLIC_KEY=', 'VAPID_PRIVATE_KEY='))]
    
    # Add new VAPID keys
    lines.extend([
        f'VAPID_PRIVATE_KEY={private_key_b64}\n',
        f'VAPID_PUBLIC_KEY={public_key_b64}\n'
    ])
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print("VAPID keys generated and saved to .env file:")
    print(f"VAPID_PUBLIC_KEY={public_key_b64}")
    print(f"VAPID_PRIVATE_KEY={private_key_b64}")

if __name__ == '__main__':
    generate_vapid_keys() 