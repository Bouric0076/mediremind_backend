"""
EmailService module for rendering and sending medication reminder emails.
Integrates TemplateManager to render templates and uses ResendEmailService
for reliable email delivery with idempotency.
"""
import logging
from typing import Dict, Any, Optional
from django.utils.html import strip_tags

from .resend_service import resend_service
from .template_manager import template_manager, TemplateType

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications using Resend backend."""

    def __init__(self):
        self.resend_service = resend_service

    async def send_medication_reminder(
        self,
        to_email: str,
        subject: Optional[str],
        template_data: Dict[str, Any]
    ) -> bool:
        """
        Send a medication reminder email using Resend service.

        Args:
            to_email: Recipient email address
            subject: Optional subject to use; if not provided, template subject is used
            template_data: Dict containing fields like user_name, medication_name, dosage, time, app_url

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not to_email:
                logger.error("No recipient email provided for medication reminder")
                return False

            # Prepare template data for Resend service
            resend_template_data = {
                'medication_name': template_data.get('medication_name', ''),
                'dosage': template_data.get('dosage', ''),
                'time': template_data.get('time', ''),
                'patient_name': template_data.get('user_name', 'Patient'),
                'medication_id': template_data.get('medication_id')
            }

            # Use Resend service for reliable delivery with idempotency
            success, message = self.resend_service.send_medication_reminder_email(
                to_email=to_email,
                patient_name=resend_template_data['patient_name'],
                medication_name=resend_template_data['medication_name'],
                dosage=resend_template_data['dosage'],
                time=resend_template_data['time'],
                medication_id=resend_template_data.get('medication_id')
            )
            
            if success:
                logger.info(f"Medication reminder email sent successfully via Resend to {to_email}")
            else:
                logger.error(f"Failed to send medication reminder email to {to_email}: {message}")
            
            return bool(success)
        except Exception as e:
            logger.error(f"Error sending medication reminder email: {e}")
            return False

    async def send_appointment_confirmation_email(
        self,
        to_email: str,
        appointment_details: Dict[str, Any]
    ) -> bool:
        """
        Send appointment confirmation email using Resend service.

        Args:
            to_email: Recipient email address
            appointment_details: Dict containing appointment information

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not to_email:
                logger.error("No recipient email provided for appointment confirmation")
                return False

            # Use Resend service for reliable delivery with idempotency
            success, message = self.resend_service.send_appointment_confirmation_email(
                to_email=to_email,
                patient_name=appointment_details.get('patient_name', 'Patient'),
                appointment_details=appointment_details
            )
            
            if success:
                logger.info(f"Appointment confirmation email sent successfully via Resend to {to_email}")
            else:
                logger.error(f"Failed to send appointment confirmation email to {to_email}: {message}")
            
            return bool(success)
        except Exception as e:
            logger.error(f"Error sending appointment confirmation email: {e}")
            return False

    async def send_appointment_reminder_email(
        self,
        to_email: str,
        appointment_details: Dict[str, Any]
    ) -> bool:
        """
        Send appointment reminder email using Resend service.

        Args:
            to_email: Recipient email address
            appointment_details: Dict containing appointment information

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not to_email:
                logger.error("No recipient email provided for appointment reminder")
                return False

            # Use Resend service for reliable delivery with idempotency
            success, message = self.resend_service.send_appointment_reminder_email(
                to_email=to_email,
                patient_name=appointment_details.get('patient_name', 'Patient'),
                appointment_details=appointment_details
            )
            
            if success:
                logger.info(f"Appointment reminder email sent successfully via Resend to {to_email}")
            else:
                logger.error(f"Failed to send appointment reminder email to {to_email}: {message}")
            
            return bool(success)
        except Exception as e:
            logger.error(f"Error sending appointment reminder email: {e}")
            return False

    async def send_emergency_alert_email(
        self,
        to_email: str,
        alert_message: str,
        severity: str = 'high'
    ) -> bool:
        """
        Send emergency alert email using Resend service.

        Args:
            to_email: Recipient email address
            alert_message: Emergency alert message
            severity: Alert severity (low, medium, high, critical)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not to_email:
                logger.error("No recipient email provided for emergency alert")
                return False

            # Use Resend service for reliable delivery with idempotency
            success, message = self.resend_service.send_emergency_alert_email(
                to_email=to_email,
                patient_name='Patient',  # Will be handled by template
                alert_message=alert_message,
                severity=severity
            )
            
            if success:
                logger.info(f"Emergency alert email sent successfully via Resend to {to_email}")
            else:
                logger.error(f"Failed to send emergency alert email to {to_email}: {message}")
            
            return bool(success)
        except Exception as e:
            logger.error(f"Error sending emergency alert email: {e}")
            return False

    async def send_welcome_email(
        self,
        to_email: str,
        patient_name: str,
        clinic_name: str = "MediRemind"
    ) -> bool:
        """
        Send welcome email using Resend service.

        Args:
            to_email: Recipient email address
            patient_name: Patient name
            clinic_name: Clinic name (default: MediRemind)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not to_email:
                logger.error("No recipient email provided for welcome email")
                return False

            # Use Resend service for reliable delivery with idempotency
            success, message = self.resend_service.send_welcome_email(
                to_email=to_email,
                patient_name=patient_name,
                clinic_name=clinic_name
            )
            
            if success:
                logger.info(f"Welcome email sent successfully via Resend to {to_email}")
            else:
                logger.error(f"Failed to send welcome email to {to_email}: {message}")
            
            return bool(success)
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return False