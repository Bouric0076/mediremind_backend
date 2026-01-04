#!/usr/bin/env python
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
sys.path.append('c:\\Users\\bouri\\Documents\\Projects\\mediremind_backend')
django.setup()

from notifications.template_manager import TemplateManager, TemplateContext, RecipientType
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)

# Create a simple test context
context = TemplateContext(
    recipient_name='Test Patient',
    recipient_email='test@example.com',
    recipient_type=RecipientType.PATIENT,
    appointment={
        'id': 'test-123',
        'patient_name': 'Test Patient',
        'provider_name': 'Dr. Test',
        'appointment_date': '2026-01-05',
        'start_time': '10:00:00',
        'appointment_type': 'Consultation',
        'location': 'Test Clinic'
    }
)

template_manager = TemplateManager()
try:
    success, subject, html_message = template_manager.render_template_with_fallback('appointment_confirmation_patient', context)
    print(f'Success: {success}')
    print(f'Subject: {subject}')
    print(f'Message length: {len(html_message) if html_message else 0}')
    if success:
        print('✅ Template rendering fix is working correctly!')
    else:
        print('❌ Template rendering still has issues')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()