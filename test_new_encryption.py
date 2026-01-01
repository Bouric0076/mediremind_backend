#!/usr/bin/env python
"""
Test creating new encrypted data and verify it works with frontend
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from accounts.models import EnhancedPatient
from encryption.key_manager import key_manager

def test_new_encryption():
    """Test creating new encrypted data"""
    
    # Create test patient with encrypted data
    test_data = {
        'phone': '+254722987654',
        'address_line1': '456 Test Street',
        'allergies': 'None known',
        'insurance_provider': 'Test Insurance'
    }
    
    print("Creating new patient with encrypted data...")
    
    # Encrypt the data
    encrypted_data = {}
    for field, value in test_data.items():
        encrypted = key_manager.encrypt(value)
        encrypted_data[field] = encrypted
        print(f"{field}: {value} -> {encrypted[:50]}...")
    
    import uuid
    
    # Create user first
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create(
        username=f'testpatient_{uuid.uuid4().hex[:8]}',
        email=f'test_{uuid.uuid4().hex[:8]}@example.com',
        first_name='Test',
        last_name='Patient'
    )
    
    from datetime import date
    
    # Create patient with encrypted data
    patient = EnhancedPatient.objects.create(
        user=user,
        phone=encrypted_data['phone'],
        address_line1=encrypted_data['address_line1'],
        allergies=encrypted_data['allergies'],
        insurance_provider=encrypted_data['insurance_provider'],
        # Set other required fields
        date_of_birth=date(1990, 1, 1),
        gender='M',
        city='Nairobi',
        state='Nairobi'
    )
    
    print(f"\nCreated patient {patient.id}")
    
    # Test decryption
    print("\nTesting decryption...")
    for field in ['phone', 'address_line1', 'allergies', 'insurance_provider']:
        encrypted_value = getattr(patient, field)
        decrypted_value = key_manager.decrypt(encrypted_value)
        print(f"{field}: {encrypted_value[:50]}... -> {decrypted_value}")
    
    return patient

if __name__ == "__main__":
    patient = test_new_encryption()
    print(f"\n✅ Test completed! Patient ID: {patient.id}")