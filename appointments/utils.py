from datetime import datetime, time
from django.http import JsonResponse
from django.utils import timezone
from .models import Appointment
from .datetime_utils import DateTimeValidator

def validate_appointment_datetime(date_str, time_str):
    """Validate appointment date and time using comprehensive validator"""
    return DateTimeValidator.validate_appointment_datetime(date_str, time_str)

def check_doctor_availability(doctor_id, date_str, time_str, exclude_appointment_id=None):
    """Check if doctor is available at the given time"""
    try:
        # Parse date and time
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(time_str, '%H:%M').time()
        
        # Build query
        conflicting_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            date=appointment_date,
            time=appointment_time
        ).exclude(status='cancelled')
        
        # Exclude current appointment if updating
        if exclude_appointment_id:
            conflicting_appointments = conflicting_appointments.exclude(id=exclude_appointment_id)
        
        if conflicting_appointments.exists():
            return False, "Doctor is already booked at this time"
            
        return True, None
    except Exception as e:
        return False, f"Error checking doctor availability: {str(e)}"

def check_patient_availability(patient_id, date_str, time_str, exclude_appointment_id=None):
    """Check if patient has any conflicting appointments"""
    try:
        # Parse date and time
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(time_str, '%H:%M').time()
        
        # Build query
        conflicting_appointments = Appointment.objects.filter(
            patient_id=patient_id,
            date=appointment_date,
            time=appointment_time
        ).exclude(status='cancelled')
        
        # Exclude current appointment if updating
        if exclude_appointment_id:
            conflicting_appointments = conflicting_appointments.exclude(id=exclude_appointment_id)
        
        if conflicting_appointments.exists():
            return False, "Patient already has an appointment at this time"
            
        return True, None
    except Exception as e:
        return False, f"Error checking patient availability: {str(e)}"

def validate_appointment_type(type_str):
    """Validate appointment type"""
    valid_types = ["initial", "follow-up"]
    if type_str.lower() not in valid_types:
        return False, f"Invalid appointment type. Must be one of: {', '.join(valid_types)}"
    return True, None

def validate_appointment_status(status_str, is_doctor=False):
    """Validate appointment status based on role"""
    valid_statuses = [
        "requested",
        "scheduled",
        "reschedule_requested",
        "declined",
        "pending",
        "confirmed",
        "cancelled",
        "missed"
    ]
    
    # Additional validation for doctor-specific status changes
    if is_doctor and status_str not in ["approved", "rejected", "reschedule"]:
        return False, "Invalid status for doctor. Must be: approved, rejected, or reschedule"
        
    if status_str not in valid_statuses:
        return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        
    return True, None

def get_filtered_appointments(user_id, is_doctor=False, **filters):
    """Get filtered appointments for a user"""
    try:
        # Base query with related fields
        if is_doctor:
            queryset = Appointment.objects.filter(doctor_id=user_id).select_related('patient')
        else:
            queryset = Appointment.objects.filter(patient_id=user_id).select_related('doctor')
            
        # Apply status filter
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
            
        # Apply date range filter
        if filters.get('start_date'):
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
            queryset = queryset.filter(date__gte=start_date)
        if filters.get('end_date'):
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
            queryset = queryset.filter(date__lte=end_date)
            
        # Apply upcoming/past filter
        today = timezone.now().date()
        if filters.get('type') == 'upcoming':
            queryset = queryset.filter(date__gte=today)
        elif filters.get('type') == 'past':
            queryset = queryset.filter(date__lt=today)
            
        # Apply sorting
        queryset = queryset.order_by('date', 'time')
        
        # Format the response
        appointments = []
        for apt in queryset:
            apt_data = {
                'id': apt.id,
                'date': apt.date.strftime('%Y-%m-%d'),
                'time': apt.time.strftime('%H:%M'),
                'status': apt.status,
                'type': apt.type,
                'notes': apt.notes,
                'doctor_id': apt.doctor_id,
                'patient_id': apt.patient_id,
            }
            
            if is_doctor and apt.patient:
                apt_data["patient_name"] = apt.patient.full_name if hasattr(apt.patient, 'full_name') else None
                apt_data["patient_phone"] = apt.patient.phone if hasattr(apt.patient, 'phone') else None
            elif not is_doctor and apt.doctor:
                apt_data["doctor_name"] = apt.doctor.full_name if hasattr(apt.doctor, 'full_name') else None
                
            appointments.append(apt_data)
            
        return True, appointments
    except Exception as e:
        return False, f"Error fetching appointments: {str(e)}"