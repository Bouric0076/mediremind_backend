"""
Calendar Integration Settings and Configuration
Centralized configuration for all calendar integration features.
"""

from django.conf import settings
import os

# =============================================================================
# GOOGLE CALENDAR SETTINGS
# =============================================================================

GOOGLE_CALENDAR_CONFIG = {
    'CLIENT_ID': os.getenv('GOOGLE_CALENDAR_CLIENT_ID', ''),
    'CLIENT_SECRET': os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET', ''),
    'REDIRECT_URI': os.getenv('GOOGLE_CALENDAR_REDIRECT_URI', 'http://localhost:8000/api/calendar/oauth/callback/'),
    'SCOPES': [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ],
    'API_VERSION': 'v3',
    'MAX_RESULTS': 2500,  # Maximum events to fetch per request
    'SYNC_WINDOW_DAYS': 90,  # Days to sync forward/backward
}

# =============================================================================
# MICROSOFT OUTLOOK SETTINGS
# =============================================================================

OUTLOOK_CALENDAR_CONFIG = {
    'CLIENT_ID': os.getenv('OUTLOOK_CALENDAR_CLIENT_ID', ''),
    'CLIENT_SECRET': os.getenv('OUTLOOK_CALENDAR_CLIENT_SECRET', ''),
    'TENANT_ID': os.getenv('OUTLOOK_TENANT_ID', 'common'),
    'REDIRECT_URI': os.getenv('OUTLOOK_CALENDAR_REDIRECT_URI', 'http://localhost:8000/api/calendar/oauth/outlook/callback/'),
    'SCOPES': [
        'https://graph.microsoft.com/calendars.readwrite',
        'https://graph.microsoft.com/user.read'
    ],
    'API_VERSION': 'v1.0',
    'AUTHORITY': 'https://login.microsoftonline.com/',
}

# =============================================================================
# CALENDLY SETTINGS
# =============================================================================

CALENDLY_CONFIG = {
    'CLIENT_ID': os.getenv('CALENDLY_CLIENT_ID', ''),
    'CLIENT_SECRET': os.getenv('CALENDLY_CLIENT_SECRET', ''),
    'REDIRECT_URI': os.getenv('CALENDLY_REDIRECT_URI', 'http://localhost:8000/api/calendar/oauth/calendly/callback/'),
    'API_BASE_URL': 'https://api.calendly.com',
    'WEBHOOK_SIGNING_KEY': os.getenv('CALENDLY_WEBHOOK_SIGNING_KEY', ''),
}

# =============================================================================
# APPLE CALENDAR (ICLOUD) SETTINGS
# =============================================================================

APPLE_CALENDAR_CONFIG = {
    'CALDAV_URL': 'https://caldav.icloud.com',
    'SUPPORTED_AUTH_METHODS': ['app_specific_password'],
    'SYNC_INTERVAL_MINUTES': 30,
}

# =============================================================================
# SYNC CONFIGURATION
# =============================================================================

CALENDAR_SYNC_CONFIG = {
    # Sync intervals (in minutes)
    'REAL_TIME_SYNC_INTERVAL': 5,
    'BATCH_SYNC_INTERVAL': 15,
    'FULL_SYNC_INTERVAL': 1440,  # 24 hours
    
    # Retry configuration
    'MAX_SYNC_RETRIES': 3,
    'RETRY_BACKOFF_SECONDS': 60,
    
    # Rate limiting
    'API_RATE_LIMIT_PER_MINUTE': 100,
    'BURST_RATE_LIMIT': 10,
    
    # Data retention
    'SYNC_LOG_RETENTION_DAYS': 30,
    'EXTERNAL_EVENT_RETENTION_DAYS': 365,
    
    # Conflict detection
    'CONFLICT_DETECTION_ENABLED': True,
    'AUTO_RESOLVE_LOW_SEVERITY': True,
    'CONFLICT_NOTIFICATION_ENABLED': True,
}

# =============================================================================
# AI/ML CONFIGURATION
# =============================================================================

AI_CALENDAR_CONFIG = {
    # Medical appointment detection
    'MEDICAL_KEYWORDS': [
        'appointment', 'doctor', 'clinic', 'hospital', 'medical',
        'checkup', 'consultation', 'patient', 'treatment', 'therapy',
        'dentist', 'physician', 'nurse', 'surgery', 'exam', 'visit',
        'follow-up', 'screening', 'vaccination', 'lab', 'test',
        'radiology', 'mri', 'ct scan', 'ultrasound', 'x-ray'
    ],
    
    # Confidence thresholds
    'MEDICAL_DETECTION_THRESHOLD': 0.7,
    'CONFLICT_SEVERITY_THRESHOLD': {
        'low': 0.3,
        'medium': 0.6,
        'high': 0.8
    },
    
    # Machine learning models
    'ML_MODEL_ENABLED': False,  # Enable when ML models are trained
    'ML_MODEL_PATH': os.path.join(settings.BASE_DIR, 'ml_models', 'calendar_classifier.pkl'),
    'FEATURE_EXTRACTION_ENABLED': True,
}

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

CALENDAR_SECURITY_CONFIG = {
    # OAuth token encryption
    'ENCRYPT_TOKENS': True,
    'TOKEN_ENCRYPTION_KEY': os.getenv('CALENDAR_TOKEN_ENCRYPTION_KEY', settings.SECRET_KEY),
    
    # API security
    'REQUIRE_HTTPS_OAUTH': not settings.DEBUG,
    'OAUTH_STATE_TIMEOUT_MINUTES': 10,
    'TOKEN_REFRESH_BUFFER_MINUTES': 5,
    
    # Data privacy
    'ANONYMIZE_PATIENT_DATA_IN_EXTERNAL_CALENDAR': True,
    'LOG_SENSITIVE_DATA': False,
    'AUDIT_CALENDAR_ACCESS': True,
}

# =============================================================================
# NOTIFICATION CONFIGURATION
# =============================================================================

CALENDAR_NOTIFICATION_CONFIG = {
    # Conflict notifications
    'NOTIFY_ON_CONFLICTS': True,
    'CONFLICT_NOTIFICATION_CHANNELS': ['email', 'in_app'],
    'IMMEDIATE_NOTIFICATION_SEVERITY': ['high'],
    
    # Sync notifications
    'NOTIFY_ON_SYNC_FAILURES': True,
    'SYNC_FAILURE_NOTIFICATION_THRESHOLD': 3,  # Consecutive failures
    
    # Success notifications
    'NOTIFY_ON_SUCCESSFUL_INTEGRATION': True,
    'WEEKLY_SYNC_SUMMARY': True,
}

# =============================================================================
# PERFORMANCE CONFIGURATION
# =============================================================================

CALENDAR_PERFORMANCE_CONFIG = {
    # Caching
    'CACHE_AVAILABILITY_MINUTES': 15,
    'CACHE_EXTERNAL_EVENTS_MINUTES': 30,
    'CACHE_PROVIDER_PREFERENCES_HOURS': 24,
    
    # Database optimization
    'BATCH_SIZE_SYNC_EVENTS': 100,
    'BULK_CREATE_BATCH_SIZE': 500,
    'INDEX_OPTIMIZATION_ENABLED': True,
    
    # Background tasks
    'CELERY_TASK_PRIORITY': {
        'real_time_sync': 9,
        'conflict_resolution': 8,
        'batch_sync': 5,
        'cleanup': 1
    }
}

# =============================================================================
# FEATURE FLAGS
# =============================================================================

CALENDAR_FEATURE_FLAGS = {
    # Core features
    'GOOGLE_CALENDAR_ENABLED': True,
    'OUTLOOK_CALENDAR_ENABLED': True,
    'CALENDLY_INTEGRATION_ENABLED': True,
    'APPLE_CALENDAR_ENABLED': False,  # Coming soon
    
    # Advanced features
    'AI_CONFLICT_RESOLUTION': True,
    'PREDICTIVE_SCHEDULING': False,  # Beta feature
    'SMART_AVAILABILITY_SUGGESTIONS': True,
    'AUTOMATED_RESCHEDULING': False,  # Beta feature
    
    # Experimental features
    'VOICE_SCHEDULING_INTEGRATION': False,
    'NATURAL_LANGUAGE_PROCESSING': False,
    'CROSS_PROVIDER_COORDINATION': False,
}

# =============================================================================
# WEBHOOK CONFIGURATION
# =============================================================================

CALENDAR_WEBHOOK_CONFIG = {
    # Google Calendar webhooks
    'GOOGLE_WEBHOOK_ENABLED': True,
    'GOOGLE_WEBHOOK_TTL_SECONDS': 3600,  # 1 hour
    'GOOGLE_WEBHOOK_VERIFICATION_TOKEN': os.getenv('GOOGLE_WEBHOOK_TOKEN', ''),
    
    # Outlook webhooks
    'OUTLOOK_WEBHOOK_ENABLED': True,
    'OUTLOOK_WEBHOOK_VALIDATION_TOKENS': os.getenv('OUTLOOK_WEBHOOK_TOKENS', '').split(','),
    
    # Calendly webhooks
    'CALENDLY_WEBHOOK_ENABLED': True,
    'CALENDLY_WEBHOOK_SIGNING_KEY': os.getenv('CALENDLY_WEBHOOK_SIGNING_KEY', ''),
    
    # General webhook settings
    'WEBHOOK_RETRY_ATTEMPTS': 3,
    'WEBHOOK_TIMEOUT_SECONDS': 30,
    'WEBHOOK_RATE_LIMIT_PER_MINUTE': 1000,
}

# =============================================================================
# ANALYTICS CONFIGURATION
# =============================================================================

CALENDAR_ANALYTICS_CONFIG = {
    # Metrics collection
    'COLLECT_SYNC_METRICS': True,
    'COLLECT_USAGE_METRICS': True,
    'COLLECT_PERFORMANCE_METRICS': True,
    
    # Reporting
    'DAILY_SYNC_REPORTS': True,
    'WEEKLY_USAGE_REPORTS': True,
    'MONTHLY_ANALYTICS_SUMMARY': True,
    
    # Data retention for analytics
    'METRICS_RETENTION_DAYS': 90,
    'DETAILED_LOGS_RETENTION_DAYS': 7,
}

# =============================================================================
# DEVELOPMENT & TESTING CONFIGURATION
# =============================================================================

if settings.DEBUG:
    # Development overrides
    CALENDAR_SYNC_CONFIG['REAL_TIME_SYNC_INTERVAL'] = 1  # 1 minute for testing
    CALENDAR_SECURITY_CONFIG['REQUIRE_HTTPS_OAUTH'] = False
    CALENDAR_NOTIFICATION_CONFIG['NOTIFY_ON_SUCCESSFUL_INTEGRATION'] = False
    
    # Test data
    CALENDAR_TEST_CONFIG = {
        'MOCK_EXTERNAL_CALENDARS': True,
        'GENERATE_TEST_EVENTS': True,
        'SIMULATE_CONFLICTS': True,
        'TEST_PROVIDER_COUNT': 5,
        'TEST_EVENTS_PER_PROVIDER': 20,
    }

# =============================================================================
# VALIDATION
# =============================================================================

def validate_calendar_settings():
    """
    Validate that all required calendar integration settings are properly configured.
    """
    errors = []
    
    # Check required Google Calendar settings
    if CALENDAR_FEATURE_FLAGS['GOOGLE_CALENDAR_ENABLED']:
        if not GOOGLE_CALENDAR_CONFIG['CLIENT_ID']:
            errors.append("GOOGLE_CALENDAR_CLIENT_ID environment variable is required")
        if not GOOGLE_CALENDAR_CONFIG['CLIENT_SECRET']:
            errors.append("GOOGLE_CALENDAR_CLIENT_SECRET environment variable is required")
    
    # Check required Outlook settings
    if CALENDAR_FEATURE_FLAGS['OUTLOOK_CALENDAR_ENABLED']:
        if not OUTLOOK_CALENDAR_CONFIG['CLIENT_ID']:
            errors.append("OUTLOOK_CALENDAR_CLIENT_ID environment variable is required")
        if not OUTLOOK_CALENDAR_CONFIG['CLIENT_SECRET']:
            errors.append("OUTLOOK_CALENDAR_CLIENT_SECRET environment variable is required")
    
    # Check Celery configuration for background tasks
    if not hasattr(settings, 'CELERY_BROKER_URL'):
        errors.append("CELERY_BROKER_URL is required for calendar sync tasks")
    
    if errors:
        raise ValueError(f"Calendar integration configuration errors: {', '.join(errors)}")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_provider_config(provider_name: str) -> dict:
    """
    Get configuration for a specific calendar provider.
    """
    provider_configs = {
        'google': GOOGLE_CALENDAR_CONFIG,
        'outlook': OUTLOOK_CALENDAR_CONFIG,
        'calendly': CALENDLY_CONFIG,
        'apple': APPLE_CALENDAR_CONFIG,
    }
    
    return provider_configs.get(provider_name.lower(), {})

def is_feature_enabled(feature_name: str) -> bool:
    """
    Check if a specific calendar feature is enabled.
    """
    return CALENDAR_FEATURE_FLAGS.get(feature_name, False)

def get_sync_interval(sync_type: str) -> int:
    """
    Get sync interval for a specific sync type.
    """
    intervals = {
        'real_time': CALENDAR_SYNC_CONFIG['REAL_TIME_SYNC_INTERVAL'],
        'batch': CALENDAR_SYNC_CONFIG['BATCH_SYNC_INTERVAL'],
        'full': CALENDAR_SYNC_CONFIG['FULL_SYNC_INTERVAL'],
    }
    
    return intervals.get(sync_type, CALENDAR_SYNC_CONFIG['BATCH_SYNC_INTERVAL'])

# Run validation on import (only in production)
if not settings.DEBUG:
    try:
        validate_calendar_settings()
    except ValueError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Calendar settings validation warning: {e}")