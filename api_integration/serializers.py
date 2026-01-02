from rest_framework import serializers
from .models import HospitalIntegration, DataProcessingConsent, APILog, SecurityIncident
from encryption.fields import EnhancedEncryptedCharField

class HospitalIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for hospital integration configuration"""
    
    class Meta:
        model = HospitalIntegration
        fields = [
            'id', 'hospital', 'status', 'api_version', 'allowed_endpoints',
            'data_retention_days', 'encryption_enabled', 'consent_management_enabled',
            'audit_logging_enabled', 'rate_limit_per_minute', 'rate_limit_per_hour',
            'rate_limit_per_day', 'created_at', 'updated_at', 'last_accessed'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_accessed']

class HospitalIntegrationSetupSerializer(serializers.ModelSerializer):
    """Serializer for initial hospital integration setup"""
    
    hospital_name = serializers.CharField(write_only=True)
    hospital_type = serializers.ChoiceField(
        choices=['hospital', 'clinic', 'medical_center', 'urgent_care', 'specialty_clinic'],
        write_only=True
    )
    contact_email = serializers.EmailField(write_only=True)
    contact_phone = serializers.CharField(write_only=True)
    
    class Meta:
        model = HospitalIntegration
        fields = [
            'hospital_name', 'hospital_type', 'contact_email', 'contact_phone',
            'data_retention_days', 'encryption_enabled', 'consent_management_enabled',
            'audit_logging_enabled'
        ]
    
    def create(self, validated_data):
        """Create hospital and integration setup"""
        from accounts.models import Hospital
        
        # Extract hospital data
        hospital_name = validated_data.pop('hospital_name')
        hospital_type = validated_data.pop('hospital_type')
        contact_email = validated_data.pop('contact_email')
        contact_phone = validated_data.pop('contact_phone')
        
        # Create hospital
        hospital = Hospital.objects.create(
            name=hospital_name,
            hospital_type=hospital_type,
            email=contact_email,
            phone=contact_phone,
            slug=hospital_name.lower().replace(' ', '-')
        )
        
        # Create integration
        integration = HospitalIntegration.objects.create(
            hospital=hospital,
            **validated_data
        )
        
        return integration

class DataProcessingConsentSerializer(serializers.ModelSerializer):
    """Serializer for data processing consent"""
    
    class Meta:
        model = DataProcessingConsent
        fields = [
            'id', 'consent_type', 'status', 'granted_at', 'withdrawn_at',
            'expires_at', 'consent_text', 'consent_version', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class APILogSerializer(serializers.ModelSerializer):
    """Serializer for API log entries"""
    
    class Meta:
        model = APILog
        fields = [
            'id', 'integration', 'method', 'endpoint', 'status_code',
            'ip_address', 'auth_status', 'message', 'data_categories',
            'created_at', 'response_time_ms'
        ]
        read_only_fields = ['id', 'created_at']

class SecurityIncidentSerializer(serializers.ModelSerializer):
    """Serializer for security incidents"""
    
    class Meta:
        model = SecurityIncident
        fields = [
            'id', 'integration', 'title', 'description', 'severity',
            'incident_type', 'source', 'status', 'created_at',
            'resolved_at', 'resolution_notes', 'escalated_at'
        ]
        read_only_fields = ['id', 'created_at', 'resolved_at', 'escalated_at']

class PatientDataSerializer(serializers.Serializer):
    """Serializer for patient data received via API"""
    
    patient_id = serializers.CharField(max_length=100)
    national_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    date_of_birth = serializers.DateField(required=False)
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'], required=False)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    # Medical information
    blood_type = serializers.CharField(max_length=10, required=False, allow_blank=True)
    allergies = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True
    )
    medical_conditions = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        allow_empty=True
    )
    
    # Emergency contact
    emergency_contact_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    emergency_contact_relationship = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    # Consent information
    consent_given = serializers.BooleanField(default=True)
    consent_date = serializers.DateTimeField(required=False)
    consent_version = serializers.CharField(max_length=20, default='1.0')
    
    def validate_phone(self, value):
        """Validate phone number format"""
        import re
        phone_pattern = r'^\+?1?\d{9,15}$'
        if not re.match(phone_pattern, value):
            raise serializers.ValidationError("Invalid phone number format")
        return value
    
    def validate_email(self, value):
        """Validate email format"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Invalid email format")
        return value

class AppointmentDataSerializer(serializers.Serializer):
    """Serializer for appointment data received via API"""
    
    appointment_id = serializers.CharField(max_length=100)
    patient_id = serializers.CharField(max_length=100)
    doctor_name = serializers.CharField(max_length=255)
    doctor_specialty = serializers.CharField(max_length=100, required=False)
    
    appointment_date = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(min_value=1, max_value=480)
    
    appointment_type = serializers.ChoiceField(
        choices=['consultation', 'follow_up', 'procedure', 'surgery', 'checkup']
    )
    specialty = serializers.CharField(max_length=100, required=False)
    
    # Location
    department = serializers.CharField(max_length=100, required=False)
    room_number = serializers.CharField(max_length=20, required=False)
    
    # Status
    status = serializers.ChoiceField(
        choices=['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show'],
        default='scheduled'
    )
    
    # Reminder settings
    reminder_enabled = serializers.BooleanField(default=True)
    reminder_time_minutes = serializers.IntegerField(default=60)
    
    # Additional notes
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)

class ReminderDataSerializer(serializers.Serializer):
    """Serializer for reminder data received via API"""
    
    reminder_id = serializers.CharField(max_length=100)
    appointment_id = serializers.CharField(max_length=100)
    patient_id = serializers.CharField(max_length=100)
    
    reminder_type = serializers.ChoiceField(
        choices=['sms', 'email', 'push_notification', 'call']
    )
    reminder_time = serializers.DateTimeField()
    message_template = serializers.CharField(max_length=1000, required=False)
    
    # Status tracking
    status = serializers.ChoiceField(
        choices=['pending', 'sent', 'delivered', 'failed', 'cancelled'],
        default='pending'
    )
    sent_at = serializers.DateTimeField(required=False)
    delivered_at = serializers.DateTimeField(required=False)
    failure_reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    # Delivery details
    delivery_method = serializers.CharField(max_length=50, required=False)
    delivery_address = serializers.CharField(max_length=255, required=False)
    
    # Response tracking
    response_received = serializers.BooleanField(default=False)
    response_content = serializers.CharField(max_length=500, required=False, allow_blank=True)
    response_time = serializers.DateTimeField(required=False)

class APIResponseSerializer(serializers.Serializer):
    """Standard API response serializer"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField(required=False)
    errors = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    request_id = serializers.UUIDField()
    timestamp = serializers.DateTimeField()

class ErrorResponseSerializer(serializers.Serializer):
    """Standard error response serializer"""
    
    success = serializers.BooleanField(default=False)
    error_code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)
    request_id = serializers.UUIDField()
    timestamp = serializers.DateTimeField()