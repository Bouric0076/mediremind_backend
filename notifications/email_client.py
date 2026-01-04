"""
Unified Email Client using Resend API for both development and production.
This service provides consistent email sending with TemplateManager integration.
"""
import logging
import os
import hashlib
import json
from typing import Dict, Optional, Tuple, Any, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import resend
from django.utils.html import strip_tags
from django.template.loader import render_to_string

from .template_manager import (
    template_manager, 
    TemplateContext, 
    RecipientType,
    TemplateType
)
from .error_handler import notification_error_handler, ErrorContext, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)

class EmailClient:
    """Unified email client using Resend API with TemplateManager integration"""
    
    def __init__(self):
        """Initialize with Resend API key and deduplication cache"""
        self.api_key = os.getenv('RESEND_API_KEY')
        self.from_email = os.getenv('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
        self.from_name = os.getenv('RESEND_FROM_NAME', 'MediRemind')
        self.deduplication_ttl = int(os.getenv('EMAIL_DEDUPLICATION_TTL', '86400'))  # 24 hours default
        
        if self.api_key:
            resend.api_key = self.api_key
            self.service = resend  # Add service attribute for compatibility
            logger.info("Resend email service initialized with idempotency")
        else:
            self.service = None  # No service in development mode
            logger.warning("RESEND_API_KEY not configured - using console backend for development")
    
    def _generate_message_id(self, to_email: str, subject: str, content_hash: str, tags: Dict[str, str] = None) -> str:
        """Generate a unique message ID for deduplication"""
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

    @staticmethod
    def send_email(subject: str, message: str, recipient_list: List[str], html_message: str = None) -> Tuple[bool, str]:
        """
        Unified email sending method that uses Resend API in production 
        and console backend in development
        """
        try:
            client = EmailClient()
            
            # In development without Resend API key, use console backend
            if not client.api_key and settings.DEBUG:
                logger.info("Using console email backend for development")
                from django.core.mail import send_mail as django_send_mail
                
                if not recipient_list:
                    return False, "No recipients specified"

                # Use Django's console backend for development
                django_send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_list,
                    html_message=html_message,
                    fail_silently=False
                )
                
                logger.info(f"Email sent to console backend: {recipient_list}")
                return True, "Email sent to console backend"
            
            # Use Resend API for production or when API key is available
            return client._send_resend_email(
                to_email=recipient_list[0] if recipient_list else None,
                subject=subject,
                html_content=html_message or f"<p>{message}</p>",
                text_content=message
            )
            
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _send_resend_email(
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
        """Send email using Resend API with optional idempotency"""
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

    
    

    @staticmethod
    def send_appointment_confirmation_email(appointment_data, recipient_email, is_patient=True, 
                                          user_preferences=None, additional_links=None):
        """Send enhanced appointment confirmation email with personalization"""
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
            template_key = "appointment_confirmation_patient" if is_patient else "appointment_confirmation_doctor"
            
            # Create enhanced template context with properly structured appointment data
            # Build nested appointment structure that matches template expectations
            structured_appointment = {
                'id': appointment_data.get('id'),
                'appointment_date': appointment_data.get('appointment_date'),
                'start_time': appointment_data.get('start_time'),
                'duration': appointment_data.get('duration', 30),
                'status': appointment_data.get('status', 'created'),
                'patient': {
                    'name': appointment_data.get('patient', {}).get('name') or appointment_data.get('patient_name', 'Patient'),
                    'email': appointment_data.get('patient', {}).get('email') or appointment_data.get('patient_email'),
                    'id': appointment_data.get('patient', {}).get('id') or appointment_data.get('patient_id')
                },
                'provider': {
                    'name': appointment_data.get('provider', {}).get('name') or appointment_data.get('provider_name', 'Dr. Smith'),
                    'email': appointment_data.get('provider', {}).get('email') or appointment_data.get('provider_email'),
                    'id': appointment_data.get('provider', {}).get('id') or appointment_data.get('provider_id')
                },
                'appointment_type': {
                    'name': appointment_data.get('appointment_type', {}).get('name') or appointment_data.get('appointment_type_name', 'Consultation')
                },
                'hospital': {
                    'name': appointment_data.get('hospital', {}).get('name') or appointment_data.get('hospital_name', 'MediRemind Partner Clinic')
                },
                'room': {
                    'name': appointment_data.get('room', {}).get('name') or appointment_data.get('room_name', 'Room 1')
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
            result = EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )
            logger.info(f"send_email returned: {result}, type: {type(result)}")
            return result

        except Exception as e:
            error_context = notification_error_handler.handle_email_error(
                error=e,
                context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email},
                email_data={'subject': subject, 'html_message': html_message}
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
            
            # Create enhanced template context
            context = TemplateContext(
                recipient_name=appointment_data.get('patient_name' if is_patient else 'doctor_name', 'there'),
                recipient_email=recipient_email,
                recipient_type=RecipientType.PATIENT if is_patient else RecipientType.DOCTOR,
                appointment=appointment_data,
                preferences=user_preferences or {},
                links=additional_links or {}
            )
            
            # Render template with enhanced features
            logger.info(f"Rendering appointment creation template with key: {template_key}")
            try:
                success, subject, html_message = template_manager.render_template_with_fallback(template_key, context)
                if not success:
                    error_context = notification_error_handler.handle_template_error(
                        template_key=template_key,
                        error=Exception(html_message),
                        context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email}
                    )
                    return False, f"Template rendering failed: {html_message}"
                logger.info(f"Appointment creation template rendered, subject: {subject}")
            except Exception as e:
                error_context = notification_error_handler.handle_template_error(
                    template_key=template_key,
                    error=e,
                    context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email}
                )
                return False, f"Template rendering failed: {str(e)}"

            return EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )

        except Exception as e:
            error_context = notification_error_handler.handle_email_error(
                error=e,
                context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email},
                email_data={'subject': subject, 'html_message': html_message}
            )
            logger.error(f"Error sending appointment confirmation email: {str(e)}")
            return False, str(e)

    def send_appointment_creation_email(appointment_data, recipient_email, is_patient=True, 
                                      user_preferences=None, additional_links=None):
        """Send enhanced appointment creation email with personalization"""
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
            
            # Create enhanced template context
            context = TemplateContext(
                recipient_name=appointment_data.get('patient_name' if is_patient else 'doctor_name', 'there'),
                recipient_email=recipient_email,
                recipient_type=RecipientType.PATIENT if is_patient else RecipientType.DOCTOR,
                appointment=appointment_data,
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
            
            logger.info(f"About to call send_email from send_appointment_creation_email")
            result = EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )
            logger.info(f"send_email returned: {result}, type: {type(result)}")
            return result

        except Exception as e:
            error_context = notification_error_handler.handle_email_error(
                error=e,
                context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email},
                email_data={'subject': subject, 'html_message': html_message}
            )
            error_msg = f"Error in send_appointment_creation_email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def send_appointment_update_email(appointment_data, update_type, recipient_email, is_patient=True,
                                    user_preferences=None, additional_links=None):
        """Send enhanced appointment update email (reschedule/cancellation) with personalization"""
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

            # Determine template key based on update type and recipient
            logger.info(f"Determining template for update_type: {update_type}, is_patient: {is_patient}")
            if update_type == "reschedule":
                template_key = "appointment_reschedule_patient" if is_patient else "appointment_reschedule_doctor"
            elif update_type == "cancellation":
                template_key = "appointment_cancellation_patient" if is_patient else "appointment_cancellation_doctor"
            elif update_type == "no-show":
                template_key = "appointment_no_show_patient" if is_patient else "appointment_no_show_emergency"
            elif update_type == "created":
                template_key = "appointment_confirmation_patient" if is_patient else "appointment_confirmation_doctor"
            else:
                logger.error(f"Invalid update_type: {update_type}")
                return False, "Invalid update type"
            logger.info(f"Selected template key: {template_key}")

            # Create enhanced template context with properly structured appointment data
            logger.info(f"Creating template context with appointment_data: {appointment_data}")
            
            # Build properly structured appointment object that matches API format
            structured_appointment = {
                'id': appointment_data.get('id'),
                'appointment_date': appointment_data.get('appointment_date'),
                'start_time': appointment_data.get('start_time'),
                'duration': appointment_data.get('duration', 30),
                'notes': appointment_data.get('notes', ''),
                'location': appointment_data.get('location', ''),
                'patient_name': appointment_data.get('patient_name'),
                'provider_name': appointment_data.get('provider_name'),
                'appointment_type': {
                    'name': appointment_data.get('appointment_type_name', appointment_data.get('appointment_type', ''))
                },
                'provider': {
                    'user': {
                        'full_name': appointment_data.get('provider_name', ''),
                        'first_name': appointment_data.get('provider_name', '').split()[0] if appointment_data.get('provider_name') else '',
                        'last_name': ' '.join(appointment_data.get('provider_name', '').split()[1:]) if appointment_data.get('provider_name') and len(appointment_data.get('provider_name', '').split()) > 1 else '',
                        'email': appointment_data.get('provider_email', '')
                    },
                    'specialization': appointment_data.get('specialty', ''),
                    'department': appointment_data.get('department', ''),
                    'hospital': {
                        'name': appointment_data.get('hospital_name', ''),
                        'hospital_type': appointment_data.get('hospital_type', ''),
                        'address_line_1': appointment_data.get('hospital_address', '').split(',')[0] if appointment_data.get('hospital_address') else '',
                        'city': appointment_data.get('hospital_address', '').split(',')[1].strip() if appointment_data.get('hospital_address') and ',' in appointment_data.get('hospital_address') else '',
                        'phone': appointment_data.get('hospital_phone', '')
                    }
                },
                'patient': {
                    'user': {
                        'full_name': appointment_data.get('patient_name', ''),
                        'first_name': appointment_data.get('patient_name', '').split()[0] if appointment_data.get('patient_name') else '',
                        'last_name': ' '.join(appointment_data.get('patient_name', '').split()[1:]) if appointment_data.get('patient_name') and len(appointment_data.get('patient_name', '').split()) > 1 else '',
                        'email': appointment_data.get('patient_email', '')
                    }
                }
            }
            
            context = TemplateContext(
                recipient_name=appointment_data.get('patient_name' if is_patient else 'doctor_name', 'there'),
                recipient_email=recipient_email,
                recipient_type=RecipientType.PATIENT if is_patient else RecipientType.DOCTOR,
                appointment=structured_appointment,
                preferences=user_preferences or {},
                links=additional_links or {}
            )
            
            # Add update_type to metadata for template access
            context.metadata['update_type'] = update_type
            logger.info(f"Template context created: {context}")
            
            # Debug: Check if we can access the context attributes
            logger.info(f"Context recipient_name: {context.recipient_name}")
            logger.info(f"Context appointment: {context.appointment}")
            
            # Render template with enhanced features
            logger.info(f"About to render template with key: {template_key}")
            try:
                success, subject, html_message = template_manager.render_template_with_fallback(template_key, context)
                if not success:
                    error_context = notification_error_handler.handle_template_error(
                        template_key=template_key,
                        error=Exception(html_message),
                        context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email, 'update_type': update_type}
                    )
                    return False, f"Template rendering failed: {html_message}"
                logger.info(f"Template rendered successfully, subject: {subject}")
            except Exception as e:
                error_context = notification_error_handler.handle_template_error(
                    template_key=template_key,
                    error=e,
                    context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email, 'update_type': update_type}
                )
                logger.error(f"Error rendering template: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return False, f"Template rendering error: {str(e)}"

            # Send email and return the result tuple
            logger.info(f"About to send email with subject: {subject}")
            result = EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )
            logger.info(f"Email send result: {result}, type: {type(result)}")
            return result

        except Exception as e:
            error_context = notification_error_handler.handle_email_error(
                error=e,
                context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email, 'update_type': update_type},
                email_data={'subject': subject, 'html_message': html_message}
            )
            logger.error(f"Error sending appointment update email: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def send_appointment_update_email_legacy(appointment_data, update_type, recipient_email, is_patient=True):
        """Legacy method for backward compatibility"""
        try:
            # Ensure appointment_data is a dict
            if isinstance(appointment_data, str):
                try:
                    appointment_data = json.loads(appointment_data)
                except Exception:
                    logger.error("appointment_data is a string but not valid JSON")
                    return False, "Invalid appointment data format"

            templates = {
                'reschedule': {
                    'patient': "notifications/email/appointment_reschedule_patient.html",
                    'doctor': "notifications/email/appointment_reschedule_doctor.html"
                },
                'cancellation': {
                    'patient': "notifications/email/appointment_cancellation_patient.html",
                    'doctor': "notifications/email/appointment_cancellation_doctor.html"
                }
            }

            if update_type not in templates:
                return False, f"Invalid update type: {update_type}"

            template = templates[update_type]['patient' if is_patient else 'doctor']
            subject = f"Appointment {update_type.title()} - MediRemind"

            html_message = render_to_string(template, {
                'appointment': appointment_data,
                'recipient_name': appointment_data.get('patient_name' if is_patient else 'doctor_name'),
            })

            return EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )

        except Exception as e:
            error_context = notification_error_handler.handle_email_error(
                error=e,
                context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email, 'update_type': update_type},
                email_data={'subject': subject, 'html_message': html_message}
            )
            logger.error(f"Error sending appointment update email: {str(e)}")
            return False, str(e)

    @staticmethod
    def send_appointment_reminder_email(appointment_data, recipient_email, is_patient=True):
        """Send appointment reminder email"""
        try:
            # Ensure appointment_data is a dict
            if isinstance(appointment_data, str):
                try:
                    appointment_data = json.loads(appointment_data)
                except Exception:
                    logger.error("appointment_data is a string but not valid JSON")
                    return False, "Invalid appointment data format"

            template = "notifications/email/appointment_reminder.html"
            subject = "Appointment Reminder - MediRemind"

            html_message = render_to_string(template, {
                'appointment': appointment_data,
                'recipient_name': appointment_data.get('patient_name' if is_patient else 'doctor_name'),
            })

            return EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )

        except Exception as e:
            error_context = notification_error_handler.handle_email_error(
                error=e,
                context_data={'appointment_id': appointment_data.get('id'), 'recipient_email': recipient_email},
                email_data={'subject': subject, 'html_message': html_message}
            )
            logger.error(f"Error sending appointment reminder email: {str(e)}")
            return False, str(e)

    @staticmethod
    def send_medication_reminder_email(patient_name, medication_name, dosage, scheduled_time, recipient_email):
        """Send medication reminder email"""
        try:
            template = "notifications/email/medication_reminder.html"
            subject = f"Medication Reminder: {medication_name}"

            html_message = render_to_string(template, {
                'patient_name': patient_name,
                'medication_name': medication_name,
                'dosage': dosage,
                'scheduled_time': scheduled_time,
            })

            return EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )

        except Exception as e:
            error_context = notification_error_handler.handle_email_error(
                error=e,
                context_data={'recipient_email': recipient_email, 'medication_name': medication_name},
                email_data={'subject': subject, 'html_message': html_message}
            )
            logger.error(f"Error sending medication reminder email: {str(e)}")
            return False, str(e)

    @staticmethod
    def send_emergency_alert_email(patient_name, alert_type, severity, message, recipient_email, location=None):
        """Send emergency alert email"""
        try:
            template = "notifications/email/emergency_alert.html"
            subject = f"EMERGENCY ALERT: {alert_type} - {severity.upper()}"

            html_message = render_to_string(template, {
                'patient_name': patient_name,
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                'location': location,
                'timestamp': timezone.now(),
            })

            return EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )

        except Exception as e:
            error_context = notification_error_handler.handle_email_error(
                error=e,
                context_data={'recipient_email': recipient_email, 'alert_type': alert_type, 'severity': severity},
                email_data={'subject': subject, 'html_message': html_message}
            )
            logger.error(f"Error sending emergency alert email: {str(e)}")
            return False, str(e)

    @staticmethod
    def send_welcome_email(patient_name, clinic_name, recipient_email):
        """Send welcome email"""
        try:
            template = "notifications/email/welcome.html"
            subject = f"Welcome to {clinic_name} - MediRemind"

            html_message = render_to_string(template, {
                'patient_name': patient_name,
                'clinic_name': clinic_name,
            })

            return EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )

        except Exception as e:
            error_context = notification_error_handler.handle_email_error(
                error=e,
                context_data={'recipient_email': recipient_email, 'patient_name': patient_name},
                email_data={'subject': subject, 'html_message': html_message}
            )
            logger.error(f"Error sending welcome email: {str(e)}")
            return False, str(e)

# Create a singleton instance
email_client = EmailClient()