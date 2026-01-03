"""
Celery configuration for MediRemind backend
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')

# Import celery signals for monitoring
from notifications import celery_signals

app = Celery('mediremind_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
    # Task routing for calendar integration
    task_routes={
        'calendar_integrations.tasks.*': {'queue': 'calendar'},
        'notifications.tasks.*': {'queue': 'notifications'},
    },
    # Redis Cloud specific settings - Enhanced for Render environment
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=20,  # Increased from 10 to 20
    broker_connection_retry_delay=10.0,  # Increased from 5.0 to 10.0 seconds
    broker_pool_limit=10,  # Connection pool limit
    broker_heartbeat=30,  # Heartbeat to keep connection alive
    broker_heartbeat_checkrate=10,  # Check heartbeat every 10 seconds
    # Enhanced error handling and monitoring
    task_send_sent_event=True,
    task_store_errors_even_if_ignored=True,
    worker_send_task_events=True,
    task_reject_on_worker_lost=True,
    # Task result expiration (1 hour)
    result_expires=3600,
    # Enhanced task retry settings for Render environment
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    # Rate limiting for email tasks
    task_annotations={
        'notifications.tasks.send_appointment_confirmation_async': {
            'rate_limit': '10/m'  # Max 10 emails per minute
        },
        'notifications.tasks.send_appointment_reminder_async': {
            'rate_limit': '20/m'  # Max 20 reminders per minute
        },
    },
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')