"""
Calendar Integration URLs - MVP Version
Simplified URL patterns for basic calendar integration functionality.
"""

from django.urls import path
from . import views

app_name = 'calendar_integrations'

urlpatterns = [
    # Integration management
    path('integrations/', views.CalendarIntegrationsView.as_view(), name='integrations'),
    path('integrations/<int:integration_id>/', views.CalendarIntegrationDetailView.as_view(), name='integration_detail'),
    path('integrations/<int:integration_id>/sync/', views.CalendarSyncView.as_view(), name='sync'),
    path('integrations/<int:integration_id>/status/', views.CalendarSyncStatusView.as_view(), name='sync_status'),
    
    # Google Calendar specific OAuth endpoints (matching frontend expectations)
    path('google/auth/', views.GoogleCalendarAuthView.as_view(), name='google_auth'),
    path('google/callback/', views.GoogleCalendarCallbackView.as_view(), name='google_callback'),
    
    # Generic OAuth flow (keeping for compatibility)
    path('oauth/callback/', views.CalendarOAuthCallbackView.as_view(), name='oauth_callback'),
    
    # Calendar events (both with and without integration_id)
    path('events/', views.CalendarEventsListView.as_view(), name='events_list'),
    path('events/<int:integration_id>/', views.CalendarEventsView.as_view(), name='events'),
    
    # Conflict management
    path('conflicts/', views.CalendarConflictsView.as_view(), name='conflicts'),
    path('conflicts/<int:conflict_id>/resolve/', views.CalendarConflictResolveView.as_view(), name='resolve_conflict'),
    
    # Token refresh
    path('integrations/<uuid:integration_id>/refresh/', views.CalendarTokenRefreshView.as_view(), name='calendar-token-refresh'),
    
    # Availability calculation
    path('availability/', views.CalendarAvailabilityView.as_view(), name='availability'),
]