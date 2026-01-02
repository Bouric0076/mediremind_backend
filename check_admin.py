#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to the path
sys.path.append('c:\\Users\\bouri\\Documents\\Projects\\mediremind_backend')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

try:
    admin_user = User.objects.get(email='admin@mediremind.test')
    print(f'✅ Found admin user: {admin_user.username}')
    print(f'   Email: {admin_user.email}')
    print(f'   Role: {getattr(admin_user, "role", "not set")}')
except User.DoesNotExist:
    print('❌ Admin user not found')
    # List all users
    users = User.objects.all()
    print('Available users:')
    for user in users:
        print(f'  - {user.username} ({user.email})')