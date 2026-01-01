"""
TextSMS Client for Kenya SMS API Integration
Replaces Beem Africa SMS service with TextSMS.co.ke API
"""

import os
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

@dataclass
class SMSMessage:
    """Data class for SMS message"""
    mobile: str
    message: str
    shortcode: str = "TextSMS"
    client_sms_id: Optional[str] = None
    time_to_send: Optional[str] = None

@dataclass
class SMSResponse:
    """Data class for SMS API response"""
    success: bool
    message: str
    response_code: Optional[int] = None
    message_id: Optional[str] = None
    mobile: Optional[str] = None
    network_id: Optional[str] = None
    client_sms_id: Optional[str] = None

class TextSMSClient:
    """Client for interacting with TextSMS.co.ke SMS API"""
    
    # API Endpoints
    SEND_SMS_URL = "https://sms.textsms.co.ke/api/services/sendsms/"
    SEND_BULK_URL = "https://sms.textsms.co.ke/api/services/sendbulk/"
    GET_DLR_URL = "https://sms.textsms.co.ke/api/services/getdlr/"
    GET_BALANCE_URL = "https://sms.textsms.co.ke/api/services/getbalance/"
    
    # Response codes mapping
    RESPONSE_CODES = {
        0: "Successful Request Call",  # TextSMS uses 0 for success
        200: "Successful Request Call",
        1001: "Invalid sender id",
        1002: "Network not allowed",
        1003: "Invalid mobile number",
        1004: "Low bulk credits",
        1005: "Failed. System error",
        1006: "Invalid credentials",
        1007: "Failed. System error",
        1008: "No Delivery Report",
        1009: "Unsupported data type",
        1010: "Unsupported request type",
        4090: "Internal Error. Try again after 5 minutes",
        4091: "No Partner ID is Set",
        4092: "No API KEY Provided",
        4093: "Details Not Found"
    }
    
    def __init__(self):
        """Initialize TextSMS client with configuration"""
        self.api_key = getattr(settings, 'TEXTSMS_API_KEY', None)
        self.partner_id = getattr(settings, 'TEXTSMS_PARTNER_ID', None)
        self.sender_id = getattr(settings, 'TEXTSMS_SENDER_ID', 'TextSMS')
        
        # Validate configuration
        if not all([self.api_key, self.partner_id]):
            logger.warning("TextSMS settings not configured properly")
            
    def _format_mobile_number(self, mobile: str) -> str:
        """Format mobile number to Kenyan format (254XXXXXXXXX)"""
        import re
        
        # Remove any spaces, dashes, parentheses, or plus signs
        mobile = re.sub(r'[\s\-\(\)\+]', '', mobile)
        
        # Handle different formats
        if mobile.startswith('0'):
            # Convert 07XXXXXXXX to 2547XXXXXXXX
            mobile = '254' + mobile[1:]
        elif mobile.startswith('7') and len(mobile) == 9:
            # Convert 7XXXXXXXX to 2547XXXXXXXX
            mobile = '254' + mobile
        elif mobile.startswith('1') and len(mobile) == 10 and mobile[1:4] == '26':
            # Handle format like "12608815999" (appears to be US format but actually Kenyan)
            # Remove the "1" prefix and add "254"
            mobile = '254' + mobile[3:]
        elif mobile.startswith('254') and len(mobile) == 12:
            # Already in correct format
            pass
        elif not mobile.startswith('254') and len(mobile) == 9:
            # Assume it's a Kenyan number (7XXXXXXXX) and add 254
            mobile = '254' + mobile
        else:
            # For any other format, try to extract 9 digits starting with 7
            match = re.search(r'7\d{8}', mobile)
            if match:
                mobile = '254' + match.group()
            else:
                # If no valid Kenyan format found, return as-is and let validation handle it
                pass
            
        return mobile
    
    def _make_request(self, url: str, data: Dict, method: str = 'POST') -> Dict:
        """Make HTTP request to TextSMS API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            if method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, params=data, headers=headers, timeout=30)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"TextSMS API request failed: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"TextSMS API response parsing failed: {str(e)}")
            raise
    
    def send_sms(self, recipient: str, message: str, shortcode: Optional[str] = None, 
                 schedule_time: Optional[str] = None) -> Tuple[bool, str]:
        """
        Send single SMS message
        
        Args:
            recipient: Mobile number (will be formatted to 254XXXXXXXXX)
            message: SMS message content
            shortcode: Sender ID (optional, defaults to configured sender_id)
            schedule_time: Schedule time in format "YYYY-MM-DD HH:MM" (optional)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Skip SMS sending in development mode
            if getattr(settings, 'DEBUG', False):
                logger.info(f"Development mode: SMS skipped. Would send to {recipient}: {message}")
                return True, "SMS skipped - development mode"
                
            if not all([self.api_key, self.partner_id]):
                logger.warning("TextSMS settings not configured - skipping SMS")
                return True, "SMS skipped - not configured"

            if not recipient or not message:
                return False, "Recipient and message are required"

            # Format mobile number
            formatted_mobile = self._format_mobile_number(recipient)
            
            # Prepare request data
            data = {
                "apikey": self.api_key,
                "partnerID": self.partner_id,
                "message": message,
                "shortcode": shortcode or self.sender_id,
                "mobile": formatted_mobile
            }
            
            # Add schedule time if provided
            if schedule_time:
                data["timeToSend"] = schedule_time
            
            # Make API request
            response = self._make_request(self.SEND_SMS_URL, data)
            
            # Parse response
            if 'responses' in response and len(response['responses']) > 0:
                first_response = response['responses'][0]
                # Try both possible field names for response code
                response_code = first_response.get('response-code') or first_response.get('respose-code', 0)
                
                # TextSMS API returns 0 for successful SMS sending, not 200
                if response_code == 0 or response_code == 200:
                    message_id = first_response.get('messageid')
                    logger.info(f"SMS sent successfully to {formatted_mobile}, Message ID: {message_id}")
                    return True, f"SMS sent successfully. Message ID: {message_id}"
                else:
                    error_msg = self.RESPONSE_CODES.get(response_code, f"Unknown error code: {response_code}")
                    logger.error(f"SMS sending failed: {error_msg}")
                    return False, error_msg
            else:
                logger.error("Invalid response format from TextSMS API")
                return False, "Invalid response format"

        except Exception as e:
            error_msg = f"SMS sending failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_bulk_sms(self, messages: List[SMSMessage]) -> List[SMSResponse]:
        """
        Send bulk SMS messages (up to 20 messages per call)
        
        Args:
            messages: List of SMSMessage objects
            
        Returns:
            List of SMSResponse objects
        """
        try:
            if not messages:
                return []
                
            if len(messages) > 20:
                logger.warning("TextSMS API supports max 20 messages per bulk call. Truncating.")
                messages = messages[:20]
            
            # Skip SMS sending in development mode
            if getattr(settings, 'DEBUG', False):
                logger.info(f"Development mode: Bulk SMS skipped. Would send {len(messages)} messages")
                return [SMSResponse(True, "SMS skipped - development mode") for _ in messages]
                
            if not all([self.api_key, self.partner_id]):
                logger.warning("TextSMS settings not configured - skipping bulk SMS")
                return [SMSResponse(True, "SMS skipped - not configured") for _ in messages]
            
            # Prepare bulk request data
            sms_list = []
            for i, msg in enumerate(messages):
                sms_data = {
                    "partnerID": self.partner_id,
                    "apikey": self.api_key,
                    "mobile": self._format_mobile_number(msg.mobile),
                    "message": msg.message,
                    "shortcode": msg.shortcode or self.sender_id,
                    "pass_type": "plain"
                }
                
                if msg.client_sms_id:
                    sms_data["clientsmsid"] = msg.client_sms_id
                else:
                    sms_data["clientsmsid"] = f"bulk_{int(datetime.now().timestamp())}_{i}"
                    
                if msg.time_to_send:
                    sms_data["timeToSend"] = msg.time_to_send
                    
                sms_list.append(sms_data)
            
            bulk_data = {
                "count": len(sms_list),
                "smslist": sms_list
            }
            
            # Make API request
            response = self._make_request(self.SEND_BULK_URL, bulk_data)
            
            # Parse responses
            results = []
            if 'responses' in response:
                for resp in response['responses']:
                    response_code = resp.get('respose-code', 0)  # Note: API has typo "respose"
                    success = response_code == 200
                    message = self.RESPONSE_CODES.get(response_code, f"Unknown error code: {response_code}")
                    
                    results.append(SMSResponse(
                        success=success,
                        message=message,
                        response_code=response_code,
                        message_id=resp.get('messageid'),
                        mobile=resp.get('mobile'),
                        network_id=resp.get('networkid'),
                        client_sms_id=resp.get('clientsmsid')
                    ))
            
            return results
            
        except Exception as e:
            error_msg = f"Bulk SMS sending failed: {str(e)}"
            logger.error(error_msg)
            return [SMSResponse(False, error_msg) for _ in messages]
    
    def get_delivery_report(self, message_id: str) -> Dict:
        """
        Get delivery report for a sent message
        
        Args:
            message_id: Message ID returned from send_sms
            
        Returns:
            Dictionary with delivery report data
        """
        try:
            if not all([self.api_key, self.partner_id, message_id]):
                return {"error": "Missing required parameters"}
            
            data = {
                "apikey": self.api_key,
                "partnerID": self.partner_id,
                "messageID": message_id
            }
            
            response = self._make_request(self.GET_DLR_URL, data)
            return response
            
        except Exception as e:
            logger.error(f"Failed to get delivery report: {str(e)}")
            return {"error": str(e)}
    
    def get_account_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            Dictionary with balance information
        """
        try:
            if not all([self.api_key, self.partner_id]):
                return {"error": "Missing API credentials"}
            
            data = {
                "apikey": self.api_key,
                "partnerID": self.partner_id
            }
            
            response = self._make_request(self.GET_BALANCE_URL, data)
            return response
            
        except Exception as e:
            logger.error(f"Failed to get account balance: {str(e)}")
            return {"error": str(e)}
    
    def send_scheduled_sms(self, recipient: str, message: str, schedule_datetime: datetime,
                          shortcode: Optional[str] = None) -> Tuple[bool, str]:
        """
        Send SMS at a scheduled time
        
        Args:
            recipient: Mobile number
            message: SMS message content
            schedule_datetime: When to send the message
            shortcode: Sender ID (optional)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Format datetime for TextSMS API
        schedule_time = schedule_datetime.strftime("%Y-%m-%d %H:%M")
        return self.send_sms(recipient, message, shortcode, schedule_time)
    
    def send_whatsapp(self, recipient: str, template_name: str, language_code: str = "en", 
                     template_params: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        WhatsApp functionality placeholder (TextSMS doesn't support WhatsApp)
        Maintained for compatibility with existing code
        
        Returns:
            Tuple indicating WhatsApp is not supported
        """
        logger.warning("WhatsApp messaging not supported by TextSMS API")
        return False, "WhatsApp messaging not supported by TextSMS API"

# Create singleton instance
textsms_client = TextSMSClient()

__all__ = ['textsms_client', 'TextSMSClient', 'SMSMessage', 'SMSResponse']