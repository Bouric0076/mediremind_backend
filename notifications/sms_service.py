"""
SMSService stub for sending SMS notifications.
Currently implements a simulated send to satisfy imports and enable testing.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SMSService:
    """Simple SMS service stub."""

    async def send_sms(self, phone_number: str, message: str, sender_id: Optional[str] = None) -> bool:
        """
        Simulate sending an SMS message.
        Args:
            phone_number: Destination phone number in E.164 format if possible
            message: SMS text content
            sender_id: Optional sender identifier
        Returns:
            bool: True if simulated send is successful, False otherwise
        """
        try:
            if not phone_number:
                logger.error("SMSService.send_sms called without phone_number")
                return False
            if not message:
                logger.error("SMSService.send_sms called without message")
                return False

            logger.info(f"[SMS STUB] Sending SMS to {phone_number}: {message}")
            return True
        except Exception as e:
            logger.error(f"SMSService error: {e}")
            return False