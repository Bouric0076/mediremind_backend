"""
Medication reminder service for scheduling and managing medication notifications.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, time
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from .notification_sender import notification_sender
from .models import ScheduledTask

logger = logging.getLogger(__name__)

class MedicationReminderService:
    """
    Service for managing medication reminders with local notification support.
    """
    
    def __init__(self):
        self.notification_sender = notification_sender
    
    async def schedule_medication_reminder(
        self,
        user: User,
        medication_id: str,
        medication_name: str,
        dosage: str,
        schedule_times: List[str],  # List of times like ["08:00", "14:00", "20:00"]
        start_date: datetime = None,
        end_date: datetime = None,
        days_of_week: List[int] = None,  # [0-6] where 0 is Monday
        channels: List[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule recurring medication reminders.
        
        Args:
            user: User to schedule reminders for
            medication_id: Unique identifier for the medication
            medication_name: Name of the medication
            dosage: Dosage information
            schedule_times: List of times in HH:MM format
            start_date: When to start reminders (default: today)
            end_date: When to stop reminders (optional)
            days_of_week: Which days to send reminders (default: all days)
            channels: Notification channels to use
        
        Returns:
            Dict with scheduling results and reminder IDs
        """
        if start_date is None:
            start_date = timezone.now().date()
        
        if days_of_week is None:
            days_of_week = list(range(7))  # All days
        
        if channels is None:
            channels = ['fcm', 'web_push']
        
        scheduled_reminders = []
        
        try:
            for schedule_time in schedule_times:
                # Parse time
                hour, minute = map(int, schedule_time.split(':'))
                reminder_time = time(hour, minute)
                
                # Create scheduled task for each time
                task = ScheduledTask.objects.create(
                    user_id=user.id,
                    task_type='medication_reminder',
                    delivery_method=','.join(channels),
                    priority='high',
                    status='scheduled',
                    title=f"{medication_name} Reminder",
                    message=f"Time to take your {medication_name} ({dosage})",
                    scheduled_time=timezone.make_aware(
                        datetime.combine(start_date, reminder_time)
                    ),
                    metadata={
                        'medication_id': medication_id,
                        'medication_name': medication_name,
                        'dosage': dosage,
                        'schedule_time': schedule_time,
                        'days_of_week': days_of_week,
                        'channels': channels,
                        'recurring': True,
                        'end_date': end_date.isoformat() if end_date else None
                    }
                )
                
                scheduled_reminders.append({
                    'task_id': task.id,
                    'medication_id': medication_id,
                    'time': schedule_time,
                    'next_reminder': task.scheduled_time
                })
            
            logger.info(f"Scheduled {len(scheduled_reminders)} medication reminders for user {user.id}")
            
            return {
                'success': True,
                'scheduled_reminders': scheduled_reminders,
                'total_reminders': len(scheduled_reminders)
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule medication reminders for user {user.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'scheduled_reminders': scheduled_reminders
            }
    
    async def send_immediate_medication_reminder(
        self,
        user: User,
        medication_name: str,
        dosage: str,
        reminder_type: str = 'scheduled',
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        Send an immediate medication reminder.
        
        Args:
            user: User to send reminder to
            medication_name: Name of the medication
            dosage: Dosage information
            reminder_type: Type of reminder ('scheduled', 'missed', 'overdue')
            channels: Notification channels to use
        
        Returns:
            Dict with success status for each channel
        """
        current_time = timezone.now().strftime('%H:%M')
        
        # Add urgency indicators based on reminder type
        if reminder_type == 'missed':
            title_prefix = "Missed Medication"
            message_prefix = "You missed your"
        elif reminder_type == 'overdue':
            title_prefix = "Overdue Medication"
            message_prefix = "Your medication is overdue:"
        else:
            title_prefix = "Medication Reminder"
            message_prefix = "Time to take your"
        
        return await self.notification_sender.send_medication_reminder(
            user=user,
            medication_name=medication_name,
            dosage=dosage,
            time=current_time,
            channels=channels
        )
    
    async def handle_medication_taken(
        self,
        user: User,
        medication_id: str,
        taken_time: datetime = None
    ) -> Dict[str, Any]:
        """
        Handle when user marks medication as taken.
        
        Args:
            user: User who took the medication
            medication_id: ID of the medication
            taken_time: When the medication was taken (default: now)
        
        Returns:
            Dict with confirmation and next reminder info
        """
        if taken_time is None:
            taken_time = timezone.now()
        
        try:
            # Find the most recent reminder for this medication
            recent_reminder = ScheduledTask.objects.filter(
                user_id=user.id,
                task_type='medication_reminder',
                metadata__medication_id=medication_id,
                scheduled_time__lte=taken_time + timedelta(hours=1)  # Within 1 hour
            ).order_by('-scheduled_time').first()
            
            if recent_reminder:
                # Update the reminder status
                recent_reminder.status = 'completed'
                recent_reminder.completed_time = taken_time
                recent_reminder.metadata['taken_time'] = taken_time.isoformat()
                recent_reminder.save()
            
            # Find next scheduled reminder
            next_reminder = ScheduledTask.objects.filter(
                user_id=user.id,
                task_type='medication_reminder',
                metadata__medication_id=medication_id,
                status='scheduled',
                scheduled_time__gt=taken_time
            ).order_by('scheduled_time').first()
            
            # Send confirmation notification
            confirmation_result = await self.notification_sender.send_system_notification(
                user=user,
                title="Medication Confirmed",
                message=f"Great! You've taken your medication at {taken_time.strftime('%H:%M')}",
                notification_type='medication_confirmation',
                data={
                    'medication_id': medication_id,
                    'taken_time': taken_time.isoformat(),
                    'next_reminder': next_reminder.scheduled_time.isoformat() if next_reminder else None
                },
                channels=['fcm']
            )
            
            return {
                'success': True,
                'taken_time': taken_time.isoformat(),
                'next_reminder': next_reminder.scheduled_time.isoformat() if next_reminder else None,
                'confirmation_sent': confirmation_result.get('fcm', False)
            }
            
        except Exception as e:
            logger.error(f"Failed to handle medication taken for user {user.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def snooze_medication_reminder(
        self,
        user: User,
        medication_id: str,
        snooze_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Snooze a medication reminder.
        
        Args:
            user: User who wants to snooze
            medication_id: ID of the medication
            snooze_minutes: How many minutes to snooze
        
        Returns:
            Dict with snooze confirmation and new reminder time
        """
        try:
            snooze_time = timezone.now() + timedelta(minutes=snooze_minutes)
            
            # Create a new snoozed reminder
            task = ScheduledTask.objects.create(
                user_id=user.id,
                task_type='medication_reminder',
                delivery_method='fcm,web_push',
                priority='high',
                status='scheduled',
                title=f"Snoozed Reminder",
                message=f"Snoozed medication reminder",
                scheduled_time=snooze_time,
                metadata={
                    'medication_id': medication_id,
                    'snoozed': True,
                    'original_time': timezone.now().isoformat(),
                    'snooze_minutes': snooze_minutes
                }
            )
            
            # Send snooze confirmation
            confirmation_result = await self.notification_sender.send_system_notification(
                user=user,
                title="⏰ Reminder Snoozed",
                message=f"Medication reminder snoozed for {snooze_minutes} minutes",
                notification_type='medication_snooze',
                data={
                    'medication_id': medication_id,
                    'snooze_time': snooze_time.isoformat(),
                    'snooze_minutes': snooze_minutes
                },
                channels=['fcm']
            )
            
            return {
                'success': True,
                'snoozed_until': snooze_time.isoformat(),
                'snooze_minutes': snooze_minutes,
                'task_id': task.id,
                'confirmation_sent': confirmation_result.get('fcm', False)
            }
            
        except Exception as e:
            logger.error(f"Failed to snooze medication reminder for user {user.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_upcoming_reminders(
        self,
        user: User,
        hours_ahead: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming medication reminders for a user.
        
        Args:
            user: User to get reminders for
            hours_ahead: How many hours ahead to look
        
        Returns:
            List of upcoming reminders
        """
        try:
            end_time = timezone.now() + timedelta(hours=hours_ahead)
            
            upcoming_tasks = ScheduledTask.objects.filter(
                user_id=user.id,
                task_type='medication_reminder',
                status='scheduled',
                scheduled_time__gte=timezone.now(),
                scheduled_time__lte=end_time
            ).order_by('scheduled_time')
            
            reminders = []
            for task in upcoming_tasks:
                metadata = task.metadata or {}
                reminders.append({
                    'task_id': task.id,
                    'medication_id': metadata.get('medication_id'),
                    'medication_name': metadata.get('medication_name'),
                    'dosage': metadata.get('dosage'),
                    'scheduled_time': task.scheduled_time.isoformat(),
                    'time_until': (task.scheduled_time - timezone.now()).total_seconds() / 60,  # minutes
                    'channels': metadata.get('channels', [])
                })
            
            return reminders
            
        except Exception as e:
            logger.error(f"Failed to get upcoming reminders for user {user.id}: {e}")
            return []
    
    async def cancel_medication_reminders(
        self,
        user: User,
        medication_id: str
    ) -> Dict[str, Any]:
        """
        Cancel all scheduled reminders for a specific medication.
        
        Args:
            user: User to cancel reminders for
            medication_id: ID of the medication
        
        Returns:
            Dict with cancellation results
        """
        try:
            # Find all scheduled reminders for this medication
            scheduled_reminders = ScheduledTask.objects.filter(
                user_id=user.id,
                task_type='medication_reminder',
                metadata__medication_id=medication_id,
                status='scheduled'
            )
            
            cancelled_count = scheduled_reminders.count()
            
            # Update status to cancelled
            scheduled_reminders.update(
                status='cancelled',
                completed_time=timezone.now()
            )
            
            logger.info(f"Cancelled {cancelled_count} medication reminders for user {user.id}, medication {medication_id}")
            
            return {
                'success': True,
                'cancelled_count': cancelled_count
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel medication reminders for user {user.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Singleton instance
medication_reminder_service = MedicationReminderService()