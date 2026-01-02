#!/usr/bin/env python3
"""
Dead Letter Queue API endpoints for managing failed notifications
"""

import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

from notifications.models import ScheduledTask, NotificationLog
from notifications.dead_letter_queue import DeadLetterQueue, DeadLetterQueueManager
from authentication.middleware import get_request_user
from datetime import datetime

def parse_datetime_safe(date_str):
    """Safely parse datetime string"""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None

logger = logging.getLogger(__name__)


@csrf_exempt
def get_dead_letter_queue(request):
    """
    GET /api/notifications/dead-letter-queue/
    
    Get dead letter queue entries with filtering and pagination
    
    Query Parameters:
    - status: Filter by status (pending_review, manually_resolved, archived, etc.)
    - failure_type: Filter by failure type
    - delivery_method: Filter by delivery method
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - search: Search by patient_id, appointment_id, or error message
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get user and hospital context
        user = get_request_user(request)
        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Get query parameters
        status = request.GET.get('status')
        failure_type = request.GET.get('failure_type')
        delivery_method = request.GET.get('delivery_method')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        search = request.GET.get('search')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        
        # Build query
        queryset = DeadLetterQueue.objects.all()
        
        # Apply filters
        if status:
            queryset = queryset.filter(status=status)
        
        if failure_type:
            queryset = queryset.filter(failure_type=failure_type)
        
        if delivery_method:
            queryset = queryset.filter(delivery_method=delivery_method)
        
        if start_date:
            start_dt = parse_datetime_safe(start_date)
            if start_dt:
                queryset = queryset.filter(created_at__gte=start_dt)
        
        if end_date:
            end_dt = parse_datetime_safe(end_date)
            if end_dt:
                queryset = queryset.filter(created_at__lte=end_dt)
        
        if search:
            queryset = queryset.filter(
                Q(patient_id__icontains=search) |
                Q(appointment_id__icontains=search) |
                Q(final_error_message__icontains=search) |
                Q(original_message_data__icontains=search)
            )
        
        # Apply hospital filtering if user has hospital context
        if hasattr(user, 'profile') and user.profile.hospital_id:
            # Filter by hospital through patient appointments
            # This assumes we can link patients to hospitals through their appointments
            patient_ids = get_patient_ids_for_hospital(user.profile.hospital_id)
            queryset = queryset.filter(patient_id__in=patient_ids)
        
        # Paginate results
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize results
        entries = []
        for entry in page_obj:
            entries.append({
                'id': str(entry.id),
                'original_task_id': str(entry.original_task_id),
                'task_type': entry.task_type,
                'appointment_id': str(entry.appointment_id),
                'patient_id': entry.patient_id,
                'provider_id': entry.provider_id,
                'delivery_method': entry.delivery_method,
                'failure_type': entry.failure_type,
                'final_error_message': entry.final_error_message,
                'error_history': entry.error_history,
                'retry_count': entry.retry_count,
                'max_retries_attempted': entry.max_retries_attempted,
                'original_scheduled_time': entry.original_scheduled_time.isoformat(),
                'final_failure_time': entry.final_failure_time.isoformat(),
                'status': entry.status,
                'reviewed_at': entry.reviewed_at.isoformat() if entry.reviewed_at else None,
                'reviewed_by': entry.reviewed_by,
                'resolution_notes': entry.resolution_notes,
                'resolution_data': entry.resolution_data,
                'created_at': entry.created_at.isoformat(),
                'updated_at': entry.updated_at.isoformat(),
                'can_be_retried': entry.can_be_retried(),
                'retry_suggestion': entry.get_retry_suggestion(),
            })
        
        return JsonResponse({
            'entries': entries,
            'pagination': {
                'page': page_obj.number,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_entries': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving dead letter queue: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
def get_dead_letter_statistics(request):
    """
    GET /api/notifications/dead-letter-queue/statistics/
    
    Get dead letter queue statistics
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get user and hospital context
        user = get_request_user(request)
        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Get statistics
        stats = DeadLetterQueueManager.get_statistics()
        
        # Get additional statistics
        now = timezone.now()
        
        # Recent failures (last 7 days by day)
        recent_failures = []
        for i in range(7):
            date = now - timedelta(days=i)
            count = DeadLetterQueue.objects.filter(
                final_failure_time__date=date.date()
            ).count()
            recent_failures.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        # Top failure types
        failure_type_stats = DeadLetterQueue.objects.values('failure_type').annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]
        
        # Top delivery methods with failures
        delivery_method_stats = DeadLetterQueue.objects.values('delivery_method').annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]
        
        # Retry candidates
        retry_candidates = DeadLetterQueueManager.get_retry_candidates()
        
        return JsonResponse({
            'statistics': stats,
            'recent_failures': recent_failures,
            'failure_type_breakdown': [
                {'failure_type': item['failure_type'], 'count': item['count']}
                for item in failure_type_stats
            ],
            'delivery_method_breakdown': [
                {'delivery_method': item['delivery_method'], 'count': item['count']}
                for item in delivery_method_stats
            ],
            'retry_candidates_count': retry_candidates.count(),
            'retry_candidates': [
                {
                    'id': str(entry.id),
                    'original_task_id': str(entry.original_task_id),
                    'task_type': entry.task_type,
                    'delivery_method': entry.delivery_method,
                    'failure_type': entry.failure_type,
                    'final_error_message': entry.final_error_message,
                    'retry_count': entry.retry_count,
                    'created_at': entry.created_at.isoformat(),
                    'can_be_retried': entry.can_be_retried(),
                    'retry_suggestion': entry.get_retry_suggestion(),
                }
                for entry in retry_candidates[:10]  # Return first 10 candidates
            ]
        })
        
    except Exception as e:
        logger.error(f"Error retrieving dead letter statistics: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
def review_dead_letter_entry(request, entry_id):
    """
    POST /api/notifications/dead-letter-queue/{entry_id}/review/
    
    Review and update a dead letter queue entry
    
    Request Body:
    {
        "action": "mark_resolved" | "archive" | "retry" | "requires_manual_intervention",
        "reviewed_by": "user@example.com",
        "resolution_notes": "Optional resolution notes",
        "resolution_data": {}
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get user and hospital context
        user = get_request_user(request)
        if not user:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Validate required fields
        action = data.get('action')
        reviewed_by = data.get('reviewed_by', user.email if hasattr(user, 'email') else 'unknown')
        
        if not action:
            return JsonResponse({'error': 'Action is required'}, status=400)
        
        # Get the dead letter entry
        try:
            entry = DeadLetterQueue.objects.get(id=entry_id)
        except DeadLetterQueue.DoesNotExist:
            return JsonResponse({'error': 'Dead letter entry not found'}, status=404)
        
        # Check hospital access
        if hasattr(user, 'profile') and user.profile.hospital_id:
            patient_ids = get_patient_ids_for_hospital(user.profile.hospital_id)
            if entry.patient_id not in patient_ids:
                return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Handle different actions
        if action == 'mark_resolved':
            entry.mark_as_reviewed(
                reviewed_by=reviewed_by,
                resolution_notes=data.get('resolution_notes', ''),
                resolution_data=data.get('resolution_data', {})
            )
            message = 'Entry marked as resolved'
            
        elif action == 'archive':
            entry.archive()
            message = 'Entry archived'
            
        elif action == 'retry':
            if not entry.can_be_retried():
                return JsonResponse({
                    'error': 'This entry cannot be retried',
                    'reason': entry.get_retry_suggestion()
                }, status=400)
            
            # Create a new task from the dead letter entry
            try:
                new_task = retry_from_dead_letter(entry, reviewed_by)
                entry.status = 'manually_resolved'
                entry.resolution_notes = f"Manually retried as task {new_task.id}"
                entry.resolution_data = {'retry_task_id': str(new_task.id)}
                entry.save()
                message = f'Entry retried as new task {new_task.id}'
            except Exception as e:
                logger.error(f"Error retrying dead letter entry {entry_id}: {e}")
                return JsonResponse({'error': 'Failed to create retry task'}, status=500)
                
        elif action == 'requires_manual_intervention':
            entry.status = 'requires_manual_intervention'
            entry.reviewed_by = reviewed_by
            entry.resolution_notes = data.get('resolution_notes', 'Requires manual intervention')
            entry.save()
            message = 'Entry marked as requiring manual intervention'
            
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        return JsonResponse({
            'message': message,
            'entry': {
                'id': str(entry.id),
                'status': entry.status,
                'reviewed_by': entry.reviewed_by,
                'reviewed_at': entry.reviewed_at.isoformat() if entry.reviewed_at else None,
                'resolution_notes': entry.resolution_notes,
                'can_be_retried': entry.can_be_retried(),
            }
        })
        
    except Exception as e:
        logger.error(f"Error reviewing dead letter entry {entry_id}: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


def retry_from_dead_letter(entry: DeadLetterQueue, reviewed_by: str) -> ScheduledTask:
    """Create a new task from a dead letter entry for retry"""
    
    # Create a new scheduled task with the same data but fresh retry count
    new_task = ScheduledTask.objects.create(
        task_type=entry.task_type,
        appointment_id=entry.appointment_id,
        delivery_method=entry.delivery_method,
        scheduled_time=timezone.now() + timedelta(minutes=5),  # Retry in 5 minutes
        priority=1,  # High priority for manual retries
        status='pending',
        retry_count=0,  # Fresh retry count
        max_retries=entry.max_retries_attempted + 2,  # Allow 2 more retries
        message_data=entry.original_message_data,
        error_message=None,  # Clear error message
    )
    
    # Create a notification log entry for the retry
    NotificationLog.objects.create(
        task_id=new_task.id,
        appointment_id=entry.appointment_id,
        patient_id=entry.patient_id,
        provider_id=entry.provider_id,
        notification_type=entry.task_type,
        delivery_method=entry.delivery_method,
        status='pending',
        scheduled_time=new_task.scheduled_time,
        message_data=entry.original_message_data,
        notes=f"Manual retry from dead letter queue entry {entry.id}, reviewed by {reviewed_by}",
    )
    
    return new_task


def get_patient_ids_for_hospital(hospital_id: str):
    """Get patient IDs for a specific hospital (placeholder - implement based on your data model)"""
    # This is a placeholder function - implement based on your actual data model
    # You might need to query your Supabase database or use your existing patient service
    return []