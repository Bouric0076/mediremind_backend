#!/usr/bin/env python
"""
Script to create test staff accounts for MediRemind system
"""
import os
import sys
import django
from datetime import date, timedelta
from django.contrib.auth.hashers import make_password
import django.utils.timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from authentication.models import User
from accounts.models import EnhancedStaffProfile, Specialization

def create_test_staff():
    """Create test staff accounts with complete profiles"""
    
    # Create specializations first
    specializations = [
        {'name': 'Cardiology', 'description': 'Heart and cardiovascular system'},
        {'name': 'Emergency Medicine', 'description': 'Emergency and urgent care'},
        {'name': 'Family Medicine', 'description': 'Primary care for all ages'},
        {'name': 'Internal Medicine', 'description': 'Adult internal medicine'},
        {'name': 'Pediatrics', 'description': 'Children and adolescent care'},
    ]
    
    created_specializations = {}
    for spec_data in specializations:
        specialization, created = Specialization.objects.get_or_create(
            name=spec_data['name'],
            defaults={'description': spec_data['description']}
        )
        created_specializations[spec_data['name']] = specialization
        if created:
            print(f"Created specialization: {specialization.name}")
        else:
            print(f"Specialization already exists: {specialization.name}")
    
    # Test staff data
    staff_data = [
        {
            'email': 'dr.sarah.johnson@hospital.com',
            'password': 'TestDoctor123!',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'full_name': 'Dr. Sarah Johnson',
            'role': 'doctor',
            'job_title': 'Cardiologist',
            'department': 'Cardiology',
            'specialization': 'Cardiology',
            'employment_status': 'full_time',
            'license_number': 'MD123456',
            'license_state': 'NY',
            'license_expiration': date(2025, 12, 31),
        },
        {
            'email': 'dr.michael.chen@hospital.com',
            'password': 'TestDoctor123!',
            'first_name': 'Michael',
            'last_name': 'Chen',
            'full_name': 'Dr. Michael Chen',
            'role': 'doctor',
            'job_title': 'Emergency Physician',
            'department': 'Emergency Medicine',
            'specialization': 'Emergency Medicine',
            'employment_status': 'full_time',
            'license_number': 'MD789012',
            'license_state': 'NY',
            'license_expiration': date(2025, 6, 30),
        },
        {
            'email': 'dr.emily.davis@hospital.com',
            'password': 'TestDoctor123!',
            'first_name': 'Emily',
            'last_name': 'Davis',
            'full_name': 'Dr. Emily Davis',
            'role': 'doctor',
            'job_title': 'Family Medicine Physician',
            'department': 'Family Medicine',
            'specialization': 'Family Medicine',
            'employment_status': 'full_time',
            'license_number': 'MD345678',
            'license_state': 'NY',
            'license_expiration': date(2026, 3, 15),
        },
        {
            'email': 'nurse.mary.wilson@hospital.com',
            'password': 'TestNurse123!',
            'first_name': 'Mary',
            'last_name': 'Wilson',
            'full_name': 'Mary Wilson, RN',
            'role': 'nurse',
            'job_title': 'Registered Nurse',
            'department': 'Emergency Medicine',
            'specialization': 'Emergency Medicine',
            'employment_status': 'full_time',
            'license_number': 'RN567890',
            'license_state': 'NY',
            'license_expiration': date(2025, 8, 31),
        },
        {
            'email': 'dr.james.brown@hospital.com',
            'password': 'TestDoctor123!',
            'first_name': 'James',
            'last_name': 'Brown',
            'full_name': 'Dr. James Brown',
            'role': 'doctor',
            'job_title': 'Pediatrician',
            'department': 'Pediatrics',
            'specialization': 'Pediatrics',
            'employment_status': 'full_time',
            'license_number': 'MD901234',
            'license_state': 'NY',
            'license_expiration': date(2025, 11, 30),
        },
    ]
    
    created_count = 0
    
    for staff_info in staff_data:
        try:
            # Check if user already exists
            if User.objects.filter(email=staff_info['email']).exists():
                print(f"Staff member with email {staff_info['email']} already exists. Skipping...")
                continue
            
            # Create user account
            user = User.objects.create(
                email=staff_info['email'],
                password=make_password(staff_info['password']),
                first_name=staff_info['first_name'],
                last_name=staff_info['last_name'],
                full_name=staff_info['full_name'],
                role=staff_info['role'],
                is_active=True,
                is_verified=True,
                date_joined=django.utils.timezone.now()
            )
            
            # Create staff profile
            specialization = created_specializations.get(staff_info['specialization'])
            staff_profile = EnhancedStaffProfile.objects.create(
                user=user,
                specialization=specialization,
                department=staff_info['department'],
                job_title=staff_info['job_title'],
                employment_status=staff_info['employment_status'],
                hire_date=date.today() - timedelta(days=365),  # Hired 1 year ago
                license_number=staff_info['license_number'],
                license_state=staff_info['license_state'],
                license_expiration=staff_info['license_expiration'],
                license_status='active',
                is_active=True,
                can_prescribe=True if staff_info['role'] == 'doctor' else False,
                can_order_tests=True if staff_info['role'] == 'doctor' else False,
            )
            
            created_count += 1
            print(f"Created staff member: {user.full_name} ({user.email})")
            
        except Exception as e:
            print(f"Error creating staff member {staff_info['email']}: {str(e)}")
    
    print(f"\nSuccessfully created {created_count} staff members!")
    print("\nTest staff credentials:")
    print("=" * 50)
    for staff_info in staff_data:
        print(f"Email: {staff_info['email']}")
        print(f"Password: {staff_info['password']}")
        print(f"Role: {staff_info['job_title']}")
        print("-" * 30)

if __name__ == '__main__':
    create_test_staff()