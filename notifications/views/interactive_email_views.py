from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, Any, Optional

from ..interactive_email import (
    InteractiveEmailService, 
    ActionType, 
    RealTimeStatusService,
    CalendarEvent
)
from ..models import (
    Notification, 
    NotificationTemplate, 
    NotificationRecipient
)
from appointments.models import Appointment
from accounts.models import EnhancedPatient
from medications.models import MedicationReminder
from billing.models import Invoice
from surveys.models import Survey, SurveyResponse

logger = logging.getLogger(__name__)

class InteractiveEmailActionView(View):
    """Handle interactive email actions"""
    
    def __init__(self):
        super().__init__()
        self.interactive_service = InteractiveEmailService(
            base_url=settings.BASE_URL,
            secret_key=settings.INTERACTIVE_EMAIL_SECRET_KEY
        )
        self.status_service = RealTimeStatusService(
            redis_client=getattr(settings, 'REDIS_CLIENT', None)
        )
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        """Handle GET requests for interactive email actions"""
        try:
            # Extract and verify parameters
            params = dict(request.GET.items())
            
            # Verify signature
            if not self.interactive_service.verify_signature(params.copy()):
                return JsonResponse({'error': 'Invalid signature'}, status=403)
            
            # Check expiration
            expires_at = int(params.get('expires_at', 0))
            if datetime.utcnow().timestamp() > expires_at:
                return JsonResponse({'error': 'Action expired'}, status=410)
            
            # Extract action details
            action_type = ActionType(params.get('action'))
            user_id = params.get('user_id')
            resource_id = params.get('resource_id')
            
            # Route to appropriate handler
            return self._handle_action(action_type, user_id, resource_id, params)
            
        except Exception as e:
            logger.error(f"Error handling interactive email action: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def _handle_action(self, action_type: ActionType, user_id: str, 
                      resource_id: str, params: Dict[str, Any]) -> JsonResponse:
        """Route action to appropriate handler"""
        
        handlers = {
            ActionType.CONFIRM_APPOINTMENT: self._handle_confirm_appointment,
            ActionType.RESCHEDULE_APPOINTMENT: self._handle_reschedule_appointment,
            ActionType.CANCEL_APPOINTMENT: self._handle_cancel_appointment,
            ActionType.ADD_TO_CALENDAR: self._handle_add_to_calendar,
            ActionType.MARK_MEDICATION_TAKEN: self._handle_mark_medication_taken,
            ActionType.SNOOZE_REMINDER: self._handle_snooze_reminder,
            ActionType.SURVEY_RATING: self._handle_survey_rating,
            ActionType.PAYMENT_LINK: self._handle_payment_link,
            ActionType.VIEW_RESULTS: self._handle_view_results,
            ActionType.CALL_PATIENT: self._handle_call_patient,
            ActionType.SEND_MESSAGE: self._handle_send_message,
            ActionType.UPDATE_PREFERENCES: self._handle_update_preferences,
        }
        
        handler = handlers.get(action_type)
        if not handler:
            return JsonResponse({'error': 'Unsupported action type'}, status=400)
        
        return handler(user_id, resource_id, params)
    
    def _handle_confirm_appointment(self, user_id: str, resource_id: str, 
                                  params: Dict[str, Any]) -> JsonResponse:
        """Handle appointment confirmation"""
        try:
            appointment = get_object_or_404(Appointment, id=resource_id)
            
            # Update appointment status
            appointment.status = 'confirmed'
            appointment.confirmed_at = timezone.now()
            appointment.save()
            
            # Update real-time status
            channel_id = self.status_service.create_status_channel(
                'appointment', resource_id
            )
            self.status_service.update_status(channel_id, {
                'status': 'confirmed',
                'message': 'Appointment confirmed successfully',
                'confirmed_at': timezone.now().isoformat()
            })
            
            # Log the action
            logger.info(f"Appointment {resource_id} confirmed by user {user_id}")
            
            return JsonResponse({
                'success': True,
                'message': 'Appointment confirmed successfully',
                'redirect_url': f'/appointments/{resource_id}/confirmed'
            })
            
        except Exception as e:
            logger.error(f"Error confirming appointment: {str(e)}")
            return JsonResponse({'error': 'Failed to confirm appointment'}, status=500)
    
    def _handle_reschedule_appointment(self, user_id: str, resource_id: str, 
                                     params: Dict[str, Any]) -> JsonResponse:
        """Handle appointment rescheduling"""
        try:
            appointment = get_object_or_404(Appointment, id=resource_id)
            
            # Check if rescheduling is allowed
            if appointment.appointment_datetime <= timezone.now() + timedelta(hours=24):
                return JsonResponse({
                    'error': 'Cannot reschedule appointments less than 24 hours in advance'
                }, status=400)
            
            # Redirect to rescheduling interface
            reschedule_url = f'/appointments/{resource_id}/reschedule?token={params.get("nonce")}'
            
            return JsonResponse({
                'success': True,
                'message': 'Redirecting to rescheduling interface',
                'redirect_url': reschedule_url
            })
            
        except Exception as e:
            logger.error(f"Error handling reschedule request: {str(e)}")
            return JsonResponse({'error': 'Failed to process reschedule request'}, status=500)
    
    def _handle_cancel_appointment(self, user_id: str, resource_id: str, 
                                 params: Dict[str, Any]) -> JsonResponse:
        """Handle appointment cancellation"""
        try:
            appointment = get_object_or_404(Appointment, id=resource_id)
            
            # Update appointment status
            appointment.status = 'cancelled'
            appointment.cancelled_at = timezone.now()
            appointment.cancellation_reason = 'Patient cancelled via email'
            appointment.save()
            
            # Update real-time status
            channel_id = self.status_service.create_status_channel(
                'appointment', resource_id
            )
            self.status_service.update_status(channel_id, {
                'status': 'cancelled',
                'message': 'Appointment cancelled successfully',
                'cancelled_at': timezone.now().isoformat()
            })
            
            # Log the action
            logger.info(f"Appointment {resource_id} cancelled by user {user_id}")
            
            return JsonResponse({
                'success': True,
                'message': 'Appointment cancelled successfully',
                'redirect_url': f'/appointments/{resource_id}/cancelled'
            })
            
        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            return JsonResponse({'error': 'Failed to cancel appointment'}, status=500)
    
    def _handle_add_to_calendar(self, user_id: str, resource_id: str, 
                              params: Dict[str, Any]) -> HttpResponse:
        """Handle calendar file generation"""
        try:
            format_type = params.get('format', 'ics')
            
            if format_type == 'ics':
                # Generate ICS file
                event_data = json.loads(params.get('event_data', '{}'))
                ics_content = self._generate_ics_file(event_data)
                
                response = HttpResponse(ics_content, content_type='text/calendar')
                response['Content-Disposition'] = f'attachment; filename="appointment_{resource_id}.ics"'
                return response
            
            return JsonResponse({'error': 'Unsupported calendar format'}, status=400)
            
        except Exception as e:
            logger.error(f"Error generating calendar file: {str(e)}")
            return JsonResponse({'error': 'Failed to generate calendar file'}, status=500)
    
    def _handle_mark_medication_taken(self, user_id: str, resource_id: str, 
                                    params: Dict[str, Any]) -> JsonResponse:
        """Handle medication taken confirmation"""
        try:
            reminder = get_object_or_404(MedicationReminder, id=resource_id)
            
            # Record medication taken
            from medications.models import MedicationLog
            MedicationLog.objects.create(
                medication_reminder=reminder,
                patient=reminder.patient,
                taken_at=timezone.now(),
                status='taken',
                source='email_action'
            )
            
            # Update real-time status
            channel_id = self.status_service.create_status_channel(
                'medication', resource_id
            )
            self.status_service.update_status(channel_id, {
                'status': 'taken',
                'message': 'Medication marked as taken',
                'taken_at': timezone.now().isoformat()
            })
            
            return JsonResponse({
                'success': True,
                'message': 'Medication marked as taken successfully'
            })
            
        except Exception as e:
            logger.error(f"Error marking medication as taken: {str(e)}")
            return JsonResponse({'error': 'Failed to mark medication as taken'}, status=500)
    
    def _handle_snooze_reminder(self, user_id: str, resource_id: str, 
                              params: Dict[str, Any]) -> JsonResponse:
        """Handle reminder snoozing"""
        try:
            reminder = get_object_or_404(MedicationReminder, id=resource_id)
            snooze_minutes = int(params.get('snooze_minutes', 30))
            
            # Update reminder time
            reminder.next_reminder_time = timezone.now() + timedelta(minutes=snooze_minutes)
            reminder.save()
            
            # Update real-time status
            channel_id = self.status_service.create_status_channel(
                'medication', resource_id
            )
            self.status_service.update_status(channel_id, {
                'status': 'snoozed',
                'message': f'Reminder snoozed for {snooze_minutes} minutes',
                'snoozed_until': reminder.next_reminder_time.isoformat()
            })
            
            return JsonResponse({
                'success': True,
                'message': f'Reminder snoozed for {snooze_minutes} minutes'
            })
            
        except Exception as e:
            logger.error(f"Error snoozing reminder: {str(e)}")
            return JsonResponse({'error': 'Failed to snooze reminder'}, status=500)
    
    def _handle_survey_rating(self, user_id: str, resource_id: str, 
                            params: Dict[str, Any]) -> JsonResponse:
        """Handle quick survey rating"""
        try:
            survey = get_object_or_404(Survey, id=resource_id)
            rating = int(params.get('rating', 0))
            question = params.get('question', 'overall_satisfaction')
            
            # Create or update survey response
            response, created = SurveyResponse.objects.get_or_create(
                survey=survey,
                patient_id=user_id,
                defaults={'responses': {}}
            )
            
            # Update response data
            if not response.responses:
                response.responses = {}
            response.responses[question] = rating
            response.completed_at = timezone.now()
            response.save()
            
            # Update real-time status
            channel_id = self.status_service.create_status_channel(
                'survey', resource_id
            )
            self.status_service.update_status(channel_id, {
                'status': 'partial_response',
                'message': f'Rating submitted: {rating} stars',
                'rating': rating,
                'question': question
            })
            
            return JsonResponse({
                'success': True,
                'message': f'Thank you for your {rating}-star rating!',
                'redirect_url': f'/surveys/{resource_id}/complete'
            })
            
        except Exception as e:
            logger.error(f"Error submitting survey rating: {str(e)}")
            return JsonResponse({'error': 'Failed to submit rating'}, status=500)
    
    def _handle_payment_link(self, user_id: str, resource_id: str, 
                           params: Dict[str, Any]) -> JsonResponse:
        """Handle payment link generation"""
        try:
            invoice = get_object_or_404(Invoice, id=resource_id)
            
            # Generate secure payment link
            payment_url = f'/billing/pay/{resource_id}?token={params.get("nonce")}'
            
            return JsonResponse({
                'success': True,
                'message': 'Redirecting to secure payment portal',
                'redirect_url': payment_url
            })
            
        except Exception as e:
            logger.error(f"Error generating payment link: {str(e)}")
            return JsonResponse({'error': 'Failed to generate payment link'}, status=500)
    
    def _handle_view_results(self, user_id: str, resource_id: str, 
                           params: Dict[str, Any]) -> JsonResponse:
        """Handle viewing results/documents"""
        try:
            document_type = params.get('document_type', 'general')
            real_time = params.get('real_time', False)
            
            if real_time:
                # Return real-time status page
                status_url = f'/status/{document_type}/{resource_id}?token={params.get("nonce")}'
            else:
                # Return document view
                status_url = f'/documents/{document_type}/{resource_id}?token={params.get("nonce")}'
            
            return JsonResponse({
                'success': True,
                'message': 'Redirecting to document view',
                'redirect_url': status_url
            })
            
        except Exception as e:
            logger.error(f"Error handling view results: {str(e)}")
            return JsonResponse({'error': 'Failed to access document'}, status=500)
    
    def _handle_call_patient(self, user_id: str, resource_id: str, 
                           params: Dict[str, Any]) -> JsonResponse:
        """Handle provider call patient action"""
        try:
            # This would integrate with a calling system
            # For now, we'll log the action and redirect to calling interface
            
            call_url = f'/provider/call-patient/{resource_id}?token={params.get("nonce")}'
            
            return JsonResponse({
                'success': True,
                'message': 'Redirecting to calling interface',
                'redirect_url': call_url
            })
            
        except Exception as e:
            logger.error(f"Error handling call patient: {str(e)}")
            return JsonResponse({'error': 'Failed to initiate call'}, status=500)
    
    def _handle_send_message(self, user_id: str, resource_id: str, 
                           params: Dict[str, Any]) -> JsonResponse:
        """Handle provider send message action"""
        try:
            message_url = f'/provider/send-message/{resource_id}?token={params.get("nonce")}'
            
            return JsonResponse({
                'success': True,
                'message': 'Redirecting to messaging interface',
                'redirect_url': message_url
            })
            
        except Exception as e:
            logger.error(f"Error handling send message: {str(e)}")
            return JsonResponse({'error': 'Failed to open messaging'}, status=500)
    
    def _handle_update_preferences(self, user_id: str, resource_id: str, 
                                 params: Dict[str, Any]) -> JsonResponse:
        """Handle preference updates"""
        try:
            preferences_url = f'/preferences/{user_id}?token={params.get("nonce")}'
            
            return JsonResponse({
                'success': True,
                'message': 'Redirecting to preferences',
                'redirect_url': preferences_url
            })
            
        except Exception as e:
            logger.error(f"Error handling preferences update: {str(e)}")
            return JsonResponse({'error': 'Failed to access preferences'}, status=500)
    
    def _generate_ics_file(self, event_data: Dict[str, Any]) -> str:
        """Generate ICS calendar file content"""
        start_time = datetime.fromisoformat(event_data['start_time'])
        end_time = datetime.fromisoformat(event_data['end_time'])
        
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MediRemind//Medical Appointment//EN
BEGIN:VEVENT
UID:{event_data.get('uid', 'appointment-' + str(timezone.now().timestamp()))}
DTSTAMP:{timezone.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_time.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{end_time.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{event_data['title']}
DESCRIPTION:{event_data['description']}
LOCATION:{event_data.get('location', '')}
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:Appointment Reminder
END:VALARM
END:VEVENT
END:VCALENDAR"""
        
        return ics_content

class RealTimeStatusView(View):
    """Handle real-time status updates"""
    
    def __init__(self):
        super().__init__()
        self.status_service = RealTimeStatusService(
            redis_client=getattr(settings, 'REDIS_CLIENT', None)
        )
    
    def get(self, request, resource_type, resource_id):
        """Get current status for a resource"""
        try:
            # Verify token
            token = request.GET.get('token')
            if not token:
                return JsonResponse({'error': 'Missing token'}, status=403)
            
            # Get status
            channel_id = f"{resource_type}:{resource_id}"
            status = self.status_service.get_status(channel_id)
            
            if not status:
                return JsonResponse({'error': 'Status not found'}, status=404)
            
            return JsonResponse({
                'success': True,
                'status': status,
                'channel_id': channel_id
            })
            
        except Exception as e:
            logger.error(f"Error getting real-time status: {str(e)}")
            return JsonResponse({'error': 'Failed to get status'}, status=500)

# URL patterns would be added to urls.py:
# path('api/interactive-email/action', InteractiveEmailActionView.as_view(), name='interactive_email_action'),
# path('status/<str:resource_type>/<str:resource_id>', RealTimeStatusView.as_view(), name='real_time_status'),