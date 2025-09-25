import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class BeemClient:
    """Client for interacting with Beem Africa's SMS and WhatsApp APIs"""
    
    def __init__(self):
        self.api_key = settings.BEEM_API_KEY
        self.secret_key = settings.BEEM_SECRET_KEY
        self.sender_id = settings.BEEM_SENDER_ID
        self.whatsapp_template_namespace = os.getenv("BEEM_WHATSAPP_NAMESPACE")
        
        # API endpoints
        self.base_url = "https://apisms.beem.africa/v1/send"
        self.whatsapp_url = "https://api.beem.africa/v1/whatsapp/send-template"
        
        if not all([self.api_key, self.secret_key, self.sender_id]):
            logger.warning("Beem SMS settings not configured")
    
    def send_sms(self, recipient, message):
        """Send SMS to the specified recipient"""
        try:
            # Skip SMS sending in development mode
            if settings.DEBUG:
                logger.info(f"Development mode: SMS skipped. Would send to {recipient}: {message}")
                return True, "SMS skipped - development mode"
                
            if not all([self.api_key, self.secret_key, self.sender_id]):
                logger.warning("Beem SMS settings not configured - skipping SMS")
                return True, "SMS skipped - not configured"

            if not recipient:
                return False, "No recipient specified"

            # Prepare the request
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {self.api_key}:{self.secret_key}'
            }
            
            data = {
                'source_addr': self.sender_id,
                'schedule_time': '',
                'encoding': 0,
                'message': message,
                'recipients': [
                    {
                        'recipient_id': 1,
                        'dest_addr': recipient
                    }
                ]
            }

            # Make the API request
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                verify=True  # Enable SSL verification
            )

            if response.status_code == 200:
                return True, "SMS sent successfully"
            else:
                error_msg = f"SMS sending failed: {response.text}"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"SMS sending failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_whatsapp(self, recipient, template_name, language_code="en", template_params=None):
        """Send WhatsApp message using Beem Africa API"""
        try:
            # Skip WhatsApp sending in development mode
            if settings.DEBUG:
                logger.info(f"Development mode: WhatsApp skipped. Would send to {recipient} template: {template_name}")
                return True, "WhatsApp skipped - development mode"
                
            if not self.whatsapp_template_namespace:
                raise ValueError("WhatsApp template namespace not configured")
                
            payload = {
                "namespace": self.whatsapp_template_namespace,
                "template_name": template_name,
                "language": {"code": language_code},
                "to": recipient
            }
            
            # Add template parameters if provided
            if template_params:
                payload["parameters"] = template_params
            
            response = requests.post(
                self.whatsapp_url,
                json=payload,
                auth=(self.api_key, self.secret_key),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                print(f"WhatsApp message sending failed: {response.text}")
                return False, response.text
                
            return True, "WhatsApp message sent successfully"
            
        except Exception as e:
            print(f"Error sending WhatsApp message: {str(e)}")
            return False, str(e)

# Create a singleton instance
beem_client = BeemClient()

__all__ = ['beem_client']