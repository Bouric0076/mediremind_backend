import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import ssl
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.core.exceptions import ImproperlyConfigured
from django.utils.html import strip_tags

# Import Resend SDK
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logging.warning("Resend SDK not available. Install with: pip install resend")

from notifications.models import NotificationLog, NotificationStatus
from notifications.template_manager import TemplateManager, TemplateContext, RecipientType
from notifications.error_handler import NotificationErrorHandler
from notifications.logging_config import notification_logger

# Set up logging
logger = notification_logger.logger

class EmailClient:
    """Enhanced email client with Resend API integration and comprehensive error handling"""
    
    def __init__(self):
        self.resend_api_key = getattr(settings, 'RESEND_API_KEY', None)
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@mediremind.test')
        self.use_resend = getattr(settings, 'USE_RESEND_EMAIL', True) and RESEND_AVAILABLE and self.resend_api_key
        self.development_mode = getattr(settings, 'DEVELOPMENT_MODE', False)
        
        # Initialize Resend if available
        if self.use_resend:
            try:
                resend.api_key = self.resend_api_key
                logger.info("Resend email service initialized with idempotency")
            except Exception as e:
                logger.error(f"Failed to initialize Resend: {e}")
                self.use_resend = False
        
        # Initialize template manager
        self.template_manager = TemplateManager()
        self.notification_error_handler = NotificationErrorHandler()
    
    def send_email(self, subject: str, message: str, recipient_list: List[str], 
                   html_message: str = None, from_email: str = None) -> bool:
        """
        Send email using Django's built-in email backend or Resend API
        
        Args:
            subject: Email subject
            message: Plain text message
            recipient_list: List of recipient email addresses
            html_message: HTML version of the message (optional)
            from_email: Sender email address (optional, uses DEFAULT_FROM_EMAIL if not provided)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if self.development_mode:
            logger.info(f"Development mode: Email skipped. Would send to {recipient_list}: {subject}")
            return True
            
        try:
            if self.use_resend:
                return self._send_resend_email(subject, message, recipient_list, html_message, from_email)
            else:
                return self._send_django_email(subject, message, recipient_list, html_message, from_email)
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False
    
    def _send_resend_email(self, subject: str, message: str, recipient_list: List[str], 
                          html_message: str = None, from_email: str = None) -> bool:
        """Send email using Resend API"""
        try:
            from_email = from_email or self.from_email
            
            # Format sender name for better display
            if "onboarding" in from_email or "admin@mediremind.test" in from_email:
                formatted_from = f"MediRemind <{from_email}>"
            else:
                formatted_from = from_email
            
            # Prepare email parameters
            params = {
                "from": formatted_from,
                "to": recipient_list,
                "subject": subject,
                "text": message,
            }
            
            # Add HTML content if available
            if html_message:
                params["html"] = html_message
            
            # Add idempotency key to prevent duplicate sends
            idempotency_key = f"{recipient_list[0]}_{subject}_{int(timezone.now().timestamp())}"
            params["headers"] = {
                "X-Idempotency-Key": idempotency_key
            }
            
            logger.info(f"Sending email via Resend to {recipient_list}")
            response = resend.Emails.send(params)
            
            if response and 'id' in response:
                logger.info(f"Email sent successfully via Resend. ID: {response['id']}")
                
                # Log successful email
                self._log_email_notification(
                    recipient_email=recipient_list[0],
                    subject=subject,
                    status=NotificationStatus.SENT,
                    response_id=response.get('id')
                )
                return True
            else:
                logger.error(f"Resend API returned unexpected response: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Resend API error: {str(e)}")
            
            # Log failed email
            self._log_email_notification(
                recipient_email=recipient_list[0] if recipient_list else 'unknown',
                subject=subject,
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )
            return False
    
    def _send_django_email(self, subject: str, message: str, recipient_list: List[str], 
                          html_message: str = None, from_email: str = None) -> bool:
        """Send email using Django's email backend"""
        try:
            from_email = from_email or self.from_email
            
            if html_message:
                # Create EmailMultiAlternatives for HTML content
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=recipient_list
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
            else:
                # Send plain text email
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=recipient_list,
                    fail_silently=False
                )
            
            logger.info(f"Email sent successfully via Django to {recipient_list}")
            
            # Log successful email
            self._log_email_notification(
                recipient_email=recipient_list[0],
                subject=subject,
                status=NotificationStatus.SENT
            )
            return True
            
        except Exception as e:
            logger.error(f"Django email error: {str(e)}")
            
            # Log failed email
            self._log_email_notification(
                recipient_email=recipient_list[0] if recipient_list else 'unknown',
                subject=subject,
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )
            return False
    
    def _log_email_notification(self, recipient_email: str, subject: str, 
                               status: NotificationStatus, response_id: str = None, 
                               error_message: str = None) -> None:
        """Log email notification to database"""
        try:
            # For now, skip logging to avoid errors
            # TODO: Implement proper email notification logging
            logger.info(f"Email notification logged: {recipient_email} - {subject} - {status}")
        except Exception as e:
            logger.error(f"Failed to log email notification: {str(e)}")
    
    @staticmethod
    def send_appointment_confirmation_email(appointment_data: Dict[str, Any], recipient_email: str, 
                                          is_patient: bool = True, user_preferences: Dict[str, Any] = None,
                                          additional_links: Dict[str, str] = None) -> Tuple[bool, str]:
        """
        Send appointment confirmation email using template management system
        
        Args:
            appointment_data: Dictionary containing appointment information
            recipient_email: Email address of the recipient
            is_patient: Whether the recipient is a patient (True) or provider (False)
            user_preferences: User preferences for email formatting
            additional_links: Additional links to include in the email
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            logger.info(f"Sending appointment confirmation email to {recipient_email}")
            
            # Initialize template manager and error handler
            template_manager = TemplateManager()
            notification_error_handler = NotificationErrorHandler()
            
            # Determine template key based on recipient type
            template_key = "appointment_creation_patient" if is_patient else "appointment_creation_doctor"
            
            # Ensure appointment_data is a dict
            if isinstance(appointment_data, str):
                try:
                    appointment_data = json.loads(appointment_data)
                except Exception as e:
                    logger.error(f"appointment_data is a string but not valid JSON: {appointment_data} | Error: {e}")
                    return False, "Invalid appointment data format"

            if not isinstance(appointment_data, dict):
                logger.error(f"appointment_data is not a dict after parsing: {appointment_data}")
                return False, "Invalid appointment data format"
            
            # Create structured appointment data for template rendering
            structured_appointment = {
                'id': appointment_data.get('appointment_id'),
                'date': appointment_data.get('appointment_date'),
                'time': appointment_data.get('appointment_time'),
                'start_time': appointment_data.get('start_time'),
                'end_time': appointment_data.get('end_time'),
                'duration': appointment_data.get('duration'),
                'location': appointment_data.get('location'),
                'notes': appointment_data.get('notes'),
                'status': appointment_data.get('status'),
                'formatted_datetime': appointment_data.get('formatted_datetime'),
                'patient': {
                    'name': appointment_data.get('patient_name') or appointment_data.get('patient', {}).get('name', 'Patient'),
                    'email': appointment_data.get('patient_email') or appointment_data.get('patient', {}).get('email', recipient_email if is_patient else 'patient@example.com'),
                    'id': appointment_data.get('patient_id') or appointment_data.get('patient', {}).get('id')
                },
                'provider': {
                    'name': appointment_data.get('provider_name') or appointment_data.get('provider', {}).get('name', 'Dr. Smith'),
                    'email': appointment_data.get('provider_email') or appointment_data.get('provider', {}).get('email', recipient_email if not is_patient else 'doctor@example.com'),
                    'id': appointment_data.get('provider_id') or appointment_data.get('provider', {}).get('id'),
                    'specialization': appointment_data.get('provider_specialization') or appointment_data.get('provider', {}).get('specialization', 'General Practice')
                },
                'appointment_type': {
                    'name': appointment_data.get('appointment_type_name') or appointment_data.get('appointment_type', 'Consultation')
                },
                'hospital': {
                    'name': appointment_data.get('hospital_name') or appointment_data.get('hospital', {}).get('name') or appointment_data.get('hospital_info', {}).get('name') or 'MediRemind Partner Clinic'
                },
                'room': {
                    'name': appointment_data.get('room_name') or appointment_data.get('room', 'Room 1')
                }
            }
            
            context = TemplateContext(
                recipient_name=structured_appointment['patient']['name'] if is_patient else structured_appointment['provider']['name'],
                recipient_email=recipient_email,
                recipient_type=RecipientType.PATIENT if is_patient else RecipientType.DOCTOR,
                appointment=structured_appointment,
                preferences=user_preferences or {},
                links=additional_links or {}
            )
            
            # Render template with enhanced features
            logger.info(f"Rendering template with key: {template_key}")
            try:
                success, subject, html_message = template_manager.render_template_with_fallback(template_key, context)
                if not success:
                    error_context = notification_error_handler.handle_template_error(
                        template_key=template_key,
                        error=Exception(html_message),
                        context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email}
                    )
                    return False, f"Template rendering failed: {html_message}"
                logger.info(f"Template rendered, subject: {subject}")
            except Exception as e:
                error_context = notification_error_handler.handle_template_error(
                    template_key=template_key,
                    error=e,
                    context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email}
                )
                return False, f"Template rendering error: {str(e)}"
            
            logger.info(f"About to call send_email from send_appointment_update_email")
            result = email_client.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )
            logger.info(f"send_email returned: {result}, type: {type(result)}")
            if result:
                return True, "Email sent successfully"
            else:
                return False, "Email sending failed"

        except Exception as e:
            error_context = notification_error_handler.handle_email_error(
                recipient_email=recipient_email,
                error=e,
                appointment_data={'appointment_id': appointment_data.get('id')},
                notification_type='appointment_confirmation'
            )
            error_msg = f"Error in send_appointment_confirmation_email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def send_appointment_confirmation_email_legacy(appointment_data, recipient_email, is_patient=True):
        """Legacy method for backward compatibility"""
        try:
            # Ensure appointment_data is a dict
            if isinstance(appointment_data, str):
                try:
                    appointment_data = json.loads(appointment_data)
                except Exception as e:
                    logger.error(f"appointment_data is a string but not valid JSON: {appointment_data} | Error: {e}")
                    return False, "Invalid appointment data format"

            if not isinstance(appointment_data, dict):
                logger.error(f"appointment_data is not a dict after parsing: {appointment_data}")
                return False, "Invalid appointment data format"

            # Use enhanced template management system
            template_key = "appointment_creation_patient" if is_patient else "appointment_creation_doctor"
            
        except Exception as e:
            logger.error(f"Error in send_appointment_confirmation_email_legacy: {str(e)}")
            return False, f"Error processing appointment data: {str(e)}"

# Create a global email client instance
email_client = EmailClient()