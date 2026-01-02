from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from encryption.fields import EnhancedEncryptedCharField, EnhancedEncryptedTextField

User = get_user_model()

class HospitalIntegration(models.Model):
    """Model for managing hospital HMS integrations"""
    
    INTEGRATION_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
    ]
    
    API_VERSION_CHOICES = [
        ('v1', 'Version 1'),
        ('v2', 'Version 2'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.OneToOneField('accounts.Hospital', on_delete=models.CASCADE, related_name='api_integration')
    
    # API Configuration
    api_key = models.CharField(max_length=255, unique=True)
    api_secret = EnhancedEncryptedCharField(max_length=255)
    webhook_secret = EnhancedEncryptedCharField(max_length=255, blank=True)
    
    # Integration Settings
    status = models.CharField(max_length=20, choices=INTEGRATION_STATUS_CHOICES, default='pending')
    api_version = models.CharField(max_length=10, choices=API_VERSION_CHOICES, default='v1')
    
    # Data Processing Settings
    allowed_endpoints = models.JSONField(default=list, help_text="List of allowed API endpoints")
    data_retention_days = models.IntegerField(default=2555, help_text="Data retention period in days (7 years)")
    encryption_enabled = models.BooleanField(default=True)
    
    # Compliance Settings
    data_processing_agreement_signed = models.BooleanField(default=False)
    privacy_notice_accepted = models.BooleanField(default=False)
    consent_management_enabled = models.BooleanField(default=True)
    audit_logging_enabled = models.BooleanField(default=True)
    
    # Rate Limiting
    rate_limit_per_minute = models.IntegerField(default=100)
    rate_limit_per_hour = models.IntegerField(default=1000)
    rate_limit_per_day = models.IntegerField(default=10000)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_integrations')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_integrations')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True, help_text="Internal notes about the integration")
    
    class Meta:
        db_table = 'hospital_integrations'
        verbose_name = 'Hospital API Integration'
        verbose_name_plural = 'Hospital API Integrations'
        indexes = [
            models.Index(fields=['hospital', 'status']),
            models.Index(fields=['api_key']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.hospital.name} - API Integration"
    
    def is_active(self):
        return self.status == 'active'
    
    def can_process_data(self):
        return (self.status == 'active' and 
                self.data_processing_agreement_signed and 
                self.privacy_notice_accepted)

class APILog(models.Model):
    """Audit log for all API activities"""
    
    LOG_LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(HospitalIntegration, on_delete=models.CASCADE, related_name='api_logs')
    
    # Request Details
    method = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=255)
    request_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Response Details
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField(help_text="Response time in milliseconds")
    
    # Security and Compliance
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    auth_status = models.CharField(max_length=50, help_text="Authentication status")
    
    # Data Processing
    data_subjects_affected = models.IntegerField(default=0, help_text="Number of data subjects affected")
    personal_data_processed = models.BooleanField(default=False)
    data_categories = models.JSONField(default=list, help_text="Categories of data processed")
    
    # Logging
    log_level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, default='info')
    message = models.TextField()
    error_details = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'api_logs'
        verbose_name = 'API Log'
        verbose_name_plural = 'API Logs'
        indexes = [
            models.Index(fields=['integration', 'created_at']),
            models.Index(fields=['endpoint', 'status_code']),
            models.Index(fields=['request_id']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.integration.hospital.name} - {self.method} {self.endpoint} ({self.status_code})"

class DataProcessingConsent(models.Model):
    """Model for tracking data processing consent from hospitals"""
    
    CONSENT_TYPE_CHOICES = [
        ('data_processing', 'Data Processing Agreement'),
        ('patient_data', 'Patient Data Processing'),
        ('appointment_reminders', 'Appointment Reminders'),
        ('emergency_contact', 'Emergency Contact Processing'),
        ('analytics', 'Analytics and Reporting'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('granted', 'Granted'),
        ('withdrawn', 'Withdrawn'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(HospitalIntegration, on_delete=models.CASCADE, related_name='consents')
    
    consent_type = models.CharField(max_length=50, choices=CONSENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Consent Details
    granted_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Consent Text and Version
    consent_text = models.TextField()
    consent_version = models.CharField(max_length=20, default='1.0')
    
    # Metadata
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Revocation Reason
    withdrawal_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_processing_consents'
        verbose_name = 'Data Processing Consent'
        verbose_name_plural = 'Data Processing Consents'
        unique_together = ['integration', 'consent_type']
        indexes = [
            models.Index(fields=['integration', 'consent_type']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.integration.hospital.name} - {self.get_consent_type_display()}"
    
    def is_valid(self):
        return (self.status == 'granted' and 
                (self.expires_at is None or self.expires_at > timezone.now()))

class SecurityIncident(models.Model):
    """Model for tracking security incidents and breaches"""
    
    INCIDENT_TYPE_CHOICES = [
        ('unauthorized_access', 'Unauthorized Access'),
        ('data_breach', 'Data Breach'),
        ('api_abuse', 'API Abuse'),
        ('authentication_failure', 'Authentication Failure'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('suspicious_activity', 'Suspicious Activity'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(HospitalIntegration, on_delete=models.CASCADE, related_name='security_incidents')
    
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Incident Details
    title = models.CharField(max_length=255)
    description = models.TextField()
    affected_data_subjects = models.IntegerField(default=0)
    data_categories_affected = models.JSONField(default=list)
    
    # Investigation
    investigation_notes = models.TextField(blank=True)
    root_cause_analysis = models.TextField(blank=True)
    remediation_actions = models.TextField(blank=True)
    
    # Timestamps
    detected_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    reported_to_odpc_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'security_incidents'
        verbose_name = 'Security Incident'
        verbose_name_plural = 'Security Incidents'
        indexes = [
            models.Index(fields=['integration', 'status']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['incident_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.integration.hospital.name} - {self.title} ({self.severity})"
    
    def requires_odpc_notification(self):
        """Check if incident requires notification to ODPC within 72 hours"""
        return self.severity in ['high', 'critical'] and self.affected_data_subjects > 0