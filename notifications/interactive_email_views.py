from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import json
import logging
from .utils import get_appointment_data, get_patient_data, get_doctor_data
from .models import PushSubscription
from .push_notifications import push_notifications
from .email_client import email_client
from supabase_client import admin_client

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class InteractiveEmailActionView(View):
    """Handle interactive email actions like appointment confirmations, medication reminders, etc."""
    
    def post(self, request, action_type, entity_id):
        """Process interactive email actions"""
        try:
            data = json.loads(request.body) if request.body else {}
            
            # Route to appropriate handler based on action type
            if action_type == 'appointment':
                return self._handle_appointment_action(entity_id, data)
            elif action_type == 'medication':
                return self._handle_medication_action(entity_id, data)
            elif action_type == 'survey':
                return self._handle_survey_action(entity_id, data)
            elif action_type == 'billing':
                return self._handle_billing_action(entity_id, data)
            elif action_type == 'provider':
                return self._handle_provider_action(entity_id, data)
            else:
                return JsonResponse({'error': 'Invalid action type'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Error processing interactive email action: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def _handle_appointment_action(self, appointment_id, data):
        """Handle appointment-related actions"""
        action = data.get('action')
        
        if action == 'confirm':
            return self._confirm_appointment(appointment_id)
        elif action == 'reschedule':
            return self._reschedule_appointment(appointment_id, data)
        elif action == 'cancel':
            return self._cancel_appointment(appointment_id, data.get('reason'))
        else:
            return JsonResponse({'error': 'Invalid appointment action'}, status=400)
    
    def _confirm_appointment(self, appointment_id):
        """Confirm an appointment"""
        try:
            result = admin_client.table("appointments").update({
                "status": "confirmed",
                "confirmed_at": datetime.now().isoformat()
            }).eq("id", appointment_id).execute()
            
            if result.data:
                return JsonResponse({
                    'success': True,
                    'message': 'Appointment confirmed successfully',
                    'redirect_url': f'/appointments/{appointment_id}'
                })
            else:
                return JsonResponse({'error': 'Appointment not found'}, status=404)
                
        except Exception as e:
            logger.error(f"Error confirming appointment {appointment_id}: {e}")
            return JsonResponse({'error': 'Failed to confirm appointment'}, status=500)
    
    def _reschedule_appointment(self, appointment_id, data):
        """Reschedule an appointment"""
        new_date = data.get('new_date')
        new_time = data.get('new_time')
        
        if not new_date or not new_time:
            return JsonResponse({'error': 'New date and time required'}, status=400)
        
        try:
            result = admin_client.table("appointments").update({
                "date": new_date,
                "time": new_time,
                "status": "rescheduled",
                "rescheduled_at": datetime.now().isoformat()
            }).eq("id", appointment_id).execute()
            
            if result.data:
                return JsonResponse({
                    'success': True,
                    'message': 'Appointment rescheduled successfully',
                    'new_date': new_date,
                    'new_time': new_time
                })
            else:
                return JsonResponse({'error': 'Appointment not found'}, status=404)
                
        except Exception as e:
            logger.error(f"Error rescheduling appointment {appointment_id}: {e}")
            return JsonResponse({'error': 'Failed to reschedule appointment'}, status=500)
    
    def _cancel_appointment(self, appointment_id, reason=None):
        """Cancel an appointment"""
        try:
            update_data = {
                "status": "cancelled",
                "cancelled_at": datetime.now().isoformat()
            }
            if reason:
                update_data["cancellation_reason"] = reason
            
            result = admin_client.table("appointments").update(update_data).eq("id", appointment_id).execute()
            
            if result.data:
                return JsonResponse({
                    'success': True,
                    'message': 'Appointment cancelled successfully'
                })
            else:
                return JsonResponse({'error': 'Appointment not found'}, status=404)
                
        except Exception as e:
            logger.error(f"Error cancelling appointment {appointment_id}: {e}")
            return JsonResponse({'error': 'Failed to cancel appointment'}, status=500)
    
    def _handle_medication_action(self, medication_id, data):
        """Handle medication reminder actions"""
        action = data.get('action')
        
        if action == 'taken':
            return self._mark_medication_taken(medication_id)
        elif action == 'skip':
            return self._skip_medication(medication_id, data.get('reason'))
        elif action == 'snooze':
            return self._snooze_medication(medication_id, data.get('minutes', 30))
        else:
            return JsonResponse({'error': 'Invalid medication action'}, status=400)
    
    def _mark_medication_taken(self, medication_id):
        """Mark medication as taken"""
        try:
            result = admin_client.table("medication_logs").insert({
                "medication_id": medication_id,
                "taken_at": datetime.now().isoformat(),
                "status": "taken"
            }).execute()
            
            return JsonResponse({
                'success': True,
                'message': 'Medication marked as taken'
            })
            
        except Exception as e:
            logger.error(f"Error marking medication {medication_id} as taken: {e}")
            return JsonResponse({'error': 'Failed to update medication status'}, status=500)
    
    def _skip_medication(self, medication_id, reason=None):
        """Skip medication dose"""
        try:
            log_data = {
                "medication_id": medication_id,
                "skipped_at": datetime.now().isoformat(),
                "status": "skipped"
            }
            if reason:
                log_data["skip_reason"] = reason
            
            result = admin_client.table("medication_logs").insert(log_data).execute()
            
            return JsonResponse({
                'success': True,
                'message': 'Medication dose skipped'
            })
            
        except Exception as e:
            logger.error(f"Error skipping medication {medication_id}: {e}")
            return JsonResponse({'error': 'Failed to update medication status'}, status=500)
    
    def _snooze_medication(self, medication_id, minutes):
        """Snooze medication reminder"""
        try:
            snooze_until = datetime.now() + timedelta(minutes=minutes)
            
            result = admin_client.table("medication_reminders").update({
                "next_reminder": snooze_until.isoformat(),
                "snoozed_at": datetime.now().isoformat()
            }).eq("medication_id", medication_id).execute()
            
            return JsonResponse({
                'success': True,
                'message': f'Medication reminder snoozed for {minutes} minutes',
                'next_reminder': snooze_until.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error snoozing medication {medication_id}: {e}")
            return JsonResponse({'error': 'Failed to snooze reminder'}, status=500)
    
    def _handle_survey_action(self, survey_id, data):
        """Handle survey actions"""
        action = data.get('action')
        
        if action == 'start':
            return self._start_survey(survey_id)
        elif action == 'submit':
            return self._submit_survey_response(survey_id, data.get('responses', {}))
        elif action == 'rate':
            return self._rate_experience(survey_id, data.get('rating'))
        else:
            return JsonResponse({'error': 'Invalid survey action'}, status=400)
    
    def _start_survey(self, survey_id):
        """Start a survey"""
        return JsonResponse({
            'success': True,
            'message': 'Survey started',
            'redirect_url': f'/surveys/{survey_id}'
        })
    
    def _submit_survey_response(self, survey_id, responses):
        """Submit survey responses"""
        try:
            result = admin_client.table("survey_responses").insert({
                "survey_id": survey_id,
                "responses": responses,
                "submitted_at": datetime.now().isoformat()
            }).execute()
            
            return JsonResponse({
                'success': True,
                'message': 'Survey response submitted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error submitting survey response for {survey_id}: {e}")
            return JsonResponse({'error': 'Failed to submit survey response'}, status=500)
    
    def _rate_experience(self, survey_id, rating):
        """Rate experience"""
        if not rating or not (1 <= int(rating) <= 5):
            return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
        
        try:
            result = admin_client.table("experience_ratings").insert({
                "survey_id": survey_id,
                "rating": int(rating),
                "rated_at": datetime.now().isoformat()
            }).execute()
            
            return JsonResponse({
                'success': True,
                'message': 'Rating submitted successfully',
                'rating': rating
            })
            
        except Exception as e:
            logger.error(f"Error submitting rating for survey {survey_id}: {e}")
            return JsonResponse({'error': 'Failed to submit rating'}, status=500)
    
    def _handle_billing_action(self, bill_id, data):
        """Handle billing actions"""
        action = data.get('action')
        
        if action == 'pay':
            return self._process_payment(bill_id, data)
        elif action == 'view':
            return self._view_bill(bill_id)
        elif action == 'dispute':
            return self._dispute_bill(bill_id, data.get('reason'))
        else:
            return JsonResponse({'error': 'Invalid billing action'}, status=400)
    
    def _process_payment(self, bill_id, data):
        """Process bill payment"""
        return JsonResponse({
            'success': True,
            'message': 'Redirecting to payment portal',
            'redirect_url': f'/billing/pay/{bill_id}'
        })
    
    def _view_bill(self, bill_id):
        """View bill details"""
        return JsonResponse({
            'success': True,
            'message': 'Redirecting to bill details',
            'redirect_url': f'/billing/view/{bill_id}'
        })
    
    def _dispute_bill(self, bill_id, reason):
        """Dispute a bill"""
        try:
            result = admin_client.table("billing_disputes").insert({
                "bill_id": bill_id,
                "reason": reason,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }).execute()
            
            return JsonResponse({
                'success': True,
                'message': 'Billing dispute submitted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error submitting billing dispute for {bill_id}: {e}")
            return JsonResponse({'error': 'Failed to submit dispute'}, status=500)
    
    def _handle_provider_action(self, provider_id, data):
        """Handle provider communication actions"""
        action = data.get('action')
        
        if action == 'call':
            return self._initiate_call(provider_id)
        elif action == 'message':
            return self._send_message(provider_id, data.get('message'))
        elif action == 'schedule':
            return self._schedule_appointment(provider_id, data)
        else:
            return JsonResponse({'error': 'Invalid provider action'}, status=400)
    
    def _initiate_call(self, provider_id):
        """Initiate call with provider"""
        return JsonResponse({
            'success': True,
            'message': 'Redirecting to call interface',
            'redirect_url': f'/providers/call/{provider_id}'
        })
    
    def _send_message(self, provider_id, message):
        """Send message to provider"""
        if not message:
            return JsonResponse({'error': 'Message content required'}, status=400)
        
        try:
            result = admin_client.table("provider_messages").insert({
                "provider_id": provider_id,
                "message": message,
                "sent_at": datetime.now().isoformat(),
                "status": "sent"
            }).execute()
            
            return JsonResponse({
                'success': True,
                'message': 'Message sent to provider successfully'
            })
            
        except Exception as e:
            logger.error(f"Error sending message to provider {provider_id}: {e}")
            return JsonResponse({'error': 'Failed to send message'}, status=500)
    
    def _schedule_appointment(self, provider_id, data):
        """Schedule appointment with provider"""
        return JsonResponse({
            'success': True,
            'message': 'Redirecting to appointment scheduling',
            'redirect_url': f'/appointments/schedule/{provider_id}'
        })


class RealTimeStatusView(View):
    """Handle real-time status updates for various entities"""
    
    def get(self, request, entity_type, entity_id):
        """Get real-time status for an entity"""
        try:
            if entity_type == 'appointment':
                return self._get_appointment_status(entity_id)
            elif entity_type == 'medication':
                return self._get_medication_status(entity_id)
            elif entity_type == 'survey':
                return self._get_survey_status(entity_id)
            elif entity_type == 'billing':
                return self._get_billing_status(entity_id)
            else:
                return JsonResponse({'error': 'Invalid entity type'}, status=400)
                
        except Exception as e:
            logger.error(f"Error getting status for {entity_type} {entity_id}: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def _get_appointment_status(self, appointment_id):
        """Get appointment status"""
        try:
            appointment_data = get_appointment_data(appointment_id)
            if not appointment_data:
                return JsonResponse({'error': 'Appointment not found'}, status=404)
            
            return JsonResponse({
                'status': appointment_data['status'],
                'date': appointment_data['date'],
                'time': appointment_data['time'],
                'location': appointment_data.get('location'),
                'last_updated': appointment_data.get('updated_at')
            })
            
        except Exception as e:
            logger.error(f"Error getting appointment status {appointment_id}: {e}")
            return JsonResponse({'error': 'Failed to get appointment status'}, status=500)
    
    def _get_medication_status(self, medication_id):
        """Get medication status"""
        try:
            result = admin_client.table("medications").select("*").eq("id", medication_id).single().execute()
            
            if not result.data:
                return JsonResponse({'error': 'Medication not found'}, status=404)
            
            medication = result.data
            return JsonResponse({
                'status': medication.get('status'),
                'next_dose': medication.get('next_dose'),
                'last_taken': medication.get('last_taken'),
                'adherence_rate': medication.get('adherence_rate')
            })
            
        except Exception as e:
            logger.error(f"Error getting medication status {medication_id}: {e}")
            return JsonResponse({'error': 'Failed to get medication status'}, status=500)
    
    def _get_survey_status(self, survey_id):
        """Get survey status"""
        try:
            result = admin_client.table("surveys").select("*").eq("id", survey_id).single().execute()
            
            if not result.data:
                return JsonResponse({'error': 'Survey not found'}, status=404)
            
            survey = result.data
            return JsonResponse({
                'status': survey.get('status'),
                'completion_rate': survey.get('completion_rate'),
                'expires_at': survey.get('expires_at'),
                'responses_count': survey.get('responses_count', 0)
            })
            
        except Exception as e:
            logger.error(f"Error getting survey status {survey_id}: {e}")
            return JsonResponse({'error': 'Failed to get survey status'}, status=500)
    
    def _get_billing_status(self, bill_id):
        """Get billing status"""
        try:
            result = admin_client.table("bills").select("*").eq("id", bill_id).single().execute()
            
            if not result.data:
                return JsonResponse({'error': 'Bill not found'}, status=404)
            
            bill = result.data
            return JsonResponse({
                'status': bill.get('status'),
                'amount': bill.get('amount'),
                'due_date': bill.get('due_date'),
                'payment_method': bill.get('payment_method'),
                'last_updated': bill.get('updated_at')
            })
            
        except Exception as e:
            logger.error(f"Error getting billing status {bill_id}: {e}")
            return JsonResponse({'error': 'Failed to get billing status'}, status=500)