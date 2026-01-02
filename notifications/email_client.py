from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import json
import ssl
import certifi
import os
import socket
from .template_manager import (
    template_manager, 
    TemplateContext, 
    RecipientType, 
    TemplateType
)


logger = logging.getLogger(__name__)

class EmailClient:
    """Client for handling email notifications"""
    
    @staticmethod
    def send_email(subject, message, recipient_list, html_message=None):
        """Send an email to the specified recipients"""
        try:
            # Check if using console backend (for development)
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                # For console backend, we don't need SMTP credentials
                logger.info("Using console email backend - emails will be printed to console")
            elif not all([settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD]):
                logger.warning("Email settings not configured")
                return False, "Email settings not configured"

            if not recipient_list:
                return False, "No recipients specified"

            # If no HTML message provided, create a simple HTML version
            if not html_message:
                html_message = f"<p>{message}</p>"

            # Handle different email backends
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                # For console backend, use default Django send_mail
                logger.info("Using console email backend - skipping SMTP configuration")
                email_backend = None
            else:
                # For SMTP backends, configure properly
                # Log SSL certificate path
                cert_path = certifi.where()
                logger.info(f"Using SSL certificates from: {cert_path}")
                
                # Log email settings (excluding password)
                logger.info(f"Email settings: host={settings.EMAIL_HOST}, port={settings.EMAIL_PORT}, "
                           f"use_tls={settings.EMAIL_USE_TLS}, use_ssl={settings.EMAIL_USE_SSL}")

                # Skip network connectivity test for Render environment (causes timeout)
                if os.getenv('RENDER', 'false').lower() != 'true':
                    # Test network connectivity before attempting to send (only in non-Render environments)
                    try:
                        # Test DNS resolution
                        socket.gethostbyname(settings.EMAIL_HOST)
                        logger.info(f"DNS resolution successful for {settings.EMAIL_HOST}")
                        
                        # Test port connectivity
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(5)  # Reduced timeout to 5 seconds
                        result = sock.connect_ex((settings.EMAIL_HOST, settings.EMAIL_PORT))
                        sock.close()
                        
                        if result != 0:
                            error_msg = f"Cannot connect to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}. Network may be restricted."
                            logger.error(error_msg)
                            return False, error_msg
                        else:
                            logger.info(f"Port connectivity test successful for {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
                            
                    except socket.gaierror as e:
                        error_msg = f"DNS resolution failed for {settings.EMAIL_HOST}: {str(e)}"
                        logger.error(error_msg)
                        return False, error_msg
                    except Exception as e:
                        error_msg = f"Network connectivity test failed: {str(e)}"
                        logger.error(error_msg)
                        return False, error_msg
                else:
                    logger.info("Running on Render - skipping network connectivity test to avoid timeout")

                # Configure email settings with improved error handling
                from django.core.mail.backends.smtp import EmailBackend
                
                # Create SSL context with better error handling
                ssl_context = ssl.create_default_context(cafile=cert_path)
                
                # For production environments with strict network policies,
                # we may need to be more permissive with SSL verification
                if os.getenv('EMAIL_SSL_PERMISSIVE', 'False').lower() == 'true':
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    logger.warning("Using permissive SSL context - not recommended for production")

                # Reduced timeout for Render environment - use very short timeout to prevent worker hangs
                email_timeout = 5 if os.getenv('RENDER', 'false').lower() == 'true' else getattr(settings, 'EMAIL_TIMEOUT', 30)
                
                email_backend = EmailBackend(
                    host=settings.EMAIL_HOST,
                    port=settings.EMAIL_PORT,
                    username=settings.EMAIL_HOST_USER,
                    password=settings.EMAIL_HOST_PASSWORD,
                    use_tls=settings.EMAIL_USE_TLS,
                    use_ssl=settings.EMAIL_USE_SSL,
                    timeout=email_timeout,
                    ssl_context=ssl_context
                )

            send_mail(
                subject=subject,
                message=strip_tags(html_message),  # Plain text version
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
                connection=email_backend
            )
            
            logger.info(f"Email sent successfully to {recipient_list}")
            return True, "Email sent successfully"

        except socket.timeout as e:
            error_msg = f"Email sending timeout: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except socket.error as e:
            error_msg = f"Network error sending email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except ssl.SSLError as e:
            error_msg = f"SSL error sending email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    
    import json
# ...existing code...

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
            subject, html_message = template_manager.render_template(template_key, context)
            
            return EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )

        except Exception as e:
            logger.error(f"Error sending appointment confirmation email: {str(e)}")
            return False, str(e)
    
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

            if is_patient:
                subject = "Appointment Confirmation - MediRemind"
                template = "notifications/email/appointment_confirmation_patient.html"
            else:
                subject = "New Appointment Request - MediRemind"
                template = "notifications/email/appointment_confirmation_doctor.html"

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
            logger.error(f"Error sending appointment confirmation email: {str(e)}")
            return False, str(e)

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
            if update_type == "reschedule":
                template_key = "appointment_reschedule_patient" if is_patient else "appointment_reschedule_doctor"
            elif update_type == "cancellation":
                template_key = "appointment_cancellation_patient" if is_patient else "appointment_cancellation_doctor"
            elif update_type == "created":
                template_key = "appointment_confirmation_patient" if is_patient else "appointment_confirmation_doctor"
            else:
                logger.error(f"Invalid update_type: {update_type}")
                return False, "Invalid update type"

            # Create enhanced template context
            context = TemplateContext(
                recipient_name=appointment_data.get('patient_name' if is_patient else 'doctor_name', 'there'),
                recipient_email=recipient_email,
                recipient_type=RecipientType.PATIENT if is_patient else RecipientType.DOCTOR,
                appointment=appointment_data,
                preferences=user_preferences or {},
                links=additional_links or {}
            )
            
            # Add update_type to metadata for template access
            context.metadata['update_type'] = update_type
            
            # Render template with enhanced features
            subject, html_message = template_manager.render_template(template_key, context)

            return EmailClient.send_email(
                subject=subject,
                message=strip_tags(html_message),
                recipient_list=[recipient_email],
                html_message=html_message
            )

        except Exception as e:
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
            logger.error(f"Error sending appointment update email: {str(e)}")
            return False, str(e)

# Create a singleton instance
email_client = EmailClient()