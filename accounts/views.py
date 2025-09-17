from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from authentication.utils import get_authenticated_user
from authentication.middleware import api_csrf_exempt, get_request_user
import json
import logging

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
        
        # Mock data for now - replace with actual database queries
        patients = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "date_of_birth": "1990-01-15",
                "status": "active"
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "phone": "+1234567891",
                "date_of_birth": "1985-03-22",
                "status": "active"
            }
        ]
        
        return JsonResponse({
            "patients": patients,
            "total": len(patients),
            "page": page,
            "limit": limit
        })
        
    except Exception as e:
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
        # Mock patient data - replace with actual database query
        patient = {
            "id": pk,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "date_of_birth": "1990-01-15",
            "status": "active",
            "address": "123 Main St, City, State 12345",
            "emergency_contact": "+1234567899"
        }
        
        return JsonResponse({"patient": patient})
        
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
