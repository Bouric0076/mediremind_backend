from django.core.management.base import BaseCommand
from notifications.utils import trigger_manual_reminder

class Command(BaseCommand):
    help = 'Manually trigger a reminder for a specific appointment'

    def add_arguments(self, parser):
        parser.add_argument('appointment_id', type=str, help='ID of the appointment to send reminder for')

    def handle(self, *args, **options):
        appointment_id = options['appointment_id']
        
        self.stdout.write(f'Triggering reminder for appointment {appointment_id}...')
        
        success, message = trigger_manual_reminder(appointment_id)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'Successfully sent reminder: {message}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to send reminder: {message}')) 