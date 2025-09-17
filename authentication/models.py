from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings
import uuid
import json


class User(AbstractUser):
    """Enhanced User model for MediRemind unified authentication system"""
    
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('admin', 'Administrator'),
        ('receptionist', 'Receptionist'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    full_name = models.CharField(max_length=255)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        blank=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    
    # Override username field to be nullable and non-unique since we use email as USERNAME_FIELD
    username = models.CharField(max_length=150, blank=True, null=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Profile settings
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    # Account status
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Security fields
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    mfa_enabled = models.BooleanField(default=False)
    
    # Fix conflicts with Django's built-in User model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='mediremind_users',
        related_query_name='mediremind_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='mediremind_users',
        related_query_name='mediremind_user',
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def get_full_name(self):
        return self.full_name
    
    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email


class EncryptedCharField(models.CharField):
    """Custom field for encrypting sensitive character data"""
    
    def __init__(self, *args, **kwargs):
        if hasattr(settings, 'FIELD_ENCRYPTION_KEY'):
            self.cipher_suite = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        else:
            # For development - use a default key (NOT for production)
            self.cipher_suite = Fernet(Fernet.generate_key())
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return self.cipher_suite.decrypt(value.encode()).decode()
        except:
            return value  # Return as-is if decryption fails
    
    def to_python(self, value):
        if isinstance(value, str) or value is None:
            return value
        try:
            return self.cipher_suite.decrypt(value.encode()).decode()
        except:
            return value
    
    def get_prep_value(self, value):
        if value is None:
            return value
        try:
            return self.cipher_suite.encrypt(value.encode()).decode()
        except:
            return value


class EncryptedTextField(models.TextField):
    """Custom field for encrypting sensitive text data"""
    
    def __init__(self, *args, **kwargs):
        if hasattr(settings, 'FIELD_ENCRYPTION_KEY'):
            self.cipher_suite = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        else:
            self.cipher_suite = Fernet(Fernet.generate_key())
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return self.cipher_suite.decrypt(value.encode()).decode()
        except:
            return value
    
    def to_python(self, value):
        if isinstance(value, str) or value is None:
            return value
        try:
            return self.cipher_suite.decrypt(value.encode()).decode()
        except:
            return value
    
    def get_prep_value(self, value):
        if value is None:
            return value
        try:
            return self.cipher_suite.encrypt(value.encode()).decode()
        except:
            return value


class EncryptedJSONField(models.JSONField):
    """Custom field for encrypting JSON data"""
    
    def __init__(self, *args, **kwargs):
        if hasattr(settings, 'FIELD_ENCRYPTION_KEY'):
            self.cipher_suite = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
        else:
            self.cipher_suite = Fernet(Fernet.generate_key())
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            decrypted = self.cipher_suite.decrypt(value.encode()).decode()
            return json.loads(decrypted)
        except:
            return value if isinstance(value, (dict, list)) else {}
    
    def to_python(self, value):
        if value is None or isinstance(value, (dict, list)):
            return value
        try:
            decrypted = self.cipher_suite.decrypt(value.encode()).decode()
            return json.loads(decrypted)
        except:
            return value if isinstance(value, (dict, list)) else {}
    
    def get_prep_value(self, value):
        if value is None:
            return value
        try:
            json_str = json.dumps(value)
            return self.cipher_suite.encrypt(json_str.encode()).decode()
        except:
            return json.dumps(value) if value else None


class Permission(models.Model):
    """Granular permission system for healthcare operations"""
    
    PERMISSION_CATEGORIES = [
        ('patient_data', 'Patient Data'),
        ('medical_records', 'Medical Records'),
        ('appointments', 'Appointments'),
        ('billing', 'Billing'),
        ('reports', 'Reports'),
        ('system', 'System Administration'),
        ('staff_management', 'Staff Management'),
        ('notifications', 'Notifications'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=50, unique=True, db_index=True)
    category = models.CharField(max_length=20, choices=PERMISSION_CATEGORIES)
    description = models.TextField()
    is_sensitive = models.BooleanField(default=False, help_text="Requires additional verification")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_permissions'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['codename']),
            models.Index(fields=['category']),
            models.Index(fields=['is_sensitive']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.codename})"


class RolePermission(models.Model):
    """Default permissions for each role"""
    
    ROLE_CHOICES = [
        # Patient Roles
        ('patient', 'Patient'),
        ('patient_guardian', 'Patient Guardian'),
        
        # Clinical Staff
        ('physician', 'Physician'),
        ('nurse', 'Nurse'),
        ('nurse_practitioner', 'Nurse Practitioner'),
        ('physician_assistant', 'Physician Assistant'),
        ('therapist', 'Therapist'),
        ('technician', 'Medical Technician'),
        
        # Administrative Staff
        ('receptionist', 'Receptionist'),
        ('billing_specialist', 'Billing Specialist'),
        ('medical_records_clerk', 'Medical Records Clerk'),
        ('practice_manager', 'Practice Manager'),
        
        # System Roles
        ('system_admin', 'System Administrator'),
        ('security_officer', 'Security Officer'),
        ('compliance_officer', 'Compliance Officer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, db_index=True)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_role_permissions'
        unique_together = ['role', 'permission']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.get_role_display()} - {self.permission.name}"


class UserPermission(models.Model):
    """User-specific permission overrides"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted = models.BooleanField(default=True, help_text="True=granted, False=revoked")
    
    # Authorization tracking
    granted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='granted_permissions'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Justification
    justification = models.TextField(blank=True)
    
    class Meta:
        db_table = 'auth_user_permissions'
        unique_together = ['user', 'permission']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['granted']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        status = "Granted" if self.granted else "Revoked"
        return f"{self.user.email} - {self.permission.name} ({status})"
    
    @property
    def is_active(self):
        """Check if permission is currently active"""
        if not self.granted:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True


class MFADevice(models.Model):
    """Multi-factor authentication devices"""
    
    MFA_TYPES = [
        ('totp', 'Time-based OTP (Authenticator App)'),
        ('sms', 'SMS Verification'),
        ('email', 'Email Verification'),
        ('hardware', 'Hardware Token'),
        ('backup', 'Backup Codes'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_type = models.CharField(max_length=20, choices=MFA_TYPES)
    device_name = models.CharField(max_length=100)
    
    # Device-specific data (encrypted)
    secret_key = EncryptedCharField(max_length=255, blank=True)  # For TOTP
    phone_number = EncryptedCharField(max_length=255, blank=True)  # For SMS
    
    # Status
    is_active = models.BooleanField(default=True)
    is_backup = models.BooleanField(default=False)
    
    # Usage tracking
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    use_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'auth_mfa_devices'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['device_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name} ({self.get_device_type_display()})"


class LoginAttempt(models.Model):
    """Track login attempts for security monitoring"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email_attempted = models.CharField(max_length=255, db_index=True)
    
    # Request details
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField()
    
    # Attempt details
    success = models.BooleanField(db_index=True)
    failure_reason = models.CharField(max_length=100, blank=True)
    
    # MFA details
    mfa_required = models.BooleanField(default=False)
    mfa_success = models.BooleanField(null=True, blank=True)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Session info
    session_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'auth_login_attempts'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
            models.Index(fields=['email_attempted', 'timestamp']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.email_attempted} - {status} ({self.timestamp})"


class UserSession(models.Model):
    """Enhanced session management with security features"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Request details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_fingerprint = models.CharField(max_length=255, blank=True)
    
    # Security features
    is_active = models.BooleanField(default=True, db_index=True)
    requires_reauth = models.BooleanField(default=False)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    
    # Termination
    terminated_at = models.DateTimeField(null=True, blank=True)
    termination_reason = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'auth_user_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.created_at} ({'Active' if self.is_active else 'Inactive'})"
    
    @property
    def is_expired(self):
        """Check if session is expired"""
        return self.expires_at <= timezone.now()
    
    def terminate(self, reason='manual'):
        """Terminate the session"""
        self.is_active = False
        self.terminated_at = timezone.now()
        self.termination_reason = reason
        self.save(update_fields=['is_active', 'terminated_at', 'termination_reason'])


class AuditLog(models.Model):
    """Comprehensive audit logging for HIPAA compliance"""
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read/View'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Data Export'),
        ('print', 'Print'),
        ('share', 'Share/Send'),
        ('access', 'Access'),
        ('search', 'Search'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    user_role = models.CharField(max_length=30)
    
    # What
    action = models.CharField(max_length=20, choices=ACTION_TYPES, db_index=True)
    resource_type = models.CharField(max_length=50, db_index=True)  # Model name
    resource_id = models.CharField(max_length=255, db_index=True)  # Object ID
    
    # When & Where
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Details
    description = models.TextField()
    old_values = models.JSONField(null=True, blank=True)  # For updates
    new_values = models.JSONField(null=True, blank=True)  # For updates
    
    # Patient Context (for HIPAA)
    patient_affected = models.ForeignKey(
        'accounts.EnhancedPatient', 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs'
    )
    
    # Risk Assessment
    risk_level = models.CharField(
        max_length=20, 
        choices=RISK_LEVELS, 
        default='low',
        db_index=True
    )
    
    # Additional metadata
    session_id = models.CharField(max_length=255, blank=True)
    request_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['patient_affected', 'timestamp']),
            models.Index(fields=['risk_level', 'timestamp']),
            models.Index(fields=['timestamp']),  # For time-based queries
        ]
    
    def __str__(self):
        user_info = self.user.email if self.user else 'System'
        return f"{user_info} - {self.get_action_display()} {self.resource_type} ({self.timestamp})"


class DataAccessPolicy(models.Model):
    """Define data access policies for different resources"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    resource_type = models.CharField(max_length=50, db_index=True)
    
    # Access Rules
    allowed_roles = models.JSONField(default=list)
    required_permissions = models.JSONField(default=list)
    
    # Conditions
    time_restrictions = models.JSONField(
        default=dict, 
        help_text="Business hours, days of week, etc."
    )
    location_restrictions = models.JSONField(
        default=dict, 
        help_text="IP ranges, geographic restrictions, etc."
    )
    
    # Patient Relationship Requirements
    requires_patient_relationship = models.BooleanField(default=True)
    allowed_relationship_types = models.JSONField(
        default=list, 
        help_text="Types of relationships allowed (primary_care, consulting, etc.)"
    )
    
    # Audit Requirements
    requires_justification = models.BooleanField(default=False)
    requires_supervisor_approval = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_policies'
    )
    
    class Meta:
        db_table = 'data_access_policies'
        verbose_name_plural = 'Data Access Policies'
        indexes = [
            models.Index(fields=['resource_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.resource_type})"


class SecurityAlert(models.Model):
    """Security alerts and incidents"""
    
    ALERT_TYPES = [
        ('failed_login', 'Failed Login Attempts'),
        ('account_lockout', 'Account Lockout'),
        ('suspicious_access', 'Suspicious Access Pattern'),
        ('data_breach', 'Potential Data Breach'),
        ('unauthorized_access', 'Unauthorized Access Attempt'),
        ('privilege_escalation', 'Privilege Escalation'),
        ('unusual_activity', 'Unusual User Activity'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Informational'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    
    # Alert details
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Related entities
    user_affected = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Metadata
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='resolved_alerts'
    )
    
    # Additional data
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'security_alerts'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['alert_type', 'detected_at']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['user_affected', 'detected_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_severity_display()} ({self.get_status_display()})"