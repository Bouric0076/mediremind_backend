from django.core.management.base import BaseCommand
from notifications.beem_client import beem_client

class Command(BaseCommand):
    help = 'Test Beem Africa notification sending'

    def add_arguments(self, parser):
        parser.add_argument('phone', type=str, help='Phone number to send test message to')
        parser.add_argument('--channel', type=str, default='sms', choices=['sms', 'whatsapp'],
                          help='Channel to use (sms or whatsapp)')

    def handle(self, *args, **options):
        phone = options['phone']
        channel = options['channel']
        
        self.stdout.write(f'Sending test {channel} message to {phone}...')
        
        try:
            if channel == 'whatsapp':
                # Test WhatsApp template message
                template_params = {
                    "1": "Test User",
                    "2": "Monday, January 1 at 9:00 AM",
                    "3": "John Smith",
                    "4": "Main Hospital"
                }
                
                success, message = beem_client.send_whatsapp(
                    recipient=phone,
                    template_name="appointment_reminder",
                    template_params=template_params
                )
            else:
                # Test SMS message
                test_message = (
                    "This is a test message from MediRemind. "
                    "If you receive this, the SMS notification system is working correctly."
                )
                success, message = beem_client.send_sms(recipient=phone, message=test_message)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'Successfully sent {channel} message: {message}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send {channel} message: {message}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending test message: {str(e)}')) 