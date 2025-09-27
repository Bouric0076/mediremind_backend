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
from .google_calendar_service import GoogleCalendarService, CalendarErrorCodes
from .token_refresh import TokenRefreshManager

# Configure dedicated logger for calendar integration views
logger = logging.getLogger(__name__)
calendar_views_logger = logging.getLogger('calendar_integration.views')

# Configure console handler if not already configured
if not calendar_views_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    calendar_views_logger.addHandler(console_handler)
    calendar_views_logger.setLevel(logging.DEBUG)
    calendar_views_logger.propagate = False


class CalendarIntegrationsView(APIView):
    """
    API endpoint for managing calendar integrations
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all user's calendar integrations"""
        calendar_views_logger.info(f"Fetching calendar integrations for user: {request.user.id}")
        
        try:
            integrations = CalendarIntegration.objects.filter(user=request.user)
            calendar_views_logger.debug(f"Found {integrations.count()} integrations for user {request.user.id}")
            
            # Return standardized format matching frontend CalendarIntegration interface
            integrations_data = []
            for integration in integrations:
                calendar_views_logger.debug(f"Processing integration {integration.id} - provider: {integration.provider}, status: {integration.status}")
                integrations_data.append({
                    'id': integration.id,
                    'user_id': str(request.user.id),
                    'provider': integration.provider,
                    'calendar_id': integration.calendar_id,
                    'calendar_name': integration.calendar_name,
                    'status': integration.status,
                    'sync_enabled': integration.sync_enabled,
                    'last_sync_at': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                    'access_token': '',  # Don't expose tokens in response
                    'refresh_token': '',  # Don't expose tokens in response
                    'token_expiry': integration.token_expiry.isoformat() if integration.token_expiry else None,
                    'sync_status': integration.status,
                    'last_sync': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                    'next_sync': integration.next_sync_at.isoformat() if integration.next_sync_at else None,
                    'created_at': integration.created_at.isoformat(),
                    'updated_at': integration.updated_at.isoformat()
                })
            
            calendar_views_logger.info(f"Successfully returned {len(integrations_data)} integrations for user {request.user.id}")
            return Response(integrations_data)
            
        except Exception as e:
            calendar_views_logger.error(f"Error fetching integrations for user {request.user.id if request.user.is_authenticated else 'anonymous'}: {e}", exc_info=True)
            logger.error(f"Error fetching integrations: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Initiate OAuth flow for a calendar provider"""
        try:
            provider = request.data.get('provider')
            redirect_uri = request.data.get('redirect_uri', 'http://localhost:3000/settings')
            
            if not provider:
                return Response({
                    'success': False,
                    'error': 'Provider is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if provider == 'google':
                service = GoogleCalendarService()
                auth_url = service.get_authorization_url(
                    provider_profile_id=request.user.id,
                    redirect_uri=redirect_uri
                )
                
                return Response({
                    'success': True,
                    'authorization_url': auth_url,
                    'provider': provider
                })
            
            return Response({
                'success': False,
                'error': 'Provider not supported'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error initiating OAuth: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """Delete a calendar integration"""
        try:
            integration_id = request.data.get('integration_id')
            
            if not integration_id:
                return Response({
                    'success': False,
                    'error': 'Integration ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            integration = CalendarIntegration.objects.get(
                id=integration_id,
                user=request.user
            )
            
            integration.delete()
            
            return Response({
                'success': True,
                'message': 'Integration deleted successfully'
            })
            
        except CalendarIntegration.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Integration not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting integration: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarOAuthCallbackView(APIView):
    """
    Generic OAuth callback handler for all calendar providers
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle OAuth callback for any supported provider"""
        calendar_views_logger.info(f"Processing OAuth callback for user {request.user.id}")
        
        try:
            provider = request.data.get('provider')
            authorization_code = request.data.get('code')
            state = request.data.get('state')
            
            calendar_views_logger.debug(f"OAuth callback data - provider: {provider}, has_code: {bool(authorization_code)}, has_state: {bool(state)}")
            
            if not all([provider, authorization_code, state]):
                calendar_views_logger.warning(f"Missing OAuth callback parameters - provider: {provider}, code: {bool(authorization_code)}, state: {bool(state)}")
                return Response({
                    'success': False,
                    'error': 'Missing required parameters'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if provider == 'google':
                calendar_views_logger.debug(f"Processing Google OAuth callback for user {request.user.id}")
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
                
                calendar_views_logger.info(f"Calendar integration {'created' if created else 'updated'} for user {request.user.id} - provider: {provider}, calendar_id: {token_data['calendar_id']}")
                
                # Schedule first sync
                integration.schedule_next_sync(minutes=5)
                calendar_views_logger.debug(f"Scheduled first sync for integration {integration.id} in 5 minutes")
                
                # Return standardized response format matching frontend expectations
                response_data = {
                    'id': integration.id,
                    'user_id': str(request.user.id),
                    'provider': integration.provider,
                    'calendar_id': integration.calendar_id,
                    'calendar_name': integration.calendar_name,
                    'status': integration.status,
                    'sync_enabled': integration.sync_enabled,
                    'last_sync_at': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                    'access_token': '',  # Don't expose tokens in response
                    'refresh_token': '',  # Don't expose tokens in response
                    'token_expiry': integration.token_expiry.isoformat() if integration.token_expiry else None,
                    'sync_status': integration.status,
                    'last_sync': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                    'next_sync': integration.next_sync_at.isoformat() if integration.next_sync_at else None,
                    'created_at': integration.created_at.isoformat(),
                    'updated_at': integration.updated_at.isoformat()
                }
                
                calendar_views_logger.info(f"Successfully processed OAuth callback for user {request.user.id}")
                return Response(response_data)
            
            calendar_views_logger.warning(f"Unsupported provider in OAuth callback: {provider}")
            return Response({
                'success': False,
                'error': 'Provider not supported'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            calendar_views_logger.error(f"OAuth callback error for user {request.user.id}: {e}", exc_info=True)
            logger.error(f"OAuth callback error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleCalendarAuthView(APIView):
    """
    Google Calendar specific authentication endpoint with enhanced security
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Initiate Google Calendar OAuth flow via GET request"""
        try:
            user = request.user
            
            service = GoogleCalendarService()
            redirect_uri = request.GET.get('redirect_uri', 'http://localhost:8000/api/calendar/google/callback/')
            
            # Generate secure state token
            state_token = service.generate_state_token(user.id)
            
            # Store state in session for validation
            request.session['oauth_state'] = state_token
            request.session['oauth_user_id'] = user.id
            request.session.save()
            
            auth_url = service.get_authorization_url(
                provider_profile_id=user.id,
                redirect_uri=redirect_uri,
                state=state_token
            )
            
            from django.shortcuts import redirect
            return redirect(auth_url)
            
        except Exception as e:
            logger.error(f"Error initiating Google auth: {e}")
            return Response({
                'success': False,
                'error': 'Failed to initiate OAuth flow',
                'error_code': CalendarErrorCodes.OAUTH_INITIATION_FAILED
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Initiate Google Calendar OAuth flow with enhanced security"""
        try:
            logger.info("Starting Google OAuth initiation")
            user = request.user
            logger.info(f"User: {user.id}, Email: {user.email}")
            
            service = GoogleCalendarService()
            redirect_uri = request.data.get('redirect_uri', 'http://localhost:8000/api/calendar/google/callback/')
            logger.info(f"Redirect URI: {redirect_uri}")
            
            # Generate secure state token for authenticated user
            logger.info("Generating state token...")
            state_token = service.generate_state_token(user.id)
            logger.info(f"State token generated: {state_token}")
            
            # Store state in session for validation
            logger.info("Storing state in session...")
            request.session['oauth_state'] = state_token
            request.session['oauth_user_id'] = str(user.id)  # Convert UUID to string for session storage
            request.session.save()
            logger.info("Session saved successfully")
            
            logger.info("Getting authorization URL...")
            auth_url_response = service.get_authorization_url(
                provider_profile_id=user.id,
                redirect_uri=redirect_uri,
                state=state_token
            )
            logger.info(f"Authorization URL response: {auth_url_response}")
            
            # Check if the service returned an error
            if not auth_url_response.get('success'):
                logger.error(f"Service returned error: {auth_url_response}")
                return Response({
                    'success': False,
                    'error': auth_url_response.get('error', 'Failed to generate authorization URL'),
                    'error_code': auth_url_response.get('error_code', CalendarErrorCodes.OAUTH_INITIATION_FAILED)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Extract the actual authorization URL string
            authorization_url = auth_url_response.get('authorization_url')
            logger.info(f"Extracted authorization URL: {authorization_url}")
            
            return Response({
                'success': True,
                'authorization_url': authorization_url,
                'provider': 'google',
                'state': state_token
            })
            
        except Exception as e:
            logger.error(f"Error initiating Google auth: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception args: {e.args}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': 'Failed to initiate OAuth flow',
                'error_code': CalendarErrorCodes.OAUTH_INITIATION_FAILED
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleCalendarCallbackView(APIView):
    """
    Google Calendar OAuth callback handler with enhanced security and error handling
    """
    permission_classes = []  # Allow unauthenticated access for OAuth callback
    
    def get(self, request):
        """Handle Google Calendar OAuth callback (GET request from Google)"""
        try:
            code = request.GET.get('code')
            state = request.GET.get('state')
            error = request.GET.get('error')
            
            integration_data = None
            
            # Enhanced session debugging
            logger.info(f"OAuth callback received - Code: {'present' if code else 'missing'}, State: {state[:20] if state else 'missing'}")
            logger.info(f"Session key: {request.session.session_key}")
            logger.info(f"Session data keys: {list(request.session.keys())}")
            logger.info(f"Session cookie age: {request.session.get_expiry_age()}")
            
            # Check if session exists and create if needed
            if not request.session.session_key:
                request.session.create()
                logger.info(f"Created new session: {request.session.session_key}")
            
            if code and not error:
                try:
                    service = GoogleCalendarService()
                    
                    # First, try to find the session with the matching state token
                    user_id = None
                    session_state = request.session.get('oauth_state')
                    session_user_id = request.session.get('oauth_user_id')
                    
                    logger.info(f"Current session state: {session_state[:20] if session_state else 'None'}")
                    logger.info(f"Current session user ID: {session_user_id}")
                    logger.info(f"Provided state: {state[:20] if state else 'None'}")
                    
                    # Validate state parameter (check both cache and session)
                    state_valid = service.validate_state_token(state)
                    if state_valid:
                        logger.info("State validated via cache")
                        logger.info(f"State validation data: {state_valid}")
                        # Extract user_id from validated state data
                        user_id = state_valid.get('provider_profile_id')
                        logger.info(f"User ID from validated state: {user_id}")
                        
                        # If we don't have user_id from cache, try session as fallback
                        if not user_id:
                            user_id = session_user_id
                            logger.info(f"Fallback to session user ID: {user_id}")
                    else:
                        logger.info("Cache validation failed, checking session...")
                        
                        if session_state == state and session_user_id:
                            logger.info(f"State token validated via current session: {state[:20]}...")
                            state_valid = True
                            user_id = session_user_id
                        else:
                            # Try to find session by state token across all active sessions
                            logger.info("Attempting cross-session state validation...")
                            from django.contrib.sessions.models import Session
                            from django.utils import timezone
                            
                            active_sessions = Session.objects.filter(expire_date__gt=timezone.now())
                            logger.info(f"Found {active_sessions.count()} active sessions")
                            
                            for session_obj in active_sessions:
                                try:
                                    session_data = session_obj.get_decoded()
                                    stored_state = session_data.get('oauth_state')
                                    stored_user_id = session_data.get('oauth_user_id')
                                    
                                    if stored_state == state and stored_user_id:
                                        logger.info(f"Found matching state in session: {session_obj.session_key[:10]}...")
                                        logger.info(f"Matching user ID: {stored_user_id}")
                                        
                                        # Copy session data to current request
                                        request.session['oauth_state'] = stored_state
                                        request.session['oauth_user_id'] = stored_user_id
                                        request.session.save()
                                        
                                        state_valid = True
                                        user_id = stored_user_id
                                        break
                                except Exception as session_error:
                                    logger.warning(f"Error decoding session {session_obj.session_key}: {session_error}")
                                    continue
                            
                            if not state_valid:
                                logger.warning(f"Invalid state token in OAuth callback: {state[:20] if state else 'None'}")
                                error = "Invalid or expired state parameter"
                    
                    if state_valid and user_id:
                        logger.info(f"Processing OAuth callback for user: {user_id}")
                        
                        # Process OAuth callback with user ID from session
                        result = service.handle_oauth_callback_with_user(
                            authorization_code=code,
                            state=state,
                            user_id=user_id,
                            redirect_uri='http://localhost:8000/api/calendar/google/callback/'
                        )
                        
                        # Process result if callback was successful
                        if result and result.get('success'):
                            logger.info("OAuth callback successful, processing integration data")
                            integration_data = {
                                'provider_profile_id': result.get('provider_profile_id'),
                                'message': result.get('message', 'Google Calendar connected successfully')
                            }
                            # Clear OAuth session data after successful completion
                            request.session.pop('oauth_state', None)
                            request.session.pop('oauth_user_id', None)
                            request.session.save()
                        elif result:
                            logger.error(f"OAuth callback failed: {result.get('error')}")
                            error = result.get('error', 'OAuth processing failed')
                        else:
                            logger.error("OAuth callback returned no result")
                            error = "OAuth processing failed - no result returned"
                    elif state_valid and not user_id:
                        logger.error("State validated but no user ID found")
                        error = "Session expired - user context lost"
                    else:
                        logger.error("State validation failed")
                        error = "Invalid or expired state parameter"
                            
                except Exception as integration_error:
                    logger.error(f"Failed to process OAuth callback: {integration_error}")
                    error = "Failed to process OAuth callback"
            
            # Render OAuth callback page for popup communication
            return render(request, 'oauth_callback.html', {
                'code': code,
                'state': state,
                'error': error,
                'integration_data': integration_data
            })
            
        except Exception as e:
            logger.error(f"Google OAuth callback error: {e}")
            return render(request, 'oauth_callback.html', {
                'error': 'OAuth callback processing failed'
            })
    
    def post(self, request):
        """Handle Google Calendar OAuth callback with authentication"""
        try:
            code = request.data.get('code')
            state = request.data.get('state')
            
            if not code:
                return Response({
                    'success': False,
                    'error': 'Authorization code required',
                    'error_code': CalendarErrorCodes.MISSING_AUTH_CODE
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not state:
                return Response({
                    'success': False,
                    'error': 'State parameter required',
                    'error_code': CalendarErrorCodes.MISSING_STATE_PARAMETER
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get authenticated user
            from authentication.middleware import get_request_user
            user = get_request_user(request)
            
            if not user:
                return Response({
                    'success': False,
                    'error': 'User must be authenticated to complete calendar integration',
                    'error_code': CalendarErrorCodes.AUTHENTICATION_REQUIRED,
                    'redirect_to_login': True
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            service = GoogleCalendarService()
            
            # Validate state parameter
            if not service.validate_state_token(state):
                return Response({
                    'success': False,
                    'error': 'Invalid state parameter',
                    'error_code': CalendarErrorCodes.INVALID_STATE_PARAMETER
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process OAuth callback
            result = service.handle_oauth_callback(
                authorization_code=code,
                state=state,
                redirect_uri='http://localhost:8000/api/calendar/google/callback/'
            )
            
            if not result['success']:
                return Response({
                    'success': False,
                    'error': result['error'],
                    'error_code': result.get('error_code', CalendarErrorCodes.OAUTH_CALLBACK_FAILED)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token_data = result['data']
            
            # Create or update integration
            integration, created = CalendarIntegration.objects.update_or_create(
                user=user,
                provider='google',
                calendar_id=token_data['calendar_id'],
                defaults={
                    'calendar_name': token_data['calendar_name'],
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data['refresh_token'],
                    'token_expiry': datetime.fromisoformat(token_data['token_expiry']) if token_data['token_expiry'] else None,
                    'status': 'active',
                    'sync_enabled': False  # Default to disabled
                }
            )
            
            # Log successful integration
            logger.info(f"Calendar integration {'created' if created else 'updated'} for user {user.id}")
            
            # Return standardized response format
            return Response({
                'success': True,
                'integration': {
                    'id': integration.id,
                    'user_id': str(user.id),
                    'provider': integration.provider,
                    'calendar_id': integration.calendar_id,
                    'calendar_name': integration.calendar_name,
                    'status': integration.status,
                    'sync_enabled': integration.sync_enabled,
                    'last_sync_at': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                    'token_expiry': integration.token_expiry.isoformat() if integration.token_expiry else None,
                    'created_at': integration.created_at.isoformat(),
                    'updated_at': integration.updated_at.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Google OAuth callback error: {e}")
            return Response({
                'success': False,
                'error': 'OAuth callback processing failed',
                'error_code': CalendarErrorCodes.OAUTH_CALLBACK_FAILED
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarEventsListView(APIView):
    """
    List all calendar events across all integrations
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get events from all user's calendar integrations"""
        try:
            # Get date range from query params
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Get all user's integrations
            integrations = CalendarIntegration.objects.filter(
                user=request.user,
                status='active'
            )
            
            all_events = []
            
            for integration in integrations:
                events_query = integration.events.all()
                
                if start_date:
                    events_query = events_query.filter(start_time__gte=start_date)
                if end_date:
                    events_query = events_query.filter(end_time__lte=end_date)
                
                for event in events_query[:50]:  # Limit per integration
                    all_events.append({
                        'id': event.id,
                        'external_id': event.external_event_id,
                        'title': event.title,
                        'description': event.description,
                        'start_time': event.start_time.isoformat(),
                        'end_time': event.end_time.isoformat(),
                        'location': event.location,
                        'is_medical_appointment': event.is_medical_appointment,
                        'integration_id': integration.id,
                        'calendar_name': integration.calendar_name,
                        'provider': integration.provider,
                        'created_at': event.created_at.isoformat()
                    })
            
            # Sort by start time
            all_events.sort(key=lambda x: x['start_time'])
            
            return Response({
                'success': True,
                'events': all_events,
                'total_count': len(all_events),
                'integrations_count': integrations.count()
            })
            
        except Exception as e:
            logger.error(f"Error fetching events list: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarSyncView(APIView):
    """
    Manual calendar sync operations
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, integration_id):
        """Trigger manual sync for a specific integration"""
        calendar_views_logger.info(f"Manual sync requested for integration {integration_id} by user {request.user.id}")
        
        try:
            integration = get_object_or_404(
                CalendarIntegration,
                id=integration_id,
                user=request.user
            )
            
            calendar_views_logger.debug(f"Found integration {integration_id} - provider: {integration.provider}, status: {integration.status}")
            
            if integration.provider == 'google':
                calendar_views_logger.debug(f"Starting Google Calendar sync for integration {integration_id}")
                service = GoogleCalendarService(integration)
                sync_result = service.sync_events()
                
                # Update integration sync status
                integration.last_sync_at = timezone.now()
                integration.save()
                
                calendar_views_logger.info(f"Manual sync completed for integration {integration_id} - result: {sync_result}")
                
                return Response({
                    'success': True,
                    'sync_result': sync_result,
                    'integration_id': integration.id,
                    'last_sync_at': integration.last_sync_at.isoformat()
                })
            
            calendar_views_logger.warning(f"Unsupported provider for sync: {integration.provider}")
            return Response({
                'success': False,
                'error': 'Provider not supported for sync'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            calendar_views_logger.error(f"Error syncing calendar integration {integration_id} for user {request.user.id}: {e}", exc_info=True)
            logger.error(f"Error syncing calendar: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarSyncStatusView(APIView):
    """
    Get sync status for a specific integration
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, integration_id):
        """Get sync status for integration"""
        try:
            integration = get_object_or_404(
                CalendarIntegration,
                id=integration_id,
                user=request.user
            )
            
            # Get latest sync log
            latest_sync = CalendarSyncLog.objects.filter(
                integration=integration
            ).order_by('-created_at').first()
            
            # Check if sync is currently running
            is_syncing = latest_sync and latest_sync.status == 'in_progress'
            
            return Response({
                'success': True,
                'integration_id': integration.id,
                'status': integration.status,
                'sync_enabled': integration.sync_enabled,
                'last_sync_at': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                'next_sync_at': integration.next_sync_at.isoformat() if integration.next_sync_at else None,
                'is_syncing': is_syncing,
                'latest_sync': {
                    'id': latest_sync.id,
                    'status': latest_sync.status,
                    'sync_type': latest_sync.sync_type,
                    'events_processed': latest_sync.events_processed,
                    'events_added': latest_sync.events_added,
                    'events_updated': latest_sync.events_updated,
                    'conflicts_detected': latest_sync.conflicts_detected,
                    'error_message': latest_sync.error_message,
                    'created_at': latest_sync.created_at.isoformat(),
                    'completed_at': latest_sync.completed_at.isoformat() if latest_sync.completed_at else None
                } if latest_sync else None
            })
            
        except Exception as e:
            logger.error(f"Error fetching sync status: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarIntegrationDetailView(APIView):
    """
    Handle individual integration operations (update, delete)
    """
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, integration_id):
        """Update integration settings"""
        try:
            integration = get_object_or_404(
                CalendarIntegration,
                id=integration_id,
                user=request.user
            )
            
            # Update allowed fields
            allowed_fields = ['sync_enabled', 'calendar_name']
            for field in allowed_fields:
                if field in request.data:
                    setattr(integration, field, request.data[field])
            
            integration.save()
            
            return Response({
                'success': True,
                'integration': {
                    'id': integration.id,
                    'provider': integration.provider,
                    'calendar_name': integration.calendar_name,
                    'status': integration.status,
                    'sync_enabled': integration.sync_enabled,
                    'last_sync_at': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                    'created_at': integration.created_at.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error updating integration: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, integration_id):
        """Delete integration"""
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


class CalendarConflictsView(APIView):
    """
    Handle calendar conflicts
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all conflicts for user's integrations"""
        try:
            # Get user's integrations
            user_integrations = CalendarIntegration.objects.filter(user=request.user)
            
            # Get conflicts for these integrations
            conflicts = CalendarConflict.objects.filter(
                integration__in=user_integrations,
                status='pending'
            ).order_by('-created_at')
            
            conflicts_data = []
            for conflict in conflicts:
                conflicts_data.append({
                    'id': conflict.id,
                    'integration_id': conflict.integration.id,
                    'calendar_name': conflict.integration.calendar_name,
                    'provider': conflict.integration.provider,
                    'conflict_type': conflict.conflict_type,
                    'external_event_id': conflict.external_event_id,
                    'internal_event_id': conflict.internal_event_id,
                    'external_event_data': conflict.external_event_data,
                    'internal_event_data': conflict.internal_event_data,
                    'status': conflict.status,
                    'created_at': conflict.created_at.isoformat(),
                    'resolved_at': conflict.resolved_at.isoformat() if conflict.resolved_at else None
                })
            
            return Response({
                'success': True,
                'conflicts': conflicts_data,
                'total_count': len(conflicts_data)
            })
            
        except Exception as e:
            logger.error(f"Error fetching conflicts: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarConflictResolveView(APIView):
    """
    Resolve specific calendar conflicts
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, conflict_id):
        """Resolve a calendar conflict"""
        try:
            conflict = get_object_or_404(
                CalendarConflict,
                id=conflict_id,
                integration__user=request.user
            )
            
            resolution = request.data.get('resolution')
            if resolution not in ['keep_internal', 'keep_external', 'merge']:
                return Response({
                    'success': False,
                    'error': 'Invalid resolution type'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Apply resolution logic
            if resolution == 'keep_internal':
                # Keep the internal event, ignore external
                conflict.resolution = 'keep_internal'
                conflict.status = 'resolved'
                
            elif resolution == 'keep_external':
                # Update internal event with external data
                if conflict.internal_event_id:
                    try:
                        from appointments.models import Appointment
                        appointment = Appointment.objects.get(id=conflict.internal_event_id)
                        external_data = conflict.external_event_data
                        
                        # Update appointment with external event data
                        if 'title' in external_data:
                            appointment.title = external_data['title']
                        if 'start_time' in external_data:
                            appointment.appointment_date = datetime.fromisoformat(external_data['start_time'])
                        if 'description' in external_data:
                            appointment.notes = external_data['description']
                        
                        appointment.save()
                        
                    except Exception as update_error:
                        logger.error(f"Error updating appointment: {update_error}")
                
                conflict.resolution = 'keep_external'
                conflict.status = 'resolved'
                
            elif resolution == 'merge':
                # Create merged event (simplified implementation)
                conflict.resolution = 'merge'
                conflict.status = 'resolved'
            
            conflict.resolved_at = timezone.now()
            conflict.save()
            
            return Response({
                'success': True,
                'conflict_id': conflict.id,
                'resolution': resolution,
                'resolved_at': conflict.resolved_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CalendarEventsView(APIView):
    """
    Handle events for a specific integration
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, integration_id):
        """Get events for a specific integration"""
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
            
            events_data = []
            for event in events_query.order_by('start_time')[:100]:  # Limit results
                events_data.append({
                    'id': event.id,
                    'external_id': event.external_event_id,
                    'title': event.title,
                    'description': event.description,
                    'start_time': event.start_time.isoformat(),
                    'end_time': event.end_time.isoformat(),
                    'location': event.location,
                    'is_medical_appointment': event.is_medical_appointment,
                    'created_at': event.created_at.isoformat(),
                    'updated_at': event.updated_at.isoformat()
                })
            
            return Response({
                'success': True,
                'events': events_data,
                'integration': {
                    'id': integration.id,
                    'provider': integration.provider,
                    'calendar_name': integration.calendar_name,
                    'status': integration.status
                },
                'total_count': len(events_data)
            })
            
        except Exception as e:
            logger.error(f"Error fetching integration events: {e}")
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


class CalendarTokenRefreshView(APIView):
    """
    Handle token refresh for calendar integrations with enhanced error handling
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, integration_id):
        """Refresh access token for a specific integration"""
        try:
            integration = get_object_or_404(
                CalendarIntegration,
                id=integration_id,
                user=request.user
            )
            
            service = GoogleCalendarService()
            
            # Use the enhanced token refresh from GoogleCalendarService
            result = service.refresh_integration_token(integration)
            
            if result['success']:
                # Reload integration to get updated token data
                integration.refresh_from_db()
                
                logger.info(f"Token refreshed successfully for integration {integration_id}")
                
                # Return updated integration data
                return Response({
                    'success': True,
                    'integration': {
                        'id': str(integration.id),
                        'user_id': integration.user.id,
                        'provider': integration.provider,
                        'calendar_id': integration.calendar_id,
                        'calendar_name': integration.calendar_name,
                        'status': integration.status,
                        'sync_enabled': integration.sync_enabled,
                        'last_sync_at': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                        'token_expiry': integration.token_expiry.isoformat() if integration.token_expiry else None,
                        'sync_status': integration.sync_status,
                        'last_sync': integration.last_sync_at.isoformat() if integration.last_sync_at else None,
                        'next_sync': integration.next_sync_at.isoformat() if integration.next_sync_at else None,
                        'created_at': integration.created_at.isoformat(),
                        'updated_at': integration.updated_at.isoformat(),
                    }
                })
            else:
                logger.error(f"Token refresh failed for integration {integration_id}: {result['error']}")
                
                # Update integration status if token refresh failed
                if result.get('error_code') == CalendarErrorCodes.INVALID_REFRESH_TOKEN:
                    integration.status = 'token_expired'
                    integration.save()
                
                return Response({
                    'success': False,
                    'error': result['error'],
                    'error_code': result.get('error_code', CalendarErrorCodes.TOKEN_REFRESH_FAILED),
                    'requires_reauth': result.get('error_code') == CalendarErrorCodes.INVALID_REFRESH_TOKEN
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except CalendarIntegration.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Integration not found',
                'error_code': CalendarErrorCodes.INTEGRATION_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error refreshing token for integration {integration_id}: {e}")
            return Response({
                'success': False,
                'error': 'Token refresh failed',
                'error_code': CalendarErrorCodes.TOKEN_REFRESH_FAILED
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)