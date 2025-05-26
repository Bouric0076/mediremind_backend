from datetime import datetime, timedelta
from supabase_client import admin_client
from .twilio_client import twilio_client
from .push_notifications import push_notifications
from .models import PushSubscription
import pytz
from .email_client import email_client
from .beem_client import beem_client
import logging

logger = logging.getLogger(__name__)

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
            "location": appointment.get("location_text", "Main Hospital"),
            "patient_name": patient.get("full_name"),
            "patient_phone": patient.get("phone"),
            "doctor_name": doctor.get("full_name"),
            "patient_id": patient.get("user_id"),  # For push notifications
            "doctor_id": doctor.get("user_id")  # For push notifications
        }
    except Exception as e:
        print(f"Error getting appointment details: {str(e)}")
        return None

def get_appointment_data(appointment_id):
    """Get formatted appointment data for notifications"""
    try:
        # Get the appointment details
        result = admin_client.table("appointments").select(
            "*"
        ).eq("id", appointment_id).single().execute()
        
        if not result.data:
            return None, "Appointment not found"
            
        appointment = result.data
        
        # Get doctor details from users table via staff_profiles
        doctor_result = admin_client.table("staff_profiles").select(
            "user_id",
            "users!inner(full_name)"
        ).eq("user_id", appointment["doctor_id"]).single().execute()
        
        # Get patient details from users table via patients
        patient_result = admin_client.table("patients").select(
            "user_id",
            "users!inner(full_name, phone)"
        ).eq("user_id", appointment["patient_id"]).single().execute()
        
        if not doctor_result.data or not patient_result.data:
            return None, "Could not find doctor or patient details"
            
        doctor_data = doctor_result.data.get("users", {})
        patient_data = patient_result.data.get("users", {})
        
        formatted_data = {
            "id": appointment["id"],
            "doctor_name": doctor_data.get("full_name", "Unknown Doctor"),
            "patient_name": patient_data.get("full_name", "Unknown Patient"),
            "patient_phone": patient_data.get("phone"),
            "patient_id": appointment["patient_id"],
            "doctor_id": appointment["doctor_id"],
            "appointment_time": f"{appointment['date']} {appointment['time']}",
            "location": appointment.get("location_text", "Main Hospital"),
            "type": appointment.get("type", "consultation"),
            "status": appointment.get("status", "scheduled")
        }
        
        if not formatted_data["patient_id"]:
            return None, "Patient ID not found"
            
        return formatted_data, None
    except Exception as e:
        print(f"Error in get_appointment_data: {str(e)}")  # Add debug logging
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

        # Send WhatsApp message to patient if phone number is available
        if appointment_data.get('patient_phone'):
            success, message = twilio_client.send_whatsapp(
                recipient=appointment_data['patient_phone'],
                message=f"Your appointment with Dr. {appointment_data['doctor_name']} has been confirmed for {appointment_data['appointment_time']}."
            )
            if not success:
                logger.error(f"Failed to send confirmation WhatsApp to patient: {message}")

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

        # Send WhatsApp message to patient if phone number is available
        if appointment_data.get('patient_phone'):
            message = f"Your appointment with Dr. {appointment_data['doctor_name']} has been {update_type}ed for {appointment_data['date']} at {appointment_data['time']}."
            success, msg = twilio_client.send_whatsapp(
                to=appointment_data['patient_phone'],
                message=message
            )
            if not success:
                logger.error(f"Failed to send update WhatsApp to patient: {msg}")

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
                print(f"Failed to send reminder for appointment {appointment['id']}: {message}")
        
        return True, f"Sent {success_count} reminders, {fail_count} failed"
        
    except Exception as e:
        print(f"Error sending upcoming reminders: {str(e)}")
        return False, str(e) 