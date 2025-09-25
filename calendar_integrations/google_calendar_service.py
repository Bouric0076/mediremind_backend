"""
Google Calendar Integration Service - MVP Version
Handles OAuth authentication, token management, and basic calendar synchronization.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# MVP Configuration - simplified settings
GOOGLE_CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

GOOGLE_CLIENT_CONFIG = {
    'web': {
        'client_id': os.getenv('GOOGLE_CALENDAR_CLIENT_ID', ''),
        'client_secret': os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET', ''),
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'redirect_uris': [os.getenv('GOOGLE_CALENDAR_REDIRECT_URI', 'http://localhost:8000/api/calendar/oauth/callback/')]
    }
}


class GoogleCalendarService:
    """
    MVP Google Calendar service with essential functionality.
    """
    
    def __init__(self, integration=None):
        self.integration = integration
        self.service = None
        
    def get_authorization_url(self, provider_profile_id: int, redirect_uri: str = None) -> str:
        """
        Generate Google OAuth authorization URL.
        """
        try:
            if not GOOGLE_CLIENT_CONFIG['web']['client_id']:
                raise ValueError("Google Calendar Client ID not configured")
            
            flow = Flow.from_client_config(
                GOOGLE_CLIENT_CONFIG,
                scopes=GOOGLE_CALENDAR_SCOPES
            )
            
            flow.redirect_uri = redirect_uri or GOOGLE_CLIENT_CONFIG['web']['redirect_uris'][0]
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=str(provider_profile_id)  # Pass provider ID in state
            )
            
            logger.info(f"Generated authorization URL for provider {provider_profile_id}")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {e}")
            raise
    
    def handle_oauth_callback(self, authorization_code: str, state: str, redirect_uri: str = None) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for tokens.
        """
        try:
            flow = Flow.from_client_config(
                GOOGLE_CLIENT_CONFIG,
                scopes=GOOGLE_CALENDAR_SCOPES
            )
            
            flow.redirect_uri = redirect_uri or GOOGLE_CLIENT_CONFIG['web']['redirect_uris'][0]
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            # Get user info
            service = build('calendar', 'v3', credentials=credentials)
            calendar_list = service.calendarList().list().execute()
            
            primary_calendar = None
            for calendar in calendar_list.get('items', []):
                if calendar.get('primary'):
                    primary_calendar = calendar
                    break
            
            return {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None,
                'calendar_id': primary_calendar.get('id') if primary_calendar else 'primary',
                'calendar_name': primary_calendar.get('summary', 'Primary Calendar') if primary_calendar else 'Primary Calendar',
                'provider_profile_id': int(state)
            }
            
        except Exception as e:
            logger.error(f"OAuth callback failed: {e}")
            raise
    
    def build_service(self) -> bool:
        """
        Build Google Calendar service with stored credentials.
        """
        try:
            if not self.integration:
                return False
            
            # Create credentials from stored tokens
            credentials = Credentials(
                token=self.integration.access_token,
                refresh_token=self.integration.refresh_token,
                token_uri=GOOGLE_CLIENT_CONFIG['web']['token_uri'],
                client_id=GOOGLE_CLIENT_CONFIG['web']['client_id'],
                client_secret=GOOGLE_CLIENT_CONFIG['web']['client_secret']
            )
            
            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                # Update stored tokens
                self.integration.access_token = credentials.token
                if credentials.expiry:
                    self.integration.token_expiry = credentials.expiry
                self.integration.save()
            
            self.service = build('calendar', 'v3', credentials=credentials)
            return True
            
        except Exception as e:
            logger.error(f"Failed to build Google Calendar service: {e}")
            return False
    
    def fetch_events(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Fetch events from Google Calendar.
        """
        try:
            if not self.build_service():
                raise Exception("Failed to build Google Calendar service")
            
            # Default date range: 7 days back, 30 days forward
            if not start_date:
                start_date = timezone.now() - timedelta(days=7)
            if not end_date:
                end_date = timezone.now() + timedelta(days=30)
            
            # Convert to RFC3339 format
            time_min = start_date.isoformat()
            time_max = end_date.isoformat()
            
            events_result = self.service.events().list(
                calendarId=self.integration.calendar_id or 'primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=250,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            processed_events = []
            for event in events:
                processed_event = self._process_event(event)
                if processed_event:
                    processed_events.append(processed_event)
            
            logger.info(f"Fetched {len(processed_events)} events from Google Calendar")
            return processed_events
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            raise
    
    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an event in Google Calendar.
        """
        try:
            if not self.build_service():
                raise Exception("Failed to build Google Calendar service")
            
            # Format event for Google Calendar API
            google_event = {
                'summary': event_data.get('title', 'Medical Appointment'),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': event_data['start_time'].isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event_data['end_time'].isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if event_data.get('location'):
                google_event['location'] = event_data['location']
            
            created_event = self.service.events().insert(
                calendarId=self.integration.calendar_id or 'primary',
                body=google_event
            ).execute()
            
            logger.info(f"Created event in Google Calendar: {created_event.get('id')}")
            return self._process_event(created_event)
            
        except HttpError as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            raise
    
    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an event in Google Calendar.
        """
        try:
            if not self.build_service():
                raise Exception("Failed to build Google Calendar service")
            
            # Get existing event
            existing_event = self.service.events().get(
                calendarId=self.integration.calendar_id or 'primary',
                eventId=event_id
            ).execute()
            
            # Update event data
            existing_event['summary'] = event_data.get('title', existing_event.get('summary'))
            existing_event['description'] = event_data.get('description', existing_event.get('description'))
            
            if 'start_time' in event_data:
                existing_event['start'] = {
                    'dateTime': event_data['start_time'].isoformat(),
                    'timeZone': 'UTC',
                }
            
            if 'end_time' in event_data:
                existing_event['end'] = {
                    'dateTime': event_data['end_time'].isoformat(),
                    'timeZone': 'UTC',
                }
            
            if event_data.get('location'):
                existing_event['location'] = event_data['location']
            
            updated_event = self.service.events().update(
                calendarId=self.integration.calendar_id or 'primary',
                eventId=event_id,
                body=existing_event
            ).execute()
            
            logger.info(f"Updated event in Google Calendar: {event_id}")
            return self._process_event(updated_event)
            
        except HttpError as e:
            logger.error(f"Failed to update Google Calendar event: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to update event: {e}")
            raise
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event from Google Calendar.
        """
        try:
            if not self.build_service():
                raise Exception("Failed to build Google Calendar service")
            
            self.service.events().delete(
                calendarId=self.integration.calendar_id or 'primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"Deleted event from Google Calendar: {event_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Event not found for deletion: {event_id}")
                return True  # Consider it successful if already deleted
            logger.error(f"Failed to delete Google Calendar event: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete event: {e}")
            return False
    
    def _process_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and normalize a Google Calendar event.
        """
        try:
            # Skip events without start time
            if 'start' not in event:
                return None
            
            # Handle all-day events
            start_time = event['start'].get('dateTime')
            end_time = event['end'].get('dateTime') if 'end' in event else None
            
            if not start_time:
                # All-day event
                start_date = event['start'].get('date')
                end_date = event['end'].get('date') if 'end' in event else start_date
                
                if start_date:
                    start_time = f"{start_date}T00:00:00Z"
                    end_time = f"{end_date}T23:59:59Z"
                else:
                    return None
            
            # Parse datetime
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00')) if end_time else start_dt + timedelta(hours=1)
            except ValueError:
                logger.warning(f"Invalid datetime format in event {event.get('id')}")
                return None
            
            return {
                'id': event.get('id'),
                'title': event.get('summary', 'Untitled'),
                'description': event.get('description', ''),
                'start_time': start_dt,
                'end_time': end_dt,
                'location': event.get('location', ''),
                'attendees': [attendee.get('email') for attendee in event.get('attendees', [])],
                'status': event.get('status', 'confirmed'),
                'created': datetime.fromisoformat(event.get('created', '').replace('Z', '+00:00')) if event.get('created') else None,
                'updated': datetime.fromisoformat(event.get('updated', '').replace('Z', '+00:00')) if event.get('updated') else None,
                'raw_data': event
            }
            
        except Exception as e:
            logger.error(f"Failed to process event {event.get('id', 'unknown')}: {e}")
            return None
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the Google Calendar connection.
        """
        try:
            if not self.build_service():
                return {
                    'success': False,
                    'error': 'Failed to build service'
                }
            
            # Try to get calendar info
            calendar = self.service.calendars().get(
                calendarId=self.integration.calendar_id or 'primary'
            ).execute()
            
            return {
                'success': True,
                'calendar_name': calendar.get('summary'),
                'calendar_id': calendar.get('id'),
                'timezone': calendar.get('timeZone')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def is_medical_appointment(event_data: Dict[str, Any]) -> bool:
    """
    Simple medical appointment detection for MVP.
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