#!/usr/bin/env python3
"""
Dead Letter Queue implementation for failed notifications.
Handles notifications that have exceeded maximum retry attempts.
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import json

class DeadLetterQueue(models.Model):
    """Model for storing failed notifications that have exceeded maximum retry attempts"""
    
    FAILURE_TYPES = [
        ('max_retries_exceeded', 'Maximum Retries Exceeded'),
        ('permanent_failure', 'Permanent Failure'),
        ('invalid_recipient', 'Invalid Recipient'),
        ('service_unavailable', 'Service Unavailable'),
        ('authentication_error', 'Authentication Error'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('template_error', 'Template Error'),
        ('data_corruption', 'Data Corruption'),
        ('timeout', 'Timeout'),
        ('unknown', 'Unknown Error'),
    ]
    
    STATUSES = [
        ('pending_review', 'Pending Review'),
        ('manually_resolved', 'Manually Resolved'),
        ('archived', 'Archived'),
        ('auto_resolved', 'Auto Resolved'),
        ('requires_manual_intervention', 'Requires Manual Intervention'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Original task information
    original_task_id = models.UUIDField(unique=True)
    task_type = models.CharField(max_length=20)
    appointment_id = models.UUIDField()
    patient_id = models.CharField(max_length=255)
    provider_id = models.CharField(max_length=255, blank=True)
    delivery_method = models.CharField(max_length=20)
    
    # Failure information
    failure_type = models.CharField(max_length=30, choices=FAILURE_TYPES, default='unknown')
    final_error_message = models.TextField()
    error_history = models.JSONField(default=list)  # List of all error messages from retry attempts
    retry_count = models.IntegerField(default=0)
    max_retries_attempted = models.IntegerField(default=0)
    
    # Original message data
    original_message_data = models.JSONField(default=dict)
    original_scheduled_time = models.DateTimeField()
    final_failure_time = models.DateTimeField(default=timezone.now)
    
    # Resolution tracking
    status = models.CharField(max_length=30, choices=STATUSES, default='pending_review')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.CharField(max_length=255, blank=True)
    resolution_notes = models.TextField(blank=True)
    resolution_data = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_dead_letter_queue'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['failure_type', 'created_at']),
            models.Index(fields=['delivery_method', 'status']),
            models.Index(fields=['appointment_id', 'status']),
            models.Index(fields=['patient_id', 'status']),
            models.Index(fields=['final_failure_time']),
            models.Index(fields=['original_scheduled_time']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"DLQ Entry {self.id} - {self.task_type} - {self.failure_type}"
    
    def clean(self):
        """Validate the model"""
        if self.retry_count > self.max_retries_attempted:
            raise ValidationError("Retry count cannot exceed maximum retries attempted")
    
    def mark_as_reviewed(self, reviewed_by: str, resolution_notes: str = "", 
                          resolution_data: dict = None) -> None:
        """Mark the dead letter entry as reviewed"""
        self.status = 'manually_resolved'
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.resolution_notes = resolution_notes
        if resolution_data:
            self.resolution_data = resolution_data
        self.save()
    
    def archive(self) -> None:
        """Archive the dead letter entry"""
        self.status = 'archived'
        self.save()
    
    def can_be_retried(self) -> bool:
        """Check if this notification can be retried"""
        return self.status in ['pending_review', 'requires_manual_intervention'] and \
               self.failure_type not in ['permanent_failure', 'invalid_recipient', 'data_corruption']
    
    def get_retry_suggestion(self) -> dict:
        """Get retry suggestions based on failure type"""
        suggestions = {
            'max_retries_exceeded': {
                'can_retry': True,
                'suggestion': 'Consider increasing retry limit or retrying with different parameters',
                'priority': 'medium'
            },
            'service_unavailable': {
                'can_retry': True,
                'suggestion': 'Retry when service is available, check service status',
                'priority': 'high'
            },
            'rate_limit_exceeded': {
                'can_retry': True,
                'suggestion': 'Retry after rate limit period, consider implementing backoff',
                'priority': 'medium'
            },
            'timeout': {
                'can_retry': True,
                'suggestion': 'Retry with longer timeout or check network connectivity',
                'priority': 'medium'
            },
            'authentication_error': {
                'can_retry': True,
                'suggestion': 'Check authentication credentials and retry',
                'priority': 'high'
            },
            'template_error': {
                'can_retry': True,
                'suggestion': 'Fix template issues and retry',
                'priority': 'medium'
            },
            'permanent_failure': {
                'can_retry': False,
                'suggestion': 'Do not retry, this is a permanent failure',
                'priority': 'low'
            },
            'invalid_recipient': {
                'can_retry': False,
                'suggestion': 'Do not retry, recipient is invalid',
                'priority': 'low'
            },
            'data_corruption': {
                'can_retry': False,
                'suggestion': 'Do not retry, data is corrupted',
                'priority': 'low'
            },
            'unknown': {
                'can_retry': True,
                'suggestion': 'Investigate error and determine if retry is appropriate',
                'priority': 'medium'
            }
        }
        
        return suggestions.get(self.failure_type, suggestions['unknown'])


class DeadLetterQueueManager:
    """Manager for handling dead letter queue operations"""
    
    @staticmethod
    def add_to_dead_letter_queue(task, final_error_message: str, failure_type: str = 'unknown') -> DeadLetterQueue:
        """Add a failed task to the dead letter queue"""
        
        # Get error history from the task's logs
        error_history = []
        if hasattr(task, 'logs'):
            error_logs = task.logs.filter(status='failed').order_by('created_at')
            error_history = [
                {
                    'timestamp': log.created_at.isoformat(),
                    'error_message': log.error_message,
                    'status': log.status
                }
                for log in error_logs
            ]
        
        dlq_entry = DeadLetterQueue.objects.create(
            original_task_id=task.id,
            task_type=task.task_type,
            appointment_id=task.appointment_id,
            patient_id=task.message_data.get('patient_id', ''),
            provider_id=task.message_data.get('provider_id', ''),
            delivery_method=task.delivery_method,
            failure_type=failure_type,
            final_error_message=final_error_message,
            error_history=error_history,
            retry_count=task.retry_count,
            max_retries_attempted=task.max_retries,
            original_message_data=task.message_data,
            original_scheduled_time=task.scheduled_time
        )
        
        return dlq_entry
    
    @staticmethod
    def get_pending_reviews():
        """Get all pending review entries"""
        return DeadLetterQueue.objects.filter(status='pending_review').order_by('-created_at')
    
    @staticmethod
    def get_by_failure_type(failure_type: str):
        """Get entries by failure type"""
        return DeadLetterQueue.objects.filter(failure_type=failure_type).order_by('-created_at')
    
    @staticmethod
    def get_retry_candidates():
        """Get entries that are candidates for retry"""
        return DeadLetterQueue.objects.filter(
            status__in=['pending_review', 'requires_manual_intervention']
        ).exclude(
            failure_type__in=['permanent_failure', 'invalid_recipient', 'data_corruption']
        ).order_by('-created_at')
    
    @staticmethod
    def get_statistics() -> dict:
        """Get dead letter queue statistics"""
        total_entries = DeadLetterQueue.objects.count()
        
        status_counts = {
            status: DeadLetterQueue.objects.filter(status=status).count()
            for status, _ in DeadLetterQueue.STATUSES
        }
        
        failure_type_counts = {
            failure_type: DeadLetterQueue.objects.filter(failure_type=failure_type).count()
            for failure_type, _ in DeadLetterQueue.FAILURE_TYPES
        }
        
        # Time-based statistics
        from datetime import timedelta
        now = timezone.now()
        
        last_24h = DeadLetterQueue.objects.filter(created_at__gte=now - timedelta(days=1)).count()
        last_7d = DeadLetterQueue.objects.filter(created_at__gte=now - timedelta(days=7)).count()
        last_30d = DeadLetterQueue.objects.filter(created_at__gte=now - timedelta(days=30)).count()
        
        return {
            'total_entries': total_entries,
            'status_counts': status_counts,
            'failure_type_counts': failure_type_counts,
            'recent_entries': {
                'last_24h': last_24h,
                'last_7d': last_7d,
                'last_30d': last_30d
            },
            'pending_review_count': status_counts.get('pending_review', 0),
            'retry_candidates_count': DeadLetterQueue.objects.filter(
                status__in=['pending_review', 'requires_manual_intervention']
            ).exclude(
                failure_type__in=['permanent_failure', 'invalid_recipient', 'data_corruption']
            ).count()
        }


# Enhanced retry logic for ScheduledTask
class EnhancedRetryMixin:
    """Mixin to add enhanced retry logic with dead letter queue support"""
    
    def should_retry(self) -> bool:
        """Determine if the task should be retried"""
        if self.status == 'failed' and self.retry_count < self.max_retries:
            return True
        return False
    
    def handle_failure(self, error_message: str, failure_type: str = 'unknown') -> None:
        """Handle task failure with dead letter queue support"""
        self.status = 'failed'
        self.error_message = error_message
        self.last_attempt = timezone.now()
        
        # Check if we've exceeded max retries
        if self.retry_count >= self.max_retries:
            # Add to dead letter queue
            try:
                DeadLetterQueueManager.add_to_dead_letter_queue(
                    self, error_message, failure_type
                )
                # Mark as cancelled since it's now in DLQ
                self.status = 'cancelled'
                self.cancelled_at = timezone.now()
            except Exception as dlq_error:
                # If we can't add to DLQ, at least log it
                print(f"Failed to add task {self.id} to dead letter queue: {dlq_error}")
        
        self.save()
    
    def retry_with_backoff(self) -> bool:
        """Retry with exponential backoff"""
        if not self.should_retry():
            return False
        
        # Calculate backoff delay (exponential with jitter)
        import random
        base_delay = 60  # 1 minute base delay
        max_delay = 3600  # 1 hour max delay
        
        delay = min(base_delay * (2 ** self.retry_count), max_delay)
        jitter = random.uniform(0.1, 0.3) * delay
        total_delay = delay + jitter
        
        # Schedule retry
        from datetime import timedelta
        self.scheduled_time = timezone.now() + timedelta(seconds=total_delay)
        self.retry_count += 1
        self.status = 'retrying'
        self.save()
        
        return True