"""
Celery signal handlers for monitoring and error tracking.
Provides detailed logging and alerting for failed tasks.
"""
import logging
from celery import signals
from django.utils import timezone
from django.conf import settings
import json

logger = logging.getLogger(__name__)


@signals.task_failure.connect
def log_task_failure(sender, task_id, exception, args, kwargs, traceback, einfo, **extra):
    """Log detailed information when a task fails"""
    logger.error(
        f"Task {sender.name} ({task_id}) failed with exception: {exception}",
        extra={
            'task_id': task_id,
            'task_name': sender.name,
            'exception': str(exception),
            'args': args,
            'kwargs': kwargs,
            'traceback': traceback,
            'timestamp': timezone.now().isoformat(),
            'environment': settings.DEBUG and 'development' or 'production'
        }
    )
    
    # Special handling for email tasks
    if 'appointment' in sender.name.lower() and 'email' in sender.name.lower():
        logger.error(
            f"Email task failure detected: {sender.name}",
            extra={
                'task_type': 'email',
                'appointment_id': kwargs.get('appointment_id') if kwargs else None,
                'recipient': kwargs.get('patient_email') if kwargs else None,
                'retry_count': getattr(sender, 'max_retries', 3) - getattr(sender, 'retries', 0)
            }
        )


@signals.task_retry.connect
def log_task_retry(sender, task_id, exception, args, kwargs, einfo, **extra):
    """Log when a task is being retried"""
    logger.warning(
        f"Task {sender.name} ({task_id}) is being retried due to: {exception}",
        extra={
            'task_id': task_id,
            'task_name': sender.name,
            'exception': str(exception),
            'retry_count': getattr(sender, 'retries', 0),
            'max_retries': getattr(sender, 'max_retries', 3),
            'timestamp': timezone.now().isoformat()
        }
    )


@signals.task_success.connect
def log_task_success(sender, result, **extra):
    """Log successful task completion"""
    logger.info(
        f"Task {sender.name} completed successfully",
        extra={
            'task_name': sender.name,
            'result': str(result) if result else None,
            'timestamp': timezone.now().isoformat()
        }
    )


@signals.task_prerun.connect
def log_task_start(sender, task_id, args, kwargs, **extra):
    """Log when a task starts execution"""
    logger.info(
        f"Task {sender.name} ({task_id}) started execution",
        extra={
            'task_id': task_id,
            'task_name': sender.name,
            'args': args,
            'kwargs': kwargs,
            'timestamp': timezone.now().isoformat()
        }
    )


@signals.worker_ready.connect
def log_worker_ready(sender, **extra):
    """Log when a worker is ready to process tasks"""
    logger.info(
        "Celery worker is ready to process tasks",
        extra={
            'worker_info': str(sender),
            'timestamp': timezone.now().isoformat()
        }
    )


@signals.worker_shutdown.connect
def log_worker_shutdown(sender, **extra):
    """Log when a worker is shutting down"""
    logger.warning(
        "Celery worker is shutting down",
        extra={
            'worker_info': str(sender),
            'timestamp': timezone.now().isoformat()
        }
    )