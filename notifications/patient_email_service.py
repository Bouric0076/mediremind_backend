"""
Patient Email Service for Account Creation and Management
Handles sending welcome emails, login credentials, and account-related notifications to patients.
"""

import logging
from typing import Optional, Dict, Any
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from .email_client import email_client
from accounts.models import EnhancedPatient

logger = logging.getLogger(__name__)


class PatientEmailService:
    """Service for handling patient account-related email communications."""
    
    def __init__(self):
        self.email_client = email_client
        
    def send_welcome_email_with_credentials(
        self, 
        patient: EnhancedPatient, 
        temporary_password: Optional[str] = None
    ) -> bool:
        """
        Send welcome email to patient with login credentials.
        
        Args:
            patient: The EnhancedPatient instance
            temporary_password: The temporary password for the patient's account
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            if not patient.user or not patient.user.email:
                logger.error(f"Patient {patient.id} has no user account or email address")
                return False
                
            # Prepare template context
            context = self._prepare_welcome_context_with_credentials(patient, temporary_password)
            
            # Render email template
            html_content = render_to_string(
                'notifications/email/patient_welcome_with_credentials.html',
                context
            )
            
            # Send email
            success = self.email_client.send_email(
                to_email=patient.user.email,
                subject=f"Welcome to MediRemind - Your Account is Ready!",
                html_content=html_content,
                from_name="MediRemind Team",
                reply_to=self._get_hospital_email(patient)
            )
            
            if success:
                logger.info(f"Welcome email with credentials sent to {patient.user.email}")
            else:
                logger.error(f"Failed to send welcome email with credentials to {patient.user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending welcome email with credentials to patient {patient.id}: {str(e)}")
            return False
    
    def send_welcome_email_no_credentials(self, patient: EnhancedPatient) -> bool:
        """
        Send welcome email to patient without login credentials (for patients without user accounts).
        
        Args:
            patient: The EnhancedPatient instance
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            if not patient.email:
                logger.error(f"Patient {patient.id} has no email address")
                return False
                
            # Prepare template context
            context = self._prepare_welcome_context_no_credentials(patient)
            
            # Render email template
            html_content = render_to_string(
                'notifications/email/patient_welcome_no_credentials.html',
                context
            )
            
            # Send email
            success = self.email_client.send_email(
                to_email=patient.email,
                subject=f"Welcome to MediRemind - You're All Set!",
                html_content=html_content,
                from_name="MediRemind Team",
                reply_to=self._get_hospital_email(patient)
            )
            
            if success:
                logger.info(f"Welcome email (no credentials) sent to {patient.email}")
            else:
                logger.error(f"Failed to send welcome email (no credentials) to {patient.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending welcome email (no credentials) to patient {patient.id}: {str(e)}")
            return False
    
    def send_account_activation_email(
        self, 
        patient: EnhancedPatient, 
        temporary_password: Optional[str] = None
    ) -> bool:
        """
        Send account activation email when a user account is created for an existing patient.
        
        Args:
            patient: The EnhancedPatient instance
            temporary_password: The temporary password for the patient's account
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            if not patient.user or not patient.user.email:
                logger.error(f"Patient {patient.id} has no user account or email address")
                return False
                
            # Prepare template context (similar to welcome with credentials)
            context = self._prepare_welcome_context_with_credentials(patient, temporary_password)
            context.update({
                'is_activation': True,
                'activation_message': 'Your online account has been activated!'
            })
            
            # Render email template
            html_content = render_to_string(
                'notifications/email/patient_welcome_with_credentials.html',
                context
            )
            
            # Send email
            success = self.email_client.send_email(
                to_email=patient.user.email,
                subject=f"Your MediRemind Account is Now Active! 🔓",
                html_content=html_content,
                from_name="MediRemind Team",
                reply_to=self._get_hospital_email(patient)
            )
            
            if success:
                logger.info(f"Account activation email sent to {patient.user.email}")
            else:
                logger.error(f"Failed to send account activation email to {patient.user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending account activation email to patient {patient.id}: {str(e)}")
            return False
    
    def send_password_reset_email(self, patient: EnhancedPatient, reset_token: str) -> bool:
        """
        Send password reset email to patient.
        
        Args:
            patient: The EnhancedPatient instance
            reset_token: The password reset token
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            if not patient.user or not patient.user.email:
                logger.error(f"Patient {patient.id} has no user account or email address")
                return False
                
            # Prepare reset URL
            reset_url = self._build_reset_url(reset_token)
            
            # Prepare template context
            context = {
                'patient_name': patient.user.get_full_name() or 'Patient',
                'hospital_name': patient.hospital.name if patient.hospital else 'Your Healthcare Provider',
                'reset_url': reset_url,
                'reset_token': reset_token,
                'expiry_hours': 24,  # Token expires in 24 hours
                'support_url': self._get_support_url(),
                'privacy_url': self._get_privacy_url(),
                'current_year': timezone.now().year
            }
            
            # For now, use the welcome template as base (you can create a dedicated reset template later)
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Password Reset Request</h2>
                <p>Hello {context['patient_name']},</p>
                <p>You requested a password reset for your MediRemind account. Click the link below to reset your password:</p>
                <p><a href="{reset_url}" style="background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Reset Password</a></p>
                <p>This link will expire in {context['expiry_hours']} hours.</p>
                <p>If you didn't request this reset, please ignore this email.</p>
                <p>Best regards,<br>The MediRemind Team</p>
            </div>
            """
            
            # Send email
            success = self.email_client.send_email(
                to_email=patient.user.email,
                subject=f"Reset Your MediRemind Password 🔑",
                html_content=html_content,
                from_name="MediRemind Team",
                reply_to=self._get_hospital_email(patient)
            )
            
            if success:
                logger.info(f"Password reset email sent to {patient.user.email}")
            else:
                logger.error(f"Failed to send password reset email to {patient.user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending password reset email to patient {patient.id}: {str(e)}")
            return False
    
    def _prepare_welcome_context_with_credentials(
        self, 
        patient: EnhancedPatient, 
        temporary_password: Optional[str]
    ) -> Dict[str, Any]:
        """Prepare template context for welcome email with credentials."""
        # Get hospital from patient's hospital relationships
        hospital = self._get_patient_hospital(patient)
        
        return {
            'patient_name': patient.user.full_name or 'Patient',
            'first_name': patient.user.full_name.split(' ')[0] if patient.user.full_name else 'Patient',
            'last_name': ' '.join(patient.user.full_name.split(' ')[1:]) if patient.user.full_name and ' ' in patient.user.full_name else '',
            'patient_email': patient.user.email,
            'temporary_password': temporary_password or '(Please contact support)',
            'hospital_name': hospital.name if hospital else 'Your Healthcare Provider',
            'patient_id': str(patient.id),
            'registration_date': patient.created_at.strftime('%B %d, %Y'),
            'primary_doctor': self._get_primary_doctor_name(patient),
            'mobile_app_url': self._get_mobile_app_url(),
            'support_url': self._get_support_url(),
            'privacy_url': self._get_privacy_url(),
            'current_year': timezone.now().year,
            'hospital_phone': self._get_hospital_phone(hospital),
            'hospital_email': self._get_hospital_email(hospital),
            'hospital_website': self._get_hospital_website(hospital),
            'hospital_address': self._get_hospital_address(hospital)
        }
    
    def _prepare_welcome_context_no_credentials(self, patient: EnhancedPatient) -> Dict[str, Any]:
        """Prepare template context for welcome email without credentials."""
        # Get hospital from patient's hospital relationships
        hospital = self._get_patient_hospital(patient)
        
        return {
            'patient_name': patient.user.full_name or 'Patient',
            'first_name': patient.user.full_name.split(' ')[0] if patient.user.full_name else 'Patient',
            'last_name': ' '.join(patient.user.full_name.split(' ')[1:]) if patient.user.full_name and ' ' in patient.user.full_name else '',
            'hospital_name': hospital.name if hospital else 'Your Healthcare Provider',
            'patient_id': str(patient.id),
            'registration_date': patient.created_at.strftime('%B %d, %Y'),
            'primary_doctor': self._get_primary_doctor_name(patient),
            'support_url': self._get_support_url(),
            'privacy_url': self._get_privacy_url(),
            'current_year': timezone.now().year,
            'hospital_phone': self._get_hospital_phone(hospital),
            'hospital_email': self._get_hospital_email(hospital),
            'hospital_website': self._get_hospital_website(hospital),
            'hospital_address': self._get_hospital_address(hospital)
        }
    
    def _get_patient_hospital(self, patient: EnhancedPatient):
        """Get the hospital associated with the patient."""
        try:
            # Get the active hospital relationship for this patient
            from accounts.models import HospitalPatient
            hospital_patient = HospitalPatient.objects.filter(
                patient=patient,
                status='active'
            ).select_related('hospital').first()
            
            if hospital_patient:
                return hospital_patient.hospital
            return None
        except Exception:
            return None
    
    def _get_primary_doctor_name(self, patient: EnhancedPatient) -> Optional[str]:
        """Get the primary doctor's name for the patient."""
        try:
            if patient.primary_care_physician:
                return patient.primary_care_physician.user.full_name
            return None
        except Exception:
            return None
    
    def _get_hospital_phone(self, hospital) -> Optional[str]:
        """Get hospital phone number."""
        if hospital and hasattr(hospital, 'phone'):
            return hospital.phone
        return None
    
    def _get_hospital_email(self, hospital) -> Optional[str]:
        """Get hospital email address."""
        if hospital and hasattr(hospital, 'email'):
            return hospital.email
        return getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@mediremind.com')
    
    def _get_hospital_website(self, hospital) -> Optional[str]:
        """Get hospital website URL."""
        if hospital and hasattr(hospital, 'website'):
            return hospital.website
        return None
    
    def _get_hospital_address(self, hospital) -> Optional[str]:
        """Get hospital address."""
        if hospital and hasattr(hospital, 'full_address'):
            return hospital.full_address
        return None
    
    def _get_mobile_app_url(self) -> str:
        """Get the mobile app download URL."""
        try:
            return getattr(settings, 'PATIENT_NOTIFICATION_SETTINGS', {}).get(
                'PATIENT_PORTAL_URL', 
                'https://app.mediremind.com'
            )
        except Exception:
            return 'https://app.mediremind.com'
    
    def _get_support_url(self) -> str:
        """Get the support URL."""
        try:
            return getattr(settings, 'SUPPORT_URL', 'https://mediremind.com/support')
        except Exception:
            return '#'
    
    def _get_privacy_url(self) -> str:
        """Get the privacy policy URL."""
        try:
            return getattr(settings, 'PRIVACY_URL', 'https://mediremind.com/privacy')
        except Exception:
            return '#'

    def send_emergency_contact_notification(self, patient: EnhancedPatient) -> bool:
        """
        Send notification email to emergency contact when they are added to a patient's profile.
        
        Args:
            patient: The EnhancedPatient instance
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Check if emergency contact email is available
            if not patient.emergency_contact_email:
                logger.warning(f"No emergency contact email for patient {patient.id}")
                return False
            
            # Check if emergency contact notifications are enabled
            if not patient.notify_emergency_contact:
                logger.info(f"Emergency contact notifications disabled for patient {patient.id}")
                return False
            
            # Check if this notification type is enabled
            notification_types = patient.emergency_contact_notification_types or []
            if 'emergency_contact_added' not in notification_types:
                logger.info(f"Emergency contact added notifications not enabled for patient {patient.id}")
                return False
            
            # Check if email is a preferred notification method
            notification_methods = patient.emergency_contact_notification_methods or []
            if 'email' not in notification_methods:
                logger.info(f"Email notifications not enabled for emergency contact of patient {patient.id}")
                return False
            
            # Prepare email context
            context = self._prepare_emergency_contact_context(patient)
            
            # Render email template
            html_content = render_to_string(
                'notifications/email/emergency_contact_notification.html',
                context
            )
            
            # Send email
            subject = f"You've been added as an emergency contact for {context['patient_name']}"
            
            success, error_msg = self.email_client.send_email(
                subject=subject,
                message=strip_tags(html_content),
                recipient_list=[patient.emergency_contact_email],
                html_message=html_content
            )
            
            if success:
                logger.info(f"Emergency contact notification sent successfully for patient {patient.id}")
                return True
            else:
                logger.error(f"Failed to send emergency contact notification for patient {patient.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending emergency contact notification for patient {patient.id}: {str(e)}")
            return False

    def _prepare_emergency_contact_context(self, patient: EnhancedPatient) -> Dict[str, Any]:
        """Prepare template context for emergency contact notification email."""
        # Get hospital from patient's hospital relationships
        hospital = self._get_patient_hospital(patient)
        
        return {
            'emergency_contact_name': patient.emergency_contact_name or 'Emergency Contact',
            'patient_name': patient.user.full_name or 'Patient',
            'patient_first_name': patient.user.full_name.split(' ')[0] if patient.user.full_name else 'Patient',
            'patient_last_name': ' '.join(patient.user.full_name.split(' ')[1:]) if patient.user.full_name and ' ' in patient.user.full_name else '',
            'patient_id': str(patient.id),
            'emergency_contact_relationship': patient.emergency_contact_relationship or 'Emergency Contact',
            'hospital_name': hospital.name if hospital else 'Healthcare Provider',
            'hospital_phone': self._get_hospital_phone(hospital),
            'hospital_email': self._get_hospital_email(hospital),
            'hospital_website': self._get_hospital_website(hospital),
            'hospital_address': self._get_hospital_address(hospital),
            'primary_doctor': self._get_primary_doctor_name(patient),
            'registration_date': patient.created_at.strftime('%B %d, %Y'),
            'support_url': self._get_support_url(),
            'privacy_url': self._get_privacy_url(),
            'current_year': timezone.now().year,
        }
    
    def _build_reset_url(self, reset_token: str) -> str:
        """Build password reset URL."""
        base_url = getattr(settings, 'PATIENT_PORTAL_URL', 'https://app.mediremind.com')
        return f"{base_url}/reset-password?token={reset_token}"