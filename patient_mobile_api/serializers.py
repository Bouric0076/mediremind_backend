"""
Patient Mobile API Serializers
Provides serializers specifically designed for the patient mobile application dashboard
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import EnhancedPatient, Hospital
from appointments.models import Appointment, AppointmentType
from prescriptions.models import Prescription, MedicationReminder
from notifications.models import ScheduledTask

User = get_user_model()


class DashboardAppointmentSerializer(serializers.ModelSerializer):
    """Simplified appointment serializer for dashboard display"""
    doctor_name = serializers.SerializerMethodField()
    hospital_name = serializers.SerializerMethodField()
    appointment_type_name = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()
    formatted_time = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor_name', 'hospital_name', 'appointment_type_name',
            'appointment_date', 'start_time', 'formatted_date', 'formatted_time',
            'status', 'status_display', 'reason', 'can_cancel'
        ]
    
    def get_doctor_name(self, obj):
        return obj.provider.user.full_name if obj.provider and obj.provider.user else "Unknown Doctor"
    
    def get_hospital_name(self, obj):
        return obj.hospital.name if obj.hospital else "Unknown Hospital"
    
    def get_appointment_type_name(self, obj):
        return obj.appointment_type.name if obj.appointment_type else "General Consultation"
    
    def get_formatted_date(self, obj):
        return obj.appointment_date.strftime('%B %d, %Y')
    
    def get_formatted_time(self, obj):
        return obj.start_time.strftime('%I:%M %p')
    
    def get_status_display(self, obj):
        status_map = {
            'scheduled': 'Scheduled',
            'confirmed': 'Confirmed',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'cancelled': 'Cancelled',
            'no_show': 'No Show'
        }
        return status_map.get(obj.status, obj.status.title())
    
    def get_can_cancel(self, obj):
        return obj.status in ['scheduled', 'confirmed'] and obj.appointment_date >= timezone.now().date()


class DashboardMedicationSerializer(serializers.ModelSerializer):
    """Simplified medication serializer for dashboard display"""
    medication_name = serializers.SerializerMethodField()
    next_dose_time = serializers.SerializerMethodField()
    doses_today = serializers.SerializerMethodField()
    dosage = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicationReminder
        fields = [
            'id', 'medication_name', 'dosage', 'frequency',
            'next_dose_time', 'doses_today', 'is_active'
        ]
    
    def get_medication_name(self, obj):
        return obj.prescription.drug.name if obj.prescription and obj.prescription.drug else "Unknown Medication"
    
    def get_dosage(self, obj):
        return obj.prescription.dosage if obj.prescription else "Unknown Dosage"
    
    def get_next_dose_time(self, obj):
        # This would need to be calculated based on the reminder schedule
        # For now, returning a placeholder
        return "08:00 AM"
    
    def get_doses_today(self, obj):
        # Calculate how many doses are scheduled for today
        return len(obj.times) if obj.times else 1


class DashboardNotificationSerializer(serializers.ModelSerializer):
    """Simplified notification serializer for dashboard display"""
    title = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    formatted_time = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduledTask
        fields = ['id', 'title', 'message', 'formatted_time', 'status']
    
    def get_title(self, obj):
        title_map = {
            'reminder': 'Appointment Reminder',
            'confirmation': 'Appointment Confirmation',
            'update': 'Appointment Update',
            'cancellation': 'Appointment Cancelled',
            'no_show': 'Missed Appointment'
        }
        return title_map.get(obj.task_type, 'Notification')
    
    def get_message(self, obj):
        return obj.message_data.get('message', 'You have a notification') if obj.message_data else 'You have a notification'
    
    def get_formatted_time(self, obj):
        return obj.created_at.strftime('%I:%M %p')


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    appointments_today = serializers.IntegerField()
    medications_due = serializers.IntegerField()
    pending_reminders = serializers.IntegerField()
    reports_available = serializers.IntegerField()


class DashboardHealthMetricsSerializer(serializers.Serializer):
    """Serializer for health metrics display"""
    blood_pressure = serializers.CharField(default="120/80")
    heart_rate = serializers.CharField(default="72 bpm")
    weight = serializers.CharField(default="70 kg")
    temperature = serializers.CharField(default="98.6°F")
    last_updated = serializers.DateTimeField(default=timezone.now)


class DashboardServiceSerializer(serializers.Serializer):
    """Serializer for available services"""
    id = serializers.CharField()
    name = serializers.CharField()
    icon = serializers.CharField()
    description = serializers.CharField()
    is_available = serializers.BooleanField(default=True)


class PatientDashboardSerializer(serializers.Serializer):
    """Main dashboard serializer that combines all dashboard data"""
    patient_name = serializers.CharField()
    todays_stats = DashboardStatsSerializer()
    upcoming_appointments = DashboardAppointmentSerializer(many=True)
    current_medications = DashboardMedicationSerializer(many=True)
    recent_notifications = DashboardNotificationSerializer(many=True)
    services = DashboardServiceSerializer(many=True)
    last_updated = serializers.DateTimeField(default=timezone.now)