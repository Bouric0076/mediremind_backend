from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid


class DrugCategory(models.Model):
    """Categories for medications (e.g., Antibiotics, Analgesics, etc.)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=20, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drug_categories'
        ordering = ['name']
        verbose_name_plural = 'Drug Categories'
    
    def __str__(self):
        return self.name


class Drug(models.Model):
    """Master drug/medication database"""
    
    FORM_CHOICES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('liquid', 'Liquid/Syrup'),
        ('injection', 'Injection'),
        ('cream', 'Cream/Ointment'),
        ('drops', 'Drops'),
        ('inhaler', 'Inhaler'),
        ('patch', 'Patch'),
        ('suppository', 'Suppository'),
    ]
    
    SCHEDULE_CHOICES = [
        ('otc', 'Over-the-Counter'),
        ('rx', 'Prescription'),
        ('controlled_1', 'Schedule I'),
        ('controlled_2', 'Schedule II'),
        ('controlled_3', 'Schedule III'),
        ('controlled_4', 'Schedule IV'),
        ('controlled_5', 'Schedule V'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255)
    brand_names = models.JSONField(default=list, help_text="List of brand names")
    
    # Classification
    category = models.ForeignKey(
        DrugCategory,
        on_delete=models.CASCADE,
        related_name='drugs'
    )
    drug_class = models.CharField(max_length=100, blank=True)
    
    # Physical Properties
    form = models.CharField(max_length=20, choices=FORM_CHOICES)
    strength = models.CharField(max_length=50, help_text="e.g., 500mg, 10mg/ml")
    unit = models.CharField(max_length=20, help_text="mg, ml, units, etc.")
    
    # Regulatory
    ndc_number = models.CharField(max_length=20, blank=True, help_text="National Drug Code")
    schedule = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='rx')
    
    # Clinical Information
    indications = models.TextField(help_text="What the drug is used for")
    contraindications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    warnings = models.TextField(blank=True)
    
    # Dosing Information
    usual_adult_dose = models.TextField(blank=True)
    usual_pediatric_dose = models.TextField(blank=True)
    max_daily_dose = models.CharField(max_length=100, blank=True)
    
    # Storage and Handling
    storage_requirements = models.TextField(blank=True)
    shelf_life_months = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_formulary = models.BooleanField(default=True, help_text="Available in formulary")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drugs'
        ordering = ['generic_name']
        indexes = [
            models.Index(fields=['generic_name']),
            models.Index(fields=['category']),
            models.Index(fields=['schedule']),
            models.Index(fields=['is_active', 'is_formulary']),
        ]
    
    def __str__(self):
        return f"{self.generic_name} ({self.strength})"


class DrugInteraction(models.Model):
    """Drug-drug interactions"""
    
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('contraindicated', 'Contraindicated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    drug_1 = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name='interactions_as_drug1'
    )
    drug_2 = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name='interactions_as_drug2'
    )
    
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    mechanism = models.TextField(blank=True)
    management = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drug_interactions'
        unique_together = [['drug_1', 'drug_2']]
        indexes = [
            models.Index(fields=['severity']),
            models.Index(fields=['is_active']),
        ]
    
    def clean(self):
        if self.drug_1 == self.drug_2:
            raise ValidationError("A drug cannot interact with itself")
    
    def __str__(self):
        return f"{self.drug_1.generic_name} + {self.drug_2.generic_name} ({self.severity})"


class Prescription(models.Model):
    """Prescription orders from healthcare providers"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('discontinued', 'Discontinued'),
    ]
    
    PRIORITY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription_number = models.CharField(max_length=50, unique=True)
    
    # Relationships
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='prescription_orders'
    )
    prescriber = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.CASCADE,
        related_name='prescription_orders'
    )
    drug = models.ForeignKey(
        Drug,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    
    # Prescription Details
    dosage = models.CharField(max_length=100, help_text="e.g., 500mg")
    frequency = models.CharField(max_length=100, help_text="e.g., twice daily, every 8 hours")
    route = models.CharField(max_length=50, help_text="e.g., oral, IV, topical")
    duration = models.CharField(max_length=100, help_text="e.g., 7 days, 2 weeks")
    
    # Quantity and Refills
    quantity = models.PositiveIntegerField(help_text="Number of units to dispense")
    refills_allowed = models.PositiveIntegerField(default=0)
    refills_remaining = models.PositiveIntegerField(default=0)
    
    # Instructions
    sig = models.TextField(help_text="Directions for use (Sig)")
    indication = models.CharField(max_length=255, blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='routine')
    
    prescribed_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Pharmacy Information
    pharmacy = models.CharField(max_length=255, blank=True)
    pharmacy_phone = models.CharField(max_length=20, blank=True)
    
    # Clinical Information
    diagnosis_code = models.CharField(max_length=20, blank=True, help_text="ICD-10 code")
    
    # Flags
    is_generic_allowed = models.BooleanField(default=True)
    is_controlled_substance = models.BooleanField(default=False)
    requires_monitoring = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prescription_orders'
        ordering = ['-prescribed_date']
        indexes = [
            models.Index(fields=['prescription_number']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['prescriber', 'prescribed_date']),
            models.Index(fields=['drug', 'status']),
            models.Index(fields=['status', 'prescribed_date']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()
        
        if not self.refills_remaining:
            self.refills_remaining = self.refills_allowed
        
        super().save(*args, **kwargs)
    
    def generate_prescription_number(self):
        """Generate unique prescription number"""
        import random
        import string
        
        prefix = 'RX'
        timestamp = timezone.now().strftime('%Y%m%d')
        random_suffix = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{timestamp}{random_suffix}"
    
    def __str__(self):
        return f"{self.prescription_number} - {self.patient.user.full_name} - {self.drug.generic_name}"
    
    @property
    def is_active(self):
        """Check if prescription is currently active"""
        return self.status == 'active' and (not self.end_date or self.end_date >= timezone.now().date())
    
    @property
    def days_remaining(self):
        """Calculate days remaining in prescription"""
        if self.end_date:
            remaining = (self.end_date - timezone.now().date()).days
            return max(0, remaining)
        return None
    
    def can_refill(self):
        """Check if prescription can be refilled"""
        return self.refills_remaining > 0 and self.status == 'active'


class PrescriptionFill(models.Model):
    """Record of prescription fills/dispensing"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('filled', 'Filled'),
        ('partial', 'Partially Filled'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='fills'
    )
    
    # Fill Details
    fill_number = models.PositiveIntegerField(default=1)
    quantity_dispensed = models.PositiveIntegerField()
    days_supply = models.PositiveIntegerField()
    
    # Dates
    fill_date = models.DateTimeField(default=timezone.now)
    pickup_date = models.DateTimeField(null=True, blank=True)
    
    # Pharmacy Information
    pharmacy_name = models.CharField(max_length=255)
    pharmacist_name = models.CharField(max_length=255, blank=True)
    lot_number = models.CharField(max_length=50, blank=True)
    
    # Financial
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    copay = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prescription_fills'
        ordering = ['-fill_date']
        unique_together = [['prescription', 'fill_number']]
        indexes = [
            models.Index(fields=['prescription', 'fill_date']),
            models.Index(fields=['status', 'fill_date']),
        ]
    
    def __str__(self):
        return f"Fill #{self.fill_number} - {self.prescription.prescription_number}"


class MedicationAdherence(models.Model):
    """Track patient medication adherence"""
    
    ADHERENCE_CHOICES = [
        ('excellent', 'Excellent (>95%)'),
        ('good', 'Good (80-95%)'),
        ('fair', 'Fair (60-79%)'),
        ('poor', 'Poor (<60%)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='adherence_records'
    )
    
    # Adherence Metrics
    period_start = models.DateField()
    period_end = models.DateField()
    doses_prescribed = models.PositiveIntegerField()
    doses_taken = models.PositiveIntegerField()
    adherence_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    adherence_rating = models.CharField(max_length=20, choices=ADHERENCE_CHOICES)
    
    # Tracking Method
    tracking_method = models.CharField(
        max_length=50,
        choices=[
            ('self_report', 'Self Report'),
            ('pill_count', 'Pill Count'),
            ('pharmacy_refill', 'Pharmacy Refill'),
            ('electronic_monitor', 'Electronic Monitor'),
        ]
    )
    
    # Barriers and Notes
    missed_dose_reasons = models.JSONField(
        default=list,
        help_text="Reasons for missed doses"
    )
    notes = models.TextField(blank=True)
    
    # Metadata
    recorded_by = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='adherence_assessments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medication_adherence'
        ordering = ['-period_end']
        indexes = [
            models.Index(fields=['prescription', 'period_end']),
            models.Index(fields=['adherence_rating']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate adherence percentage
        if self.doses_prescribed > 0:
            self.adherence_percentage = (self.doses_taken / self.doses_prescribed) * 100
        
        # Set adherence rating based on percentage
        if self.adherence_percentage >= 95:
            self.adherence_rating = 'excellent'
        elif self.adherence_percentage >= 80:
            self.adherence_rating = 'good'
        elif self.adherence_percentage >= 60:
            self.adherence_rating = 'fair'
        else:
            self.adherence_rating = 'poor'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.prescription.patient.user.full_name} - {self.adherence_percentage}% ({self.period_start} to {self.period_end})"


class MedicationReminder(models.Model):
    """Medication reminders for patients"""
    
    FREQUENCY_CHOICES = [
        ('once_daily', 'Once Daily'),
        ('twice_daily', 'Twice Daily'),
        ('three_times_daily', 'Three Times Daily'),
        ('four_times_daily', 'Four Times Daily'),
        ('every_4_hours', 'Every 4 Hours'),
        ('every_6_hours', 'Every 6 Hours'),
        ('every_8_hours', 'Every 8 Hours'),
        ('every_12_hours', 'Every 12 Hours'),
        ('as_needed', 'As Needed'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    
    # Reminder Settings
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    times = models.JSONField(
        default=list,
        help_text="List of times for reminders (HH:MM format)"
    )
    
    # Notification Preferences
    send_sms = models.BooleanField(default=False)
    send_email = models.BooleanField(default=True)
    send_push = models.BooleanField(default=True)
    
    # Advanced Settings
    advance_notice_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Minutes before dose time to send reminder"
    )
    snooze_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Snooze duration in minutes"
    )
    max_snoozes = models.PositiveIntegerField(
        default=3,
        help_text="Maximum number of snoozes allowed"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medication_reminders'
        indexes = [
            models.Index(fields=['prescription', 'is_active']),
            models.Index(fields=['frequency']),
        ]
    
    def __str__(self):
        return f"Reminder: {self.prescription.drug.generic_name} - {self.frequency}"


class PharmacyPartner(models.Model):
    """Partner pharmacies for prescription fulfillment"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=255)
    chain_name = models.CharField(max_length=255, blank=True)
    license_number = models.CharField(max_length=50, unique=True)
    
    # Contact Information
    phone = models.CharField(max_length=20)
    fax = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    
    # Services
    accepts_insurance = models.BooleanField(default=True)
    delivery_available = models.BooleanField(default=False)
    accepts_electronic_prescriptions = models.BooleanField(default=True)
    
    # Hours
    hours_of_operation = models.JSONField(
        default=dict,
        help_text="Operating hours by day of week"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_preferred = models.BooleanField(default=False)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pharmacy_partners'
        ordering = ['name']
        indexes = [
            models.Index(fields=['license_number']),
            models.Index(fields=['is_active', 'is_preferred']),
            models.Index(fields=['city', 'state']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def full_address(self):
        """Get formatted full address"""
        address_parts = [self.address_line1]
        if self.address_line2:
            address_parts.append(self.address_line2)
        address_parts.append(f"{self.city}, {self.state} {self.zip_code}")
        return ", ".join(address_parts)
