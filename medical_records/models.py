from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class MedicalRecord(models.Model):
    """Main medical record for a patient visit or encounter"""
    
    RECORD_TYPE_CHOICES = [
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('procedure', 'Procedure'),
        ('surgery', 'Surgery'),
        ('lab_review', 'Lab Review'),
        ('imaging_review', 'Imaging Review'),
        ('discharge', 'Discharge Summary'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core Relationships
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='medical_records'
    )
    provider = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.CASCADE,
        related_name='medical_records'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_records'
    )
    
    # Record Information
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES)
    visit_date = models.DateTimeField()
    chief_complaint = models.TextField(help_text="Patient's main concern")
    
    # Clinical Assessment
    history_of_present_illness = models.TextField(blank=True)
    review_of_systems = models.JSONField(default=dict, blank=True)
    physical_examination = models.TextField(blank=True)
    
    # Vital Signs
    vital_signs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Blood pressure, heart rate, temperature, etc."
    )
    
    # Assessment and Plan
    assessment = models.TextField(blank=True, help_text="Clinical assessment")
    plan = models.TextField(blank=True, help_text="Treatment plan")
    
    # Diagnoses (ICD-10 codes)
    primary_diagnosis = models.ForeignKey(
        'Diagnosis',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_records'
    )
    secondary_diagnoses = models.ManyToManyField(
        'Diagnosis',
        blank=True,
        related_name='secondary_records'
    )
    
    # Follow-up Instructions
    follow_up_instructions = models.TextField(blank=True)
    next_appointment_recommended = models.BooleanField(default=False)
    next_appointment_timeframe = models.CharField(max_length=100, blank=True)
    
    # Status and Metadata
    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medical_records'
        ordering = ['-visit_date']
        indexes = [
            models.Index(fields=['patient', 'visit_date']),
            models.Index(fields=['provider', 'visit_date']),
            models.Index(fields=['record_type']),
            models.Index(fields=['is_finalized']),
        ]
    
    def __str__(self):
        return f"{self.patient.user.full_name} - {self.record_type} ({self.visit_date.date()})"
    
    def finalize_record(self):
        """Finalize the medical record"""
        self.is_finalized = True
        self.finalized_at = timezone.now()
        self.save()


class Diagnosis(models.Model):
    """ICD-10 diagnosis codes and descriptions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    icd10_code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=500)
    category = models.CharField(max_length=100, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'diagnoses'
        ordering = ['icd10_code']
        indexes = [
            models.Index(fields=['icd10_code']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.icd10_code} - {self.description}"


class Medication(models.Model):
    """Medication database with drug information"""
    
    MEDICATION_TYPE_CHOICES = [
        ('brand', 'Brand Name'),
        ('generic', 'Generic'),
        ('compound', 'Compound'),
        ('otc', 'Over-the-Counter'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_names = models.JSONField(default=list, blank=True)
    
    # Classification
    medication_type = models.CharField(max_length=20, choices=MEDICATION_TYPE_CHOICES)
    drug_class = models.CharField(max_length=100, blank=True)
    controlled_substance_schedule = models.CharField(max_length=10, blank=True)
    
    # Drug Information
    active_ingredients = models.JSONField(default=list, blank=True)
    strength_options = models.JSONField(default=list, blank=True)
    dosage_forms = models.JSONField(default=list, blank=True)
    
    # Safety Information
    contraindications = models.TextField(blank=True)
    warnings = models.TextField(blank=True)
    side_effects = models.JSONField(default=list, blank=True)
    drug_interactions = models.JSONField(default=list, blank=True)
    
    # Metadata
    ndc_number = models.CharField(max_length=20, blank=True, help_text="National Drug Code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medications'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['drug_class']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class LabResult(models.Model):
    """Laboratory test results"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('abnormal', 'Abnormal - Requires Review'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core Relationships
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='lab_results'
    )
    ordered_by = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.CASCADE,
        related_name='ordered_lab_results'
    )
    reviewed_by = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_lab_results'
    )
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_results'
    )
    
    # Test Information
    test_name = models.CharField(max_length=200)
    test_code = models.CharField(max_length=50, blank=True)
    test_category = models.CharField(max_length=100, blank=True)
    
    # Results
    result_value = models.CharField(max_length=200, blank=True)
    result_unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=200, blank=True)
    is_abnormal = models.BooleanField(default=False)
    
    # Additional Information
    specimen_type = models.CharField(max_length=100, blank=True)
    collection_date = models.DateTimeField()
    result_date = models.DateTimeField(null=True, blank=True)
    
    # Status and Notes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    interpretation = models.TextField(blank=True)
    
    # Lab Information
    lab_name = models.CharField(max_length=200, blank=True)
    lab_reference_number = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lab_results'
        ordering = ['-collection_date']
        indexes = [
            models.Index(fields=['patient', 'collection_date']),
            models.Index(fields=['test_name']),
            models.Index(fields=['status']),
            models.Index(fields=['is_abnormal']),
        ]
    
    def __str__(self):
        return f"{self.patient.user.full_name} - {self.test_name} ({self.collection_date.date()})"


class ClinicalNote(models.Model):
    """Clinical notes and documentation"""
    
    NOTE_TYPE_CHOICES = [
        ('progress', 'Progress Note'),
        ('consultation', 'Consultation Note'),
        ('procedure', 'Procedure Note'),
        ('discharge', 'Discharge Note'),
        ('telephone', 'Telephone Note'),
        ('nursing', 'Nursing Note'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core Relationships
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='clinical_notes'
    )
    author = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.CASCADE,
        related_name='clinical_notes'
    )
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clinical_notes'
    )
    
    # Note Information
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Metadata
    note_date = models.DateTimeField()
    is_confidential = models.BooleanField(default=False)
    is_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clinical_notes'
        ordering = ['-note_date']
        indexes = [
            models.Index(fields=['patient', 'note_date']),
            models.Index(fields=['author', 'note_date']),
            models.Index(fields=['note_type']),
            models.Index(fields=['is_signed']),
        ]
    
    def __str__(self):
        return f"{self.patient.user.full_name} - {self.title} ({self.note_date.date()})"
    
    def sign_note(self):
        """Sign the clinical note"""
        self.is_signed = True
        self.signed_at = timezone.now()
        self.save()


class MedicalDocument(models.Model):
    """Medical documents and file attachments"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('lab_report', 'Lab Report'),
        ('imaging', 'Imaging Study'),
        ('pathology', 'Pathology Report'),
        ('consultation_letter', 'Consultation Letter'),
        ('discharge_summary', 'Discharge Summary'),
        ('insurance_form', 'Insurance Form'),
        ('consent_form', 'Consent Form'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Core Relationships
    patient = models.ForeignKey(
        'accounts.EnhancedPatient',
        on_delete=models.CASCADE,
        related_name='medical_documents'
    )
    uploaded_by = models.ForeignKey(
        'accounts.EnhancedStaffProfile',
        on_delete=models.CASCADE,
        related_name='uploaded_documents'
    )
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    
    # Document Information
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # File Information
    file = models.FileField(upload_to='medical_documents/%Y/%m/')
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=50)
    
    # Metadata
    document_date = models.DateField()
    is_confidential = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medical_documents'
        ordering = ['-document_date']
        indexes = [
            models.Index(fields=['patient', 'document_date']),
            models.Index(fields=['document_type']),
            models.Index(fields=['is_confidential']),
        ]
    
    def __str__(self):
        return f"{self.patient.user.full_name} - {self.title} ({self.document_date})"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)
