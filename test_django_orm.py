#!/usr/bin/env python
"""
Test the Django ORM decryption directly to verify the encryption system works
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from accounts.models import EnhancedPatient
from encryption.key_manager import key_manager

def test_django_orm_decryption():
    """Test decryption through Django ORM"""
    
    print("Testing Django ORM decryption...")
    
    # Get the patient we created earlier
    try:
        patient = EnhancedPatient.objects.get(id="6fe9d5da-05fa-4469-8f7f-f423949361c4")
        print(f"Found patient: {patient.user.first_name} {patient.user.last_name}")
        
        print(f"\nDecrypted fields from Django ORM:")
        print(f"Phone: {patient.phone}")
        print(f"Address: {patient.address_line1}")
        print(f"Allergies: {patient.allergies}")
        print(f"Insurance: {patient.insurance_provider}")
        
        # Test if the fields are properly encrypted in database
        print(f"\nTesting raw database values...")
        from django.db import connection
        
        # Get the actual table name
        table_name = EnhancedPatient._meta.db_table
        print(f"Table name: {table_name}")
        
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT phone, address_line1, allergies, insurance_provider "
                f"FROM {table_name} WHERE id = %s",
                [patient.id]
            )
            row = cursor.fetchone()
            if row:
                print(f"Raw phone in DB: {row[0][:50]}...")
                print(f"Raw address in DB: {row[1][:50]}...")
                print(f"Raw allergies in DB: {row[2][:50]}...")
                print(f"Raw insurance in DB: {row[3][:50]}...")
                
                # Check if they have the v1: prefix
                for i, field_name in enumerate(['phone', 'address', 'allergies', 'insurance']):
                    if row[i] and row[i].startswith('v1:'):
                        print(f"✅ {field_name} is properly encrypted with v1: prefix")
                    else:
                        print(f"❌ {field_name} is not properly encrypted")
        
        print("\n✅ Django ORM decryption test completed successfully!")
        
    except EnhancedPatient.DoesNotExist:
        print("❌ Patient not found. Run the encryption test first to create a patient.")
    except Exception as e:
        print(f"❌ Error testing Django ORM decryption: {e}")

if __name__ == "__main__":
    test_django_orm_decryption()