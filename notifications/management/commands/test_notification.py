from django.core.management.base import BaseCommand
from notifications.textsms_client import textsms_client

class Command(BaseCommand):
    help = 'Test TextSMS notification sending'

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
                # WhatsApp functionality not yet implemented in TextSMS client
                self.stdout.write(self.style.WARNING('WhatsApp functionality not yet implemented with TextSMS API'))
                return
            else:
                # Test SMS message
                test_message = (
                    "This is a test message from MediRemind using TextSMS API. "
                    "If you receive this, the SMS notification system is working correctly."
                )
                success, message = textsms_client.send_sms(recipient=phone, message=test_message)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'Successfully sent {channel} message: {message}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send {channel} message: {message}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending test message: {str(e)}'))