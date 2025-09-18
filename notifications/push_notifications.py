from django.conf import settings
# from pywebpush import webpush, WebPushException  # Commented out - not compatible with Python 3.13
import json
from pathlib import Path
from supabase_client import admin_client
import base64
from io import BytesIO

class PushNotificationHandler:
    """Handler for web push notifications"""
    
    def __init__(self):
        """Initialize with VAPID keys from settings"""
        self.vapid_private_key = settings.WEBPUSH_SETTINGS.get('VAPID_PRIVATE_KEY')
        self.vapid_public_key = settings.WEBPUSH_SETTINGS.get('VAPID_PUBLIC_KEY')
        self.vapid_claims = {
            "sub": f"mailto:{settings.WEBPUSH_SETTINGS.get('VAPID_ADMIN_EMAIL', 'admin@mediremind.com')}",
            "aud": "https://fcm.googleapis.com"  # Required for Chrome/Firefox
        }
        
        # Web push functionality temporarily disabled due to Python 3.13 compatibility issues
        if not self.vapid_private_key or not self.vapid_public_key:
            print("Warning: VAPID keys not properly configured. Web push notifications disabled.")
    
    def send_push_notification(self, subscription_info, title, message, url=None, data=None):
        """Send a push notification to a subscription"""
        # Web push functionality temporarily disabled due to Python 3.13 compatibility issues
        print(f"Web push notification disabled: {title} - {message}")
        print("Web push functionality temporarily disabled due to Python 3.13 compatibility issues")
        return False, "Web push functionality temporarily disabled"
    
    def get_user_subscriptions(self, user_id):
        """Get all push subscriptions for a user from Supabase"""
        try:
            if not user_id:
                print("No user ID provided")
                return []

            result = admin_client.table("push_subscriptions").select("*").eq("user_id", user_id).execute()
            
            if not result.data:
                print(f"No subscriptions found for user {user_id}")
                return []
                
            subscriptions = []
            for sub in result.data:
                subscription_info = {
                    'endpoint': sub['endpoint'],
                    'keys': {
                        'p256dh': sub['p256dh'],
                        'auth': sub['auth']
                    }
                }
                subscriptions.append(subscription_info)
                
            return subscriptions
        except Exception as e:
            print(f"Error getting user subscriptions: {str(e)}")
            return []
    
    def send_to_user(self, user_id, title, message, url=None, data=None):
        """Send push notification to all user's subscriptions"""
        try:
            if not user_id:
                return False, "User ID is required"

            subscriptions = self.get_user_subscriptions(user_id)
            if not subscriptions:
                return False, "No push subscriptions found for user"

            success = False
            errors = []
            for subscription in subscriptions:
                # Try sending to each subscription
                push_success, push_message = self.send_push_notification(
                    subscription_info=subscription,
                    title=title,
                    message=message,
                    url=url,
                    data=data
                )
                if push_success:
                    success = True
                else:
                    errors.append(push_message)

            if success:
                return True, "Push notification sent successfully to at least one subscription"
            else:
                error_msg = "; ".join(errors) if errors else "Failed to send to all subscriptions"
                return False, error_msg
        except Exception as e:
            return False, str(e)
    
    def send_appointment_reminder_push(self, user_id, appointment_data):
        """Send appointment reminder push notification"""
        if not user_id or not appointment_data:
            return False, "User ID and appointment data are required"
            
        title = "Upcoming Appointment Reminder"
        message = (
            f"You have an appointment with Dr. {appointment_data.get('doctor_name', 'Unknown')} "
            f"on {appointment_data.get('appointment_time', 'Unknown')} at {appointment_data.get('location', 'Unknown')}"
        )
        url = "/appointments"  # Frontend URL for appointments page
        
        return self.send_to_user(
            user_id=user_id,
            title=title,
            message=message,
            url=url,
            data={"appointment_id": appointment_data.get("id")}
        )
    
    def send_appointment_update_push(self, user_id, appointment_data, update_type):
        """Send appointment update push notification"""
        if not user_id or not appointment_data or not update_type:
            return False, "User ID, appointment data, and update type are required"

        if update_type == "confirmation":
            title = "Appointment Confirmed"
            message = (
                f"Your appointment with Dr. {appointment_data.get('doctor_name', 'Unknown')} "
                f"on {appointment_data.get('appointment_time', 'Unknown')} has been confirmed."
            )
        elif update_type == "cancellation":
            title = "Appointment Cancelled"
            message = (
                f"Your appointment with Dr. {appointment_data.get('doctor_name', 'Unknown')} "
                f"on {appointment_data.get('appointment_time', 'Unknown')} has been cancelled."
            )
        elif update_type == "reschedule":
            title = "Appointment Rescheduled"
            message = (
                f"Your appointment with Dr. {appointment_data.get('doctor_name', 'Unknown')} "
                f"has been rescheduled to {appointment_data.get('appointment_time', 'Unknown')}."
            )
        else:
            return False, "Invalid update type"
        
        url = f"/appointments/{appointment_data.get('id')}"
        
        return self.send_to_user(
            user_id=user_id,
            title=title,
            message=message,
            url=url,
            data={"appointment_id": appointment_data.get("id")}
        )

push_notifications = PushNotificationHandler()

__all__ = ['push_notifications']