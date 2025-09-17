from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    MedicalRecord, Diagnosis, Medication,
    LabResult, ClinicalNote, MedicalDocument
)


# DiagnosisInline removed - Diagnosis model doesn't have ForeignKey to MedicalRecord


# Prescription model moved to prescriptions app


class LabResultInline(admin.TabularInline):
    """Inline admin for lab results"""
    model = LabResult
    extra = 1
    fields = ('test_name', 'result_value', 'reference_range', 'status')


class ClinicalNoteInline(admin.StackedInline):
    """Inline admin for clinical notes"""
    model = ClinicalNote
    extra = 1
    fields = ('note_type', 'content', 'is_confidential')


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    """Admin interface for MedicalRecord model"""
    
    list_display = (
        'get_patient_name', 'get_provider_name',
        'visit_date', 'record_type', 'chief_complaint', 'is_finalized'
    )
    list_filter = (
        'record_type', 'is_finalized', 'visit_date', 'created_at'
    )
    search_fields = (
        'record_id', 'patient__user__first_name',
        'patient__user__last_name', 'provider__user__first_name',
        'provider__user__last_name', 'chief_complaint'
    )
    ordering = ('-visit_date', '-created_at')
    date_hierarchy = 'visit_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'patient', 'provider', 'record_id', 'visit_date', 'visit_type'
            )
        }),
        ('Visit Details', {
            'fields': (
                'chief_complaint', 'history_of_present_illness',
                'review_of_systems', 'physical_examination'
            )
        }),
        ('Vital Signs', {
            'fields': (
                'temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic',
                'heart_rate', 'respiratory_rate', 'oxygen_saturation', 'weight', 'height'
            )
        }),
        ('Assessment & Plan', {
            'fields': (
                'assessment', 'plan', 'follow_up_instructions'
            )
        }),
        ('Status', {
            'fields': ('is_finalized', 'finalized_at')
        }),
    )
    
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [LabResultInline, ClinicalNoteInline]
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.patient.user.get_full_name() or obj.patient.user.username
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'patient__user__first_name'
    
    def get_provider_name(self, obj):
        """Display provider's full name"""
        return obj.provider.user.get_full_name() or obj.provider.user.username
    get_provider_name.short_description = 'Provider'
    get_provider_name.admin_order_field = 'provider__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'patient__user', 'provider__user'
        )
    
    def save_model(self, request, obj, form, change):
        """Auto-generate record ID if not provided"""
        if not obj.record_id:
            obj.record_id = obj.generate_record_id()
        super().save_model(request, obj, form, change)


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    """Admin interface for Diagnosis model"""
    
    list_display = (
        'icd10_code', 'description', 'category', 'is_active', 'created_at'
    )
    list_filter = (
        'category', 'is_active', 'created_at'
    )
    search_fields = (
        'icd10_code', 'description', 'category'
    )
    ordering = ('icd10_code',)
    
    fieldsets = (
        ('Diagnosis Information', {
            'fields': (
                'icd10_code', 'description', 'category'
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
            )
        }),
    )


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    """Admin interface for Medication model"""
    
    list_display = (
        'name', 'generic_name', 'medication_type', 'drug_class', 'is_active'
    )
    list_filter = (
        'medication_type', 'drug_class', 'is_active', 'created_at'
    )
    search_fields = (
        'name', 'generic_name', 'ndc_number', 'drug_class'
    )
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'generic_name', 'brand_names'
            )
        }),
        ('Classification', {
            'fields': (
                'medication_type', 'drug_class', 'controlled_substance_schedule'
            )
        }),
        ('Formulation', {
            'fields': (
                'active_ingredients', 'strength_options', 'dosage_forms'
            )
        }),
        ('Regulatory', {
            'fields': (
                'ndc_number',
            )
        }),
        ('Clinical Information', {
            'fields': (
                'contraindications', 'warnings', 'side_effects', 'drug_interactions'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


# Prescription admin moved to prescriptions app


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    """Admin interface for LabResult model"""
    
    list_display = (
        'get_patient_name', 'test_name', 'result_value',
        'reference_range', 'status', 'collection_date'
    )
    list_filter = (
        'status', 'collection_date', 'result_date', 'is_abnormal'
    )
    search_fields = (
        'test_name', 'test_code', 'patient__user__first_name',
        'patient__user__last_name'
    )
    ordering = ('-collection_date',)
    
    fieldsets = (
        ('Test Information', {
            'fields': (
                'patient', 'medical_record', 'test_name', 'test_code', 'test_category'
            )
        }),
        ('Results', {
            'fields': (
                'result_value', 'result_unit', 'reference_range',
                'is_abnormal', 'interpretation'
            )
        }),
        ('Dates & Status', {
            'fields': (
                'collection_date', 'result_date', 'status'
            )
        }),
        ('Additional Information', {
            'fields': (
                'lab_name', 'lab_reference_number', 'specimen_type', 'notes'
            ),
            'classes': ('collapse',)
        }),
        ('Staff', {
            'fields': (
                'ordered_by', 'reviewed_by'
            )
        }),
    )
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'patient__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'medical_record__patient__user'
        )


@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    """Admin interface for ClinicalNote model"""
    
    list_display = (
        'get_patient_name', 'note_type', 'get_content_preview',
        'is_confidential', 'created_at'
    )
    list_filter = (
        'note_type', 'is_confidential', 'created_at'
    )
    search_fields = (
        'medical_record__patient__user__first_name',
        'medical_record__patient__user__last_name', 'content'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Note Information', {
            'fields': (
                'medical_record', 'note_type', 'is_confidential'
            )
        }),
        ('Content', {
            'fields': ('content',)
        }),
    )
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.medical_record.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'medical_record__patient__user__first_name'
    
    def get_content_preview(self, obj):
        """Display content preview"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    get_content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'medical_record__patient__user'
        )


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):
    """Admin interface for MedicalDocument model"""
    
    list_display = (
        'get_patient_name', 'document_type', 'title',
        'file_size_display', 'created_at'
    )
    list_filter = (
        'document_type', 'created_at'
    )
    search_fields = (
        'title', 'description', 'medical_record__patient__user__first_name',
        'medical_record__patient__user__last_name'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Document Information', {
            'fields': (
                'medical_record', 'document_type', 'title', 'description'
            )
        }),
        ('File Information', {
            'fields': (
                'file', 'file_size'
            )
        }),
    )
    
    readonly_fields = ('file_size', 'created_at', 'updated_at')
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.medical_record.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'medical_record__patient__user__first_name'
    
    def file_size_display(self, obj):
        """Display file size in human readable format"""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "Unknown"
    file_size_display.short_description = 'File Size'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'medical_record__patient__user'
        )
