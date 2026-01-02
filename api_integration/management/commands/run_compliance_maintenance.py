from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run compliance maintenance tasks for API integration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=['data_retention', 'consent_expiry', 'security_incidents', 'all'],
            default='all',
            help='Specific task to run (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no actual changes)'
        )
    
    def handle(self, *args, **options):
        """Run compliance maintenance tasks"""
        task = options['task']
        dry_run = options['dry_run']
        
        self.stdout.write(f"Running compliance maintenance: {task}")
        
        try:
            if task in ['data_retention', 'all']:
                self.handle_data_retention(dry_run)
            
            if task in ['consent_expiry', 'all']:
                self.handle_consent_expiry(dry_run)
            
            if task in ['security_incidents', 'all']:
                self.handle_security_incidents(dry_run)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully completed compliance maintenance')
            )
            
        except Exception as e:
            logger.error(f"Compliance maintenance failed: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Compliance maintenance failed: {str(e)}')
            )
            raise
    
    def handle_data_retention(self, dry_run=False):
        """Handle data retention policies"""
        from .compliance import DataRetentionManager
        
        self.stdout.write("Processing data retention policies...")
        
        if dry_run:
            self.stdout.write("DRY RUN: Would process data retention policies")
            return
        
        try:
            deleted_count = DataRetentionManager.delete_expired_data()
            self.stdout.write(f"Deleted {deleted_count} expired data records")
            
            archived_count = DataRetentionManager.archive_old_data()
            self.stdout.write(f"Archived {archived_count} old data records")
            
        except Exception as e:
            logger.error(f"Data retention processing failed: {str(e)}")
            self.stdout.write(
                self.style.WARNING(f'Data retention processing failed: {str(e)}')
            )
    
    def handle_consent_expiry(self, dry_run=False):
        """Handle consent expiry notifications"""
        from .compliance import ConsentExpiryManager
        
        self.stdout.write("Processing consent expiry notifications...")
        
        if dry_run:
            self.stdout.write("DRY RUN: Would process consent expiry notifications")
            return
        
        try:
            # Notify about expiring consents (30 days before expiry)
            expiring_count = ConsentExpiryManager.notify_expiring_consents(days_before_expiry=30)
            self.stdout.write(f"Notified {expiring_count} expiring consents")
            
            # Expire consents that have passed expiry date
            expired_count = ConsentExpiryManager.expire_old_consents()
            self.stdout.write(f"Expired {expired_count} old consents")
            
        except Exception as e:
            logger.error(f"Consent expiry processing failed: {str(e)}")
            self.stdout.write(
                self.style.WARNING(f'Consent expiry processing failed: {str(e)}')
            )
    
    def handle_security_incidents(self, dry_run=False):
        """Handle security incident management"""
        from .compliance import SecurityIncidentManager
        
        self.stdout.write("Processing security incidents...")
        
        if dry_run:
            self.stdout.write("DRY RUN: Would process security incidents")
            return
        
        try:
            # Escalate old unresolved incidents
            escalated_count = SecurityIncidentManager.escalate_old_incidents()
            self.stdout.write(f"Escalated {escalated_count} old security incidents")
            
            # Generate incident reports
            reports_generated = SecurityIncidentManager.generate_monthly_reports()
            self.stdout.write(f"Generated {reports_generated} security incident reports")
            
        except Exception as e:
            logger.error(f"Security incident processing failed: {str(e)}")
            self.stdout.write(
                self.style.WARNING(f'Security incident processing failed: {str(e)}')
            )

class DataRetentionManager:
    """Manager for data retention policies"""
    
    @staticmethod
    def delete_expired_data():
        """Delete data that has exceeded retention period"""
        from .models import HospitalIntegration
        from appointments.models import Patient, Appointment
        
        deleted_count = 0
        
        # Process each integration's data retention policy
        for integration in HospitalIntegration.objects.filter(status='active'):
            retention_date = timezone.now() - timedelta(days=integration.data_retention_days)
            
            # Delete expired patient data (after archiving)
            patients_to_delete = Patient.objects.filter(
                hospital=integration.hospital,
                created_at__lt=retention_date,
                is_archived=True
            )
            deleted_count += patients_to_delete.count()
            patients_to_delete.delete()
            
            # Delete expired appointment data
            appointments_to_delete = Appointment.objects.filter(
                patient__hospital=integration.hospital,
                created_at__lt=retention_date
            )
            deleted_count += appointments_to_delete.count()
            appointments_to_delete.delete()
        
        return deleted_count
    
    @staticmethod
    def archive_old_data():
        """Archive data that is approaching retention limit"""
        from .models import HospitalIntegration
        from appointments.models import Patient
        
        archived_count = 0
        
        # Process each integration's data retention policy
        for integration in HospitalIntegration.objects.filter(status='active'):
            retention_date = timezone.now() - timedelta(days=integration.data_retention_days)
            
            # Archive patient data that will be deleted soon (30 days before retention)
            archive_date = retention_date + timedelta(days=30)
            
            patients_to_archive = Patient.objects.filter(
                hospital=integration.hospital,
                created_at__lt=archive_date,
                is_archived=False
            )
            
            archived_count += patients_to_archive.count()
            patients_to_archive.update(
                is_archived=True,
                archived_at=timezone.now(),
                archived_reason='Data retention policy - approaching expiry'
            )
        
        return archived_count

class ConsentExpiryManager:
    """Manager for consent expiry notifications and processing"""
    
    @staticmethod
    def notify_expiring_consents(days_before_expiry=30):
        """Notify about consents that will expire soon"""
        from .models import DataProcessingConsent
        from django.core.mail import send_mail
        
        notification_date = timezone.now() + timedelta(days=days_before_expiry)
        
        expiring_consents = DataProcessingConsent.objects.filter(
            status='active',
            expires_at__date=notification_date.date()
        )
        
        notified_count = 0
        
        for consent in expiring_consents:
            try:
                # Send notification to hospital admin
                send_mail(
                    subject='Data Processing Consent Expiring Soon',
                    message=f'Your {consent.consent_type} consent will expire on {consent.expires_at}. Please renew if you wish to continue using our services.',
                    from_email='noreply@mediremind.co.ke',
                    recipient_list=[consent.integration.hospital.email],
                    fail_silently=True
                )
                
                # Create notification record
                consent.notified_at = timezone.now()
                consent.save(update_fields=['notified_at'])
                
                notified_count += 1
                
            except Exception as e:
                logger.error(f"Failed to notify consent expiry for {consent.id}: {str(e)}")
        
        return notified_count
    
    @staticmethod
    def expire_old_consents():
        """Expire consents that have passed their expiry date"""
        from .models import DataProcessingConsent
        
        expired_consents = DataProcessingConsent.objects.filter(
            status='active',
            expires_at__lt=timezone.now()
        )
        
        expired_count = expired_consents.count()
        
        # Update status to expired
        expired_consents.update(
            status='expired',
            expired_at=timezone.now()
        )
        
        return expired_count

class SecurityIncidentManager:
    """Manager for security incident handling"""
    
    @staticmethod
    def escalate_old_incidents():
        """Escalate unresolved incidents that are older than 24 hours"""
        from .models import SecurityIncident
        
        escalation_date = timezone.now() - timedelta(hours=24)
        
        incidents_to_escalate = SecurityIncident.objects.filter(
            status='open',
            created_at__lt=escalation_date,
            severity__in=['medium', 'high']
        )
        
        escalated_count = incidents_to_escalate.count()
        
        # Escalate severity
        for incident in incidents_to_escalate:
            if incident.severity == 'medium':
                incident.severity = 'high'
            elif incident.severity == 'high':
                incident.severity = 'critical'
            
            incident.escalated_at = timezone.now()
            incident.save(update_fields=['severity', 'escalated_at'])
            
            # Send escalation notification
            from django.core.mail import send_mail
            try:
                send_mail(
                    subject=f'Security Incident Escalated - {incident.title}',
                    message=f'A security incident has been escalated to {incident.severity} severity. Please review immediately.',
                    from_email='security@mediremind.co.ke',
                    recipient_list=['security@mediremind.co.ke'],
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"Failed to send escalation notification for incident {incident.id}: {str(e)}")
        
        return escalated_count
    
    @staticmethod
    def generate_monthly_reports():
        """Generate monthly security incident reports"""
        from .models import SecurityIncident
        from django.core.mail import send_mail
        
        # Get incidents from last month
        last_month = timezone.now() - timedelta(days=30)
        
        incidents = SecurityIncident.objects.filter(
            created_at__gte=last_month
        )
        
        # Generate report
        report_data = {
            'total_incidents': incidents.count(),
            'open_incidents': incidents.filter(status='open').count(),
            'resolved_incidents': incidents.filter(status='resolved').count(),
            'by_severity': {
                'low': incidents.filter(severity='low').count(),
                'medium': incidents.filter(severity='medium').count(),
                'high': incidents.filter(severity='high').count(),
                'critical': incidents.filter(severity='critical').count(),
            },
            'by_type': {},
            'by_source': {}
        }
        
        # Group by incident type and source
        for incident in incidents:
            report_data['by_type'][incident.incident_type] = report_data['by_type'].get(incident.incident_type, 0) + 1
            report_data['by_source'][incident.source] = report_data['by_source'].get(incident.source, 0) + 1
        
        # Send report email
        try:
            send_mail(
                subject='Monthly Security Incident Report',
                message=f'Monthly security incident report generated. Total incidents: {report_data["total_incidents"]}.',
                from_email='security@mediremind.co.ke',
                recipient_list=['security@mediremind.co.ke'],
                fail_silently=True
            )
            
            return 1  # One report generated
            
        except Exception as e:
            logger.error(f"Failed to generate security incident report: {str(e)}")
            return 0