"""
Django signals for automatic patient account communication.
Handles lifecycle events to send welcome emails and notifications.
"""

import logging
import secrets
import string
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from .models import EnhancedPatient
from notifications.patient_email_service import PatientEmailService

logger = logging.getLogger(__name__)
User = get_user_model()


def generate_temporary_password(length=12):
    """Generate a secure temporary password for new patient accounts."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure password has at least one of each type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*")
    ]
    
    # Fill the rest randomly
    for _ in range(length - 4):
        password.append(secrets.choice(characters))
    
    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


@receiver(post_save, sender=EnhancedPatient)
def handle_patient_created(sender, instance, created, **kwargs):
    """
    Handle patient creation to automatically send welcome emails.
    
    Args:
        sender: The model class (EnhancedPatient)
        instance: The actual patient instance
        created: Boolean indicating if this is a new patient
        **kwargs: Additional keyword arguments
    """
    if not created:
        # Only handle new patient creation, not updates
        return
        
    try:
        logger.info(f"New patient created: {instance.id}. Processing welcome email.")
        
        # Initialize email service
        email_service = PatientEmailService()
        
        # Check if patient has an associated user account
        if hasattr(instance, 'user') and instance.user:
            # Patient has a user account - send credentials
            user = instance.user
            
            # Generate temporary password if user doesn't have a usable password
            temporary_password = None
            if not user.has_usable_password():
                temporary_password = generate_temporary_password()
                user.set_password(temporary_password)
                user.save(update_fields=['password'])
                logger.info(f"Generated temporary password for user {user.id}")
            
            # Send welcome email with credentials
            success = email_service.send_welcome_email_with_credentials(
                patient=instance,
                temporary_password=temporary_password
            )
            
            if success:
                logger.info(f"Welcome email with credentials sent to patient {instance.id}")
                
                # Log the email sending event
                from notifications.models import NotificationLog
                NotificationLog.objects.create(
                    recipient_type='patient',
                    recipient_id=str(instance.id),
                    notification_type='welcome_email_with_credentials',
                    channel='email',
                    status='sent',
                    sent_at=timezone.now(),
                    metadata={
                        'patient_email': user.email,
                        'hospital_id': str(instance.hospital.id) if instance.hospital else None,
                        'has_temporary_password': temporary_password is not None
                    }
                )
            else:
                logger.error(f"Failed to send welcome email with credentials to patient {instance.id}")
                
        else:
            # Patient doesn't have a user account - send registration confirmation
            success = email_service.send_welcome_email_no_credentials(
                patient=instance
            )
            
            if success:
                logger.info(f"Welcome email (no credentials) sent to patient {instance.id}")
                
                # Log the email sending event
                from notifications.models import NotificationLog
                NotificationLog.objects.create(
                    recipient_type='patient',
                    recipient_id=str(instance.id),
                    notification_type='welcome_email_no_credentials',
                    channel='email',
                    status='sent',
                    sent_at=timezone.now(),
                    metadata={
                        'patient_email': instance.email,
                        'hospital_id': str(instance.hospital.id) if instance.hospital else None,
                        'has_user_account': False
                    }
                )
            else:
                logger.error(f"Failed to send welcome email (no credentials) to patient {instance.id}")
                
    except Exception as e:
        logger.error(f"Error handling patient creation signal for {instance.id}: {str(e)}")
        
        # Log the error event
        try:
            from notifications.models import NotificationLog
            NotificationLog.objects.create(
                recipient_type='patient',
                recipient_id=str(instance.id),
                notification_type='welcome_email_error',
                channel='email',
                status='failed',
                sent_at=timezone.now(),
                error_message=str(e),
                metadata={
                    'error_type': type(e).__name__,
                    'hospital_id': str(instance.hospital.id) if instance.hospital else None
                }
            )
        except Exception as log_error:
            logger.error(f"Failed to log notification error: {str(log_error)}")


@receiver(post_save, sender=User)
def handle_user_created_for_patient(sender, instance, created, **kwargs):
    """
    Handle user creation to check if it's associated with a patient and send appropriate emails.
    This handles cases where a user account is created after the patient record.
    
    Args:
        sender: The model class (User)
        instance: The actual user instance
        created: Boolean indicating if this is a new user
        **kwargs: Additional keyword arguments
    """
    if not created:
        # Only handle new user creation, not updates
        return
        
    try:
        # Check if this user is associated with a patient
        try:
            patient = EnhancedPatient.objects.get(user=instance)
        except EnhancedPatient.DoesNotExist:
            # User is not a patient, skip
            return
            
        logger.info(f"User account created for existing patient: {patient.id}")
        
        # Initialize email service
        email_service = PatientEmailService()
        
        # Generate temporary password if user doesn't have a usable password
        temporary_password = None
        if not instance.has_usable_password():
            temporary_password = generate_temporary_password()
            instance.set_password(temporary_password)
            instance.save(update_fields=['password'])
            logger.info(f"Generated temporary password for patient user {instance.id}")
        
        # Send account activation email
        success = email_service.send_account_activation_email(
            patient=patient,
            temporary_password=temporary_password
        )
        
        if success:
            logger.info(f"Account activation email sent to patient {patient.id}")
            
            # Log the email sending event
            from notifications.models import NotificationLog
            NotificationLog.objects.create(
                recipient_type='patient',
                recipient_id=str(patient.id),
                notification_type='account_activation_email',
                channel='email',
                status='sent',
                sent_at=timezone.now(),
                metadata={
                    'patient_email': instance.email,
                    'user_id': str(instance.id),
                    'hospital_id': str(patient.hospital.id) if patient.hospital else None,
                    'has_temporary_password': temporary_password is not None
                }
            )
        else:
            logger.error(f"Failed to send account activation email to patient {patient.id}")
            
    except Exception as e:
        logger.error(f"Error handling user creation signal for patient: {str(e)}")