from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from .models import (
    DrugCategory, Drug, DrugInteraction, Prescription,
    PrescriptionFill, MedicationAdherence, MedicationReminder,
    PharmacyPartner
)


class DrugInteractionInline(admin.TabularInline):
    """Inline admin for drug interactions"""
    model = DrugInteraction
    fk_name = 'drug_1'
    extra = 0
    fields = ('drug_2', 'severity', 'description', 'is_active')


class PrescriptionFillInline(admin.TabularInline):
    """Inline admin for prescription fills"""
    model = PrescriptionFill
    extra = 0
    fields = (
        'fill_number', 'quantity_dispensed', 'days_supply',
        'fill_date', 'pharmacy', 'status'
    )
    readonly_fields = ('fill_number',)


class MedicationReminderInline(admin.TabularInline):
    """Inline admin for medication reminders"""
    model = MedicationReminder
    extra = 0
    fields = (
        'reminder_time', 'frequency', 'is_active', 'notification_method'
    )


@admin.register(DrugCategory)
class DrugCategoryAdmin(admin.ModelAdmin):
    """Admin interface for DrugCategory model"""
    
    list_display = ('name', 'code', 'description')
    list_filter = ('created_at',)
    search_fields = ('name', 'code', 'description')
    ordering = ('name',)
    
    fieldsets = (
        ('Category Information', {
            'fields': (
                'name', 'code', 'description', 'parent'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    """Admin interface for Drug model"""
    
    list_display = (
        'name', 'generic_name', 'strength', 'form',
        'category', 'is_active'
    )
    list_filter = (
        'category', 'form', 'schedule', 'is_active'
    )
    search_fields = (
        'name', 'generic_name', 'manufacturer', 'ndc_number'
    )
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'generic_name', 'category', 'description'
            )
        }),
        ('Classification', {
            'fields': (
                'therapeutic_class', 'pharmacologic_class',
                'controlled_substance_schedule'
            )
        }),
        ('Physical Properties', {
            'fields': (
                'strength', 'dosage_form', 'route_of_administration',
                'color', 'shape', 'imprint'
            )
        }),
        ('Regulatory', {
            'fields': (
                'ndc_number', 'manufacturer', 'fda_approval_date',
                'requires_prescription', 'is_controlled_substance'
            )
        }),
        ('Clinical Information', {
            'fields': (
                'indications', 'contraindications', 'side_effects',
                'warnings', 'drug_interactions'
            ),
            'classes': ('collapse',)
        }),
        ('Dosing', {
            'fields': (
                'usual_adult_dose', 'usual_pediatric_dose',
                'maximum_daily_dose'
            ),
            'classes': ('collapse',)
        }),
        ('Storage & Status', {
            'fields': (
                'storage_requirements', 'shelf_life', 'is_active'
            )
        }),
    )
    
    inlines = [DrugInteractionInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


@admin.register(DrugInteraction)
class DrugInteractionAdmin(admin.ModelAdmin):
    """Admin interface for DrugInteraction model"""
    
    list_display = (
        'get_drug_1_name', 'get_drug_2_name', 'severity',
        'description', 'is_active'
    )
    list_filter = ('severity', 'is_active')
    search_fields = (
        'drug_1__name', 'drug_2__name', 'description'
    )
    ordering = ('drug_1__name', 'drug_2__name')
    
    fieldsets = (
        ('Drugs', {
            'fields': ('drug_1', 'drug_2')
        }),
        ('Interaction Details', {
            'fields': (
                'severity', 'interaction_type', 'description',
                'mechanism', 'clinical_effects'
            )
        }),
        ('Management', {
            'fields': (
                'management_strategy', 'monitoring_requirements'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def get_drug_1_name(self, obj):
        """Display first drug name"""
        return obj.drug_1.name
    get_drug_1_name.short_description = 'Drug 1'
    get_drug_1_name.admin_order_field = 'drug_1__name'
    
    def get_drug_2_name(self, obj):
        """Display second drug name"""
        return obj.drug_2.name
    get_drug_2_name.short_description = 'Drug 2'
    get_drug_2_name.admin_order_field = 'drug_2__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'drug_a', 'drug_b'
        )


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """Admin interface for Prescription model"""
    
    list_display = (
        'prescription_number', 'get_patient_name', 'get_prescriber_name',
        'get_drug_name', 'quantity', 'status', 'prescribed_date'
    )
    list_filter = (
        'status', 'prescribed_date', 'end_date',
        'is_generic_allowed'
    )
    search_fields = (
        'prescription_number', 'patient__user__first_name',
        'patient__user__last_name', 'prescriber__user__first_name',
        'prescriber__user__last_name', 'drug__name'
    )
    ordering = ('-prescribed_date',)
    date_hierarchy = 'prescribed_date'
    
    fieldsets = (
        ('Prescription Information', {
            'fields': (
                'patient', 'prescriber', 'drug', 'prescription_number'
            )
        }),
        ('Dosage & Instructions', {
            'fields': (
                'dosage', 'route', 'quantity',
                'duration', 'sig', 'frequency'
            )
        }),
        ('Refills & Substitution', {
            'fields': (
                'refills_allowed', 'refills_remaining',
                'is_generic_allowed'
            )
        }),
        ('Dates', {
            'fields': (
                'prescribed_date', 'start_date', 'end_date'
            )
        }),
        ('Clinical Information', {
            'fields': (
                'diagnosis_code', 'indication', 'special_instructions'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )
    
    readonly_fields = (
        'prescription_number', 'created_at', 'updated_at'
    )
    inlines = [PrescriptionFillInline, MedicationReminderInline]
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.patient.user.get_full_name() or obj.patient.user.username
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'patient__user__first_name'
    
    def get_prescriber_name(self, obj):
        """Display prescriber's full name"""
        return obj.prescriber.user.get_full_name() or obj.prescriber.user.username
    get_prescriber_name.short_description = 'Prescriber'
    get_prescriber_name.admin_order_field = 'prescriber__user__first_name'
    
    def get_drug_name(self, obj):
        """Display drug name"""
        return obj.drug.name
    get_drug_name.short_description = 'Drug'
    get_drug_name.admin_order_field = 'drug__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'patient__user', 'prescriber__user', 'drug'
        )
    
    def save_model(self, request, obj, form, change):
        """Auto-generate prescription number if not provided"""
        if not obj.prescription_number:
            obj.prescription_number = obj.generate_prescription_number()
        super().save_model(request, obj, form, change)


@admin.register(PrescriptionFill)
class PrescriptionFillAdmin(admin.ModelAdmin):
    """Admin interface for PrescriptionFill model"""
    
    list_display = (
        'get_prescription_number', 'get_patient_name', 'fill_number',
        'quantity_dispensed', 'fill_date', 'pharmacy_name', 'status'
    )
    list_filter = (
        'status', 'fill_date'
    )
    search_fields = (
        'prescription__prescription_number',
        'prescription__patient__user__first_name',
        'prescription__patient__user__last_name',
        'pharmacy_name', 'pharmacist_name'
    )
    ordering = ('-fill_date',)
    
    fieldsets = (
        ('Fill Information', {
            'fields': (
                'prescription', 'fill_number', 'quantity_dispensed',
                'days_supply', 'fill_date'
            )
        }),
        ('Pharmacy Details', {
            'fields': (
                'pharmacy', 'pharmacist_name', 'pharmacist_license'
            )
        }),
        ('Costs', {
            'fields': (
                'cost_to_patient', 'insurance_copay', 'total_cost'
            )
        }),
        ('Status & Notes', {
            'fields': (
                'status', 'notes'
            )
        }),
    )
    
    readonly_fields = ('fill_number',)
    
    def get_prescription_number(self, obj):
        """Display prescription number"""
        return obj.prescription.prescription_number
    get_prescription_number.short_description = 'Prescription Number'
    get_prescription_number.admin_order_field = 'prescription__prescription_number'
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.prescription.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'prescription__patient__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'prescription__patient__user', 'pharmacy'
        )


@admin.register(MedicationAdherence)
class MedicationAdherenceAdmin(admin.ModelAdmin):
    """Admin interface for MedicationAdherence model"""
    
    list_display = (
        'get_prescription_number', 'get_patient_name', 'tracking_period',
        'doses_taken', 'doses_prescribed', 'adherence_percentage', 'adherence_rating'
    )
    list_filter = (
        'adherence_rating', 'period_start', 'period_end'
    )
    search_fields = (
        'prescription__prescription_number',
        'prescription__patient__user__first_name',
        'prescription__patient__user__last_name'
    )
    ordering = ('-period_start',)
    
    fieldsets = (
        ('Tracking Information', {
            'fields': (
                'prescription', 'period_start', 'period_end'
            )
        }),
        ('Adherence Data', {
            'fields': (
                'doses_taken', 'doses_prescribed', 'adherence_percentage', 'adherence_rating'
            )
        }),
        ('Additional Information', {
            'fields': (
                'notes', 'assessed_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('adherence_percentage', 'adherence_rating')
    
    def get_prescription_number(self, obj):
        """Display prescription number"""
        return obj.prescription.prescription_number
    get_prescription_number.short_description = 'Prescription Number'
    get_prescription_number.admin_order_field = 'prescription__prescription_number'
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.prescription.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'prescription__patient__user__first_name'
    
    def tracking_period(self, obj):
        """Display tracking period"""
        return f"{obj.period_start} to {obj.period_end}"
    tracking_period.short_description = 'Tracking Period'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'prescription__patient__user'
        )


@admin.register(MedicationReminder)
class MedicationReminderAdmin(admin.ModelAdmin):
    """Admin interface for MedicationReminder model"""
    
    list_display = (
        'get_prescription_number', 'get_patient_name', 'frequency',
        'send_sms', 'send_email', 'is_active'
    )
    list_filter = (
        'frequency', 'send_sms', 'send_email', 'is_active'
    )
    search_fields = (
        'prescription__prescription_number',
        'prescription__patient__user__first_name',
        'prescription__patient__user__last_name'
    )
    ordering = ('frequency',)
    
    fieldsets = (
        ('Reminder Information', {
            'fields': (
                'prescription', 'frequency', 'times'
            )
        }),
        ('Notification Settings', {
            'fields': (
                'send_sms', 'send_email', 'send_push'
            )
        }),
        ('Advanced Settings', {
            'fields': (
                'advance_notice_minutes', 'snooze_minutes', 'max_snoozes'
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
            )
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_prescription_number(self, obj):
        """Display prescription number"""
        return obj.prescription.prescription_number
    get_prescription_number.short_description = 'Prescription Number'
    get_prescription_number.admin_order_field = 'prescription__prescription_number'
    
    def get_patient_name(self, obj):
        """Display patient's full name"""
        return obj.prescription.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'prescription__patient__user__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'prescription__patient__user'
        )


@admin.register(PharmacyPartner)
class PharmacyPartnerAdmin(admin.ModelAdmin):
    """Admin interface for PharmacyPartner model"""
    
    list_display = (
        'name', 'chain_name', 'phone', 'is_active',
        'accepts_insurance', 'delivery_available'
    )
    list_filter = (
        'is_active', 'accepts_insurance', 'delivery_available'
    )
    search_fields = (
        'name', 'license_number', 'phone', 'email',
        'address_line1', 'city'
    )
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'chain_name', 'license_number'
            )
        }),
        ('Contact Information', {
            'fields': (
                'phone', 'fax', 'email', 'website'
            )
        }),
        ('Address', {
            'fields': (
                'address_line1', 'address_line2', 'city', 'state', 'zip_code'
            )
        }),
        ('Services', {
            'fields': (
                'accepts_insurance', 'delivery_available',
                'accepts_electronic_prescriptions'
            )
        }),
        ('Hours', {
            'fields': (
                'monday_hours', 'tuesday_hours', 'wednesday_hours',
                'thursday_hours', 'friday_hours', 'saturday_hours',
                'sunday_hours'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
