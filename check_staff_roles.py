import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
sys.path.append('c:/Users/bouri/Documents/Projects/mediremind_backend')
django.setup()

from accounts.models import EnhancedStaffProfile

# Check available staff roles
print('Available EnhancedStaffProfile roles:')
staff = EnhancedStaffProfile.objects.all()[:5]
for s in staff:
    print(f'ID: {s.id}')
    print(f'  User: {s.user.full_name} ({s.user.email})')
    print(f'  Role: {s.user.role}')
    print(f'  Hospital: {s.hospital.name if s.hospital else "None"}')
    print('---')

# Check if there are any doctors
print('\nStaff with doctor role:')
doctors = EnhancedStaffProfile.objects.filter(user__role='doctor')
print(f'Found {doctors.count()} doctors')
for d in doctors[:3]:
    print(f'  {d.user.full_name} ({d.user.email})')