"""
Logging configuration for authentication and sync operations
"""

import os
from django.conf import settings

# Sync logging configuration
SYNC_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'sync_detailed': {
            'format': '[{asctime}] {levelname} {name} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'sync_json': {
            'format': '{"timestamp": "{asctime}", "level": "{levelname}", "logger": "{name}", "message": "{message}"}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'sync_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(getattr(settings, 'LOG_DIR', 'logs'), 'sync_operations.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'sync_detailed',
            'encoding': 'utf-8'
        },
        'sync_error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(getattr(settings, 'LOG_DIR', 'logs'), 'sync_errors.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
            'formatter': 'sync_detailed',
            'encoding': 'utf-8'
        },
        'sync_json_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(getattr(settings, 'LOG_DIR', 'logs'), 'sync_operations.json'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 3,
            'formatter': 'sync_json',
            'encoding': 'utf-8'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'sync_detailed'
        }
    },
    'loggers': {
        'authentication.sync': {
            'handlers': ['sync_file', 'sync_error_file', 'sync_json_file'],
            'level': 'INFO',
            'propagate': False
        },
        'authentication.signals': {
            'handlers': ['sync_file', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'authentication.services': {
            'handlers': ['sync_file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}


def setup_sync_logging():
    """
    Setup sync logging configuration
    """
    import logging.config
    
    # Ensure log directory exists
    log_dir = getattr(settings, 'LOG_DIR', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Apply logging configuration
    logging.config.dictConfig(SYNC_LOGGING_CONFIG)
    
    # Test logging setup
    sync_logger = logging.getLogger('authentication.sync')
    sync_logger.info("Sync logging configuration initialized successfully")


def get_sync_logger(name: str = 'authentication.sync'):
    """
    Get a configured sync logger
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Monitoring and alerting configuration
SYNC_MONITORING_CONFIG = {
    'error_threshold': 10,  # Alert if more than 10 errors in 1 hour
    'sync_ratio_threshold': 0.8,  # Alert if sync ratio drops below 80%
    'health_check_interval': 300,  # Check health every 5 minutes
    'alert_cooldown': 3600,  # Don't send duplicate alerts within 1 hour
}


class SyncMonitor:
    """
    Monitor sync operations and trigger alerts
    """
    
    def __init__(self):
        self.logger = get_sync_logger('authentication.sync.monitor')
    
    def check_error_rate(self) -> dict:
        """
        Check if error rate exceeds threshold
        """
        from django.utils import timezone
        from datetime import timedelta
        from authentication.models import AuditLog
        
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        error_count = AuditLog.objects.filter(
            action__startswith='SYNC_',
            success=False,
            timestamp__gte=one_hour_ago
        ).count()
        
        total_count = AuditLog.objects.filter(
            action__startswith='SYNC_',
            timestamp__gte=one_hour_ago
        ).count()
        
        error_rate = error_count / max(total_count, 1)
        threshold_exceeded = error_count > SYNC_MONITORING_CONFIG['error_threshold']
        
        if threshold_exceeded:
            self.logger.warning(
                f"Sync error threshold exceeded: {error_count} errors in last hour "
                f"(rate: {error_rate:.2%})"
            )
        
        return {
            'error_count': error_count,
            'total_count': total_count,
            'error_rate': error_rate,
            'threshold_exceeded': threshold_exceeded,
            'threshold': SYNC_MONITORING_CONFIG['error_threshold']
        }
    
    def check_sync_health(self) -> dict:
        """
        Perform comprehensive sync health check
        """
        from authentication.sync_utils import SyncMetrics
        
        health_status = SyncMetrics.get_sync_health_status()
        error_rate_status = self.check_error_rate()
        
        overall_health = 'healthy'
        if (health_status.get('health_status') == 'critical' or 
            error_rate_status.get('threshold_exceeded')):
            overall_health = 'critical'
        elif health_status.get('health_status') == 'warning':
            overall_health = 'warning'
        
        result = {
            'overall_health': overall_health,
            'sync_metrics': health_status,
            'error_metrics': error_rate_status,
            'timestamp': timezone.now().isoformat()
        }
        
        if overall_health == 'critical':
            self.logger.error(f"Sync system health is critical: {result}")
        elif overall_health == 'warning':
            self.logger.warning(f"Sync system health warning: {result}")
        else:
            self.logger.info(f"Sync system health check passed: {result}")
        
        return result