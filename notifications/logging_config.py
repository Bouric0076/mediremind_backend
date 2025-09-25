import logging
import logging.handlers
import os
from datetime import datetime
from typing import Dict, Any, Optional
import json
from enum import Enum
from dataclasses import dataclass, asdict
from supabase_client import supabase

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    SCHEDULER = "scheduler"
    QUEUE = "queue"
    NOTIFICATION = "notification"
    BACKGROUND_TASK = "background_task"
    API = "api"
    DATABASE = "database"
    SYSTEM = "system"
    SECURITY = "security"
    CACHE = "cache"

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    component: str
    user_id: Optional[str] = None
    appointment_id: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        data['category'] = self.category.value
        return data

class DatabaseLogHandler(logging.Handler):
    """Custom log handler that stores logs in Supabase"""
    
    def __init__(self, table_name: str = 'system_logs'):
        super().__init__()
        self.table_name = table_name
        self.batch_size = 10
        self.log_batch = []
    
    def emit(self, record):
        """Emit a log record to the database"""
        try:
            # Extract structured data from record
            log_data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'category': getattr(record, 'category', 'system'),
                'component': getattr(record, 'component', record.name),
                'message': record.getMessage(),
                'user_id': getattr(record, 'user_id', None),
                'appointment_id': getattr(record, 'appointment_id', None),
                'task_id': getattr(record, 'task_id', None),
                'metadata': getattr(record, 'metadata', None),
                'error_details': getattr(record, 'error_details', None),
                'request_id': getattr(record, 'request_id', None),
                'module': record.module,
                'function': record.funcName,
                'line_number': record.lineno
            }
            
            # Add to batch
            self.log_batch.append(log_data)
            
            # Flush batch if it reaches batch size
            if len(self.log_batch) >= self.batch_size:
                self.flush_batch()
                
        except Exception as e:
            # Fallback to console logging if database logging fails
            print(f"Failed to log to database: {e}")
            print(f"Original log: {record.getMessage()}")
    
    def flush_batch(self):
        """Flush the current batch to database"""
        if not self.log_batch:
            return
            
        try:
            result = supabase.table(self.table_name).insert(self.log_batch).execute()
            if result.data:
                self.log_batch.clear()
        except Exception as e:
            print(f"Failed to flush log batch to database: {e}")
            # Keep the batch for retry
    
    def close(self):
        """Close handler and flush remaining logs"""
        self.flush_batch()
        super().close()

class NotificationLogger:
    """Centralized logger for the notification system"""
    
    def __init__(self, name: str = 'notifications'):
        self.logger = logging.getLogger(name)
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        json_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for all logs
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'notifications.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'errors.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Database handler
        try:
            db_handler = DatabaseLogHandler()
            db_handler.setLevel(logging.INFO)
            self.logger.addHandler(db_handler)
        except Exception as e:
            self.logger.warning(f"Failed to setup database logging: {e}")
    
    def log(self, level: LogLevel, category: LogCategory, message: str, 
            component: str, **kwargs):
        """Log a structured message"""
        extra = {
            'category': category.value,
            'component': component,
            **kwargs
        }
        
        log_method = getattr(self.logger, level.value.lower())
        log_method(message, extra=extra)
    
    def debug(self, category: LogCategory, message: str, component: str, **kwargs):
        """Log debug message"""
        self.log(LogLevel.DEBUG, category, message, component, **kwargs)
    
    def info(self, category: LogCategory, message: str, component: str, **kwargs):
        """Log info message"""
        self.log(LogLevel.INFO, category, message, component, **kwargs)
    
    def warning(self, category: LogCategory, message: str, component: str, **kwargs):
        """Log warning message"""
        self.log(LogLevel.WARNING, category, message, component, **kwargs)
    
    def error(self, category: LogCategory, message: str, component: str, **kwargs):
        """Log error message"""
        self.log(LogLevel.ERROR, category, message, component, **kwargs)
    
    def critical(self, category: LogCategory, message: str, component: str, **kwargs):
        """Log critical message"""
        self.log(LogLevel.CRITICAL, category, message, component, **kwargs)
    
    def log_scheduler_event(self, event: str, task_id: str = None, 
                           appointment_id: str = None, **kwargs):
        """Log scheduler-specific events"""
        self.info(
            LogCategory.SCHEDULER, 
            f"Scheduler event: {event}",
            "scheduler",
            task_id=task_id,
            appointment_id=appointment_id,
            **kwargs
        )
    
    def log_queue_event(self, event: str, queue_type: str = None, 
                       message_count: int = None, **kwargs):
        """Log queue-specific events"""
        metadata = {'queue_type': queue_type, 'message_count': message_count}
        metadata.update(kwargs.get('metadata', {}))
        
        self.info(
            LogCategory.QUEUE,
            f"Queue event: {event}",
            "queue_manager",
            metadata=metadata,
            **kwargs
        )
    
    def log_notification_event(self, event: str, notification_type: str = None,
                              recipient: str = None, appointment_id: str = None,
                              **kwargs):
        """Log notification-specific events"""
        metadata = {
            'notification_type': notification_type,
            'recipient': recipient
        }
        metadata.update(kwargs.get('metadata', {}))
        
        self.info(
            LogCategory.NOTIFICATION,
            f"Notification event: {event}",
            "notification_sender",
            appointment_id=appointment_id,
            metadata=metadata,
            **kwargs
        )
    
    def log_api_request(self, method: str, endpoint: str, user_id: str = None,
                       status_code: int = None, response_time: float = None,
                       **kwargs):
        """Log API request events"""
        metadata = {
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'response_time_ms': response_time
        }
        metadata.update(kwargs.get('metadata', {}))
        
        level = LogLevel.INFO if status_code and status_code < 400 else LogLevel.WARNING
        
        self.log(
            level,
            LogCategory.API,
            f"API {method} {endpoint} - {status_code}",
            "api",
            user_id=user_id,
            metadata=metadata,
            **kwargs
        )
    
    def log_database_operation(self, operation: str, table: str, 
                              record_count: int = None, duration: float = None,
                              **kwargs):
        """Log database operation events"""
        metadata = {
            'operation': operation,
            'table': table,
            'record_count': record_count,
            'duration_ms': duration
        }
        metadata.update(kwargs.get('metadata', {}))
        
        self.info(
            LogCategory.DATABASE,
            f"Database {operation} on {table}",
            "database",
            metadata=metadata,
            **kwargs
        )
    
    def log_security_event(self, event: str, user_id: str = None, 
                          ip_address: str = None, **kwargs):
        """Log security-related events"""
        metadata = {
            'ip_address': ip_address,
            'event_type': event
        }
        metadata.update(kwargs.get('metadata', {}))
        
        self.warning(
            LogCategory.SECURITY,
            f"Security event: {event}",
            "security",
            user_id=user_id,
            metadata=metadata,
            **kwargs
        )

class LogAnalyzer:
    """Analyze logs for patterns and issues"""
    
    def __init__(self, logger: NotificationLogger):
        self.logger = logger
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        try:
            from_time = datetime.now() - timedelta(hours=hours)
            
            result = supabase.table('system_logs').select('*').gte(
                'timestamp', from_time.isoformat()
            ).eq('level', 'ERROR').execute()
            
            errors = result.data if result.data else []
            
            # Group errors by component and category
            error_summary = {}
            for error in errors:
                component = error.get('component', 'unknown')
                category = error.get('category', 'unknown')
                key = f"{component}:{category}"
                
                if key not in error_summary:
                    error_summary[key] = {
                        'count': 0,
                        'latest_error': None,
                        'component': component,
                        'category': category
                    }
                
                error_summary[key]['count'] += 1
                if not error_summary[key]['latest_error'] or \
                   error['timestamp'] > error_summary[key]['latest_error']['timestamp']:
                    error_summary[key]['latest_error'] = error
            
            return {
                'total_errors': len(errors),
                'error_breakdown': error_summary,
                'time_range_hours': hours
            }
            
        except Exception as e:
            self.logger.error(
                LogCategory.SYSTEM,
                f"Failed to get error summary: {str(e)}",
                "log_analyzer"
            )
            return {'error': str(e)}
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics from logs"""
        try:
            from_time = datetime.now() - timedelta(hours=hours)
            
            # Get API performance metrics
            result = supabase.table('system_logs').select('*').gte(
                'timestamp', from_time.isoformat()
            ).eq('category', 'api').execute()
            
            api_logs = result.data if result.data else []
            
            response_times = []
            status_codes = {}
            
            for log in api_logs:
                metadata = log.get('metadata', {})
                if 'response_time_ms' in metadata:
                    response_times.append(metadata['response_time_ms'])
                
                status_code = metadata.get('status_code')
                if status_code:
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                'api_metrics': {
                    'total_requests': len(api_logs),
                    'average_response_time_ms': avg_response_time,
                    'status_code_distribution': status_codes
                },
                'time_range_hours': hours
            }
            
        except Exception as e:
            self.logger.error(
                LogCategory.SYSTEM,
                f"Failed to get performance metrics: {str(e)}",
                "log_analyzer"
            )
            return {'error': str(e)}

# Global logger instance
notification_logger = NotificationLogger()
log_analyzer = LogAnalyzer(notification_logger)

# Convenience functions
def log_scheduler_event(event: str, **kwargs):
    notification_logger.log_scheduler_event(event, **kwargs)

def log_queue_event(event: str, **kwargs):
    notification_logger.log_queue_event(event, **kwargs)

def log_notification_event(event: str, **kwargs):
    notification_logger.log_notification_event(event, **kwargs)

def log_api_request(method: str, endpoint: str, **kwargs):
    notification_logger.log_api_request(method, endpoint, **kwargs)

def log_database_operation(operation: str, table: str, **kwargs):
    notification_logger.log_database_operation(operation, table, **kwargs)

def log_security_event(event: str, **kwargs):
    notification_logger.log_security_event(event, **kwargs)

__all__ = [
    'LogLevel', 'LogCategory', 'LogEntry', 'NotificationLogger',
    'LogAnalyzer', 'notification_logger', 'log_analyzer',
    'log_scheduler_event', 'log_queue_event', 'log_notification_event',
    'log_api_request', 'log_database_operation', 'log_security_event'
]