from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from authentication.utils import get_authenticated_user
from authentication.middleware import api_csrf_exempt, get_request_user
from .models import EnhancedPatient, EnhancedStaffProfile, Hospital
from .serializers import (
    HospitalSerializer, HospitalListSerializer, HospitalUpdateSerializer,
    EnhancedPatientSerializer, EnhancedStaffProfileSerializer
)
from authentication.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json
import logging
from datetime import datetime

# Test endpoint for debugging authentication
@api_csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
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

# Hospital Registration endpoint

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def register_hospital(request):
    """Register a new hospital with admin user - MVP auto-approval"""
    logger = logging.getLogger(__name__)
    
    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        # Import the serializer
        from .serializers import HospitalRegistrationSerializer
        
        # Validate and create hospital + admin
        serializer = HospitalRegistrationSerializer(data=data)
        if serializer.is_valid():
            result = serializer.save()
            
            hospital = result['hospital']
            admin_user = result['admin_user']
            staff_profile = result['staff_profile']
            
            logger.info(f"Hospital registration successful: {hospital.name} with admin: {admin_user.email}")
            
            # Return success response with hospital and admin details
            response_data = {
                'success': True,
                'message': 'Hospital registered successfully',
                'hospital': {
                    'id': hospital.id,
                    'name': hospital.name,
                    'slug': hospital.slug,
                    'email': hospital.email,
                    'status': hospital.status,
                    'is_verified': hospital.is_verified,
                },
                'admin_user': {
                    'id': admin_user.id,
                    'email': admin_user.email,
                    'full_name': admin_user.full_name,
                    'role': admin_user.role,
                },
                'staff_profile': {
                    'id': staff_profile.id,
                    'job_title': staff_profile.job_title,
                    'employment_status': staff_profile.employment_status,
                }
            }
            
            return JsonResponse(response_data, status=201)
        else:
            logger.warning(f"Hospital registration validation failed: {serializer.errors}")
            return JsonResponse({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=400)
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON in hospital registration request")
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.error(f"Hospital registration error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }, status=500)

# Patient API endpoints

@api_csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def get_all_patients(request):
    """Get all patients with pagination - filtered by hospital"""
    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Get user's hospital
        staff_profile = getattr(user, 'staff_profile', None)
        
        # Get user role - handle both direct attribute and profile dict
        user_role = getattr(user, 'role', None)
        if user_role is None and hasattr(user, 'profile') and isinstance(user.profile, dict):
            user_role = user.profile.get('role')
        
        # Get staff profile for the user
        try:
            staff_profile = EnhancedStaffProfile.objects.get(user_id=user.id)
        except EnhancedStaffProfile.DoesNotExist:
            staff_profile = None
        
        # For admin users, check if they have a hospital association
        if user_role == 'admin':
            # Check if this admin user registered a hospital
            from .models import Hospital
            logger = logging.getLogger(__name__)
            
            # First check if staff profile exists and has a hospital
            if staff_profile and staff_profile.hospital:
                hospital = staff_profile.hospital
            else:
                # Find hospitals registered by this admin
                registered_hospitals = Hospital.objects.filter(
                    enhancedstaffprofile__user__email=user.email,
                    enhancedstaffprofile__user__role='admin'
                ).order_by('created_at')
                
                # Also check for hospitals where this admin might be associated
                admin_hospitals = Hospital.objects.filter(
                    staff_members__user=user
                ).order_by('created_at')
                
                if registered_hospitals.exists():
                    # Use the first hospital this admin registered
                    hospital = registered_hospitals.first()
                    
                    # Ensure staff profile exists
                    if not staff_profile:
                        logger.info(f"Creating staff profile for admin user {user.id} with their registered hospital {hospital.id}")
                        staff_profile = EnhancedStaffProfile.objects.create(
                            user=user,
                            hospital=hospital,
                            job_title="Hospital Administrator",
                            employment_status='full_time',
                            hire_date=timezone.now().date(),
                            work_email=user.email,
                        )
                    elif not staff_profile.hospital:
                        # Update existing staff profile with the hospital
                        staff_profile.hospital = hospital
                        staff_profile.save()
                        logger.info(f"Updated staff profile {staff_profile.id} with hospital {hospital.id}")
                elif admin_hospitals.exists():
                    # Use the first hospital where this admin is associated
                    hospital = admin_hospitals.first()
                    
                    # Ensure staff profile exists
                    if not staff_profile:
                        logger.info(f"Creating staff profile for admin user {user.id} with their associated hospital {hospital.id}")
                        staff_profile = EnhancedStaffProfile.objects.create(
                            user=user,
                            hospital=hospital,
                            job_title="Hospital Administrator",
                            employment_status='full_time',
                            hire_date=timezone.now().date(),
                            work_email=user.email,
                        )
                else:
                    return JsonResponse({"error": "Admin users must be associated with a hospital through their staff profile"}, status=403)
        elif not staff_profile or not staff_profile.hospital:
            return JsonResponse({"error": "User must be associated with a hospital"}, status=403)
        else:
            hospital = staff_profile.hospital
        
        # Get query parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        search = request.GET.get('search', '').strip()
        
        # Build query - only get patients associated with this hospital
        from .models import HospitalPatient
        hospital_patient_ids = HospitalPatient.objects.filter(
            hospital=hospital,
            status='active'
        ).values_list('patient_id', flat=True)
        
        patients_query = EnhancedPatient.objects.select_related('user').filter(
            id__in=hospital_patient_ids,
            is_active=True
        )
        
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
@require_http_methods(["GET", "OPTIONS"])
def get_patient_detail(request, pk):
    """Get patient details by ID"""
    logger = logging.getLogger(__name__)
    
    # Get authenticated user using unified middleware
    auth_user = get_request_user(request)
    if not auth_user:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    logger.debug(f"Authenticated user: {auth_user}")
    
    # Extract the actual Django user from the AuthenticatedUser wrapper
    if hasattr(auth_user, 'user'):
        user = auth_user.user
    else:
        user = auth_user
    
    logger.debug(f"Django user: {user}")
    
    # Ensure the user is a valid Django User instance
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not isinstance(user, User):
        logger.error(f"Invalid user object type: {type(user)}")
        return JsonResponse({"error": "Invalid user object"}, status=400)
    
    # Retrieve the staff profile for the authenticated user
    try:
        staff_profile = EnhancedStaffProfile.objects.get(user=user)
        logger.debug(f"Staff profile: {staff_profile}")
    except EnhancedStaffProfile.DoesNotExist:
        logger.warning("No staff profile found for the authenticated user.")
        return JsonResponse({"error": "Staff profile not found"}, status=404)
    
    # Check if the staff profile is associated with a hospital
    hospital = getattr(staff_profile, 'hospital', None)
    if not hospital:
        logger.warning("No hospital associated with staff profile.")
        return JsonResponse({"error": "No hospital associated with staff profile"}, status=400)
    
    logger.debug(f"Hospital associated with staff profile: {hospital}")
    logger.info(f"Get patient detail request for patient ID {pk} from user: {user.id}")

    try:
        # Get the patient by ID
        patient = get_object_or_404(EnhancedPatient, id=pk)
        
        # Check if this patient belongs to the user's hospital
        from .models import HospitalPatient
        hospital_patient = HospitalPatient.objects.filter(
            hospital=hospital,
            patient=patient,
            status='active'
        ).first()
        
        if not hospital_patient:
            logger.warning(f"Patient {pk} does not belong to hospital {hospital.id}")
            return JsonResponse({"error": "Patient not found in this hospital"}, status=404)
        
        # Get patient's user information
        patient_user = patient.user
        
        # Prepare response data
        response_data = {
            "id": str(patient.id),
            "firstName": patient_user.full_name.split(' ')[0] if ' ' in patient_user.full_name else patient_user.full_name,
            "lastName": ' '.join(patient_user.full_name.split(' ')[1:]) if ' ' in patient_user.full_name else '',
            "fullName": patient_user.full_name,
            "email": patient_user.email,
            "phone": patient.phone,  # This will be decrypted automatically
            "dateOfBirth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "age": patient.age,
            "gender": patient.get_gender_display(),
            "status": "active" if patient.is_active else "inactive",
            "createdAt": patient.created_at.isoformat(),
            "updatedAt": patient.updated_at.isoformat(),
            
            # Address information
            "address": {
                "street": patient.address_line1 or "",
                "city": patient.city or "",
                "state": patient.state or "",
                "zipCode": patient.zip_code or "",
                "country": patient.country or ""
            },
            
            # Emergency contact
            "emergencyContact": {
                "name": patient.emergency_contact_name or "",
                "relationship": patient.emergency_contact_relationship or "",
                "phone": patient.emergency_contact_phone or ""
            },
            
            # Medical information
            "medicalInfo": {
                "bloodType": patient.blood_type or "",
                "allergies": patient.allergies or "",
                "medications": patient.current_medications or "",
                "medicalHistory": patient.medical_conditions or ""
            },
            
            # Insurance information
            "insurance": {
                "provider": patient.insurance_provider or "",
                "policyNumber": patient.insurance_policy_number or "",
                "groupNumber": patient.insurance_group_number or ""
            },
            
            # Hospital relationship
            "hospitalRelationship": {
                "relationshipType": hospital_patient.relationship_type,
                "status": hospital_patient.status,
                "since": hospital_patient.created_at.isoformat()
            }
        }
        
        # Add primary care physician if available
        if patient.primary_care_physician:
            physician = patient.primary_care_physician
            response_data["primaryCarePhysician"] = {
                "id": str(physician.id),
                "name": physician.user.full_name,
                "email": physician.user.email
            }
        
        return JsonResponse(response_data)
            
    except Exception as e:
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
@require_http_methods(["GET", "OPTIONS"])
def get_all_staff(request):
    """Get all staff members"""
    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Extract the actual Django user from the AuthenticatedUser wrapper
        if hasattr(user, 'user'):
            django_user = user.user
        else:
            django_user = user
            
        # Get the staff profile for the authenticated user
        try:
            staff_profile = EnhancedStaffProfile.objects.get(user=django_user)
        except EnhancedStaffProfile.DoesNotExist:
            return JsonResponse({"error": "Staff profile not found"}, status=404)
            
        # Check if the staff profile is associated with a hospital
        hospital = getattr(staff_profile, 'hospital', None)
        if not hospital:
            return JsonResponse({"error": "No hospital associated with staff profile"}, status=400)
            
        # Get all active staff members from the same hospital
        staff_query = EnhancedStaffProfile.objects.select_related('user', 'specialization').filter(
            is_active=True,
            hospital=hospital,
            employment_status__in=['full_time', 'part_time', 'contract', 'per_diem', 'locum_tenens']
        ).order_by('user__full_name')
        
        # Serialize staff data
        staff_data = []
        for staff_member in staff_query:
            staff_data.append({
                "id": str(staff_member.id),
                "name": staff_member.user.full_name,
                "email": staff_member.user.email,
                "role": staff_member.job_title,
                "department": staff_member.department,
                "specialization": staff_member.specialization.name if staff_member.specialization else None,
                "employment_status": staff_member.get_employment_status_display(),
                "status": "active" if staff_member.is_active else "inactive",
                "created_at": staff_member.created_at.isoformat(),
                "updated_at": staff_member.updated_at.isoformat()
            })
        
        return JsonResponse({"staff": staff_data, "total": len(staff_data)})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Care Team API endpoints

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
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
@require_http_methods(["GET", "OPTIONS"])
def get_staff_detail(request, pk):
    """Get staff member details by ID"""
    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Extract the actual Django user from the AuthenticatedUser wrapper
        if hasattr(user, 'user'):
            django_user = user.user
        else:
            django_user = user
            
        # Get the staff profile for the authenticated user
        try:
            staff_profile = EnhancedStaffProfile.objects.get(user=django_user)
        except EnhancedStaffProfile.DoesNotExist:
            return JsonResponse({"error": "Staff profile not found"}, status=404)
            
        # Check if the staff profile is associated with a hospital
        hospital = getattr(staff_profile, 'hospital', None)
        if not hospital:
            return JsonResponse({"error": "No hospital associated with staff profile"}, status=400)
        
        # Get the requested staff member, ensuring they belong to the same hospital
        try:
            staff_member = EnhancedStaffProfile.objects.select_related('user', 'specialization').get(
                id=pk,
                hospital=hospital  # This ensures the staff member belongs to the same hospital
            )
        except EnhancedStaffProfile.DoesNotExist:
            return JsonResponse({"error": "Staff member not found or not authorized to access"}, status=404)
        
        # Serialize staff data
        staff = {
            "id": str(staff_member.id),
            "name": staff_member.user.full_name,
            "email": staff_member.user.email,
            "role": staff_member.job_title,
            "department": staff_member.department,
            "status": "active" if staff_member.is_active else "inactive",
            "phone": staff_member.work_phone or "",
            "hire_date": staff_member.hire_date.isoformat() if staff_member.hire_date else "",
            "specializations": [staff_member.specialization.name] if staff_member.specialization else []
        }
        
        return JsonResponse({"staff": staff})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
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
@require_http_methods(["PUT", "OPTIONS"])
def update_staff(request, pk):
    """Update staff member information"""
    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Extract the actual Django user from the AuthenticatedUser wrapper
        if hasattr(user, 'user'):
            django_user = user.user
        else:
            django_user = user
            
        # Get the staff profile for the authenticated user
        try:
            staff_profile = EnhancedStaffProfile.objects.get(user=django_user)
        except EnhancedStaffProfile.DoesNotExist:
            return JsonResponse({"error": "Staff profile not found"}, status=404)
            
        # Check if the staff profile is associated with a hospital
        hospital = getattr(staff_profile, 'hospital', None)
        if not hospital:
            return JsonResponse({"error": "No hospital associated with staff profile"}, status=400)
        
        # Get the staff member to update, ensuring they belong to the same hospital
        try:
            staff_to_update = EnhancedStaffProfile.objects.select_related('user').get(
                id=pk,
                hospital=hospital  # This ensures the staff member belongs to the same hospital
            )
        except EnhancedStaffProfile.DoesNotExist:
            return JsonResponse({"error": "Staff member not found or not authorized to update"}, status=404)
        
        # Parse request data
        data = json.loads(request.body)
        
        # Update staff member information
        if 'name' in data and data['name']:
            name_parts = data['name'].split(' ', 1)
            staff_to_update.user.first_name = name_parts[0]
            staff_to_update.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            staff_to_update.user.save()
            
        if 'email' in data and data['email']:
            staff_to_update.user.email = data['email']
            staff_to_update.user.save()
            
        if 'role' in data:
            staff_to_update.job_title = data['role']
            
        if 'department' in data:
            staff_to_update.department = data['department']
            
        if 'status' in data:
            staff_to_update.is_active = data['status'] == 'active'
            
        # Save the updated staff profile
        staff_to_update.save()
        
        # Return the updated staff data
        staff = {
            "id": str(staff_to_update.id),
            "name": staff_to_update.user.full_name,
            "email": staff_to_update.user.email,
            "role": staff_to_update.job_title,
            "department": staff_to_update.department,
            "status": "active" if staff_to_update.is_active else "inactive"
        }
        
        return JsonResponse({"staff": staff, "message": "Staff member updated successfully"})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
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
@require_http_methods(["GET", "OPTIONS"])
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
@require_http_methods(["GET", "OPTIONS"])
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
@require_http_methods(["GET", "OPTIONS"])
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
@require_http_methods(["PUT", "OPTIONS"])
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
@require_http_methods(["DELETE", "OPTIONS"])
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


@api_csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def create_patient(request):
    """Create a new patient with optional account creation"""
    logger = logging.getLogger(__name__)
    
    # Get authenticated user using unified middleware
    auth_user = get_request_user(request)
    if not auth_user:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    logger.debug(f"Authenticated user: {auth_user}")
    
    # Extract the actual Django user from the AuthenticatedUser wrapper
    if hasattr(auth_user, 'user'):
        user = auth_user.user
    else:
        user = auth_user
    
    logger.debug(f"Django user: {user}")
    
    # Ensure the user is a valid Django User instance
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not isinstance(user, User):
        logger.error(f"Invalid user object type: {type(user)}")
        return JsonResponse({"error": "Invalid user object"}, status=400)
    
    # Retrieve the staff profile for the authenticated user
    try:
        staff_profile = EnhancedStaffProfile.objects.get(user=user)
        logger.debug(f"Staff profile: {staff_profile}")
    except EnhancedStaffProfile.DoesNotExist:
        logger.warning("No staff profile found for the authenticated user.")
        return JsonResponse({"error": "Staff profile not found"}, status=404)
    
    # Check if the staff profile is associated with a hospital
    hospital = getattr(staff_profile, 'hospital', None)
    if not hospital:
        logger.warning("No hospital associated with staff profile.")
        return JsonResponse({"error": "No hospital associated with staff profile"}, status=400)
    
    logger.debug(f"Hospital associated with staff profile: {hospital}")
    logger.info(f"Create patient request from authenticated user: {user.id}")

    try:
        from .models import EnhancedPatient
        from datetime import datetime
        
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
            'username': data['email'],
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
        
        # Create EnhancedPatient
        patient_data = {
            'user': patient_user,
            'date_of_birth': datetime.strptime(data['dateOfBirth'], '%Y-%m-%d').date(),
            'gender': gender_mapping.get(data['gender'], 'O'),
            'phone': data['phone'],
            'created_by': user,
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
        
        # Create hospital-patient relationship
        logger.debug(f"Hospital for relationship: {hospital}")
        if hospital:
            from .models import HospitalPatient
            HospitalPatient.objects.create(
                hospital=hospital,
                patient=patient,
                relationship_type='admin_added',
                status='active',
                added_by=user,
                notes=f"Patient added by {user.full_name}"
            )
        
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
            response_data['accountCreated'] = True
            response_data['message'] = "Patient created successfully with account"
        else:
            response_data['accountCreated'] = False
            response_data['message'] = "Patient created successfully without account"
        
        logger.info(f"Patient created successfully: {patient.id}")
        return JsonResponse(response_data, status=201)
        
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)