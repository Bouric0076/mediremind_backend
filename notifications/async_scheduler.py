"""
Enhanced Async Notification Scheduler with improved scalability and performance.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import aiodns
from django.utils import timezone
from django.db import transaction

from .models import AppointmentReminder, NotificationLog
from .utils import (
    get_appointment_data,
    get_patient_data,
    get_doctor_data
)

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = 3
    MEDIUM = 2
    HIGH = 1
    URGENT = 0

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

@dataclass
class AsyncTask:
    """Async task representation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    appointment_id: str = ""
    reminder_type: str = ""
    delivery_method: str = ""
    scheduled_time: datetime = field(default_factory=datetime.now)
    priority: TaskPriority = TaskPriority.MEDIUM
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    last_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    message_data: Dict = field(default_factory=dict)

    def __lt__(self, other):
        """For priority queue ordering"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.scheduled_time < other.scheduled_time

class AsyncNotificationScheduler:
    """
    High-performance async notification scheduler with improved scalability.
    
    Features:
    - Async/await for better concurrency
    - Connection pooling for HTTP requests
    - Batch processing capabilities
    - Advanced rate limiting
    - Circuit breaker pattern
    - Health monitoring
    """
    
    def __init__(self, 
                 max_concurrent_tasks: int = 50,
                 check_interval: float = 1.0,
                 batch_size: int = 10,
                 connection_pool_size: int = 100):
        
        self.max_concurrent_tasks = max_concurrent_tasks
        self.check_interval = check_interval
        self.batch_size = batch_size
        self.connection_pool_size = connection_pool_size
        
        # Async components
        self.task_queue = asyncio.PriorityQueue()
        self.processing_tasks: Set[asyncio.Task] = set()
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.processor_task: Optional[asyncio.Task] = None
        
        # HTTP session for connection pooling
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Thread pool for CPU-bound tasks
        self.thread_executor = ThreadPoolExecutor(max_workers=10)
        
        # Rate limiting (per minute)
        self.rate_limits = {
            'sms': {'limit': 10, 'window': 60, 'sent': []},
            'email': {'limit': 100, 'window': 60, 'sent': []},
            'push': {'limit': 500, 'window': 60, 'sent': []},
            'whatsapp': {'limit': 5, 'window': 60, 'sent': []}
        }
        
        # Circuit breaker states
        self.circuit_breakers = {
            'sms': {'failures': 0, 'last_failure': None, 'state': 'closed'},
            'email': {'failures': 0, 'last_failure': None, 'state': 'closed'},
            'push': {'failures': 0, 'last_failure': None, 'state': 'closed'},
            'whatsapp': {'failures': 0, 'last_failure': None, 'state': 'closed'}
        }
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'retried': 0,
            'cancelled': 0,
            'rate_limited': 0,
            'circuit_breaker_trips': 0
        }

    async def start(self):
        """Start the async scheduler"""
        if self.is_running:
            logger.warning("Async scheduler is already running")
            return
        
        logger.info("Starting async notification scheduler...")
        
        # Initialize HTTP session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=self.connection_pool_size,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        self.is_running = True
        
        # Start scheduler and processor tasks
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.processor_task = asyncio.create_task(self._processor_loop())
        
        # Load pending reminders from database
        await self._load_pending_reminders()
        
        logger.info("Async notification scheduler started successfully")

    async def stop(self):
        """Stop the async scheduler"""
        if not self.is_running:
            return
        
        logger.info("Stopping async notification scheduler...")
        self.is_running = False
        
        # Cancel scheduler tasks
        if self.scheduler_task:
            self.scheduler_task.cancel()
        if self.processor_task:
            self.processor_task.cancel()
        
        # Cancel all processing tasks
        for task in self.processing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        # Close HTTP session
        if self.http_session:
            await self.http_session.close()
        
        # Shutdown thread executor
        self.thread_executor.shutdown(wait=True)
        
        logger.info("Async notification scheduler stopped")

    async def schedule_reminder(self, 
                              appointment_id: str,
                              reminder_type: str,
                              scheduled_time: datetime,
                              delivery_method: str,
                              priority: TaskPriority = TaskPriority.MEDIUM,
                              message_data: Optional[Dict] = None) -> str:
        """Schedule a reminder task"""
        
        task = AsyncTask(
            task_type="reminder",
            appointment_id=appointment_id,
            reminder_type=reminder_type,
            delivery_method=delivery_method,
            scheduled_time=scheduled_time,
            priority=priority,
            message_data=message_data or {}
        )
        
        # Store in database
        await self._store_task_in_db(task)
        
        # Add to queue
        await self.task_queue.put(task)
        
        logger.info(f"Scheduled {reminder_type} reminder for appointment {appointment_id}")
        return task.id

    async def cancel_appointment_reminders(self, appointment_id: str) -> int:
        """Cancel all reminders for an appointment"""
        try:
            # Cancel in database
            cancelled_count = await self._cancel_reminders_in_db(appointment_id)
            
            # Update stats
            self.stats['cancelled'] += cancelled_count
            
            logger.info(f"Cancelled {cancelled_count} reminders for appointment {appointment_id}")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"Failed to cancel reminders for appointment {appointment_id}: {str(e)}")
            return 0

    async def _scheduler_loop(self):
        """Main async scheduler loop"""
        while self.is_running:
            try:
                current_time = datetime.now()
                due_tasks = []
                
                # Collect due tasks (batch processing)
                for _ in range(self.batch_size):
                    try:
                        task = await asyncio.wait_for(self.task_queue.get(), timeout=0.1)
                        if task.scheduled_time <= current_time and task.status == TaskStatus.PENDING:
                            due_tasks.append(task)
                        else:
                            # Put back if not due
                            await self.task_queue.put(task)
                            break
                    except asyncio.TimeoutError:
                        break
                
                # Process due tasks
                for task in due_tasks:
                    if len(self.processing_tasks) < self.max_concurrent_tasks:
                        if await self._check_rate_limit_async(task.delivery_method):
                            if self._check_circuit_breaker(task.delivery_method):
                                task.status = TaskStatus.PROCESSING
                                processing_task = asyncio.create_task(self._process_task_async(task))
                                self.processing_tasks.add(processing_task)
                                processing_task.add_done_callback(self.processing_tasks.discard)
                            else:
                                # Circuit breaker open, reschedule
                                task.scheduled_time = current_time + timedelta(minutes=5)
                                await self.task_queue.put(task)
                        else:
                            # Rate limited, reschedule
                            task.scheduled_time = current_time + timedelta(seconds=30)
                            await self.task_queue.put(task)
                            self.stats['rate_limited'] += 1
                    else:
                        # Too many concurrent tasks, put back
                        await self.task_queue.put(task)
                        break
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in async scheduler loop: {str(e)}")
                await asyncio.sleep(self.check_interval)

    async def _processor_loop(self):
        """Background processor for cleanup and maintenance"""
        while self.is_running:
            try:
                # Clean up rate limits
                await self._cleanup_rate_limits_async()
                
                # Reset circuit breakers if needed
                await self._reset_circuit_breakers()
                
                # Log statistics
                if self.stats['total_processed'] % 100 == 0 and self.stats['total_processed'] > 0:
                    logger.info(f"Scheduler stats: {self.stats}")
                
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error(f"Error in processor loop: {str(e)}")
                await asyncio.sleep(60)

    async def _process_task_async(self, task: AsyncTask):
        """Process a single task asynchronously"""
        try:
            task.last_attempt = datetime.now()
            
            # Get appointment and patient data
            appointment_data = await asyncio.get_event_loop().run_in_executor(
                self.thread_executor, get_appointment_data, task.appointment_id
            )
            
            if not appointment_data:
                raise Exception(f"Appointment {task.appointment_id} not found")
            
            patient_data = await asyncio.get_event_loop().run_in_executor(
                self.thread_executor, get_patient_data, appointment_data.get('patient_id')
            )
            
            # Send notification based on delivery method
            success = False
            if task.delivery_method == 'email':
                success = await self._send_email_async(task, appointment_data, patient_data)
            elif task.delivery_method == 'sms':
                success = await self._send_sms_async(task, appointment_data, patient_data)
            elif task.delivery_method == 'push':
                success = await self._send_push_async(task, appointment_data, patient_data)
            elif task.delivery_method == 'whatsapp':
                success = await self._send_whatsapp_async(task, appointment_data, patient_data)
            
            if success:
                task.status = TaskStatus.COMPLETED
                self.stats['successful'] += 1
                await self._log_notification_async(task, 'sent', None)
            else:
                raise Exception(f"Failed to send {task.delivery_method} notification")
                
        except Exception as e:
            await self._handle_task_failure_async(task, str(e))
        
        finally:
            self.stats['total_processed'] += 1
            await self._update_task_in_db(task)

    async def _check_rate_limit_async(self, delivery_method: str) -> bool:
        """Check if delivery method is within rate limits"""
        if delivery_method not in self.rate_limits:
            return True
        
        limit_config = self.rate_limits[delivery_method]
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=limit_config['window'])
        
        # Remove old entries
        limit_config['sent'] = [
            sent_time for sent_time in limit_config['sent']
            if sent_time > window_start
        ]
        
        # Check if under limit
        if len(limit_config['sent']) < limit_config['limit']:
            limit_config['sent'].append(current_time)
            return True
        
        return False

    async def _cleanup_rate_limits_async(self):
        """Clean up old rate limit entries"""
        current_time = datetime.now()
        
        for method, config in self.rate_limits.items():
            window_start = current_time - timedelta(seconds=config['window'])
            config['sent'] = [
                sent_time for sent_time in config['sent']
                if sent_time > window_start
            ]

    def _check_circuit_breaker(self, delivery_method: str) -> bool:
        """Check circuit breaker state"""
        breaker = self.circuit_breakers.get(delivery_method, {})
        
        if breaker.get('state') == 'open':
            # Check if we should try again
            if breaker.get('last_failure'):
                if datetime.now() - breaker['last_failure'] > timedelta(minutes=5):
                    breaker['state'] = 'half-open'
                    return True
            return False
        
        return True

    async def _reset_circuit_breakers(self):
        """Reset circuit breakers that have been open for too long"""
        current_time = datetime.now()
        
        for method, breaker in self.circuit_breakers.items():
            if breaker['state'] == 'open' and breaker.get('last_failure'):
                if current_time - breaker['last_failure'] > timedelta(minutes=10):
                    breaker['state'] = 'closed'
                    breaker['failures'] = 0
                    logger.info(f"Reset circuit breaker for {method}")

    async def _handle_task_failure_async(self, task: AsyncTask, error_message: str):
        """Handle task failure with retry logic"""
        task.error_message = error_message
        task.retry_count += 1
        
        # Update circuit breaker
        breaker = self.circuit_breakers.get(task.delivery_method, {})
        breaker['failures'] = breaker.get('failures', 0) + 1
        breaker['last_failure'] = datetime.now()
        
        if breaker['failures'] >= 5:
            breaker['state'] = 'open'
            self.stats['circuit_breaker_trips'] += 1
            logger.warning(f"Circuit breaker opened for {task.delivery_method}")
        
        if task.retry_count <= task.max_retries:
            # Exponential backoff
            delay_minutes = 2 ** task.retry_count
            task.scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
            task.status = TaskStatus.RETRYING
            await self.task_queue.put(task)
            self.stats['retried'] += 1
            logger.info(f"Retrying task {task.id} in {delay_minutes} minutes")
        else:
            task.status = TaskStatus.FAILED
            self.stats['failed'] += 1
            logger.error(f"Task {task.id} failed permanently: {error_message}")
        
        await self._log_notification_async(task, 'failed', error_message)

    # Placeholder methods for actual notification sending
    async def _send_email_async(self, task: AsyncTask, appointment_data: Dict, patient_data: Dict) -> bool:
        """Send email notification asynchronously"""
        # Implementation would use aiosmtplib or similar
        await asyncio.sleep(0.1)  # Simulate async operation
        return True

    async def _send_sms_async(self, task: AsyncTask, appointment_data: Dict, patient_data: Dict) -> bool:
        """Send SMS notification asynchronously"""
        # Implementation would use async HTTP client
        await asyncio.sleep(0.1)  # Simulate async operation
        return True

    async def _send_push_async(self, task: AsyncTask, appointment_data: Dict, patient_data: Dict) -> bool:
        """Send push notification asynchronously"""
        # Implementation would use async HTTP client
        await asyncio.sleep(0.1)  # Simulate async operation
        return True

    async def _send_whatsapp_async(self, task: AsyncTask, appointment_data: Dict, patient_data: Dict) -> bool:
        """Send WhatsApp notification asynchronously"""
        # Implementation would use async HTTP client
        await asyncio.sleep(0.1)  # Simulate async operation
        return True

    # Database operations (would be implemented with async ORM)
    async def _store_task_in_db(self, task: AsyncTask):
        """Store task in database"""
        pass

    async def _update_task_in_db(self, task: AsyncTask):
        """Update task in database"""
        pass

    async def _cancel_reminders_in_db(self, appointment_id: str) -> int:
        """Cancel reminders in database"""
        return 0

    async def _load_pending_reminders(self):
        """Load pending reminders from database"""
        pass

    async def _log_notification_async(self, task: AsyncTask, status: str, error_message: Optional[str]):
        """Log notification attempt"""
        pass

    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        return {
            **self.stats,
            'queue_size': self.task_queue.qsize(),
            'processing_tasks': len(self.processing_tasks),
            'is_running': self.is_running
        }

# Global async scheduler instance
async_scheduler = AsyncNotificationScheduler()

# Async management functions
async def start_async_scheduler():
    """Start the async scheduler"""
    await async_scheduler.start()

async def stop_async_scheduler():
    """Stop the async scheduler"""
    await async_scheduler.stop()

def get_async_scheduler_status():
    """Get async scheduler status"""
    return async_scheduler.get_stats()