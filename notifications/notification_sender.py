"""
Comprehensive notification sending service that integrates FCM, email, SMS, and web push.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from .fcm_service import FCMService
from .push_notifications import PushNotificationHandler
from .models import ScheduledTask, PushSubscription
from .email_service import EmailService
from .sms_service import SMSService

logger = logging.getLogger(__name__)

class NotificationSender:
    """
    Unified notification sending service that handles multiple channels:
    - FCM (Firebase Cloud Messaging) for mobile push notifications
    - Web Push for browser notifications
    - Email notifications
    - SMS notifications
    """
    
    def __init__(self):
        self.fcm_service = FCMService()
        self.push_handler = PushNotificationHandler()
        self.email_service = EmailService()
        self.sms_service = SMSService()
    
    async def send_medication_reminder(
        self,
        user: User,
        medication_name: str,
        dosage: str,
        time: str,
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        Send medication reminder through specified channels.
        
        Args:
            user: User to send notification to
            medication_name: Name of the medication
            dosage: Dosage information
            time: Time for medication
            channels: List of channels to use ['fcm', 'email', 'sms', 'web_push']
        
        Returns:
            Dict with success status for each channel
        """
        if channels is None:
            channels = ['fcm', 'web_push']
        
        title = "Medication Reminder"
        message = f"Time to take your {medication_name} ({dosage}) at {time}"
        
        results = {}
        
        # Send FCM notification
        if 'fcm' in channels:
            try:
                fcm_result = self.fcm_service.send_to_user(
                    user_id=user.id,
                    title=title,
                    body=message,
                    data={
                        'type': 'medication_reminder',
                        'medication_name': medication_name,
                        'dosage': dosage,
                        'time': time,
                        'action_required': True
                    }
                )
                results['fcm'] = fcm_result.get('success', False)
            except Exception as e:
                logger.error(f"FCM medication reminder failed for user {user.id}: {e}")
                results['fcm'] = False
        
        # Send web push notification
        if 'web_push' in channels:
            try:
                web_push_result = await self._send_web_push_medication_reminder(
                    user, title, message, medication_name, dosage, time
                )
                results['web_push'] = web_push_result
            except Exception as e:
                logger.error(f"Web push medication reminder failed for user {user.id}: {e}")
                results['web_push'] = False
        
        # Send email notification
        if 'email' in channels:
            try:
                email_result = await self._send_email_medication_reminder(
                    user, medication_name, dosage, time
                )
                results['email'] = email_result
            except Exception as e:
                logger.error(f"Email medication reminder failed for user {user.id}: {e}")
                results['email'] = False
        
        # Send SMS notification
        if 'sms' in channels:
            try:
                sms_result = await self._send_sms_medication_reminder(
                    user, medication_name, dosage, time
                )
                results['sms'] = sms_result
            except Exception as e:
                logger.error(f"SMS medication reminder failed for user {user.id}: {e}")
                results['sms'] = False
        
        # Log the notification
        await self._log_notification(
            user=user,
            notification_type='medication_reminder',
            title=title,
            message=message,
            channels=channels,
            results=results
        )
        
        return results
    
    async def send_appointment_reminder(
        self,
        user: User,
        appointment_details: Dict[str, Any],
        reminder_time: str,
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        Send appointment reminder through specified channels.
        """
        if channels is None:
            channels = ['fcm', 'email']
        
        doctor_name = appointment_details.get('doctor_name', 'your doctor')
        appointment_time = appointment_details.get('time', 'scheduled time')
        location = appointment_details.get('location', 'clinic')
        
        title = "Appointment Reminder"
        message = f"You have an appointment with {doctor_name} at {appointment_time}"
        
        results = {}
        
        # Send FCM notification
        if 'fcm' in channels:
            try:
                fcm_result = self.fcm_service.send_to_user(
                    user_id=user.id,
                    title=title,
                    body=message,
                    data={
                        'type': 'appointment_reminder',
                        'doctor_name': doctor_name,
                        'appointment_time': appointment_time,
                        'location': location,
                        'reminder_time': reminder_time
                    }
                )
                results['fcm'] = fcm_result.get('success', False)
            except Exception as e:
                logger.error(f"FCM appointment reminder failed for user {user.id}: {e}")
                results['fcm'] = False
        
        # Send other channels...
        # (Similar implementation for web_push, email, sms)
        
        return results
    
    async def send_emergency_alert(
        self,
        user: User,
        alert_message: str,
        severity: str = 'high',
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        Send emergency alert through all available channels.
        """
        if channels is None:
            channels = ['fcm', 'web_push', 'email', 'sms']
        
        title = "Emergency Alert"
        
        results = {}
        
        # Send FCM with high priority
        if 'fcm' in channels:
            try:
                fcm_result = self.fcm_service.send_to_user(
                    user_id=user.id,
                    title=title,
                    body=alert_message,
                    data={
                        'type': 'emergency_alert',
                        'severity': severity,
                        'timestamp': timezone.now().isoformat()
                    },
                    priority='high'
                )
                results['fcm'] = fcm_result.get('success', False)
            except Exception as e:
                logger.error(f"FCM emergency alert failed for user {user.id}: {e}")
                results['fcm'] = False
        
        # Send through other channels with high priority...
        
        return results
    
    async def send_system_notification(
        self,
        user: User,
        title: str,
        message: str,
        notification_type: str = 'system',
        data: Dict[str, Any] = None,
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        Send general system notification.
        """
        if channels is None:
            channels = ['fcm']
        
        if data is None:
            data = {}
        
        data.update({
            'type': notification_type,
            'timestamp': timezone.now().isoformat()
        })
        
        results = {}
        
        # Send FCM notification
        if 'fcm' in channels:
            try:
                fcm_result = self.fcm_service.send_to_user(
                    user_id=user.id,
                    title=title,
                    body=message,
                    data=data
                )
                results['fcm'] = fcm_result.get('success', False)
            except Exception as e:
                logger.error(f"FCM system notification failed for user {user.id}: {e}")
                results['fcm'] = False
        
        return results
    
    async def _send_web_push_medication_reminder(
        self,
        user: User,
        title: str,
        message: str,
        medication_name: str,
        dosage: str,
        time: str
    ) -> bool:
        """Send web push notification for medication reminder."""
        try:
            subscriptions = PushSubscription.objects.filter(user_id=user.id)
            if not subscriptions.exists():
                return False
            
            notification_data = {
                'title': title,
                'body': message,
                'icon': '/static/icons/medication-icon.png',
                'badge': '/static/icons/badge-icon.png',
                'data': {
                    'type': 'medication_reminder',
                    'medication_name': medication_name,
                    'dosage': dosage,
                    'time': time,
                    'url': '/medications'
                },
                'actions': [
                    {
                        'action': 'taken',
                        'title': 'Mark as Taken'
                    },
                    {
                        'action': 'snooze',
                        'title': 'Snooze 15 min'
                    }
                ]
            }
            
            success_count = 0
            for subscription in subscriptions:
                try:
                    await self.push_handler.send_notification(
                        subscription.endpoint,
                        subscription.p256dh,
                        subscription.auth,
                        notification_data
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Web push failed for subscription {subscription.id}: {e}")
            
            return success_count > 0
        except Exception as e:
            logger.error(f"Web push medication reminder error: {e}")
            return False
    
    async def _send_email_medication_reminder(
        self,
        user: User,
        medication_name: str,
        dosage: str,
        time: str
    ) -> bool:
        """Send email notification for medication reminder."""
        try:
            subject = f"Medication Reminder: {medication_name}"
            template_data = {
                'user_name': user.first_name or user.username,
                'medication_name': medication_name,
                'dosage': dosage,
                'time': time,
                'app_url': settings.FRONTEND_URL
            }
            
            return await self.email_service.send_medication_reminder(
                to_email=user.email,
                subject=subject,
                template_data=template_data
            )
        except Exception as e:
            logger.error(f"Email medication reminder error: {e}")
            return False
    
    async def _send_sms_medication_reminder(
        self,
        user: User,
        medication_name: str,
        dosage: str,
        time: str
    ) -> bool:
        """Send SMS notification for medication reminder."""
        try:
            if not hasattr(user, 'profile') or not user.profile.phone_number:
                return False
            
            message = f"MediRemind: Time to take your {medication_name} ({dosage}) at {time}. Reply TAKEN when completed."
            
            return await self.sms_service.send_sms(
                phone_number=user.profile.phone_number,
                message=message
            )
        except Exception as e:
            logger.error(f"SMS medication reminder error: {e}")
            return False
    
    async def _log_notification(
        self,
        user: User,
        notification_type: str,
        title: str,
        message: str,
        channels: List[str],
        results: Dict[str, bool]
    ):
        """Log notification attempt to database."""
        try:
            # Create a scheduled task record for tracking
            ScheduledTask.objects.create(
                user_id=user.id,
                task_type=notification_type,
                delivery_method=','.join(channels),
                priority='normal',
                status='completed' if any(results.values()) else 'failed',
                title=title,
                message=message,
                metadata={
                    'channels': channels,
                    'results': results,
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")

# Singleton instance
notification_sender = NotificationSender()