import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
from collections import deque, defaultdict
import uuid
from supabase_client import supabase
from .logging_config import notification_logger, LogCategory
from .monitoring import metrics_collector

class DeliveryStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"
    ABANDONED = "abandoned"

class DeliveryMethod(Enum):
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    VOICE = "voice"

class FailureReason(Enum):
    NETWORK_ERROR = "network_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INVALID_RECIPIENT = "invalid_recipient"
    RATE_LIMITED = "rate_limited"
    AUTHENTICATION_FAILED = "authentication_failed"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

@dataclass
class DeliveryAttempt:
    """Individual delivery attempt record"""
    id: str
    notification_id: str
    method: DeliveryMethod
    recipient: str
    message: str
    status: DeliveryStatus
    attempt_number: int
    timestamp: datetime
    response_time_ms: Optional[float] = None
    failure_reason: Optional[FailureReason] = None
    error_details: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['method'] = self.method.value
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.failure_reason:
            data['failure_reason'] = self.failure_reason.value
        return data

@dataclass
class NotificationTask:
    """Notification delivery task"""
    id: str
    appointment_id: str
    recipient_id: str
    message: str
    primary_method: DeliveryMethod
    fallback_methods: List[DeliveryMethod]
    max_attempts: int
    retry_intervals: List[int]  # seconds between retries
    priority: int  # 1-10, higher is more important
    created_at: datetime
    expires_at: datetime
    attempts: List[DeliveryAttempt]
    current_status: DeliveryStatus
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['primary_method'] = self.primary_method.value
        data['fallback_methods'] = [m.value for m in self.fallback_methods]
        data['created_at'] = self.created_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat()
        data['current_status'] = self.current_status.value
        data['attempts'] = [attempt.to_dict() for attempt in self.attempts]
        return data

class DeliveryProvider:
    """Base class for delivery providers"""
    
    def __init__(self, name: str, method: DeliveryMethod):
        self.name = name
        self.method = method
        self.is_available = True
        self.rate_limit_remaining = 1000
        self.last_error = None
        self.error_count = 0
        self.success_count = 0
    
    def send(self, recipient: str, message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send notification - to be implemented by subclasses"""
        raise NotImplementedError
    
    def check_health(self) -> bool:
        """Check if provider is healthy"""
        return self.is_available and self.error_count < 10
    
    def record_success(self):
        """Record successful delivery"""
        self.success_count += 1
        self.error_count = max(0, self.error_count - 1)
        self.last_error = None
    
    def record_failure(self, error: str):
        """Record failed delivery"""
        self.error_count += 1
        self.last_error = error
        if self.error_count >= 10:
            self.is_available = False

# SMS Provider removed - Twilio integration no longer supported

class EmailProvider(DeliveryProvider):
    """Email delivery provider"""
    
    def __init__(self, name: str = "smtp"):
        super().__init__(name, DeliveryMethod.EMAIL)
    
    def send(self, recipient: str, message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            from .email_client import send_email
            
            start_time = time.time()
            subject = metadata.get('subject', 'Appointment Reminder') if metadata else 'Appointment Reminder'
            result = send_email(recipient, subject, message)
            response_time = (time.time() - start_time) * 1000
            
            if result.get('success'):
                self.record_success()
                return {
                    'success': True,
                    'provider_response': result,
                    'response_time_ms': response_time
                }
            else:
                error = result.get('error', 'Unknown email error')
                self.record_failure(error)
                return {
                    'success': False,
                    'error': error,
                    'provider_response': result,
                    'response_time_ms': response_time
                }
                
        except Exception as e:
            self.record_failure(str(e))
            return {
                'success': False,
                'error': str(e),
                'response_time_ms': 0
            }

class PushProvider(DeliveryProvider):
    """Push notification delivery provider"""
    
    def __init__(self, name: str = "webpush"):
        super().__init__(name, DeliveryMethod.PUSH)
    
    def send(self, recipient: str, message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            from .push_notifications import send_push_notification
            
            start_time = time.time()
            title = metadata.get('title', 'Appointment Reminder') if metadata else 'Appointment Reminder'
            result = send_push_notification(recipient, title, message)
            response_time = (time.time() - start_time) * 1000
            
            if result.get('success'):
                self.record_success()
                return {
                    'success': True,
                    'provider_response': result,
                    'response_time_ms': response_time
                }
            else:
                error = result.get('error', 'Unknown push notification error')
                self.record_failure(error)
                return {
                    'success': False,
                    'error': error,
                    'provider_response': result,
                    'response_time_ms': response_time
                }
                
        except Exception as e:
            self.record_failure(str(e))
            return {
                'success': False,
                'error': str(e),
                'response_time_ms': 0
            }

class FailsafeDeliveryManager:
    """Manages fail-safe notification delivery with multiple providers and retry logic"""
    
    def __init__(self):
        self.providers = {
            DeliveryMethod.EMAIL: [EmailProvider()],
            DeliveryMethod.PUSH: [PushProvider()]
        }
        
        self.pending_tasks = deque()
        self.retry_queue = deque()
        self.completed_tasks = {}
        
        self.is_running = False
        self.worker_threads = []
        self.retry_thread = None
        
        self.default_retry_intervals = [30, 300, 900, 3600]  # 30s, 5m, 15m, 1h
        self.default_max_attempts = 5
        
        self.stats = {
            'total_tasks': 0,
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'abandoned_tasks': 0,
            'retry_attempts': 0
        }
    
    def start(self, num_workers: int = 3):
        """Start the delivery manager"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker threads
        for i in range(num_workers):
            worker = threading.Thread(target=self._worker_loop, args=(f"worker-{i}",), daemon=True)
            worker.start()
            self.worker_threads.append(worker)
        
        # Start retry thread
        self.retry_thread = threading.Thread(target=self._retry_loop, daemon=True)
        self.retry_thread.start()
        
        notification_logger.info(
            LogCategory.SYSTEM,
            f"Failsafe delivery manager started with {num_workers} workers",
            "failsafe_manager"
        )
    
    def stop(self):
        """Stop the delivery manager"""
        self.is_running = False
        
        # Wait for threads to finish
        for worker in self.worker_threads:
            worker.join(timeout=5)
        
        if self.retry_thread:
            self.retry_thread.join(timeout=5)
        
        notification_logger.info(
            LogCategory.SYSTEM,
            "Failsafe delivery manager stopped",
            "failsafe_manager"
        )
    
    def schedule_notification(self, appointment_id: str, recipient_id: str, message: str,
                            primary_method: DeliveryMethod, 
                            fallback_methods: List[DeliveryMethod] = None,
                            priority: int = 5, expires_in_hours: int = 24,
                            max_attempts: int = None,
                            retry_intervals: List[int] = None) -> str:
        """Schedule a notification for delivery"""
        
        task_id = str(uuid.uuid4())
        now = datetime.now()
        
        task = NotificationTask(
            id=task_id,
            appointment_id=appointment_id,
            recipient_id=recipient_id,
            message=message,
            primary_method=primary_method,
            fallback_methods=fallback_methods or [],
            max_attempts=max_attempts or self.default_max_attempts,
            retry_intervals=retry_intervals or self.default_retry_intervals,
            priority=priority,
            created_at=now,
            expires_at=now + timedelta(hours=expires_in_hours),
            attempts=[],
            current_status=DeliveryStatus.PENDING
        )
        
        self.pending_tasks.append(task)
        self.stats['total_tasks'] += 1
        
        # Store task in database
        try:
            supabase.table('notification_tasks').insert(task.to_dict()).execute()
        except Exception as e:
            notification_logger.error(
                LogCategory.DATABASE,
                f"Failed to store notification task: {str(e)}",
                "failsafe_manager",
                task_id=task_id
            )
        
        notification_logger.info(
            LogCategory.NOTIFICATION,
            f"Notification scheduled for delivery",
            "failsafe_manager",
            task_id=task_id,
            appointment_id=appointment_id,
            metadata={'method': primary_method.value, 'priority': priority}
        )
        
        return task_id
    
    def _worker_loop(self, worker_name: str):
        """Main worker loop for processing notifications"""
        while self.is_running:
            try:
                task = self._get_next_task()
                if task:
                    self._process_task(task, worker_name)
                else:
                    time.sleep(1)  # No tasks available, wait
            except Exception as e:
                notification_logger.error(
                    LogCategory.SYSTEM,
                    f"Error in worker {worker_name}: {str(e)}",
                    "failsafe_manager",
                    error_details=str(e)
                )
                time.sleep(5)  # Wait before retrying
    
    def _retry_loop(self):
        """Loop for processing retry queue"""
        while self.is_running:
            try:
                current_time = datetime.now()
                tasks_to_retry = []
                
                # Check retry queue for tasks ready to retry
                while self.retry_queue:
                    task, retry_time = self.retry_queue.popleft()
                    if current_time >= retry_time:
                        tasks_to_retry.append(task)
                    else:
                        # Put it back, it's not time yet
                        self.retry_queue.appendleft((task, retry_time))
                        break
                
                # Add retry tasks back to pending queue
                for task in tasks_to_retry:
                    self.pending_tasks.append(task)
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                notification_logger.error(
                    LogCategory.SYSTEM,
                    f"Error in retry loop: {str(e)}",
                    "failsafe_manager",
                    error_details=str(e)
                )
                time.sleep(30)
    
    def _get_next_task(self) -> Optional[NotificationTask]:
        """Get the next task to process (priority-based)"""
        if not self.pending_tasks:
            return None
        
        # Sort by priority (higher priority first) and creation time
        sorted_tasks = sorted(self.pending_tasks, 
                            key=lambda t: (-t.priority, t.created_at))
        
        # Remove and return the highest priority task
        task = sorted_tasks[0]
        self.pending_tasks.remove(task)
        return task
    
    def _process_task(self, task: NotificationTask, worker_name: str):
        """Process a notification task"""
        # Check if task has expired
        if datetime.now() > task.expires_at:
            self._abandon_task(task, "Task expired")
            return
        
        # Determine which method to use
        methods_to_try = [task.primary_method] + task.fallback_methods
        
        for method in methods_to_try:
            if len(task.attempts) >= task.max_attempts:
                break
            
            success = self._attempt_delivery(task, method, worker_name)
            if success:
                self._complete_task(task)
                return
        
        # All methods failed, schedule for retry or abandon
        if len(task.attempts) < task.max_attempts:
            self._schedule_retry(task)
        else:
            self._abandon_task(task, "Max attempts exceeded")
    
    def _attempt_delivery(self, task: NotificationTask, method: DeliveryMethod, 
                         worker_name: str) -> bool:
        """Attempt to deliver notification using specified method"""
        attempt_id = str(uuid.uuid4())
        attempt_number = len(task.attempts) + 1
        
        # Get recipient contact info
        recipient_contact = self._get_recipient_contact(task.recipient_id, method)
        if not recipient_contact:
            # Record failed attempt
            attempt = DeliveryAttempt(
                id=attempt_id,
                notification_id=task.id,
                method=method,
                recipient=task.recipient_id,
                message=task.message,
                status=DeliveryStatus.FAILED,
                attempt_number=attempt_number,
                timestamp=datetime.now(),
                failure_reason=FailureReason.INVALID_RECIPIENT,
                error_details=f"No {method.value} contact info found"
            )
            task.attempts.append(attempt)
            return False
        
        # Get available provider
        provider = self._get_available_provider(method)
        if not provider:
            # Record failed attempt
            attempt = DeliveryAttempt(
                id=attempt_id,
                notification_id=task.id,
                method=method,
                recipient=recipient_contact,
                message=task.message,
                status=DeliveryStatus.FAILED,
                attempt_number=attempt_number,
                timestamp=datetime.now(),
                failure_reason=FailureReason.SERVICE_UNAVAILABLE,
                error_details=f"No available {method.value} provider"
            )
            task.attempts.append(attempt)
            return False
        
        # Attempt delivery
        try:
            result = provider.send(recipient_contact, task.message)
            
            if result['success']:
                # Successful delivery
                attempt = DeliveryAttempt(
                    id=attempt_id,
                    notification_id=task.id,
                    method=method,
                    recipient=recipient_contact,
                    message=task.message,
                    status=DeliveryStatus.SENT,
                    attempt_number=attempt_number,
                    timestamp=datetime.now(),
                    response_time_ms=result.get('response_time_ms'),
                    provider_response=result.get('provider_response')
                )
                task.attempts.append(attempt)
                
                # Record metrics
                metrics_collector.increment_counter(f'notifications.{method.value}.success')
                metrics_collector.record_timer(f'notifications.{method.value}.response_time', 
                                              result.get('response_time_ms', 0))
                
                notification_logger.info(
                    LogCategory.NOTIFICATION,
                    f"Notification delivered successfully via {method.value}",
                    "failsafe_manager",
                    task_id=task.id,
                    appointment_id=task.appointment_id,
                    metadata={'method': method.value, 'attempt': attempt_number, 'worker': worker_name}
                )
                
                return True
            else:
                # Failed delivery
                failure_reason = self._determine_failure_reason(result['error'])
                attempt = DeliveryAttempt(
                    id=attempt_id,
                    notification_id=task.id,
                    method=method,
                    recipient=recipient_contact,
                    message=task.message,
                    status=DeliveryStatus.FAILED,
                    attempt_number=attempt_number,
                    timestamp=datetime.now(),
                    response_time_ms=result.get('response_time_ms'),
                    failure_reason=failure_reason,
                    error_details=result['error'],
                    provider_response=result.get('provider_response')
                )
                task.attempts.append(attempt)
                
                # Record metrics
                metrics_collector.increment_counter(f'notifications.{method.value}.failure')
                
                notification_logger.warning(
                    LogCategory.NOTIFICATION,
                    f"Notification delivery failed via {method.value}: {result['error']}",
                    "failsafe_manager",
                    task_id=task.id,
                    appointment_id=task.appointment_id,
                    metadata={'method': method.value, 'attempt': attempt_number, 'worker': worker_name}
                )
                
                return False
                
        except Exception as e:
            # Exception during delivery
            attempt = DeliveryAttempt(
                id=attempt_id,
                notification_id=task.id,
                method=method,
                recipient=recipient_contact,
                message=task.message,
                status=DeliveryStatus.FAILED,
                attempt_number=attempt_number,
                timestamp=datetime.now(),
                failure_reason=FailureReason.UNKNOWN,
                error_details=str(e)
            )
            task.attempts.append(attempt)
            
            notification_logger.error(
                LogCategory.NOTIFICATION,
                f"Exception during notification delivery via {method.value}: {str(e)}",
                "failsafe_manager",
                task_id=task.id,
                appointment_id=task.appointment_id,
                error_details=str(e)
            )
            
            return False
    
    def _get_recipient_contact(self, recipient_id: str, method: DeliveryMethod) -> Optional[str]:
        """Get recipient contact information for specified method"""
        try:
            # Get user data from database
            result = supabase.table('users').select('*').eq('id', recipient_id).execute()
            
            if not result.data:
                return None
            
            user = result.data[0]
            
            if method == DeliveryMethod.SMS:
                return user.get('phone')
            elif method == DeliveryMethod.EMAIL:
                return user.get('email')
            elif method == DeliveryMethod.PUSH:
                # For push notifications, we need the subscription endpoint
                push_result = supabase.table('push_subscriptions').select('endpoint').eq(
                    'user_id', recipient_id
                ).eq('active', True).execute()
                
                if push_result.data:
                    return push_result.data[0]['endpoint']
            
            return None
            
        except Exception as e:
            notification_logger.error(
                LogCategory.DATABASE,
                f"Error getting recipient contact: {str(e)}",
                "failsafe_manager",
                error_details=str(e)
            )
            return None
    
    def _get_available_provider(self, method: DeliveryMethod) -> Optional[DeliveryProvider]:
        """Get an available provider for the specified method"""
        providers = self.providers.get(method, [])
        
        for provider in providers:
            if provider.check_health():
                return provider
        
        return None
    
    def _determine_failure_reason(self, error_message: str) -> FailureReason:
        """Determine failure reason from error message"""
        error_lower = error_message.lower()
        
        if 'network' in error_lower or 'connection' in error_lower:
            return FailureReason.NETWORK_ERROR
        elif 'timeout' in error_lower:
            return FailureReason.TIMEOUT
        elif 'rate limit' in error_lower or 'too many requests' in error_lower:
            return FailureReason.RATE_LIMITED
        elif 'authentication' in error_lower or 'unauthorized' in error_lower:
            return FailureReason.AUTHENTICATION_FAILED
        elif 'invalid' in error_lower or 'not found' in error_lower:
            return FailureReason.INVALID_RECIPIENT
        elif 'unavailable' in error_lower or 'service' in error_lower:
            return FailureReason.SERVICE_UNAVAILABLE
        else:
            return FailureReason.UNKNOWN
    
    def _schedule_retry(self, task: NotificationTask):
        """Schedule task for retry"""
        attempt_count = len(task.attempts)
        if attempt_count < len(task.retry_intervals):
            retry_delay = task.retry_intervals[attempt_count - 1]
        else:
            retry_delay = task.retry_intervals[-1]  # Use last interval
        
        retry_time = datetime.now() + timedelta(seconds=retry_delay)
        self.retry_queue.append((task, retry_time))
        
        task.current_status = DeliveryStatus.RETRY
        self.stats['retry_attempts'] += 1
        
        notification_logger.info(
            LogCategory.NOTIFICATION,
            f"Task scheduled for retry in {retry_delay} seconds",
            "failsafe_manager",
            task_id=task.id,
            appointment_id=task.appointment_id
        )
    
    def _complete_task(self, task: NotificationTask):
        """Mark task as completed"""
        task.current_status = DeliveryStatus.SENT
        self.completed_tasks[task.id] = task
        self.stats['successful_deliveries'] += 1
        
        # Update database
        try:
            supabase.table('notification_tasks').update({
                'current_status': task.current_status.value,
                'attempts': [attempt.to_dict() for attempt in task.attempts]
            }).eq('id', task.id).execute()
        except Exception as e:
            notification_logger.error(
                LogCategory.DATABASE,
                f"Failed to update completed task: {str(e)}",
                "failsafe_manager",
                task_id=task.id
            )
    
    def _abandon_task(self, task: NotificationTask, reason: str):
        """Abandon task due to failure"""
        task.current_status = DeliveryStatus.ABANDONED
        self.completed_tasks[task.id] = task
        self.stats['abandoned_tasks'] += 1
        
        notification_logger.warning(
            LogCategory.NOTIFICATION,
            f"Task abandoned: {reason}",
            "failsafe_manager",
            task_id=task.id,
            appointment_id=task.appointment_id,
            metadata={'reason': reason, 'attempts': len(task.attempts)}
        )
        
        # Update database
        try:
            supabase.table('notification_tasks').update({
                'current_status': task.current_status.value,
                'attempts': [attempt.to_dict() for attempt in task.attempts]
            }).eq('id', task.id).execute()
        except Exception as e:
            notification_logger.error(
                LogCategory.DATABASE,
                f"Failed to update abandoned task: {str(e)}",
                "failsafe_manager",
                task_id=task.id
            )
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        # Check completed tasks first
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].to_dict()
        
        # Check pending tasks
        for task in self.pending_tasks:
            if task.id == task_id:
                return task.to_dict()
        
        # Check retry queue
        for task, retry_time in self.retry_queue:
            if task.id == task_id:
                task_dict = task.to_dict()
                task_dict['retry_time'] = retry_time.isoformat()
                return task_dict
        
        # Check database
        try:
            result = supabase.table('notification_tasks').select('*').eq('id', task_id).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            notification_logger.error(
                LogCategory.DATABASE,
                f"Error getting task status: {str(e)}",
                "failsafe_manager",
                task_id=task_id
            )
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get delivery statistics"""
        provider_stats = {}
        for method, providers in self.providers.items():
            provider_stats[method.value] = {
                'providers': [
                    {
                        'name': p.name,
                        'is_available': p.is_available,
                        'success_count': p.success_count,
                        'error_count': p.error_count,
                        'last_error': p.last_error
                    } for p in providers
                ]
            }
        
        return {
            'general_stats': self.stats,
            'queue_status': {
                'pending_tasks': len(self.pending_tasks),
                'retry_queue': len(self.retry_queue),
                'completed_tasks': len(self.completed_tasks)
            },
            'provider_stats': provider_stats,
            'is_running': self.is_running
        }

# Global instance
failsafe_manager = FailsafeDeliveryManager()

# Convenience functions
def schedule_notification(appointment_id: str, recipient_id: str, message: str,
                        primary_method: DeliveryMethod, **kwargs) -> str:
    """Schedule a notification for fail-safe delivery"""
    return failsafe_manager.schedule_notification(
        appointment_id, recipient_id, message, primary_method, **kwargs
    )

def get_delivery_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get delivery status for a task"""
    return failsafe_manager.get_task_status(task_id)

def get_delivery_statistics() -> Dict[str, Any]:
    """Get delivery statistics"""
    return failsafe_manager.get_statistics()

__all__ = [
    'DeliveryStatus', 'DeliveryMethod', 'FailureReason',
    'DeliveryAttempt', 'NotificationTask', 'DeliveryProvider',
    'EmailProvider', 'PushProvider',
    'FailsafeDeliveryManager', 'failsafe_manager',
    'schedule_notification', 'get_delivery_status', 'get_delivery_statistics'
]