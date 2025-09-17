import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import traceback
import json
import uuid
from collections import defaultdict, deque
from supabase_client import supabase
from .logging_config import notification_logger, LogCategory
from .monitoring import metrics_collector
from .circuit_breaker import circuit_manager, CircuitBreakerOpenException

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    NETWORK = "network"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"

class RecoveryAction(Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    CIRCUIT_BREAK = "circuit_break"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class ErrorContext:
    """Context information for an error"""
    error_id: str
    timestamp: datetime
    function_name: str
    module_name: str
    error_type: str
    error_message: str
    stack_trace: str
    severity: ErrorSeverity
    category: ErrorCategory
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    appointment_id: Optional[str] = None
    notification_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'error_id': self.error_id,
            'timestamp': self.timestamp.isoformat(),
            'function_name': self.function_name,
            'module_name': self.module_name,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'severity': self.severity.value,
            'category': self.category.value,
            'metadata': self.metadata,
            'user_id': self.user_id,
            'appointment_id': self.appointment_id,
            'notification_id': self.notification_id
        }

@dataclass
class RecoveryStrategy:
    """Strategy for recovering from errors"""
    name: str
    action: RecoveryAction
    max_attempts: int = 3
    delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 300.0
    conditions: List[Callable[[ErrorContext], bool]] = field(default_factory=list)
    recovery_function: Optional[Callable[[ErrorContext], Any]] = None
    
    def should_apply(self, error_context: ErrorContext) -> bool:
        """Check if this strategy should be applied to the error"""
        if not self.conditions:
            return True
        return all(condition(error_context) for condition in self.conditions)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = self.delay_seconds * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_delay_seconds)

@dataclass
class RecoveryAttempt:
    """Record of a recovery attempt"""
    attempt_id: str
    error_id: str
    strategy_name: str
    attempt_number: int
    timestamp: datetime
    success: bool
    duration_ms: float
    result: Optional[Any] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'attempt_id': self.attempt_id,
            'error_id': self.error_id,
            'strategy_name': self.strategy_name,
            'attempt_number': self.attempt_number,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'duration_ms': self.duration_ms,
            'result': str(self.result) if self.result else None,
            'error_message': self.error_message
        }

class ErrorRecoveryManager:
    """Manages error recovery strategies and execution"""
    
    def __init__(self):
        self.strategies: List[RecoveryStrategy] = []
        self.error_history: deque = deque(maxlen=1000)
        self.recovery_attempts: Dict[str, List[RecoveryAttempt]] = defaultdict(list)
        
        # Error pattern tracking
        self.error_patterns = defaultdict(int)
        self.error_trends = defaultdict(list)
        
        # Recovery statistics
        self.stats = {
            'total_errors': 0,
            'recovered_errors': 0,
            'failed_recoveries': 0,
            'manual_interventions': 0
        }
        
        self.lock = threading.RLock()
        
        # Initialize default strategies
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """Initialize default recovery strategies"""
        
        # Network error retry strategy
        network_retry = RecoveryStrategy(
            name="network_retry",
            action=RecoveryAction.RETRY,
            max_attempts=3,
            delay_seconds=2.0,
            backoff_multiplier=2.0,
            conditions=[
                lambda ctx: ctx.category == ErrorCategory.NETWORK,
                lambda ctx: ctx.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]
            ]
        )
        
        # Database connection retry strategy
        db_retry = RecoveryStrategy(
            name="database_retry",
            action=RecoveryAction.RETRY,
            max_attempts=5,
            delay_seconds=1.0,
            backoff_multiplier=1.5,
            conditions=[
                lambda ctx: ctx.category == ErrorCategory.DATABASE,
                lambda ctx: "connection" in ctx.error_message.lower()
            ]
        )
        
        # External service fallback strategy
        service_fallback = RecoveryStrategy(
            name="service_fallback",
            action=RecoveryAction.FALLBACK,
            max_attempts=1,
            conditions=[
                lambda ctx: ctx.category == ErrorCategory.EXTERNAL_SERVICE,
                lambda ctx: ctx.severity != ErrorSeverity.CRITICAL
            ],
            recovery_function=self._external_service_fallback
        )
        
        # Critical error escalation strategy
        critical_escalation = RecoveryStrategy(
            name="critical_escalation",
            action=RecoveryAction.ESCALATE,
            max_attempts=1,
            conditions=[
                lambda ctx: ctx.severity == ErrorSeverity.CRITICAL
            ],
            recovery_function=self._escalate_critical_error
        )
        
        # Circuit breaker strategy
        circuit_break = RecoveryStrategy(
            name="circuit_break",
            action=RecoveryAction.CIRCUIT_BREAK,
            max_attempts=1,
            conditions=[
                lambda ctx: "CircuitBreakerOpen" in ctx.error_type
            ],
            recovery_function=self._handle_circuit_breaker_error
        )
        
        self.strategies.extend([
            network_retry, db_retry, service_fallback, 
            critical_escalation, circuit_break
        ])
    
    def add_strategy(self, strategy: RecoveryStrategy):
        """Add a custom recovery strategy"""
        with self.lock:
            self.strategies.append(strategy)
            notification_logger.info(
                LogCategory.SYSTEM,
                f"Added recovery strategy: {strategy.name}",
                "error_recovery"
            )
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """Remove a recovery strategy"""
        with self.lock:
            for i, strategy in enumerate(self.strategies):
                if strategy.name == strategy_name:
                    del self.strategies[i]
                    notification_logger.info(
                        LogCategory.SYSTEM,
                        f"Removed recovery strategy: {strategy_name}",
                        "error_recovery"
                    )
                    return True
            return False
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Any:
        """Handle an error with recovery strategies"""
        error_context = self._create_error_context(error, context or {})
        
        with self.lock:
            self.stats['total_errors'] += 1
            self.error_history.append(error_context)
            self._track_error_patterns(error_context)
        
        # Store error in database
        self._store_error(error_context)
        
        # Find applicable recovery strategies
        applicable_strategies = [
            strategy for strategy in self.strategies 
            if strategy.should_apply(error_context)
        ]
        
        if not applicable_strategies:
            notification_logger.warning(
                LogCategory.ERROR,
                f"No recovery strategy found for error: {error_context.error_type}",
                "error_recovery",
                error_id=error_context.error_id
            )
            raise error
        
        # Try recovery strategies in order
        for strategy in applicable_strategies:
            try:
                result = self._execute_recovery_strategy(strategy, error_context)
                if result is not None:
                    with self.lock:
                        self.stats['recovered_errors'] += 1
                    return result
            except Exception as recovery_error:
                notification_logger.error(
                    LogCategory.ERROR,
                    f"Recovery strategy '{strategy.name}' failed: {str(recovery_error)}",
                    "error_recovery",
                    error_id=error_context.error_id,
                    error_details=str(recovery_error)
                )
        
        # All recovery strategies failed
        with self.lock:
            self.stats['failed_recoveries'] += 1
        
        notification_logger.error(
            LogCategory.ERROR,
            f"All recovery strategies failed for error: {error_context.error_type}",
            "error_recovery",
            error_id=error_context.error_id
        )
        
        raise error
    
    def _create_error_context(self, error: Exception, context: Dict[str, Any]) -> ErrorContext:
        """Create error context from exception and additional context"""
        error_id = str(uuid.uuid4())
        
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        # Determine error category and severity
        category = self._categorize_error(error, context)
        severity = self._determine_severity(error, context, category)
        
        return ErrorContext(
            error_id=error_id,
            timestamp=datetime.now(),
            function_name=context.get('function_name', 'unknown'),
            module_name=context.get('module_name', 'unknown'),
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=stack_trace,
            severity=severity,
            category=category,
            metadata=context.get('metadata', {}),
            user_id=context.get('user_id'),
            appointment_id=context.get('appointment_id'),
            notification_id=context.get('notification_id')
        )
    
    def _categorize_error(self, error: Exception, context: Dict[str, Any]) -> ErrorCategory:
        """Categorize error based on type and context"""
        error_type = type(error).__name__.lower()
        error_message = str(error).lower()
        
        if 'network' in error_message or 'connection' in error_message:
            return ErrorCategory.NETWORK
        elif 'database' in error_message or 'sql' in error_message:
            return ErrorCategory.DATABASE
        elif 'auth' in error_message or 'permission' in error_message:
            return ErrorCategory.AUTHENTICATION
        elif 'validation' in error_message or 'invalid' in error_message:
            return ErrorCategory.VALIDATION
        elif any(service in error_message for service in ['smtp', 'push']):
            return ErrorCategory.EXTERNAL_SERVICE
        elif 'system' in error_message or 'os' in error_message:
            return ErrorCategory.SYSTEM
        else:
            return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, error: Exception, context: Dict[str, Any], 
                          category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity"""
        error_message = str(error).lower()
        
        # Critical errors
        if any(keyword in error_message for keyword in 
               ['critical', 'fatal', 'system failure', 'data corruption']):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if (category == ErrorCategory.DATABASE and 'connection' in error_message) or \
           (category == ErrorCategory.SYSTEM) or \
           ('timeout' in error_message and category == ErrorCategory.EXTERNAL_SERVICE):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.NETWORK, ErrorCategory.EXTERNAL_SERVICE, 
                       ErrorCategory.AUTHENTICATION]:
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    def _execute_recovery_strategy(self, strategy: RecoveryStrategy, 
                                 error_context: ErrorContext) -> Any:
        """Execute a recovery strategy"""
        if strategy.action == RecoveryAction.RETRY:
            return self._execute_retry_strategy(strategy, error_context)
        elif strategy.action == RecoveryAction.FALLBACK:
            return self._execute_fallback_strategy(strategy, error_context)
        elif strategy.action == RecoveryAction.ESCALATE:
            return self._execute_escalation_strategy(strategy, error_context)
        elif strategy.action == RecoveryAction.CIRCUIT_BREAK:
            return self._execute_circuit_break_strategy(strategy, error_context)
        elif strategy.action == RecoveryAction.IGNORE:
            return self._execute_ignore_strategy(strategy, error_context)
        else:
            raise ValueError(f"Unknown recovery action: {strategy.action}")
    
    def _execute_retry_strategy(self, strategy: RecoveryStrategy, 
                              error_context: ErrorContext) -> Any:
        """Execute retry recovery strategy"""
        for attempt in range(1, strategy.max_attempts + 1):
            if attempt > 1:
                delay = strategy.calculate_delay(attempt)
                time.sleep(delay)
            
            attempt_id = str(uuid.uuid4())
            start_time = time.time()
            
            try:
                # If there's a custom recovery function, use it
                if strategy.recovery_function:
                    result = strategy.recovery_function(error_context)
                else:
                    # Default retry behavior - re-raise the original error
                    # This allows the calling code to retry the operation
                    result = None
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Record successful attempt
                recovery_attempt = RecoveryAttempt(
                    attempt_id=attempt_id,
                    error_id=error_context.error_id,
                    strategy_name=strategy.name,
                    attempt_number=attempt,
                    timestamp=datetime.now(),
                    success=True,
                    duration_ms=duration_ms,
                    result=result
                )
                
                self.recovery_attempts[error_context.error_id].append(recovery_attempt)
                
                notification_logger.info(
                    LogCategory.ERROR,
                    f"Recovery attempt {attempt} succeeded for strategy '{strategy.name}'",
                    "error_recovery",
                    error_id=error_context.error_id,
                    attempt_id=attempt_id
                )
                
                return result
                
            except Exception as retry_error:
                duration_ms = (time.time() - start_time) * 1000
                
                # Record failed attempt
                recovery_attempt = RecoveryAttempt(
                    attempt_id=attempt_id,
                    error_id=error_context.error_id,
                    strategy_name=strategy.name,
                    attempt_number=attempt,
                    timestamp=datetime.now(),
                    success=False,
                    duration_ms=duration_ms,
                    error_message=str(retry_error)
                )
                
                self.recovery_attempts[error_context.error_id].append(recovery_attempt)
                
                if attempt == strategy.max_attempts:
                    notification_logger.error(
                        LogCategory.ERROR,
                        f"All {strategy.max_attempts} retry attempts failed for strategy '{strategy.name}'",
                        "error_recovery",
                        error_id=error_context.error_id
                    )
                    raise retry_error
        
        return None
    
    def _execute_fallback_strategy(self, strategy: RecoveryStrategy, 
                                 error_context: ErrorContext) -> Any:
        """Execute fallback recovery strategy"""
        if not strategy.recovery_function:
            raise ValueError(f"Fallback strategy '{strategy.name}' requires a recovery function")
        
        attempt_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            result = strategy.recovery_function(error_context)
            duration_ms = (time.time() - start_time) * 1000
            
            recovery_attempt = RecoveryAttempt(
                attempt_id=attempt_id,
                error_id=error_context.error_id,
                strategy_name=strategy.name,
                attempt_number=1,
                timestamp=datetime.now(),
                success=True,
                duration_ms=duration_ms,
                result=result
            )
            
            self.recovery_attempts[error_context.error_id].append(recovery_attempt)
            
            notification_logger.info(
                LogCategory.ERROR,
                f"Fallback strategy '{strategy.name}' succeeded",
                "error_recovery",
                error_id=error_context.error_id
            )
            
            return result
            
        except Exception as fallback_error:
            duration_ms = (time.time() - start_time) * 1000
            
            recovery_attempt = RecoveryAttempt(
                attempt_id=attempt_id,
                error_id=error_context.error_id,
                strategy_name=strategy.name,
                attempt_number=1,
                timestamp=datetime.now(),
                success=False,
                duration_ms=duration_ms,
                error_message=str(fallback_error)
            )
            
            self.recovery_attempts[error_context.error_id].append(recovery_attempt)
            
            notification_logger.error(
                LogCategory.ERROR,
                f"Fallback strategy '{strategy.name}' failed: {str(fallback_error)}",
                "error_recovery",
                error_id=error_context.error_id
            )
            
            raise fallback_error
    
    def _execute_escalation_strategy(self, strategy: RecoveryStrategy, 
                                   error_context: ErrorContext) -> Any:
        """Execute escalation recovery strategy"""
        if strategy.recovery_function:
            return strategy.recovery_function(error_context)
        else:
            # Default escalation behavior
            return self._escalate_critical_error(error_context)
    
    def _execute_circuit_break_strategy(self, strategy: RecoveryStrategy, 
                                      error_context: ErrorContext) -> Any:
        """Execute circuit breaker recovery strategy"""
        if strategy.recovery_function:
            return strategy.recovery_function(error_context)
        else:
            return self._handle_circuit_breaker_error(error_context)
    
    def _execute_ignore_strategy(self, strategy: RecoveryStrategy, 
                               error_context: ErrorContext) -> Any:
        """Execute ignore recovery strategy"""
        notification_logger.info(
            LogCategory.ERROR,
            f"Ignoring error as per strategy '{strategy.name}'",
            "error_recovery",
            error_id=error_context.error_id
        )
        return None
    
    def _external_service_fallback(self, error_context: ErrorContext) -> Any:
        """Fallback for external service errors"""
        # Try alternative notification methods
        if 'sms' in error_context.function_name.lower():
            notification_logger.info(
                LogCategory.ERROR,
                "SMS service failed, attempting email fallback",
                "error_recovery",
                error_id=error_context.error_id
            )
            # Return indication to use email instead
            return {'fallback_method': 'email'}
        elif 'email' in error_context.function_name.lower():
            notification_logger.info(
                LogCategory.ERROR,
                "Email service failed, attempting SMS fallback",
                "error_recovery",
                error_id=error_context.error_id
            )
            return {'fallback_method': 'sms'}
        
        return None
    
    def _escalate_critical_error(self, error_context: ErrorContext) -> Any:
        """Escalate critical errors"""
        with self.lock:
            self.stats['manual_interventions'] += 1
        
        # Send alert to administrators
        alert_data = {
            'error_id': error_context.error_id,
            'severity': error_context.severity.value,
            'category': error_context.category.value,
            'message': error_context.error_message,
            'timestamp': error_context.timestamp.isoformat(),
            'requires_immediate_attention': True
        }
        
        # Store alert in database
        try:
            supabase.table('system_alerts').insert(alert_data).execute()
        except Exception as e:
            notification_logger.error(
                LogCategory.DATABASE,
                f"Failed to store system alert: {str(e)}",
                "error_recovery",
                error_id=error_context.error_id
            )
        
        notification_logger.critical(
            LogCategory.ERROR,
            f"Critical error escalated: {error_context.error_message}",
            "error_recovery",
            error_id=error_context.error_id,
            metadata=alert_data
        )
        
        return None
    
    def _handle_circuit_breaker_error(self, error_context: ErrorContext) -> Any:
        """Handle circuit breaker errors"""
        notification_logger.warning(
            LogCategory.ERROR,
            "Circuit breaker is open, service temporarily unavailable",
            "error_recovery",
            error_id=error_context.error_id
        )
        
        # Return indication that service is temporarily unavailable
        return {'status': 'service_unavailable', 'retry_after': 60}
    
    def _track_error_patterns(self, error_context: ErrorContext):
        """Track error patterns for analysis"""
        pattern_key = f"{error_context.category.value}:{error_context.error_type}"
        self.error_patterns[pattern_key] += 1
        
        # Track trends (errors per hour)
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        self.error_trends[pattern_key].append(current_hour)
        
        # Keep only last 24 hours of data
        cutoff_time = current_hour - timedelta(hours=24)
        self.error_trends[pattern_key] = [
            timestamp for timestamp in self.error_trends[pattern_key]
            if timestamp >= cutoff_time
        ]
    
    def _store_error(self, error_context: ErrorContext):
        """Store error in database"""
        try:
            supabase.table('error_logs').insert(error_context.to_dict()).execute()
        except Exception as e:
            notification_logger.error(
                LogCategory.DATABASE,
                f"Failed to store error log: {str(e)}",
                "error_recovery",
                error_details=str(e)
            )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error and recovery statistics"""
        with self.lock:
            return {
                'general_stats': self.stats.copy(),
                'error_patterns': dict(self.error_patterns),
                'recent_errors': len(self.error_history),
                'active_strategies': len(self.strategies),
                'strategy_names': [s.name for s in self.strategies]
            }
    
    def get_error_trends(self) -> Dict[str, List[str]]:
        """Get error trends over time"""
        trends = {}
        for pattern, timestamps in self.error_trends.items():
            trends[pattern] = [ts.isoformat() for ts in timestamps]
        return trends
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent errors"""
        with self.lock:
            recent = list(self.error_history)[-limit:]
            return [error.to_dict() for error in recent]

# Global error recovery manager
error_recovery_manager = ErrorRecoveryManager()

# Decorator for automatic error handling
def handle_errors(context: Dict[str, Any] = None):
    """Decorator to automatically handle errors with recovery strategies"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                recovery_context = context or {}
                recovery_context.update({
                    'function_name': func.__name__,
                    'module_name': func.__module__
                })
                return error_recovery_manager.handle_error(e, recovery_context)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator

# Convenience functions
def add_recovery_strategy(strategy: RecoveryStrategy):
    """Add a custom recovery strategy"""
    error_recovery_manager.add_strategy(strategy)

def get_error_statistics() -> Dict[str, Any]:
    """Get error and recovery statistics"""
    return error_recovery_manager.get_error_statistics()

def get_recent_errors(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent errors"""
    return error_recovery_manager.get_recent_errors(limit)

__all__ = [
    'ErrorSeverity', 'ErrorCategory', 'RecoveryAction',
    'ErrorContext', 'RecoveryStrategy', 'RecoveryAttempt',
    'ErrorRecoveryManager', 'error_recovery_manager',
    'handle_errors', 'add_recovery_strategy',
    'get_error_statistics', 'get_recent_errors'
]