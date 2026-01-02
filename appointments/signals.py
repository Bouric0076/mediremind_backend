"""
Django signals for automatic appointment reminder management.
Handles lifecycle events to trigger, update, or cancel reminders.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from .models import Appointment
from notifications.appointment_reminders import AppointmentReminderService
from notifications.scheduler import NotificationScheduler

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Appointment)
def handle_appointment_created_or_updated(sender, instance, created, **kwargs):
    """
    Handle appointment creation and updates to automatically manage reminders.
    
    Args:
        sender: The model class (Appointment)
        instance: The actual appointment instance
        created: Boolean indicating if this is a new appointment
        **kwargs: Additional keyword arguments
    """
    try:
        # Initialize services
        reminder_service = AppointmentReminderService()
        scheduler = NotificationScheduler()
        
        # Add idempotency check to prevent duplicate signal processing
        signal_key = f"appointment_signal_processed:{instance.id}:{created}"
        if cache.get(signal_key):
            logger.warning(f"Signal already processed for appointment {instance.id}, skipping duplicate processing")
            return
        
        # Set signal processing lock (2 minute TTL to prevent race conditions)
        cache.set(signal_key, True, 120)
        
        if created:
            # New appointment created - schedule reminders
            logger.info(f"New appointment created: {instance.id}. Scheduling reminders.")
            
            # Only schedule reminders for future appointments that are scheduled or confirmed
            if instance.is_upcoming and instance.status in ['scheduled', 'confirmed']:
                reminder_service.schedule_appointment_reminders(instance)
                logger.info(f"Reminders scheduled for appointment {instance.id}")
            else:
                logger.info(f"Skipping reminder scheduling for appointment {instance.id} - not upcoming or wrong status")
                
        else:
            # Existing appointment updated - handle status changes
            logger.info(f"Appointment updated: {instance.id}. Checking for status changes.")
            
            # Get the previous state to compare changes
            try:
                # Get the previous instance from database
                previous_instance = Appointment.objects.get(id=instance.id)
                
                # Check if status changed to cancelled, completed, or no_show
                if instance.status in ['cancelled', 'completed', 'no_show'] and previous_instance.status not in ['cancelled', 'completed', 'no_show']:
                    # Cancel all pending reminders for this appointment
                    logger.info(f"Appointment {instance.id} status changed to {instance.status}. Cancelling reminders.")
                    scheduler.cancel_appointment_reminders(instance.id)
                    
                elif instance.status in ['scheduled', 'confirmed'] and previous_instance.status not in ['scheduled', 'confirmed']:
                    # Appointment reactivated - reschedule reminders if upcoming
                    if instance.is_upcoming:
                        logger.info(f"Appointment {instance.id} reactivated. Rescheduling reminders.")
                        reminder_service.schedule_appointment_reminders(instance)
                        
                elif (instance.appointment_date != previous_instance.appointment_date or 
                      instance.start_time != previous_instance.start_time) and instance.status in ['scheduled', 'confirmed']:
                    # Date or time changed - reschedule reminders
                    logger.info(f"Appointment {instance.id} date/time changed. Rescheduling reminders.")
                    scheduler.cancel_appointment_reminders(instance.id)
                    if instance.is_upcoming:
                        reminder_service.schedule_appointment_reminders(instance)
                        
            except Appointment.DoesNotExist:
                # This shouldn't happen in post_save, but handle gracefully
                logger.warning(f"Could not find previous state for appointment {instance.id}")
                
    except Exception as e:
        logger.error(f"Error handling appointment signal for {instance.id}: {str(e)}")


@receiver(pre_save, sender=Appointment)
def store_previous_appointment_state(sender, instance, **kwargs):
    """
    Store the previous state of the appointment before saving.
    This helps us detect changes in post_save signal.
    """
    if instance.pk:  # Only for existing appointments
        try:
            # Store previous state as an attribute on the instance
            previous = Appointment.objects.get(pk=instance.pk)
            instance._previous_status = previous.status
            instance._previous_date = previous.appointment_date
            instance._previous_time = previous.start_time
        except Appointment.DoesNotExist:
            # New appointment, no previous state
            instance._previous_status = None
            instance._previous_date = None
            instance._previous_time = None


def handle_appointment_cancellation(appointment_id):
    """
    Utility function to handle appointment cancellation.
    Can be called directly when cancelling appointments.
    
    Args:
        appointment_id: UUID of the appointment to cancel reminders for
    """
    try:
        scheduler = NotificationScheduler()
        scheduler.cancel_appointment_reminders(appointment_id)
        logger.info(f"Cancelled all reminders for appointment {appointment_id}")
    except Exception as e:
        logger.error(f"Error cancelling reminders for appointment {appointment_id}: {str(e)}")


def handle_appointment_rescheduling(appointment_id, old_datetime, new_datetime):
    """
    Utility function to handle appointment rescheduling.
    
    Args:
        appointment_id: UUID of the appointment
        old_datetime: Previous appointment datetime
        new_datetime: New appointment datetime
    """
    try:
        scheduler = NotificationScheduler()
        reminder_service = AppointmentReminderService()
        
        # Cancel old reminders
        scheduler.cancel_appointment_reminders(appointment_id)
        
        # Schedule new reminders if appointment is in the future
        appointment = Appointment.objects.get(id=appointment_id)
        if appointment.is_upcoming and appointment.status in ['scheduled', 'confirmed']:
            reminder_service.schedule_appointment_reminders(appointment)
            
        logger.info(f"Rescheduled reminders for appointment {appointment_id} from {old_datetime} to {new_datetime}")
        
    except Exception as e:
        logger.error(f"Error rescheduling reminders for appointment {appointment_id}: {str(e)}")