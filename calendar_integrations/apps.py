"""
Calendar Integrations Django App Configuration
"""

from django.apps import AppConfig


class CalendarIntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calendar_integrations'
    verbose_name = 'Calendar Integrations'
    
    def ready(self):
        """Initialize calendar integration services when app is ready"""
        try:
            # Import and initialize background sync tasks
            from .tasks import start_calendar_sync_scheduler
            start_calendar_sync_scheduler()
        except ImportError:
            # Tasks module not yet created, skip for now
            pass