#!/usr/bin/env python
"""
Script to create 5 test patient accounts for MediRemind system
"""
import os
import sys
import django
from datetime import date, timedelta
from django.contrib.auth.hashers import make_password

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from authentication.models import User
from accounts.models import EnhancedPatient

def create_test_patients():
    """Create 5 test patient accounts with complete profiles"""
    
    # Test patient data
    patients_data = [
        {
            'email': 'patient1@test.com',
            'password': 'TestPatient123!',
            'first_name': 'John',
            'last_name': 'Smith',
            'full_name': 'John Smith',
            'phone': '+1234567890',
            'date_of_birth': date(1985, 3, 15),
            'gender': 'M',
            'marital_status': 'married',
            'address_line1': '123 Main Street',
            'city': 'New York',
            'state': 'NY',
            'zip_code': '10001',
            'emergency_contact_name': 'Jane Smith',
            'emergency_contact_relationship': 'Spouse',
            'emergency_contact_phone': '+1234567891',
            'blood_type': 'O+',
            'height_inches': 72,
            'weight_lbs': 180,
        },
        {
            'email': 'patient2@test.com',
            'password': 'TestPatient123!',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'full_name': 'Sarah Johnson',
            'phone': '+1234567892',
            'date_of_birth': date(1990, 7, 22),
            'gender': 'F',
            'marital_status': 'single',
            'address_line1': '456 Oak Avenue',
            'city': 'Los Angeles',
            'state': 'CA',
            'zip_code': '90210',
            'emergency_contact_name': 'Robert Johnson',
            'emergency_contact_relationship': 'Father',
            'emergency_contact_phone': '+1234567893',
            'blood_type': 'A+',
            'height_inches': 65,
            'weight_lbs': 140,
        },
        {
            'email': 'patient3@test.com',
            'password': 'TestPatient123!',
            'first_name': 'Michael',
            'last_name': 'Brown',
            'full_name': 'Michael Brown',
            'phone': '+1234567894',
            'date_of_birth': date(1978, 11, 8),
            'gender': 'M',
            'marital_status': 'divorced',
            'address_line1': '789 Pine Road',
            'city': 'Chicago',
            'state': 'IL',
            'zip_code': '60601',
            'emergency_contact_name': 'Lisa Brown',
            'emergency_contact_relationship': 'Sister',
            'emergency_contact_phone': '+1234567895',
            'blood_type': 'B+',
            'height_inches': 70,
            'weight_lbs': 190,
        },
        {
            'email': 'patient4@test.com',
            'password': 'TestPatient123!',
            'first_name': 'Emily',
            'last_name': 'Davis',
            'full_name': 'Emily Davis',
            'phone': '+1234567896',
            'date_of_birth': date(1995, 2, 14),
            'gender': 'F',
            'marital_status': 'single',
            'address_line1': '321 Elm Street',
            'city': 'Houston',
            'state': 'TX',
            'zip_code': '77001',
            'emergency_contact_name': 'David Davis',
            'emergency_contact_relationship': 'Brother',
            'emergency_contact_phone': '+1234567897',
            'blood_type': 'AB+',
            'height_inches': 63,
            'weight_lbs': 125,
        },
        {
            'email': 'patient5@test.com',
            'password': 'TestPatient123!',
            'first_name': 'James',
            'last_name': 'Wilson',
            'full_name': 'James Wilson',
            'phone': '+1234567898',
            'date_of_birth': date(1982, 9, 30),
            'gender': 'M',
            'marital_status': 'married',
            'address_line1': '654 Maple Drive',
            'city': 'Phoenix',
            'state': 'AZ',
            'zip_code': '85001',
            'emergency_contact_name': 'Maria Wilson',
            'emergency_contact_relationship': 'Spouse',
            'emergency_contact_phone': '+1234567899',
            'blood_type': 'O-',
            'height_inches': 68,
            'weight_lbs': 165,
        }
    ]
    
    created_accounts = []
    
    for patient_data in patients_data:
        try:
            # Check if user already exists
            if User.objects.filter(email=patient_data['email']).exists():
                print(f"User with email {patient_data['email']} already exists. Skipping...")
                continue
            
            # Create User account
            user = User.objects.create(
                email=patient_data['email'],
                username=patient_data['email'],  # Use email as username
                first_name=patient_data['first_name'],
                last_name=patient_data['last_name'],
                full_name=patient_data['full_name'],
                phone=patient_data['phone'],
                role='patient',
                password=make_password(patient_data['password']),
                email_notifications=True,
                sms_notifications=True,
                push_notifications=True,
            )
            
            # Create Patient Profile
            patient = EnhancedPatient.objects.create(
                user=user,
                date_of_birth=patient_data['date_of_birth'],
                gender=patient_data['gender'],
                marital_status=patient_data['marital_status'],
                phone=patient_data['phone'],
                address_line1=patient_data['address_line1'],
                city=patient_data['city'],
                state=patient_data['state'],
                zip_code=patient_data['zip_code'],
                emergency_contact_name=patient_data['emergency_contact_name'],
                emergency_contact_relationship=patient_data['emergency_contact_relationship'],
                emergency_contact_phone=patient_data['emergency_contact_phone'],
                blood_type=patient_data['blood_type'],
                height_inches=patient_data['height_inches'],
                weight_lbs=patient_data['weight_lbs'],
                smoking_status='never',
                alcohol_use='none',
            )
            
            created_accounts.append({
                'email': patient_data['email'],
                'password': patient_data['password'],
                'name': patient_data['full_name'],
                'user_id': str(user.id),
                'patient_id': str(patient.id)
            })
            
            print(f"✅ Created patient account: {patient_data['full_name']} ({patient_data['email']})")
            
        except Exception as e:
            print(f"❌ Error creating patient {patient_data['full_name']}: {str(e)}")
    
    return created_accounts

if __name__ == '__main__':
    print("Creating 5 test patient accounts...")
    print("=" * 50)
    
    accounts = create_test_patients()
    
    print("\n" + "=" * 50)
    print("PATIENT ACCOUNT CREATION SUMMARY")
    print("=" * 50)
    
    if accounts:
        print(f"✅ Successfully created {len(accounts)} patient accounts")
        print("\nLOGIN DETAILS:")
        print("-" * 30)
        for account in accounts:
            print(f"Name: {account['name']}")
            print(f"Email: {account['email']}")
            print(f"Password: {account['password']}")
            print(f"User ID: {account['user_id']}")
            print(f"Patient ID: {account['patient_id']}")
            print("-" * 30)
    else:
        print("❌ No accounts were created")
    
    print("\nAll patient accounts are ready for testing!")