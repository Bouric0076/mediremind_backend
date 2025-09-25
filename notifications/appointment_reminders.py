"""
Enhanced Appointment Reminder System
Handles automated reminders for appointments with multiple notification channels
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from django.utils import timezone
from django.db import models
from appointments.models import Appointment, AppointmentType
from accounts.models import EnhancedPatient, EnhancedStaffProfile
from .utils import (
    send_appointment_reminder,
    send_appointment_confirmation,
    send_appointment_update,
    get_appointment_details
)
from .email_client import email_client
from .textsms_client import textsms_client
from .push_notifications import push_notifications

logger = logging.getLogger(__name__)

class ReminderType(Enum):
    """Types of appointment reminders"""
    CONFIRMATION = "confirmation"
    REMINDER_24H = "reminder_24h"
    REMINDER_2H = "reminder_2h"
    REMINDER_30M = "reminder_30m"
    FOLLOW_UP = "follow_up"
    CANCELLATION = "cancellation"
    RESCHEDULING = "rescheduling"

class NotificationChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WHATSAPP = "whatsapp"

@dataclass
class ReminderConfig:
    """Configuration for appointment reminders"""
    reminder_type: ReminderType
    channels: List[NotificationChannel]
    timing_offset: timedelta  # How long before appointment to send
    is_active: bool = True
    priority: int = 1  # 1=highest, 5=lowest

class AppointmentReminderService:
    """Service for managing appointment reminders"""
    
    def __init__(self):
        self.reminder_configs = self._load_default_configs()
        self.active_reminders = {}
        
    def _load_default_configs(self) -> Dict[ReminderType, ReminderConfig]:
        """Load default reminder configurations"""
        return {
            ReminderType.CONFIRMATION: ReminderConfig(
                reminder_type=ReminderType.CONFIRMATION,
                channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
                timing_offset=timedelta(minutes=0),  # Immediate
                priority=1
            ),
            ReminderType.REMINDER_24H: ReminderConfig(
                reminder_type=ReminderType.REMINDER_24H,
                channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH],
                timing_offset=timedelta(hours=24),
                priority=2
            ),
            ReminderType.REMINDER_2H: ReminderConfig(
                reminder_type=ReminderType.REMINDER_2H,
                channels=[NotificationChannel.SMS, NotificationChannel.PUSH],
                timing_offset=timedelta(hours=2),
                priority=1
            ),
            ReminderType.REMINDER_30M: ReminderConfig(
                reminder_type=ReminderType.REMINDER_30M,
                channels=[NotificationChannel.SMS, NotificationChannel.PUSH],
                timing_offset=timedelta(minutes=30),
                priority=1
            ),
            ReminderType.FOLLOW_UP: ReminderConfig(
                reminder_type=ReminderType.FOLLOW_UP,
                channels=[NotificationChannel.EMAIL],
                timing_offset=timedelta(hours=-24),  # 24 hours after appointment
                priority=3
            )
        }
    
    def schedule_appointment_reminders(self, appointment: Appointment) -> bool:
        """Schedule all reminders for an appointment"""
        try:
            appointment_datetime = datetime.combine(appointment.appointment_date, appointment.start_time)
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime)
            
            # Get patient preferences
            patient_preferences = self._get_patient_notification_preferences(appointment.patient)
            
            scheduled_count = 0
            for reminder_type, config in self.reminder_configs.items():
                if not config.is_active:
                    continue
                    
                # Calculate when to send the reminder
                if reminder_type == ReminderType.CONFIRMATION:
                    send_time = timezone.now()  # Send immediately
                elif reminder_type == ReminderType.FOLLOW_UP:
                    send_time = appointment_datetime - config.timing_offset  # After appointment
                else:
                    send_time = appointment_datetime - config.timing_offset  # Before appointment
                
                # Only schedule future reminders
                if send_time > timezone.now():
                    success = self._schedule_single_reminder(
                        appointment, reminder_type, config, send_time, patient_preferences
                    )
                    if success:
                        scheduled_count += 1
                elif reminder_type == ReminderType.CONFIRMATION:
                    # Send confirmation immediately
                    self._send_immediate_reminder(
                        appointment, reminder_type, config, patient_preferences
                    )
                    scheduled_count += 1
            
            logger.info(f"Scheduled {scheduled_count} reminders for appointment {appointment.id}")
            return scheduled_count > 0
            
        except Exception as e:
            logger.error(f"Error scheduling reminders for appointment {appointment.id}: {str(e)}")
            return False
    
    def _schedule_single_reminder(
        self, 
        appointment: Appointment, 
        reminder_type: ReminderType, 
        config: ReminderConfig, 
        send_time: datetime,
        patient_preferences: Dict
    ) -> bool:
        """Schedule a single reminder"""
        try:
            # Filter channels based on patient preferences
            active_channels = self._filter_channels_by_preferences(
                config.channels, patient_preferences
            )
            
            if not active_channels:
                logger.warning(f"No active channels for reminder {reminder_type} for appointment {appointment.id}")
                return False
            
            reminder_data = {
                'appointment_id': str(appointment.id),
                'reminder_type': reminder_type.value,
                'channels': [channel.value for channel in active_channels],
                'send_time': send_time.isoformat(),
                'patient_id': str(appointment.patient.id),
                'provider_id': str(appointment.provider.id),
                'appointment_data': self._prepare_appointment_data(appointment)
            }
            
            # Store in database or queue system
            # For now, we'll use a simple in-memory storage
            reminder_id = f"{appointment.id}_{reminder_type.value}_{send_time.timestamp()}"
            self.active_reminders[reminder_id] = reminder_data
            
            logger.info(f"Scheduled reminder {reminder_type.value} for appointment {appointment.id} at {send_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling single reminder: {str(e)}")
            return False
    
    def _send_immediate_reminder(
        self, 
        appointment: Appointment, 
        reminder_type: ReminderType, 
        config: ReminderConfig,
        patient_preferences: Dict
    ):
        """Send a reminder immediately"""
        try:
            active_channels = self._filter_channels_by_preferences(
                config.channels, patient_preferences
            )
            
            appointment_data = self._prepare_appointment_data(appointment)
            
            # Send to patient
            for channel in active_channels:
                self._send_notification_via_channel(
                    channel, appointment_data, reminder_type, appointment
                )
            
            # Send to emergency contact if enabled
            self._send_emergency_contact_notification(
                appointment, reminder_type, appointment_data
            )
                
        except Exception as e:
            logger.error(f"Error sending immediate reminder: {str(e)}")
    
    def _send_notification_via_channel(
        self, 
        channel: NotificationChannel, 
        appointment_data: Dict, 
        reminder_type: ReminderType,
        appointment: Appointment
    ):
        """Send notification via specific channel"""
        try:
            if channel == NotificationChannel.EMAIL:
                self._send_email_notification(appointment_data, reminder_type, appointment)
            elif channel == NotificationChannel.SMS:
                self._send_sms_notification(appointment_data, reminder_type, appointment)
            elif channel == NotificationChannel.PUSH:
                self._send_push_notification(appointment_data, reminder_type, appointment)
            elif channel == NotificationChannel.WHATSAPP:
                self._send_whatsapp_notification(appointment_data, reminder_type, appointment)
                
        except Exception as e:
            logger.error(f"Error sending {channel.value} notification: {str(e)}")
    
    def _send_email_notification(self, appointment_data: Dict, reminder_type: ReminderType, appointment: Appointment):
        """Send email notification"""
        try:
            template_name = self._get_email_template_name(reminder_type)
            subject = self._get_email_subject(reminder_type, appointment_data)
            
            email_client.send_appointment_confirmation_email(
                appointment_data=appointment_data,
                recipient_email=appointment.patient.user.email,
                is_patient=True
            )
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
    
    def _send_sms_notification(self, appointment_data: Dict, reminder_type: ReminderType, appointment: Appointment):
        """Send SMS notification"""
        try:
            message = self._get_sms_message(reminder_type, appointment_data)
            phone_number = getattr(appointment.patient, 'phone', None)
            
            if phone_number:
                success, response_message = textsms_client.send_sms(
                    recipient=phone_number,
                    message=message
                )
                if success:
                    logger.info(f"SMS sent successfully to {phone_number}: {response_message}")
                else:
                    logger.error(f"SMS sending failed to {phone_number}: {response_message}")
            else:
                logger.warning(f"No phone number for patient {appointment.patient.id}")
                
        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
    
    def _send_push_notification(self, appointment_data: Dict, reminder_type: ReminderType, appointment: Appointment):
        """Send push notification"""
        try:
            title = self._get_push_title(reminder_type)
            body = self._get_push_body(reminder_type, appointment_data)
            
            push_notifications.send_to_user(
                user_id=str(appointment.patient.user.id),
                title=title,
                body=body,
                data=appointment_data
            )
            
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
    
    def _send_whatsapp_notification(self, appointment_data: Dict, reminder_type: ReminderType, appointment: Appointment):
        """Send WhatsApp notification - placeholder for future implementation"""
        logger.info(f"WhatsApp notification placeholder - appointment {appointment.id}")
        # TODO: Implement WhatsApp notification logic
        pass
    
    def _send_emergency_contact_notification(
        self, 
        appointment: Appointment, 
        reminder_type: ReminderType, 
        appointment_data: Dict
    ):
        """Send notification to emergency contact if enabled"""
        try:
            patient = appointment.patient
            
            # Check if emergency contact notifications are enabled
            if not getattr(patient, 'notify_emergency_contact', False):
                return
            
            # Check if this reminder type should be sent to emergency contact
            notification_types = getattr(patient, 'emergency_contact_notification_types', [])
            reminder_type_mapping = {
                ReminderType.CONFIRMATION: 'appointment_confirmation',
                ReminderType.REMINDER_24H: 'appointment_reminder',
                ReminderType.REMINDER_2H: 'appointment_reminder',
                ReminderType.REMINDER_30M: 'appointment_reminder',
                ReminderType.CANCELLATION: 'appointment_cancellation',
                ReminderType.RESCHEDULING: 'appointment_rescheduled',
                ReminderType.FOLLOW_UP: 'follow_up'
            }
            
            mapped_type = reminder_type_mapping.get(reminder_type)
            if mapped_type not in notification_types:
                return
            
            # Get emergency contact information
            emergency_contact_name = getattr(patient, 'emergency_contact_name', '')
            emergency_contact_phone = getattr(patient, 'emergency_contact_phone', '')
            emergency_contact_email = getattr(patient, 'emergency_contact_email', '')
            emergency_contact_relationship = getattr(patient, 'emergency_contact_relationship', '')
            
            if not emergency_contact_name:
                logger.warning(f"No emergency contact name for patient {patient.id}")
                return
            
            # Get preferred notification methods
            notification_methods = getattr(patient, 'emergency_contact_notification_methods', ['email', 'sms'])
            
            # Prepare emergency contact appointment data
            emergency_appointment_data = appointment_data.copy()
            emergency_appointment_data.update({
                'emergency_contact_name': emergency_contact_name,
                'emergency_contact_relationship': emergency_contact_relationship,
                'patient_name': f"{patient.user.first_name} {patient.user.last_name}",
                'is_emergency_contact_notification': True
            })
            
            # Send notifications via preferred methods
            if 'email' in notification_methods and emergency_contact_email:
                self._send_emergency_contact_email(
                    emergency_appointment_data, reminder_type, emergency_contact_email
                )
            
            if 'sms' in notification_methods and emergency_contact_phone:
                self._send_emergency_contact_sms(
                    emergency_appointment_data, reminder_type, emergency_contact_phone
                )
            
            logger.info(f"Sent emergency contact notification for appointment {appointment.id} to {emergency_contact_name}")
            
        except Exception as e:
            logger.error(f"Error sending emergency contact notification: {str(e)}")
    
    def _send_emergency_contact_email(
        self, 
        appointment_data: Dict, 
        reminder_type: ReminderType, 
        emergency_contact_email: str
    ):
        """Send email notification to emergency contact"""
        try:
            template_name = f"emergency_contact_{self._get_email_template_name(reminder_type)}"
            subject = f"[Emergency Contact] {self._get_email_subject(reminder_type, appointment_data)}"
            
            email_client.send_appointment_confirmation_email(
                appointment_data=appointment_data,
                recipient_email=emergency_contact_email,
                is_patient=False
            )
            
        except Exception as e:
            logger.error(f"Error sending emergency contact email: {str(e)}")
    
    def _send_emergency_contact_sms(
        self, 
        appointment_data: Dict, 
        reminder_type: ReminderType, 
        emergency_contact_phone: str
    ):
        """Send SMS notification to emergency contact"""
        try:
            message = self._get_emergency_contact_sms_message(reminder_type, appointment_data)
            
            success, response_message = textsms_client.send_sms(
                recipient=emergency_contact_phone,
                message=message
            )
            
            if success:
                logger.info(f"Emergency contact SMS sent successfully to {emergency_contact_phone}: {response_message}")
            else:
                logger.error(f"Emergency contact SMS sending failed to {emergency_contact_phone}: {response_message}")
            
        except Exception as e:
            logger.error(f"Error sending emergency contact SMS: {str(e)}")
    
    def _get_emergency_contact_sms_message(self, reminder_type: ReminderType, appointment_data: Dict) -> str:
        """Get SMS message for emergency contact notifications"""
        patient_name = appointment_data.get('patient_name', 'Patient')
        relationship = appointment_data.get('emergency_contact_relationship', 'Emergency Contact')
        
        messages = {
            ReminderType.CONFIRMATION: f"Hello {appointment_data['emergency_contact_name']}, {patient_name}'s appointment with Dr. {appointment_data['provider_name']} is confirmed for {appointment_data['formatted_datetime']} at {appointment_data['location']}. You are receiving this as their {relationship}.",
            ReminderType.REMINDER_24H: f"Reminder: {patient_name} has an appointment tomorrow at {appointment_data['appointment_time']} with Dr. {appointment_data['provider_name']}. You are receiving this as their {relationship}.",
            ReminderType.REMINDER_2H: f"Reminder: {patient_name}'s appointment with Dr. {appointment_data['provider_name']} is in 2 hours at {appointment_data['appointment_time']}. You are receiving this as their {relationship}.",
            ReminderType.REMINDER_30M: f"Reminder: {patient_name}'s appointment with Dr. {appointment_data['provider_name']} is in 30 minutes at {appointment_data['location']}. You are receiving this as their {relationship}.",
            ReminderType.FOLLOW_UP: f"Follow-up: {patient_name} had an appointment recently. Please check if they need any assistance. You are receiving this as their {relationship}.",
            ReminderType.CANCELLATION: f"Notice: {patient_name}'s appointment on {appointment_data['formatted_datetime']} has been cancelled. You are receiving this as their {relationship}.",
            ReminderType.RESCHEDULING: f"Notice: {patient_name}'s appointment has been rescheduled to {appointment_data['formatted_datetime']} with Dr. {appointment_data['provider_name']}. You are receiving this as their {relationship}."
        }
        return messages.get(reminder_type, f"Appointment notification for {patient_name}")
    
    def send_no_show_alert_to_emergency_contact(self, appointment: Appointment):
        """Send no-show alert to emergency contact"""
        try:
            patient = appointment.patient
            
            # Check if emergency contact notifications are enabled
            if not getattr(patient, 'notify_emergency_contact', False):
                return
            
            # Check if no-show alerts should be sent to emergency contact
            notification_types = getattr(patient, 'emergency_contact_notification_types', [])
            if 'no_show_alert' not in notification_types:
                return
            
            # Get emergency contact information
            emergency_contact_name = getattr(patient, 'emergency_contact_name', '')
            emergency_contact_phone = getattr(patient, 'emergency_contact_phone', '')
            emergency_contact_email = getattr(patient, 'emergency_contact_email', '')
            emergency_contact_relationship = getattr(patient, 'emergency_contact_relationship', '')
            
            if not emergency_contact_name:
                return
            
            # Prepare appointment data
            appointment_data = self._prepare_appointment_data(appointment)
            appointment_data.update({
                'emergency_contact_name': emergency_contact_name,
                'emergency_contact_relationship': emergency_contact_relationship,
                'patient_name': f"{patient.user.first_name} {patient.user.last_name}",
                'is_emergency_contact_notification': True
            })
            
            # Get preferred notification methods
            notification_methods = getattr(patient, 'emergency_contact_notification_methods', ['email', 'sms'])
            
            # Send notifications
            if 'email' in notification_methods and emergency_contact_email:
                email_client.send_appointment_confirmation_email(
                    appointment_data=appointment_data,
                    recipient_email=emergency_contact_email,
                    is_patient=False
                )
            
            if 'sms' in notification_methods and emergency_contact_phone:
                message = f"Alert: {appointment_data['patient_name']} did not attend their appointment on {appointment_data['formatted_datetime']} with Dr. {appointment_data['provider_name']}. You are receiving this as their {emergency_contact_relationship}. Please check on them."
                beem_client.send_sms(
                    recipient=emergency_contact_phone,
                    message=message
                )
            
            logger.info(f"Sent no-show alert to emergency contact for appointment {appointment.id}")
            
        except Exception as e:
            logger.error(f"Error sending no-show alert to emergency contact: {str(e)}")
    
    def _get_patient_notification_preferences(self, patient: EnhancedPatient) -> Dict:
        """Get patient's notification preferences"""
        # Default preferences if not set
        default_preferences = {
            'email': True,
            'sms': True,
            'push': True,
            'whatsapp': False
        }
        
        # Try to get from patient profile
        try:
            if hasattr(patient, 'notification_preferences'):
                return patient.notification_preferences
        except:
            pass
            
        return default_preferences
    
    def _filter_channels_by_preferences(
        self, 
        channels: List[NotificationChannel], 
        preferences: Dict
    ) -> List[NotificationChannel]:
        """Filter channels based on patient preferences"""
        active_channels = []
        
        for channel in channels:
            if preferences.get(channel.value, True):  # Default to True if not specified
                active_channels.append(channel)
                
        return active_channels
    
    def _prepare_appointment_data(self, appointment: Appointment) -> Dict:
        """Prepare appointment data for notifications"""
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
        
        return {
            'appointment_id': str(appointment.id),
            'patient_name': f"{appointment.patient.user.first_name} {appointment.patient.user.last_name}",
            'doctor_name': f"{appointment.provider.user.first_name} {appointment.provider.user.last_name}",
            'provider_name': f"{appointment.provider.user.first_name} {appointment.provider.user.last_name}",  # Keep for backward compatibility
            'appointment_date': appointment.appointment_date.strftime('%Y-%m-%d'),
            'appointment_time': appointment.start_time.strftime('%H:%M'),
            'appointment_type': appointment.appointment_type.name,
            'duration': appointment.duration,
            'location': location,
            'notes': appointment.notes or '',
            'status': appointment.status,
            'formatted_datetime': f"{appointment.appointment_date.strftime('%A, %B %d, %Y')} at {appointment.start_time.strftime('%I:%M %p')}"
        }
    
    def _get_email_template_name(self, reminder_type: ReminderType) -> str:
        """Get email template name for reminder type"""
        template_map = {
            ReminderType.CONFIRMATION: 'appointment_confirmation',
            ReminderType.REMINDER_24H: 'appointment_reminder_24h',
            ReminderType.REMINDER_2H: 'appointment_reminder_2h',
            ReminderType.REMINDER_30M: 'appointment_reminder_30m',
            ReminderType.FOLLOW_UP: 'appointment_follow_up',
            ReminderType.CANCELLATION: 'appointment_cancellation',
            ReminderType.RESCHEDULING: 'appointment_rescheduling'
        }
        return template_map.get(reminder_type, 'appointment_reminder')
    
    def _get_email_subject(self, reminder_type: ReminderType, appointment_data: Dict) -> str:
        """Get email subject for reminder type"""
        subject_map = {
            ReminderType.CONFIRMATION: f"Appointment Confirmed - {appointment_data['formatted_datetime']}",
            ReminderType.REMINDER_24H: f"Appointment Reminder - Tomorrow at {appointment_data['appointment_time']}",
            ReminderType.REMINDER_2H: f"Appointment Reminder - In 2 Hours",
            ReminderType.REMINDER_30M: f"Appointment Reminder - In 30 Minutes",
            ReminderType.FOLLOW_UP: f"Follow-up: Your Recent Appointment",
            ReminderType.CANCELLATION: f"Appointment Cancelled - {appointment_data['formatted_datetime']}",
            ReminderType.RESCHEDULING: f"Appointment Rescheduled - New Time: {appointment_data['formatted_datetime']}"
        }
        return subject_map.get(reminder_type, "Appointment Notification")
    
    def _get_sms_message(self, reminder_type: ReminderType, appointment_data: Dict) -> str:
        """Get SMS message for reminder type"""
        messages = {
            ReminderType.CONFIRMATION: f"Appointment confirmed with Dr. {appointment_data['provider_name']} on {appointment_data['formatted_datetime']} at {appointment_data['location']}",
            ReminderType.REMINDER_24H: f"Reminder: You have an appointment tomorrow at {appointment_data['appointment_time']} with Dr. {appointment_data['provider_name']}",
            ReminderType.REMINDER_2H: f"Reminder: Your appointment with Dr. {appointment_data['provider_name']} is in 2 hours at {appointment_data['appointment_time']}",
            ReminderType.REMINDER_30M: f"Reminder: Your appointment with Dr. {appointment_data['provider_name']} is in 30 minutes at {appointment_data['location']}",
            ReminderType.FOLLOW_UP: f"Thank you for your recent appointment. Please contact us if you have any questions.",
            ReminderType.CANCELLATION: f"Your appointment on {appointment_data['formatted_datetime']} has been cancelled. Please contact us to reschedule.",
            ReminderType.RESCHEDULING: f"Your appointment has been rescheduled to {appointment_data['formatted_datetime']} with Dr. {appointment_data['provider_name']}"
        }
        return messages.get(reminder_type, "Appointment notification")
    
    def _get_push_title(self, reminder_type: ReminderType) -> str:
        """Get push notification title"""
        titles = {
            ReminderType.CONFIRMATION: "Appointment Confirmed",
            ReminderType.REMINDER_24H: "Appointment Tomorrow",
            ReminderType.REMINDER_2H: "Appointment in 2 Hours",
            ReminderType.REMINDER_30M: "Appointment in 30 Minutes",
            ReminderType.FOLLOW_UP: "Appointment Follow-up",
            ReminderType.CANCELLATION: "Appointment Cancelled",
            ReminderType.RESCHEDULING: "Appointment Rescheduled"
        }
        return titles.get(reminder_type, "Appointment Notification")
    
    def _get_push_body(self, reminder_type: ReminderType, appointment_data: Dict) -> str:
        """Get push notification body"""
        bodies = {
            ReminderType.CONFIRMATION: f"Your appointment with Dr. {appointment_data['provider_name']} is confirmed for {appointment_data['formatted_datetime']}",
            ReminderType.REMINDER_24H: f"Don't forget your appointment tomorrow at {appointment_data['appointment_time']}",
            ReminderType.REMINDER_2H: f"Your appointment with Dr. {appointment_data['provider_name']} is in 2 hours",
            ReminderType.REMINDER_30M: f"Your appointment is starting soon at {appointment_data['location']}",
            ReminderType.FOLLOW_UP: "How was your recent appointment? We'd love your feedback.",
            ReminderType.CANCELLATION: f"Your appointment on {appointment_data['formatted_datetime']} has been cancelled",
            ReminderType.RESCHEDULING: f"New appointment time: {appointment_data['formatted_datetime']}"
        }
        return bodies.get(reminder_type, "You have an appointment notification")
    
    def cancel_appointment_reminders(self, appointment_id: str) -> bool:
        """Cancel all reminders for an appointment"""
        try:
            cancelled_count = 0
            reminders_to_remove = []
            
            for reminder_id, reminder_data in self.active_reminders.items():
                if reminder_data['appointment_id'] == appointment_id:
                    reminders_to_remove.append(reminder_id)
                    cancelled_count += 1
            
            for reminder_id in reminders_to_remove:
                del self.active_reminders[reminder_id]
            
            logger.info(f"Cancelled {cancelled_count} reminders for appointment {appointment_id}")
            return cancelled_count > 0
            
        except Exception as e:
            logger.error(f"Error cancelling reminders for appointment {appointment_id}: {str(e)}")
            return False
    
    def process_pending_reminders(self):
        """Process all pending reminders that are due"""
        try:
            current_time = timezone.now()
            processed_count = 0
            
            reminders_to_process = []
            for reminder_id, reminder_data in self.active_reminders.items():
                send_time = datetime.fromisoformat(reminder_data['send_time'])
                if timezone.make_aware(send_time) <= current_time:
                    reminders_to_process.append((reminder_id, reminder_data))
            
            for reminder_id, reminder_data in reminders_to_process:
                try:
                    # Get appointment
                    appointment = Appointment.objects.get(id=reminder_data['appointment_id'])
                    reminder_type = ReminderType(reminder_data['reminder_type'])
                    
                    # Send notifications via all specified channels
                    for channel_name in reminder_data['channels']:
                        channel = NotificationChannel(channel_name)
                        self._send_notification_via_channel(
                            channel, reminder_data['appointment_data'], reminder_type, appointment
                        )
                    
                    # Send to emergency contact if enabled
                    self._send_emergency_contact_notification(
                        appointment, reminder_type, reminder_data['appointment_data']
                    )
                    
                    # Remove from active reminders
                    del self.active_reminders[reminder_id]
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing reminder {reminder_id}: {str(e)}")
            
            if processed_count > 0:
                logger.info(f"Processed {processed_count} appointment reminders")
                
        except Exception as e:
            logger.error(f"Error processing pending reminders: {str(e)}")

# Global instance
appointment_reminder_service = AppointmentReminderService()