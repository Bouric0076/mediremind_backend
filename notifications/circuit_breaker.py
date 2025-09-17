import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import statistics
from collections import deque
from .logging_config import notification_logger, LogCategory
from .monitoring import metrics_collector

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open" # Testing if service has recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Number of failures to open circuit
    success_threshold: int = 3          # Number of successes to close circuit
    timeout_seconds: int = 60           # Time to wait before trying half-open
    window_size: int = 100              # Size of sliding window for metrics
    failure_rate_threshold: float = 0.5 # Failure rate to open circuit (0.0-1.0)
    slow_call_threshold_ms: int = 5000  # Calls slower than this are considered failures
    minimum_calls: int = 10             # Minimum calls before evaluating failure rate

@dataclass
class CallResult:
    """Result of a function call"""
    success: bool
    duration_ms: float
    timestamp: datetime
    error: Optional[str] = None

class CircuitBreaker:
    """Circuit breaker implementation for protecting external services"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now()
        
        # Sliding window for call results
        self.call_history = deque(maxlen=self.config.window_size)
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes = 0
        
        notification_logger.info(
            LogCategory.SYSTEM,
            f"Circuit breaker '{name}' initialized",
            "circuit_breaker",
            metadata={'config': self.config.__dict__}
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self.lock:
            self.total_calls += 1
            
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    self._record_rejected_call()
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )
            
            # Execute the function
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Check if call was too slow
                if duration_ms > self.config.slow_call_threshold_ms:
                    self._record_failure(duration_ms, "Slow call")
                else:
                    self._record_success(duration_ms)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self._record_failure(duration_ms, str(e))
                raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.timeout_seconds
    
    def _transition_to_half_open(self):
        """Transition circuit to half-open state"""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.failure_count = 0
        self.last_state_change = datetime.now()
        self.state_changes += 1
        
        notification_logger.info(
            LogCategory.SYSTEM,
            f"Circuit breaker '{self.name}' transitioned from {old_state.value} to {self.state.value}",
            "circuit_breaker"
        )
        
        metrics_collector.increment_counter(f'circuit_breaker.{self.name}.state_change')
    
    def _transition_to_open(self):
        """Transition circuit to open state"""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.last_failure_time = datetime.now()
        self.last_state_change = datetime.now()
        self.state_changes += 1
        
        notification_logger.warning(
            LogCategory.SYSTEM,
            f"Circuit breaker '{self.name}' transitioned from {old_state.value} to {self.state.value}",
            "circuit_breaker",
            metadata={
                'failure_count': self.failure_count,
                'failure_rate': self._calculate_failure_rate()
            }
        )
        
        metrics_collector.increment_counter(f'circuit_breaker.{self.name}.opened')
    
    def _transition_to_closed(self):
        """Transition circuit to closed state"""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.now()
        self.state_changes += 1
        
        notification_logger.info(
            LogCategory.SYSTEM,
            f"Circuit breaker '{self.name}' transitioned from {old_state.value} to {self.state.value}",
            "circuit_breaker"
        )
        
        metrics_collector.increment_counter(f'circuit_breaker.{self.name}.closed')
    
    def _record_success(self, duration_ms: float):
        """Record a successful call"""
        call_result = CallResult(
            success=True,
            duration_ms=duration_ms,
            timestamp=datetime.now()
        )
        
        self.call_history.append(call_result)
        self.total_successes += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
        
        metrics_collector.increment_counter(f'circuit_breaker.{self.name}.success')
        metrics_collector.record_timer(f'circuit_breaker.{self.name}.duration', duration_ms)
    
    def _record_failure(self, duration_ms: float, error: str):
        """Record a failed call"""
        call_result = CallResult(
            success=False,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            error=error
        )
        
        self.call_history.append(call_result)
        self.total_failures += 1
        self.failure_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state opens the circuit
            self._transition_to_open()
        elif self.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if self._should_open_circuit():
                self._transition_to_open()
        
        metrics_collector.increment_counter(f'circuit_breaker.{self.name}.failure')
    
    def _record_rejected_call(self):
        """Record a call that was rejected due to open circuit"""
        metrics_collector.increment_counter(f'circuit_breaker.{self.name}.rejected')
    
    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened based on failure criteria"""
        # Check failure count threshold
        if self.failure_count >= self.config.failure_threshold:
            return True
        
        # Check failure rate threshold
        if len(self.call_history) >= self.config.minimum_calls:
            failure_rate = self._calculate_failure_rate()
            if failure_rate >= self.config.failure_rate_threshold:
                return True
        
        return False
    
    def _calculate_failure_rate(self) -> float:
        """Calculate current failure rate from call history"""
        if not self.call_history:
            return 0.0
        
        failures = sum(1 for call in self.call_history if not call.success)
        return failures / len(self.call_history)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self.lock:
            recent_calls = list(self.call_history)[-50:]  # Last 50 calls
            
            if recent_calls:
                recent_durations = [call.duration_ms for call in recent_calls]
                avg_duration = statistics.mean(recent_durations)
                p95_duration = statistics.quantiles(recent_durations, n=20)[18] if len(recent_durations) > 1 else 0
            else:
                avg_duration = 0
                p95_duration = 0
            
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'total_calls': self.total_calls,
                'total_failures': self.total_failures,
                'total_successes': self.total_successes,
                'failure_rate': self._calculate_failure_rate(),
                'state_changes': self.state_changes,
                'last_state_change': self.last_state_change.isoformat(),
                'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
                'call_history_size': len(self.call_history),
                'avg_duration_ms': avg_duration,
                'p95_duration_ms': p95_duration,
                'config': {
                    'failure_threshold': self.config.failure_threshold,
                    'success_threshold': self.config.success_threshold,
                    'timeout_seconds': self.config.timeout_seconds,
                    'failure_rate_threshold': self.config.failure_rate_threshold,
                    'slow_call_threshold_ms': self.config.slow_call_threshold_ms
                }
            }
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        with self.lock:
            old_state = self.state
            self._transition_to_closed()
            self.call_history.clear()
            
            notification_logger.info(
                LogCategory.SYSTEM,
                f"Circuit breaker '{self.name}' manually reset from {old_state.value}",
                "circuit_breaker"
            )
    
    def force_open(self):
        """Manually force circuit breaker to open state"""
        with self.lock:
            old_state = self.state
            self._transition_to_open()
            
            notification_logger.warning(
                LogCategory.SYSTEM,
                f"Circuit breaker '{self.name}' manually forced open from {old_state.value}",
                "circuit_breaker"
            )

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.RLock()
    
    def get_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]
    
    def remove_breaker(self, name: str) -> bool:
        """Remove a circuit breaker"""
        with self.lock:
            if name in self.breakers:
                del self.breakers[name]
                return True
            return False
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        with self.lock:
            return {name: breaker.get_statistics() for name, breaker in self.breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.reset()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of all circuit breakers"""
        with self.lock:
            total_breakers = len(self.breakers)
            open_breakers = sum(1 for b in self.breakers.values() if b.state == CircuitState.OPEN)
            half_open_breakers = sum(1 for b in self.breakers.values() if b.state == CircuitState.HALF_OPEN)
            closed_breakers = sum(1 for b in self.breakers.values() if b.state == CircuitState.CLOSED)
            
            return {
                'total_breakers': total_breakers,
                'open_breakers': open_breakers,
                'half_open_breakers': half_open_breakers,
                'closed_breakers': closed_breakers,
                'health_percentage': (closed_breakers / total_breakers * 100) if total_breakers > 0 else 100,
                'breaker_names': list(self.breakers.keys())
            }

# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()

# Predefined circuit breakers for common services
def get_sms_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for SMS service"""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=30,
        failure_rate_threshold=0.6,
        slow_call_threshold_ms=10000  # SMS can be slow
    )
    return circuit_manager.get_breaker('sms_service', config)

def get_email_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for email service"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout_seconds=60,
        failure_rate_threshold=0.5,
        slow_call_threshold_ms=15000  # Email can be slower
    )
    return circuit_manager.get_breaker('email_service', config)

def get_push_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for push notification service"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout_seconds=30,
        failure_rate_threshold=0.4,
        slow_call_threshold_ms=5000  # Push should be fast
    )
    return circuit_manager.get_breaker('push_service', config)

def get_database_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for database operations"""
    config = CircuitBreakerConfig(
        failure_threshold=10,
        success_threshold=5,
        timeout_seconds=15,
        failure_rate_threshold=0.3,
        slow_call_threshold_ms=2000  # Database should be fast
    )
    return circuit_manager.get_breaker('database_service', config)

# Decorator for easy circuit breaker usage
def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """Decorator to add circuit breaker protection to functions"""
    def decorator(func):
        breaker = circuit_manager.get_breaker(name, config)
        
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator

__all__ = [
    'CircuitState', 'CircuitBreakerConfig', 'CallResult',
    'CircuitBreaker', 'CircuitBreakerOpenException', 'CircuitBreakerManager',
    'circuit_manager', 'circuit_breaker',
    'get_sms_circuit_breaker', 'get_email_circuit_breaker',
    'get_push_circuit_breaker', 'get_database_circuit_breaker'
]