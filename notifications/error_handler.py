"""
Comprehensive error handling and logging utilities for the notification system.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from django.utils import timezone

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorCategory(Enum):
    TEMPLATE_RENDERING = "template_rendering"
    EMAIL_SENDING = "email_sending"
    SMS_SENDING = "sms_sending"
    PUSH_NOTIFICATION = "push_notification"
    API_INTEGRATION = "api_integration"
    DATABASE = "database"
    VALIDATION = "validation"
    NETWORK = "network"


@dataclass
class ErrorContext:
    error_type: str
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    context_data: Dict[str, Any]
    timestamp: timezone.datetime
    stack_trace: Optional[str] = None
    user_id: Optional[int] = None
    appointment_id: Optional[int] = None
    notification_type: Optional[str] = None
    channel: Optional[str] = None


class NotificationErrorHandler:
    """Centralized error handler for notification system"""
    
    def __init__(self):
        self.error_stats = {
            'total_errors': 0,
            'errors_by_severity': {severity.value: 0 for severity in ErrorSeverity},
            'errors_by_category': {category.value: 0 for category in ErrorCategory},
            'recent_errors': []
        }
        self.max_recent_errors = 100
    
    def log_error(self, error_context: ErrorContext) -> None:
        """Log error with structured context"""
        self.error_stats['total_errors'] += 1
        self.error_stats['errors_by_severity'][error_context.severity.value] += 1
        self.error_stats['errors_by_category'][error_context.category.value] += 1
        
        # Add to recent errors
        self.error_stats['recent_errors'].append({
            'timestamp': error_context.timestamp.isoformat(),
            'severity': error_context.severity.value,
            'category': error_context.category.value,
            'message': error_context.message,
            'context': error_context.context_data
        })
        
        if len(self.error_stats['recent_errors']) > self.max_recent_errors:
            self.error_stats['recent_errors'].pop(0)
        
        # Log with appropriate level
        log_message = self._format_error_message(error_context)
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra=error_context.context_data)
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra=error_context.context_data)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra=error_context.context_data)
        else:
            logger.info(log_message, extra=error_context.context_data)
    
    def _format_error_message(self, error_context: ErrorContext) -> str:
        """Format error message for logging"""
        base_message = f"[{error_context.category.value.upper()}] {error_context.message}"
        
        # Add context information
        context_parts = []
        if error_context.user_id:
            context_parts.append(f"User: {error_context.user_id}")
        if error_context.appointment_id:
            context_parts.append(f"Appointment: {error_context.appointment_id}")
        if error_context.notification_type:
            context_parts.append(f"Type: {error_context.notification_type}")
        if error_context.channel:
            context_parts.append(f"Channel: {error_context.channel}")
        
        if context_parts:
            base_message += f" ({', '.join(context_parts)})"
        
        return base_message
    
    def handle_template_error(self, template_key: str, error: Exception, 
                            context_data: Dict[str, Any] = None) -> ErrorContext:
        """Handle template rendering errors"""
        error_context = ErrorContext(
            error_type=type(error).__name__,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.TEMPLATE_RENDERING,
            message=f"Template rendering failed for {template_key}: {str(error)}",
            context_data={
                'template_key': template_key,
                'error_details': str(error),
                **(context_data or {})
            },
            timestamp=timezone.now(),
            stack_trace=traceback.format_exc()
        )
        
        self.log_error(error_context)
        return error_context
    
    def handle_email_error(self, recipient_email: str, error: Exception,
                          appointment_data: Dict[str, Any] = None, 
                          notification_type: str = None) -> ErrorContext:
        """Handle email sending errors"""
        # Determine severity based on error type
        severity = ErrorSeverity.HIGH
        if "invalid" in str(error).lower():
            severity = ErrorSeverity.MEDIUM
        elif "rate" in str(error).lower():
            severity = ErrorSeverity.LOW
        elif "network" in str(error).lower() or "timeout" in str(error).lower():
            severity = ErrorSeverity.MEDIUM
        
        error_context = ErrorContext(
            error_type=type(error).__name__,
            severity=severity,
            category=ErrorCategory.EMAIL_SENDING,
            message=f"Email sending failed for {recipient_email}: {str(error)}",
            context_data={
                'recipient_email': recipient_email,
                'error_details': str(error),
                **(appointment_data or {})
            },
            timestamp=timezone.now(),
            stack_trace=traceback.format_exc(),
            notification_type=notification_type
        )
        
        self.log_error(error_context)
        return error_context
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error statistics"""
        return {
            'total_errors': self.error_stats['total_errors'],
            'errors_by_severity': self.error_stats['errors_by_severity'].copy(),
            'errors_by_category': self.error_stats['errors_by_category'].copy(),
            'recent_errors': self.error_stats['recent_errors'].copy()
        }


# Global error handler instance
notification_error_handler = NotificationErrorHandler()