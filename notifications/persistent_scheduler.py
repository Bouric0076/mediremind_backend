"""
Database-backed persistent notification scheduler.
"""

import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, F

from .models import ScheduledTask, NotificationLog, SchedulerStats
from .utils import (
    get_appointment_data,
    get_patient_data,
    get_doctor_data
)

logger = logging.getLogger(__name__)

class PersistentNotificationScheduler:
    """
    Database-backed notification scheduler with persistent storage.
    
    Features:
    - Persistent task storage in database
    - Multi-threaded processing
    - Automatic recovery on restart
    - Comprehensive logging and statistics
    - Rate limiting and circuit breakers
    """
    
    def __init__(self, 
                 max_workers: int = 20,
                 check_interval: int = 10,
                 batch_size: int = 50):
        
        self.max_workers = max_workers
        self.check_interval = check_interval
        self.batch_size = batch_size
        
        # Threading components
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None
        
        # Active tasks tracking
        self.active_tasks: Set[str] = set()
        self.processing_lock = threading.Lock()
        
        # Rate limiting (per minute)
        self.rate_limits = {
            'sms': {'limit': 10, 'window': 60},
            'email': {'limit': 100, 'window': 60},
            'push': {'limit': 500, 'window': 60},
            'whatsapp': {'limit': 5, 'window': 60}
        }
        
        # Circuit breaker states
        self.circuit_breakers = {
            'sms': {'failures': 0, 'last_failure': None, 'state': 'closed'},
            'email': {'failures': 0, 'last_failure': None, 'state': 'closed'},
            'push': {'failures': 0, 'last_failure': None, 'state': 'closed'},
            'whatsapp': {'failures': 0, 'last_failure': None, 'state': 'closed'}
        }

    def start(self):
        """Start the persistent scheduler"""
        if self.is_running:
            logger.warning("Persistent scheduler is already running")
            return
        
        logger.info("Starting persistent notification scheduler...")
        
        self.is_running = True
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        # Recover any processing tasks that were interrupted
        self._recover_interrupted_tasks()
        
        logger.info("Persistent notification scheduler started successfully")

    def stop(self):
        """Stop the persistent scheduler"""
        if not self.is_running:
            return
        
        logger.info("Stopping persistent notification scheduler...")
        self.is_running = False
        
        # Wait for threads to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=30)
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=30)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Persistent notification scheduler stopped")

    def schedule_reminder(self, 
                         appointment_id: str,
                         reminder_type: str,
                         scheduled_time: datetime,
                         delivery_method: str,
                         priority: int = 2,
                         message_data: Optional[Dict] = None) -> str:
        """Schedule a reminder task with persistent storage"""
        
        try:
            with transaction.atomic():
                task = ScheduledTask.objects.create(
                    task_type='reminder',
                    appointment_id=appointment_id,
                    reminder_type=reminder_type,
                    delivery_method=delivery_method,
                    scheduled_time=scheduled_time,
                    priority=priority,
                    message_data=message_data or {}
                )
            
            logger.info(f"Scheduled {reminder_type} reminder for appointment {appointment_id} at {scheduled_time}")
            return str(task.id)
            
        except Exception as e:
            logger.error(f"Failed to schedule reminder: {str(e)}")
            raise

    def cancel_appointment_reminders(self, appointment_id: str) -> int:
        """Cancel all pending reminders for an appointment"""
        try:
            with transaction.atomic():
                cancelled_tasks = ScheduledTask.objects.filter(
                    appointment_id=appointment_id,
                    status__in=['pending', 'retrying']
                ).update(
                    status='cancelled',
                    cancelled_at=timezone.now()
                )
            
            logger.info(f"Cancelled {cancelled_tasks} reminders for appointment {appointment_id}")
            return cancelled_tasks
            
        except Exception as e:
            logger.error(f"Failed to cancel reminders for appointment {appointment_id}: {str(e)}")
            return 0

    def _scheduler_loop(self):
        """Main scheduler loop that processes due tasks"""
        while self.is_running:
            try:
                # Get due tasks from database
                due_tasks = self._get_due_tasks()
                
                if due_tasks:
                    logger.info(f"Processing {len(due_tasks)} due tasks")
                    
                    # Submit tasks to thread pool
                    futures = []
                    for task in due_tasks:
                        if len(self.active_tasks) < self.max_workers:
                            if self._check_rate_limit(task.delivery_method):
                                if self._check_circuit_breaker(task.delivery_method):
                                    # Mark as processing
                                    task.status = 'processing'
                                    task.save()
                                    
                                    with self.processing_lock:
                                        self.active_tasks.add(str(task.id))
                                    
                                    future = self.executor.submit(self._process_task, task)
                                    futures.append(future)
                                else:
                                    # Circuit breaker open, reschedule
                                    self._reschedule_task(task, minutes=5)
                            else:
                                # Rate limited, reschedule
                                self._reschedule_task(task, seconds=30)
                        else:
                            # Too many active tasks, will be picked up next cycle
                            break
                    
                    # Handle completed futures (non-blocking check)
                    if futures:
                        try:
                            # Check for completed futures without blocking
                            for future in as_completed(futures, timeout=0.1):
                                try:
                                    future.result()
                                except Exception as e:
                                    logger.error(f"Task processing error: {str(e)}")
                        except TimeoutError:
                            # No futures completed yet, continue to next iteration
                            pass
                
                # Sleep before next check
                threading.Event().wait(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                threading.Event().wait(self.check_interval)

    def _cleanup_loop(self):
        """Background cleanup and maintenance loop"""
        while self.is_running:
            try:
                # Reset circuit breakers
                self._reset_circuit_breakers()
                
                # Update daily statistics
                self._update_daily_stats()
                
                # Clean up old completed tasks (older than 30 days)
                self._cleanup_old_tasks()
                
                # Clean up old logs (older than 90 days)
                self._cleanup_old_logs()
                
                # Sleep for 1 hour
                threading.Event().wait(3600)
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                threading.Event().wait(3600)

    def _get_due_tasks(self) -> List[ScheduledTask]:
        """Get tasks that are due for processing"""
        try:
            current_time = timezone.now()
            
            due_tasks = ScheduledTask.objects.filter(
                Q(status='pending') | Q(status='retrying'),
                scheduled_time__lte=current_time
            ).order_by('priority', 'scheduled_time')[:self.batch_size]
            
            return list(due_tasks)
            
        except Exception as e:
            logger.error(f"Failed to get due tasks: {str(e)}")
            return []

    def _process_task(self, task: ScheduledTask):
        """Process a single task"""
        try:
            start_time = timezone.now()
            task.last_attempt = start_time
            task.save()
            
            # Get appointment and patient data
            appointment_data = get_appointment_data(str(task.appointment_id))
            if not appointment_data:
                raise Exception(f"Appointment {task.appointment_id} not found")
            
            patient_data = get_patient_data(appointment_data.get('patient_id'))
            provider_data = get_doctor_data(appointment_data.get('provider_id'))
            
            # Send notification based on delivery method
            success = False
            if task.delivery_method == 'email':
                success = self._send_email(task, appointment_data, patient_data, provider_data)
            elif task.delivery_method == 'sms':
                success = self._send_sms(task, appointment_data, patient_data, provider_data)
            elif task.delivery_method == 'push':
                success = self._send_push(task, appointment_data, patient_data, provider_data)
            elif task.delivery_method == 'whatsapp':
                success = self._send_whatsapp(task, appointment_data, patient_data, provider_data)
            
            if success:
                # Mark as completed
                task.status = 'completed'
                task.completed_at = timezone.now()
                task.save()
                
                # Log success
                self._log_notification(task, 'sent', None)
                
                # Reset circuit breaker on success
                self.circuit_breakers[task.delivery_method]['failures'] = 0
                
                logger.info(f"Successfully processed task {task.id}")
            else:
                raise Exception(f"Failed to send {task.delivery_method} notification")
                
        except Exception as e:
            self._handle_task_failure(task, str(e))
        
        finally:
            # Remove from active tasks
            with self.processing_lock:
                self.active_tasks.discard(str(task.id))

    def _handle_task_failure(self, task: ScheduledTask, error_message: str):
        """Handle task failure with retry logic"""
        task.error_message = error_message
        task.retry_count += 1
        
        # Update circuit breaker
        breaker = self.circuit_breakers.get(task.delivery_method, {})
        breaker['failures'] = breaker.get('failures', 0) + 1
        breaker['last_failure'] = timezone.now()
        
        if breaker['failures'] >= 5:
            breaker['state'] = 'open'
            logger.warning(f"Circuit breaker opened for {task.delivery_method}")
        
        if task.retry_count <= task.max_retries:
            # Exponential backoff
            delay_minutes = 2 ** task.retry_count
            task.scheduled_time = timezone.now() + timedelta(minutes=delay_minutes)
            task.status = 'retrying'
            task.save()
            logger.info(f"Retrying task {task.id} in {delay_minutes} minutes")
        else:
            task.status = 'failed'
            task.save()
            logger.error(f"Task {task.id} failed permanently: {error_message}")
        
        # Log failure
        self._log_notification(task, 'failed', error_message)

    def _check_rate_limit(self, delivery_method: str) -> bool:
        """Check if delivery method is within rate limits"""
        if delivery_method not in self.rate_limits:
            return True
        
        limit_config = self.rate_limits[delivery_method]
        current_time = timezone.now()
        window_start = current_time - timedelta(seconds=limit_config['window'])
        
        # Count recent notifications
        recent_count = NotificationLog.objects.filter(
            delivery_method=delivery_method,
            status='sent',
            created_at__gte=window_start
        ).count()
        
        return recent_count < limit_config['limit']

    def _check_circuit_breaker(self, delivery_method: str) -> bool:
        """Check circuit breaker state"""
        breaker = self.circuit_breakers.get(delivery_method, {})
        
        if breaker.get('state') == 'open':
            # Check if we should try again
            if breaker.get('last_failure'):
                if timezone.now() - breaker['last_failure'] > timedelta(minutes=5):
                    breaker['state'] = 'half-open'
                    return True
            return False
        
        return True

    def _reset_circuit_breakers(self):
        """Reset circuit breakers that have been open for too long"""
        current_time = timezone.now()
        
        for method, breaker in self.circuit_breakers.items():
            if breaker['state'] == 'open' and breaker.get('last_failure'):
                if current_time - breaker['last_failure'] > timedelta(minutes=10):
                    breaker['state'] = 'closed'
                    breaker['failures'] = 0
                    logger.info(f"Reset circuit breaker for {method}")

    def _reschedule_task(self, task: ScheduledTask, minutes: int = 0, seconds: int = 0):
        """Reschedule a task for later"""
        delay = timedelta(minutes=minutes, seconds=seconds)
        task.scheduled_time = timezone.now() + delay
        task.save()

    def _recover_interrupted_tasks(self):
        """Recover tasks that were processing when the scheduler was stopped"""
        try:
            interrupted_tasks = ScheduledTask.objects.filter(status='processing')
            count = interrupted_tasks.update(status='pending')
            
            if count > 0:
                logger.info(f"Recovered {count} interrupted tasks")
                
        except Exception as e:
            logger.error(f"Failed to recover interrupted tasks: {str(e)}")

    def _log_notification(self, task: ScheduledTask, status: str, error_message: Optional[str]):
        """Log notification attempt"""
        try:
            appointment_data, error = get_appointment_data(str(task.appointment_id))
            
            # Handle case where appointment data couldn't be retrieved
            patient_id = ''
            provider_id = ''
            if appointment_data and not error:
                patient_id = appointment_data.get('patient_id', '')
                provider_id = appointment_data.get('provider_id', '')
            
            NotificationLog.objects.create(
                task=task,
                appointment_id=task.appointment_id,
                patient_id=patient_id,
                provider_id=provider_id,
                delivery_method=task.delivery_method,
                status=status,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")

    def _update_daily_stats(self):
        """Update daily statistics"""
        try:
            today = timezone.now().date()
            
            # Get today's stats
            completed_today = ScheduledTask.objects.filter(
                completed_at__date=today,
                status='completed'
            ).count()
            
            failed_today = ScheduledTask.objects.filter(
                last_attempt__date=today,
                status='failed'
            ).count()
            
            # Update or create stats record
            stats, created = SchedulerStats.objects.get_or_create(
                date=today,
                defaults={
                    'total_processed': completed_today + failed_today,
                    'successful': completed_today,
                    'failed': failed_today
                }
            )
            
            if not created:
                stats.total_processed = completed_today + failed_today
                stats.successful = completed_today
                stats.failed = failed_today
                stats.save()
                
        except Exception as e:
            logger.error(f"Failed to update daily stats: {str(e)}")

    def _cleanup_old_tasks(self):
        """Clean up old completed tasks"""
        try:
            cutoff_date = timezone.now() - timedelta(days=30)
            
            deleted_count = ScheduledTask.objects.filter(
                status__in=['completed', 'failed', 'cancelled'],
                created_at__lt=cutoff_date
            ).delete()[0]
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old tasks")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old tasks: {str(e)}")

    def _cleanup_old_logs(self):
        """Clean up old notification logs"""
        try:
            cutoff_date = timezone.now() - timedelta(days=90)
            
            deleted_count = NotificationLog.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old logs")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {str(e)}")

    # Placeholder methods for actual notification sending
    def _send_email(self, task: ScheduledTask, appointment_data: Dict, patient_data: Dict, provider_data: Dict) -> bool:
        """Send email notification"""
        # Implementation would use Django's email backend
        return True

    def _send_sms(self, task: ScheduledTask, appointment_data: Dict, patient_data: Dict, provider_data: Dict) -> bool:
        """Send SMS notification"""
        # Implementation would use SMS service API
        return True

    def _send_push(self, task: ScheduledTask, appointment_data: Dict, patient_data: Dict, provider_data: Dict) -> bool:
        """Send push notification"""
        # Implementation would use push notification service
        return True

    def _send_whatsapp(self, task: ScheduledTask, appointment_data: Dict, patient_data: Dict, provider_data: Dict) -> bool:
        """Send WhatsApp notification"""
        # Implementation would use WhatsApp Business API
        return True

    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        try:
            pending_count = ScheduledTask.objects.filter(status='pending').count()
            processing_count = ScheduledTask.objects.filter(status='processing').count()
            
            today_stats = SchedulerStats.objects.filter(
                date=timezone.now().date()
            ).first()
            
            return {
                'is_running': self.is_running,
                'pending_tasks': pending_count,
                'processing_tasks': processing_count,
                'active_tasks': len(self.active_tasks),
                'max_workers': self.max_workers,
                'today_stats': {
                    'total_processed': today_stats.total_processed if today_stats else 0,
                    'successful': today_stats.successful if today_stats else 0,
                    'failed': today_stats.failed if today_stats else 0
                } if today_stats else None,
                'circuit_breakers': self.circuit_breakers
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {'error': str(e)}

# Global persistent scheduler instance
persistent_scheduler = PersistentNotificationScheduler()

# Management functions
def start_persistent_scheduler():
    """Start the persistent scheduler"""
    persistent_scheduler.start()

def stop_persistent_scheduler():
    """Stop the persistent scheduler"""
    persistent_scheduler.stop()

def get_persistent_scheduler_status():
    """Get persistent scheduler status"""
    return persistent_scheduler.get_stats()