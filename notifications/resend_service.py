"""
Comprehensive Resend email service for reliable, idempotent email delivery in production.
This service provides async email sending with proper error handling, retry logic, and
deduplication to ensure emails are sent exactly once.
Integrates with TemplateManager for consistent template rendering across all email types.
"""
import logging
import os
import hashlib
import json
from typing import Dict, Optional, Tuple, Any
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import resend

from .template_manager import template_manager, TemplateType, RecipientType, TemplateContext

logger = logging.getLogger(__name__)


class ResendEmailService:
    """Production-grade, idempotent email service using Resend API"""
    
    def __init__(self):
        """Initialize Resend with API key and deduplication cache"""
        self.api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('RESEND_FROM_EMAIL', 'noreply@mediremind.com')
        self.from_name = os.getenv('RESEND_FROM_NAME', 'MediRemind')
        self.deduplication_ttl = int(os.getenv('EMAIL_DEDUPLICATION_TTL', '86400'))  # 24 hours default
        
        if self.api_key:
            resend.api_key = self.api_key
            logger.info("Resend email service initialized with idempotency")
        else:
            logger.warning("RESEND_API_KEY not configured - email service will be disabled")
    
    def _generate_message_id(self, to_email: str, subject: str, content_hash: str, tags: Dict[str, str] = None) -> str:
        """Generate a unique message ID for deduplication"""
        # Create a deterministic hash based on email content and metadata
        id_components = [
            to_email.lower().strip(),
            subject.strip(),
            content_hash,
            json.dumps(tags or {}, sort_keys=True)
        ]
        message_id = hashlib.sha256("|".join(id_components).encode()).hexdigest()[:32]
        return f"msg_{message_id}"
    
    def _is_duplicate_message(self, message_id: str) -> bool:
        """Check if this message has already been sent recently"""
        cache_key = f"email_sent:{message_id}"
        return cache.get(cache_key) is not None
    
    def _mark_message_sent(self, message_id: str, resend_id: str = None):
        """Mark a message as sent in the cache"""
        cache_key = f"email_sent:{message_id}"
        cache.set(cache_key, {
            'sent_at': timezone.now().isoformat(),
            'resend_id': resend_id
        }, self.deduplication_ttl)
        logger.info(f"Message {message_id} marked as sent with TTL {self.deduplication_ttl}")
    
    def _sanitize_tags(self, tags: Dict[str, str]) -> Dict[str, str]:
        """Sanitize tags to comply with Resend API requirements"""
        sanitized = {}
        logger.debug(f"Sanitizing tags: {tags}")
        for key, value in tags.items():
            # Replace invalid characters with underscores
            sanitized_key = ''.join(c if c.isalnum() or c in '-_' else '_' for c in key)
            # For email addresses, replace @ with _at_ and . with _dot_
            sanitized_value = str(value)
            if '@' in sanitized_value and '.' in sanitized_value:
                # It's likely an email address
                sanitized_value = sanitized_value.replace('@', '_at_').replace('.', '_dot_')
            else:
                # Regular sanitization for other values
                sanitized_value = sanitized_value.replace(' ', '_').replace(':', '_').replace('/', '_')
            sanitized[sanitized_key] = sanitized_value
            logger.debug(f"Sanitized tag: {key} -> {sanitized_key}, {value} -> {sanitized_value}")
        logger.debug(f"Final sanitized tags: {sanitized}")
        return sanitized
    
    def _get_email_hash(self, html_content: str, text_content: str = None) -> str:
        """Generate a hash of email content for deduplication"""
        content_to_hash = html_content
        if text_content:
            content_to_hash += f"|{text_content}"
        return hashlib.sha256(content_to_hash.encode()).hexdigest()[:16]
    
    def render_template(
        self,
        template_type: TemplateType,
        recipient_name: str,
        recipient_email: str,
        template_data: Dict[str, Any],
        recipient_type: RecipientType = RecipientType.PATIENT
    ) -> Tuple[str, str]:
        """
        Render email template using TemplateManager
        
        Args:
            template_type: Type of template to render
            recipient_name: Name of recipient
            recipient_email: Email of recipient
            template_data: Data for template rendering
            recipient_type: Type of recipient (patient, doctor, admin)
            
        Returns:
            Tuple of (subject, html_content)
        """
        try:
            # Create template context
            context = TemplateContext(
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                recipient_type=recipient_type,
                personalization=template_data
            )
            
            # Render template using TemplateManager
            subject, html_content = template_manager.render_template(
                template_type,
                context
            )
            
            return subject, html_content
            
        except Exception as e:
            logger.error(f"Failed to render template {template_type.value}: {str(e)}")
            raise
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enable_idempotency: bool = True,
        from_email: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Send email using Resend API with optional idempotency
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Optional plain text content
            reply_to: Optional reply-to address
            tags: Optional tags for tracking
            enable_idempotency: Whether to enable deduplication (default: True)
            from_email: Optional custom from email address (overrides default)
            
        Returns:
            Tuple of (success, message)
        """
        if not self.api_key:
            return False, "Resend API key not configured"
        
        if not to_email:
            return False, "No recipient email provided"
        
        # Generate content hash for idempotency
        content_hash = self._get_email_hash(html_content, text_content)
        
        # Generate unique message ID for deduplication
        message_id = self._generate_message_id(to_email, subject, content_hash, tags)
        
        # Check for duplicate if idempotency is enabled
        if enable_idempotency and self._is_duplicate_message(message_id):
            logger.info(f"Duplicate email detected and skipped: {message_id}")
            cached_data = cache.get(f"email_sent:{message_id}")
            if cached_data and cached_data.get('resend_id'):
                return True, f"DUPLICATE_SKIPPED_{cached_data['resend_id']}"
            return True, "DUPLICATE_SKIPPED"
        
        try:
            # Prepare email parameters
            from_address = from_email or self.from_email
            params = {
                "from": f"{self.from_name} <{from_address}>",
                "to": to_email,
                "subject": subject,
                "html": html_content,
            }
            
            # Add text content if provided
            if text_content:
                params["text"] = text_content
            
            # Add reply-to if provided
            if reply_to:
                params["reply_to"] = reply_to
            
            # Add tags if provided
            if tags:
                sanitized_tags = self._sanitize_tags(tags)
                logger.debug(f"Adding sanitized tags to email: {sanitized_tags}")
                params["tags"] = sanitized_tags
            
            # Add custom headers for tracking
            params["headers"] = {
                "X-Message-ID": message_id,
                "X-Sent-At": timezone.now().isoformat()
            }
            
            # Send email via Resend
            response = resend.Emails.send(params)
            
            # Check if email was sent successfully
            if response and response.get('id'):
                resend_id = response['id']
                logger.info(f"Email sent successfully via Resend to {to_email}, ID: {resend_id}")
                
                # Mark as sent in cache if idempotency is enabled
                if enable_idempotency:
                    self._mark_message_sent(message_id, resend_id)
                
                return True, resend_id
            else:
                error_msg = f"Resend API returned unexpected response: {response}"
                logger.error(error_msg)
                return False, error_msg
                
        except resend.exceptions.ResendError as e:
            error_msg = f"Resend API error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error sending email via Resend: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_appointment_confirmation_email(
        self,
        to_email: str,
        patient_name: str,
        appointment_details: Dict,
        from_email: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Send appointment confirmation email using TemplateManager
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            appointment_details: Dictionary with appointment information
            from_email: Optional custom from email address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Prepare template data
            template_data = {
                'appointment': appointment_details,
                'patient_name': patient_name,
                'date': appointment_details.get('date'),
                'time': appointment_details.get('time'),
                'doctor_name': appointment_details.get('doctor_name'),
                'location': appointment_details.get('location'),
                'appointment_type': appointment_details.get('appointment_type', 'Consultation'),
                'notes': appointment_details.get('notes')
            }
            
            # Render template using TemplateManager
            subject, html_content = self.render_template(
                template_type=TemplateType.APPOINTMENT_CONFIRMATION,
                recipient_name=patient_name,
                recipient_email=to_email,
                template_data=template_data,
                recipient_type=RecipientType.PATIENT
            )
            
            # Send email with Resend
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                tags={
                    'type': 'appointment_confirmation',
                    'appointment_id': str(appointment_details.get('id', '')),
                    'patient_email': to_email
                },
                from_email=from_email
            )
            
        except Exception as e:
            error_msg = f"Failed to send appointment confirmation email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        text_content = f"""
        Appointment Confirmed
        
        Dear {patient_name},
        
        Your appointment has been confirmed:
        
        Date: {appointment_details.get('date', 'TBD')}
        Time: {appointment_details.get('time', 'TBD')}
        Doctor: {appointment_details.get('doctor_name', 'TBD')}
        Location: {appointment_details.get('location', 'TBD')}
        Type: {appointment_details.get('appointment_type', 'Consultation')}
        {f'Notes: {appointment_details.get("notes")}' if appointment_details.get('notes') else ''}
        
        If you need to reschedule or cancel, please contact us.
        
        Best regards,
        The MediRemind Team
        """
        
        tags = {
            'type': 'appointment_confirmation',
            'patient_id': str(appointment_details.get('patient_id', '')),
            'appointment_id': str(appointment_details.get('id', ''))
        }
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags=tags
        )
    
    def send_appointment_reminder_email(
        self,
        to_email: str,
        patient_name: str,
        appointment_details: Dict,
        from_email: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Send appointment reminder email using TemplateManager
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            appointment_details: Dictionary with appointment information
            from_email: Optional custom from email address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Prepare template data
            template_data = {
                'appointment': appointment_details,
                'patient_name': patient_name,
                'date': appointment_details.get('date'),
                'time': appointment_details.get('time'),
                'doctor_name': appointment_details.get('doctor_name'),
                'location': appointment_details.get('location'),
                'appointment_type': appointment_details.get('appointment_type', 'Consultation'),
                'reminder_time': 'tomorrow'  # This is a reminder for tomorrow
            }
            
            # Render template using TemplateManager
            subject, html_content = self.render_template(
                template_type=TemplateType.APPOINTMENT_REMINDER,
                recipient_name=patient_name,
                recipient_email=to_email,
                template_data=template_data,
                recipient_type=RecipientType.PATIENT
            )
            
            # Send email with Resend
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                tags={
                    'type': 'appointment_reminder',
                    'appointment_id': str(appointment_details.get('id', '')),
                    'patient_email': to_email,
                    'reminder_type': 'tomorrow'
                },
                from_email=from_email
            )
            
        except Exception as e:
            error_msg = f"Failed to send appointment reminder email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Appointment Reminder</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 5px; }}
                .appointment-details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Appointment Reminder</h1>
                </div>
                <div class="content">
                    <p>Dear {patient_name},</p>
                    <p>This is a friendly reminder about your upcoming appointment:</p>
                    
                    <div class="appointment-details">
                        <h3>Appointment Details</h3>
                        <p><strong>Date:</strong> {appointment_details.get('date', 'TBD')}</p>
                        <p><strong>Time:</strong> {appointment_details.get('time', 'TBD')}</p>
                        <p><strong>Doctor:</strong> {appointment_details.get('doctor_name', 'TBD')}</p>
                        <p><strong>Location:</strong> {appointment_details.get('location', 'TBD')}</p>
                        <p><strong>Type:</strong> {appointment_details.get('appointment_type', 'Consultation')}</p>
                    </div>
                    
                    <p>Please arrive 15 minutes early for check-in.</p>
                    
                    <p>If you need to reschedule or cancel, please contact us as soon as possible.</p>
                    
                    <p>Best regards,<br>
                    The MediRemind Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated reminder. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Appointment Reminder
        
        Dear {patient_name},
        
        This is a reminder about your upcoming appointment:
        
        Date: {appointment_details.get('date', 'TBD')}
        Time: {appointment_details.get('time', 'TBD')}
        Doctor: {appointment_details.get('doctor_name', 'TBD')}
        Location: {appointment_details.get('location', 'TBD')}
        Type: {appointment_details.get('appointment_type', 'Consultation')}
        
        Please arrive 15 minutes early for check-in.
        
        If you need to reschedule or cancel, please contact us.
        
        Best regards,
        The MediRemind Team
        """
        
        tags = {
            'type': 'appointment_reminder',
            'patient_id': str(appointment_details.get('patient_id', '')),
            'appointment_id': str(appointment_details.get('id', ''))
        }
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags=tags
        )
    
    def send_medication_reminder_email(
        self,
        to_email: str,
        patient_name: str,
        medication_name: str,
        dosage: str,
        time: str,
        medication_id: int = None,
        from_email: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Send medication reminder email using TemplateManager
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            medication_name: Medication name
            dosage: Medication dosage
            time: Time to take medication
            medication_id: Optional medication ID for tracking
            from_email: Optional custom from email address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Prepare template data
            template_data = {
                'medication_name': medication_name,
                'dosage': dosage,
                'time': time,
                'patient_name': patient_name,
                'medication_id': medication_id
            }
            
            # Render template using TemplateManager
            subject, html_content = self.render_template(
                template_type=TemplateType.MEDICATION_REMINDER,
                recipient_name=patient_name,
                recipient_email=to_email,
                template_data=template_data,
                recipient_type=RecipientType.PATIENT
            )
            
            # Send email with Resend
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                tags={
                    'type': 'medication_reminder',
                    'medication_name': medication_name,
                    'medication_id': str(medication_id) if medication_id else '',
                    'patient_email': to_email
                },
                from_email=from_email
            )
            
        except Exception as e:
            error_msg = f"Failed to send medication reminder email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        text_content = f"""
        Medication Reminder
        
        Dear {patient_name},
        
        It's time to take your medication:
        
        Medication: {medication_name}
        Dosage: {dosage}
        Time: {time}
        
        Please take your medication as prescribed.
        
        Best regards,
        The MediRemind Team
        """
        
        tags = {
            'type': 'medication_reminder',
            'patient_id': str(medication_id) if medication_id else '',
            'medication_name': medication_name
        }
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags=tags
        )
    
    def send_emergency_alert_email(
        self,
        to_email: str,
        patient_name: str,
        alert_message: str,
        severity: str = 'high',
        from_email: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Send emergency alert email using TemplateManager
        
        Args:
            to_email: Recipient email address
            patient_name: Patient name
            alert_message: Emergency alert message
            severity: Alert severity (low, medium, high, critical)
            from_email: Optional custom from email address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Prepare template data
            template_data = {
                'alert_message': alert_message,
                'severity': severity,
                'patient_name': patient_name,
                'alert_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Render template using TemplateManager
            subject, html_content = self.render_template(
                template_type=TemplateType.EMERGENCY_NOTIFICATION,
                recipient_name=patient_name,
                recipient_email=to_email,
                template_data=template_data,
                recipient_type=RecipientType.PATIENT
            )
            
            # Send email with Resend
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                tags={
                    'type': 'emergency_alert',
                    'severity': severity,
                    'patient_email': to_email
                },
                from_email=from_email
            )
            
        except Exception as e:
            error_msg = f"Failed to send emergency alert email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        text_content = f"""
        EMERGENCY ALERT - SEVERITY: {severity.upper()}
        
        Dear {patient_name},
        
        An emergency alert has been triggered:
        
        Message: {alert_message}
        Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        Severity: {severity.upper()}
        
        Please take immediate action as appropriate.
        
        If this is a medical emergency, call 911 immediately.
        
        Best regards,
        The MediRemind Team
        """
        
        tags = {
            'type': 'emergency_alert',
            'severity': severity.lower(),
            'patient_name': patient_name
        }
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags=tags
        )
    
    def send_appointment_update_email(
        self,
        to_email: str,
        patient_name: str,
        appointment_details: Dict,
        update_type: str,
        is_patient: bool = True
    ) -> Tuple[bool, str]:
        """
        Send appointment update email (reschedule/cancellation)
        
        Args:
            to_email: Recipient email address
            patient_name: Patient name
            appointment_details: Dictionary with appointment information
            update_type: Type of update ('reschedule', 'cancellation')
            is_patient: Whether recipient is patient (True) or doctor (False)
            
        Returns:
            Tuple of (success, message)
        """
        # Determine subject and styling based on update type
        if update_type.lower() == 'reschedule':
            subject = f"🔄 Appointment Rescheduled - {appointment_details.get('date', 'TBD')}"
            header_color = '#2196F3'
            header_text = 'Appointment Rescheduled'
        elif update_type.lower() == 'cancellation':
            subject = f"❌ Appointment Cancelled - {appointment_details.get('date', 'TBD')}"
            header_color = '#F44336'
            header_text = 'Appointment Cancelled'
        else:
            return False, f"Invalid update type: {update_type}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{header_text}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {header_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 5px; }}
                .appointment-details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{header_text}</h1>
                </div>
                <div class="content">
                    <p>Dear {patient_name},</p>
                    <p>Your appointment has been {update_type.lower()}d. Here are the updated details:</p>
                    
                    <div class="appointment-details">
                        <h3>Appointment Details</h3>
                        <p><strong>Date:</strong> {appointment_details.get('date', 'TBD')}</p>
                        <p><strong>Time:</strong> {appointment_details.get('time', 'TBD')}</p>
                        <p><strong>Doctor:</strong> {appointment_details.get('doctor_name', 'TBD')}</p>
                        <p><strong>Location:</strong> {appointment_details.get('location', 'TBD')}</p>
                        {f'<p><strong>Reason:</strong> {appointment_details.get("reason")}</p>' if appointment_details.get('reason') else ''}
                    </div>
                    
                    <p>If you have any questions, please contact us.</p>
                    
                    <p>Best regards,<br>
                    The MediRemind Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        {header_text.upper()}
        
        Dear {patient_name},
        
        Your appointment has been {update_type.lower()}d:
        
        Date: {appointment_details.get('date', 'TBD')}
        Time: {appointment_details.get('time', 'TBD')}
        Doctor: {appointment_details.get('doctor_name', 'TBD')}
        Location: {appointment_details.get('location', 'TBD')}
        {f'Reason: {appointment_details.get("reason")}' if appointment_details.get('reason') else ''}
        
        If you have any questions, please contact us.
        
        Best regards,
        The MediRemind Team
        """
        
        tags = {
            'type': f'appointment_{update_type.lower()}',
            'patient_id': str(appointment_details.get('patient_id', '')),
            'appointment_id': str(appointment_details.get('id', '')),
            'recipient_type': 'patient' if is_patient else 'doctor'
        }
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags=tags
        )
    
    def send_welcome_email(
        self,
        to_email: str,
        patient_name: str,
        clinic_name: str = "MediRemind",
        from_email: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Send welcome email to new patients using TemplateManager
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            clinic_name: Clinic name (default: MediRemind)
            from_email: Optional custom from email address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Prepare template data
            template_data = {
                'clinic_name': clinic_name,
                'patient_name': patient_name,
                'features': [
                    'Schedule and manage appointments',
                    'Set up medication reminders',
                    'Receive notifications on your preferred channels',
                    'Secure access to your health information'
                ]
            }
            
            # Render template using TemplateManager
            subject, html_content = self.render_template(
                template_type=TemplateType.WELCOME,
                recipient_name=patient_name,
                recipient_email=to_email,
                template_data=template_data,
                recipient_type=RecipientType.PATIENT
            )
            
            # Send email with Resend
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                tags={
                    'type': 'welcome_email',
                    'clinic_name': clinic_name,
                    'patient_email': to_email
                },
                from_email=from_email
            )
            
        except Exception as e:
            error_msg = f"Failed to send welcome email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_appointment_update_email(
        self,
        to_email: str,
        patient_name: str,
        appointment_details: Dict,
        update_type: str = 'rescheduled',
        from_email: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Send appointment update email (rescheduled or cancelled) using TemplateManager
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            appointment_details: Dictionary with appointment information
            update_type: Type of update ('rescheduled' or 'cancelled')
            from_email: Optional custom from email address
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Determine template type based on update type
            template_type = (
                TemplateType.APPOINTMENT_RESCHEDULE if update_type.lower() == 'rescheduled'
                else TemplateType.APPOINTMENT_CANCELLATION
            )
            
            # Prepare template data
            template_data = {
                'appointment': appointment_details,
                'patient_name': patient_name,
                'update_type': update_type.lower(),
                'date': appointment_details.get('date'),
                'time': appointment_details.get('time'),
                'doctor_name': appointment_details.get('doctor_name'),
                'location': appointment_details.get('location'),
                'appointment_type': appointment_details.get('appointment_type', 'Consultation')
            }
            
            # Render template using TemplateManager
            subject, html_content = self.render_template(
                template_type=template_type,
                recipient_name=patient_name,
                recipient_email=to_email,
                template_data=template_data,
                recipient_type=RecipientType.PATIENT
            )
            
            # Send email with Resend
            return self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                tags={
                    'type': f'appointment_{update_type.lower()}',
                    'appointment_id': str(appointment_details.get('id', '')),
                    'patient_email': to_email,
                    'update_type': update_type.lower()
                },
                from_email=from_email
            )
            
        except Exception as e:
            error_msg = f"Failed to send appointment update email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

# Global instance
resend_service = ResendEmailService()