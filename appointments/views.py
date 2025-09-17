from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from supabase_client import admin_client
from authentication.utils import get_authenticated_user
from authentication.middleware import api_csrf_exempt, get_request_user
from .utils import (
    validate_appointment_datetime,
    check_doctor_availability,
    check_patient_availability,
    validate_appointment_type,
    validate_appointment_status,
    get_filtered_appointments
)
from notifications.utils import send_appointment_confirmation, send_appointment_update
import json
import uuid
from datetime import datetime, timedelta


def send_appointment_notification(appointment_data, action, patient_email, doctor_email):
    """Send appointment notifications"""
    try:
        # Format the notification message based on action
        if action == "created":
            message = f"New appointment scheduled for {appointment_data['date']} at {appointment_data['time']}"
        elif action == "updated":
            message = f"Appointment updated for {appointment_data['date']} at {appointment_data['time']}"
        elif action == "cancelled":
            message = f"Appointment cancelled for {appointment_data['date']} at {appointment_data['time']}"
        else:
            message = f"Appointment {action} for {appointment_data['date']} at {appointment_data['time']}"
        
        # Send notifications (implement based on your notification system)
        print(f"Notification sent: {message} to {patient_email} and {doctor_email}")
        
    except Exception as e:
        print(f"Failed to send notification: {str(e)}")


@api_csrf_exempt
def create_appointment(request):
    """Create a new appointment - accessible by both staff and patients"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Get authenticated user using unified middleware
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        data = json.loads(request.body)
        
        # Required fields
        required_fields = ["doctor_id", "patient_id", "date", "time", "type"]
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    "error": f"Missing required field: {field}"
                }, status=400)

        # Validate appointment type
        valid, error_msg = validate_appointment_type(data["type"])
        if not valid:
            return JsonResponse({"error": error_msg}, status=400)

        # Validate date and time
        valid, error_msg = validate_appointment_datetime(data["date"], data["time"])
        if not valid:
            return JsonResponse({"error": error_msg}, status=400)

        # Verify doctor exists
        doctor_result = admin_client.table("staff_profiles").select("*").eq("user_id", data["doctor_id"]).execute()
        if not doctor_result.data:
            return JsonResponse({"error": "Doctor not found"}, status=400)

        # Verify patient exists
        patient_result = admin_client.table("enhanced_patients").select("*").eq("user_id", data["patient_id"]).execute()
        if not patient_result.data:
            return JsonResponse({"error": "Patient not found"}, status=400)

        # Check doctor availability
        valid, error_msg = check_doctor_availability(data["doctor_id"], data["date"], data["time"])
        if not valid:
            return JsonResponse({"error": error_msg}, status=409)

        # Check patient availability
        valid, error_msg = check_patient_availability(data["patient_id"], data["date"], data["time"])
        if not valid:
            return JsonResponse({"error": error_msg}, status=409)

        # Determine initial status based on who's creating
        user_role = user.profile.get('role', 'patient')
        if user_role == 'doctor' or user_role == 'admin':
            initial_status = "scheduled"
        else:
            initial_status = "requested"

        # Create appointment
        appointment_data = {
            "id": str(uuid.uuid4()),
            "patient_id": data["patient_id"],
            "doctor_id": data["doctor_id"],
            "date": data["date"],
            "time": data["time"],
            "type": data["type"].lower(),
            "location_text": data.get("location_text", "Main Hospital"),
            "status": initial_status,
            "initiated_by": user_role,
            "notes": data.get("notes", ""),
            "preferred_channel": data.get("preferred_channel", "sms"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        result = admin_client.table("appointments").insert(appointment_data).execute()
        
        if result.data:
            # Send confirmation notification
            try:
                patient_email = patient_result.data[0].get('email')
                doctor_email = doctor_result.data[0].get('email')
                send_appointment_notification(result.data[0], "created", patient_email, doctor_email)
            except Exception as e:
                print(f"Notification error: {str(e)}")

            return JsonResponse({
                "message": "Appointment created successfully",
                "appointment": result.data[0]
            }, status=201)
        else:
            return JsonResponse({"error": "Failed to create appointment"}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@csrf_exempt
def get_appointment(request, appointment_id):
    """Get a specific appointment by ID"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        # Get appointment with patient and doctor details
        result = admin_client.table("appointments").select(
            "*",
            "patient:patient_id(user_id, full_name, phone, email)",
            "doctor:doctor_id(user_id, full_name, position, email)"
        ).eq("id", appointment_id).execute()

        if not result.data:
            return JsonResponse({"error": "Appointment not found"}, status=404)

        appointment = result.data[0]
        
        # Check if user has permission to view this appointment
        user_role = user.profile.get('role', 'patient')
        if user_role not in ['admin', 'doctor']:
            # Patients can only view their own appointments
            if appointment['patient_id'] != user.id:
                return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role == 'doctor':
            # Doctors can only view their own appointments
            if appointment['doctor_id'] != user.id:
                return JsonResponse({"error": "Permission denied"}, status=403)

        return JsonResponse({
            "message": "Appointment retrieved successfully",
            "appointment": appointment
        }, status=200)

    except Exception as e:
        print(f"Get appointment error: {str(e)}")
        return JsonResponse({"error": "Failed to retrieve appointment"}, status=500)


@csrf_exempt
def update_appointment(request, appointment_id):
    """Update an existing appointment"""
    if request.method != "PUT":
        return JsonResponse({"error": "Method not allowed"}, status=405)

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
        
        # Get existing appointment
        existing_result = admin_client.table("appointments").select("*").eq("id", appointment_id).execute()
        if not existing_result.data:
            return JsonResponse({"error": "Appointment not found"}, status=404)

        existing_appointment = existing_result.data[0]
        user_role = user.profile.get('role', 'patient')
        
        # Check permissions
        if user_role not in ['admin', 'doctor']:
            if existing_appointment['patient_id'] != user.id:
                return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role == 'doctor':
            if existing_appointment['doctor_id'] != user.id:
                return JsonResponse({"error": "Permission denied"}, status=403)

        # Prepare update data
        update_data = {"updated_at": datetime.now().isoformat()}
        
        # Handle different update scenarios
        if "status" in data:
            valid, error_msg = validate_appointment_status(data["status"], user_role == 'doctor')
            if not valid:
                return JsonResponse({"error": error_msg}, status=400)
            update_data["status"] = data["status"]

        if "date" in data or "time" in data:
            new_date = data.get("date", existing_appointment["date"])
            new_time = data.get("time", existing_appointment["time"])
            
            # Validate new date/time
            valid, error_msg = validate_appointment_datetime(new_date, new_time)
            if not valid:
                return JsonResponse({"error": error_msg}, status=400)

            # Check availability (excluding current appointment)
            valid, error_msg = check_doctor_availability(
                existing_appointment["doctor_id"], new_date, new_time, appointment_id
            )
            if not valid:
                return JsonResponse({"error": error_msg}, status=409)

            valid, error_msg = check_patient_availability(
                existing_appointment["patient_id"], new_date, new_time, appointment_id
            )
            if not valid:
                return JsonResponse({"error": error_msg}, status=409)

            update_data["date"] = new_date
            update_data["time"] = new_time

        # Update other fields
        updatable_fields = ["notes", "location_text", "preferred_channel", "type"]
        for field in updatable_fields:
            if field in data:
                if field == "type":
                    valid, error_msg = validate_appointment_type(data[field])
                    if not valid:
                        return JsonResponse({"error": error_msg}, status=400)
                update_data[field] = data[field]

        # Perform update
        result = admin_client.table("appointments").update(update_data).eq("id", appointment_id).execute()
        
        if result.data:
            # Send update notification
            try:
                patient_result = admin_client.table("enhanced_patients").select("email").eq("user_id", existing_appointment["patient_id"]).execute()
                doctor_result = admin_client.table("staff_profiles").select("email").eq("user_id", existing_appointment["doctor_id"]).execute()
                
                if patient_result.data and doctor_result.data:
                    send_appointment_notification(
                        result.data[0], "updated", 
                        patient_result.data[0].get('email'),
                        doctor_result.data[0].get('email')
                    )
            except Exception as e:
                print(f"Notification error: {str(e)}")

            return JsonResponse({
                "message": "Appointment updated successfully",
                "appointment": result.data[0]
            }, status=200)
        else:
            return JsonResponse({"error": "Failed to update appointment"}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@csrf_exempt
def delete_appointment(request, appointment_id):
    """Delete an appointment"""
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        # Get existing appointment
        existing_result = admin_client.table("appointments").select("*").eq("id", appointment_id).execute()
        if not existing_result.data:
            return JsonResponse({"error": "Appointment not found"}, status=404)

        existing_appointment = existing_result.data[0]
        user_role = user.profile.get('role', 'patient')
        
        # Check permissions - only doctors and admins can delete appointments
        if user_role not in ['admin', 'doctor']:
            return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role == 'doctor':
            if existing_appointment['doctor_id'] != user.id:
                return JsonResponse({"error": "Permission denied"}, status=403)

        # Perform deletion
        result = admin_client.table("appointments").delete().eq("id", appointment_id).execute()
        
        if result.data:
            # Send cancellation notification
            try:
                patient_result = admin_client.table("enhanced_patients").select("email").eq("user_id", existing_appointment["patient_id"]).execute()
                doctor_result = admin_client.table("staff_profiles").select("email").eq("user_id", existing_appointment["doctor_id"]).execute()
                
                if patient_result.data and doctor_result.data:
                    send_appointment_notification(
                        existing_appointment, "cancelled", 
                        patient_result.data[0].get('email'),
                        doctor_result.data[0].get('email')
                    )
            except Exception as e:
                print(f"Notification error: {str(e)}")

            return JsonResponse({
                "message": "Appointment deleted successfully"
            }, status=200)
        else:
            return JsonResponse({"error": "Failed to delete appointment"}, status=500)

    except Exception as e:
        print(f"Delete appointment error: {str(e)}")
        return JsonResponse({"error": "Failed to delete appointment"}, status=500)


@csrf_exempt
def list_appointments(request):
    """List appointments with filtering options"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        # Get query parameters
        status_filter = request.GET.get('status')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        appointment_type = request.GET.get('type')  # 'upcoming' or 'past'
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        
        user_role = user.profile.get('role', 'patient')
        
        # Use the existing utility function for filtering
        appointments = get_filtered_appointments(
            user_id=user.id,
            user_role=user_role,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            appointment_type=appointment_type
        )
        
        # Apply pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_appointments = appointments[start_index:end_index]
        
        return JsonResponse({
            "message": "Appointments retrieved successfully",
            "appointments": paginated_appointments,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(appointments),
                "has_next": end_index < len(appointments),
                "has_prev": page > 1
            }
        }, status=200)

    except ValueError as e:
        return JsonResponse({"error": "Invalid pagination parameters"}, status=400)
    except Exception as e:
        print(f"List appointments error: {str(e)}")
        return JsonResponse({"error": "Failed to retrieve appointments"}, status=500)


@csrf_exempt
def get_appointment_stats(request):
    """Get appointment statistics for dashboard"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({"error": "Authorization required"}, status=401)

    token = auth_header.split(' ')[1]
    user = get_authenticated_user(token)
    if not user:
        return JsonResponse({"error": "Invalid token"}, status=401)

    try:
        user_role = user.profile.get('role', 'patient')
        today = datetime.now().date()
        
        # Base query depending on user role
        if user_role == 'patient':
            base_query = admin_client.table("appointments").select("*").eq("patient_id", user.id)
        elif user_role == 'doctor':
            base_query = admin_client.table("appointments").select("*").eq("doctor_id", user.id)
        else:  # admin
            base_query = admin_client.table("appointments").select("*")
        
        # Get all appointments for the user
        all_appointments = base_query.execute().data
        
        # Calculate statistics
        stats = {
            "total": len(all_appointments),
            "pending": len([a for a in all_appointments if a['status'] == 'pending']),
            "confirmed": len([a for a in all_appointments if a['status'] == 'confirmed']),
            "completed": len([a for a in all_appointments if a['status'] == 'completed']),
            "cancelled": len([a for a in all_appointments if a['status'] == 'cancelled']),
            "today": len([a for a in all_appointments if a['date'] == str(today)]),
            "this_week": 0,
            "this_month": 0
        }
        
        # Calculate week and month stats
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        for appointment in all_appointments:
            app_date = datetime.strptime(appointment['date'], '%Y-%m-%d').date()
            if app_date >= week_start:
                stats["this_week"] += 1
            if app_date >= month_start:
                stats["this_month"] += 1
        
        return JsonResponse({"message": "Statistics retrieved successfully", "stats": stats}, status=200)

    except Exception as e:
        print(f"Get stats error: {str(e)}")
        return JsonResponse({"error": "Failed to retrieve statistics"}, status=500)
