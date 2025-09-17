from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction, models
from django.utils import timezone
from authentication.utils import get_authenticated_user
from authentication.middleware import api_csrf_exempt, get_request_user
from .models import Appointment, AppointmentType
from accounts.models import EnhancedPatient, EnhancedStaffProfile
from .utils import (
    validate_appointment_datetime,
    check_doctor_availability,
    check_patient_availability,
    validate_appointment_type,
    validate_appointment_status,
    get_filtered_appointments
)
from notifications.utils import send_appointment_confirmation, send_appointment_update
from notifications.appointment_reminders import appointment_reminder_service
import json
import uuid
from datetime import datetime, timedelta, time, date
import logging


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

        # Validate doctor exists
        try:
            doctor = EnhancedStaffProfile.objects.get(id=data["doctor_id"])
        except EnhancedStaffProfile.DoesNotExist:
            return JsonResponse({"error": "Doctor not found"}, status=404)

        # Validate patient exists
        try:
            patient = EnhancedPatient.objects.get(id=data["patient_id"])
        except EnhancedPatient.DoesNotExist:
            return JsonResponse({"error": "Patient not found"}, status=404)

        # Validate appointment type
        try:
            appointment_type = AppointmentType.objects.get(name__iexact=data["type"])
        except AppointmentType.DoesNotExist:
            return JsonResponse({"error": "Invalid appointment type"}, status=400)

        # Parse date and time
        try:
            appointment_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            appointment_time = datetime.strptime(data["time"], "%H:%M").time()
            appointment_datetime = timezone.make_aware(
                datetime.combine(appointment_date, appointment_time)
            )
        except ValueError:
            return JsonResponse({"error": "Invalid date or time format"}, status=400)

        # Check doctor availability
        valid, error_msg = check_doctor_availability(data["doctor_id"], data["date"], data["time"])
        if not valid:
            return JsonResponse({"error": error_msg}, status=409)

        # Check patient availability
        valid, error_msg = check_patient_availability(data["patient_id"], data["date"], data["time"])
        if not valid:
            return JsonResponse({"error": error_msg}, status=409)

        # Set initial status based on user role
        user_role = getattr(user, 'role', 'patient')
        if user_role in ['doctor', 'admin']:
            initial_status = "scheduled"
        else:
            initial_status = "requested"

        # Create appointment with transaction
        with transaction.atomic():
            appointment = Appointment.objects.create(
                patient=patient,
                provider=doctor,
                appointment_type=appointment_type,
                scheduled_date=appointment_date,
                scheduled_time=appointment_time,
                status=initial_status,
                priority='medium',
                location_text=data.get("location_text", "Main Hospital"),
                notes=data.get("notes", ""),
                preferred_communication_channel=data.get("preferred_channel", "sms"),
                created_by=user
            )

            # Send confirmation notification
            try:
                send_appointment_notification(appointment, "created", patient.user.email, doctor.user.email)
            except Exception as e:
                logging.error(f"Notification error: {str(e)}")

            # Schedule appointment reminders
            try:
                appointment_reminder_service.schedule_appointment_reminders(appointment)
                logging.info(f"Scheduled reminders for appointment {appointment.id}")
            except Exception as e:
                logging.error(f"Error scheduling reminders: {str(e)}")

            return JsonResponse({
                "message": "Appointment created successfully",
                "appointment": {
                    "id": str(appointment.id),
                    "patient_id": str(appointment.patient.id),
                    "doctor_id": str(appointment.provider.id),
                    "patient_name": f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}",
                    "doctor_name": f"{appointment.provider.user.first_name} {appointment.provider.user.last_name}",
                    "date": appointment.scheduled_date.strftime("%Y-%m-%d"),
                    "time": appointment.scheduled_time.strftime("%H:%M"),
                    "type": appointment.appointment_type.name,
                    "status": appointment.status,
                    "location": appointment.location_text,
                    "notes": appointment.notes,
                    "created_at": appointment.created_at.isoformat()
                }
            }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@api_csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def update_appointment(request, appointment_id):
    """Update an existing appointment"""
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        user_role = getattr(user, 'role', 'patient')
        if user_role == 'patient':
            # Patients can only update their own appointments
            try:
                patient = EnhancedPatient.objects.get(user=user)
                if appointment.patient != patient:
                    return JsonResponse({"error": "Permission denied"}, status=403)
            except EnhancedPatient.DoesNotExist:
                return JsonResponse({"error": "Patient profile not found"}, status=404)
        elif user_role == 'doctor':
            # Doctors can update appointments they're assigned to
            try:
                staff = EnhancedStaffProfile.objects.get(user=user)
                if appointment.provider != staff:
                    return JsonResponse({"error": "Permission denied"}, status=403)
            except EnhancedStaffProfile.DoesNotExist:
                return JsonResponse({"error": "Staff profile not found"}, status=404)

        data = json.loads(request.body)
        
        # Update allowed fields
        if 'status' in data:
            valid, error_msg = validate_appointment_status(data['status'])
            if not valid:
                return JsonResponse({"error": error_msg}, status=400)
            appointment.status = data['status']
            
        if 'notes' in data:
            appointment.notes = data['notes']
            
        if 'priority' in data and data['priority'] in ['low', 'normal', 'high', 'urgent', 'emergency']:
            appointment.priority = data['priority']
            
        # Only allow rescheduling if user has permission
        if user_role in ['doctor', 'admin'] and ('date' in data or 'time' in data):
            if 'date' in data:
                try:
                    new_date = datetime.strptime(data['date'], "%Y-%m-%d").date()
                    appointment.appointment_date = new_date
                except ValueError:
                    return JsonResponse({"error": "Invalid date format"}, status=400)
                    
            if 'time' in data:
                try:
                    new_time = datetime.strptime(data['time'], "%H:%M").time()
                    appointment.start_time = new_time
                    # Calculate end time based on appointment type duration
                    duration = appointment.appointment_type.default_duration
                    end_datetime = datetime.combine(appointment.appointment_date, new_time) + timedelta(minutes=duration)
                    appointment.end_time = end_datetime.time()
                except ValueError:
                    return JsonResponse({"error": "Invalid time format"}, status=400)

        appointment.save()
        
        # Send update notification
        try:
            send_appointment_notification(appointment, "updated", appointment.patient.user.email, appointment.provider.user.email)
        except Exception as e:
            logging.error(f"Notification error: {str(e)}")

        return JsonResponse({
            "message": "Appointment updated successfully",
            "appointment": {
                "id": str(appointment.id),
                "status": appointment.status,
                "date": appointment.appointment_date.strftime("%Y-%m-%d"),
                "time": appointment.start_time.strftime("%H:%M"),
                "notes": appointment.notes,
                "priority": appointment.priority,
                "updated_at": appointment.updated_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@api_csrf_exempt
@require_http_methods(["DELETE"])
def cancel_appointment(request, appointment_id):
    """Cancel an appointment (soft delete)"""
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        user_role = getattr(user, 'role', 'patient')
        if user_role == 'patient':
            try:
                patient = EnhancedPatient.objects.get(user=user)
                if appointment.patient != patient:
                    return JsonResponse({"error": "Permission denied"}, status=403)
            except EnhancedPatient.DoesNotExist:
                return JsonResponse({"error": "Patient profile not found"}, status=404)
        elif user_role == 'doctor':
            try:
                staff = EnhancedStaffProfile.objects.get(user=user)
                if appointment.provider != staff:
                    return JsonResponse({"error": "Permission denied"}, status=403)
            except EnhancedStaffProfile.DoesNotExist:
                return JsonResponse({"error": "Staff profile not found"}, status=404)

        # Update status to cancelled
        appointment.status = 'cancelled'
        appointment.cancelled_at = timezone.now()
        appointment.cancelled_by = user
        appointment.save()
        
        # Send cancellation notification
        try:
            send_appointment_notification(appointment, "cancelled", appointment.patient.user.email, appointment.provider.user.email)
        except Exception as e:
            logging.error(f"Notification error: {str(e)}")

        return JsonResponse({
            "message": "Appointment cancelled successfully",
            "appointment_id": str(appointment.id)
        })
        
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_all_appointments(request):
    """Get all appointments with filtering and pagination"""
    # Verify authentication
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        # Get the actual Django User model from AuthenticatedUser
        django_user = user.user if hasattr(user, 'user') else user
        
        # Build query based on user role
        user_role = getattr(django_user, 'role', 'patient')
        
        if user_role == 'patient':
            # Patients can only see their own appointments
            try:
                patient = EnhancedPatient.objects.get(user=django_user)
                appointments = Appointment.objects.filter(patient=patient)
            except EnhancedPatient.DoesNotExist:
                return JsonResponse({"error": "Patient profile not found"}, status=404)
        elif user_role == 'doctor':
            # Doctors can see appointments they're assigned to
            try:
                staff = EnhancedStaffProfile.objects.get(user=django_user)
                appointments = Appointment.objects.filter(provider=staff)
            except EnhancedStaffProfile.DoesNotExist:
                return JsonResponse({"error": "Staff profile not found"}, status=404)
        else:
            # Admins can see all appointments
            appointments = Appointment.objects.all()

        # Apply filters
        status = request.GET.get('status')
        if status:
            appointments = appointments.filter(status=status)

        date_from = request.GET.get('date_from')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                appointments = appointments.filter(appointment_date__gte=date_from)
            except ValueError:
                return JsonResponse({"error": "Invalid date_from format"}, status=400)

        date_to = request.GET.get('date_to')
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                appointments = appointments.filter(appointment_date__lte=date_to)
            except ValueError:
                return JsonResponse({"error": "Invalid date_to format"}, status=400)

        # Search functionality
        search = request.GET.get('search')
        if search:
            appointments = appointments.filter(
                models.Q(patient__user__first_name__icontains=search) |
                models.Q(patient__user__last_name__icontains=search) |
                models.Q(provider__user__first_name__icontains=search) |
                models.Q(provider__user__last_name__icontains=search) |
                models.Q(appointment_type__name__icontains=search) |
                models.Q(notes__icontains=search)
            )

        # Ordering
        order_by = request.GET.get('order_by', '-appointment_date')
        appointments = appointments.order_by(order_by)

        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        paginator = Paginator(appointments, page_size)
        
        try:
            appointments_page = paginator.page(page)
        except:
            return JsonResponse({"error": "Invalid page number"}, status=400)

        # Serialize appointments
        appointments_data = []
        for appointment in appointments_page:
            appointments_data.append({
                "id": str(appointment.id),
                "patient_id": str(appointment.patient.id),
                "patient_name": f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}",
                "provider_id": str(appointment.provider.id),
                "provider_name": f"{appointment.provider.user.first_name} {appointment.provider.user.last_name}",
                "appointment_type": appointment.appointment_type.name,
                "scheduled_date": appointment.scheduled_date.strftime("%Y-%m-%d"),
                "scheduled_time": appointment.scheduled_time.strftime("%H:%M"),
                "status": appointment.status,
                "priority": appointment.priority,
                "location": appointment.location_text,
                "notes": appointment.notes,
                "created_at": appointment.created_at.isoformat(),
                "updated_at": appointment.updated_at.isoformat()
            })

        return JsonResponse({
            "appointments": appointments_data,
            "pagination": {
                "current_page": page,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "has_next": appointments_page.has_next(),
                "has_previous": appointments_page.has_previous()
            }
        })

    except Exception as e:
        logging.error(f"Error in get_all_appointments: {str(e)}")
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_appointment_detail(request, appointment_id):
    """Get detailed information about a specific appointment"""
    # Verify authentication
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        user_role = getattr(user, 'role', 'patient')
        if user_role == 'patient':
            if appointment.patient.user != user:
                return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role == 'doctor':
            if appointment.provider.user != user:
                return JsonResponse({"error": "Permission denied"}, status=403)
        # Admins can view any appointment

        appointment_data = {
            "id": str(appointment.id),
            "patient": {
                "id": str(appointment.patient.id),
                "name": f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}",
                "email": appointment.patient.user.email,
                "phone": appointment.patient.phone_number,
                "date_of_birth": appointment.patient.date_of_birth.strftime("%Y-%m-%d") if appointment.patient.date_of_birth else None,
                "gender": appointment.patient.gender
            },
            "provider": {
                "id": str(appointment.provider.id),
                "name": f"{appointment.provider.user.first_name} {appointment.provider.user.last_name}",
                "email": appointment.provider.user.email,
                "specialization": appointment.provider.specialization,
                "department": appointment.provider.department
            },
            "appointment_type": {
                "name": appointment.appointment_type.name,
                "description": appointment.appointment_type.description,
                "duration_minutes": appointment.appointment_type.duration_minutes,
                "base_price": str(appointment.appointment_type.base_price)
            },
            "scheduled_date": appointment.scheduled_date.strftime("%Y-%m-%d"),
            "scheduled_time": appointment.scheduled_time.strftime("%H:%M"),
            "status": appointment.status,
            "priority": appointment.priority,
            "location": appointment.location_text,
            "notes": appointment.notes,
            "preferred_communication_channel": appointment.preferred_communication_channel,
            "created_at": appointment.created_at.isoformat(),
            "updated_at": appointment.updated_at.isoformat(),
            "created_by": f"{appointment.created_by.first_name} {appointment.created_by.last_name}" if appointment.created_by else None
        }

        return JsonResponse({"appointment": appointment_data})

    except Exception as e:
        logging.error(f"Error in get_appointment_detail: {str(e)}")
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def update_appointment(request, appointment_id):
    """Update an existing appointment"""
    # Verify authentication
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        data = json.loads(request.body)
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        user_role = getattr(user, 'role', 'patient')
        if user_role == 'patient':
            if appointment.patient.user != user:
                return JsonResponse({"error": "Permission denied"}, status=403)
            # Patients can only update limited fields
            allowed_fields = ['notes', 'preferred_communication_channel']
        elif user_role == 'doctor':
            if appointment.provider.user != user:
                return JsonResponse({"error": "Permission denied"}, status=403)
            # Doctors can update more fields
            allowed_fields = ['status', 'notes', 'location_text', 'priority']
        else:
            # Admins can update all fields
            allowed_fields = ['status', 'notes', 'location_text', 'priority', 'scheduled_date', 'scheduled_time']

        with transaction.atomic():
            updated_fields = []
            
            # Update allowed fields
            for field, value in data.items():
                if field in allowed_fields:
                    if field == 'scheduled_date':
                        try:
                            appointment.scheduled_date = datetime.strptime(value, "%Y-%m-%d").date()
                            updated_fields.append(field)
                        except ValueError:
                            return JsonResponse({"error": "Invalid date format"}, status=400)
                    elif field == 'scheduled_time':
                        try:
                            appointment.scheduled_time = datetime.strptime(value, "%H:%M").time()
                            updated_fields.append(field)
                        except ValueError:
                            return JsonResponse({"error": "Invalid time format"}, status=400)
                    elif field == 'status':
                        valid_statuses = ['requested', 'scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show']
                        if value in valid_statuses:
                            appointment.status = value
                            updated_fields.append(field)
                        else:
                            return JsonResponse({"error": "Invalid status"}, status=400)
                    elif field == 'priority':
                        valid_priorities = ['low', 'medium', 'high', 'urgent']
                        if value in valid_priorities:
                            appointment.priority = value
                            updated_fields.append(field)
                        else:
                            return JsonResponse({"error": "Invalid priority"}, status=400)
                    else:
                        setattr(appointment, field, value)
                        updated_fields.append(field)

            if updated_fields:
                appointment.save()
                
                # Send notification if status changed
                if 'status' in updated_fields:
                    try:
                        send_appointment_notification(appointment, "updated", 
                                                    appointment.patient.user.email, 
                                                    appointment.provider.user.email)
                    except Exception as e:
                        logging.error(f"Notification error: {str(e)}")

                return JsonResponse({
                    "message": "Appointment updated successfully",
                    "updated_fields": updated_fields,
                    "appointment": {
                        "id": str(appointment.id),
                        "status": appointment.status,
                        "scheduled_date": appointment.scheduled_date.strftime("%Y-%m-%d"),
                        "scheduled_time": appointment.scheduled_time.strftime("%H:%M"),
                        "notes": appointment.notes,
                        "updated_at": appointment.updated_at.isoformat()
                    }
                })
            else:
                return JsonResponse({"message": "No valid fields to update"}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logging.error(f"Error in update_appointment: {str(e)}")
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    # Verify authentication
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        user_role = getattr(user, 'role', 'patient')
        if user_role == 'patient':
            if appointment.patient.user != user:
                return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role == 'doctor':
            if appointment.provider.user != user:
                return JsonResponse({"error": "Permission denied"}, status=403)
        # Admins can cancel any appointment

        # Check if appointment can be cancelled
        if appointment.status in ['completed', 'cancelled']:
            return JsonResponse({"error": "Cannot cancel completed or already cancelled appointment"}, status=400)

        # Get cancellation reason if provided
        cancellation_reason = ""
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                cancellation_reason = data.get('reason', '')
            except json.JSONDecodeError:
                pass

        with transaction.atomic():
            appointment.status = 'cancelled'
            if cancellation_reason:
                appointment.notes = f"{appointment.notes}\n\nCancellation reason: {cancellation_reason}".strip()
            appointment.save()

            # Send cancellation notification
            try:
                send_appointment_notification(appointment, "cancelled", 
                                            appointment.patient.user.email, 
                                            appointment.provider.user.email)
            except Exception as e:
                logging.error(f"Notification error: {str(e)}")

            return JsonResponse({
                "message": "Appointment cancelled successfully",
                "appointment": {
                    "id": str(appointment.id),
                    "status": appointment.status,
                    "updated_at": appointment.updated_at.isoformat()
                }
            })

    except Exception as e:
        logging.error(f"Error in cancel_appointment: {str(e)}")
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
            # Cancel appointment reminders
            try:
                appointment_reminder_service.cancel_appointment_reminders(appointment_id)
                logging.info(f"Cancelled reminders for appointment {appointment_id}")
            except Exception as e:
                logging.error(f"Error cancelling reminders: {str(e)}")

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
                "message": "Appointment deleted successfully",
                "appointment_id": appointment_id
            }, status=200)
        else:
            return JsonResponse({"error": "Failed to delete appointment"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@api_csrf_exempt
@require_http_methods(["GET"])
def check_availability(request):
    """Check doctor and time slot availability"""
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        doctor_id = request.GET.get('doctor_id')
        date = request.GET.get('date')
        time = request.GET.get('time')
        duration = int(request.GET.get('duration', 30))  # Default 30 minutes
        
        if not all([doctor_id, date, time]):
            return JsonResponse({"error": "Missing required parameters: doctor_id, date, time"}, status=400)

        # Validate date and time format
        try:
            appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
            appointment_time = datetime.strptime(time, "%H:%M").time()
        except ValueError:
            return JsonResponse({"error": "Invalid date or time format"}, status=400)

        # Check if doctor exists
        try:
            doctor = EnhancedStaffProfile.objects.get(id=doctor_id)
        except EnhancedStaffProfile.DoesNotExist:
            return JsonResponse({"error": "Doctor not found"}, status=404)

        # Check availability
        doctor_available, doctor_msg = check_doctor_availability(doctor_id, date, time)
        
        # Get available time slots for the day
        available_slots = get_available_time_slots(doctor_id, date, duration)
        
        return JsonResponse({
            "available": doctor_available,
            "message": doctor_msg if not doctor_available else "Time slot is available",
            "doctor_name": f"{doctor.user.first_name} {doctor.user.last_name}",
            "available_slots": available_slots,
            "requested_slot": {
                "date": date,
                "time": time,
                "duration": duration
            }
        })
        
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@api_csrf_exempt
@require_http_methods(["GET"])
def get_appointment_statistics(request):
    """Get appointment statistics for dashboard"""
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        user_role = getattr(user, 'role', 'patient')
        
        # Base query filters
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        if user_role == 'patient':
            try:
                patient = EnhancedPatient.objects.get(user=user)
                base_query = Appointment.objects.filter(patient=patient)
            except EnhancedPatient.DoesNotExist:
                return JsonResponse({"error": "Patient profile not found"}, status=404)
        elif user_role == 'doctor':
            try:
                staff = EnhancedStaffProfile.objects.get(user=user)
                base_query = Appointment.objects.filter(provider=staff)
            except EnhancedStaffProfile.DoesNotExist:
                return JsonResponse({"error": "Staff profile not found"}, status=404)
        else:
            base_query = Appointment.objects.all()

        # Calculate statistics
        stats = {
            "today": {
                "total": base_query.filter(appointment_date=today).count(),
                "scheduled": base_query.filter(appointment_date=today, status='scheduled').count(),
                "completed": base_query.filter(appointment_date=today, status='completed').count(),
                "cancelled": base_query.filter(appointment_date=today, status='cancelled').count(),
            },
            "this_week": {
                "total": base_query.filter(appointment_date__gte=week_start).count(),
                "scheduled": base_query.filter(appointment_date__gte=week_start, status='scheduled').count(),
                "completed": base_query.filter(appointment_date__gte=week_start, status='completed').count(),
                "cancelled": base_query.filter(appointment_date__gte=week_start, status='cancelled').count(),
            },
            "this_month": {
                "total": base_query.filter(appointment_date__gte=month_start).count(),
                "scheduled": base_query.filter(appointment_date__gte=month_start, status='scheduled').count(),
                "completed": base_query.filter(appointment_date__gte=month_start, status='completed').count(),
                "cancelled": base_query.filter(appointment_date__gte=month_start, status='cancelled').count(),
            },
            "upcoming": base_query.filter(
                appointment_date__gte=today,
                status__in=['scheduled', 'confirmed']
            ).order_by('appointment_date', 'start_time')[:5].values(
                'id', 'appointment_date', 'start_time', 'appointment_type__name',
                'patient__user__first_name', 'patient__user__last_name'
            )
        }
        
        return JsonResponse({"statistics": stats})
        
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@api_csrf_exempt
@require_http_methods(["POST"])
def bulk_update_appointments(request):
    """Bulk update multiple appointments"""
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    # Only allow admin and doctor roles for bulk operations
    user_role = getattr(user, 'role', 'patient')
    if user_role not in ['admin', 'doctor']:
        return JsonResponse({"error": "Permission denied"}, status=403)

    try:
        data = json.loads(request.body)
        appointment_ids = data.get('appointment_ids', [])
        update_data = data.get('update_data', {})
        
        if not appointment_ids:
            return JsonResponse({"error": "No appointment IDs provided"}, status=400)
            
        if not update_data:
            return JsonResponse({"error": "No update data provided"}, status=400)

        # Validate update data
        allowed_fields = ['status', 'priority', 'notes']
        update_fields = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if 'status' in update_fields:
            valid, error_msg = validate_appointment_status(update_fields['status'])
            if not valid:
                return JsonResponse({"error": error_msg}, status=400)

        # Get appointments to update
        appointments = Appointment.objects.filter(id__in=appointment_ids)
        
        # Check permissions for doctor role
        if user_role == 'doctor':
            try:
                staff = EnhancedStaffProfile.objects.get(user=user)
                appointments = appointments.filter(provider=staff)
            except EnhancedStaffProfile.DoesNotExist:
                return JsonResponse({"error": "Staff profile not found"}, status=404)

        if not appointments.exists():
            return JsonResponse({"error": "No appointments found or permission denied"}, status=404)

        # Perform bulk update
        updated_count = appointments.update(**update_fields)
        
        return JsonResponse({
            "message": f"Successfully updated {updated_count} appointments",
            "updated_count": updated_count,
            "appointment_ids": list(appointments.values_list('id', flat=True))
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


def get_available_time_slots(doctor_id, date, duration=30):
    """Helper function to get available time slots for a doctor on a specific date"""
    try:
        # Get doctor's working hours (assuming 9 AM to 5 PM for now)
        start_hour = 9
        end_hour = 17
        slot_duration = duration
        
        # Get existing appointments for the doctor on that date
        existing_appointments = Appointment.objects.filter(
            provider_id=doctor_id,
            appointment_date=date,
            status__in=['scheduled', 'confirmed', 'in_progress']
        ).values_list('start_time', 'end_time')
        
        # Generate all possible time slots
        available_slots = []
        current_time = time(start_hour, 0)
        end_time = time(end_hour, 0)
        
        while current_time < end_time:
            slot_end = (datetime.combine(date, current_time) + timedelta(minutes=slot_duration)).time()
            
            # Check if this slot conflicts with existing appointments
            is_available = True
            for apt_start, apt_end in existing_appointments:
                if (current_time < apt_end and slot_end > apt_start):
                    is_available = False
                    break
            
            if is_available and slot_end <= end_time:
                available_slots.append(current_time.strftime("%H:%M"))
            
            # Move to next slot
            current_time = (datetime.combine(date, current_time) + timedelta(minutes=slot_duration)).time()
        
        return available_slots
        
    except Exception as e:
        logging.error(f"Error getting available time slots: {str(e)}")
        return []


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
