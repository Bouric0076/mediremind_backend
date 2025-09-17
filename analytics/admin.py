from django.contrib import admin
from .models import (
    SystemMetrics, UserActivity, AppointmentAnalytics,
    RevenueAnalytics, PatientDemographics, SystemPerformance,
    PopularServices
)


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_users', 'active_users', 'new_registrations',
        'total_appointments', 'completed_appointments', 'total_revenue'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['date']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'login_count', 'appointments_booked',
        'appointments_attended', 'last_activity'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['-date', 'user']
    readonly_fields = ['created_at']


@admin.register(AppointmentAnalytics)
class AppointmentAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'department', 'total_appointments', 'completed_appointments',
        'no_show_appointments', 'cancelled_appointments'
    ]
    list_filter = ['date', 'department', 'created_at']
    search_fields = ['department']
    ordering = ['-date', 'department']
    readonly_fields = ['created_at']


@admin.register(RevenueAnalytics)
class RevenueAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'department', 'total_revenue', 'consultation_revenue',
        'procedure_revenue', 'outstanding_payments'
    ]
    list_filter = ['date', 'department', 'created_at']
    search_fields = ['department']
    ordering = ['-date', 'department']
    readonly_fields = ['created_at']


@admin.register(PatientDemographics)
class PatientDemographicsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'age_group', 'gender', 'total_patients',
        'new_patients', 'returning_patients'
    ]
    list_filter = ['date', 'age_group', 'gender', 'created_at']
    search_fields = ['age_group', 'gender']
    ordering = ['-date', 'age_group', 'gender']
    readonly_fields = ['created_at']


@admin.register(SystemPerformance)
class SystemPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'cpu_usage', 'memory_usage', 'disk_usage',
        'active_sessions', 'api_response_time', 'error_count'
    ]
    list_filter = ['timestamp']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']


@admin.register(PopularServices)
class PopularServicesAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'service_name', 'department', 'booking_count',
        'completion_rate', 'average_rating', 'revenue_generated'
    ]
    list_filter = ['date', 'department', 'created_at']
    search_fields = ['service_name', 'department']
    ordering = ['-date', '-booking_count']
    readonly_fields = ['created_at']
