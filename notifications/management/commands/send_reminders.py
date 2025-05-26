from django.core.management.base import BaseCommand
from notifications.utils import send_upcoming_appointment_reminders

class Command(BaseCommand):
    help = 'Send reminders for upcoming appointments'

    def handle(self, *args, **options):
        self.stdout.write('Sending reminders for upcoming appointments...')
        
        success, message = send_upcoming_appointment_reminders()
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'Successfully sent reminders: {message}'))
        else:
            self.stdout.write(self.style.ERROR(f'Failed to send reminders: {message}')) 