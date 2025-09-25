"""
Calendar Integration Tasks - MVP Version
Simplified background tasks for basic calendar integration functionality.
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from django.db import transaction

from .models import CalendarIntegration, ExternalCalendarEvent, CalendarSyncLog, CalendarConflict
from .google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_calendar_events(self, integration_id):
    """
    MVP task to sync events from external calendar.
    """
    try:
        integration = CalendarIntegration.objects.get(
            id=integration_id,
            status='active',
            sync_enabled=True
        )
        
        logger.info(f"Starting sync for integration {integration_id}")
        
        # Create sync log
        sync_log = CalendarSyncLog.objects.create(
            integration=integration,
            sync_type='automatic',
            status='running',
            started_at=timezone.now()
        )
        
        try:
            if integration.provider == 'google':
                service = GoogleCalendarService(integration)
                
                # Test connection
                connection_test = service.test_connection()
                if not connection_test['success']:
                    raise Exception(f"Connection failed: {connection_test['error']}")
                
                # Fetch events
                events = service.fetch_events()
                
                # Process events
                events_created = 0
                events_updated = 0
                conflicts_detected = 0
                
                with transaction.atomic():
                    for event_data in events:
                        external_event, created = ExternalCalendarEvent.objects.update_or_create(
                            integration=integration,
                            external_event_id=event_data['id'],
                            defaults={
                                'title': event_data['title'],
                                'description': event_data['description'],
                                'start_time': event_data['start_time'],
                                'end_time': event_data['end_time'],
                                'location': event_data['location'],
                                'last_modified': event_data['updated'] or timezone.now(),
                                'is_medical_appointment': _is_medical_appointment(event_data)
                            }
                        )
                        
                        if created:
                            events_created += 1
                        else:
                            events_updated += 1
                        
                        # Simple conflict detection
                        if external_event.is_medical_appointment:
                            conflicts = _detect_conflicts(external_event)
                            conflicts_detected += len(conflicts)
                
                # Update integration
                integration.last_sync_at = timezone.now()
                integration.schedule_next_sync()
                
                # Update sync log
                sync_log.status = 'success'
                sync_log.events_processed = len(events)
                sync_log.events_created = events_created
                sync_log.events_updated = events_updated
                sync_log.conflicts_detected = conflicts_detected
                sync_log.completed_at = timezone.now()
                sync_log.save()
                
                logger.info(f"Sync completed for integration {integration_id}: "
                           f"{events_created} created, {events_updated} updated, "
                           f"{conflicts_detected} conflicts")
                
                return {
                    'success': True,
                    'events_processed': len(events),
                    'events_created': events_created,
                    'events_updated': events_updated,
                    'conflicts_detected': conflicts_detected
                }
            
            else:
                raise Exception(f"Provider {integration.provider} not supported")
                
        except Exception as e:
            # Update sync log with error
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            # Update integration status
            integration.status = 'error'
            integration.save()
            
            raise e
            
    except CalendarIntegration.DoesNotExist:
        logger.error(f"Integration {integration_id} not found")
        return {'success': False, 'error': 'Integration not found'}
        
    except Exception as e:
        logger.error(f"Sync failed for integration {integration_id}: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries * 60  # 1, 2, 4 minutes
            raise self.retry(countdown=countdown, exc=e)
        
        return {'success': False, 'error': str(e)}


@shared_task
def detect_calendar_conflicts():
    """
    MVP task to detect conflicts across all active integrations.
    """
    try:
        logger.info("Starting conflict detection")
        
        # Get all medical appointments from last 7 days and next 30 days
        start_date = timezone.now() - timedelta(days=7)
        end_date = timezone.now() + timedelta(days=30)
        
        medical_events = ExternalCalendarEvent.objects.filter(
            is_medical_appointment=True,
            start_time__gte=start_date,
            start_time__lte=end_date,
            integration__status='active'
        ).select_related('integration')
        
        conflicts_detected = 0
        
        for event in medical_events:
            conflicts = _detect_conflicts(event)
            conflicts_detected += len(conflicts)
        
        logger.info(f"Conflict detection completed: {conflicts_detected} conflicts found")
        
        return {
            'success': True,
            'conflicts_detected': conflicts_detected
        }
        
    except Exception as e:
        logger.error(f"Conflict detection failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_sync_logs():
    """
    MVP task to clean up old sync logs.
    """
    try:
        # Delete sync logs older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        
        deleted_count = CalendarSyncLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old sync logs")
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Sync log cleanup failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def schedule_all_syncs():
    """
    MVP task to schedule sync for all active integrations.
    """
    try:
        integrations = CalendarIntegration.objects.filter(
            status='active',
            sync_enabled=True
        )
        
        scheduled_count = 0
        
        for integration in integrations:
            # Check if sync is due
            if integration.is_sync_due():
                sync_calendar_events.delay(integration.id)
                scheduled_count += 1
        
        logger.info(f"Scheduled sync for {scheduled_count} integrations")
        
        return {
            'success': True,
            'scheduled_count': scheduled_count
        }
        
    except Exception as e:
        logger.error(f"Sync scheduling failed: {e}")
        return {'success': False, 'error': str(e)}


# Helper functions

def _is_medical_appointment(event_data):
    """
    Simple medical appointment detection.
    """
    medical_keywords = [
        'appointment', 'doctor', 'clinic', 'hospital', 'medical',
        'checkup', 'consultation', 'patient', 'treatment', 'therapy',
        'dentist', 'physician', 'nurse', 'surgery', 'exam'
    ]
    
    text_to_check = (
        event_data.get('title', '') + ' ' + 
        event_data.get('description', '') + ' ' +
        event_data.get('location', '')
    ).lower()
    
    return any(keyword in text_to_check for keyword in medical_keywords)


def _detect_conflicts(external_event):
    """
    Simple conflict detection for medical appointments.
    """
    conflicts = []
    
    try:
        # Check for overlapping events in the same time slot
        overlapping_events = ExternalCalendarEvent.objects.filter(
            integration__user=external_event.integration.user,
            start_time__lt=external_event.end_time,
            end_time__gt=external_event.start_time
        ).exclude(id=external_event.id)
        
        for overlapping_event in overlapping_events:
            # Create conflict record
            conflict, created = CalendarConflict.objects.get_or_create(
                integration=external_event.integration,
                external_event=external_event,
                conflict_type='time_overlap',
                defaults={
                    'conflict_details': {
                        'overlapping_event_id': overlapping_event.id,
                        'overlapping_event_title': overlapping_event.title,
                        'overlap_start': max(external_event.start_time, overlapping_event.start_time).isoformat(),
                        'overlap_end': min(external_event.end_time, overlapping_event.end_time).isoformat()
                    }
                }
            )
            
            if created:
                conflicts.append(conflict)
                logger.info(f"Conflict detected: {external_event.title} overlaps with {overlapping_event.title}")
    
    except Exception as e:
        logger.error(f"Error detecting conflicts for event {external_event.id}: {e}")
    
    return conflicts