from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class DataRetentionManager:
    """Manages data retention and deletion according to KDPA requirements"""
    
    @staticmethod
    def should_delete_data(integration, data_type='patient_data'):
        """Check if data should be deleted based on retention policy"""
        retention_days = integration.data_retention_days
        
        if data_type == 'patient_data':
            # Patient data retention period
            retention_date = timezone.now() - timedelta(days=retention_days)
            return retention_date
        elif data_type == 'audit_logs':
            # Audit logs retention (longer for compliance)
            audit_retention_days = max(retention_days, 2555)  # 7 years minimum
            return timezone.now() - timedelta(days=audit_retention_days)
        
        return timezone.now() - timedelta(days=retention_days)
    
    @staticmethod
    def delete_expired_data():
        """Delete data that has exceeded retention period"""
        from .models import HospitalIntegration, APILog
        from appointments.models import Patient, Appointment
        
        try:
            # Get all active integrations
            integrations = HospitalIntegration.objects.filter(status='active')
            
            for integration in integrations:
                retention_date = DataRetentionManager.should_delete_data(integration)
                
                # Delete expired patient data (soft delete for audit)
                patients_to_archive = Patient.objects.filter(
                    hospital=integration.hospital,
                    created_at__lt=retention_date,
                    is_archived=False
                )
                
                count = patients_to_archive.count()
                if count > 0:
                    # Archive instead of hard delete for compliance
                    patients_to_archive.update(
                        is_archived=True,
                        archived_at=timezone.now(),
                        archived_reason='Data retention policy expired'
                    )
                    
                    logger.info(f"Archived {count} patient records for {integration.hospital.name}")
                
                # Delete expired appointments (hard delete)
                appointments_to_delete = Appointment.objects.filter(
                    hospital=integration.hospital,
                    created_at__lt=retention_date,
                    appointment_date__lt=timezone.now()  # Only delete past appointments
                )
                
                appointment_count = appointments_to_delete.count()
                if appointment_count > 0:
                    appointments_to_delete.delete()
                    logger.info(f"Deleted {appointment_count} expired appointments for {integration.hospital.name}")
                
                # Archive old audit logs (keep recent ones for compliance)
                audit_retention_date = DataRetentionManager.should_delete_data(integration, 'audit_logs')
                old_logs = APILog.objects.filter(
                    integration=integration,
                    created_at__lt=audit_retention_date
                )
                
                log_count = old_logs.count()
                if log_count > 0:
                    # Archive to separate storage (implementation depends on your setup)
                    # For now, we'll keep them but mark as archived
                    old_logs.update(archived=True)
                    logger.info(f"Archived {log_count} old audit logs for {integration.hospital.name}")
                    
        except Exception as e:
            logger.error(f"Error during data retention cleanup: {str(e)}")
            # Log to security incidents
            from .models import SecurityIncident
            SecurityIncident.objects.create(
                integration=None,  # System-wide incident
                title="Data Retention Cleanup Error",
                description=f"Error occurred during automated data retention cleanup: {str(e)}",
                severity="medium",
                incident_type="system_error",
                source="data_retention_manager"
            )

class ConsentExpiryManager:
    """Manages consent expiry and renewal notifications"""
    
    @staticmethod
    def check_consent_expiry():
        """Check for expired consents and notify"""
        from .models import DataProcessingConsent
        
        try:
            # Find consents expiring in the next 30 days
            expiring_soon = timezone.now() + timedelta(days=30)
            
            expiring_consents = DataProcessingConsent.objects.filter(
                status='active',
                expires_at__lte=expiring_soon,
                expiry_notified=False
            )
            
            for consent in expiring_consents:
                # Send notification to hospital
                logger.warning(
                    f"Consent expiring soon for {consent.integration.hospital.name}: "
                    f"{consent.consent_type} (expires {consent.expires_at})"
                )
                
                # Mark as notified to prevent duplicate notifications
                consent.expiry_notified = True
                consent.save()
                
                # Log the notification
                from .models import APILog
                APILog.objects.create(
                    integration=consent.integration,
                    method='SYSTEM',
                    endpoint='consent_expiry_check',
                    status_code=200,
                    ip_address='127.0.0.1',
                    auth_status='success',
                    message=f"Consent expiry notification sent for {consent.consent_type}",
                    data_categories=['consent_data']
                )
                
        except Exception as e:
            logger.error(f"Error checking consent expiry: {str(e)}")

class ComplianceReporter:
    """Generates compliance reports for ODPC and internal audits"""
    
    @staticmethod
    def generate_monthly_compliance_report():
        """Generate monthly compliance report"""
        from .models import HospitalIntegration, APILog, SecurityIncident
        
        try:
            report_data = {
                'report_date': timezone.now(),
                'report_period': 'monthly',
                'integrations': {},
                'summary': {
                    'total_integrations': 0,
                    'active_integrations': 0,
                    'total_api_calls': 0,
                    'security_incidents': 0,
                    'consent_issues': 0
                }
            }
            
            integrations = HospitalIntegration.objects.all()
            report_data['summary']['total_integrations'] = integrations.count()
            report_data['summary']['active_integrations'] = integrations.filter(status='active').count()
            
            for integration in integrations:
                # Get API usage stats for the month
                current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                monthly_logs = APILog.objects.filter(
                    integration=integration,
                    created_at__gte=current_month
                )
                
                # Get security incidents
                monthly_incidents = SecurityIncident.objects.filter(
                    integration=integration,
                    created_at__gte=current_month
                )
                
                # Check consent status
                from .models import DataProcessingConsent
                expired_consents = DataProcessingConsent.objects.filter(
                    integration=integration,
                    status='expired'
                )
                
                report_data['integrations'][integration.hospital.name] = {
                    'status': integration.status,
                    'api_calls': monthly_logs.count(),
                    'security_incidents': monthly_incidents.count(),
                    'expired_consents': expired_consents.count(),
                    'data_retention_days': integration.data_retention_days,
                    'encryption_enabled': integration.encryption_enabled
                }
                
                report_data['summary']['total_api_calls'] += monthly_logs.count()
                report_data['summary']['security_incidents'] += monthly_incidents.count()
                report_data['summary']['consent_issues'] += expired_consents.count()
            
            # Log the report generation
            logger.info(f"Monthly compliance report generated: {report_data['summary']}")
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            return None