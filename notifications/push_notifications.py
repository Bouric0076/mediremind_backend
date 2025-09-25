from django.conf import settings
from pywebpush import webpush, WebPushException  # Re-enabled - pywebpush is compatible with Python 3.13
import json
from pathlib import Path
from supabase_client import admin_client
from .logging_config import NotificationLogger, LogCategory
import base64
from io import BytesIO

class PushNotificationHandler:
    """Handler for web push notifications"""
    
    def __init__(self):
        """Initialize with VAPID keys from settings"""
        self.logger = NotificationLogger('push_notifications')
        try:
            webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
            self.vapid_private_key = webpush_settings.get('VAPID_PRIVATE_KEY')
            self.vapid_public_key = webpush_settings.get('VAPID_PUBLIC_KEY')
            self.vapid_claims = {
                "sub": f"mailto:{webpush_settings.get('VAPID_ADMIN_EMAIL', 'admin@mediremind.com')}",
                "aud": "https://fcm.googleapis.com"  # Required for Chrome/Firefox
            }
        except:
            # Fallback for when Django settings are not configured (e.g., during testing)
            self.vapid_private_key = None
            self.vapid_public_key = None
            self.vapid_claims = {
                "sub": "mailto:admin@mediremind.com",
                "aud": "https://fcm.googleapis.com"
            }
        
        if not self.vapid_private_key or not self.vapid_public_key:
            self.logger.warning(
                LogCategory.NOTIFICATION,
                "VAPID keys not properly configured. Web push notifications disabled.",
                "push_notification_manager",
                metadata={'vapid_configured': False}
            )
    
    def send_push_notification(self, subscription_info, title, message, url=None, data=None):
        """Send a push notification to a subscription"""
        if not self.vapid_private_key or not self.vapid_public_key:
            self.logger.warning(
                LogCategory.NOTIFICATION,
                "VAPID keys not configured for push notification",
                "push_notification_sender",
                metadata={'title': title, 'vapid_configured': False}
            )
            return False, "VAPID keys not configured"
        
        try:
            payload = {
                "title": title,
                "body": message,
                "icon": "/static/icons/notification-icon.png",
                "badge": "/static/icons/badge-icon.png",
                "data": data or {}
            }
            
            if url:
                payload["data"]["url"] = url
            
            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{self.vapid_email}",
                    "aud": f"{subscription_info['endpoint'].split('/')[2]}"
                }
            )
            
            self.logger.info(
                LogCategory.NOTIFICATION,
                f"Push notification sent successfully: {title}",
                "push_notification_sender",
                metadata={'title': title, 'endpoint': subscription_info.get('endpoint', 'unknown')}
            )
            return True, "Notification sent successfully"
            
        except WebPushException as e:
            self.logger.error(
                LogCategory.NOTIFICATION,
                f"Failed to send push notification: {title}",
                "push_notification_sender",
                metadata={'title': title, 'error_type': 'WebPushException'},
                error_details=str(e)
            )
            return False, f"WebPush error: {str(e)}"
        except Exception as e:
            self.logger.error(
                LogCategory.NOTIFICATION,
                f"Unexpected error sending push notification: {title}",
                "push_notification_sender",
                metadata={'title': title, 'error_type': type(e).__name__},
                error_details=str(e)
            )
            return False, f"Unexpected error: {str(e)}"
    
    def get_user_subscriptions(self, user_id):
        """Get all push subscriptions for a user from Supabase"""
        try:
            if not user_id:
                self.logger.warning(
                    LogCategory.NOTIFICATION,
                    "No user ID provided for subscription lookup",
                    "push_subscription_manager"
                )
                return []

            result = admin_client.table("push_subscriptions").select("*").eq("user_id", user_id).execute()
            
            if not result.data:
                self.logger.info(
                    LogCategory.NOTIFICATION,
                    f"No push subscriptions found for user",
                    "push_subscription_manager",
                    user_id=user_id
                )
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
            self.logger.error(
                LogCategory.DATABASE,
                "Error retrieving user push subscriptions",
                "push_subscription_manager",
                user_id=user_id,
                error_details=str(e)
            )
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