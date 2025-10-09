from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import uuid


class AppointmentType(models.Model):
    """Different types of appointments (consultation, follow-up, procedure, etc.)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(
        'accounts.Hospital',
        on_delete=models.CASCADE,
        related_name='appointment_types'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=20)
    
    # Duration and Scheduling
    default_duration = models.PositiveIntegerField(
        help_text="Default duration in minutes"
    )
    buffer_time = models.PositiveIntegerField(
        default=0,
        help_text="Buffer time after appointment in minutes"
    )
    
    # Pricing
    base_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Base cost for this appointment type"
    )
    
    # Requirements
    requires_preparation = models.BooleanField(default=False)
    preparation_instructions = models.TextField(blank=True)
    requires_fasting = models.BooleanField(default=False)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    color_code = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Hex color code for calendar display"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointment_types'
        ordering = ['name']
        unique_together = [
            ('hospital', 'name'),
            ('hospital', 'code'),
        ]
        indexes = [
            models.Index(fields=['hospital']),
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class Appointment(models.Model):
    """Enhanced appointment model with comprehensive scheduling features"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('refunded', 'Refunded'),
        ('waived', 'Waived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core Relationships
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    provider = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    hospital = models.ForeignKey(
        'accounts.Hospital',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    appointment_type = models.ForeignKey(
        AppointmentType,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    
    # Scheduling Information
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.PositiveIntegerField(
        help_text="Actual duration in minutes"
    )
    
    # Appointment Details
    title = models.CharField(max_length=255, blank=True)
    reason = models.TextField(help_text="Reason for appointment")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # Status and Priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    # Recurring Appointments
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.JSONField(
        null=True,
        blank=True,
        help_text="Recurrence pattern (frequency, end date, etc.)"
    )
    parent_appointment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recurring_appointments'
    )
    
    # Resource Allocation
    room = models.ForeignKey(
        'Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments'
    )
    equipment_needed = models.ManyToManyField(
        'Equipment',
        blank=True,
        related_name='appointments'
    )
    
    # Financial Information
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Tracking Information
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_appointments'
    )
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    
    # Cancellation Information
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='cancelled_appointments'
    )
    cancellation_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointments'
        indexes = [
            models.Index(fields=['hospital']),
            models.Index(fields=['appointment_date', 'start_time']),
            models.Index(fields=['patient', 'appointment_date']),
            models.Index(fields=['provider', 'appointment_date']),
            models.Index(fields=['hospital', 'appointment_date']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['room', 'appointment_date']),
        ]
        unique_together = [['provider', 'appointment_date', 'start_time']]
    
    def clean(self):
        # Validate hospital consistency
        if self.patient and self.provider and self.hospital:
            if self.patient.hospital != self.hospital:
                raise ValidationError("Patient must belong to the same hospital")
            if self.provider.hospital != self.hospital:
                raise ValidationError("Provider must belong to the same hospital")
        
        # Validate appointment type belongs to the same hospital
        if self.appointment_type and self.hospital:
            if self.appointment_type.hospital != self.hospital:
                raise ValidationError("Appointment type must belong to the same hospital")
        
        # Validate appointment date is not in the past
        if self.appointment_date < timezone.now().date():
            raise ValidationError("Appointment date cannot be in the past")
        
        # Auto-calculate end_time if not provided but duration and start_time are available
        if not self.end_time and self.duration and self.start_time:
            # Calculate end_time from start_time + duration
            start_datetime = timezone.make_aware(timezone.datetime.combine(self.appointment_date, self.start_time))
            end_datetime = start_datetime + timezone.timedelta(minutes=self.duration)
            self.end_time = end_datetime.time()
        
        # If duration is not provided, use appointment type's default duration as fallback
        if not self.duration and self.appointment_type:
            self.duration = self.appointment_type.default_duration
            # Recalculate end_time with the default duration
            if self.start_time:
                start_datetime = timezone.make_aware(timezone.datetime.combine(self.appointment_date, self.start_time))
                end_datetime = start_datetime + timezone.timedelta(minutes=self.duration)
                self.end_time = end_datetime.time()
        
        # Validate appointment times (only if both are set)
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time")
            
            # Validate duration matches time difference
            start_datetime = timezone.make_aware(timezone.datetime.combine(self.appointment_date, self.start_time))
            end_datetime = timezone.make_aware(timezone.datetime.combine(self.appointment_date, self.end_time))
            calculated_duration = int((end_datetime - start_datetime).total_seconds() / 60)
            
            if abs(self.duration - calculated_duration) > 1:  # Allow 1 minute tolerance
                raise ValidationError("Duration must match the time difference")
    
    def save(self, *args, **kwargs):
        # Auto-calculate end_time if not provided but duration and start_time are available
        if not self.end_time and self.duration and self.start_time:
            # Calculate end_time from start_time + duration
            start_datetime = timezone.make_aware(timezone.datetime.combine(self.appointment_date, self.start_time))
            end_datetime = start_datetime + timezone.timedelta(minutes=self.duration)
            self.end_time = end_datetime.time()
        
        # If duration is not provided, use appointment type's default duration as fallback
        if not self.duration and self.appointment_type:
            self.duration = self.appointment_type.default_duration
            # Recalculate end_time with the default duration
            if self.start_time:
                start_datetime = timezone.make_aware(timezone.datetime.combine(self.appointment_date, self.start_time))
                end_datetime = start_datetime + timezone.timedelta(minutes=self.duration)
                self.end_time = end_datetime.time()
        
        # Set estimated cost from appointment type if not provided
        if not self.estimated_cost and self.appointment_type.base_cost:
            self.estimated_cost = self.appointment_type.base_cost
        
        super().save(*args, **kwargs)
        
        # Automatically create or update HospitalPatient relationship
        self._ensure_hospital_patient_relationship()
    
    def __str__(self):
        return f"{self.patient.user.full_name} - {self.provider.user.full_name} ({self.appointment_date} {self.start_time})"
    
    @property
    def is_today(self):
        """Check if appointment is today"""
        return self.appointment_date == timezone.now().date()
    
    @property
    def is_upcoming(self):
        """Check if appointment is upcoming"""
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.start_time)
        )
        return appointment_datetime > now
    
    def _ensure_hospital_patient_relationship(self):
        """Ensure HospitalPatient relationship exists for this appointment"""
        from accounts.models import HospitalPatient
        from django.utils import timezone
        
        # Get or create the hospital-patient relationship
        hospital_patient, created = HospitalPatient.objects.get_or_create(
            hospital=self.hospital,
            patient=self.patient,
            defaults={
                'relationship_type': 'appointment',
                'status': 'active',
                'first_visit_date': timezone.now(),
                'last_visit_date': timezone.now(),
            }
        )
        
        # Update last visit date if relationship already exists
        if not created:
            hospital_patient.update_last_visit(timezone.now())
            
            # Update relationship type to recurring if patient has multiple appointments
            appointment_count = self.patient.appointments.filter(hospital=self.hospital).count()
            if appointment_count > 1 and hospital_patient.relationship_type == 'appointment':
                hospital_patient.relationship_type = 'recurring'
                hospital_patient.save(update_fields=['relationship_type', 'updated_at'])
    
    @property
    def time_until_appointment(self):
        """Get time until appointment"""
        now = timezone.now()
        appointment_datetime = timezone.make_aware(timezone.datetime.combine(self.appointment_date, self.start_time))
        if appointment_datetime > now:
            return appointment_datetime - now
        return None
    
    def can_be_cancelled(self):
        """Check if appointment can be cancelled"""
        return self.status in ['scheduled', 'confirmed'] and self.is_upcoming
    
    def can_be_rescheduled(self):
        """Check if appointment can be rescheduled"""
        return self.status in ['scheduled', 'confirmed'] and self.is_upcoming


class AppointmentWaitlist(models.Model):
    """Waitlist for appointments when preferred slots are not available"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('notified', 'Notified'),
        ('scheduled', 'Scheduled'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core Information
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='waitlist_entries'
    )
    provider = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.CASCADE,
        related_name='waitlist_entries'
    )
    appointment_type = models.ForeignKey(
        AppointmentType,
        on_delete=models.CASCADE,
        related_name='waitlist_entries'
    )
    
    # Preferences
    preferred_date_start = models.DateField()
    preferred_date_end = models.DateField()
    preferred_time_start = models.TimeField(null=True, blank=True)
    preferred_time_end = models.TimeField(null=True, blank=True)
    preferred_days = models.JSONField(
        default=list,
        help_text="Preferred days of week (0=Monday, 6=Sunday)"
    )
    
    # Details
    reason = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=Appointment.PRIORITY_CHOICES,
        default='normal'
    )
    
    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    position = models.PositiveIntegerField(default=1)
    
    # Notification Information
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    response_deadline = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointment_waitlist'
        ordering = ['priority', 'created_at']
        indexes = [
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['preferred_date_start', 'preferred_date_end']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"Waitlist: {self.patient.user.full_name} - {self.provider.user.full_name}"
    
    def is_date_suitable(self, date):
        """Check if a date is suitable for this waitlist entry"""
        if not (self.preferred_date_start <= date <= self.preferred_date_end):
            return False
        
        if self.preferred_days:
            return date.weekday() in self.preferred_days
        
        return True
    
    def is_time_suitable(self, time):
        """Check if a time is suitable for this waitlist entry"""
        if self.preferred_time_start and self.preferred_time_end:
            return self.preferred_time_start <= time <= self.preferred_time_end
        return True


class Room(models.Model):
    """Room/facility resource for appointments"""
    
    ROOM_TYPE_CHOICES = [
        ('consultation', 'Consultation Room'),
        ('examination', 'Examination Room'),
        ('procedure', 'Procedure Room'),
        ('surgery', 'Surgery Room'),
        ('lab', 'Laboratory'),
        ('imaging', 'Imaging Room'),
        ('therapy', 'Therapy Room'),
        ('conference', 'Conference Room'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    
    # Capacity and Features
    capacity = models.PositiveIntegerField(default=1)
    features = models.JSONField(
        default=list,
        help_text="Room features and equipment"
    )
    
    # Location
    floor = models.CharField(max_length=10, blank=True)
    building = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    
    # Metadata
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rooms'
        ordering = ['room_number']
        indexes = [
            models.Index(fields=['room_type']),
            models.Index(fields=['is_active', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.room_number} - {self.name}"


class Equipment(models.Model):
    """Equipment resource for appointments"""
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_order', 'Out of Order'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    equipment_id = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100)
    
    # Details
    manufacturer = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    
    # Status and Location
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    location = models.CharField(max_length=255, blank=True)
    assigned_room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipment'
    )
    
    # Maintenance
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    is_portable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'equipment'
        ordering = ['name']
        indexes = [
            models.Index(fields=['equipment_id']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_room']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.equipment_id})"
    
    @property
    def is_available(self):
        """Check if equipment is available for use"""
        return self.status == 'available'
    
    @property
    def needs_maintenance(self):
        """Check if equipment needs maintenance"""
        if self.next_maintenance:
            return self.next_maintenance <= timezone.now().date()
        return False
