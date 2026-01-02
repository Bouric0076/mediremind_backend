from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from notifications.dead_letter_queue import EnhancedRetryMixin

class PushSubscription(models.Model):
    """Model to store web push subscriptions"""
    user_id = models.CharField(max_length=255)  # Supabase user ID
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=255)  # User's public key
    auth = models.CharField(max_length=255)  # User's auth secret
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_id', 'endpoint')
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['endpoint'])
        ]

    def to_subscription_info(self):
        """Convert to subscription info format for webpush"""
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh,
                'auth': self.auth
            }
        }


class ScheduledTask(EnhancedRetryMixin, models.Model):
    """Model for persistent task storage with enhanced retry logic"""
    
    TASK_TYPES = [
        ('reminder', 'Appointment Reminder'),
        ('confirmation', 'Appointment Confirmation'),
        ('update', 'Appointment Update'),
        ('cancellation', 'Appointment Cancellation'),
        ('no_show', 'No Show Notification'),
        ('manual', 'Manual Notification'),
        ('notification', 'Generic Notification'),
    ]
    
    DELIVERY_METHODS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    PRIORITIES = [
        (0, 'Urgent'),
        (1, 'High'),
        (2, 'Medium'),
        (3, 'Low'),
    ]
    
    STATUSES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    appointment_id = models.UUIDField()
    reminder_type = models.CharField(max_length=50, blank=True)
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHODS)
    scheduled_time = models.DateTimeField()
    priority = models.IntegerField(choices=PRIORITIES, default=2)
    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    error_message = models.TextField(blank=True, null=True)
    message_data = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    last_attempt = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'scheduled_time']),
            models.Index(fields=['appointment_id', 'status']),
            models.Index(fields=['delivery_method', 'status']),
            models.Index(fields=['priority', 'scheduled_time']),
            models.Index(fields=['created_at']),
            # Additional indexes for monitoring queries
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['task_type', 'status']),
            models.Index(fields=['delivery_method', 'created_at']),
            models.Index(fields=['scheduled_time', 'status']),
        ]
        ordering = ['priority', 'scheduled_time']
    
    def __str__(self):
        return f"{self.task_type} - {self.appointment_id} - {self.status}"
    
    def is_due(self):
        """Check if task is due for processing"""
        return self.scheduled_time <= timezone.now() and self.status == 'pending'
    
    def can_retry(self):
        """Check if task can be retried"""
        return self.retry_count < self.max_retries and self.status in ['failed', 'retrying']


class NotificationLog(models.Model):
    """Model to log all notification attempts"""
    
    STATUSES = [
        ('sent', 'Sent Successfully'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(ScheduledTask, on_delete=models.CASCADE, related_name='logs')
    appointment_id = models.UUIDField()
    patient_id = models.CharField(max_length=255)  # Supabase user ID
    provider_id = models.CharField(max_length=255, blank=True)  # Supabase user ID
    delivery_method = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUSES)
    error_message = models.TextField(blank=True, null=True)
    external_id = models.CharField(max_length=255, blank=True)  # External service message ID
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['appointment_id', 'created_at']),
            models.Index(fields=['patient_id', 'created_at']),
            models.Index(fields=['delivery_method', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['external_id']),
            # Additional indexes for monitoring queries
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['delivery_method', 'created_at']),
            models.Index(fields=['patient_id', 'status']),
            models.Index(fields=['appointment_id', 'status']),
            models.Index(fields=['task', 'status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.delivery_method} - {self.appointment_id} - {self.status}"


class SchedulerStats(models.Model):
    """Model to track scheduler performance statistics"""
    
    date = models.DateField(default=timezone.now)
    total_processed = models.IntegerField(default=0)
    successful = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    retried = models.IntegerField(default=0)
    cancelled = models.IntegerField(default=0)
    rate_limited = models.IntegerField(default=0)
    circuit_breaker_trips = models.IntegerField(default=0)
    
    # Performance metrics
    avg_processing_time = models.FloatField(default=0.0)  # in seconds
    max_queue_size = models.IntegerField(default=0)
    max_concurrent_tasks = models.IntegerField(default=0)
    
    # Delivery method breakdown
    email_sent = models.IntegerField(default=0)
    sms_sent = models.IntegerField(default=0)
    push_sent = models.IntegerField(default=0)
    whatsapp_sent = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('date',)
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"Stats for {self.date} - {self.total_processed} processed"