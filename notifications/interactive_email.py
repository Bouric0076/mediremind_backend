from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import uuid
import hashlib
import hmac
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    """Types of interactive email actions"""
    CONFIRM_APPOINTMENT = "confirm_appointment"
    RESCHEDULE_APPOINTMENT = "reschedule_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"
    ADD_TO_CALENDAR = "add_to_calendar"
    MARK_MEDICATION_TAKEN = "mark_medication_taken"
    SNOOZE_REMINDER = "snooze_reminder"
    QUICK_RESPONSE = "quick_response"
    SURVEY_RATING = "survey_rating"
    PAYMENT_LINK = "payment_link"
    UPLOAD_DOCUMENT = "upload_document"
    CALL_PATIENT = "call_patient"
    SEND_MESSAGE = "send_message"
    VIEW_RESULTS = "view_results"
    UPDATE_PREFERENCES = "update_preferences"
    EMERGENCY_CONTACT = "emergency_contact"
    # Additional action types for test compatibility
    APPOINTMENT_CONFIRM = "appointment_confirm"
    APPOINTMENT_RESCHEDULE = "appointment_reschedule"
    APPOINTMENT_CANCEL = "appointment_cancel"
    MEDICATION_TAKEN = "medication_taken"
    MEDICATION_SKIP = "medication_skip"
    MEDICATION_SNOOZE = "medication_snooze"
    SURVEY_START = "survey_start"
    SURVEY_SUBMIT = "survey_submit"
    SURVEY_RATE = "survey_rate"
    BILLING_PAY = "billing_pay"
    BILLING_VIEW = "billing_view"
    BILLING_DISPUTE = "billing_dispute"
    PROVIDER_CALL = "provider_call"
    PROVIDER_MESSAGE = "provider_message"
    PROVIDER_SCHEDULE = "provider_schedule"

class CalendarProvider(Enum):
    """Supported calendar providers"""
    GOOGLE = "google"
    OUTLOOK = "outlook"
    APPLE = "apple"
    YAHOO = "yahoo"
    ICS = "ics"

@dataclass
class InteractiveAction:
    """Represents an interactive email action"""
    action_type: ActionType
    label: str
    url: str
    style: str = "primary"  # primary, secondary, success, warning, danger
    icon: Optional[str] = None
    confirmation_required: bool = False
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class CalendarEvent:
    """Represents a calendar event for integration"""
    title: str
    start_time: datetime
    end_time: datetime
    description: str
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    reminder_minutes: List[int] = None
    timezone: str = "UTC"
    organizer_email: Optional[str] = None
    organizer_name: Optional[str] = None

@dataclass
class QuickResponse:
    """Represents a quick response option"""
    text: str
    value: str
    action_url: str
    style: str = "outline"

class InteractiveEmailService:
    """Service for handling interactive email features"""
    
    def __init__(self, base_url: str, secret_key: str):
        self.base_url = base_url.rstrip('/')
        self.secret_key = secret_key
    
    def generate_action_url(self, 
                           action_type: ActionType, 
                           user_id: str, 
                           resource_id: str, 
                           expires_in_hours: int = 24,
                           **kwargs) -> str:
        """Generate a secure action URL for interactive email actions"""
        
        # Create expiration timestamp
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Create payload
        payload = {
            'action': action_type.value,
            'user_id': user_id,
            'resource_id': resource_id,
            'expires_at': int(expires_at.timestamp()),
            'nonce': str(uuid.uuid4()),
            **kwargs
        }
        
        # Generate signature
        signature = self._generate_signature(payload)
        payload['signature'] = signature
        
        # Build URL
        query_string = urlencode(payload)
        return f"{self.base_url}/api/interactive-email/action?{query_string}"
    
    def generate_calendar_links(self, event: CalendarEvent) -> Dict[str, str]:
        """Generate calendar links for multiple providers"""
        links = {}
        
        # Google Calendar
        google_params = {
            'action': 'TEMPLATE',
            'text': event.title,
            'dates': f"{self._format_google_date(event.start_time)}/{self._format_google_date(event.end_time)}",
            'details': event.description,
            'location': event.location or '',
            'trp': 'false'
        }
        links[CalendarProvider.GOOGLE.value] = f"https://calendar.google.com/calendar/render?{urlencode(google_params)}"
        
        # Outlook Calendar
        outlook_params = {
            'subject': event.title,
            'startdt': event.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'enddt': event.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'body': event.description,
            'location': event.location or ''
        }
        links[CalendarProvider.OUTLOOK.value] = f"https://outlook.live.com/calendar/0/deeplink/compose?{urlencode(outlook_params)}"
        
        # Yahoo Calendar
        yahoo_params = {
            'v': '60',
            'title': event.title,
            'st': event.start_time.strftime('%Y%m%dT%H%M%SZ'),
            'et': event.end_time.strftime('%Y%m%dT%H%M%SZ'),
            'desc': event.description,
            'in_loc': event.location or ''
        }
        links[CalendarProvider.YAHOO.value] = f"https://calendar.yahoo.com/?{urlencode(yahoo_params)}"
        
        # ICS file download
        ics_url = self.generate_action_url(
            ActionType.ADD_TO_CALENDAR,
            'system',
            str(uuid.uuid4()),
            format='ics',
            event_data=self._serialize_event(event)
        )
        links[CalendarProvider.ICS.value] = ics_url
        
        return links
    
    def generate_appointment_actions(self, 
                                   appointment_id: str, 
                                   patient_id: str,
                                   appointment_datetime: datetime) -> List[InteractiveAction]:
        """Generate interactive actions for appointment emails"""
        actions = []
        
        # Confirm appointment
        confirm_url = self.generate_action_url(
            ActionType.CONFIRM_APPOINTMENT,
            patient_id,
            appointment_id
        )
        actions.append(InteractiveAction(
            action_type=ActionType.CONFIRM_APPOINTMENT,
            label="✅ Confirm Appointment",
            url=confirm_url,
            style="success",
            icon="✅"
        ))
        
        # Reschedule appointment (only if more than 24 hours away)
        if appointment_datetime > datetime.utcnow() + timedelta(hours=24):
            reschedule_url = self.generate_action_url(
                ActionType.RESCHEDULE_APPOINTMENT,
                patient_id,
                appointment_id
            )
            actions.append(InteractiveAction(
                action_type=ActionType.RESCHEDULE_APPOINTMENT,
                label="📅 Reschedule",
                url=reschedule_url,
                style="warning",
                icon="📅"
            ))
        
        # Cancel appointment
        cancel_url = self.generate_action_url(
            ActionType.CANCEL_APPOINTMENT,
            patient_id,
            appointment_id
        )
        actions.append(InteractiveAction(
            action_type=ActionType.CANCEL_APPOINTMENT,
            label="❌ Cancel",
            url=cancel_url,
            style="danger",
            icon="❌",
            confirmation_required=True
        ))
        
        return actions
    
    def generate_medication_actions(self, 
                                  medication_id: str, 
                                  patient_id: str) -> List[InteractiveAction]:
        """Generate interactive actions for medication reminders"""
        actions = []
        
        # Mark as taken
        taken_url = self.generate_action_url(
            ActionType.MARK_MEDICATION_TAKEN,
            patient_id,
            medication_id,
            timestamp=datetime.utcnow().isoformat()
        )
        actions.append(InteractiveAction(
            action_type=ActionType.MARK_MEDICATION_TAKEN,
            label="✅ Mark as Taken",
            url=taken_url,
            style="success",
            icon="💊"
        ))
        
        # Snooze reminder
        snooze_url = self.generate_action_url(
            ActionType.SNOOZE_REMINDER,
            patient_id,
            medication_id,
            snooze_minutes=30
        )
        actions.append(InteractiveAction(
            action_type=ActionType.SNOOZE_REMINDER,
            label="⏰ Snooze 30min",
            url=snooze_url,
            style="secondary",
            icon="⏰"
        ))
        
        return actions
    
    def generate_survey_quick_responses(self, 
                                      survey_id: str, 
                                      patient_id: str) -> List[QuickResponse]:
        """Generate quick response options for surveys"""
        responses = []
        
        # Rating responses
        for rating in range(1, 6):
            rating_url = self.generate_action_url(
                ActionType.SURVEY_RATING,
                patient_id,
                survey_id,
                rating=rating,
                question='overall_satisfaction'
            )
            responses.append(QuickResponse(
                text=f"{rating} Star{'s' if rating != 1 else ''}",
                value=str(rating),
                action_url=rating_url,
                style="outline"
            ))
        
        return responses
    
    def generate_billing_actions(self, 
                               invoice_id: str, 
                               patient_id: str,
                               amount: float) -> List[InteractiveAction]:
        """Generate interactive actions for billing emails"""
        actions = []
        
        # Pay now
        payment_url = self.generate_action_url(
            ActionType.PAYMENT_LINK,
            patient_id,
            invoice_id,
            amount=amount,
            expires_in_hours=72
        )
        actions.append(InteractiveAction(
            action_type=ActionType.PAYMENT_LINK,
            label="💳 Pay Now",
            url=payment_url,
            style="primary",
            icon="💳"
        ))
        
        # View invoice
        view_url = self.generate_action_url(
            ActionType.VIEW_RESULTS,
            patient_id,
            invoice_id,
            document_type='invoice'
        )
        actions.append(InteractiveAction(
            action_type=ActionType.VIEW_RESULTS,
            label="📄 View Invoice",
            url=view_url,
            style="secondary",
            icon="📄"
        ))
        
        return actions
    
    def generate_provider_actions(self, 
                                resource_type: str,
                                resource_id: str, 
                                provider_id: str) -> List[InteractiveAction]:
        """Generate interactive actions for provider emails"""
        actions = []
        
        if resource_type == 'patient_noshow':
            # Call patient
            call_url = self.generate_action_url(
                ActionType.CALL_PATIENT,
                provider_id,
                resource_id
            )
            actions.append(InteractiveAction(
                action_type=ActionType.CALL_PATIENT,
                label="📞 Call Patient",
                url=call_url,
                style="primary",
                icon="📞"
            ))
            
            # Send message
            message_url = self.generate_action_url(
                ActionType.SEND_MESSAGE,
                provider_id,
                resource_id
            )
            actions.append(InteractiveAction(
                action_type=ActionType.SEND_MESSAGE,
                label="💬 Send Message",
                url=message_url,
                style="secondary",
                icon="💬"
            ))
        
        return actions
    
    def generate_status_update_link(self, 
                                  resource_type: str,
                                  resource_id: str, 
                                  user_id: str) -> str:
        """Generate a real-time status update link"""
        return self.generate_action_url(
            ActionType.VIEW_RESULTS,
            user_id,
            resource_id,
            resource_type=resource_type,
            real_time=True,
            expires_in_hours=168  # 1 week
        )
    
    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """Generate HMAC signature for payload security"""
        # Sort payload for consistent signature
        sorted_payload = dict(sorted(payload.items()))
        
        # Create message string
        message = '&'.join([f"{k}={v}" for k, v in sorted_payload.items() if k != 'signature'])
        
        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, payload: Dict[str, Any]) -> bool:
        """Verify the signature of a payload"""
        if 'signature' not in payload:
            return False
        
        provided_signature = payload.pop('signature')
        expected_signature = self._generate_signature(payload)
        
        # Restore signature to payload
        payload['signature'] = provided_signature
        
        return hmac.compare_digest(provided_signature, expected_signature)
    
    def _format_google_date(self, dt: datetime) -> str:
        """Format datetime for Google Calendar"""
        return dt.strftime('%Y%m%dT%H%M%SZ')
    
    def _serialize_event(self, event: CalendarEvent) -> Dict[str, Any]:
        """Serialize calendar event for URL parameters"""
        return {
            'title': event.title,
            'start_time': event.start_time.isoformat(),
            'end_time': event.end_time.isoformat(),
            'description': event.description,
            'location': event.location,
            'timezone': event.timezone
        }

class RealTimeStatusService:
    """Service for real-time status updates"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
    
    def create_status_channel(self, resource_type: str, resource_id: str) -> str:
        """Create a real-time status update channel"""
        channel_id = f"{resource_type}:{resource_id}:{uuid.uuid4().hex[:8]}"
        
        if self.redis_client:
            # Set initial status
            self.redis_client.hset(
                f"status:{channel_id}",
                mapping={
                    'created_at': datetime.utcnow().isoformat(),
                    'resource_type': resource_type,
                    'resource_id': resource_id,
                    'status': 'active'
                }
            )
            # Set expiration (7 days)
            self.redis_client.expire(f"status:{channel_id}", 604800)
        
        return channel_id
    
    def update_status(self, channel_id: str, status_data: Dict[str, Any]) -> bool:
        """Update status for a channel"""
        if not self.redis_client:
            return False
        
        try:
            # Update status data
            status_data['updated_at'] = datetime.utcnow().isoformat()
            self.redis_client.hset(f"status:{channel_id}", mapping=status_data)
            
            # Publish update to subscribers
            self.redis_client.publish(f"status_updates:{channel_id}", 
                                    str(status_data))
            return True
        except Exception:
            return False
    
    def get_status(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get current status for a channel"""
        if not self.redis_client:
            return None
        
        try:
            status = self.redis_client.hgetall(f"status:{channel_id}")
            return {k.decode(): v.decode() for k, v in status.items()} if status else None
        except Exception:
            return None

# Example usage and integration helpers
def create_interactive_email_context(service: InteractiveEmailService,
                                    template_type: str,
                                    user_id: str,
                                    resource_id: str,
                                    **kwargs) -> Dict[str, Any]:
    """Create interactive email context based on template type"""
    context = {
        'interactive_actions': [],
        'calendar_links': {},
        'quick_responses': [],
        'status_update_link': None
    }
    
    if template_type == 'appointment_confirmation':
        appointment_datetime = kwargs.get('appointment_datetime')
        if appointment_datetime:
            context['interactive_actions'] = service.generate_appointment_actions(
                resource_id, user_id, appointment_datetime
            )
            
            # Add calendar event
            event = CalendarEvent(
                title=kwargs.get('appointment_title', 'Medical Appointment'),
                start_time=appointment_datetime,
                end_time=appointment_datetime + timedelta(hours=1),
                description=kwargs.get('appointment_description', ''),
                location=kwargs.get('clinic_address', '')
            )
            context['calendar_links'] = service.generate_calendar_links(event)
    
    elif template_type == 'medication_reminder':
        context['interactive_actions'] = service.generate_medication_actions(
            resource_id, user_id
        )
    
    elif template_type == 'survey_request':
        context['quick_responses'] = service.generate_survey_quick_responses(
            resource_id, user_id
        )
    
    elif template_type == 'billing_reminder':
        amount = kwargs.get('amount', 0.0)
        context['interactive_actions'] = service.generate_billing_actions(
            resource_id, user_id, amount
        )
    
    # Add status update link for all templates
    context['status_update_link'] = service.generate_status_update_link(
        template_type, resource_id, user_id
    )
    
    return context