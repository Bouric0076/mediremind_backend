"""
EmailService module for rendering and sending medication reminder emails.
Integrates TemplateManager to render templates and uses EmailClient
for SMTP delivery.
"""
import logging
from typing import Dict, Any, Optional
from django.utils.html import strip_tags

from .email_client import email_client
from .template_manager import template_manager, TemplateType

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        self.email_client = email_client

    async def send_medication_reminder(
        self,
        to_email: str,
        subject: Optional[str],
        template_data: Dict[str, Any]
    ) -> bool:
        """
        Send a medication reminder email.

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

            # Map incoming template_data to TemplateManager expected context
            context = {
                'recipient_name': template_data.get('user_name') or 'Patient',
                'medication': {
                    'name': template_data.get('medication_name') or '',
                    'dosage': template_data.get('dosage') or '',
                    'time': template_data.get('time') or ''
                },
                'links': {
                    'app_url': template_data.get('app_url')
                },
                'preferences': {},
                'metadata': {}
            }

            # Render subject and HTML content via TemplateManager
            rendered_subject, html_content = template_manager.render_template(
                TemplateType.MEDICATION_REMINDER,
                context
            )

            # Use provided subject if available, otherwise use rendered subject
            final_subject = subject or rendered_subject

            success, _message = self.email_client.send_email(
                subject=final_subject,
                message=strip_tags(html_content),
                recipient_list=[to_email],
                html_message=html_content
            )
            return bool(success)
        except Exception as e:
            logger.error(f"Error sending medication reminder email: {e}")
            return False