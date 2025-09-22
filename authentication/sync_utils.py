import logging
import traceback
import json
from datetime import datetime
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from .models import AuditLog

# Create dedicated logger for sync operations
sync_logger = logging.getLogger('authentication.sync')


def serialize_for_json(obj):
    """
    Safely serialize objects for JSON storage, converting datetime objects to ISO format strings
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj


class SyncErrorHandler:
    """Comprehensive error handling for user synchronization operations"""
    
    @staticmethod
    def log_sync_operation(operation: str, email: str, success: bool, 
                          details: Dict[str, Any] = None, error: Exception = None):
        """
        Log synchronization operations with comprehensive details
        
        Args:
            operation: Type of sync operation (e.g., 'user_creation', 'user_update')
            email: User email being synchronized
            success: Whether the operation was successful
            details: Additional operation details
            error: Exception if operation failed
        """
        try:
            log_level = logging.INFO if success else logging.ERROR
            
            # Create log message
            status = "SUCCESS" if success else "FAILED"
            message = f"SYNC {status}: {operation} for {email}"
            
            if details:
                message += f" | Details: {details}"
            
            if error:
                message += f" | Error: {str(error)}"
                message += f" | Traceback: {traceback.format_exc()}"
            
            sync_logger.log(log_level, message)
            
            # Also create audit log in database
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                user = None
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    pass
                
                # Serialize the new_values to handle datetime objects
                serialized_new_values = serialize_for_json({
                    'operation': operation,
                    'email': email,
                    'details': details or {},
                    'error': str(error) if error else None,
                    'success': success
                })
                
                AuditLog.objects.create(
                    user=user,
                    user_role=user.groups.first().name if user and user.groups.exists() else 'unknown',
                    action='create' if 'create' in operation.lower() else 'update',
                    resource_type='UserSync',
                    resource_id=email,
                    description=message,
                    ip_address='127.0.0.1',  # System operation
                    user_agent='System/Sync',
                    risk_level='medium' if not success else 'low',
                    new_values=serialized_new_values
                )
            except Exception as audit_error:
                sync_logger.error(f"Failed to create audit log: {str(audit_error)}")
                
        except Exception as log_error:
            # Fallback logging if our logging fails
            print(f"SYNC LOGGING ERROR: {str(log_error)}")
            print(f"Original operation: {operation} for {email}, success: {success}")
    
    @staticmethod
    def handle_supabase_error(operation: str, email: str, error: Exception) -> Dict[str, Any]:
        """
        Handle Supabase-specific errors with detailed categorization
        
        Args:
            operation: The operation that failed
            email: User email
            error: The exception that occurred
            
        Returns:
            Dict with error details and suggested actions
        """
        error_str = str(error).lower()
        error_details = {
            'operation': operation,
            'email': email,
            'error_type': 'unknown',
            'error_message': str(error),
            'suggested_action': 'Contact system administrator',
            'retry_recommended': False
        }
        
        # Categorize common Supabase errors
        if 'invalid login credentials' in error_str:
            error_details.update({
                'error_type': 'invalid_credentials',
                'suggested_action': 'User should reset password',
                'retry_recommended': False
            })
        elif 'user already exists' in error_str or 'already registered' in error_str:
            error_details.update({
                'error_type': 'user_exists',
                'suggested_action': 'User already exists in Supabase',
                'retry_recommended': False
            })
        elif 'network' in error_str or 'connection' in error_str or 'timeout' in error_str:
            error_details.update({
                'error_type': 'network_error',
                'suggested_action': 'Retry operation after network stabilizes',
                'retry_recommended': True
            })
        elif 'rate limit' in error_str or 'too many requests' in error_str:
            error_details.update({
                'error_type': 'rate_limit',
                'suggested_action': 'Wait before retrying operation',
                'retry_recommended': True
            })
        elif 'unauthorized' in error_str or 'forbidden' in error_str:
            error_details.update({
                'error_type': 'authorization_error',
                'suggested_action': 'Check Supabase API keys and permissions',
                'retry_recommended': False
            })
        
        SyncErrorHandler.log_sync_operation(operation, email, False, error_details, error)
        return error_details
    
    @staticmethod
    def handle_django_error(operation: str, email: str, error: Exception) -> Dict[str, Any]:
        """
        Handle Django-specific errors with detailed categorization
        
        Args:
            operation: The operation that failed
            email: User email
            error: The exception that occurred
            
        Returns:
            Dict with error details and suggested actions
        """
        error_str = str(error).lower()
        error_details = {
            'operation': operation,
            'email': email,
            'error_type': 'unknown',
            'error_message': str(error),
            'suggested_action': 'Contact system administrator',
            'retry_recommended': False
        }
        
        # Categorize common Django errors
        if 'unique constraint' in error_str or 'already exists' in error_str:
            error_details.update({
                'error_type': 'user_exists',
                'suggested_action': 'User already exists in Django',
                'retry_recommended': False
            })
        elif 'database' in error_str or 'connection' in error_str:
            error_details.update({
                'error_type': 'database_error',
                'suggested_action': 'Check database connection and retry',
                'retry_recommended': True
            })
        elif 'validation' in error_str or 'invalid' in error_str:
            error_details.update({
                'error_type': 'validation_error',
                'suggested_action': 'Check user data format and requirements',
                'retry_recommended': False
            })
        elif 'permission' in error_str or 'forbidden' in error_str:
            error_details.update({
                'error_type': 'permission_error',
                'suggested_action': 'Check user permissions and database access',
                'retry_recommended': False
            })
        
        SyncErrorHandler.log_sync_operation(operation, email, False, error_details, error)
        return error_details


class SyncMetrics:
    """Track synchronization metrics and health"""
    
    @staticmethod
    def get_sync_health_status() -> Dict[str, Any]:
        """
        Get overall synchronization health status
        
        Returns:
            Dict with sync health metrics
        """
        try:
            from django.contrib.auth import get_user_model
            from supabase_client import admin_client
            
            User = get_user_model()
            
            # Get counts
            django_count = User.objects.count()
            
            try:
                supabase_users = admin_client.auth.admin.list_users()
                supabase_count = len(supabase_users)
                supabase_available = True
            except Exception as e:
                supabase_count = 0
                supabase_available = False
                sync_logger.error(f"Supabase unavailable for health check: {str(e)}")
            
            # Calculate sync ratio
            if django_count > 0 and supabase_count > 0:
                sync_ratio = min(django_count, supabase_count) / max(django_count, supabase_count)
            else:
                sync_ratio = 0.0
            
            # Determine health status
            if not supabase_available:
                health_status = 'critical'
            elif sync_ratio >= 0.95:
                health_status = 'healthy'
            elif sync_ratio >= 0.80:
                health_status = 'warning'
            else:
                health_status = 'critical'
            
            # Get recent sync errors
            recent_errors = AuditLog.objects.filter(
                action__startswith='SYNC_',
                success=False,
                timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count()
            
            return {
                'health_status': health_status,
                'django_users': django_count,
                'supabase_users': supabase_count,
                'sync_ratio': round(sync_ratio, 3),
                'supabase_available': supabase_available,
                'recent_errors_24h': recent_errors,
                'last_checked': timezone.now().isoformat()
            }
            
        except Exception as e:
            sync_logger.error(f"Error getting sync health status: {str(e)}")
            return {
                'health_status': 'unknown',
                'error': str(e),
                'last_checked': timezone.now().isoformat()
            }


def safe_sync_operation(operation_name: str):
    """
    Decorator for safe synchronization operations with comprehensive error handling
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            email = kwargs.get('email', 'unknown')
            try:
                result = func(*args, **kwargs)
                SyncErrorHandler.log_sync_operation(
                    operation_name, email, True, 
                    {'result': result if isinstance(result, dict) else 'success'}
                )
                return result
            except Exception as e:
                error_details = SyncErrorHandler.handle_supabase_error(operation_name, email, e)
                # Re-raise the exception after logging
                raise e
        return wrapper
    return decorator