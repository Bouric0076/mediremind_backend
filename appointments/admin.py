from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q
from .models import AppointmentType, Appointment, AppointmentWaitlist, Room, Equipment


@admin.register(AppointmentType)
class AppointmentTypeAdmin(admin.ModelAdmin):
    """Admin interface for AppointmentType model"""
    
    list_display = (
        'name', 'default_duration', 'base_cost', 'is_active'
    )
    list_filter = (
        'is_active',
    )
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'description', 'category', 'duration_minutes'
            )
        }),
        ('Cost & Requirements', {
            'fields': (
                'base_cost', 'requires_referral', 'requires_fasting',
                'requires_preparation', 'preparation_instructions'
            )
        }),
        ('Availability', {
            'fields': (
                'is_telehealth_available', 'is_active'
            )
        }),
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin interface for Appointment model"""
    
    list_display = (
        'get_patient_name', 'get_provider_name',
        'appointment_type', 'appointment_date', 'start_time',
        'status', 'priority', 'payment_status'
    )
    list_filter = (
        'status', 'priority', 'payment_status',
        'appointment_date', 'created_at'
    )
    search_fields = (
        'appointment_id', 'patient__user__first_name',
        'patient__user__last_name', 'provider__user__first_name',
        'provider__user__last_name', 'chief_complaint'
    )
    ordering = ('-appointment_date', '-start_time')
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'patient', 'provider', 'appointment_type', 'appointment_id'
            )
        }),
        ('Scheduling', {
            'fields': (
                'appointment_date', 'start_time', 'end_time',
                'is_telehealth', 'telehealth_link'
            )
        }),
        ('Status & Priority', {
            'fields': (
                'status', 'priority', 'chief_complaint', 'notes'
            )
        }),
        ('Recurrence', {
            'fields': (
                'is_recurring', 'recurrence_pattern', 'recurrence_end_date',
                'parent_appointment'
            ),
            'classes': ('collapse',)
        }),
        ('Resources', {
            'fields': (
                'room', 'equipment_needed'
            ),
            'classes': ('collapse',)
        }),
        ('Financial', {
            'fields': (
                'estimated_cost', 'actual_cost', 'payment_status',
                'insurance_authorization_code'
            ),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': (
                'checked_in_at', 'started_at', 'completed_at',
                'cancelled_at', 'cancellation_reason', 'cancelled_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'id', 'created_at', 'updated_at'
    )
    filter_horizontal = ('equipment_needed',)
    
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
            'patient__user', 'provider__user', 'appointment_type', 'room'
        ).prefetch_related('equipment_needed')
    
    def save_model(self, request, obj, form, change):
        """Auto-generate appointment ID if not provided"""
        if not obj.appointment_id:
            obj.appointment_id = obj.generate_appointment_id()
        super().save_model(request, obj, form, change)


@admin.register(AppointmentWaitlist)
class AppointmentWaitlistAdmin(admin.ModelAdmin):
    """Admin interface for AppointmentWaitlist model"""
    
    list_display = (
        'get_patient_name', 'get_provider_name', 'appointment_type',
        'preferred_date_start', 'priority', 'status'
    )
    list_filter = (
        'status', 'priority', 'appointment_type',
        'preferred_date_start', 'created_at'
    )
    search_fields = (
        'patient__user__first_name', 'patient__user__last_name',
        'provider__user__first_name', 'provider__user__last_name',
        'reason'
    )
    ordering = ('-priority', 'created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'patient', 'provider', 'appointment_type', 'reason'
            )
        }),
        ('Preferences', {
            'fields': (
                'preferred_date', 'preferred_time', 'preferred_date_range_start',
                'preferred_date_range_end', 'preferred_days_of_week',
                'preferred_time_range_start', 'preferred_time_range_end'
            )
        }),
        ('Status & Priority', {
            'fields': (
                'priority', 'status', 'notes'
            )
        }),
        ('Notifications', {
            'fields': (
                'notification_sent_at', 'notification_response_deadline'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'notification_sent_at')
    
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
            'patient__user', 'provider__user', 'appointment_type'
        )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin interface for Room model"""
    
    list_display = (
        'name', 'room_number', 'room_type', 'capacity',
        'floor', 'building', 'is_active'
    )
    list_filter = ('room_type', 'is_active', 'floor', 'building')
    search_fields = ('name', 'room_number', 'description')
    ordering = ('building', 'floor', 'room_number')
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'room_number', 'room_type', 'description'
            )
        }),
        ('Capacity & Features', {
            'fields': (
                'capacity', 'features'
            )
        }),
        ('Location', {
            'fields': (
                'floor', 'building', 'location_notes'
            )
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """Admin interface for Equipment model"""
    
    list_display = (
        'name', 'equipment_id', 'category', 'manufacturer',
        'location', 'status'
    )
    list_filter = (
        'category', 'status', 'manufacturer',
        'last_maintenance', 'next_maintenance'
    )
    search_fields = (
        'name', 'equipment_id', 'manufacturer', 'model',
        'serial_number', 'description'
    )
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'equipment_id', 'category', 'description'
            )
        }),
        ('Manufacturer Details', {
            'fields': (
                'manufacturer', 'model', 'serial_number',
                'purchase_date', 'warranty_expiry_date'
            )
        }),
        ('Location & Status', {
            'fields': (
                'current_location', 'status'
            )
        }),
        ('Maintenance', {
            'fields': (
                'last_maintenance_date', 'next_maintenance_date',
                'maintenance_notes'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('equipment_id',)
    
    def save_model(self, request, obj, form, change):
        """Auto-generate equipment ID if not provided"""
        if not obj.equipment_id:
            obj.equipment_id = obj.generate_equipment_id()
        super().save_model(request, obj, form, change)
