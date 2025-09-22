from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction, models
from django.utils import timezone
from authentication.utils import get_authenticated_user
from authentication.middleware import api_csrf_exempt, get_request_user
from .models import Appointment, AppointmentType, Room, Equipment
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

logger = logging.getLogger(__name__)


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
        
        # Send notifications using the notification system
        send_appointment_confirmation(patient_email, appointment_data)
        send_appointment_update(doctor_email, appointment_data, action)
        logger.info(f"Notification sent: {message} to {patient_email} and {doctor_email}")
        
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")


@api_csrf_exempt
def create_appointment(request):
    """Create a new appointment - accessible by both staff and patients"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Verify authentication
    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['patient_id', 'provider_id', 'appointment_type_id', 'date', 'time']
        for field in required_fields:
            if field not in data:
                return JsonResponse({"error": f"Missing required field: {field}"}, status=400)

        # Validate and get related objects
        try:
            patient = EnhancedPatient.objects.get(id=data['patient_id'])
            provider = EnhancedStaffProfile.objects.get(id=data['provider_id'], role='doctor')
            appointment_type = AppointmentType.objects.get(id=data['appointment_type_id'])
        except (EnhancedPatient.DoesNotExist, EnhancedStaffProfile.DoesNotExist, AppointmentType.DoesNotExist) as e:
            return JsonResponse({"error": f"Invalid reference: {str(e)}"}, status=400)

        # Validate date and time
        valid, error_msg = validate_appointment_datetime(data['date'], data['time'])
        if not valid:
            return JsonResponse({"error": error_msg}, status=400)

        # Check availability
        valid, error_msg = check_doctor_availability(provider.id, data['date'], data['time'])
        if not valid:
            return JsonResponse({"error": error_msg}, status=409)

        valid, error_msg = check_patient_availability(patient.id, data['date'], data['time'])
        if not valid:
            return JsonResponse({"error": error_msg}, status=409)

        # Create appointment with transaction
        with transaction.atomic():
            appointment = Appointment.objects.create(
                patient=patient,
                provider=provider,
                appointment_type=appointment_type,
                date=data['date'],
                time=data['time'],
                title=data.get('title', f"{appointment_type.name} - {patient.user.get_full_name()}"),
                reason=data.get('reason', ''),
                notes=data.get('notes', ''),
                status='pending',
                priority=data.get('priority', 'medium'),
                created_by=user
            )

            # Send notifications
            appointment_data = {
                'id': appointment.id,
                'date': appointment.date,
                'time': appointment.time,
                'type': appointment.appointment_type.name,
                'patient': patient.user.get_full_name(),
                'provider': provider.user.get_full_name()
            }
            
            send_appointment_notification(
                appointment_data, 
                'created',
                patient.user.email,
                provider.user.email
            )

            # Schedule reminder
            appointment_reminder_service.schedule_reminder(appointment.id)

        return JsonResponse({
            "message": "Appointment created successfully",
            "appointment_id": appointment.id
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Create appointment error: {str(e)}")
        return JsonResponse({"error": "Failed to create appointment"}, status=500)


@api_csrf_exempt
def update_appointment(request, appointment_id):
    """Update an existing appointment"""
    if request.method != "PUT":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        user_role = getattr(user, 'role', 'patient')
        if user_role == 'patient' and appointment.patient.user != user:
            return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role == 'doctor' and appointment.provider.user != user:
            return JsonResponse({"error": "Permission denied"}, status=403)

        data = json.loads(request.body)
        
        # Track changes for notifications
        changes = {}
        
        # Update allowed fields based on user role
        if user_role in ['admin', 'staff']:
            updatable_fields = ['date', 'time', 'status', 'priority', 'notes', 'reason', 'title']
        elif user_role == 'doctor':
            updatable_fields = ['status', 'notes', 'date', 'time']
        else:  # patient
            updatable_fields = ['notes', 'reason']

        with transaction.atomic():
            for field in updatable_fields:
                if field in data:
                    old_value = getattr(appointment, field)
                    new_value = data[field]
                    
                    if field in ['date', 'time'] and old_value != new_value:
                        # Validate new date/time
                        date_val = data.get('date', appointment.date)
                        time_val = data.get('time', appointment.time)
                        
                        valid, error_msg = validate_appointment_datetime(date_val, time_val)
                        if not valid:
                            return JsonResponse({"error": error_msg}, status=400)

                        # Check availability (excluding current appointment)
                        valid, error_msg = check_doctor_availability(
                            appointment.provider.id, date_val, time_val, appointment_id
                        )
                        if not valid:
                            return JsonResponse({"error": error_msg}, status=409)

                        valid, error_msg = check_patient_availability(
                            appointment.patient.id, date_val, time_val, appointment_id
                        )
                        if not valid:
                            return JsonResponse({"error": error_msg}, status=409)

                    if field == 'status':
                        valid, error_msg = validate_appointment_status(new_value, user_role == 'doctor')
                        if not valid:
                            return JsonResponse({"error": error_msg}, status=400)

                    if old_value != new_value:
                        changes[field] = {'old': old_value, 'new': new_value}
                        setattr(appointment, field, new_value)

            if changes:
                appointment.save()
                
                # Send update notifications
                appointment_data = {
                    'id': appointment.id,
                    'date': appointment.date,
                    'time': appointment.time,
                    'type': appointment.appointment_type.name,
                    'patient': appointment.patient.user.get_full_name(),
                    'provider': appointment.provider.user.get_full_name(),
                    'changes': changes
                }
                
                send_appointment_notification(
                    appointment_data,
                    'updated',
                    appointment.patient.user.email,
                    appointment.provider.user.email
                )

        return JsonResponse({
            "message": "Appointment updated successfully",
            "changes": changes
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Update appointment error: {str(e)}")
        return JsonResponse({"error": "Failed to update appointment"}, status=500)


@api_csrf_exempt
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        user_role = getattr(user, 'role', 'patient')
        if user_role == 'patient' and appointment.patient.user != user:
            return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role == 'doctor' and appointment.provider.user != user:
            return JsonResponse({"error": "Permission denied"}, status=403)

        # Check if appointment can be cancelled
        if appointment.status in ['completed', 'cancelled']:
            return JsonResponse({"error": "Cannot cancel completed or already cancelled appointment"}, status=400)

        data = json.loads(request.body) if request.body else {}
        cancellation_reason = data.get('reason', 'No reason provided')

        with transaction.atomic():
            appointment.status = 'cancelled'
            appointment.cancellation_reason = cancellation_reason
            appointment.cancelled_by = user
            appointment.cancelled_at = timezone.now()
            appointment.save()

            # Send cancellation notifications
            appointment_data = {
                'id': appointment.id,
                'date': appointment.date,
                'time': appointment.time,
                'type': appointment.appointment_type.name,
                'patient': appointment.patient.user.get_full_name(),
                'provider': appointment.provider.user.get_full_name(),
                'reason': cancellation_reason
            }
            
            send_appointment_notification(
                appointment_data,
                'cancelled',
                appointment.patient.user.email,
                appointment.provider.user.email
            )

        return JsonResponse({
            "message": "Appointment cancelled successfully"
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Cancel appointment error: {str(e)}")
        return JsonResponse({"error": "Failed to cancel appointment"}, status=500)


@api_csrf_exempt
def get_appointment_detail(request, appointment_id):
    """Get detailed information about a specific appointment"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        user_role = getattr(user, 'role', 'patient')
        if user_role == 'patient' and appointment.patient.user != user:
            return JsonResponse({"error": "Permission denied"}, status=403)
        elif user_role == 'doctor' and appointment.provider.user != user:
            return JsonResponse({"error": "Permission denied"}, status=403)

        appointment_data = {
            'id': appointment.id,
            'patient': {
                'id': appointment.patient.id,
                'name': appointment.patient.user.get_full_name(),
                'email': appointment.patient.user.email,
                'phone': appointment.patient.phone_number
            },
            'provider': {
                'id': appointment.provider.id,
                'name': appointment.provider.user.get_full_name(),
                'email': appointment.provider.user.email,
                'specialization': appointment.provider.specialization
            },
            'appointment_type': {
                'id': appointment.appointment_type.id,
                'name': appointment.appointment_type.name,
                'duration': appointment.appointment_type.duration_minutes,
                'price': str(appointment.appointment_type.price)
            },
            'date': appointment.date,
            'time': appointment.time,
            'duration': appointment.duration_minutes,
            'title': appointment.title,
            'reason': appointment.reason,
            'notes': appointment.notes,
            'status': appointment.status,
            'priority': appointment.priority,
            'estimated_cost': str(appointment.estimated_cost),
            'actual_cost': str(appointment.actual_cost) if appointment.actual_cost else None,
            'room': appointment.room.name if appointment.room else None,
            'equipment': [eq.name for eq in appointment.equipment.all()],
            'created_at': appointment.created_at,
            'updated_at': appointment.updated_at,
            'is_recurring': appointment.is_recurring,
            'recurrence_pattern': appointment.recurrence_pattern if appointment.is_recurring else None
        }

        return JsonResponse({
            "message": "Appointment details retrieved successfully",
            "appointment": appointment_data
        }, status=200)

    except Exception as e:
        logger.error(f"Get appointment detail error: {str(e)}")
        return JsonResponse({"error": "Failed to retrieve appointment details"}, status=500)


@api_csrf_exempt
def list_appointments(request):
    """List appointments with filtering and pagination"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        user_role = getattr(user, 'role', 'patient')
        
        # Base queryset based on user role
        if user_role == 'patient':
            queryset = Appointment.objects.filter(patient__user=user)
        elif user_role == 'doctor':
            queryset = Appointment.objects.filter(provider__user=user)
        else:  # admin/staff
            queryset = Appointment.objects.all()

        # Apply filters
        status = request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        date_from = request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        priority = request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Ordering
        queryset = queryset.order_by('date', 'time')

        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        paginator = Paginator(queryset, per_page)
        appointments_page = paginator.get_page(page)

        appointments_data = []
        for appointment in appointments_page:
            appointments_data.append({
                'id': appointment.id,
                'patient_name': appointment.patient.user.get_full_name(),
                'provider_name': appointment.provider.user.get_full_name(),
                'appointment_type': appointment.appointment_type.name,
                'date': appointment.date,
                'time': appointment.time,
                'duration': appointment.duration_minutes,
                'status': appointment.status,
                'priority': appointment.priority,
                'title': appointment.title,
                'room': appointment.room.name if appointment.room else None
            })

        return JsonResponse({
            "message": "Appointments retrieved successfully",
            "appointments": appointments_data,
            "pagination": {
                "current_page": page,
                "total_pages": paginator.num_pages,
                "total_count": paginator.count,
                "per_page": per_page,
                "has_next": appointments_page.has_next(),
                "has_previous": appointments_page.has_previous()
            }
        }, status=200)

    except Exception as e:
        logger.error(f"List appointments error: {str(e)}")
        return JsonResponse({"error": "Failed to retrieve appointments"}, status=500)


@api_csrf_exempt
def check_availability(request):
    """Check availability for a specific date, time, and provider"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        provider_id = request.GET.get('provider_id')
        date_str = request.GET.get('date')
        time_str = request.GET.get('time')
        duration = int(request.GET.get('duration', 30))

        if not all([provider_id, date_str, time_str]):
            return JsonResponse({"error": "Missing required parameters"}, status=400)

        # Validate provider
        try:
            provider = EnhancedStaffProfile.objects.get(id=provider_id, role='doctor')
        except EnhancedStaffProfile.DoesNotExist:
            return JsonResponse({"error": "Provider not found"}, status=404)

        # Check availability
        valid, error_msg = check_doctor_availability(provider_id, date_str, time_str)
        
        return JsonResponse({
            "available": valid,
            "message": "Available" if valid else error_msg,
            "provider": provider.user.get_full_name(),
            "date": date_str,
            "time": time_str,
            "duration": duration
        }, status=200)

    except Exception as e:
        logger.error(f"Check availability error: {str(e)}")
        return JsonResponse({"error": "Failed to check availability"}, status=500)


@api_csrf_exempt
def get_appointment_statistics(request):
    """Get appointment statistics for dashboard"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        user_role = getattr(user, 'role', 'patient')
        today = timezone.now().date()
        
        # Base queryset based on user role
        if user_role == 'patient':
            queryset = Appointment.objects.filter(patient__user=user)
        elif user_role == 'doctor':
            queryset = Appointment.objects.filter(provider__user=user)
        else:  # admin/staff
            queryset = Appointment.objects.all()

        # Calculate statistics
        total = queryset.count()
        pending = queryset.filter(status='pending').count()
        confirmed = queryset.filter(status='confirmed').count()
        completed = queryset.filter(status='completed').count()
        cancelled = queryset.filter(status='cancelled').count()
        today_count = queryset.filter(date=today).count()
        
        # Week and month calculations
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        this_week = queryset.filter(date__gte=week_start).count()
        this_month = queryset.filter(date__gte=month_start).count()

        stats = {
            "total": total,
            "pending": pending,
            "confirmed": confirmed,
            "completed": completed,
            "cancelled": cancelled,
            "today": today_count,
            "this_week": this_week,
            "this_month": this_month
        }

        return JsonResponse({
            "message": "Statistics retrieved successfully",
            "stats": stats
        }, status=200)

    except Exception as e:
        logger.error(f"Get statistics error: {str(e)}")
        return JsonResponse({"error": "Failed to retrieve statistics"}, status=500)


@api_csrf_exempt
def get_available_time_slots(request):
    """Get available time slots for a provider on a specific date"""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = get_request_user(request)
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        provider_id = request.GET.get('provider_id')
        date_str = request.GET.get('date')
        duration = int(request.GET.get('duration', 30))

        if not all([provider_id, date_str]):
            return JsonResponse({"error": "Missing required parameters"}, status=400)

        # Validate provider
        try:
            provider = EnhancedStaffProfile.objects.get(id=provider_id, role='doctor')
        except EnhancedStaffProfile.DoesNotExist:
            return JsonResponse({"error": "Provider not found"}, status=404)

        # Get existing appointments for the date
        existing_appointments = Appointment.objects.filter(
            provider=provider,
            date=date_str,
            status__in=['pending', 'confirmed']
        ).values_list('time', 'duration_minutes')

        # Generate time slots (9 AM to 5 PM, 30-minute intervals)
        available_slots = []
        start_time = time(9, 0)  # 9:00 AM
        end_time = time(17, 0)   # 5:00 PM
        
        current_time = datetime.combine(date.today(), start_time)
        end_datetime = datetime.combine(date.today(), end_time)
        
        while current_time < end_datetime:
            slot_time = current_time.time()
            
            # Check if this slot conflicts with existing appointments
            is_available = True
            for app_time, app_duration in existing_appointments:
                app_start = datetime.combine(date.today(), app_time)
                app_end = app_start + timedelta(minutes=app_duration)
                slot_start = current_time
                slot_end = current_time + timedelta(minutes=duration)
                
                # Check for overlap
                if not (slot_end <= app_start or slot_start >= app_end):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(slot_time.strftime('%H:%M'))
            
            current_time += timedelta(minutes=30)

        return JsonResponse({
            "message": "Available time slots retrieved successfully",
            "provider": provider.user.get_full_name(),
            "date": date_str,
            "duration": duration,
            "available_slots": available_slots
        }, status=200)

    except Exception as e:
        logger.error(f"Get available time slots error: {str(e)}")
        return JsonResponse({"error": "Failed to retrieve available time slots"}, status=500)
