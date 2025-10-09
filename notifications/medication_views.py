"""
API views for medication reminder management.
"""
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.contrib.auth.models import User
import json
from .medication_reminder_service import medication_reminder_service
from .models import ScheduledTask
from authentication.middleware import api_csrf_exempt, get_request_user

logger = logging.getLogger(__name__)

@api_csrf_exempt
@login_required
@require_http_methods(["POST"])
def schedule_medication_reminder(request):
    """
    Schedule medication reminders for a user.
    
    Expected JSON payload:
    {
        "medication_id": "med_123",
        "medication_name": "Aspirin",
        "dosage": "100mg",
        "schedule_times": ["08:00", "20:00"],
        "start_date": "2024-01-15",
        "end_date": "2024-02-15",
        "days_of_week": [0, 1, 2, 3, 4, 5, 6],
        "channels": ["fcm", "web_push"]
    }
    """
    try:
        user = get_request_user(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['medication_id', 'medication_name', 'dosage', 'schedule_times']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Parse dates
        start_date = None
        if 'start_date' in data:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        
        end_date = None
        if 'end_date' in data:
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Schedule the reminders
        result = medication_reminder_service.schedule_medication_reminder(
            user=user,
            medication_id=data['medication_id'],
            medication_name=data['medication_name'],
            dosage=data['dosage'],
            schedule_times=data['schedule_times'],
            start_date=start_date,
            end_date=end_date,
            days_of_week=data.get('days_of_week'),
            channels=data.get('channels')
        )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        logger.error(f"Error scheduling medication reminder: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@api_csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_immediate_reminder(request):
    """
    Send an immediate medication reminder.
    
    Expected JSON payload:
    {
        "medication_name": "Aspirin",
        "dosage": "100mg",
        "reminder_type": "scheduled",
        "channels": ["fcm"]
    }
    """
    try:
        user = get_request_user(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['medication_name', 'dosage']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Send the reminder
        result = medication_reminder_service.send_immediate_medication_reminder(
            user=user,
            medication_name=data['medication_name'],
            dosage=data['dosage'],
            reminder_type=data.get('reminder_type', 'scheduled'),
            channels=data.get('channels')
        )
        
        return JsonResponse({
            'success': True,
            'results': result
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        logger.error(f"Error sending immediate reminder: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@api_csrf_exempt
@login_required
@require_http_methods(["POST"])
def mark_medication_taken(request):
    """
    Mark medication as taken.
    
    Expected JSON payload:
    {
        "medication_id": "med_123",
        "taken_time": "2024-01-15T08:30:00Z"
    }
    """
    try:
        user = get_request_user(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        data = json.loads(request.body)
        
        if 'medication_id' not in data:
            return JsonResponse({
                'success': False,
                'error': 'Missing required field: medication_id'
            }, status=400)
        
        # Parse taken time
        taken_time = None
        if 'taken_time' in data:
            taken_time = datetime.fromisoformat(data['taken_time'].replace('Z', '+00:00'))
        
        # Handle medication taken
        result = medication_reminder_service.handle_medication_taken(
            user=user,
            medication_id=data['medication_id'],
            taken_time=taken_time
        )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON payload'
        }, status=400)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'Invalid date format: {e}'
        }, status=400)
    except Exception as e:
        logger.error(f"Error marking medication taken: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@api_csrf_exempt
@login_required
@require_http_methods(["POST"])
def snooze_reminder(request):
    """
    Snooze a medication reminder.
    
    Expected JSON payload:
    {
        "medication_id": "med_123",
        "snooze_minutes": 15
    }
    """
    try:
        user = get_request_user(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        data = json.loads(request.body)
        
        if 'medication_id' not in data:
            return JsonResponse({
                'success': False,
                'error': 'Missing required field: medication_id'
            }, status=400)
        
        # Snooze the reminder
        result = medication_reminder_service.snooze_medication_reminder(
            user=user,
            medication_id=data['medication_id'],
            snooze_minutes=data.get('snooze_minutes', 15)
        )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        logger.error(f"Error snoozing reminder: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_upcoming_reminders(request):
    """
    Get upcoming medication reminders for the authenticated user.
    
    Query parameters:
    - hours_ahead: Number of hours to look ahead (default: 24)
    """
    try:
        user = get_request_user(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        hours_ahead = int(request.GET.get('hours_ahead', 24))
        
        # Get upcoming reminders
        reminders = medication_reminder_service.get_upcoming_reminders(
            user=user,
            hours_ahead=hours_ahead
        )
        
        return JsonResponse({
            'success': True,
            'reminders': reminders,
            'count': len(reminders)
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid hours_ahead parameter'
        }, status=400)
    except Exception as e:
        logger.error(f"Error getting upcoming reminders: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@api_csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def cancel_medication_reminders(request):
    """
    Cancel all reminders for a specific medication.
    
    Expected JSON payload:
    {
        "medication_id": "med_123"
    }
    """
    try:
        user = get_request_user(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        data = json.loads(request.body)
        
        if 'medication_id' not in data:
            return JsonResponse({
                'success': False,
                'error': 'Missing required field: medication_id'
            }, status=400)
        
        # Cancel the reminders
        result = medication_reminder_service.cancel_medication_reminders(
            user=user,
            medication_id=data['medication_id']
        )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        logger.error(f"Error cancelling medication reminders: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_medication_history(request):
    """
    Get medication reminder history for the authenticated user.
    
    Query parameters:
    - medication_id: Filter by specific medication (optional)
    - days_back: Number of days to look back (default: 7)
    - status: Filter by status (optional)
    """
    try:
        user = get_request_user(request)
        if not user:
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        medication_id = request.GET.get('medication_id')
        days_back = int(request.GET.get('days_back', 7))
        status_filter = request.GET.get('status')
        
        # Build query
        start_date = timezone.now() - timedelta(days=days_back)
        
        query = ScheduledTask.objects.filter(
            user_id=user.id,
            task_type='medication_reminder',
            created_time__gte=start_date
        )
        
        if medication_id:
            query = query.filter(metadata__medication_id=medication_id)
        
        if status_filter:
            query = query.filter(status=status_filter)
        
        tasks = query.order_by('-scheduled_time')
        
        # Format response
        history = []
        for task in tasks:
            metadata = task.metadata or {}
            history.append({
                'task_id': task.id,
                'medication_id': metadata.get('medication_id'),
                'medication_name': metadata.get('medication_name'),
                'dosage': metadata.get('dosage'),
                'scheduled_time': task.scheduled_time.isoformat(),
                'status': task.status,
                'completed_time': task.completed_time.isoformat() if task.completed_time else None,
                'taken_time': metadata.get('taken_time'),
                'snoozed': metadata.get('snoozed', False),
                'channels': metadata.get('channels', [])
            })
        
        return JsonResponse({
            'success': True,
            'history': history,
            'count': len(history),
            'days_back': days_back
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid parameter value'
        }, status=400)
    except Exception as e:
        logger.error(f"Error getting medication history: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class MedicationReminderStatsView(View):
    """
    Get medication reminder statistics for the authenticated user.
    """
    
    def get(self, request):
        """
        Get medication reminder statistics.
        
        Query parameters:
        - days_back: Number of days to analyze (default: 30)
        """
        try:
            days_back = int(request.GET.get('days_back', 30))
            start_date = timezone.now() - timedelta(days=days_back)
            
            # Get all medication reminders in the period
            tasks = ScheduledTask.objects.filter(
                user_id=user.id,
                task_type='medication_reminder',
                created_time__gte=start_date
            )
            
            # Calculate statistics
            total_reminders = tasks.count()
            completed_reminders = tasks.filter(status='completed').count()
            missed_reminders = tasks.filter(status='failed').count()
            snoozed_reminders = tasks.filter(metadata__snoozed=True).count()
            
            # Calculate adherence rate
            adherence_rate = 0
            if total_reminders > 0:
                adherence_rate = (completed_reminders / total_reminders) * 100
            
            # Get medication breakdown
            medication_stats = {}
            for task in tasks:
                metadata = task.metadata or {}
                med_id = metadata.get('medication_id', 'unknown')
                med_name = metadata.get('medication_name', 'Unknown')
                
                if med_id not in medication_stats:
                    medication_stats[med_id] = {
                        'medication_name': med_name,
                        'total': 0,
                        'completed': 0,
                        'missed': 0,
                        'snoozed': 0
                    }
                
                medication_stats[med_id]['total'] += 1
                if task.status == 'completed':
                    medication_stats[med_id]['completed'] += 1
                elif task.status == 'failed':
                    medication_stats[med_id]['missed'] += 1
                
                if metadata.get('snoozed'):
                    medication_stats[med_id]['snoozed'] += 1
            
            return JsonResponse({
                'success': True,
                'stats': {
                    'total_reminders': total_reminders,
                    'completed_reminders': completed_reminders,
                    'missed_reminders': missed_reminders,
                    'snoozed_reminders': snoozed_reminders,
                    'adherence_rate': round(adherence_rate, 2),
                    'days_analyzed': days_back
                },
                'medication_breakdown': list(medication_stats.values())
            })
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid parameter value'
            }, status=400)
        except Exception as e:
            logger.error(f"Error getting medication stats: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Internal server error'
            }, status=500)