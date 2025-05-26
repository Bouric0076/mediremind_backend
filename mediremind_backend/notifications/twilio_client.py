import os
from twilio.rest import Client
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv()

class TwilioClient:
    """Client for handling WhatsApp messaging via Twilio"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM")  # Your Twilio WhatsApp number
        
        if not all([self.account_sid, self.auth_token, self.whatsapp_from]):
            raise ValueError("Twilio credentials not found in environment variables")
            
        self.client = Client(self.account_sid, self.auth_token)
    
    def format_whatsapp_number(self, phone_number):
        """Format phone number for WhatsApp"""
        # Remove any spaces, dashes, or parentheses
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Add whatsapp: prefix and ensure number starts with country code
        if not clean_number.startswith('+'):
            clean_number = '+' + clean_number
        return f"whatsapp:{clean_number}"
    
    def send_whatsapp(self, to_number, message):
        """Send WhatsApp message via Twilio"""
        try:
            formatted_to = self.format_whatsapp_number(to_number)
            formatted_from = self.format_whatsapp_number(self.whatsapp_from)
            
            message = self.client.messages.create(
                from_=formatted_from,
                body=message,
                to=formatted_to
            )
            
            return True, f"Message sent successfully. SID: {message.sid}"
            
        except Exception as e:
            print(f"Error sending WhatsApp message: {str(e)}")
            return False, str(e)
    
    def send_template_message(self, to_number, template_name, template_data):
        """Send a template-based WhatsApp message"""
        try:
            # Get the template message based on the template name
            message_template = self.get_message_template(template_name)
            if not message_template:
                return False, f"Template {template_name} not found"
            
            # Format the message with template data
            message = message_template.format(**template_data)
            
            # Send the formatted message
            return self.send_whatsapp(to_number, message)
            
        except KeyError as e:
            return False, f"Missing template data: {str(e)}"
        except Exception as e:
            return False, f"Error sending template message: {str(e)}"
    
    def get_message_template(self, template_name):
        """Get message template by name"""
        templates = {
            'appointment_reminder': (
                "🏥 Reminder: You have an appointment at {location} with Dr. {doctor_name} "
                "on {appointment_time}.\n\n"
                "Please reply with:\n"
                "1️⃣ to confirm\n"
                "2️⃣ to reschedule\n"
                "3️⃣ to cancel"
            ),
            'appointment_confirmation': (
                "✅ Your {appointment_type} appointment has been confirmed!\n\n"
                "📅 Date & Time: {appointment_time}\n"
                "👨‍⚕️ Doctor: Dr. {doctor_name}\n"
                "📍 Location: {location}\n\n"
                "We'll send you a reminder 24 hours before your appointment."
            ),
            'appointment_cancelled': (
                "❌ Your appointment with Dr. {doctor_name} scheduled for {appointment_time} "
                "has been cancelled.\n\n"
                "Please contact us to reschedule."
            ),
            'appointment_rescheduled': (
                "📅 Your appointment has been rescheduled:\n\n"
                "New Date & Time: {appointment_time}\n"
                "Doctor: Dr. {doctor_name}\n"
                "Location: {location}\n\n"
                "Please reply:\n"
                "1️⃣ to confirm new time\n"
                "2️⃣ if this time doesn't work"
            )
        }
        return templates.get(template_name)

# Create a singleton instance
twilio_client = TwilioClient()

__all__ = ['twilio_client'] 