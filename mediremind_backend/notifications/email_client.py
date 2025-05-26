from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import json
import ssl
import certifi
import os


logger = logging.getLogger(__name__)

class EmailClient:
    """Client for handling email notifications"""
    
    @staticmethod
    def send_email(subject, message, recipient_list, html_message=None):
        """Send an email to the specified recipients"""
        try:
            if not all([settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD]):
                logger.warning("Email settings not configured")
                return False, "Email settings not configured"

            if not recipient_list:
                return False, "No recipients specified"

            # If no HTML message provided, create a simple HTML version
            if not html_message:
                html_message = f"<p>{message}</p>"

            # Log SSL certificate path
            cert_path = certifi.where()
            logger.debug(f"Using SSL certificates from: {cert_path}")
            if not os.path.exists(cert_path):
                logger.error(f"SSL certificate file not found at: {cert_path}")

            # Create a more specific SSL context for Gmail
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.check_hostname = True
            ssl_context.load_verify_locations(cafile=cert_path)
            ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')  # Allow more permissive ciphers

            # Log email settings (excluding password)
            logger.debug(f"Email settings: host={settings.EMAIL_HOST}, port={settings.EMAIL_PORT}, "
                        f"use_tls={settings.EMAIL_USE_TLS}, use_ssl={settings.EMAIL_USE_SSL}")

            # Configure email settings
            from django.core.mail.backends.smtp import EmailBackend
            email_backend = EmailBackend(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                use_ssl=settings.EMAIL_USE_SSL,
                timeout=settings.EMAIL_TIMEOUT,
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
            return True, "Email sent successfully"

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False, str(e)

    
    import json
# ...existing code...

    @staticmethod
    def send_appointment_confirmation_email(appointment_data, recipient_email, is_patient=True):
        """Send appointment confirmation email"""
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
    def send_appointment_update_email(appointment_data, update_type, recipient_email, is_patient=True):
        """Send appointment update email"""
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