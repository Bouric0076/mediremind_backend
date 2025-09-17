from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from authentication.utils import get_authenticated_user
from authentication.middleware import api_csrf_exempt, get_request_user
from .models import EnhancedPatient, EnhancedStaffProfile
from authentication.models import User
import json
import logging
from datetime import datetime

# Test endpoint for debugging authentication
@api_csrf_exempt
@require_http_methods(["GET", "POST"])
def test_auth(request):
    """Test endpoint to debug authentication - requires valid token"""
    logger = logging.getLogger(__name__)
    
    # Get authenticated user from middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    response_data = {
        'method': request.method,
        'message': 'Authentication successful',
        'authenticated_user': {
            'id': user.id,
            'email': user.email,
            'role': getattr(user, 'role', user.profile.get('role') if hasattr(user, 'profile') else None)
        },
        'session_key': request.session.session_key,
        'user_authenticated': request.user.is_authenticated,
        'authorization_header': request.headers.get('Authorization', 'None')[:20] + '...' if request.headers.get('Authorization') else 'None'
    }
    
    logger.info(f"Auth test successful for user: {user.email}")
    return JsonResponse(response_data)

# Patient API endpoints

@api_csrf_exempt
@require_http_methods(["GET"])
def get_all_patients(request):
    """Get all patients with pagination"""
    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        search = request.GET.get('search', '').strip()
        
        # Build query
        patients_query = EnhancedPatient.objects.select_related('user').filter(is_active=True)
        
        # Apply search filter if provided
        if search:
            patients_query = patients_query.filter(
                user__full_name__icontains=search
            ) | patients_query.filter(
                user__email__icontains=search
            )
        
        # Order by creation date (newest first)
        patients_query = patients_query.order_by('-created_at')
        
        # Apply pagination
        paginator = Paginator(patients_query, limit)
        patients_page = paginator.get_page(page)
        
        # Serialize patient data
        patients_data = []
        for patient in patients_page:
            patients_data.append({
                "id": str(patient.id),
                "name": patient.user.full_name,
                "email": patient.user.email,
                "phone": patient.phone,  # This will be decrypted automatically
                "date_of_birth": patient.date_of_birth.isoformat(),
                "age": patient.age,
                "gender": patient.get_gender_display(),
                "status": "active" if patient.is_active else "inactive",
                "primary_care_physician": patient.primary_care_physician.user.full_name if patient.primary_care_physician else None,
                "created_at": patient.created_at.isoformat(),
                "updated_at": patient.updated_at.isoformat()
            })
        
        return JsonResponse({
            "patients": patients_data,
            "total": paginator.count,
            "page": page,
            "limit": limit,
            "total_pages": paginator.num_pages,
            "has_next": patients_page.has_next(),
            "has_previous": patients_page.has_previous()
        })
        
    except Exception as e:
        logging.error(f"Error fetching patients: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@api_csrf_exempt
@require_http_methods(["GET"])
def get_patient_detail(request, pk):
    """Get patient details by ID"""
    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Get patient from database
        patient = get_object_or_404(
            EnhancedPatient.objects.select_related('user', 'primary_care_physician__user'),
            id=pk,
            is_active=True
        )
        
        # Serialize detailed patient data
        patient_data = {
            "id": str(patient.id),
            "name": patient.user.full_name,
            "email": patient.user.email,
            "phone": patient.phone,
            "date_of_birth": patient.date_of_birth.isoformat(),
            "age": patient.age,
            "gender": patient.get_gender_display(),
            "marital_status": patient.get_marital_status_display() if patient.marital_status else None,
            "blood_type": patient.blood_type,
            "height_inches": patient.height_inches,
            "weight_lbs": patient.weight_lbs,
            "bmi": patient.bmi,
            "address": {
                "line1": patient.address_line1,
                "line2": patient.address_line2,
                "city": patient.city,
                "state": patient.state,
                "zip_code": patient.zip_code,
                "country": patient.country
            },
            "emergency_contact": {
                "name": patient.emergency_contact_name,
                "relationship": patient.emergency_contact_relationship,
                "phone": patient.emergency_contact_phone,
                "email": patient.emergency_contact_email
            },
            "medical_info": {
                "allergies": patient.allergies,
                "current_medications": patient.current_medications,
                "medical_conditions": patient.medical_conditions,
                "surgical_history": patient.surgical_history,
                "family_medical_history": patient.family_medical_history
            },
            "lifestyle": {
                "smoking_status": patient.get_smoking_status_display(),
                "alcohol_use": patient.get_alcohol_use_display(),
                "exercise_frequency": patient.get_exercise_frequency_display() if patient.exercise_frequency else None
            },
            "insurance": {
                "provider": patient.insurance_provider,
                "type": patient.get_insurance_type_display() if patient.insurance_type else None,
                "policy_number": patient.insurance_policy_number,
                "group_number": patient.insurance_group_number
            },
            "preferences": {
                "language": patient.preferred_language,
                "communication": patient.get_preferred_communication_display()
            },
            "primary_care_physician": {
                "id": str(patient.primary_care_physician.id),
                "name": patient.primary_care_physician.user.full_name
            } if patient.primary_care_physician else None,
            "status": "active" if patient.is_active else "inactive",
            "registration_completed": patient.registration_completed,
            "created_at": patient.created_at.isoformat(),
            "updated_at": patient.updated_at.isoformat()
        }
        
        return JsonResponse({"patient": patient_data})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_csrf_exempt
@require_http_methods(["POST"])
def create_patient(request):
    """Create a new patient"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        logger.error("Authentication failed - no valid user found")
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    logger.info(f"Create patient request from authenticated user: {user.id}")

    try:
        from django.contrib.auth import get_user_model
        from .models import EnhancedPatient
        from datetime import datetime
        
        User = get_user_model()
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'phone', 'dateOfBirth', 'gender']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({"error": f"{field} is required"}, status=400)
        
        # Handle account creation
        account_data = data.get('account', {})
        create_account = account_data.get('createAccount', False)
        account_created = False
        
        # Create User first
        user_data = {
            'email': data['email'],
            'full_name': f"{data['firstName']} {data['lastName']}",
            'role': 'patient',
            'is_active': True
        }
        
        # Check if user with this email already exists
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({"error": "A user with this email already exists"}, status=400)
        
        # Validate password if account creation is requested
        if create_account:
            password = account_data.get('password')
            if not password:
                return JsonResponse({"error": "Password is required when creating an account"}, status=400)
            
            # Validate password strength
            import re
            if len(password) < 8:
                return JsonResponse({"error": "Password must be at least 8 characters long"}, status=400)
            if not re.search(r'[a-z]', password):
                return JsonResponse({"error": "Password must contain at least one lowercase letter"}, status=400)
            if not re.search(r'[A-Z]', password):
                return JsonResponse({"error": "Password must contain at least one uppercase letter"}, status=400)
            if not re.search(r'\d', password):
                return JsonResponse({"error": "Password must contain at least one number"}, status=400)
            if not re.search(r'[@$!%*?&]', password):
                return JsonResponse({"error": "Password must contain at least one special character (@$!%*?&)"}, status=400)
        
        # Create the user
        if create_account:
            patient_user = User.objects.create_user(
                email=data['email'],
                password=account_data['password'],
                **{k: v for k, v in user_data.items() if k != 'email'}
            )
            account_created = True
        else:
            # Create user without usable password
            patient_user = User.objects.create(**user_data)
            patient_user.set_unusable_password()
            patient_user.save()
        
        # Map gender values
        gender_mapping = {
            'male': 'M',
            'female': 'F',
            'other': 'O'
        }
        
        # Get the actual User instance from the authenticated user
        if hasattr(user, 'id'):
            # If it's a DjangoAuthenticatedUser, get the actual user by ID
            from authentication.models import User
            actual_user = User.objects.get(id=user.id)
        else:
            actual_user = user
        
        # Create EnhancedPatient
        patient_data = {
            'user': patient_user,
            'date_of_birth': datetime.strptime(data['dateOfBirth'], '%Y-%m-%d').date(),
            'gender': gender_mapping.get(data['gender'], 'O'),
            'phone': data['phone'],
            'created_by': actual_user,
        }
        
        # Add address information if provided
        address = data.get('address', {})
        if address.get('street'):
            patient_data['address_line1'] = address['street']
        if address.get('city'):
            patient_data['city'] = address['city']
        if address.get('state'):
            patient_data['state'] = address['state']
        if address.get('zipCode'):
            patient_data['zip_code'] = address['zipCode']
        if address.get('country'):
            patient_data['country'] = address['country']
        
        # Add emergency contact if provided
        emergency = data.get('emergencyContact', {})
        if emergency.get('name'):
            patient_data['emergency_contact_name'] = emergency['name']
        if emergency.get('relationship'):
            patient_data['emergency_contact_relationship'] = emergency['relationship']
        if emergency.get('phone'):
            patient_data['emergency_contact_phone'] = emergency['phone']
        
        # Add medical information if provided
        medical = data.get('medicalInfo', {})
        if medical.get('bloodType'):
            patient_data['blood_type'] = medical['bloodType']
        if medical.get('allergies'):
            patient_data['allergies'] = medical['allergies']
        if medical.get('medications'):
            patient_data['current_medications'] = medical['medications']
        if medical.get('medicalHistory'):
            patient_data['medical_conditions'] = medical['medicalHistory']
        
        # Add insurance information if provided
        insurance = data.get('insurance', {})
        if insurance.get('provider'):
            patient_data['insurance_provider'] = insurance['provider']
        if insurance.get('policyNumber'):
            patient_data['insurance_policy_number'] = insurance['policyNumber']
        if insurance.get('groupNumber'):
            patient_data['insurance_group_number'] = insurance['groupNumber']
        
        # Create the patient
        patient = EnhancedPatient.objects.create(**patient_data)
        
        # Return patient data
        response_data = {
            "id": str(patient.id),
            "firstName": data['firstName'],
            "lastName": data['lastName'],
            "email": data['email'],
            "phone": data['phone'],
            "dateOfBirth": data['dateOfBirth'],
            "gender": data['gender'],
            "status": "active"
        }
        
        # Prepare response message
        if account_created:
            message = "Patient created successfully with login account! The patient can now log in to access their portal."
        else:
            message = "Patient created successfully"
        
        return JsonResponse({
            "patient": response_data, 
            "message": message,
            "account_created": account_created
        }, status=201)
        
    except Exception as e:
        # If patient creation fails, clean up the user
        if 'patient_user' in locals():
            patient_user.delete()
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_patient(request, pk):
    """Update patient information"""
    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        data = json.loads(request.body)
        # Mock update - replace with actual database update
        patient = {
            "id": pk,
            "name": data.get('name'),
            "email": data.get('email'),
            "phone": data.get('phone'),
            "date_of_birth": data.get('date_of_birth'),
            "status": data.get('status', 'active')
        }
        
        return JsonResponse({"patient": patient, "message": "Patient updated successfully"})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Staff API endpoints

@api_csrf_exempt
@require_http_methods(["GET"])
def get_all_staff(request):
    """Get all staff members"""
    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Mock staff data
        staff = [
            {
                "id": 1,
                "name": "Dr. Sarah Johnson",
                "email": "sarah.johnson@hospital.com",
                "role": "Doctor",
                "department": "Cardiology",
                "status": "active"
            },
            {
                "id": 2,
                "name": "Nurse Mary Wilson",
                "email": "mary.wilson@hospital.com",
                "role": "Nurse",
                "department": "Emergency",
                "status": "active"
            }
        ]
        
        return JsonResponse({"staff": staff, "total": len(staff)})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Care Team API endpoints

@csrf_exempt
@require_http_methods(["GET"])
def get_care_teams(request):
    """Get all care teams"""
    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        # Mock care team data
        care_teams = [
            {
                "id": 1,
                "name": "Cardiology Team A",
                "department": "Cardiology",
                "members": ["Dr. Sarah Johnson", "Nurse Mary Wilson"],
                "status": "active"
            }
        ]
        
        return JsonResponse({"care_teams": care_teams, "total": len(care_teams)})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_staff_detail(request, pk):
    """Get staff member details by ID"""
    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        # Mock staff detail data
        staff = {
            "id": pk,
            "name": "Dr. Sarah Johnson",
            "email": "sarah.johnson@hospital.com",
            "role": "Doctor",
            "department": "Cardiology",
            "status": "active",
            "phone": "+1234567892",
            "hire_date": "2020-01-15",
            "specializations": ["Cardiology", "Internal Medicine"]
        }
        
        return JsonResponse({"staff": staff})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_staff(request):
    """Create a new staff member"""
    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        data = json.loads(request.body)
        # Mock creation - replace with actual database creation
        staff = {
            "id": 999,  # Mock ID
            "name": data.get('name'),
            "email": data.get('email'),
            "role": data.get('role'),
            "department": data.get('department'),
            "status": "active"
        }
        
        return JsonResponse({"staff": staff, "message": "Staff member created successfully"}, status=201)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_staff(request, pk):
    """Update staff member information"""
    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        data = json.loads(request.body)
        # Mock update - replace with actual database update
        staff = {
            "id": pk,
            "name": data.get('name'),
            "email": data.get('email'),
            "role": data.get('role'),
            "department": data.get('department'),
            "status": data.get('status', 'active')
        }
        
        return JsonResponse({"staff": staff, "message": "Staff member updated successfully"})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_care_team(request):
    """Create a new care team"""
    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        data = json.loads(request.body)
        # Mock creation - replace with actual database creation
        care_team = {
            "id": 999,  # Mock ID
            "name": data.get('name'),
            "department": data.get('department'),
            "members": data.get('members', []),
            "status": "active"
        }
        
        return JsonResponse({"care_team": care_team, "message": "Care team created successfully"}, status=201)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_staff_credentials(request, staff_id):
    """Get staff credentials by staff ID"""
    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        # Mock credentials data
        credentials = [
            {
                "id": 1,
                "staff_id": staff_id,
                "credential_type": "Medical License",
                "credential_number": "MD123456",
                "issuing_authority": "State Medical Board",
                "issue_date": "2020-01-01",
                "expiry_date": "2025-01-01",
                "status": "active"
            }
        ]
        
        return JsonResponse({"credentials": credentials, "total": len(credentials)})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_csrf_exempt
@require_http_methods(["GET"])
def get_user_profile(request):
    """Get user profile information"""
    try:
        # Get authenticated user using unified middleware
        user = get_request_user(request)
        if not user:
            return JsonResponse({"error": "Authentication required"}, status=401)

        # Return user profile data
        return JsonResponse({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_active": user.is_active,
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        })

    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_credential_detail(request, pk):
    """Get credential details by ID"""
    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        # Mock credential detail data
        credential = {
            "id": pk,
            "staff_id": 1,
            "credential_type": "Medical License",
            "credential_number": "MD123456",
            "issuing_authority": "State Medical Board",
            "issue_date": "2020-01-01",
            "expiry_date": "2025-01-01",
            "status": "active",
            "verification_status": "verified"
        }
        
        return JsonResponse({"credential": credential})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_csrf_exempt
@require_http_methods(["PUT"])
def update_patient(request, pk):
    """Update patient information"""
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Get patient from database
        patient = get_object_or_404(
            EnhancedPatient.objects.select_related('user'),
            id=pk,
            is_active=True
        )
        
        data = json.loads(request.body)
        
        # Update user information
        if 'firstName' in data or 'lastName' in data:
            first_name = data.get('firstName', patient.user.full_name.split()[0])
            last_name = data.get('lastName', ' '.join(patient.user.full_name.split()[1:]))
            patient.user.full_name = f"{first_name} {last_name}"
        
        if 'email' in data:
            # Check if email is already taken by another user
            if User.objects.filter(email=data['email']).exclude(id=patient.user.id).exists():
                return JsonResponse({"error": "Email already exists"}, status=400)
            patient.user.email = data['email']
        
        # Update patient-specific fields
        if 'phone' in data:
            patient.phone = data['phone']
        if 'dateOfBirth' in data:
            patient.date_of_birth = datetime.strptime(data['dateOfBirth'], '%Y-%m-%d').date()
        if 'gender' in data:
            patient.gender = data['gender']
        if 'maritalStatus' in data:
            patient.marital_status = data['maritalStatus']
        if 'bloodType' in data:
            patient.blood_type = data['bloodType']
        if 'height' in data:
            patient.height_inches = data['height']
        if 'weight' in data:
            patient.weight_lbs = data['weight']
        
        # Update address
        address = data.get('address', {})
        if address:
            if 'line1' in address:
                patient.address_line1 = address['line1']
            if 'line2' in address:
                patient.address_line2 = address['line2']
            if 'city' in address:
                patient.city = address['city']
            if 'state' in address:
                patient.state = address['state']
            if 'zipCode' in address:
                patient.zip_code = address['zipCode']
            if 'country' in address:
                patient.country = address['country']
        
        # Update emergency contact
        emergency_contact = data.get('emergencyContact', {})
        if emergency_contact:
            if 'name' in emergency_contact:
                patient.emergency_contact_name = emergency_contact['name']
            if 'relationship' in emergency_contact:
                patient.emergency_contact_relationship = emergency_contact['relationship']
            if 'phone' in emergency_contact:
                patient.emergency_contact_phone = emergency_contact['phone']
            if 'email' in emergency_contact:
                patient.emergency_contact_email = emergency_contact['email']
        
        # Update medical information
        medical_info = data.get('medicalInfo', {})
        if medical_info:
            if 'allergies' in medical_info:
                patient.allergies = medical_info['allergies']
            if 'currentMedications' in medical_info:
                patient.current_medications = medical_info['currentMedications']
            if 'medicalConditions' in medical_info:
                patient.medical_conditions = medical_info['medicalConditions']
            if 'surgicalHistory' in medical_info:
                patient.surgical_history = medical_info['surgicalHistory']
            if 'familyMedicalHistory' in medical_info:
                patient.family_medical_history = medical_info['familyMedicalHistory']
        
        # Update lifestyle information
        lifestyle = data.get('lifestyle', {})
        if lifestyle:
            if 'smokingStatus' in lifestyle:
                patient.smoking_status = lifestyle['smokingStatus']
            if 'alcoholUse' in lifestyle:
                patient.alcohol_use = lifestyle['alcoholUse']
            if 'exerciseFrequency' in lifestyle:
                patient.exercise_frequency = lifestyle['exerciseFrequency']
        
        # Update insurance information
        insurance = data.get('insurance', {})
        if insurance:
            if 'provider' in insurance:
                patient.insurance_provider = insurance['provider']
            if 'type' in insurance:
                patient.insurance_type = insurance['type']
            if 'policyNumber' in insurance:
                patient.insurance_policy_number = insurance['policyNumber']
            if 'groupNumber' in insurance:
                patient.insurance_group_number = insurance['groupNumber']
        
        # Update preferences
        preferences = data.get('preferences', {})
        if preferences:
            if 'language' in preferences:
                patient.preferred_language = preferences['language']
            if 'communication' in preferences:
                patient.preferred_communication = preferences['communication']
        
        # Save changes
        with transaction.atomic():
            patient.user.save()
            patient.save()
        
        return JsonResponse({
            "message": "Patient updated successfully",
            "patient_id": str(patient.id)
        })
        
    except Exception as e:
        logging.error(f"Error updating patient: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@api_csrf_exempt
@require_http_methods(["DELETE"])
def delete_patient(request, pk):
    """Soft delete a patient (deactivate)"""
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Get patient from database
        patient = get_object_or_404(
            EnhancedPatient.objects.select_related('user'),
            id=pk,
            is_active=True
        )
        
        # Soft delete by setting is_active to False
        patient.is_active = False
        patient.user.is_active = False
        
        with transaction.atomic():
            patient.save()
            patient.user.save()
        
        return JsonResponse({
            "message": "Patient deactivated successfully",
            "patient_id": str(patient.id)
        })
        
    except Exception as e:
        logging.error(f"Error deleting patient: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
