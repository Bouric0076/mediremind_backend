from django.contrib import admin
from .models import (
    EnhancedPatient, EnhancedStaffProfile, Specialization
)


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    """Admin interface for Specialization model"""
    
    list_display = ('name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'category')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(EnhancedPatient)
class EnhancedPatientAdmin(admin.ModelAdmin):
    """Admin interface for EnhancedPatient model"""
    
    list_display = (
        'get_patient_name', 'date_of_birth', 'gender',
        'primary_care_physician', 'is_active'
    )
    list_filter = ('gender', 'is_active', 'created_at')
    search_fields = (
        'user__first_name', 'user__last_name', 'user__email',
        'medical_record_number'
    )
    ordering = ('user__last_name', 'user__first_name')
    
    def get_patient_name(self, obj):
        return obj.user.get_full_name()
    get_patient_name.short_description = 'Patient Name'
    get_patient_name.admin_order_field = 'user__first_name'


@admin.register(EnhancedStaffProfile)
class EnhancedStaffProfileAdmin(admin.ModelAdmin):
    """Admin interface for EnhancedStaffProfile model"""
    
    list_display = (
        'get_staff_name', 'job_title', 'specialization',
        'department', 'employment_status'
    )
    list_filter = ('employment_status', 'specialization', 'department')
    search_fields = (
        'user__first_name', 'user__last_name', 'user__email',
        'job_title', 'department'
    )
    ordering = ('user__last_name', 'user__first_name')
    
    def get_staff_name(self, obj):
        return obj.user.get_full_name()
    get_staff_name.short_description = 'Staff Name'
    get_staff_name.admin_order_field = 'user__first_name'
