"""
Calendar Integration Views - MVP Version
Simplified API endpoints for basic calendar integration functionality.
"""

import logging
import json
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import CalendarIntegration, ExternalCalendarEvent, CalendarSyncLog, CalendarConflict
from .google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)


class CalendarDashboardView(TemplateView):
    """
    Dashboard view for calendar integration management
    """
    template_name = 'calendar_integrations/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Calendar Integration Dashboard'
        return context


class CalendarIntegrationsView(APIView):
    """
    MVP API for managing calendar integrations.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List user's calendar integrations"""
        try:
            integrations = CalendarIntegration.objects.filter(user=request.user)
            
            data = []
            for integration in integrations:
                data.append({
                    'id': integration.id,
                    'provider': integration.provider,
                    'calendar_name': integration.calendar_name,
                    'status': integration.status,
                    'sync_enabled': integration.sync_enabled,
                    'last_sync_at': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                    'created_at': integration.created_at.isoformat()
                })
            
            return Response({
                'success': True,
                'integrations': data
            })
            
        except Exception as e:
            logger.error(f"Error fetching integrations: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create new calendar integration"""
        try:
            provider = request.data.get('provider')
            
            if provider not in ['google', 'outlook']:
                return Response({
                    'success': False,
                    'error': 'Unsupported provider'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if provider == 'google':
                service = GoogleCalendarService()
                auth_url = service.get_authorization_url(
                    provider_profile_id=request.user.id,
                    redirect_uri=request.data.get('redirect_uri')
                )
                
                return Response({
                    'success': True,
                    'authorization_url': auth_url,
                    'provider': provider
                })
            
            return Response({
                'success': False,
                'error': 'Provider not implemented yet'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
            
        except Exception as e:
            logger.error(f"Error creating integration: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, integration_id):
        """Delete calendar integration"""
        try:
            integration = get_object_or_404(
                CalendarIntegration, 
                id=integration_id, 
                user=request.user
            )
            
            integration.delete()
            
            return Response({
                'success': True,
                'message': 'Integration deleted successfully'
            })
            
        except Exception as e:
            logger.error(f"Error deleting integration: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarOAuthCallbackView(APIView):
    """
    MVP OAuth callback handler for calendar providers.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle OAuth callback"""
        try:
            provider = request.data.get('provider')
            authorization_code = request.data.get('code')
            state = request.data.get('state')
            
            if not all([provider, authorization_code, state]):
                return Response({
                    'success': False,
                    'error': 'Missing required parameters'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if provider == 'google':
                service = GoogleCalendarService()
                token_data = service.handle_oauth_callback(
                    authorization_code=authorization_code,
                    state=state,
                    redirect_uri=request.data.get('redirect_uri')
                )
                
                # Create or update integration
                integration, created = CalendarIntegration.objects.update_or_create(
                    user=request.user,
                    provider=provider,
                    calendar_id=token_data['calendar_id'],
                    defaults={
                        'calendar_name': token_data['calendar_name'],
                        'access_token': token_data['access_token'],
                        'refresh_token': token_data['refresh_token'],
                        'token_expiry': datetime.fromisoformat(token_data['token_expiry']) if token_data['token_expiry'] else None,
                        'status': 'active',
                        'sync_enabled': True
                    }
                )
                
                # Schedule first sync
                integration.schedule_next_sync(minutes=5)
                
                return Response({
                    'success': True,
                    'integration_id': integration.id,
                    'calendar_name': integration.calendar_name,
                    'created': created
                })
            
            return Response({
                'success': False,
                'error': 'Provider not supported'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarSyncView(APIView):
    """
    MVP calendar sync operations.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, integration_id):
        """Trigger manual sync"""
        try:
            integration = get_object_or_404(
                CalendarIntegration,
                id=integration_id,
                user=request.user
            )
            
            if integration.provider == 'google':
                service = GoogleCalendarService(integration)
                
                # Test connection first
                connection_test = service.test_connection()
                if not connection_test['success']:
                    return Response({
                        'success': False,
                        'error': f"Connection failed: {connection_test['error']}"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Fetch events
                events = service.fetch_events()
                
                # Process events
                events_created = 0
                events_updated = 0
                
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
                            'is_medical_appointment': self._is_medical_appointment(event_data)
                        }
                    )
                    
                    if created:
                        events_created += 1
                    else:
                        events_updated += 1
                
                # Update integration
                integration.last_sync_at = timezone.now()
                integration.status = 'active'
                integration.schedule_next_sync()
                
                # Create sync log
                CalendarSyncLog.objects.create(
                    integration=integration,
                    sync_type='manual',
                    status='success',
                    events_processed=len(events),
                    events_created=events_created,
                    events_updated=events_updated,
                    started_at=timezone.now(),
                    completed_at=timezone.now()
                )
                
                return Response({
                    'success': True,
                    'events_processed': len(events),
                    'events_created': events_created,
                    'events_updated': events_updated,
                    'last_sync_at': integration.last_sync_at.isoformat()
                })
            
            return Response({
                'success': False,
                'error': 'Provider not supported'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _is_medical_appointment(self, event_data):
        """Simple medical appointment detection"""
        medical_keywords = [
            'appointment', 'doctor', 'clinic', 'hospital', 'medical',
            'checkup', 'consultation', 'patient', 'treatment', 'therapy'
        ]
        
        text_to_check = (
            event_data.get('title', '') + ' ' + 
            event_data.get('description', '') + ' ' +
            event_data.get('location', '')
        ).lower()
        
        return any(keyword in text_to_check for keyword in medical_keywords)


class CalendarEventsView(APIView):
    """
    MVP calendar events management.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, integration_id):
        """Get events from calendar integration"""
        try:
            integration = get_object_or_404(
                CalendarIntegration,
                id=integration_id,
                user=request.user
            )
            
            # Get date range from query params
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            events_query = integration.events.all()
            
            if start_date:
                events_query = events_query.filter(start_time__gte=start_date)
            if end_date:
                events_query = events_query.filter(end_time__lte=end_date)
            
            events = []
            for event in events_query[:100]:  # Limit to 100 events
                events.append({
                    'id': event.id,
                    'external_id': event.external_event_id,
                    'title': event.title,
                    'description': event.description,
                    'start_time': event.start_time.isoformat(),
                    'end_time': event.end_time.isoformat(),
                    'location': event.location,
                    'is_medical_appointment': event.is_medical_appointment,
                    'created_at': event.created_at.isoformat()
                })
            
            return Response({
                'success': True,
                'events': events,
                'total_count': events_query.count()
            })
            
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarConflictsView(APIView):
    """
    MVP calendar conflicts management.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get calendar conflicts for user"""
        try:
            conflicts = CalendarConflict.objects.filter(
                integration__user=request.user,
                is_resolved=False
            ).select_related('integration', 'external_event')
            
            data = []
            for conflict in conflicts:
                data.append({
                    'id': conflict.id,
                    'conflict_type': conflict.conflict_type,
                    'integration_id': conflict.integration.id,
                    'calendar_name': conflict.integration.calendar_name,
                    'external_event': {
                        'title': conflict.external_event.title,
                        'start_time': conflict.external_event.start_time.isoformat(),
                        'end_time': conflict.external_event.end_time.isoformat(),
                    },
                    'conflict_details': conflict.conflict_details,
                    'created_at': conflict.created_at.isoformat()
                })
            
            return Response({
                'success': True,
                'conflicts': data
            })
            
        except Exception as e:
            logger.error(f"Error fetching conflicts: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, conflict_id):
        """Resolve calendar conflict"""
        try:
            conflict = get_object_or_404(
                CalendarConflict,
                id=conflict_id,
                integration__user=request.user
            )
            
            resolution_action = request.data.get('action')
            
            if resolution_action not in ['ignore', 'reschedule', 'cancel']:
                return Response({
                    'success': False,
                    'error': 'Invalid resolution action'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            conflict.is_resolved = True
            conflict.resolution_action = resolution_action
            conflict.resolved_at = timezone.now()
            conflict.save()
            
            return Response({
                'success': True,
                'message': 'Conflict resolved successfully'
            })
            
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarAvailabilityView(APIView):
    """
    MVP calendar availability calculation.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get availability for user's calendars"""
        try:
            date_str = request.GET.get('date')
            if not date_str:
                return Response({
                    'success': False,
                    'error': 'Date parameter required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get all active integrations for user
            integrations = CalendarIntegration.objects.filter(
                user=request.user,
                status='active',
                sync_enabled=True
            )
            
            availability_data = {}
            
            for integration in integrations:
                # Get events for the date
                events = integration.events.filter(
                    start_time__date=target_date
                ).order_by('start_time')
                
                busy_slots = []
                for event in events:
                    busy_slots.append({
                        'start_time': event.start_time.time().strftime('%H:%M'),
                        'end_time': event.end_time.time().strftime('%H:%M'),
                        'title': event.title
                    })
                
                availability_data[integration.calendar_name] = {
                    'integration_id': integration.id,
                    'provider': integration.provider,
                    'busy_slots': busy_slots,
                    'last_sync': integration.last_sync_at.isoformat() if integration.last_sync_at else None
                }
            
            return Response({
                'success': True,
                'date': date_str,
                'availability': availability_data
            })
            
        except Exception as e:
            logger.error(f"Error calculating availability: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)