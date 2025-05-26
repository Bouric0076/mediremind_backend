from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from supabase_client import supabase, admin_client
from authapp.utils import get_authenticated_user
from datetime import datetime, timedelta
from appointments.utils import (
    validate_appointment_type,
    validate_appointment_datetime,
    check_doctor_availability,
    check_patient_availability,
    validate_appointment_status,
    get_filtered_appointments
)
from notifications.utils import send_appointment_confirmation, send_appointment_update

def verify_patient_auth(request):
    """Helper function to verify patient authentication and role"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        print("No Authorization header found")
        return None, JsonResponse({"error": "Authorization header missing"}, status=401)
        
    if not auth_header.startswith('Bearer '):
        print("Invalid Authorization header format")
        return None, JsonResponse({"error": "Invalid Authorization header format. Must start with 'Bearer '"}, status=401)
    
    token = auth_header.split(' ')[1]
    print(f"Verifying token: {token[:10]}...")  # Log first 10 chars of token
    
    user = get_authenticated_user(token)
    if not user:
        print("Failed to authenticate user with token")
        return None, JsonResponse({"error": "Invalid or expired token"}, status=401)

    if not user.id:
        print(f"No user ID found in authenticated user")
        return None, JsonResponse({"error": "Invalid user data"}, status=401)

    try:
        if not user.profile:
            print(f"No profile found for user {user.id}")
            return None, JsonResponse({"error": "User profile not found"}, status=404)
            
        if user.profile.get('role') != 'patient':
            print(f"Invalid role for user {user.id}: {user.profile.get('role')}")
            return None, JsonResponse({
                "error": "Unauthorized. Only patients can access this endpoint",
                "details": f"User role '{user.profile.get('role')}' is not authorized"
            }, status=403)

        print(f"Successfully verified patient: {user.id}")
        return user, None
    except Exception as e:
        print(f"Auth verification error: {str(e)}")
        return None, JsonResponse({"error": "Authentication verification failed"}, status=500)

@csrf_exempt
def patient_dashboard(request):
    """Patient dashboard endpoint - returns profile and any additional dashboard data"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_patient_auth(request)
    if error_response:
        return error_response

    try:
        # Get patient profile using admin_client
        result = admin_client.table("patients").select("*").eq("user_id", user.id).execute()
        
        if not result.data or len(result.data) == 0:
            return JsonResponse({"error": "Patient profile not found"}, status=404)

        dashboard_data = {
            "profile": result.data[0],
            "user_id": user.id,
            "role": "patient"
        }

        return JsonResponse({
            "message": "Dashboard data retrieved successfully",
            "data": dashboard_data
        }, status=200)

    except Exception as e:
        print(f"Patient dashboard error: {str(e)}")
        return JsonResponse({"error": "Failed to retrieve dashboard data"}, status=500)

@csrf_exempt
def patient_profile(request):
    """Patient profile management endpoint - handles profile retrieval"""
    user, error_response = verify_patient_auth(request)
    if error_response:
        return error_response

    try:
        if request.method == "GET":
            # Get patient profile using admin_client
            result = admin_client.table("patients").select("*").eq("user_id", user.id).execute()
            
            if not result.data or len(result.data) == 0:
                return JsonResponse({"error": "Profile not found"}, status=404)

            return JsonResponse({
                "message": "Profile retrieved successfully",
                "profile": result.data[0]
            }, status=200)
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)

    except Exception as e:
        print(f"Patient profile error: {str(e)}")
        return JsonResponse({"error": "Failed to process profile request"}, status=500)

@csrf_exempt
def get_patient_profile(request):
    if request.method == "GET":
        user_id = request.headers.get("user_id")
        try:
            res = admin_client.table("patients").select("*").eq("user_id", user_id).single().execute()
            profile = res.data
            return JsonResponse({"profile": profile}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def update_patient_profile(request):
    """Dedicated endpoint for updating patient profile"""
    if request.method != "PUT":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_patient_auth(request)
    if error_response:
        return error_response

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body",
            "details": "Please ensure the request body contains valid JSON data"
        }, status=400)

    if not data:
        return JsonResponse({
            "error": "Empty request body",
            "details": "Please provide data to update"
        }, status=400)

    # Define updateable fields and their validation rules
    updateable_fields = {
        "full_name": str,
        "phone": str,
        "email": str,
        "gender": str,
        "date_of_birth": str,
        "emergency_contact": str
    }

    # Filter and validate update data
    update_data = {}
    validation_errors = []

    for field, value in data.items():
        if field in updateable_fields:
            if value is None:
                continue
            try:
                # Validate field type
                expected_type = updateable_fields[field]
                if not isinstance(value, expected_type):
                    validation_errors.append(f"{field} must be of type {expected_type._name_}")
                else:
                    update_data[field] = value
            except Exception as e:
                validation_errors.append(f"Error validating {field}: {str(e)}")

    if validation_errors:
        return JsonResponse({
            "error": "Validation failed",
            "details": validation_errors
        }, status=400)

    if not update_data:
        return JsonResponse({
            "error": "No valid fields to update",
            "details": f"Allowed fields are: {', '.join(updateable_fields.keys())}"
        }, status=400)

    try:
        # Update patient profile using admin_client
        profile_result = admin_client.table("patients").update(update_data).eq("user_id", user.id).execute()
        
        if not profile_result.data:
            return JsonResponse({"error": "Failed to update patient profile"}, status=500)

        # Update users table with relevant fields using admin_client
        user_update_data = {k: v for k, v in update_data.items() if k in ["full_name", "phone", "email"]}
        if user_update_data:
            admin_client.table("users").update(user_update_data).eq("id", user.id).execute()

        return JsonResponse({
            "message": "Profile updated successfully",
            "profile": profile_result.data[0]
        }, status=200)

    except Exception as e:
        print(f"Profile update error: {str(e)}")
        return JsonResponse({
            "error": "Failed to update profile",
            "details": str(e)
        }, status=500)

@csrf_exempt
def view_appointments(request):
    """Endpoint for patients to view their appointments with filtering"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_patient_auth(request)
    if error_response:
        return error_response

    # Get filter parameters from query string
    filters = {
        'status': request.GET.get('status'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
        'type': request.GET.get('type')  # 'upcoming' or 'past'
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    success, result = get_filtered_appointments(user.id, is_doctor=False, **filters)
    
    if not success:
        return JsonResponse({
            "error": "Failed to retrieve appointments",
            "details": result
        }, status=500)

    return JsonResponse({
        "message": "Appointments retrieved successfully",
        "appointments": result
    }, status=200)

@csrf_exempt
def request_appointment(request):
    """Endpoint for patients to request new appointments"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_patient_auth(request)
    if error_response:
        return error_response

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        return JsonResponse({
            "error": "Invalid JSON in request body",
            "details": str(e)
        }, status=400)

    # Validate required fields
    required_fields = ["doctor_id", "date", "time", "type"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return JsonResponse({
            "error": "Missing required fields",
            "details": f"Please provide: {', '.join(missing_fields)}"
        }, status=400)

    # Validate appointment type
    valid, error_msg = validate_appointment_type(data["type"])
    if not valid:
        return JsonResponse({
            "error": "Invalid appointment type",
            "details": error_msg
        }, status=400)

    # Validate date and time
    valid, error_msg = validate_appointment_datetime(data["date"], data["time"])
    if not valid:
        return JsonResponse({
            "error": "Invalid appointment date/time",
            "details": error_msg
        }, status=400)

    # Verify doctor exists
    doctor_result = admin_client.table("staff_profiles").select("*").eq("user_id", data["doctor_id"]).execute()
    if not doctor_result.data:
        return JsonResponse({
            "error": "Doctor not found",
            "details": "Please provide a valid doctor ID"
        }, status=400)

    # Check doctor availability
    valid, error_msg = check_doctor_availability(data["doctor_id"], data["date"], data["time"])
    if not valid:
        return JsonResponse({
            "error": "Time slot not available",
            "details": error_msg
        }, status=409)

    # Check patient availability
    valid, error_msg = check_patient_availability(user.id, data["date"], data["time"])
    if not valid:
        return JsonResponse({
            "error": "You already have an appointment at this time",
            "details": error_msg
        }, status=409)

    try:
        # Create appointment
        appointment_data = {
            "patient_id": user.id,
            "doctor_id": data["doctor_id"],
            "date": data["date"],
            "time": data["time"],
            "type": data["type"].lower(),
            "location_text": data.get("location_text", "Main Hospital"),
            "status": "requested",
            "initiated_by": "patient",
            "notes": data.get("notes", ""),
            "preferred_channel": data.get("preferred_channel", "sms")
        }

        result = admin_client.table("appointments").insert(appointment_data).execute()
        
        if not result.data:
            return JsonResponse({
                "error": "Failed to create appointment",
                "details": "Database error occurred"
            }, status=500)

        # Fetch patient and doctor emails
        appointment_id = result.data[0]["id"]
        patient_email = user.profile.get('email')
        doctor_result = admin_client.table("staff_profiles").select("email").eq("user_id", data["doctor_id"]).single().execute()
        doctor_email = doctor_result.data["email"] if doctor_result.data else None

        # Send notification to both
        send_success, send_message = send_appointment_confirmation(appointment_id, patient_email=patient_email, doctor_email=doctor_email)
        if not send_success:
            print(f"Failed to send appointment confirmation: {send_message}")

        return JsonResponse({
            "message": "Appointment request sent successfully",
            "appointment": result.data[0]
        }, status=201)

    except Exception as e:
        print(f"Request appointment error: {str(e)}")
        return JsonResponse({
            "error": "Failed to create appointment request",
            "details": str(e)
        }, status=500)

@csrf_exempt
def respond_to_appointment(request, appointment_id):
    """Endpoint for patients to respond to appointments"""
    if request.method != "PUT":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_patient_auth(request)
    if error_response:
        return error_response

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        return JsonResponse({
            "error": "Invalid JSON in request body",
            "details": str(e)
        }, status=400)

    if "status" not in data:
        return JsonResponse({
            "error": "Missing status field",
            "details": "Please provide a status: confirmed, declined, or reschedule_requested"
        }, status=400)

    # Validate status
    valid, error_msg = validate_appointment_status(data["status"], is_doctor=False)
    if not valid:
        return JsonResponse({
            "error": "Invalid status",
            "details": error_msg
        }, status=400)

    try:
        # Verify appointment exists and belongs to patient
        appointment_result = admin_client.table("appointments").select("*").eq("id", appointment_id).eq("patient_id", user.id).execute()
        
        if not appointment_result.data:
            return JsonResponse({
                "error": "Appointment not found",
                "details": "Invalid appointment ID or unauthorized access"
            }, status=404)

        current_status = appointment_result.data[0]["status"]
        if current_status in ["cancelled", "completed"]:
            return JsonResponse({
                "error": "Cannot update appointment",
                "details": f"Appointment is already {current_status}"
            }, status=400)

        # Update appointment
        update_data = {
            "status": data["status"],
            "notes": data.get("notes", "")
        }
        result = admin_client.table("appointments").update(update_data).eq("id", appointment_id).execute()
        
        if not result.data:
            return JsonResponse({
                "error": "Failed to update appointment",
                "details": "Database error occurred"
            }, status=500)

        # Fetch patient and doctor emails
        patient_email = user.profile.get('email')
        doctor_id = appointment_result.data[0]["doctor_id"]
        doctor_result = admin_client.table("staff_profiles").select("email").eq("user_id", doctor_id).single().execute()
        doctor_email = doctor_result.data["email"] if doctor_result.data else None

        # Send notification to both
        if data["status"] == "confirmed":
            send_success, send_message = send_appointment_confirmation(
                appointment_id, patient_email=patient_email, doctor_email=doctor_email
            )
        elif data["status"] == "reschedule_requested":
            send_success, send_message = send_appointment_update(
                appointment_id, "reschedule", patient_email=patient_email, doctor_email=doctor_email
            )
        elif data["status"] == "declined":
            send_success, send_message = send_appointment_update(
                appointment_id, "cancellation", patient_email=patient_email, doctor_email=doctor_email
            )
        else:
            send_success, send_message = (True, "No notification needed")

        if not send_success:
            print(f"Failed to send appointment notification: {send_message}")

        return JsonResponse({
            "message": "Appointment updated successfully",
            "appointment": result.data[0]
        })

    except Exception as e:
        print(f"Respond to appointment error: {str(e)}")
        return JsonResponse({
            "error": "Failed to process appointment response",
            "details": str(e)
        }, status=500)

def verify_staff_auth(request):
    """Helper function to verify staff authentication and role"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        print("No Authorization header found")
        return None, JsonResponse({"error": "Authorization header missing"}, status=401)
        
    if not auth_header.startswith('Bearer '):
        print("Invalid Authorization header format")
        return None, JsonResponse({"error": "Invalid Authorization header format. Must start with 'Bearer '"}, status=401)
    
    token = auth_header.split(' ')[1]
    print(f"Verifying token: {token[:10]}...")  # Log first 10 chars of token
    
    user = get_authenticated_user(token)
    if not user:
        print("Failed to authenticate user with token")
        return None, JsonResponse({"error": "Invalid or expired token"}, status=401)

    if not user.id:
        print(f"No user ID found in authenticated user")
        return None, JsonResponse({"error": "Invalid user data"}, status=401)

    try:
        if not user.profile:
            print(f"No profile found for user {user.id}")
            return None, JsonResponse({"error": "User profile not found"}, status=404)
            
        if user.profile.get('role') not in ['doctor', 'staff']:
            print(f"Invalid role for user {user.id}: {user.profile.get('role')}")
            return None, JsonResponse({
                "error": "Unauthorized. Only staff members can access this endpoint",
                "details": f"User role '{user.profile.get('role')}' is not authorized"
            }, status=403)

        print(f"Successfully verified staff member: {user.id}")
        return user, None
    except Exception as e:
        print(f"Auth verification error: {str(e)}")
        return None, JsonResponse({"error": "Authentication verification failed"}, status=500)

@csrf_exempt
def get_all_patients(request):
    """Endpoint to get all available patients"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_staff_auth(request)
    if error_response:
        return error_response

    try:
        # Get all patients with their basic information
        result = admin_client.table("patients").select(
            "user_id",
            "full_name",
            "phone",
            "email",
            "gender",
            "date_of_birth"
        ).execute()

        if not result.data:
            return JsonResponse({
                "message": "No patients found",
                "patients": []
            }, status=200)

        return JsonResponse({
            "message": "Patients retrieved successfully",
            "patients": result.data
        }, status=200)

    except Exception as e:
        print(f"Get all patients error: {str(e)}")
        return JsonResponse({
            "error": "Failed to retrieve patients",
            "details": str(e)
        }, status=500)
