"""
Calendar Integration Models - MVP Version
Simplified models for basic calendar integration functionality.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import json


class CalendarProvider(models.TextChoices):
    """Supported calendar providers for MVP"""
    GOOGLE = 'google', 'Google Calendar'
    OUTLOOK = 'outlook', 'Microsoft Outlook'


class SyncStatus(models.TextChoices):
    """Calendar sync status options"""
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    ERROR = 'error', 'Error'
    PENDING = 'pending', 'Pending Setup'


class CalendarIntegration(models.Model):
    """
    MVP model for storing calendar integration configurations.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_integrations')
    provider = models.CharField(max_length=20, choices=CalendarProvider.choices)
    calendar_id = models.CharField(max_length=255, help_text="External calendar ID")
    calendar_name = models.CharField(max_length=255, default="Primary Calendar")
    
    # OAuth tokens
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    token_expiry = models.DateTimeField(blank=True, null=True)
    
    # Sync settings
    status = models.CharField(max_length=20, choices=SyncStatus.choices, default=SyncStatus.PENDING)
    sync_enabled = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(blank=True, null=True)
    next_sync_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'provider', 'calendar_id']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_provider_display()} - {self.calendar_name}"
    
    def is_token_expired(self):
        """Check if access token is expired"""
        if not self.token_expiry:
            return False
        return timezone.now() >= self.token_expiry
    
    def schedule_next_sync(self, minutes=30):
        """Schedule next sync"""
        self.next_sync_at = timezone.now() + timedelta(minutes=minutes)
        self.save(update_fields=['next_sync_at'])


class ExternalCalendarEvent(models.Model):
    """
    MVP model for storing external calendar events.
    """
    integration = models.ForeignKey(CalendarIntegration, on_delete=models.CASCADE, related_name='events')
    external_event_id = models.CharField(max_length=255, help_text="ID from external calendar")
    
    # Event details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    
    # Classification
    is_medical_appointment = models.BooleanField(default=False)
    
    # Sync metadata
    last_modified = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['integration', 'external_event_id']
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"


class CalendarSyncLog(models.Model):
    """
    MVP model for tracking sync operations.
    """
    integration = models.ForeignKey(CalendarIntegration, on_delete=models.CASCADE, related_name='sync_logs')
    
    # Sync details
    sync_type = models.CharField(max_length=20, choices=[
        ('full', 'Full Sync'),
        ('incremental', 'Incremental Sync')
    ], default='incremental')
    
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success')
    ])
    
    # Statistics
    events_processed = models.IntegerField(default=0)
    events_created = models.IntegerField(default=0)
    events_updated = models.IntegerField(default=0)
    conflicts_detected = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.FloatField(blank=True, null=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.integration} - {self.sync_type} - {self.status}"


class CalendarConflict(models.Model):
    """
    MVP model for tracking calendar conflicts.
    """
    integration = models.ForeignKey(CalendarIntegration, on_delete=models.CASCADE, related_name='conflicts')
    external_event = models.ForeignKey(ExternalCalendarEvent, on_delete=models.CASCADE)
    
    # Conflict details
    conflict_type = models.CharField(max_length=20, choices=[
        ('overlap', 'Time Overlap'),
        ('duplicate', 'Duplicate Event')
    ])
    
    mediremind_appointment_id = models.CharField(max_length=255, blank=True)
    conflict_details = models.JSONField(default=dict)
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolution_action = models.CharField(max_length=50, blank=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Conflict: {self.external_event.title} - {self.conflict_type}"


class CalendarAvailability(models.Model):
    """
    MVP model for storing calculated availability.
    """
    integration = models.ForeignKey(CalendarIntegration, on_delete=models.CASCADE, related_name='availability')
    
    # Time slot
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Availability status
    is_available = models.BooleanField(default=True)
    availability_type = models.CharField(max_length=20, choices=[
        ('free', 'Free'),
        ('busy', 'Busy'),
        ('tentative', 'Tentative')
    ], default='free')
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['integration', 'date', 'start_time', 'end_time']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.integration.user.username} - {self.date} {self.start_time}-{self.end_time} ({self.availability_type})"