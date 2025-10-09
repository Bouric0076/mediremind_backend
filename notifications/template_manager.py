"""Template Management System for Enhanced Email Templates

This module provides advanced template management capabilities including:
- Dynamic content personalization
- Template variable management
- A/B testing support
- Template performance tracking
- Accessibility compliance
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from .interactive_email import (
    InteractiveEmailService,
    RealTimeStatusService,
    create_interactive_email_context,
    CalendarEvent
)

logger = logging.getLogger(__name__)

class TemplateType(Enum):
    """Email template types"""
    # Existing appointment templates
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    APPOINTMENT_RESCHEDULE = "appointment_reschedule"
    APPOINTMENT_CANCELLATION = "appointment_cancellation"
    APPOINTMENT_REMINDER = "appointment_reminder"
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    
    # Patient Journey Templates
    WELCOME_SERIES = "welcome_series"
    PRE_APPOINTMENT_PREP = "pre_appointment_prep"
    POST_APPOINTMENT_FOLLOWUP = "post_appointment_followup"
    HEALTH_EDUCATION = "health_education"
    MEDICATION_REMINDER = "medication_reminder"
    
    # Provider Communication Templates
    DAILY_SCHEDULE_DIGEST = "daily_schedule_digest"
    PATIENT_NO_SHOW_ALERT = "patient_no_show_alert"
    URGENT_APPOINTMENT_REQUEST = "urgent_appointment_request"
    STAFF_SCHEDULE_CHANGE = "staff_schedule_change"
    
    # Administrative Templates
    INSURANCE_VERIFICATION = "insurance_verification"
    BILLING_REMINDER = "billing_reminder"
    SURVEY_REQUEST = "survey_request"
    EMERGENCY_NOTIFICATION = "emergency_notification"

class RecipientType(Enum):
    """Recipient types for templates"""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

@dataclass
class TemplateContext:
    """Enhanced template context with personalization data"""
    recipient_name: str
    recipient_email: str
    recipient_type: RecipientType
    appointment: Dict[str, Any] = field(default_factory=dict)
    personalization: Dict[str, Any] = field(default_factory=dict)
    links: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TemplateVariant:
    """A/B testing template variant"""
    name: str
    template_path: str
    weight: float = 1.0
    active: bool = True
    performance_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class TemplateConfig:
    """Template configuration and metadata"""
    template_type: TemplateType
    recipient_type: RecipientType
    subject_template: str
    variants: List[TemplateVariant] = field(default_factory=list)
    default_context: Dict[str, Any] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)
    accessibility_features: Dict[str, bool] = field(default_factory=dict)
    performance_tracking: bool = True

class TemplateManager:
    """Advanced template management system"""
    
    def __init__(self):
        self.template_configs = self._load_template_configs()
        self.performance_data = {}
        
        # Initialize interactive email services
        self.interactive_service = InteractiveEmailService(
            base_url=getattr(settings, 'BASE_URL', os.getenv('BASE_URL', 'https://api.mediremind.com')),
            secret_key=getattr(settings, 'INTERACTIVE_EMAIL_SECRET_KEY', 'default-secret-key')
        )
        self.status_service = RealTimeStatusService(
            redis_client=getattr(settings, 'REDIS_CLIENT', None)
        )
        
    def _load_template_configs(self) -> Dict[str, TemplateConfig]:
        """Load template configurations"""
        configs = {
            "appointment_confirmation_patient": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_CONFIRMATION,
                recipient_type=RecipientType.PATIENT,
                subject_template="✅ Appointment Confirmed - {{ appointment.date }} with {{ appointment.doctor_name }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/appointment_confirmation_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "appointment.doctor_name", "appointment.date", "appointment.time"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "appointment_confirmation_doctor": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_CONFIRMATION,
                recipient_type=RecipientType.DOCTOR,
                subject_template="✅ Appointment Confirmed - {{ appointment.date }} with {{ appointment.patient_name }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/appointment_confirmation_doctor.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "appointment.patient_name", "appointment.date", "appointment.time"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "appointment_reschedule_patient": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_RESCHEDULE,
                recipient_type=RecipientType.PATIENT,
                subject_template="🔄 Appointment Rescheduled - New time: {{ appointment.date }} at {{ appointment.time }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/appointment_reschedule_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "appointment.doctor_name", "appointment.date", "appointment.time"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "appointment_cancellation_patient": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_CANCELLATION,
                recipient_type=RecipientType.PATIENT,
                subject_template="❌ Appointment Cancelled - {{ appointment.date }} with {{ appointment.doctor_name }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/appointment_cancellation_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "appointment.doctor_name", "appointment.date", "appointment.time"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "appointment_cancellation_doctor": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_CANCELLATION,
                recipient_type=RecipientType.DOCTOR,
                subject_template="❌ Appointment Cancelled - {{ appointment.date }} with {{ appointment.patient_name }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/appointment_cancellation_doctor.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "appointment.patient_name", "appointment.date", "appointment.time"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            
            # Patient Journey Templates
            "welcome_series_patient": TemplateConfig(
                template_type=TemplateType.WELCOME_SERIES,
                recipient_type=RecipientType.PATIENT,
                subject_template="🎉 Welcome to {{ clinic_name }} - Your Health Journey Starts Here!",
                variants=[
                    TemplateVariant(
                        name="onboarding_v1",
                        template_path="notifications/email/welcome_series_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "clinic_name"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "pre_appointment_prep_patient": TemplateConfig(
                template_type=TemplateType.PRE_APPOINTMENT_PREP,
                recipient_type=RecipientType.PATIENT,
                subject_template="📋 Prepare for Your Appointment - {{ appointment.date }} with {{ appointment.doctor_name }}",
                variants=[
                    TemplateVariant(
                        name="preparation_v1",
                        template_path="notifications/email/pre_appointment_prep_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "appointment.doctor_name", "appointment.date", "appointment.type"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "post_appointment_followup_patient": TemplateConfig(
                template_type=TemplateType.POST_APPOINTMENT_FOLLOWUP,
                recipient_type=RecipientType.PATIENT,
                subject_template="💊 Follow-up Care Instructions from {{ appointment.doctor_name }}",
                variants=[
                    TemplateVariant(
                        name="followup_v1",
                        template_path="notifications/email/post_appointment_followup_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "appointment.doctor_name", "care_instructions"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "health_education_patient": TemplateConfig(
                template_type=TemplateType.HEALTH_EDUCATION,
                recipient_type=RecipientType.PATIENT,
                subject_template="📚 Health Education: {{ education_topic }}",
                variants=[
                    TemplateVariant(
                        name="education_v1",
                        template_path="notifications/email/health_education_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "education_topic", "education_content"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "medication_reminder_patient": TemplateConfig(
                template_type=TemplateType.MEDICATION_REMINDER,
                recipient_type=RecipientType.PATIENT,
                subject_template="💊 Medication Reminder: {{ medication.name }}",
                variants=[
                    TemplateVariant(
                        name="medication_v1",
                        template_path="notifications/email/medication_reminder_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "medication.name", "medication.dosage"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            
            # Provider Communication Templates
            "daily_schedule_digest_doctor": TemplateConfig(
                template_type=TemplateType.DAILY_SCHEDULE_DIGEST,
                recipient_type=RecipientType.DOCTOR,
                subject_template="📅 Daily Schedule - {{ schedule_date }}",
                variants=[
                    TemplateVariant(
                        name="digest_v1",
                        template_path="notifications/email/daily_schedule_digest_doctor.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "schedule_date", "appointments"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "patient_no_show_alert_doctor": TemplateConfig(
                template_type=TemplateType.PATIENT_NO_SHOW_ALERT,
                recipient_type=RecipientType.DOCTOR,
                subject_template="⚠️ Patient No-Show Alert - {{ patient_name }}",
                variants=[
                    TemplateVariant(
                        name="noshow_v1",
                        template_path="notifications/email/patient_no_show_alert_doctor.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "patient_name", "appointment.date", "appointment.time"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "urgent_appointment_request_doctor": TemplateConfig(
                template_type=TemplateType.URGENT_APPOINTMENT_REQUEST,
                recipient_type=RecipientType.DOCTOR,
                subject_template="🚨 Urgent Appointment Request - {{ patient_name }}",
                variants=[
                    TemplateVariant(
                        name="urgent_v1",
                        template_path="notifications/email/urgent_appointment_request_doctor.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "patient_name", "urgency_reason"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "staff_schedule_change_admin": TemplateConfig(
                template_type=TemplateType.STAFF_SCHEDULE_CHANGE,
                recipient_type=RecipientType.ADMIN,
                subject_template="📋 Schedule Change Notification - {{ staff_member }}",
                variants=[
                    TemplateVariant(
                        name="schedule_change_v1",
                        template_path="notifications/email/staff_schedule_change_admin.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "staff_member", "change_details"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            
            # Administrative Templates
            "insurance_verification_patient": TemplateConfig(
                template_type=TemplateType.INSURANCE_VERIFICATION,
                recipient_type=RecipientType.PATIENT,
                subject_template="🏥 Insurance Verification - {{ verification_status }}",
                variants=[
                    TemplateVariant(
                        name="insurance_v1",
                        template_path="notifications/email/insurance_verification_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "verification_status", "insurance_details"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "billing_reminder_patient": TemplateConfig(
                template_type=TemplateType.BILLING_REMINDER,
                recipient_type=RecipientType.PATIENT,
                subject_template="💳 Payment Reminder - {{ amount_due }} Due {{ due_date }}",
                variants=[
                    TemplateVariant(
                        name="billing_v1",
                        template_path="notifications/email/billing_reminder_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "amount_due", "due_date", "payment_link"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "survey_request_patient": TemplateConfig(
                template_type=TemplateType.SURVEY_REQUEST,
                recipient_type=RecipientType.PATIENT,
                subject_template="📝 Your Feedback Matters - Rate Your Recent Visit",
                variants=[
                    TemplateVariant(
                        name="survey_v1",
                        template_path="notifications/email/survey_request_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "survey_link", "appointment.doctor_name"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "emergency_notification_all": TemplateConfig(
                template_type=TemplateType.EMERGENCY_NOTIFICATION,
                recipient_type=RecipientType.PATIENT,  # Can be overridden for different recipients
                subject_template="🚨 Important Notice: {{ emergency_type }}",
                variants=[
                    TemplateVariant(
                        name="emergency_v1",
                        template_path="notifications/email/emergency_notification_all.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "emergency_type", "emergency_message"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            
            # Patient Journey Templates
            "welcome_series_patient": TemplateConfig(
                template_type=TemplateType.WELCOME_SERIES,
                recipient_type=RecipientType.PATIENT,
                subject_template="🎉 Welcome to {{ clinic_name }} - Your Health Journey Starts Here!",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/welcome_series_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "clinic_name"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "pre_appointment_prep_patient": TemplateConfig(
                template_type=TemplateType.PRE_APPOINTMENT_PREP,
                recipient_type=RecipientType.PATIENT,
                subject_template="📋 Prepare for Your Appointment - {{ appointment.date }} with {{ appointment.doctor_name }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/pre_appointment_preparation_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "appointment.doctor_name", "appointment.date"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "post_appointment_followup_patient": TemplateConfig(
                template_type=TemplateType.POST_APPOINTMENT_FOLLOWUP,
                recipient_type=RecipientType.PATIENT,
                subject_template="📝 Follow-up from Your Visit - {{ appointment.date }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/post_appointment_followup_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "appointment.date", "visit_summary"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "health_education_patient": TemplateConfig(
                template_type=TemplateType.HEALTH_EDUCATION,
                recipient_type=RecipientType.PATIENT,
                subject_template="📚 Health Education: {{ education_topic }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/health_education_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "education_topic"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "medication_reminder_patient": TemplateConfig(
                template_type=TemplateType.MEDICATION_REMINDER,
                recipient_type=RecipientType.PATIENT,
                subject_template="💊 Medication Reminder: {{ medication.name }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/medication_reminder_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "medication.name", "medication.dosage"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            
            # Provider Communication Templates
            "daily_schedule_digest_doctor": TemplateConfig(
                template_type=TemplateType.DAILY_SCHEDULE_DIGEST,
                recipient_type=RecipientType.DOCTOR,
                subject_template="📅 Daily Schedule - {{ schedule_date }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/daily_schedule_digest_doctor.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "schedule_date", "appointments"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "patient_no_show_alert_doctor": TemplateConfig(
                template_type=TemplateType.PATIENT_NO_SHOW_ALERT,
                recipient_type=RecipientType.DOCTOR,
                subject_template="⚠️ Patient No-Show Alert - {{ patient_name }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/patient_noshow_alert_doctor.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "patient_name", "appointment_time"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "urgent_appointment_request_doctor": TemplateConfig(
                template_type=TemplateType.URGENT_APPOINTMENT_REQUEST,
                recipient_type=RecipientType.DOCTOR,
                subject_template="🚨 Urgent Appointment Request - {{ patient_name }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/urgent_appointment_request_doctor.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "patient_name", "urgency_level"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "staff_schedule_change_doctor": TemplateConfig(
                template_type=TemplateType.STAFF_SCHEDULE_CHANGE,
                recipient_type=RecipientType.DOCTOR,
                subject_template="📋 Staff Schedule Update - {{ change_date }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/staff_schedule_changes_doctor.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "change_date", "schedule_changes"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            
            # Administrative Templates
            "insurance_verification_patient": TemplateConfig(
                template_type=TemplateType.INSURANCE_VERIFICATION,
                recipient_type=RecipientType.PATIENT,
                subject_template="🏥 Insurance Verification Required - {{ appointment.date }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/insurance_verification_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "appointment.date", "insurance_status"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "billing_reminder_patient": TemplateConfig(
                template_type=TemplateType.BILLING_REMINDER,
                recipient_type=RecipientType.PATIENT,
                subject_template="💳 Payment Reminder - Account Balance: ${{ balance }}",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/billing_reminder_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "balance", "due_date"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "survey_request_patient": TemplateConfig(
                template_type=TemplateType.SURVEY_REQUEST,
                recipient_type=RecipientType.PATIENT,
                subject_template="📊 Your Feedback Matters - Rate Your Recent Visit",
                variants=[
                    TemplateVariant(
                        name="enhanced_v1",
                        template_path="notifications/email/survey_request_patient.html",
                        weight=1.0
                    )
                ],
                required_fields=["recipient_name", "visit_date", "survey_id"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            
            # Emergency Contact Templates
            "emergency_contact_appointment_confirmation": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_CONFIRMATION,
                recipient_type=RecipientType.PATIENT,  # Emergency contact as recipient
                subject_template="📅 Appointment Confirmed for {{ patient_name }} - {{ appointment.date }} at {{ appointment.time }}",
                variants=[
                    TemplateVariant(
                        name="emergency_contact_v1",
                        template_path="notifications/email/emergency_contact_appointment_confirmation.html",
                        weight=1.0
                    )
                ],
                required_fields=["emergency_contact_name", "patient_name", "appointment.date", "appointment.time", "appointment.doctor_name", "emergency_contact_relationship"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "emergency_contact_appointment_reminder": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_REMINDER,
                recipient_type=RecipientType.PATIENT,  # Emergency contact as recipient
                subject_template="⏰ Reminder: {{ patient_name }}'s Appointment Tomorrow - {{ appointment.date }} at {{ appointment.time }}",
                variants=[
                    TemplateVariant(
                        name="emergency_contact_v1",
                        template_path="notifications/email/emergency_contact_appointment_reminder.html",
                        weight=1.0
                    )
                ],
                required_fields=["emergency_contact_name", "patient_name", "appointment.date", "appointment.time", "appointment.doctor_name", "emergency_contact_relationship"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "emergency_contact_appointment_reminder_24h": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_REMINDER,
                recipient_type=RecipientType.PATIENT,  # Emergency contact as recipient
                subject_template="⏰ 24hr Reminder: {{ patient_name }}'s Appointment Tomorrow - {{ appointment.date }} at {{ appointment.time }}",
                variants=[
                    TemplateVariant(
                        name="emergency_contact_v1",
                        template_path="notifications/email/emergency_contact_appointment_reminder.html",
                        weight=1.0
                    )
                ],
                required_fields=["emergency_contact_name", "patient_name", "appointment.date", "appointment.time", "appointment.doctor_name", "emergency_contact_relationship"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "emergency_contact_appointment_reminder_2h": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_REMINDER,
                recipient_type=RecipientType.PATIENT,  # Emergency contact as recipient
                subject_template="⏰ 2hr Reminder: {{ patient_name }}'s Appointment Today - {{ appointment.time }}",
                variants=[
                    TemplateVariant(
                        name="emergency_contact_v1",
                        template_path="notifications/email/emergency_contact_appointment_reminder.html",
                        weight=1.0
                    )
                ],
                required_fields=["emergency_contact_name", "patient_name", "appointment.date", "appointment.time", "appointment.doctor_name", "emergency_contact_relationship"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "emergency_contact_appointment_reminder_30m": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_REMINDER,
                recipient_type=RecipientType.PATIENT,  # Emergency contact as recipient
                subject_template="⏰ 30min Reminder: {{ patient_name }}'s Appointment Starting Soon - {{ appointment.time }}",
                variants=[
                    TemplateVariant(
                        name="emergency_contact_v1",
                        template_path="notifications/email/emergency_contact_appointment_reminder.html",
                        weight=1.0
                    )
                ],
                required_fields=["emergency_contact_name", "patient_name", "appointment.date", "appointment.time", "appointment.doctor_name", "emergency_contact_relationship"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "emergency_contact_appointment_reschedule": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_RESCHEDULE,
                recipient_type=RecipientType.PATIENT,  # Emergency contact as recipient
                subject_template="🔄 {{ patient_name }}'s Appointment Rescheduled - New time: {{ appointment.date }} at {{ appointment.time }}",
                variants=[
                    TemplateVariant(
                        name="emergency_contact_v1",
                        template_path="notifications/email/emergency_contact_appointment_reschedule.html",
                        weight=1.0
                    )
                ],
                required_fields=["emergency_contact_name", "patient_name", "appointment.date", "appointment.time", "appointment.doctor_name", "emergency_contact_relationship"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "emergency_contact_appointment_cancellation": TemplateConfig(
                template_type=TemplateType.APPOINTMENT_CANCELLATION,
                recipient_type=RecipientType.PATIENT,  # Emergency contact as recipient
                subject_template="❌ {{ patient_name }}'s Appointment Cancelled - {{ appointment.date }} at {{ appointment.time }}",
                variants=[
                    TemplateVariant(
                        name="emergency_contact_v1",
                        template_path="notifications/email/emergency_contact_appointment_cancellation.html",
                        weight=1.0
                    )
                ],
                required_fields=["emergency_contact_name", "patient_name", "appointment.date", "appointment.time", "appointment.doctor_name", "emergency_contact_relationship"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            ),
            "emergency_contact_no_show_alert": TemplateConfig(
                template_type=TemplateType.PATIENT_NO_SHOW_ALERT,
                recipient_type=RecipientType.PATIENT,  # Emergency contact as recipient
                subject_template="⚠️ Alert: {{ patient_name }} Missed Appointment - {{ appointment.date }} at {{ appointment.time }}",
                variants=[
                    TemplateVariant(
                        name="emergency_contact_v1",
                        template_path="notifications/email/emergency_contact_no_show_alert.html",
                        weight=1.0
                    )
                ],
                required_fields=["emergency_contact_name", "patient_name", "appointment.date", "appointment.time", "appointment.doctor_name", "emergency_contact_relationship"],
                accessibility_features={
                    "high_contrast": True,
                    "screen_reader_optimized": True,
                    "alt_text_images": True
                }
            )
        }
        return configs
    
    def get_personalized_context(self, base_context: TemplateContext) -> Dict[str, Any]:
        """Generate personalized template context with interactive features"""
        context = {
            'recipient_name': base_context.recipient_name,
            'appointment': base_context.appointment,
            'support_url': base_context.links.get('support', '#'),
            'portal_url': base_context.links.get('portal', '#'),
            'unsubscribe_url': base_context.links.get('unsubscribe', '#'),
            'privacy_url': base_context.links.get('privacy', '#'),
        }
        
        # Add personalization based on recipient preferences
        if base_context.preferences.get('include_weather', False):
            context['weather_info'] = self._get_weather_info(base_context.appointment.get('location'))
        
        if base_context.preferences.get('include_preparation_tips', True):
            context['preparation_tips'] = self._get_preparation_tips(
                base_context.appointment.get('type', 'general')
            )
        
        # Add calendar integration links
        if base_context.appointment:
            context['appointment']['calendar_link'] = self._generate_calendar_link(
                base_context.appointment
            )
            context['appointment']['reschedule_link'] = self._generate_reschedule_link(
                base_context.appointment.get('id')
            )
            
            # Add comprehensive interactive email features
            interactive_context = create_interactive_email_context(
                service=self.interactive_service,
                template_type='appointment',
                user_id=base_context.recipient_email,
                resource_id=base_context.appointment.get('id', ''),
                **context
            )
            context.update(interactive_context)
            
            # Add legacy interactive features for backward compatibility
            if 'interactive_actions' not in context:
                context['interactive_actions'] = self._generate_interactive_actions(
                    base_context.appointment, base_context.recipient_type
                )
            
            # Add real-time status updates
            if 'status_update_link' not in context:
                context['appointment']['status_update_link'] = self._generate_status_update_link(
                    base_context.appointment.get('id')
                )
        
        # Add accessibility features if needed
        if base_context.preferences.get('high_contrast', False):
            context['accessibility_mode'] = 'high_contrast'
        
        return context
    
    def _get_weather_info(self, location: Optional[str]) -> Dict[str, str]:
        """Get weather information for appointment location"""
        # Placeholder for weather API integration
        return {
            'condition': 'Partly cloudy',
            'temperature': '72°F',
            'recommendation': 'Light jacket recommended'
        }
    
    def _get_preparation_tips(self, appointment_type: str) -> List[str]:
        """Get preparation tips based on appointment type"""
        tips_map = {
            'general': [
                'Bring a list of current medications',
                'Prepare questions you want to ask',
                'Bring your insurance card and ID'
            ],
            'blood_work': [
                'Fast for 12 hours before appointment',
                'Drink plenty of water',
                'Wear comfortable clothing with easy sleeve access'
            ],
            'physical_exam': [
                'Wear comfortable, loose-fitting clothing',
                'Remove jewelry and accessories',
                'Bring a list of any symptoms or concerns'
            ],
            'consultation': [
                'Prepare a list of questions',
                'Bring relevant medical records',
                'Consider bringing a family member for support'
            ]
        }
        return tips_map.get(appointment_type, tips_map['general'])
    
    def _generate_calendar_link(self, appointment: Dict[str, Any]) -> str:
        """Generate calendar link for appointment using interactive email service"""
        try:
            from appointments.datetime_utils import DateTimeValidator
            
            # Parse and validate datetime fields
            start_time = appointment.get('start_time')
            end_time = appointment.get('end_time')
            
            # Handle different datetime formats using the comprehensive validator
            if isinstance(start_time, str):
                start_time = DateTimeValidator.parse_datetime(start_time)
                if not start_time:
                    # Try parsing date and time separately
                    date_str = appointment.get('date') or appointment.get('appointment_date')
                    time_str = appointment.get('time') or appointment.get('appointment_time') or appointment.get('start_time')
                    if date_str and time_str:
                        start_time = DateTimeValidator.create_appointment_datetime(date_str, time_str)
            elif not isinstance(start_time, datetime):
                start_time = DateTimeValidator.parse_datetime(str(start_time)) if start_time else None
            
            if isinstance(end_time, str):
                end_time = DateTimeValidator.parse_datetime(end_time)
            elif not isinstance(end_time, datetime) and end_time:
                end_time = DateTimeValidator.parse_datetime(str(end_time))
            
            # If no end_time, calculate from duration or assume 1 hour
            if not end_time and start_time:
                duration_minutes = appointment.get('duration', 60)
                if isinstance(duration_minutes, str):
                    try:
                        duration_minutes = int(duration_minutes)
                    except ValueError:
                        duration_minutes = 60
                end_time = DateTimeValidator.add_duration_to_datetime(start_time, duration_minutes)
            
            # Skip calendar link generation if we don't have valid times
            if not start_time or not end_time:
                logger.warning(f"Invalid datetime for appointment {appointment.get('id')}: start_time={start_time}, end_time={end_time}")
                return '#'
            
            # Create calendar event object
            calendar_event = CalendarEvent(
                title=f"Appointment with {appointment.get('doctor_name', 'Doctor')}",
                start_time=start_time,
                end_time=end_time,
                description=appointment.get('notes', f"Location: {appointment.get('location', 'TBD')}"),
                location=appointment.get('location', '')
            )
            
            # Use interactive service to generate calendar links
            calendar_links = self.interactive_service.generate_calendar_links(calendar_event)
            # Return Google Calendar link as default
            return calendar_links.get('google', '#')
            
        except Exception as e:
            logger.error(f"Error generating calendar link: {e}")
            return '#'
    
    def _generate_reschedule_link(self, appointment_id: Optional[str]) -> str:
        """Generate reschedule link"""
        if not appointment_id:
            return '#'
        return f"{settings.FRONTEND_URL}/appointments/{appointment_id}/reschedule"
    
    def _generate_interactive_actions(self, appointment: Dict[str, Any], recipient_type: RecipientType) -> Dict[str, str]:
        """Generate interactive email action buttons using the interactive email service"""
        actions = {}
        appointment_id = appointment.get('id', '')
        
        if recipient_type == RecipientType.PATIENT:
            # Use interactive service for appointment actions
            confirm_action = self.interactive_service.create_appointment_action(
                'confirm', appointment.get('patient_id', ''), appointment_id
            )
            reschedule_action = self.interactive_service.create_appointment_action(
                'reschedule', appointment.get('patient_id', ''), appointment_id
            )
            cancel_action = self.interactive_service.create_appointment_action(
                'cancel', appointment.get('patient_id', ''), appointment_id
            )
            
            actions.update({
                'confirm_button': confirm_action.url,
                'reschedule_button': reschedule_action.url,
                'cancel_button': cancel_action.url,
                'add_to_calendar': self._generate_calendar_link(appointment),
                'contact_clinic': f"{settings.FRONTEND_URL}/contact"
            })
        elif recipient_type == RecipientType.DOCTOR:
            actions.update({
                'view_patient': f"{settings.FRONTEND_URL}/patients/{appointment.get('patient_id')}",
                'update_notes': f"{settings.FRONTEND_URL}/appointments/{appointment_id}/notes",
                'reschedule_button': f"{settings.FRONTEND_URL}/appointments/{appointment_id}/reschedule",
                'mark_complete': f"{settings.FRONTEND_URL}/api/appointments/{appointment_id}/complete"
            })
        
        return actions
    
    def _generate_status_update_link(self, appointment_id: Optional[str]) -> str:
        """Generate real-time status update link using the status service"""
        if not appointment_id:
            return '#'
        
        # Use the real-time status service to generate the link
        return self.status_service.generate_status_link(
            resource_type='appointment',
            resource_id=str(appointment_id),
            user_id=''
        )
    
    def _generate_quick_response_options(self, template_type: TemplateType) -> List[Dict[str, str]]:
        """Generate quick response options for different template types"""
        response_options = {
            TemplateType.APPOINTMENT_CONFIRMATION: [
                {'text': 'Confirm Appointment', 'action': 'confirm'},
                {'text': 'Need to Reschedule', 'action': 'reschedule'},
                {'text': 'Cancel Appointment', 'action': 'cancel'}
            ],
            TemplateType.SURVEY_REQUEST: [
                {'text': 'Take Survey Now', 'action': 'survey'},
                {'text': 'Remind Me Later', 'action': 'remind_later'},
                {'text': 'Unsubscribe', 'action': 'unsubscribe'}
            ],
            TemplateType.BILLING_REMINDER: [
                {'text': 'Pay Now', 'action': 'pay'},
                {'text': 'Set Up Payment Plan', 'action': 'payment_plan'},
                {'text': 'Contact Billing', 'action': 'contact_billing'}
            ]
        }
        return response_options.get(template_type, [])
    
    def select_template_variant(self, template_key: str, user_id: Optional[str] = None) -> TemplateVariant:
        """Select template variant for A/B testing"""
        config = self.template_configs.get(template_key)
        if not config or not config.variants:
            raise ValueError(f"No template configuration found for {template_key}")
        
        # For now, return the first active variant
        # In production, implement proper A/B testing logic
        active_variants = [v for v in config.variants if v.active]
        if not active_variants:
            raise ValueError(f"No active variants for template {template_key}")
        
        return active_variants[0]
    
    def render_template(self, template_type_or_key, context_data) -> str:
        """Render email template with flexible input types"""
        try:
            # Handle different input types
            if isinstance(template_type_or_key, TemplateType):
                template_key = self._get_template_key_from_type(template_type_or_key)
            else:
                template_key = template_type_or_key
            
            # Handle context data
            if isinstance(context_data, dict):
                template_context = context_data
            else:
                template_context = self.get_personalized_context(context_data)
            
            config = self.template_configs.get(template_key)
            if not config:
                raise ValueError(f"Template configuration not found: {template_key}")
            
            # Select template variant
            variant = self.select_template_variant(template_key)
            
            # Render subject
            subject = self._render_subject(config.subject_template, template_context)
            
            # Render HTML content
            html_content = render_to_string(variant.template_path, template_context)
            
            # Track template usage
            if config.performance_tracking:
                self._track_template_usage(template_key, variant.name)
            
            return subject, html_content
            
        except Exception as e:
            logger.error(f"Error rendering template {template_type_or_key}: {str(e)}")
            raise
    
    def _get_template_key_from_type(self, template_type: TemplateType) -> str:
        """Convert TemplateType enum to template configuration key"""
        # Map TemplateType enum values to template config keys
        type_to_key_mapping = {
            TemplateType.APPOINTMENT_CONFIRMATION: "appointment_confirmation_patient",
            TemplateType.APPOINTMENT_RESCHEDULE: "appointment_reschedule_patient", 
            TemplateType.APPOINTMENT_CANCELLATION: "appointment_cancellation_patient",
            TemplateType.APPOINTMENT_REMINDER: "appointment_reminder_patient",
            TemplateType.MEDICATION_REMINDER: "medication_reminder_patient",
            TemplateType.BILLING_REMINDER: "billing_reminder_patient",
            TemplateType.WELCOME_SERIES: "welcome_series_patient",
            TemplateType.PRE_APPOINTMENT_PREP: "pre_appointment_prep_patient",
            TemplateType.POST_APPOINTMENT_FOLLOWUP: "post_appointment_followup_patient",
            TemplateType.HEALTH_EDUCATION: "health_education_patient",
            TemplateType.DAILY_SCHEDULE_DIGEST: "daily_schedule_digest_doctor",
            TemplateType.PATIENT_NO_SHOW_ALERT: "patient_no_show_alert_doctor",
            TemplateType.URGENT_APPOINTMENT_REQUEST: "urgent_appointment_request_doctor",
            TemplateType.STAFF_SCHEDULE_CHANGE: "staff_schedule_change_doctor",
            TemplateType.INSURANCE_VERIFICATION: "insurance_verification_admin",
            TemplateType.SURVEY_REQUEST: "survey_request_patient",
            TemplateType.EMERGENCY_NOTIFICATION: "emergency_notification_admin"
        }
        
        template_key = type_to_key_mapping.get(template_type)
        if not template_key:
            raise ValueError(f"No template configuration found for {template_type}")
        
        return template_key
    
    def get_template_config(self, template_key: str) -> TemplateConfig:
        """Get template configuration by key"""
        config = self.template_configs.get(template_key)
        if not config:
            raise ValueError(f"Template configuration not found: {template_key}")
        return config
    
    def _validate_context(self, context: TemplateContext, required_fields: List[str]):
        """Validate that required fields are present in context"""
        for field in required_fields:
            if '.' in field:
                # Handle nested fields like 'appointment.doctor_name'
                parts = field.split('.')
                value = getattr(context, parts[0], {})
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        value = getattr(value, part, None)
                if value is None:
                    raise ValueError(f"Required field missing: {field}")
            else:
                if not hasattr(context, field) or getattr(context, field) is None:
                    raise ValueError(f"Required field missing: {field}")
    
    def _render_subject(self, subject_template: str, context: Dict[str, Any]) -> str:
        """Render email subject line"""
        from django.template import Template, Context
        template = Template(subject_template)
        return template.render(Context(context))
    
    def _track_template_usage(self, template_key: str, variant_name: str):
        """Track template usage for analytics"""
        timestamp = datetime.now().isoformat()
        if template_key not in self.performance_data:
            self.performance_data[template_key] = {}
        
        if variant_name not in self.performance_data[template_key]:
            self.performance_data[template_key][variant_name] = {
                'usage_count': 0,
                'last_used': timestamp
            }
        
        self.performance_data[template_key][variant_name]['usage_count'] += 1
        self.performance_data[template_key][variant_name]['last_used'] = timestamp
    
    def get_template_performance(self, template_key: str) -> Dict[str, Any]:
        """Get performance metrics for a template"""
        return self.performance_data.get(template_key, {})
    
    def create_template_variant(self, template_key: str, variant_name: str, 
                              template_path: str, weight: float = 1.0) -> bool:
        """Create a new template variant for A/B testing"""
        try:
            config = self.template_configs.get(template_key)
            if not config:
                return False
            
            new_variant = TemplateVariant(
                name=variant_name,
                template_path=template_path,
                weight=weight
            )
            
            config.variants.append(new_variant)
            logger.info(f"Created new template variant: {variant_name} for {template_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating template variant: {str(e)}")
            return False
    
    def update_variant_performance(self, template_key: str, variant_name: str, 
                                 metrics: Dict[str, float]):
        """Update performance metrics for a template variant"""
        config = self.template_configs.get(template_key)
        if not config:
            return
        
        for variant in config.variants:
            if variant.name == variant_name:
                variant.performance_metrics.update(metrics)
                break
    
    def render_bulk_templates(self, template_requests: List[Tuple[str, TemplateContext]]) -> List[Tuple[str, str]]:
        """Render multiple templates efficiently for bulk processing"""
        results = []
        
        # Group requests by template type for optimization
        grouped_requests = {}
        for template_key, context in template_requests:
            if template_key not in grouped_requests:
                grouped_requests[template_key] = []
            grouped_requests[template_key].append(context)
        
        # Process each template type in batch
        for template_key, contexts in grouped_requests.items():
            try:
                config = self.template_configs.get(template_key)
                if not config:
                    logger.error(f"Template configuration not found: {template_key}")
                    continue
                
                variant = self.select_template_variant(template_key)
                
                for context in contexts:
                    try:
                        # Validate required fields
                        self._validate_context(context, config.required_fields)
                        
                        # Generate personalized context
                        template_context = self.get_personalized_context(context)
                        
                        # Render subject and content
                        subject = self._render_subject(config.subject_template, template_context)
                        html_content = render_to_string(variant.template_path, template_context)
                        
                        results.append((subject, html_content))
                        
                        # Track usage
                        if config.performance_tracking:
                            self._track_template_usage(template_key, variant.name)
                            
                    except Exception as e:
                        logger.error(f"Error rendering template {template_key}: {str(e)}")
                        results.append(("Error", "Template rendering failed"))
                        
            except Exception as e:
                logger.error(f"Error processing template group {template_key}: {str(e)}")
        
        return results
    
    def get_template_cache_key(self, template_key: str, context_hash: str) -> str:
        """Generate cache key for template caching"""
        return f"template:{template_key}:{context_hash}"
    
    def prioritize_template_queue(self, template_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize template rendering queue based on urgency and recipient preferences"""
        def get_priority_score(request):
            template_type = request.get('template_type')
            recipient_type = request.get('recipient_type')
            urgency = request.get('urgency', 'normal')
            
            # Base priority scores
            urgency_scores = {
                'emergency': 100,
                'urgent': 80,
                'high': 60,
                'normal': 40,
                'low': 20
            }
            
            template_priority = {
                TemplateType.EMERGENCY_NOTIFICATION: 90,
                TemplateType.URGENT_APPOINTMENT_REQUEST: 85,
                TemplateType.PATIENT_NO_SHOW_ALERT: 75,
                TemplateType.APPOINTMENT_CONFIRMATION: 70,
                TemplateType.APPOINTMENT_RESCHEDULE: 65,
                TemplateType.MEDICATION_REMINDER: 60,
                TemplateType.BILLING_REMINDER: 50,
                TemplateType.SURVEY_REQUEST: 30,
                TemplateType.HEALTH_EDUCATION: 25
            }
            
            base_score = urgency_scores.get(urgency, 40)
            template_score = template_priority.get(template_type, 30)
            
            return base_score + template_score
        
        # Sort by priority score (highest first)
        return sorted(template_requests, key=get_priority_score, reverse=True)
    
    def get_template_analytics(self) -> Dict[str, Any]:
        """Get comprehensive template analytics and performance metrics"""
        analytics = {
            'total_templates': len(self.template_configs),
            'template_usage': self.performance_data,
            'popular_templates': [],
            'performance_summary': {}
        }
        
        # Calculate popular templates
        template_usage_counts = {}
        for template_key, variants in self.performance_data.items():
            total_usage = sum(variant.get('usage_count', 0) for variant in variants.values())
            template_usage_counts[template_key] = total_usage
        
        analytics['popular_templates'] = sorted(
            template_usage_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Performance summary
        analytics['performance_summary'] = {
            'total_renders': sum(template_usage_counts.values()),
            'active_templates': len([k for k, v in template_usage_counts.items() if v > 0]),
            'avg_renders_per_template': sum(template_usage_counts.values()) / len(template_usage_counts) if template_usage_counts else 0
        }
        
        return analytics
    
    def setup_cdn_integration(self, cdn_config: Dict[str, Any]) -> None:
        """Setup CDN integration for static assets in templates"""
        self.cdn_config = {
            'enabled': cdn_config.get('enabled', False),
            'base_url': cdn_config.get('base_url', ''),
            'static_path': cdn_config.get('static_path', '/static/'),
            'cache_headers': cdn_config.get('cache_headers', {
                'Cache-Control': 'public, max-age=31536000',
                'Expires': 'Thu, 31 Dec 2037 23:55:55 GMT'
            })
        }
        
        logger.info(f"CDN integration {'enabled' if self.cdn_config['enabled'] else 'disabled'}")
    
    def get_cdn_url(self, asset_path: str) -> str:
        """Get CDN URL for static assets"""
        if not self.cdn_config.get('enabled', False):
            return asset_path
        
        base_url = self.cdn_config['base_url'].rstrip('/')
        static_path = self.cdn_config['static_path'].strip('/')
        clean_asset_path = asset_path.lstrip('/')
        
        return f"{base_url}/{static_path}/{clean_asset_path}"
    
    def preload_critical_templates(self, template_keys: List[str]) -> None:
        """Preload critical templates into cache for faster rendering"""
        logger.info(f"Preloading {len(template_keys)} critical templates")
        
        for template_key in template_keys:
            try:
                config = self.template_configs.get(template_key)
                if config:
                    # Load template into memory
                    template_path = config.variants[0].template_path
                    cache_key = f"preloaded_template:{template_key}"
                    
                    # Cache template for 1 hour
                    cache.set(cache_key, template_path, 3600)
                    logger.debug(f"Preloaded template: {template_key}")
                    
            except Exception as e:
                logger.error(f"Failed to preload template {template_key}: {e}")
    
    def optimize_template_cache(self) -> Dict[str, Any]:
        """Optimize template cache by removing unused entries and updating frequently used ones"""
        optimization_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'entries_removed': 0,
            'entries_optimized': 0
        }
        
        try:
            # Get all template cache keys
            cache_keys = cache.keys('template:*')
            
            for key in cache_keys:
                usage_data = cache.get(f"{key}:usage")
                if usage_data:
                    last_used = usage_data.get('last_used')
                    usage_count = usage_data.get('count', 0)
                    
                    # Remove entries not used in the last 24 hours with low usage
                    if last_used and usage_count < 5:
                        time_diff = timezone.now() - last_used
                        if time_diff.total_seconds() > 86400:  # 24 hours
                            cache.delete(key)
                            cache.delete(f"{key}:usage")
                            optimization_stats['entries_removed'] += 1
                    else:
                        optimization_stats['entries_optimized'] += 1
                else:
                    optimization_stats['cache_misses'] += 1
            
            logger.info(f"Cache optimization completed: {optimization_stats}")
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
        
        return optimization_stats
    
    def get_template_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics for template rendering"""
        metrics = {
            'render_times': {},
            'cache_performance': {},
            'error_rates': {},
            'resource_usage': {}
        }
        
        # Calculate average render times
        for template_key, variants in self.performance_data.items():
            total_time = 0
            total_renders = 0
            
            for variant_name, variant_data in variants.items():
                render_times = variant_data.get('render_times', [])
                if render_times:
                    total_time += sum(render_times)
                    total_renders += len(render_times)
            
            if total_renders > 0:
                metrics['render_times'][template_key] = {
                    'average_ms': (total_time / total_renders) * 1000,
                    'total_renders': total_renders
                }
        
        # Cache performance metrics
        try:
            cache_stats = cache.get('template_cache_stats', {})
            metrics['cache_performance'] = {
                'hit_rate': cache_stats.get('hit_rate', 0),
                'miss_rate': cache_stats.get('miss_rate', 0),
                'total_requests': cache_stats.get('total_requests', 0)
            }
        except Exception:
            metrics['cache_performance'] = {'error': 'Cache stats unavailable'}
        
        return metrics

# Create singleton instance
template_manager = TemplateManager()