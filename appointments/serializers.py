"""
Django REST Framework Serializers for Appointment Management System
Provides comprehensive serialization for all appointment-related models
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import EnhancedPatient, EnhancedStaffProfile
from .models import AppointmentType, Appointment, AppointmentWaitlist, Room, Equipment

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information serializer"""
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'full_name']
        read_only_fields = ['id']
    
    def get_first_name(self, obj):
        # Extract first name from full_name field
        if obj.full_name:
            return obj.full_name.split()[0] if obj.full_name.split() else ""
        return ""
    
    def get_last_name(self, obj):
        # Extract last name from full_name field
        if obj.full_name:
            parts = obj.full_name.split()
            return " ".join(parts[1:]) if len(parts) > 1 else ""
        return ""


class PatientBasicSerializer(serializers.ModelSerializer):
    """Basic patient information serializer"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = EnhancedPatient
        fields = ['id', 'user', 'phone', 'date_of_birth', 'emergency_contact_name', 'emergency_contact_phone']
        read_only_fields = ['id']


class ProviderBasicSerializer(serializers.ModelSerializer):
    """Basic provider information serializer"""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = EnhancedStaffProfile
        fields = ['id', 'user', 'specialization', 'license_number', 'department']
        read_only_fields = ['id']


class AppointmentTypeSerializer(serializers.ModelSerializer):
    """Serializer for AppointmentType model"""
    
    class Meta:
        model = AppointmentType
        fields = [
            'id', 'name', 'description', 'code', 'default_duration',
            'buffer_time', 'base_cost', 'requires_preparation',
            'preparation_instructions', 'requires_fasting', 'is_active',
            'color_code', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_default_duration(self, value):
        """Validate appointment duration"""
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than 0 minutes")
        if value > 480:  # 8 hours max
            raise serializers.ValidationError("Duration cannot exceed 8 hours")
        return value
    
    def validate_base_cost(self, value):
        """Validate base cost"""
        if value < 0:
            raise serializers.ValidationError("Base cost cannot be negative")
        return value


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room model"""
    
    class Meta:
        model = Room
        fields = [
            'id', 'name', 'room_number', 'room_type', 'capacity', 'features',
            'floor', 'building', 'is_active', 'is_available', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EquipmentSerializer(serializers.ModelSerializer):
    """Serializer for Equipment model"""
    assigned_room = serializers.StringRelatedField(read_only=True)
    is_available = serializers.ReadOnlyField()
    needs_maintenance = serializers.ReadOnlyField()
    
    class Meta:
        model = Equipment
        fields = [
            'id', 'name', 'equipment_id', 'category', 'manufacturer',
            'model', 'serial_number', 'status', 'location', 'assigned_room',
            'last_maintenance', 'next_maintenance', 'description', 'is_portable',
            'is_available', 'needs_maintenance', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_available', 'needs_maintenance', 'created_at', 'updated_at']


class AppointmentSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for Appointment model"""
    patient = PatientBasicSerializer(read_only=True)
    provider = ProviderBasicSerializer(read_only=True)
    appointment_type = AppointmentTypeSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    
    # Write-only fields for creation/updates
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=EnhancedPatient.objects.all(),
        source='patient',
        write_only=True
    )
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=EnhancedStaffProfile.objects.all(),
        source='provider',
        write_only=True
    )
    appointment_type_id = serializers.PrimaryKeyRelatedField(
        queryset=AppointmentType.objects.filter(is_active=True),
        source='appointment_type',
        write_only=True
    )
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.filter(is_available=True),
        source='room',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Computed fields
    is_today = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_reschedule = serializers.SerializerMethodField()
    formatted_datetime = serializers.SerializerMethodField()
    
    # Frontend display fields
    patient_name = serializers.SerializerMethodField()
    patient_phone = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    appointment_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'provider', 'appointment_type', 'room',
            'patient_id', 'provider_id', 'appointment_type_id', 'room_id',
            'appointment_date', 'start_time', 'end_time', 'duration',
            'title', 'reason', 'notes', 'status', 'priority',
            'is_recurring', 'recurrence_pattern', 'parent_appointment',
            'estimated_cost', 'actual_cost', 'payment_status',
            'created_by', 'check_in_time', 'check_out_time',
            'cancelled_at', 'cancelled_by', 'cancellation_reason',
            'created_at', 'updated_at',
            'is_today', 'is_upcoming', 'can_cancel', 'can_reschedule',
            'formatted_datetime',
            'patient_name', 'patient_phone', 'patient_email',
            'provider_name', 'appointment_type_name'
        ]
        read_only_fields = [
            'id', 'end_time', 'duration', 'estimated_cost',
            'created_at', 'updated_at', 'is_today', 'is_upcoming',
            'can_cancel', 'can_reschedule', 'formatted_datetime',
            'patient_name', 'patient_phone', 'patient_email',
            'provider_name', 'appointment_type_name'
        ]
    
    def get_is_today(self, obj):
        """Check if appointment is today"""
        return obj.is_today
    
    def get_is_upcoming(self, obj):
        """Check if appointment is upcoming"""
        return obj.is_upcoming
    
    def get_can_cancel(self, obj):
        """Check if appointment can be cancelled"""
        return obj.can_be_cancelled()
    
    def get_can_reschedule(self, obj):
        """Check if appointment can be rescheduled"""
        return obj.can_be_rescheduled()
    
    def get_formatted_datetime(self, obj):
        """Get formatted date and time"""
        return f"{obj.appointment_date.strftime('%A, %B %d, %Y')} at {obj.start_time.strftime('%I:%M %p')}"
    
    def get_patient_name(self, obj):
        """Get patient full name"""
        return obj.patient.user.full_name if obj.patient and obj.patient.user else ""
    
    def get_patient_phone(self, obj):
        """Get patient phone"""
        return obj.patient.phone if obj.patient else ""
    
    def get_patient_email(self, obj):
        """Get patient email"""
        return obj.patient.user.email if obj.patient and obj.patient.user else ""
    
    def get_provider_name(self, obj):
        """Get provider full name"""
        return obj.provider.user.full_name if obj.provider and obj.provider.user else ""
    
    def get_appointment_type_name(self, obj):
        """Get appointment type name"""
        return obj.appointment_type.name if obj.appointment_type else ""
    
    def validate(self, data):
        """Comprehensive validation for appointment data"""
        from datetime import datetime, time
        from django.utils import timezone
        
        appointment_date = data.get('appointment_date')
        start_time = data.get('start_time')
        patient = data.get('patient')
        provider = data.get('provider')
        
        # Check if appointment is in the future
        if appointment_date and start_time:
            appointment_datetime = timezone.make_aware(
                datetime.combine(appointment_date, start_time)
            )
            if appointment_datetime <= timezone.now():
                raise serializers.ValidationError(
                    "Appointment must be scheduled for a future date and time"
                )
        
        # Check working hours (8 AM to 6 PM)
        if start_time:
            working_start = time(8, 0)
            working_end = time(18, 0)
            if start_time < working_start or start_time > working_end:
                raise serializers.ValidationError(
                    "Appointments must be scheduled between 8:00 AM and 6:00 PM"
                )
        
        # Check for conflicts (if this is a new appointment or date/time changed)
        if appointment_date and start_time and patient and provider:
            existing_appointments = Appointment.objects.filter(
                appointment_date=appointment_date,
                start_time=start_time,
                status__in=['scheduled', 'confirmed', 'pending']
            )
            
            # Exclude current appointment if updating
            if self.instance:
                existing_appointments = existing_appointments.exclude(id=self.instance.id)
            
            # Check provider availability
            provider_conflict = existing_appointments.filter(provider=provider).exists()
            if provider_conflict:
                raise serializers.ValidationError(
                    "Provider is already booked at this time"
                )
            
            # Check patient availability
            patient_conflict = existing_appointments.filter(patient=patient).exists()
            if patient_conflict:
                raise serializers.ValidationError(
                    "Patient already has an appointment at this time"
                )
        
        return data
    
    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance:  # Updating existing appointment
            current_status = self.instance.status
            valid_transitions = {
                'pending': ['scheduled', 'cancelled', 'declined'],
                'scheduled': ['confirmed', 'cancelled', 'rescheduled', 'completed'],
                'confirmed': ['completed', 'cancelled', 'no_show'],
                'rescheduled': ['scheduled', 'cancelled'],
                'completed': [],  # Cannot change from completed
                'cancelled': [],  # Cannot change from cancelled
                'no_show': [],   # Cannot change from no_show
                'declined': []   # Cannot change from declined
            }
            
            if current_status in valid_transitions:
                if value not in valid_transitions[current_status]:
                    raise serializers.ValidationError(
                        f"Cannot change status from '{current_status}' to '{value}'"
                    )
        
        return value


class AppointmentCreateSerializer(AppointmentSerializer):
    """Specialized serializer for creating appointments"""
    
    class Meta(AppointmentSerializer.Meta):
        fields = [
            'patient_id', 'provider_id', 'appointment_type_id', 'room_id',
            'appointment_date', 'start_time', 'duration', 'priority', 'reason',
            'notes', 'title'
        ]
        read_only_fields = [
            'id', 'end_time', 'estimated_cost',
            'created_at', 'updated_at', 'is_today', 'is_upcoming',
            'can_cancel', 'can_reschedule', 'formatted_datetime'
        ]
    
    def create(self, validated_data):
        """Create appointment with hospital from context"""
        # Get hospital from context (set by the view)
        hospital = self.context.get('hospital')
        user = self.context.get('user')
        
        if not hospital:
            raise serializers.ValidationError("Hospital association is required")
        
        # Set hospital and created_by
        validated_data['hospital'] = hospital
        validated_data['created_by'] = user
        
        return super().create(validated_data)


class AppointmentUpdateSerializer(AppointmentSerializer):
    """Specialized serializer for updating appointments"""
    
    class Meta(AppointmentSerializer.Meta):
        fields = [
            'appointment_date', 'start_time', 'status', 'priority',
            'reason', 'notes', 'title', 'room'
        ]


class AppointmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing appointments"""
    patient_name = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    appointment_type_name = serializers.CharField(source='appointment_type.name')
    formatted_datetime = serializers.SerializerMethodField()
    patient_id = serializers.CharField(source='patient.id')
    provider_id = serializers.CharField(source='provider.id')
    room = serializers.CharField(source='room.name', allow_null=True)
    notes = serializers.CharField(allow_blank=True)
    duration = serializers.IntegerField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient_id', 'patient_name', 'provider_id', 'provider_name',
            'appointment_type_name', 'appointment_date', 'start_time', 'duration',
            'status', 'priority', 'formatted_datetime', 'room', 'notes'
        ]
    
    def get_patient_name(self, obj):
        try:
            if obj.patient and obj.patient.user:
                return obj.patient.user.get_full_name() or "Unknown Patient"
        except AttributeError:
            pass
        return "Unknown Patient"
    
    def get_provider_name(self, obj):
        try:
            if obj.provider and obj.provider.user:
                return obj.provider.user.get_full_name() or "Unknown Provider"
        except AttributeError:
            pass
        return "Unknown Provider"
    
    def get_formatted_datetime(self, obj):
        return f"{obj.appointment_date.strftime('%m/%d/%Y')} {obj.start_time.strftime('%I:%M %p')}"


class AppointmentWaitlistSerializer(serializers.ModelSerializer):
    """Serializer for AppointmentWaitlist model"""
    patient = PatientBasicSerializer(read_only=True)
    provider = ProviderBasicSerializer(read_only=True)
    appointment_type = AppointmentTypeSerializer(read_only=True)
    
    # Write-only fields
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=EnhancedPatient.objects.all(),
        source='patient',
        write_only=True
    )
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=EnhancedStaffProfile.objects.all(),
        source='provider',
        write_only=True
    )
    appointment_type_id = serializers.PrimaryKeyRelatedField(
        queryset=AppointmentType.objects.filter(is_active=True),
        source='appointment_type',
        write_only=True
    )
    
    class Meta:
        model = AppointmentWaitlist
        fields = [
            'id', 'patient', 'provider', 'appointment_type',
            'patient_id', 'provider_id', 'appointment_type_id',
            'preferred_date_start', 'preferred_date_end', 
            'preferred_time_start', 'preferred_time_end',
            'priority', 'reason', 'status', 'position',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'position', 'created_at', 'updated_at']
    
    def validate_preferred_date_start(self, value):
        """Validate preferred date is in the future"""
        from django.utils import timezone
        if value <= timezone.now().date():
            raise serializers.ValidationError("Preferred date must be in the future")
        return value


class AppointmentStatsSerializer(serializers.Serializer):
    """Serializer for appointment statistics"""
    total_appointments = serializers.IntegerField()
    scheduled_appointments = serializers.IntegerField()
    completed_appointments = serializers.IntegerField()
    cancelled_appointments = serializers.IntegerField()
    no_show_appointments = serializers.IntegerField()
    upcoming_appointments = serializers.IntegerField()
    today_appointments = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    cancellation_rate = serializers.FloatField()
    no_show_rate = serializers.FloatField()


class TimeSlotSerializer(serializers.Serializer):
    """Serializer for available time slots"""
    time = serializers.TimeField()
    available = serializers.BooleanField()
    reason = serializers.CharField(required=False, allow_blank=True)