"""
Calendar Integration URLs - MVP Version
Simplified URL patterns for basic calendar integration functionality.
"""

from django.urls import path
from . import views

app_name = 'calendar_integrations'

urlpatterns = [
    # Dashboard
    path('', views.CalendarDashboardView.as_view(), name='dashboard'),
    
    # Integration management
    path('integrations/', views.CalendarIntegrationsView.as_view(), name='integrations'),
    path('integrations/<int:integration_id>/', views.CalendarIntegrationsView.as_view(), name='integration_detail'),
    
    # OAuth flow
    path('oauth/callback/', views.CalendarOAuthCallbackView.as_view(), name='oauth_callback'),
    
    # Calendar sync operations
    path('sync/<int:integration_id>/', views.CalendarSyncView.as_view(), name='sync'),
    
    # Calendar events
    path('events/<int:integration_id>/', views.CalendarEventsView.as_view(), name='events'),
    
    # Conflict management
    path('conflicts/', views.CalendarConflictsView.as_view(), name='conflicts'),
    path('conflicts/<int:conflict_id>/resolve/', views.CalendarConflictsView.as_view(), name='resolve_conflict'),
    
    # Availability calculation
    path('availability/', views.CalendarAvailabilityView.as_view(), name='availability'),
]