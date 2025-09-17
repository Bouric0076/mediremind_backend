# MediRemind User Management Architecture

## Executive Summary

This document defines the comprehensive user management architecture for the MediRemind healthcare platform. The system is designed to handle multiple user types (patients, healthcare providers, administrators) with robust security, scalability, and compliance with healthcare regulations.

## Current Architecture Analysis

### Strengths
- Custom User model extending AbstractUser
- Comprehensive patient and staff profile models
- Supabase integration for authentication
- Role-based user classification
- Detailed medical and professional information storage

### Issues Identified
1. **Architectural Inconsistencies**: Mixed Django/Supabase authentication patterns
2. **Security Concerns**: Direct admin client usage in views
3. **Data Structure Problems**: Inconsistent foreign key relationships
4. **Scalability Issues**: Lack of proper permission system
5. **Compliance Gaps**: Missing audit trails and data protection features

## Ideal User Management Architecture

### 1. Core User Model Design

#### Enhanced User Model
```python
class User(AbstractUser):
    """Enhanced User model with comprehensive healthcare features"""
    
    # Core Identity
    id = UUIDField(primary_key=True, default=uuid4)
    email = EmailField(unique=True, db_index=True)
    full_name = CharField(max_length=255)
    
    # Role Management
    role = CharField(max_length=20, choices=ROLE_CHOICES)
    permissions = ManyToManyField('UserPermission')
    
    # Security & Compliance
    is_verified = BooleanField(default=False)
    mfa_enabled = BooleanField(default=False)
    last_password_change = DateTimeField(auto_now_add=True)
    failed_login_attempts = PositiveIntegerField(default=0)
    account_locked_until = DateTimeField(null=True, blank=True)
    
    # Audit Trail
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    created_by = ForeignKey('self', null=True, on_delete=SET_NULL)
    last_activity = DateTimeField(null=True, blank=True)
    
    # Privacy & Preferences
    privacy_settings = JSONField(default=dict)
    notification_preferences = JSONField(default=dict)
    data_sharing_consent = BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']
```

#### Role Hierarchy
```python
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
```

### 2. Permission System Design

#### Granular Permission Model
```python
class Permission(models.Model):
    """Granular permission system for healthcare operations"""
    
    PERMISSION_CATEGORIES = [
        ('patient_data', 'Patient Data'),
        ('medical_records', 'Medical Records'),
        ('appointments', 'Appointments'),
        ('billing', 'Billing'),
        ('reports', 'Reports'),
        ('system', 'System Administration'),
    ]
    
    name = CharField(max_length=100, unique=True)
    codename = CharField(max_length=50, unique=True)
    category = CharField(max_length=20, choices=PERMISSION_CATEGORIES)
    description = TextField()
    is_sensitive = BooleanField(default=False)  # Requires additional verification
    
class RolePermission(models.Model):
    """Default permissions for each role"""
    role = CharField(max_length=20, choices=ROLE_CHOICES)
    permission = ForeignKey(Permission, on_delete=CASCADE)
    is_default = BooleanField(default=True)
    
class UserPermission(models.Model):
    """User-specific permission overrides"""
    user = ForeignKey(User, on_delete=CASCADE)
    permission = ForeignKey(Permission, on_delete=CASCADE)
    granted = BooleanField(default=True)
    granted_by = ForeignKey(User, on_delete=SET_NULL, null=True, related_name='granted_permissions')
    granted_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField(null=True, blank=True)
```

### 3. Enhanced Profile Management

#### Patient Profile Architecture
```python
class PatientProfile(models.Model):
    """Comprehensive patient profile with HIPAA compliance"""
    
    user = OneToOneField(User, on_delete=CASCADE, primary_key=True)
    
    # Identity & Demographics
    patient_id = CharField(max_length=20, unique=True, db_index=True)
    date_of_birth = DateField()
    gender = CharField(max_length=20, choices=GENDER_CHOICES)
    preferred_pronouns = CharField(max_length=50, blank=True)
    
    # Contact & Address (Encrypted)
    encrypted_address = EncryptedTextField()
    encrypted_phone = EncryptedCharField(max_length=255)
    
    # Emergency Contacts
    emergency_contacts = JSONField(default=list)  # Encrypted in application layer
    
    # Medical Information
    primary_care_provider = ForeignKey('StaffProfile', null=True, on_delete=SET_NULL)
    medical_record_number = CharField(max_length=50, unique=True)
    
    # Insurance & Billing
    insurance_information = EncryptedJSONField(default=dict)
    
    # Consent & Privacy
    hipaa_authorization = BooleanField(default=False)
    research_participation_consent = BooleanField(default=False)
    data_sharing_preferences = JSONField(default=dict)
    
    # Audit Fields
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    last_accessed = DateTimeField(null=True, blank=True)
    access_log = JSONField(default=list)  # Track who accessed when
```

#### Staff Profile Architecture
```python
class StaffProfile(models.Model):
    """Enhanced staff profile with credential management"""
    
    user = OneToOneField(User, on_delete=CASCADE, primary_key=True)
    
    # Professional Identity
    staff_id = CharField(max_length=20, unique=True, db_index=True)
    professional_title = CharField(max_length=100)
    department = ForeignKey('Department', on_delete=SET_NULL, null=True)
    
    # Credentials & Licensing
    licenses = JSONField(default=list)  # Professional licenses with expiry tracking
    certifications = JSONField(default=list)  # Board certifications
    education = JSONField(default=list)  # Educational background
    
    # Specializations
    specializations = ManyToManyField('Specialization')
    primary_specialization = ForeignKey('Specialization', on_delete=SET_NULL, null=True)
    
    # Employment
    employment_status = CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES)
    hire_date = DateField()
    supervisor = ForeignKey('self', null=True, on_delete=SET_NULL)
    
    # Clinical Settings
    can_prescribe = BooleanField(default=False)
    can_order_tests = BooleanField(default=False)
    max_patient_load = PositiveIntegerField(null=True, blank=True)
    
    # Availability & Scheduling
    default_appointment_duration = PositiveIntegerField(default=30)
    consultation_fees = JSONField(default=dict)
    
    # Status
    is_accepting_patients = BooleanField(default=True)
    is_on_call_eligible = BooleanField(default=False)
    
    # Audit Fields
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### 4. Authentication & Security Architecture

#### Multi-Factor Authentication
```python
class MFADevice(models.Model):
    """Multi-factor authentication devices"""
    
    MFA_TYPES = [
        ('totp', 'Time-based OTP (Authenticator App)'),
        ('sms', 'SMS Verification'),
        ('email', 'Email Verification'),
        ('hardware', 'Hardware Token'),
    ]
    
    user = ForeignKey(User, on_delete=CASCADE)
    device_type = CharField(max_length=20, choices=MFA_TYPES)
    device_name = CharField(max_length=100)
    secret_key = EncryptedCharField(max_length=255)  # For TOTP
    phone_number = EncryptedCharField(max_length=255, null=True)  # For SMS
    is_active = BooleanField(default=True)
    is_backup = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    last_used = DateTimeField(null=True, blank=True)

class LoginAttempt(models.Model):
    """Track login attempts for security monitoring"""
    
    user = ForeignKey(User, on_delete=CASCADE, null=True, blank=True)
    email_attempted = CharField(max_length=255)
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    success = BooleanField()
    failure_reason = CharField(max_length=100, blank=True)
    mfa_required = BooleanField(default=False)
    mfa_success = BooleanField(null=True, blank=True)
    timestamp = DateTimeField(auto_now_add=True)
    session_id = CharField(max_length=255, blank=True)
```

#### Session Management
```python
class UserSession(models.Model):
    """Enhanced session management with security features"""
    
    user = ForeignKey(User, on_delete=CASCADE)
    session_key = CharField(max_length=255, unique=True)
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    device_fingerprint = CharField(max_length=255, blank=True)
    
    # Security Features
    is_active = BooleanField(default=True)
    requires_reauth = BooleanField(default=False)
    last_activity = DateTimeField(auto_now=True)
    expires_at = DateTimeField()
    
    # Audit
    created_at = DateTimeField(auto_now_add=True)
    terminated_at = DateTimeField(null=True, blank=True)
    termination_reason = CharField(max_length=100, blank=True)
```

### 5. Audit & Compliance System

#### Comprehensive Audit Trail
```python
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
    ]
    
    # Who
    user = ForeignKey(User, on_delete=SET_NULL, null=True)
    user_role = CharField(max_length=20)
    
    # What
    action = CharField(max_length=20, choices=ACTION_TYPES)
    resource_type = CharField(max_length=50)  # Model name
    resource_id = CharField(max_length=255)  # Object ID
    
    # When & Where
    timestamp = DateTimeField(auto_now_add=True)
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    
    # Details
    description = TextField()
    old_values = JSONField(null=True, blank=True)  # For updates
    new_values = JSONField(null=True, blank=True)  # For updates
    
    # Patient Context (for HIPAA)
    patient_affected = ForeignKey('PatientProfile', null=True, on_delete=SET_NULL)
    
    # Risk Assessment
    risk_level = CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='low')
```

### 6. Data Protection & Privacy

#### Field-Level Encryption
```python
from cryptography.fernet import Fernet
from django.conf import settings

class EncryptedField(models.Field):
    """Custom field for encrypting sensitive data"""
    
    def __init__(self, *args, **kwargs):
        self.cipher_suite = Fernet(settings.FIELD_ENCRYPTION_KEY)
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self.cipher_suite.decrypt(value.encode()).decode()
    
    def to_python(self, value):
        if isinstance(value, str):
            return value
        if value is None:
            return value
        return self.cipher_suite.decrypt(value.encode()).decode()
    
    def get_prep_value(self, value):
        if value is None:
            return value
        return self.cipher_suite.encrypt(value.encode()).decode()
```

#### Data Access Controls
```python
class DataAccessPolicy(models.Model):
    """Define data access policies"""
    
    name = CharField(max_length=100, unique=True)
    resource_type = CharField(max_length=50)
    
    # Access Rules
    allowed_roles = JSONField(default=list)
    required_permissions = JSONField(default=list)
    
    # Conditions
    time_restrictions = JSONField(default=dict)  # Business hours, etc.
    location_restrictions = JSONField(default=dict)  # IP ranges, etc.
    
    # Patient Relationship Requirements
    requires_patient_relationship = BooleanField(default=True)
    allowed_relationship_types = JSONField(default=list)  # ['primary_care', 'consulting', etc.]
    
    # Audit Requirements
    requires_justification = BooleanField(default=False)
    requires_supervisor_approval = BooleanField(default=False)
    
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
```

### 7. Integration Architecture

#### Unified Authentication Service
```python
class AuthenticationService:
    """Unified authentication service integrating Django and Supabase"""
    
    def __init__(self):
        self.supabase_client = create_supabase_client()
        self.django_auth = DjangoAuthBackend()
    
    def authenticate(self, email: str, password: str, mfa_token: str = None):
        """Unified authentication flow"""
        
        # 1. Validate credentials with Supabase
        supabase_result = self.supabase_client.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        
        if not supabase_result.user:
            self.log_failed_attempt(email, 'invalid_credentials')
            raise AuthenticationError('Invalid credentials')
        
        # 2. Get Django user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.log_failed_attempt(email, 'user_not_found')
            raise AuthenticationError('User not found')
        
        # 3. Check account status
        if not user.is_active:
            self.log_failed_attempt(email, 'account_disabled')
            raise AuthenticationError('Account disabled')
        
        if user.account_locked_until and user.account_locked_until > timezone.now():
            self.log_failed_attempt(email, 'account_locked')
            raise AuthenticationError('Account temporarily locked')
        
        # 4. MFA verification if enabled
        if user.mfa_enabled:
            if not mfa_token:
                return {'requires_mfa': True, 'user_id': user.id}
            
            if not self.verify_mfa(user, mfa_token):
                self.log_failed_attempt(email, 'invalid_mfa')
                raise AuthenticationError('Invalid MFA token')
        
        # 5. Create session
        session = self.create_session(user, supabase_result.session)
        
        # 6. Log successful login
        self.log_successful_login(user)
        
        return {
            'user': user,
            'session': session,
            'supabase_session': supabase_result.session
        }
```

### 8. API Security Architecture

#### Request Authentication Middleware
```python
class HealthcareAuthMiddleware:
    """Enhanced authentication middleware for healthcare APIs"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 1. Extract and validate token
        token = self.extract_token(request)
        if not token:
            return self.unauthorized_response()
        
        # 2. Validate with Supabase
        user_data = self.validate_supabase_token(token)
        if not user_data:
            return self.unauthorized_response()
        
        # 3. Get Django user and check permissions
        user = self.get_django_user(user_data.user.id)
        if not user or not user.is_active:
            return self.unauthorized_response()
        
        # 4. Check session validity
        session = self.validate_session(user, request)
        if not session:
            return self.unauthorized_response()
        
        # 5. Attach user to request
        request.user = user
        request.session_info = session
        
        # 6. Log API access
        self.log_api_access(user, request)
        
        response = self.get_response(request)
        
        # 7. Update session activity
        self.update_session_activity(session)
        
        return response
```

## Implementation Roadmap

### Phase 1: Core Infrastructure (Weeks 1-2)
1. Enhanced User model with security features
2. Permission system implementation
3. Audit logging infrastructure
4. Field-level encryption setup

### Phase 2: Authentication & Security (Weeks 3-4)
1. Unified authentication service
2. Multi-factor authentication
3. Session management
4. API security middleware

### Phase 3: Profile Management (Weeks 5-6)
1. Enhanced patient profiles
2. Staff profile improvements
3. Data access policies
4. Privacy controls

### Phase 4: Compliance & Monitoring (Weeks 7-8)
1. HIPAA compliance features
2. Security monitoring
3. Audit reporting
4. Data breach detection

## Security Considerations

### Data Protection
- Field-level encryption for PII/PHI
- Secure key management
- Regular security audits
- Penetration testing

### Access Control
- Principle of least privilege
- Role-based access control
- Time-based access restrictions
- Geographic access controls

### Compliance
- HIPAA compliance
- SOC 2 Type II
- Regular compliance audits
- Staff training programs

## Monitoring & Alerting

### Security Monitoring
- Failed login attempt monitoring
- Unusual access pattern detection
- Privilege escalation alerts
- Data export monitoring

### Performance Monitoring
- Authentication latency
- Database query performance
- API response times
- User session analytics

## Conclusion

This architecture provides a robust, secure, and scalable user management system for the MediRemind healthcare platform. It addresses current limitations while ensuring compliance with healthcare regulations and industry best practices.

The phased implementation approach allows for gradual migration from the current system while maintaining operational continuity. Regular security reviews and updates will ensure the system remains secure and compliant as it evolves.