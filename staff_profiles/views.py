from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from supabase_client import supabase, admin_client
from authapp.utils import get_authenticated_user
from datetime import datetime, timedelta
from appointments.utils import validate_appointment_status
from appointments.utils import (
    validate_appointment_type,
    validate_appointment_datetime,
    check_doctor_availability,
    check_patient_availability,
    get_filtered_appointments
)
from notifications.utils import send_appointment_confirmation, send_appointment_update

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
            
        if user.profile.get('role') not in ['doctor', 'admin']:
            print(f"Invalid role for user {user.id}: {user.profile.get('role')}")
            return None, JsonResponse({
                "error": "Unauthorized. Only staff members can access this endpoint",
                "details": f"User role '{user.profile.get('role')}' is not authorized"
            }, status=403)

        print(f"Successfully verified staff member: {user.id} with role: {user.profile.get('role')}")
        return user, None
    except Exception as e:
        print(f"Auth verification error: {str(e)}")
        return None, JsonResponse({"error": "Authentication verification failed"}, status=500)

@csrf_exempt
def staff_dashboard(request):
    """Staff dashboard endpoint - returns profile and any additional dashboard data"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_staff_auth(request)
    if error_response:
        return error_response

    try:
        # Get staff profile using admin_client
        result = admin_client.table("staff_profiles").select("*").eq("user_id", user.id).execute()
        
        if not result.data or len(result.data) == 0:
            return JsonResponse({"error": "Staff profile not found"}, status=404)

        dashboard_data = {
            "profile": result.data[0],
            "user_id": user.id,
            "role": user.profile.get('role')
        }

        return JsonResponse({
            "message": "Dashboard data retrieved successfully",
            "data": dashboard_data
        }, status=200)

    except Exception as e:
        print(f"Staff dashboard error: {str(e)}")
        return JsonResponse({
            "error": "Failed to retrieve dashboard data",
            "details": str(e)
        }, status=500)

@csrf_exempt
def staff_profile(request):
    """Staff profile management endpoint - handles profile retrieval"""
    user, error_response = verify_staff_auth(request)
    if error_response:
        return error_response

    try:
        if request.method == "GET":
            # Get staff profile using admin_client
            result = admin_client.table("staff_profiles").select("*").eq("user_id", user.id).execute()
            
            if not result.data or len(result.data) == 0:
                return JsonResponse({"error": "Profile not found"}, status=404)

            return JsonResponse({
                "message": "Profile retrieved successfully",
                "profile": result.data[0]
            }, status=200)
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)

    except Exception as e:
        print(f"Staff profile error: {str(e)}")
        return JsonResponse({
            "error": "Failed to process profile request",
            "details": str(e)
        }, status=500)

@csrf_exempt
def update_staff_profile(request):
    """Dedicated endpoint for updating staff profile"""
    if request.method != "PUT":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_staff_auth(request)
    if error_response:
        return error_response

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in request body: {str(e)}")
        return JsonResponse({
            "error": "Invalid JSON in request body",
            "details": str(e)
        }, status=400)

    if not data:
        print("Empty request body received")
        return JsonResponse({
            "error": "Empty request body",
            "details": "Please provide data to update"
        }, status=400)

    # Define updateable fields and their validation rules
    updateable_fields = {
        "full_name": str,
        "phone": str,
        "email": str,
        "department": str,
        "position": str,
        "staff_no": str,
        "branch": str
    }

    # Filter and validate update data
    update_data = {}
    validation_errors = []

    for field, value in data.items():
        if field in updateable_fields:
            if value is None or value == "":  # Handle both None and empty string
                continue
            try:
                # Validate field type
                expected_type = updateable_fields[field]
                if not isinstance(value, expected_type):
                    error_msg = f"{field} must be of type {expected_type.__name__}"
                    print(f"Validation error: {error_msg}")
                    validation_errors.append(error_msg)
                else:
                    # Trim whitespace from string values
                    if isinstance(value, str):
                        value = value.strip()
                    update_data[field] = value
            except Exception as e:
                error_msg = f"Error validating {field}: {str(e)}"
                print(error_msg)
                validation_errors.append(error_msg)

    if validation_errors:
        return JsonResponse({
            "error": "Validation failed",
            "details": validation_errors
        }, status=400)

    if not update_data:
        print("No valid fields to update")
        return JsonResponse({
            "error": "No valid fields to update",
            "details": f"Allowed fields are: {', '.join(updateable_fields.keys())}"
        }, status=400)

    try:
        # Update staff profile using admin_client
        print(f"Updating staff profile for user {user.id} with data: {update_data}")
        profile_result = admin_client.table("staff_profiles").update(update_data).eq("user_id", user.id).execute()
        
        if not profile_result.data:
            print(f"Failed to update staff profile for user {user.id}")
            return JsonResponse({"error": "Failed to update staff profile"}, status=500)

        # Update users table with relevant fields using admin_client
        user_update_data = {k: v for k, v in update_data.items() if k in ["full_name", "phone", "email"]}
        if user_update_data:
            print(f"Updating user record for user {user.id} with data: {user_update_data}")
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
    """Endpoint for doctors to view their appointments with filtering"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_staff_auth(request)
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

    success, result = get_filtered_appointments(user.id, is_doctor=True, **filters)
    
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
def schedule_appointment(request):
    """Endpoint for doctors to schedule appointments"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_staff_auth(request)
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
    required_fields = ["patient_id", "date", "time", "type"]
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

    # Verify patient exists
    patient_result = admin_client.table("patients").select("*").eq("user_id", data["patient_id"]).execute()
    if not patient_result.data:
        return JsonResponse({
            "error": "Patient not found",
            "details": "Please provide a valid patient ID"
        }, status=400)

    # Check doctor availability
    valid, error_msg = check_doctor_availability(user.id, data["date"], data["time"])
    if not valid:
        return JsonResponse({
            "error": "Time slot not available",
            "details": error_msg
        }, status=409)

    # Check patient availability
    valid, error_msg = check_patient_availability(data["patient_id"], data["date"], data["time"])
    if not valid:
        return JsonResponse({
            "error": "Patient unavailable",
            "details": error_msg
        }, status=409)

    try:
        # Create appointment
        appointment_data = {
            "patient_id": data["patient_id"],
            "doctor_id": user.id,
            "date": data["date"],
            "time": data["time"],
            "type": data["type"].lower(),
            "location_text": data.get("location_text", "Main Hospital"),
            "status": "scheduled",
            "initiated_by": "doctor",
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
        doctor_email = user.profile.get('email')
        patient_result = admin_client.table("patients").select("email").eq("user_id", data["patient_id"]).single().execute()
        patient_email = patient_result.data["email"] if patient_result.data else None

        # Send notification to both
        send_success, send_message = send_appointment_confirmation(appointment_id, patient_email=patient_email, doctor_email=doctor_email)
        if not send_success:
            print(f"Failed to send appointment confirmation: {send_message}")

        return JsonResponse({
            "message": "Appointment scheduled successfully",
            "appointment": result.data[0]
        }, status=201)

    except Exception as e:
        print(f"Schedule appointment error: {str(e)}")
        return JsonResponse({
            "error": "Failed to schedule appointment",
            "details": str(e)
        }, status=500)

@csrf_exempt
def respond_to_request(request, appointment_id):
    """Endpoint for doctors to respond to appointment requests"""
    if request.method != "PUT":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user, error_response = verify_staff_auth(request)
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
            "details": "Please provide a status: approved, rejected, or reschedule"
        }, status=400)

    # Validate status
    valid, error_msg = validate_appointment_status(data["status"], is_doctor=True)
    if not valid:
        return JsonResponse({
            "error": "Invalid status",
            "details": error_msg
        }, status=400)

    try:
        # Verify appointment exists and belongs to doctor
        appointment_result = admin_client.table("appointments").select("*").eq("id", appointment_id).eq("doctor_id", user.id).execute()
        
        if not appointment_result.data:
            return JsonResponse({
                "error": "Appointment not found",
                "details": "Invalid appointment ID or unauthorized access"
            }, status=404)

        current_status = appointment_result.data[0]["status"]
        if current_status not in ["requested", "reschedule_requested"]:
            return JsonResponse({
                "error": "Cannot update appointment",
                "details": f"Appointment is in {current_status} state"
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
        doctor_email = user.profile.get('email')
        patient_id = appointment_result.data[0]["patient_id"]
        patient_result = admin_client.table("patients").select("email").eq("user_id", patient_id).single().execute()
        patient_email = patient_result.data["email"] if patient_result.data else None

        # Send notification to both
        if data["status"] == "approved":
            send_success, send_message = send_appointment_confirmation(
                appointment_id, patient_email=patient_email, doctor_email=doctor_email
            )
        elif data["status"] == "reschedule":
            send_success, send_message = send_appointment_update(
                appointment_id, "reschedule", patient_email=patient_email, doctor_email=doctor_email
            )
        else:  # rejected
            send_success, send_message = send_appointment_update(
                appointment_id, "cancellation", patient_email=patient_email, doctor_email=doctor_email
            )

        if not send_success:
            print(f"Failed to send appointment notification: {send_message}")

        return JsonResponse({
            "message": "Appointment updated successfully",
            "appointment": result.data[0]
        })

    except Exception as e:
        print(f"Respond to request error: {str(e)}")
        return JsonResponse({
            "error": "Failed to process appointment response",
            "details": str(e)
        }, status=500)

@csrf_exempt
def get_available_doctors(request):
    """Endpoint to fetch all available doctors"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify user authentication (any authenticated user can fetch doctors)
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return JsonResponse({"error": "Authorization header missing"}, status=401)
        
    if not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Invalid Authorization header format"}, status=401)
    
    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    try:
        # First get all users with doctor role
        doctor_users = admin_client.table("users").select("id").eq("role", "doctor").execute()
        
        if not doctor_users.data:
            return JsonResponse({
                "message": "No doctors found",
                "doctors": []
            }, status=200)

        # Get doctor IDs
        doctor_ids = [doc["id"] for doc in doctor_users.data]

        # Then get staff profiles for those doctors
        result = admin_client.table("staff_profiles") \
            .select("user_id, full_name, position, email, phone") \
            .in_("user_id", doctor_ids) \
            .execute()

        if not result.data:
            return JsonResponse({
                "message": "No doctors found",
                "doctors": []
            }, status=200)

        # Format the response
        doctors = [{
            "id": doc["user_id"],  # Using user_id as the doctor's ID
            "full_name": doc["full_name"],
            "position": doc.get("position", "General"),
            "email": doc.get("email"),
            "phone_number": doc.get("phone")
        } for doc in result.data]

        return JsonResponse({
            "message": "Doctors retrieved successfully",
            "doctors": doctors
        }, status=200)

    except Exception as e:
        print(f"Error fetching doctors: {str(e)}")
        return JsonResponse({
            "error": "Failed to retrieve doctors",
            "details": str(e)
        }, status=500)