from django.apps import AppConfig

class ApiIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_integration'
    verbose_name = 'API Integration'
    
    def ready(self):
        """Initialize API integration app"""
        # Import signal handlers
        from . import signals
        
        # Schedule compliance maintenance tasks
        from django.core.management import call_command
        from django.utils import timezone
        from datetime import timedelta
        
        # Note: In production, use proper task scheduling (Celery, cron, etc.)
        # This is just for development/testing purposes
        try:
            # Run compliance maintenance on startup (development only)
            if timezone.now().hour == 2:  # Run at 2 AM
                call_command('run_compliance_maintenance', '--task', 'all')
        except Exception:
            pass  # Ignore errors during startup