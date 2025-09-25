from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from authentication.models import EncryptedCharField, EncryptedTextField, EncryptedJSONField
import uuid
from datetime import date, timedelta

User = get_user_model()


class Hospital(models.Model):
    """Hospital/Clinic model for multi-tenant support"""
    
    HOSPITAL_TYPE_CHOICES = [
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('medical_center', 'Medical Center'),
        ('urgent_care', 'Urgent Care'),
        ('specialty_clinic', 'Specialty Clinic'),
        ('dental_clinic', 'Dental Clinic'),
        ('veterinary_clinic', 'Veterinary Clinic'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Approval'),
    ]
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    hospital_type = models.CharField(max_length=50, choices=HOSPITAL_TYPE_CHOICES, default='clinic')
    
    # Contact Information
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    website = models.URLField(blank=True)
    
    # Address Information
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')
    
    # Business Information
    license_number = EncryptedCharField(max_length=255, blank=True)
    tax_id = EncryptedCharField(max_length=255, blank=True)
    accreditation = models.JSONField(default=list, help_text="List of accreditations")
    
    # Settings and Configuration
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    currency = models.CharField(max_length=3, default='USD')
    
    # Operational Settings
    operating_hours = models.JSONField(
        default=dict,
        help_text="Weekly operating hours in JSON format"
    )
    appointment_settings = models.JSONField(
        default=dict,
        help_text="Appointment booking settings and rules"
    )
    notification_settings = models.JSONField(
        default=dict,
        help_text="Hospital-specific notification preferences"
    )
    
    # Branding
    logo = models.ImageField(upload_to='hospital_logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#007bff', help_text="Primary brand color (hex)")
    secondary_color = models.CharField(max_length=7, default='#6c757d', help_text="Secondary brand color (hex)")
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_verified = models.BooleanField(default=False)
    subscription_plan = models.CharField(max_length=50, default='basic')
    max_staff = models.PositiveIntegerField(default=50, help_text="Maximum number of staff members")
    max_patients = models.PositiveIntegerField(default=1000, help_text="Maximum number of patients")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hospitals'
        verbose_name = 'Hospital/Clinic'
        verbose_name_plural = 'Hospitals/Clinics'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['hospital_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_hospital_type_display()})"
    
    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = [self.address_line_1]
        if self.address_line_2:
            address_parts.append(self.address_line_2)
        address_parts.extend([self.city, self.state, self.postal_code])
        return ', '.join(address_parts)
    
    @property
    def staff_count(self):
        """Return current number of staff members"""
        return self.staff_members.filter(employment_status__in=['full_time', 'part_time', 'contract']).count()
    
    @property
    def patient_count(self):
        """Return current number of patients"""
        return self.hospital_patients.filter(status='active').count()
    
    def can_add_staff(self):
        """Check if hospital can add more staff members"""
        return self.staff_count < self.max_staff
    
    def can_add_patients(self):
        """Check if hospital can add more patients"""
        return self.patient_count < self.max_patients


class HospitalPatient(models.Model):
    """Relationship model linking patients to hospitals while keeping patients global"""
    
    RELATIONSHIP_TYPE_CHOICES = [
        ('appointment', 'Has Appointment'),
        ('recurring', 'Recurring Patient'),
        ('admin_added', 'Added by Admin'),
        ('transferred', 'Transferred from Another Hospital'),
        ('emergency', 'Emergency Visit'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('transferred', 'Transferred'),
        ('discharged', 'Discharged'),
    ]
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(
        'Hospital',
        on_delete=models.CASCADE,
        related_name='hospital_patients'
    )
    patient = models.ForeignKey(
        'EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='hospital_relationships'
    )
    
    # Relationship details
    relationship_type = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_TYPE_CHOICES,
        default='appointment'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Metadata
    added_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='added_hospital_patients',
        help_text="Staff member who added this patient to the hospital"
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this patient-hospital relationship"
    )
    
    # Patient-specific settings for this hospital
    preferred_language = models.CharField(max_length=10, blank=True)
    communication_preferences = models.JSONField(
        default=dict,
        help_text="Hospital-specific communication preferences"
    )
    
    # Timestamps
    first_visit_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date of first appointment/visit at this hospital"
    )
    last_visit_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date of most recent appointment/visit"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hospital_patients'
        unique_together = ['hospital', 'patient']
        verbose_name = 'Hospital Patient Relationship'
        verbose_name_plural = 'Hospital Patient Relationships'
        indexes = [
            models.Index(fields=['hospital', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['relationship_type']),
            models.Index(fields=['first_visit_date']),
            models.Index(fields=['last_visit_date']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.patient.user.full_name} at {self.hospital.name}"
    
    @property
    def is_active(self):
        """Check if this patient relationship is currently active"""
        return self.status == 'active'
    
    @property
    def visit_count(self):
        """Return number of appointments this patient has had at this hospital"""
        return self.patient.appointments.filter(hospital=self.hospital).count()
    
    def update_last_visit(self, visit_date=None):
        """Update the last visit date"""
        from django.utils import timezone
        self.last_visit_date = visit_date or timezone.now()
        self.save(update_fields=['last_visit_date', 'updated_at'])


def default_emergency_notification_types():
    """Default notification types for emergency contacts"""
    return ['appointment_reminder', 'appointment_cancellation', 'appointment_rescheduled', 'no_show_alert', 'emergency_contact_added']


def default_emergency_notification_methods():
    """Default notification methods for emergency contacts"""
    return ['email', 'sms']


class EnhancedPatient(models.Model):
    """Enhanced Patient model with comprehensive medical data management"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('Unknown', 'Unknown'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
        ('domestic_partner', 'Domestic Partner'),
    ]
    
    INSURANCE_TYPE_CHOICES = [
        ('private', 'Private Insurance'),
        ('medicare', 'Medicare'),
        ('medicaid', 'Medicaid'),
        ('self_pay', 'Self Pay'),
        ('other', 'Other'),
    ]
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    
    # Personal Information
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    
    # Contact Information (encrypted for privacy)
    phone = EncryptedCharField(max_length=255)  # Increased for encrypted values
    address_line1 = EncryptedCharField(max_length=255)
    address_line2 = EncryptedCharField(max_length=255, blank=True)
    city = EncryptedCharField(max_length=255)  # Increased for encrypted values
    state = EncryptedCharField(max_length=255)  # Increased for encrypted values
    zip_code = EncryptedCharField(max_length=255)  # Increased for encrypted values
    country = models.CharField(max_length=50, default='United States')
    
    # Emergency Contact (encrypted)
    emergency_contact_name = EncryptedCharField(max_length=255)
    emergency_contact_relationship = EncryptedCharField(max_length=255)  # Increased for encrypted values
    emergency_contact_phone = EncryptedCharField(max_length=255)  # Increased for encrypted values
    emergency_contact_email = EncryptedCharField(max_length=255, blank=True)
    
    # Medical Information
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, default='Unknown')
    height_inches = models.PositiveIntegerField(null=True, blank=True, help_text="Height in inches")
    weight_lbs = models.PositiveIntegerField(null=True, blank=True, help_text="Weight in pounds")
    
    # Medical History (encrypted)
    allergies = EncryptedTextField(blank=True, help_text="Known allergies and reactions")
    current_medications = EncryptedTextField(blank=True, help_text="Current medications and dosages")
    medical_conditions = EncryptedTextField(blank=True, help_text="Chronic conditions and diagnoses")
    surgical_history = EncryptedTextField(blank=True, help_text="Previous surgeries and procedures")
    family_medical_history = EncryptedTextField(blank=True, help_text="Relevant family medical history")
    
    # Lifestyle Information (encrypted)
    smoking_status = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('former', 'Former'),
            ('current', 'Current'),
        ],
        default='never'
    )
    alcohol_use = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('occasional', 'Occasional'),
            ('moderate', 'Moderate'),
            ('heavy', 'Heavy'),
        ],
        default='none'
    )
    exercise_frequency = models.CharField(
        max_length=20,
        choices=[
            ('none', 'None'),
            ('rare', 'Rarely'),
            ('weekly', '1-2 times per week'),
            ('regular', '3-4 times per week'),
            ('daily', 'Daily'),
        ],
        blank=True
    )
    
    # Insurance Information (encrypted)
    insurance_provider = EncryptedCharField(max_length=255, blank=True)
    insurance_type = models.CharField(max_length=20, choices=INSURANCE_TYPE_CHOICES, blank=True)
    insurance_policy_number = EncryptedCharField(max_length=100, blank=True)
    insurance_group_number = EncryptedCharField(max_length=100, blank=True)
    
    # Healthcare Preferences
    preferred_language = models.CharField(max_length=50, default='English')
    preferred_communication = models.CharField(
        max_length=20,
        choices=[
            ('phone', 'Phone'),
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('portal', 'Patient Portal'),
        ],
        default='email'
    )
    
    # Privacy and Consent
    hipaa_authorization_signed = models.BooleanField(default=False)
    hipaa_authorization_date = models.DateTimeField(null=True, blank=True)
    marketing_consent = models.BooleanField(default=False)
    research_consent = models.BooleanField(default=False)
    
    # Emergency Contact Notification Preferences
    notify_emergency_contact = models.BooleanField(
        default=True,
        help_text="Send appointment notifications to emergency contact"
    )
    emergency_contact_notification_types = models.JSONField(
        default=default_emergency_notification_types,
        help_text="Types of notifications to send to emergency contact"
    )
    emergency_contact_notification_methods = models.JSONField(
        default=default_emergency_notification_methods,
        help_text="Preferred notification methods for emergency contact (email, sms, phone)"
    )
    
    # Care Team Assignments
    primary_care_physician = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_patients',
        limit_choices_to={'user__role__in': ['physician', 'nurse_practitioner']}
    )
    
    # Account Status
    is_active = models.BooleanField(default=True)
    registration_completed = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_patients'
    )
    
    class Meta:
        db_table = 'enhanced_patients'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date_of_birth']),
            models.Index(fields=['primary_care_physician']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} (DOB: {self.date_of_birth})"
    
    @property
    def age(self):
        """Calculate current age"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def bmi(self):
        """Calculate BMI if height and weight are available"""
        if self.height_inches and self.weight_lbs:
            height_m = self.height_inches * 0.0254
            weight_kg = self.weight_lbs * 0.453592
            return round(weight_kg / (height_m ** 2), 1)
        return None
    
    def clean(self):
        """Validate patient data"""
        super().clean()
        
        # Validate age (must be reasonable)
        if self.date_of_birth:
            age = self.age
            if age < 0 or age > 150:
                raise ValidationError("Invalid date of birth")
        
        # Validate height and weight ranges
        if self.height_inches and (self.height_inches < 12 or self.height_inches > 96):
            raise ValidationError("Height must be between 12 and 96 inches")
        
        if self.weight_lbs and (self.weight_lbs < 1 or self.weight_lbs > 1000):
            raise ValidationError("Weight must be between 1 and 1000 pounds")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class PatientCareTeam(models.Model):
    """Manage patient care team assignments"""
    
    RELATIONSHIP_TYPES = [
        ('primary_care', 'Primary Care Physician'),
        ('specialist', 'Specialist'),
        ('consulting', 'Consulting Physician'),
        ('nurse', 'Primary Nurse'),
        ('therapist', 'Therapist'),
        ('case_manager', 'Case Manager'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(EnhancedPatient, on_delete=models.CASCADE, related_name='care_team')
    staff_member = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.CASCADE,
        related_name='patient_assignments'
    )
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)
    
    # Assignment details
    assigned_date = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='care_team_assignments'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Notes
    assignment_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'patient_care_teams'
        unique_together = ['patient', 'staff_member', 'relationship_type']
        indexes = [
            models.Index(fields=['patient', 'is_active']),
            models.Index(fields=['staff_member', 'is_active']),
            models.Index(fields=['relationship_type']),
        ]
    
    def __str__(self):
        return f"{self.patient.user.full_name} - {self.staff_member.user.full_name} ({self.get_relationship_type_display()})"


class Specialization(models.Model):
    """Medical specializations for healthcare providers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'specializations'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class EnhancedStaffProfile(models.Model):
    """Enhanced Staff Profile with comprehensive professional information"""
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('per_diem', 'Per Diem'),
        ('locum_tenens', 'Locum Tenens'),
        ('inactive', 'Inactive'),
    ]
    
    CREDENTIAL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Renewal'),
    ]
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='staff_members')
    
    # Professional Information
    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members'
    )
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100)
    
    # Credentials and Licensing (encrypted)
    license_number = EncryptedCharField(max_length=100, blank=True)
    license_state = models.CharField(max_length=50, blank=True)
    license_expiration = models.DateField(null=True, blank=True)
    license_status = models.CharField(
        max_length=20,
        choices=CREDENTIAL_STATUS_CHOICES,
        default='active'
    )
    
    # Additional Certifications
    board_certifications = EncryptedJSONField(
        default=list,
        help_text="List of board certifications with expiration dates"
    )
    
    # DEA and NPI (encrypted for security)
    dea_number = EncryptedCharField(max_length=255, blank=True)
    dea_expiration = models.DateField(null=True, blank=True)
    npi_number = EncryptedCharField(max_length=255, blank=True)
    
    # Employment Details
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='full_time'
    )
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    
    # Contact Information (encrypted)
    work_phone = EncryptedCharField(max_length=255, blank=True)
    work_email = models.EmailField(blank=True)
    pager = EncryptedCharField(max_length=255, blank=True)
    
    # Office/Location Information
    office_location = models.CharField(max_length=255, blank=True)
    office_address = EncryptedTextField(blank=True)
    
    # Schedule and Availability
    default_schedule = EncryptedJSONField(
        default=dict,
        help_text="Default weekly schedule"
    )
    
    # Professional Details
    years_experience = models.PositiveIntegerField(null=True, blank=True)
    education = EncryptedTextField(blank=True, help_text="Educational background")
    languages_spoken = models.JSONField(
        default=list,
        help_text="Languages spoken by the staff member"
    )
    
    # Privileges and Access
    hospital_privileges = EncryptedJSONField(
        default=list,
        help_text="Hospital privileges and admitting rights"
    )
    
    # Emergency Contact (encrypted)
    emergency_contact_name = EncryptedCharField(max_length=255, blank=True)
    emergency_contact_relationship = EncryptedCharField(max_length=100, blank=True)
    emergency_contact_phone = EncryptedCharField(max_length=255, blank=True)
    
    # Professional References
    professional_references = EncryptedJSONField(
        default=list,
        help_text="Professional references with contact information"
    )
    
    # Compliance and Training
    background_check_date = models.DateField(null=True, blank=True)
    background_check_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('cleared', 'Cleared'),
            ('flagged', 'Flagged'),
        ],
        blank=True
    )
    
    # Training Records
    hipaa_training_date = models.DateField(null=True, blank=True)
    cpr_certification_date = models.DateField(null=True, blank=True)
    cpr_expiration_date = models.DateField(null=True, blank=True)
    
    # Performance and Reviews
    last_performance_review = models.DateField(null=True, blank=True)
    next_performance_review = models.DateField(null=True, blank=True)
    
    # Account Status
    is_active = models.BooleanField(default=True)
    can_prescribe = models.BooleanField(default=False)
    can_order_tests = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_staff_profiles'
    )
    
    class Meta:
        db_table = 'enhanced_staff_profiles'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['specialization']),
            models.Index(fields=['department']),
            models.Index(fields=['employment_status']),
            models.Index(fields=['license_expiration']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.job_title}"
    
    @property
    def credentials_status(self):
        """Check overall credentials status"""
        today = date.today()
        issues = []
        
        # Check license expiration
        if self.license_expiration and self.license_expiration <= today:
            issues.append('License expired')
        elif self.license_expiration and self.license_expiration <= today + timedelta(days=30):
            issues.append('License expiring soon')
        
        # Check DEA expiration
        if self.dea_expiration and self.dea_expiration <= today:
            issues.append('DEA expired')
        elif self.dea_expiration and self.dea_expiration <= today + timedelta(days=30):
            issues.append('DEA expiring soon')
        
        # Check CPR certification
        if self.cpr_expiration_date and self.cpr_expiration_date <= today:
            issues.append('CPR certification expired')
        
        return {
            'status': 'warning' if issues else 'active',
            'issues': issues
        }
    
    def clean(self):
        """Validate staff profile data"""
        super().clean()
        
        # Validate hire date
        if self.hire_date and self.hire_date > date.today():
            raise ValidationError("Hire date cannot be in the future")
        
        # Validate termination date
        if self.termination_date and self.hire_date and self.termination_date < self.hire_date:
            raise ValidationError("Termination date cannot be before hire date")
        
        # Validate license expiration
        if self.license_expiration and self.license_expiration < date.today() - timedelta(days=365*5):
            raise ValidationError("License expiration date seems too old")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class StaffCredential(models.Model):
    """Track individual staff credentials and certifications"""
    
    CREDENTIAL_TYPES = [
        ('license', 'Professional License'),
        ('certification', 'Board Certification'),
        ('training', 'Training Certificate'),
        ('cme', 'Continuing Medical Education'),
        ('other', 'Other Credential'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff_profile = models.ForeignKey(
        EnhancedStaffProfile,
        on_delete=models.CASCADE,
        related_name='credentials'
    )
    
    # Credential Details
    credential_type = models.CharField(max_length=20, choices=CREDENTIAL_TYPES)
    credential_name = models.CharField(max_length=255)
    issuing_organization = models.CharField(max_length=255)
    
    # Credential Numbers (encrypted)
    credential_number = EncryptedCharField(max_length=100, blank=True)
    
    # Dates
    issue_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('suspended', 'Suspended'),
            ('revoked', 'Revoked'),
        ],
        default='active'
    )
    
    # Verification
    verification_date = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verified_credentials'
    )
    
    # Documentation
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'staff_credentials'
        indexes = [
            models.Index(fields=['staff_profile']),
            models.Index(fields=['credential_type']),
            models.Index(fields=['expiration_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.staff_profile.user.full_name} - {self.credential_name}"
    
    @property
    def is_expiring_soon(self):
        """Check if credential is expiring within 30 days"""
        if not self.expiration_date:
            return False
        return self.expiration_date <= date.today() + timedelta(days=30)
    
    @property
    def is_expired(self):
        """Check if credential is expired"""
        if not self.expiration_date:
            return False
        return self.expiration_date < date.today()


# Export all models
__all__ = [
    'Hospital',
    'HospitalPatient',
    'EnhancedPatient',
    'EnhancedStaffProfile', 
    'Specialization',
    'StaffCredential',
]
