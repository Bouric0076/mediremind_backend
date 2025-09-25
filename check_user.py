#!/usr/bin/env python3
"""
Script to check if the test user exists in the database
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from authentication.models import User

def check_user():
    print("🔍 Checking for user: admin@mediremind.test")
    print("=" * 50)
    
    try:
        user = User.objects.get(email='admin@mediremind.test')
        print(f'✅ User found: {user.email}')
        print(f'   Full name: {user.full_name}')
        print(f'   Role: {user.role}')
        print(f'   Is active: {user.is_active}')
        print(f'   Last login: {user.last_login}')
        print(f'   Date joined: {user.date_joined}')
        print(f'   Failed attempts: {getattr(user, "failed_login_attempts", "N/A")}')
        print(f'   Account locked until: {getattr(user, "account_locked_until", "N/A")}')
        
        # Test password verification
        test_password = "TestAdmin123!"
        password_valid = user.check_password(test_password)
        print(f'   Password valid: {password_valid}')
        
    except User.DoesNotExist:
        print('❌ User admin@mediremind.test does not exist')
        print('\nAvailable users:')
        for u in User.objects.all()[:10]:
            print(f'   - {u.email} ({u.role}) - Active: {u.is_active}')
        
        print(f'\nTotal users in database: {User.objects.count()}')

if __name__ == "__main__":
    check_user()