from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Hospital, HospitalPatient, EnhancedPatient, EnhancedStaffProfile, Specialization, StaffCredential

User = get_user_model()


class HospitalSerializer(serializers.ModelSerializer):
    """Serializer for Hospital model"""
    
    staff_count = serializers.ReadOnlyField()
    patient_count = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    can_add_staff = serializers.ReadOnlyField()
    can_add_patients = serializers.ReadOnlyField()
    
    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'slug', 'hospital_type', 'email', 'phone', 'website',
            'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country',
            'license_number', 'tax_id', 'accreditation', 'timezone', 'language', 'currency',
            'operating_hours', 'appointment_settings', 'notification_settings',
            'logo', 'primary_color', 'secondary_color', 'status', 'is_verified',
            'subscription_plan', 'max_staff', 'max_patients', 'created_at', 'updated_at',
            'staff_count', 'patient_count', 'full_address', 'can_add_staff', 'can_add_patients'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug']
    
    def create(self, validated_data):
        """Create hospital with auto-generated slug"""
        from django.utils.text import slugify
        import uuid
        
        name = validated_data.get('name')
        base_slug = slugify(name)
        slug = base_slug
        
        # Ensure unique slug
        counter = 1
        while Hospital.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        validated_data['slug'] = slug
        return super().create(validated_data)


class HospitalListSerializer(serializers.ModelSerializer):
    """Simplified serializer for hospital list views"""
    
    staff_count = serializers.ReadOnlyField()
    patient_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'slug', 'hospital_type', 'email', 'phone',
            'city', 'state', 'status', 'is_verified', 'staff_count', 'patient_count',
            'created_at'
        ]


class HospitalUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating hospital information"""
    
    class Meta:
        model = Hospital
        fields = [
            'name', 'hospital_type', 'email', 'phone', 'website',
            'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country',
            'timezone', 'language', 'currency', 'operating_hours', 'appointment_settings',
            'notification_settings', 'logo', 'primary_color', 'secondary_color',
            'max_staff', 'max_patients'
        ]
    
    def update(self, instance, validated_data):
        """Update hospital with slug regeneration if name changes"""
        from django.utils.text import slugify
        
        if 'name' in validated_data and validated_data['name'] != instance.name:
            name = validated_data['name']
            base_slug = slugify(name)
            slug = base_slug
            
            # Ensure unique slug
            counter = 1
            while Hospital.objects.filter(slug=slug).exclude(id=instance.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            instance.slug = slug
        
        return super().update(instance, validated_data)


class HospitalRegistrationSerializer(serializers.Serializer):
    """Serializer for hospital registration with admin user creation"""
    
    # Hospital fields
    hospital_name = serializers.CharField(max_length=255)
    hospital_type = serializers.ChoiceField(choices=Hospital.HOSPITAL_TYPE_CHOICES)
    hospital_email = serializers.EmailField()
    hospital_phone = serializers.CharField(max_length=20)
    hospital_website = serializers.URLField(required=False, allow_blank=True)
    
    # Hospital address
    address_line_1 = serializers.CharField(max_length=255)
    address_line_2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=100, default='United States')
    
    # Hospital business info
    license_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tax_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=50, default='America/New_York')
    language = serializers.CharField(max_length=10, default='en')
    currency = serializers.CharField(max_length=3, default='USD')
    
    # Admin user fields
    admin_first_name = serializers.CharField(max_length=150)
    admin_last_name = serializers.CharField(max_length=150)
    admin_email = serializers.EmailField()
    admin_password = serializers.CharField(min_length=8, write_only=True)
    admin_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    admin_job_title = serializers.CharField(max_length=100, default='Hospital Administrator')
    
    def validate_hospital_email(self, value):
        """Validate that hospital email is unique"""
        if Hospital.objects.filter(email=value).exists():
            raise serializers.ValidationError("A hospital with this email already exists.")
        return value
    
    def validate_admin_email(self, value):
        """Validate that admin email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_admin_password(self, value):
        """Validate password strength"""
        from django.contrib.auth.password_validation import validate_password
        try:
            validate_password(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value
    
    def create(self, validated_data):
        """Create hospital and admin user in a single transaction"""
        from django.db import transaction
        from django.utils.text import slugify
        from django.contrib.auth.hashers import make_password
        
        with transaction.atomic():
            # Extract admin user data
            admin_data = {
                'first_name': validated_data.pop('admin_first_name'),
                'last_name': validated_data.pop('admin_last_name'),
                'email': validated_data.pop('admin_email'),
                'password': validated_data.pop('admin_password'),
                'phone': validated_data.pop('admin_phone', ''),
                'job_title': validated_data.pop('admin_job_title'),
            }
            
            # Create hospital
            hospital_data = {
                'name': validated_data['hospital_name'],
                'hospital_type': validated_data['hospital_type'],
                'email': validated_data['hospital_email'],
                'phone': validated_data['hospital_phone'],
                'website': validated_data.get('hospital_website', ''),
                'address_line_1': validated_data['address_line_1'],
                'address_line_2': validated_data.get('address_line_2', ''),
                'city': validated_data['city'],
                'state': validated_data['state'],
                'postal_code': validated_data['postal_code'],
                'country': validated_data['country'],
                'license_number': validated_data.get('license_number', ''),
                'tax_id': validated_data.get('tax_id', ''),
                'timezone': validated_data['timezone'],
                'language': validated_data['language'],
                'currency': validated_data['currency'],
                'status': 'active',  # Auto-approve for MVP
                'is_verified': True,  # Auto-verify for MVP
                'subscription_plan': 'basic',  # Default plan
                'max_staff': 50,  # Default limits
                'max_patients': 1000,
            }
            
            # Generate unique slug
            base_slug = slugify(hospital_data['name'])
            slug = base_slug
            counter = 1
            while Hospital.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            hospital_data['slug'] = slug
            
            # Create hospital
            hospital = Hospital.objects.create(**hospital_data)
            
            # Create admin user
            admin_user = User.objects.create(
                first_name=admin_data['first_name'],
                last_name=admin_data['last_name'],
                full_name=f"{admin_data['first_name']} {admin_data['last_name']}",
                email=admin_data['email'],
                password=make_password(admin_data['password']),
                phone=admin_data.get('phone', ''),
                is_active=True,
                role='admin'
            )
            
            # Create staff profile for admin
            staff_profile = EnhancedStaffProfile.objects.create(
                user=admin_user,
                hospital=hospital,
                job_title=admin_data['job_title'],
                employment_status='full_time',
                hire_date=timezone.now().date(),
                work_email=admin_data['email'],
                work_phone=admin_data.get('phone', ''),
            )
            
            return {
                'hospital': hospital,
                'admin_user': admin_user,
                'staff_profile': staff_profile
            }


class HospitalPatientSerializer(serializers.ModelSerializer):
    """Serializer for HospitalPatient relationship model"""
    
    patient_name = serializers.CharField(source='patient.user.full_name', read_only=True)
    patient_email = serializers.CharField(source='patient.user.email', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    added_by_name = serializers.CharField(source='added_by.full_name', read_only=True)
    visit_count = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = HospitalPatient
        fields = [
            'id', 'hospital', 'patient', 'relationship_type', 'status',
            'added_by', 'notes', 'preferred_language', 'communication_preferences',
            'first_visit_date', 'last_visit_date', 'created_at', 'updated_at',
            'patient_name', 'patient_email', 'hospital_name', 'added_by_name',
            'visit_count', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'first_visit_date', 'last_visit_date']


class HospitalPatientListSerializer(serializers.ModelSerializer):
    """Simplified serializer for hospital patient list views"""
    
    patient_name = serializers.CharField(source='patient.user.full_name', read_only=True)
    patient_email = serializers.CharField(source='patient.user.email', read_only=True)
    patient_phone = serializers.CharField(source='patient.phone', read_only=True)
    patient_age = serializers.IntegerField(source='patient.age', read_only=True)
    patient_gender = serializers.CharField(source='patient.get_gender_display', read_only=True)
    visit_count = serializers.ReadOnlyField()
    
    class Meta:
        model = HospitalPatient
        fields = [
            'id', 'relationship_type', 'status', 'first_visit_date', 'last_visit_date',
            'patient_name', 'patient_email', 'patient_phone', 'patient_age', 
            'patient_gender', 'visit_count'
        ]


class SpecializationSerializer(serializers.ModelSerializer):
    """Serializer for Specialization model"""
    
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'code', 'is_active']


class StaffCredentialSerializer(serializers.ModelSerializer):
    """Serializer for StaffCredential model"""
    
    is_expiring_soon = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = StaffCredential
        fields = [
            'id', 'credential_name', 'credential_type', 'issuing_authority',
            'issue_date', 'expiration_date', 'credential_number', 'verification_url',
            'status', 'notes', 'is_expiring_soon', 'is_expired', 'created_at', 'updated_at'
        ]


class EnhancedStaffProfileSerializer(serializers.ModelSerializer):
    """Serializer for EnhancedStaffProfile model"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    specialization_name = serializers.CharField(source='specialization.name', read_only=True)
    credentials = StaffCredentialSerializer(many=True, read_only=True)
    
    class Meta:
        model = EnhancedStaffProfile
        fields = [
            'id', 'user', 'hospital', 'specialization', 'department', 'job_title',
            'license_number', 'license_state', 'license_expiration', 'license_status',
            'board_certifications', 'dea_number', 'dea_expiration', 'npi_number',
            'employment_status', 'hire_date', 'termination_date', 'work_phone',
            'work_email', 'pager', 'office_location', 'office_address',
            'default_schedule', 'years_experience', 'education', 'languages_spoken',
            'bio', 'consultation_fee', 'is_accepting_new_patients', 'availability_notes',
            'user_email', 'user_full_name', 'hospital_name', 'specialization_name',
            'credentials', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EnhancedPatientSerializer(serializers.ModelSerializer):
    """Serializer for EnhancedPatient model"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = EnhancedPatient
        fields = [
            'id', 'user', 'hospital', 'date_of_birth', 'gender', 'marital_status',
            'phone', 'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'country', 'blood_type', 'height', 'weight', 'allergies', 'medical_history',
            'current_medications', 'insurance_provider', 'insurance_policy_number',
            'insurance_type', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'emergency_contact_email',
            'emergency_contact_address', 'emergency_notification_types',
            'emergency_notification_methods', 'preferred_language', 'preferred_pharmacy',
            'user_email', 'user_full_name', 'hospital_name', 'age',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']