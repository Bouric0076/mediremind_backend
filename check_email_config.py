#!/usr/bin/env python
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

print('=== Current Email Configuration ===')
print(f'DEBUG: {settings.DEBUG}')
print(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
print(f'EMAIL_SERVICE: {getattr(settings, "EMAIL_SERVICE", "not set")}')
print(f'EMAIL_HOST: {settings.EMAIL_HOST}')
print(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
print(f'EMAIL_HOST_PASSWORD: {"***" if settings.EMAIL_HOST_PASSWORD else "not set"}')
print(f'EMAIL_PORT: {settings.EMAIL_PORT}')
print(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
print(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')

print('\n=== Environment Variables ===')
print(f'EMAIL_SERVICE from env: {os.getenv("EMAIL_SERVICE", "not set")}')
print(f'EMAIL_HOST from env: {os.getenv("EMAIL_HOST", "not set")}')
print(f'EMAIL_HOST_USER from env: {os.getenv("EMAIL_HOST_USER", "not set")}')
print(f'EMAIL_HOST_PASSWORD from env: {"***" if os.getenv("EMAIL_HOST_PASSWORD") else "not set"}')
print(f'RENDER from env: {os.getenv("RENDER", "not set")}')

print('\n=== Analysis ===')
if settings.DEBUG:
    print('✓ DEBUG mode is ON - emails will be printed to console')
    print('✓ Console backend is working correctly')
else:
    print('✓ DEBUG mode is OFF - emails will be sent via SMTP')
    if settings.EMAIL_HOST == 'localhost':
        print('⚠️  Warning: EMAIL_HOST is localhost - emails may not be delivered')
    if not settings.EMAIL_HOST_USER:
        print('⚠️  Warning: EMAIL_HOST_USER is not configured')
    if not settings.EMAIL_HOST_PASSWORD:
        print('⚠️  Warning: EMAIL_HOST_PASSWORD is not configured')