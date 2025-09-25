from datetime import datetime, timedelta
from supabase_client import admin_client
from .push_notifications import push_notifications
from .models import PushSubscription
import pytz
from .email_client import email_client
from .beem_client import beem_client
import logging
from .logging_config import NotificationLogger, LogCategory

logger = logging.getLogger(__name__)
notification_logger = NotificationLogger('notification_utils')

def format_appointment_time(date_str, time_str):
    """Format appointment date and time for messages"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.strptime(time_str, '%H:%M').time()
        dt = datetime.combine(date, time)
        return dt.strftime('%A, %B %d at %I:%M %p')
    except ValueError:
        return f"{date_str} at {time_str}"

def get_appointment_details(appointment_id):
    """Get full appointment details including patient and doctor info"""
    try:
        result = admin_client.table("appointments").select(
            "*",
            "patient:patient_id(*)",
            "doctor:doctor_id(*)"
        ).eq("id", appointment_id).single().execute()
        
        if not result.data:
            return None
            
        appointment = result.data
        patient = appointment.get("patient", {})
        doctor = appointment.get("doctor", {})
        
        formatted_time = format_appointment_time(appointment["date"], appointment["time"])
        
        return {
            "id": appointment["id"],
            "date": appointment["date"],
            "time": appointment["time"],
            "appointment_time": formatted_time,  # Formatted for messages
            "type": appointment["type"],
            "status": appointment["status"],
            "location": appointment.get("location", "Main Hospital"),
            "patient_name": patient.get("full_name"),
            "patient_phone": patient.get("phone"),
            "doctor_name": doctor.get("full_name"),
            "patient_id": patient.get("user_id"),  # For push notifications
            "doctor_id": doctor.get("user_id")  # For push notifications
        }
    except Exception as e:
        notification_logger.error(
            LogCategory.DATABASE,
            "Error retrieving appointment details from Supabase",
            "appointment_data_fetcher",
            appointment_id=appointment_id,
            error_details=str(e)
        )
        return None

def get_appointment_data(appointment_id):
    """Get formatted appointment data for notifications"""
    try:
        # Import Django models here to avoid circular imports
        from appointments.models import Appointment
        from accounts.models import EnhancedPatient, EnhancedStaffProfile
        
        # Get the appointment from Django database
        try:
            appointment = Appointment.objects.select_related(
                'patient__user', 'provider__user', 'appointment_type', 'room'
            ).get(id=appointment_id)
        except Appointment.DoesNotExist:
            return None, "Appointment not found"
        
        # Format location from room information
        location = "Main Hospital"
        if appointment.room:
            location_parts = []
            if appointment.room.name:
                location_parts.append(appointment.room.name)
            if appointment.room.room_number:
                location_parts.append(f"Room {appointment.room.room_number}")
            if appointment.room.floor:
                location_parts.append(f"Floor {appointment.room.floor}")
            if appointment.room.building:
                location_parts.append(appointment.room.building)
            
            if location_parts:
                location = ", ".join(location_parts)
        
        # Format the data
        formatted_data = {
            "id": str(appointment.id),
            "doctor_name": appointment.provider.user.get_full_name(),
            "patient_name": appointment.patient.user.get_full_name(),
            "patient_phone": getattr(appointment.patient.user, 'phone', ''),
            "patient_id": str(appointment.patient.user.id),
            "doctor_id": str(appointment.provider.user.id),
            "appointment_time": f"{appointment.appointment_date} {appointment.start_time}",
            "location": location,
            "type": appointment.appointment_type.name if appointment.appointment_type else "consultation",
            "status": appointment.status
        }
        
        return formatted_data, None
    except Exception as e:
        notification_logger.error(
            LogCategory.DATABASE,
            "Error retrieving appointment data from Django models",
            "appointment_data_processor",
            appointment_id=appointment_id,
            error_details=str(e)
        )
        return None, str(e)

def send_push_to_user(user_id, title, message, url=None, data=None):
    """Helper function to send push notification to all user's subscriptions"""
    try:
        # Get all subscriptions for the user
        subscriptions = PushSubscription.objects.filter(user_id=user_id)
        if not subscriptions:
            return False, "No push subscriptions found for user"

        success = False
        for subscription in subscriptions:
            # Try sending to each subscription
            push_success, push_message = push_notifications.send_push_notification(
                subscription_info=subscription.to_subscription_info(),
                title=title,
                message=message,
                url=url,
                data=data
            )
            if push_success:
                success = True

        return success, "Push notification sent successfully" if success else "Failed to send to all subscriptions"
    except Exception as e:
        return False, str(e)

def get_patient_data(patient_id):
    """Get patient data by ID"""
    try:
        result = admin_client.table("enhanced_patients").select("*").eq("id", patient_id).single().execute()
        
        if not result.data:
            return None
            
        patient = result.data
        return {
            "id": patient["id"],
            "full_name": patient.get("full_name"),
            "email": patient.get("email"),
            "phone": patient.get("phone"),
            "date_of_birth": patient.get("date_of_birth"),
            "gender": patient.get("gender"),
            "address": patient.get("address"),
            "emergency_contact": patient.get("emergency_contact"),
            "medical_history": patient.get("medical_history"),
            "allergies": patient.get("allergies"),
            "medications": patient.get("medications"),
            "insurance_info": patient.get("insurance_info"),
            "preferences": patient.get("preferences", {}),
            "created_at": patient.get("created_at"),
            "updated_at": patient.get("updated_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting patient data for ID {patient_id}: {e}")
        return None

def get_doctor_data(doctor_id):
    """Get doctor data by ID"""
    try:
        result = admin_client.table("doctors").select("*").eq("id", doctor_id).single().execute()
        
        if not result.data:
            return None
            
        doctor = result.data
        return {
            "id": doctor["id"],
            "full_name": doctor.get("full_name"),
            "email": doctor.get("email"),
            "phone": doctor.get("phone"),
            "specialization": doctor.get("specialization"),
            "department": doctor.get("department"),
            "license_number": doctor.get("license_number"),
            "years_of_experience": doctor.get("years_of_experience"),
            "education": doctor.get("education"),
            "certifications": doctor.get("certifications"),
            "languages": doctor.get("languages", []),
            "office_location": doctor.get("office_location"),
            "schedule": doctor.get("schedule", {}),
            "bio": doctor.get("bio"),
            "profile_image": doctor.get("profile_image"),
            "availability": doctor.get("availability", {}),
            "created_at": doctor.get("created_at"),
            "updated_at": doctor.get("updated_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting doctor data for ID {doctor_id}: {e}")
        return None

def send_appointment_reminder(appointment_id):
    """Send appointment reminder notification"""
    try:
        appointment_data, error = get_appointment_data(appointment_id)
        if error:
            return False, error
            
        # Send push notification to patient
        success, message = push_notifications.send_appointment_reminder_push(
            appointment_data["patient_id"],
            appointment_data
        )
        
        if not success:
            return False, f"Failed to send push notification: {message}"
            
        return True, "Reminder sent successfully"
    except Exception as e:
        return False, str(e)

def send_appointment_confirmation(appointment_id, patient_email, doctor_email):
    """Send appointment confirmation notifications to both patient and doctor"""
    try:
        # Get formatted appointment data
        appointment_data, error = get_appointment_data(appointment_id)
        if error:
            logger.error(f"Failed to get appointment data: {error}")
            return False, error

        # Send email to patient
        success, message = email_client.send_appointment_confirmation_email(
            appointment_data=appointment_data,
            recipient_email=patient_email,
            is_patient=True
        )
        if not success:
            logger.error(f"Failed to send confirmation email to patient: {message}")

        # Send email to doctor
        success, message = email_client.send_appointment_confirmation_email(
            appointment_data=appointment_data,
            recipient_email=doctor_email,
            is_patient=False
        )
        if not success:
            logger.error(f"Failed to send confirmation email to doctor: {message}")

        # Send SMS to patient if phone number is available
        if appointment_data.get('patient_phone'):
            success, message = beem_client.send_sms(
                recipient=appointment_data['patient_phone'],
                message=f"Your appointment with Dr. {appointment_data['doctor_name']} has been confirmed for {appointment_data['appointment_time']}."
            )
            if not success:
                logger.error(f"Failed to send confirmation SMS to patient: {message}")

        # Send push notification to patient if device token is available
        if appointment_data.get('patient_id'):
            success, message = push_notifications.send_appointment_update_push(
                user_id=appointment_data['patient_id'],
                appointment_data=appointment_data,
                update_type="confirmation"
            )
            if not success:
                logger.error(f"Failed to send confirmation push notification to patient: {message}")

        return True, "Notifications sent successfully"

    except Exception as e:
        logger.error(f"Error sending appointment confirmation notifications: {str(e)}")
        return False, str(e)

def send_appointment_update(appointment_data, update_type, patient_email, doctor_email):
    """Send appointment update notifications to both patient and doctor"""
    try:
        # Send email to patient
        success, message = email_client.send_appointment_update_email(
            appointment_data=appointment_data,
            update_type=update_type,
            recipient_email=patient_email,
            is_patient=True
        )
        if not success:
            logger.error(f"Failed to send update email to patient: {message}")

        # Send email to doctor
        success, message = email_client.send_appointment_update_email(
            appointment_data=appointment_data,
            update_type=update_type,
            recipient_email=doctor_email,
            is_patient=False
        )
        if not success:
            logger.error(f"Failed to send update email to doctor: {message}")

        # Send SMS to patient if phone number is available
        if appointment_data.get('patient_phone'):
            message = f"Your appointment with Dr. {appointment_data['doctor_name']} has been {update_type}ed for {appointment_data['date']} at {appointment_data['time']}."
            success, msg = beem_client.send_sms(
                recipient=appointment_data['patient_phone'],
                message=message
            )
            if not success:
                logger.error(f"Failed to send update SMS to patient: {msg}")

        # Send push notification to patient if device token is available
        if appointment_data.get('patient_device_token'):
            success, message = send_push_notification(
                device_token=appointment_data['patient_device_token'],
                title=f"Appointment {update_type.title()}ed",
                body=f"Your appointment with Dr. {appointment_data['doctor_name']} has been {update_type}ed for {appointment_data['date']} at {appointment_data['time']}."
            )
            if not success:
                logger.error(f"Failed to send update push notification to patient: {message}")

        return True, "Notifications sent successfully"

    except Exception as e:
        logger.error(f"Error sending appointment update notifications: {str(e)}")
        return False, str(e)

def trigger_manual_reminder(appointment_id):
    """Manually trigger a reminder for testing"""
    try:
        appointment_data, error = get_appointment_data(appointment_id)
        if error:
            return False, error
            
        # Send push notification
        success, message = push_notifications.send_appointment_reminder_push(
            appointment_data["patient_id"],
            appointment_data
        )
        
        if not success:
            return False, f"Failed to send push notification: {message}"
            
        return True, "Manual reminder sent successfully"
    except Exception as e:
        return False, str(e)

def check_upcoming_appointments():
    """Check and send reminders for upcoming appointments"""
    try:
        # Get appointments in the next 24 hours
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        result = admin_client.table("appointments").select("id").eq("date", tomorrow_str).execute()
        
        if not result.data:
            return True, "No upcoming appointments found"
            
        success_count = 0
        total_count = len(result.data)
        
        for appointment in result.data:
            success, _ = send_appointment_reminder(appointment["id"])
            if success:
                success_count += 1
                
        return True, f"Processed {success_count}/{total_count} reminders successfully"
    except Exception as e:
        return False, str(e)

def send_upcoming_appointment_reminders():
    """Send reminders for appointments in the next 24 hours"""
    try:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Get all appointments for tomorrow that haven't been reminded in the last 12 hours
        twelve_hours_ago = (datetime.now() - timedelta(hours=12)).isoformat()
        
        result = admin_client.table("appointments").select("id").eq("date", tomorrow).execute()
        
        if not result.data:
            return True, "No upcoming appointments to remind"
            
        success_count = 0
        fail_count = 0
        
        for appointment in result.data:
            success, message = send_appointment_reminder(appointment["id"])
            if success:
                success_count += 1
            else:
                fail_count += 1
                notification_logger.error(
                    LogCategory.NOTIFICATION,
                    "Failed to send appointment reminder",
                    "reminder_scheduler",
                    appointment_id=appointment['id'],
                    error_message=message
                )
        
        return True, f"Sent {success_count} reminders, {fail_count} failed"
        
    except Exception as e:
        notification_logger.error(
            LogCategory.NOTIFICATION,
            "Error sending upcoming appointment reminders",
            "reminder_scheduler",
            error_details=str(e)
        )
        return False, str(e)