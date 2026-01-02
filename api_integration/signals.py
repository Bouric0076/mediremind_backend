import logging
from django.db.models.signals import post_save, post_delete, post_init
from django.dispatch import receiver
from django.utils import timezone
from .models import HospitalIntegration, DataProcessingConsent, SecurityIncident

logger = logging.getLogger(__name__)

@receiver(post_save, sender=HospitalIntegration)
def log_integration_changes(sender, instance, created, **kwargs):
    """Log changes to hospital integrations"""
    if created:
        logger.info(f"New hospital integration created: {instance.hospital.name} (ID: {instance.id})")
    else:
        # Check if status changed
        if hasattr(instance, '_original_status') and instance.status != instance._original_status:
            logger.info(f"Integration status changed for {instance.hospital.name}: {instance._original_status} -> {instance.status}")
            
            # Create security incident for status changes
            if instance.status in ['suspended', 'revoked']:
                SecurityIncident.objects.create(
                    integration=instance,
                    title=f"Integration {instance.status.title()}",
                    description=f"Hospital integration was {instance.status} for {instance.hospital.name}",
                    severity="medium" if instance.status == "suspended" else "high",
                    incident_type="integration_status_change",
                    source="system"
                )

@receiver(post_save, sender=DataProcessingConsent)
def log_consent_changes(sender, instance, created, **kwargs):
    """Log changes to data processing consents"""
    if created:
        logger.info(f"New consent created for {instance.integration.hospital.name}: {instance.consent_type}")
    else:
        # Check if status changed
        if hasattr(instance, '_original_status') and instance.status != instance._original_status:
            logger.info(f"Consent status changed for {instance.integration.hospital.name}: {instance.consent_type} - {instance._original_status} -> {instance.status}")
            
            # Create security incident for consent withdrawals
            if instance.status == 'withdrawn':
                SecurityIncident.objects.create(
                    integration=instance.integration,
                    title="Consent Withdrawn",
                    description=f"Data processing consent was withdrawn for {instance.consent_type}",
                    severity="medium",
                    incident_type="consent_withdrawal",
                    source="user"
                )