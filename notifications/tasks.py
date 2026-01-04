"""
Celery tasks for notification handling with proper retry policies and error handling.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

from .models import NotificationLog, ScheduledTask, PushSubscription
from .fcm_service import FCMService
from .email_service import EmailService
from .sms_service import SMSService
from .push_notifications import PushNotificationHandler
import json

logger = logging.getLogger(__name__)


def create_notification_log(
    user: User,
    notification_type: str,
    title: str,
    message: str,
    channels: List[str],
    appointment_id: int = None,
    medication_id: int = None
) -> NotificationLog:
    """Create initial notification log entry before sending."""
    return NotificationLog.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        channels=channels,
        status='pending',
        appointment_id=appointment_id,
        medication_id=medication_id,
        created_at=timezone.now(),
        metadata={'channels_requested': channels}
    )


def update_notification_log(
    log: NotificationLog,
    channel: str,
    success: bool,
    provider_id: str = None,
    error_code: str = None,
    error_message: str = None
):
    """Update notification log with channel-specific results."""
    if not hasattr(log, 'results'):
        log.results = {}
    if not hasattr(log, 'provider_ids'):
        log.provider_ids = {}
    if not hasattr(log, 'error_codes'):
        log.error_codes = {}
    
    log.results[channel] = success
    if provider_id:
        log.provider_ids[channel] = provider_id
    if error_code:
        log.error_codes[channel] = error_code
    if error_message:
        if not hasattr(log, 'error_messages'):
            log.error_messages = {}
        log.error_messages[channel] = error_message
    
    # Update overall status
    if any(log.results.values()):
        log.status = 'sent'
    else:
        log.status = 'failed'
    
    log.updated_at = timezone.now()
    log.save()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_medication_reminder_task(
    self,
    user_id: int,
    medication_name: str,
    dosage: str,
    time: str,
    channels: List[str] = None,
    medication_id: int = None
):
    """
    Celery task for sending medication reminders with proper retry and logging.
    """
    try:
        user = User.objects.get(id=user_id)
        if channels is None:
            channels = ['fcm', 'email']
        
        title = f"Medication Reminder: {medication_name}"
        message = f"Time to take your {medication_name} ({dosage}) at {time}"
        
        # Create initial log entry
        log = create_notification_log(
            user=user,
            notification_type='medication_reminder',
            title=title,
            message=message,
            channels=channels,
            medication_id=medication_id
        )
        
        # Initialize services
        fcm_service = FCMService()
        email_service = EmailService()
        sms_service = SMSService()
        push_handler = PushNotificationHandler()
        
        # Send through each channel
        for channel in channels:
            try:
                if channel == 'fcm':
                    result = fcm_service.send_to_user(
                        user_id=user.id,
                        title=title,
                        body=message,
                        data={
                            'type': 'medication_reminder',
                            'medication_name': medication_name,
                            'dosage': dosage,
                            'time': time,
                            'medication_id': medication_id
                        }
                    )
                    update_notification_log(
                        log, 'fcm', 
                        result.get('success', False),
                        provider_id=result.get('message_id'),
                        error_code=result.get('error_code'),
                        error_message=result.get('error_message')
                    )
                
                elif channel == 'email':
                    template_data = {
                        'user_name': user.first_name or user.username,
                        'medication_name': medication_name,
                        'dosage': dosage,
                        'time': time,
                        'app_url': settings.FRONTEND_URL
                    }
                    success = email_service.send_medication_reminder(
                        to_email=user.email,
                        subject=title,
                        template_data=template_data
                    )
                    update_notification_log(log, 'email', success)
                
                elif channel == 'sms':
                    if hasattr(user, 'profile') and user.profile.phone_number:
                        sms_message = f"MediRemind: Time to take your {medication_name} ({dosage}) at {time}. Reply TAKEN when completed."
                        success = sms_service.send_sms(
                            phone_number=user.profile.phone_number,
                            message=sms_message
                        )
                        update_notification_log(log, 'sms', success)
                
                elif channel == 'web_push':
                    subscriptions = PushSubscription.objects.filter(user_id=user.id)
                    if subscriptions.exists():
                        notification_data = {
                            'title': title,
                            'body': message,
                            'icon': '/static/icons/medication-icon.png',
                            'data': {
                                'type': 'medication_reminder',
                                'medication_name': medication_name,
                                'dosage': dosage,
                                'time': time,
                                'url': '/medications'
                            }
                        }
                        success_count = 0
                        for subscription in subscriptions:
                            try:
                                push_handler.send_notification(
                                    subscription.endpoint,
                                    subscription.p256dh,
                                    subscription.auth,
                                    notification_data
                                )
                                success_count += 1
                            except Exception as e:
                                logger.error(f"Web push failed for subscription {subscription.id}: {e}")
                        
                        update_notification_log(log, 'web_push', success_count > 0)
            
            except Exception as e:
                logger.error(f"Channel {channel} failed for medication reminder: {e}")
                update_notification_log(
                    log, channel, False,
                    error_message=str(e)
                )
        
        return {"status": "completed", "log_id": log.id}
        
    except Exception as exc:
        logger.error(f"Medication reminder task failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_appointment_reminder_task(
    self,
    user_id: int,
    appointment_details: Dict[str, Any],
    reminder_time: str,
    channels: List[str] = None,
    appointment_id: int = None
):
    """
    Celery task for sending appointment reminders.
    """
    try:
        user = User.objects.get(id=user_id)
        if channels is None:
            channels = ['fcm', 'email']
        
        title = f"Appointment Reminder"
        message = f"You have an appointment with {appointment_details.get('doctor_name', 'your doctor')} at {reminder_time}"
        
        # Create initial log entry
        log = create_notification_log(
            user=user,
            notification_type='appointment_reminder',
            title=title,
            message=message,
            channels=channels,
            appointment_id=appointment_id
        )
        
        # Initialize services
        fcm_service = FCMService()
        email_service = EmailService()
        sms_service = SMSService()
        
        # Send through each channel
        for channel in channels:
            try:
                if channel == 'fcm':
                    result = fcm_service.send_to_user(
                        user_id=user.id,
                        title=title,
                        body=message,
                        data={
                            'type': 'appointment_reminder',
                            'appointment_id': appointment_id,
                            'doctor_name': appointment_details.get('doctor_name'),
                            'appointment_time': reminder_time,
                            'location': appointment_details.get('location')
                        }
                    )
                    update_notification_log(
                        log, 'fcm',
                        result.get('success', False),
                        provider_id=result.get('message_id'),
                        error_code=result.get('error_code'),
                        error_message=result.get('error_message')
                    )
                
                elif channel == 'email':
                    success = email_service.send_appointment_confirmation_email(
                        to_email=user.email,
                        appointment_details=appointment_details
                    )
                    update_notification_log(log, 'email', success)
                
                elif channel == 'sms':
                    if hasattr(user, 'profile') and user.profile.phone_number:
                        sms_message = f"Appointment reminder: {appointment_details.get('doctor_name')} at {reminder_time}. Location: {appointment_details.get('location', 'TBD')}"
                        success = sms_service.send_sms(
                            phone_number=user.profile.phone_number,
                            message=sms_message
                        )
                        update_notification_log(log, 'sms', success)
            
            except Exception as e:
                logger.error(f"Channel {channel} failed for appointment reminder: {e}")
                update_notification_log(
                    log, channel, False,
                    error_message=str(e)
                )
        
        return {"status": "completed", "log_id": log.id}
        
    except Exception as exc:
        logger.error(f"Appointment reminder task failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_emergency_alert_task(
    self,
    user_id: int,
    alert_message: str,
    severity: str = 'high',
    channels: List[str] = None
):
    """
    Celery task for sending emergency alerts with high priority.
    """
    try:
        user = User.objects.get(id=user_id)
        if channels is None:
            channels = ['fcm', 'sms', 'email']
        
        title = f"Emergency Alert"
        
        # Create initial log entry
        log = create_notification_log(
            user=user,
            notification_type='emergency_alert',
            title=title,
            message=alert_message,
            channels=channels
        )
        
        # Initialize services
        fcm_service = FCMService()
        email_service = EmailService()
        sms_service = SMSService()
        
        # Send through each channel with high priority
        for channel in channels:
            try:
                if channel == 'fcm':
                    result = fcm_service.send_to_user(
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
                    update_notification_log(
                        log, 'fcm',
                        result.get('success', False),
                        provider_id=result.get('message_id'),
                        error_code=result.get('error_code'),
                        error_message=result.get('error_message')
                    )
                
                elif channel == 'email':
                    success = email_service.send_emergency_alert_email(
                        to_email=user.email,
                        alert_message=alert_message,
                        severity=severity
                    )
                    update_notification_log(log, 'email', success)
                
                elif channel == 'sms':
                    if hasattr(user, 'profile') and user.profile.phone_number:
                        sms_message = f"EMERGENCY: {alert_message}"
                        success = sms_service.send_sms(
                            phone_number=user.profile.phone_number,
                            message=sms_message
                        )
                        update_notification_log(log, 'sms', success)
            
            except Exception as e:
                logger.error(f"Channel {channel} failed for emergency alert: {e}")
                update_notification_log(
                    log, channel, False,
                    error_message=str(e)
                )
        
        return {"status": "completed", "log_id": log.id}
        
    except Exception as exc:
        logger.error(f"Emergency alert task failed: {exc}")
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))


@shared_task
def process_pending_reminders():
    """
    Periodic task to process pending medication and appointment reminders.
    Replaces time.sleep-based scheduling with proper Celery beat.
    """
    from .persistent_scheduler import PersistentNotificationScheduler
    
    try:
        scheduler = PersistentNotificationScheduler()
        stats = scheduler.get_stats()
        
        # Process pending tasks
        pending_count = scheduler.process_pending_tasks()
        
        logger.info(f"Processed {pending_count} pending reminders. Stats: {stats}")
        
        return {
            "processed_count": pending_count,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to process pending reminders: {e}")
        raise


@shared_task
def cleanup_old_notification_logs():
    """
    Periodic task to cleanup old notification logs (older than 90 days).
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count = NotificationLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old notification logs")
        return {"deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"Failed to cleanup notification logs: {e}")
        raise


@shared_task
def collect_queue_stats():
    """
    Periodic task to collect queue manager statistics and store them in the database.
    Migrates stats collection from internal threads to Celery beat.
    """
    try:
        from .queue_manager import queue_manager
        from supabase_client import admin_client
        
        # Gather status and health
        queue_status = queue_manager.get_queue_status()
        health_status = queue_manager.get_health_status()
        
        stats_data = {
            'timestamp': timezone.now().isoformat(),
            'queue_status': queue_status,
            'health_status': health_status
        }
        
        # Persist stats (compatible with previous storage schema)
        admin_client.table("system_stats").insert({
            'metric_type': 'queue_performance',
            'data': json.dumps(stats_data),
            'recorded_at': timezone.now().isoformat()
        }).execute()
        
        logger.info(f"Collected and stored queue stats: {stats_data}")
        return stats_data
    except Exception as e:
        logger.error(f"Failed to collect queue stats: {e}")
        raise


@shared_task
def monitor_notification_health():
    """
    Periodic task to monitor notification system health.
    Replaces monitoring.py time.sleep-based health checks.
    """
    try:
        from .monitoring import check_scheduler_health
        
        health_status = check_scheduler_health()
        
        # Log health status
        logger.info(f"Notification system health: {health_status}")
        
        # Alert if unhealthy
        if not health_status.get('healthy', True):
            logger.warning(f"Notification system unhealthy: {health_status}")
        
        return health_status
    except Exception as e:
        logger.error(f"Health monitoring failed: {e}")
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_appointment_confirmation_async(
    self,
    appointment_id: int,
    patient_email: str,
    patient_name: str,
    appointment_details: Dict[str, Any]
):
    """
    Async task to send appointment confirmation email using Resend.
    This task runs outside the HTTP request to prevent timeouts.
    """
    try:
        from .email_client import email_client
        
        logger.info(f"Sending appointment confirmation email for appointment {appointment_id}")
        
        # Send email via unified email client
        success, message = email_client.send_appointment_confirmation_email(
            to_email=patient_email,
            patient_name=patient_name,
            appointment_details=appointment_details
        )
        
        if success:
            logger.info(f"Appointment confirmation email sent successfully to {patient_email}, ID: {message}")
            return {
                "status": "success",
                "email_id": message,
                "appointment_id": appointment_id,
                "recipient": patient_email
            }
        else:
            logger.warning(f"Failed to send appointment confirmation email to {patient_email}: {message}")
            # Don't retry on permanent failures (invalid email, etc.)
            if "invalid" in message.lower() or "not found" in message.lower():
                return {
                    "status": "failed_permanent",
                    "error": message,
                    "appointment_id": appointment_id,
                    "recipient": patient_email
                }
            # Retry on temporary failures
            raise Exception(f"Email sending failed: {message}")
            
    except Exception as exc:
        logger.error(f"Appointment confirmation email task failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_appointment_reminder_async(
    self,
    appointment_id: int,
    patient_email: str,
    patient_name: str,
    appointment_details: Dict[str, Any]
):
    """
    Async task to send appointment reminder email using Resend.
    This task runs outside the HTTP request to prevent timeouts.
    """
    try:
        from .email_client import email_client
        
        logger.info(f"Sending appointment reminder email for appointment {appointment_id}")
        
        # Send email via unified email client
        success, message = email_client.send_appointment_reminder_email(
            to_email=patient_email,
            patient_name=patient_name,
            appointment_details=appointment_details
        )
        
        if success:
            logger.info(f"Appointment reminder email sent successfully to {patient_email}, ID: {message}")
            return {
                "status": "success",
                "email_id": message,
                "appointment_id": appointment_id,
                "recipient": patient_email
            }
        else:
            logger.warning(f"Failed to send appointment reminder email to {patient_email}: {message}")
            # Don't retry on permanent failures
            if "invalid" in message.lower() or "not found" in message.lower():
                return {
                    "status": "failed_permanent",
                    "error": message,
                    "appointment_id": appointment_id,
                    "recipient": patient_email
                }
            # Retry on temporary failures
            raise Exception(f"Email sending failed: {message}")
            
    except Exception as exc:
        logger.error(f"Appointment reminder email task failed: {exc}")
        # Retry with exponential backoff (longer delays for reminders)
        raise self.retry(exc=exc, countdown=300 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_medication_reminder_async(
    self,
    medication_id: int,
    patient_email: str,
    patient_name: str,
    medication_name: str,
    dosage: str,
    time: str
):
    """
    Async task to send medication reminder email using Resend.
    This task runs outside the HTTP request to prevent timeouts.
    """
    try:
        from .email_client import email_client
        
        logger.info(f"Sending medication reminder email for patient {patient_id}")
        
        # Send email via unified email client
        success, message = email_client.send_medication_reminder_email(
            to_email=patient_email,
            patient_name=patient_name,
            medication_name=medication_name,
            dosage=dosage,
            time=time,
            medication_id=medication_id
        )
        
        if success:
            logger.info(f"Medication reminder email sent successfully to {patient_email}, ID: {message}")
            return {
                "status": "success",
                "email_id": message,
                "medication_id": medication_id,
                "recipient": patient_email,
                "medication_name": medication_name
            }
        else:
            logger.warning(f"Failed to send medication reminder email to {patient_email}: {message}")
            # Don't retry on permanent failures
            if "invalid" in message.lower() or "not found" in message.lower():
                return {
                    "status": "failed_permanent",
                    "error": message,
                    "medication_id": medication_id,
                    "recipient": patient_email
                }
            # Retry on temporary failures
            raise Exception(f"Email sending failed: {message}")
            
    except Exception as exc:
        logger.error(f"Medication reminder email task failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=300 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_emergency_alert_async(
    self,
    alert_id: str,
    patient_email: str,
    patient_name: str,
    alert_message: str,
    severity: str = 'high'
):
    """
    Async task to send emergency alert email using Resend.
    High priority task with faster retry for critical notifications.
    """
    try:
        from .email_client import email_client
        
        logger.info(f"Sending emergency alert email to {patient_email}, severity: {severity}")
        
        # Send email via unified email client
        success, message = email_client.send_emergency_alert_email(
            to_email=patient_email,
            patient_name=patient_name,
            alert_message=alert_message,
            severity=severity
        )
        
        if success:
            logger.info(f"Emergency alert email sent successfully to {patient_email}, ID: {message}")
            return {
                "status": "success",
                "email_id": message,
                "alert_id": alert_id,
                "recipient": patient_email,
                "severity": severity
            }
        else:
            logger.warning(f"Failed to send emergency alert email to {patient_email}: {message}")
            # Don't retry on permanent failures
            if "invalid" in message.lower() or "not found" in message.lower():
                return {
                    "status": "failed_permanent",
                    "error": message,
                    "alert_id": alert_id,
                    "recipient": patient_email
                }
            # Retry on temporary failures
            raise Exception(f"Email sending failed: {message}")
            
    except Exception as exc:
        logger.error(f"Emergency alert email task failed: {exc}")
        # Retry with faster backoff for emergency alerts
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_appointment_update_async(
    self,
    appointment_id: int,
    patient_email: str,
    patient_name: str,
    appointment_details: Dict[str, Any],
    update_type: str = 'rescheduled'
):
    """
    Async task to send appointment update email (rescheduled/cancelled) using Resend.
    This task runs outside the HTTP request to prevent timeouts.
    """
    try:
        from .email_client import email_client
        
        logger.info(f"Sending appointment update email for appointment {appointment_id}")
        
        # Send email via unified email client
        success, message = email_client.send_appointment_update_email(
            to_email=patient_email,
            patient_name=patient_name,
            appointment_details=appointment_details,
            update_type=update_type
        )
        
        if success:
            logger.info(f"Appointment {update_type} email sent successfully to {patient_email}, ID: {message}")
            return {
                "status": "success",
                "email_id": message,
                "appointment_id": appointment_id,
                "recipient": patient_email,
                "update_type": update_type
            }
        else:
            logger.warning(f"Failed to send appointment {update_type} email to {patient_email}: {message}")
            # Don't retry on permanent failures
            if "invalid" in message.lower() or "not found" in message.lower():
                return {
                    "status": "failed_permanent",
                    "error": message,
                    "appointment_id": appointment_id,
                    "recipient": patient_email
                }
            # Retry on temporary failures
            raise Exception(f"Email sending failed: {message}")
            
    except Exception as exc:
        logger.error(f"Appointment {update_type} email task failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=300 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_welcome_email_async(
    self,
    user_id: int,
    patient_email: str,
    patient_name: str,
    clinic_name: str = "MediRemind"
):
    """
    Async task to send welcome email using Resend.
    This task runs outside the HTTP request to prevent timeouts.
    """
    try:
        from .email_client import email_client
        
        logger.info(f"Sending welcome email to {patient_email}")
        
        # Send email via unified email client
        success, message = email_client.send_welcome_email(
            to_email=patient_email,
            patient_name=patient_name,
            clinic_name=clinic_name
        )
        
        if success:
            logger.info(f"Welcome email sent successfully to {patient_email}, ID: {message}")
            return {
                "status": "success",
                "email_id": message,
                "user_id": user_id,
                "recipient": patient_email,
                "clinic_name": clinic_name
            }
        else:
            logger.warning(f"Failed to send welcome email to {patient_email}: {message}")
            # Don't retry on permanent failures
            if "invalid" in message.lower() or "not found" in message.lower():
                return {
                    "status": "failed_permanent",
                    "error": message,
                    "user_id": user_id,
                    "recipient": patient_email
                }
            # Retry on temporary failures
            raise Exception(f"Email sending failed: {message}")
            
    except Exception as exc:
        logger.error(f"Welcome email task failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=300 * (self.request.retries + 1))