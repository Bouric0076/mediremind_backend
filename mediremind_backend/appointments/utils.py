from datetime import datetime, time
from supabase_client import admin_client
from django.http import JsonResponse

def validate_appointment_datetime(date_str, time_str):
    """Validate appointment date and time"""
    try:
        # Parse date and time
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(time_str, '%H:%M').time()
        
        # Check if appointment is in the future
        current_datetime = datetime.now()
        appointment_datetime = datetime.combine(appointment_date, appointment_time)
        
        if appointment_datetime <= current_datetime:
            return False, "Appointment must be in the future"
            
        # Check if within working hours (8 AM to 6 PM)
        working_start = time(8, 0)
        working_end = time(18, 0)
        
        if appointment_time < working_start or appointment_time > working_end:
            return False, "Appointments must be between 8 AM and 6 PM"
            
        return True, None
    except ValueError as e:
        return False, f"Invalid date/time format: {str(e)}"

def check_doctor_availability(doctor_id, date_str, time_str, exclude_appointment_id=None):
    """Check if doctor is available at the given time"""
    try:
        query = admin_client.table("appointments").select("id").eq("doctor_id", doctor_id).eq("date", date_str).eq("time", time_str)
        
        # Exclude current appointment if updating
        if exclude_appointment_id:
            query = query.neq("id", exclude_appointment_id)
            
        # Only check non-cancelled appointments
        query = query.not_.eq("status", "cancelled")
        
        result = query.execute()
        
        if result.data:
            return False, "Doctor is already booked at this time"
            
        return True, None
    except Exception as e:
        return False, f"Error checking doctor availability: {str(e)}"

def check_patient_availability(patient_id, date_str, time_str, exclude_appointment_id=None):
    """Check if patient has any conflicting appointments"""
    try:
        query = admin_client.table("appointments").select("id").eq("patient_id", patient_id).eq("date", date_str).eq("time", time_str)
        
        # Exclude current appointment if updating
        if exclude_appointment_id:
            query = query.neq("id", exclude_appointment_id)
            
        # Only check non-cancelled appointments
        query = query.not_.eq("status", "cancelled")
        
        result = query.execute()
        
        if result.data:
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
        # Base query
        query = admin_client.table("appointments").select(
            "*",
            "patient:patient_id(*)" if is_doctor else "doctor:doctor_id(*)"
        )
        
        # Add user filter
        if is_doctor:
            query = query.eq("doctor_id", user_id)
        else:
            query = query.eq("patient_id", user_id)
            
        # Apply status filter
        if filters.get('status'):
            query = query.eq("status", filters['status'])
            
        # Apply date range filter
        if filters.get('start_date'):
            query = query.gte("date", filters['start_date'])
        if filters.get('end_date'):
            query = query.lte("date", filters['end_date'])
            
        # Apply upcoming/past filter
        today = datetime.now().strftime('%Y-%m-%d')
        if filters.get('type') == 'upcoming':
            query = query.gte("date", today)
        elif filters.get('type') == 'past':
            query = query.lt("date", today)
            
        # Apply sorting
        query = query.order("date").order("time")
        
        result = query.execute()
        
        # Format the response
        appointments = []
        for apt in result.data:
            if is_doctor:
                patient_info = apt.pop("patient", {})
                apt["patient_name"] = patient_info.get("full_name") if patient_info else None
                apt["patient_phone"] = patient_info.get("phone") if patient_info else None
            else:
                doctor_info = apt.pop("doctor", {})
                apt["doctor_name"] = doctor_info.get("full_name") if doctor_info else None
                
            appointments.append(apt)
            
        return True, appointments
    except Exception as e:
        return False, f"Error fetching appointments: {str(e)}" 