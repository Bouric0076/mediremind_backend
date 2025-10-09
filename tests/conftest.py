import os

# Ensure Django settings are configured for pytest before importing any Django models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')

# Optionally mark testing environment for conditional settings logic
os.environ.setdefault('TESTING', 'true')

import django

django.setup()