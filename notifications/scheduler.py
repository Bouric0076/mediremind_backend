import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from queue import PriorityQueue, Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from supabase_client import admin_client
from .utils import (
    send_appointment_reminder,
    send_appointment_confirmation,
    send_appointment_update
)
from .push_notifications import push_notifications
from .email_client import email_client

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Priority levels for scheduled tasks"""
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TaskStatus(Enum):
    """Status of scheduled tasks"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

@dataclass
class ScheduledTask:
    """Represents a scheduled notification task"""
    id: str
    task_type: str
    priority: TaskPriority
    scheduled_time: datetime
    appointment_id: str
    recipient_id: str
    delivery_method: str
    message_data: Dict
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    last_attempt: datetime = None
    error_message: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def __lt__(self, other):
        """For priority queue ordering"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.scheduled_time < other.scheduled_time

class NotificationScheduler:
    """Advanced scheduler for managing appointment reminders and notifications"""
    
    def __init__(self, max_workers: int = 10, check_interval: int = 30):
        self.max_workers = max_workers
        self.check_interval = check_interval
        self.task_queue = PriorityQueue()
        self.processing_queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.is_running = False
        self.scheduler_thread = None
        self.processor_thread = None
        self.active_tasks = {}
        self.task_history = []
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'retried': 0,
            'cancelled': 0
        }
        
        # Rate limiting
        self.rate_limits = {
            'sms': {'limit': 100, 'window': 3600, 'sent': []},  # 100 per hour
            'email': {'limit': 1000, 'window': 3600, 'sent': []},  # 1000 per hour
            'push': {'limit': 5000, 'window': 3600, 'sent': []},  # 5000 per hour
            'whatsapp': {'limit': 50, 'window': 3600, 'sent': []}  # 50 per hour
        }

    def start(self):
        """Start the scheduler service (delegated to Celery beat)"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        self.is_running = True
        logger.info("Notification scheduler status set to running. Task dispatch is managed by Celery beat.")
        
        # Optional: Load pending reminders if needed for immediate operations
        self._load_pending_reminders()
        
        logger.info(f"Notification scheduler initialized with {self.max_workers} workers (no internal threads)")

    def stop(self):
        """Stop the scheduler service"""
        if not self.is_running:
            return
            
        logger.info("Stopping notification scheduler (no internal threads to join)...")
        self.is_running = False
        
        # No thread joins or executor shutdown needed since threads aren't started
        logger.info("Notification scheduler stopped")

    def schedule_reminder(self, appointment_id: str, reminder_type: str, 
                         scheduled_time: datetime, delivery_method: str = 'sms',
                         priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """Schedule a new reminder task"""
        try:
            # Get appointment data
            appointment_result = admin_client.table("appointments").select(
                "*, enhanced_patients!inner(user_id, full_name, phone, email), staff_profiles!inner(user_id, full_name)"
            ).eq("id", appointment_id).single().execute()
            
            if not appointment_result.data:
                raise ValueError(f"Appointment {appointment_id} not found")
                
            appointment = appointment_result.data
            patient = appointment['enhanced_patients']
            doctor = appointment['staff_profiles']
            
            # Create task
            task = ScheduledTask(
                id=f"{appointment_id}_{reminder_type}_{int(scheduled_time.timestamp())}",
                task_type="reminder",
                priority=priority,
                scheduled_time=scheduled_time,
                appointment_id=appointment_id,
                recipient_id=patient['user_id'],
                delivery_method=delivery_method,
                message_data={
                    'appointment_id': appointment_id,
                    'patient_name': patient['full_name'],
                    'doctor_name': doctor['full_name'],
                    'appointment_date': appointment['date'],
                    'appointment_time': appointment['time'],
                    'location': appointment.get('location', 'Clinic'),
                    'reminder_type': reminder_type
                }
            )
            
            # Add to queue
            self.task_queue.put(task)
            
            # Store in database
            self._store_reminder_in_db(task)
            
            logger.info(f"Scheduled {reminder_type} reminder for appointment {appointment_id} at {scheduled_time}")
            return task.id
            
        except Exception as e:
            logger.error(f"Failed to schedule reminder: {str(e)}")
            raise

    def schedule_notification(self, notification_type: str, appointment_id: str,
                            recipient_id: str, delivery_method: str,
                            message_data: Dict, priority: TaskPriority = TaskPriority.HIGH) -> str:
        """Schedule an immediate notification"""
        task = ScheduledTask(
            id=f"{appointment_id}_{notification_type}_{int(datetime.now().timestamp())}",
            task_type=notification_type,
            priority=priority,
            scheduled_time=datetime.now(),
            appointment_id=appointment_id,
            recipient_id=recipient_id,
            delivery_method=delivery_method,
            message_data=message_data
        )
        
        self.task_queue.put(task)
        logger.info(f"Scheduled immediate {notification_type} notification for appointment {appointment_id}")
        return task.id

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        try:
            # Update in database
            admin_client.table("appointment_reminders").update({
                "status": "cancelled"
            }).eq("id", task_id).execute()
            
            # Update stats
            self.stats['cancelled'] += 1
            
            logger.info(f"Cancelled task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            return False

    def cancel_appointment_reminders(self, appointment_id: str) -> int:
        """
        Cancel all pending reminders for a specific appointment.
        
        Args:
            appointment_id: UUID of the appointment to cancel reminders for
            
        Returns:
            int: Number of reminders cancelled
        """
        try:
            # Cancel in database
            result = admin_client.table("appointment_reminders").update({
                "status": "cancelled",
                "cancelled_at": datetime.now().isoformat()
            }).eq("appointment_id", appointment_id).in_("status", ["pending", "retrying"]).execute()
            
            cancelled_count = len(result.data) if result.data else 0
            
            # Remove from in-memory queues
            # Note: This is a simplified approach. In a production system,
            # you might want to implement a more sophisticated queue management
            temp_queue = PriorityQueue()
            removed_count = 0
            
            # Remove from main task queue
            while not self.task_queue.empty():
                try:
                    task = self.task_queue.get_nowait()
                    if task.appointment_id != appointment_id:
                        temp_queue.put(task)
                    else:
                        removed_count += 1
                        task.status = TaskStatus.CANCELLED
                except Empty:
                    break
            
            # Put remaining tasks back
            while not temp_queue.empty():
                self.task_queue.put(temp_queue.get())
            
            # Remove from processing queue
            temp_processing = PriorityQueue()
            while not self.processing_queue.empty():
                try:
                    task = self.processing_queue.get_nowait()
                    if task.appointment_id != appointment_id:
                        temp_processing.put(task)
                    else:
                        removed_count += 1
                        task.status = TaskStatus.CANCELLED
                except Empty:
                    break
            
            # Put remaining tasks back
            while not temp_processing.empty():
                self.processing_queue.put(temp_processing.get())
            
            # Remove from active tasks
            active_to_remove = []
            for task_id, task in self.active_tasks.items():
                if task.appointment_id == appointment_id:
                    active_to_remove.append(task_id)
                    task.status = TaskStatus.CANCELLED
            
            for task_id in active_to_remove:
                self.active_tasks.pop(task_id, None)
                removed_count += 1
            
            # Update stats
            self.stats['cancelled'] += removed_count
            
            logger.info(f"Cancelled {cancelled_count} database reminders and {removed_count} in-memory tasks for appointment {appointment_id}")
            return max(cancelled_count, removed_count)
            
        except Exception as e:
            logger.error(f"Failed to cancel reminders for appointment {appointment_id}: {str(e)}")
            return 0

    def get_queue_status(self) -> Dict:
        """Get current queue status and statistics"""
        return {
            'is_running': self.is_running,
            'queue_size': self.task_queue.qsize(),
            'processing_size': self.processing_queue.qsize(),
            'active_tasks': len(self.active_tasks),
            'stats': self.stats.copy(),
            'rate_limits': {method: len(data['sent']) for method, data in self.rate_limits.items()}
        }

    def _scheduler_loop(self):
        """Main scheduler loop that checks for due tasks (disabled; Celery beat handles scheduling)"""
        logger.info("_scheduler_loop disabled. Celery beat processes due tasks via tasks.process_pending_reminders.")
        return

    def _processor_loop(self):
        """Process tasks from the processing queue (disabled; processing done in Celery tasks)"""
        logger.info("_processor_loop disabled. Task processing occurs within Celery task handlers.")
        return

    def _process_task(self, task: ScheduledTask) -> Tuple[bool, str]:
        """Process a single notification task"""
        try:
            task.last_attempt = datetime.now()
            
            # Update rate limit
            self.rate_limits[task.delivery_method]['sent'].append(datetime.now())
            
            # Process based on task type
            if task.task_type == "reminder":
                success, message = self._send_reminder(task)
            elif task.task_type == "confirmation":
                success, message = self._send_confirmation(task)
            elif task.task_type == "update":
                success, message = self._send_update(task)
            else:
                return False, f"Unknown task type: {task.task_type}"
            
            # Log notification
            self._log_notification(task, success, message)
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {str(e)}")
            return False, str(e)

    def _send_reminder(self, task: ScheduledTask) -> Tuple[bool, str]:
        """Send appointment reminder"""
        try:
            if task.delivery_method == 'email':
                return email_client.send_appointment_reminder_email(
                    task.message_data,
                    task.message_data['patient_email']
                )
            elif task.delivery_method == 'push':
                return push_notifications.send_appointment_reminder_push(
                    task.recipient_id,
                    task.message_data
                )
            elif task.delivery_method == 'sms':
                return False, "SMS delivery is no longer supported"
            else:
                return False, f"Unsupported delivery method: {task.delivery_method}"
                
        except Exception as e:
            return False, str(e)

    def _send_confirmation(self, task: ScheduledTask) -> Tuple[bool, str]:
        """Send appointment confirmation"""
        return send_appointment_confirmation(
            task.appointment_id,
            task.message_data.get('confirmation_type', 'confirmed')
        )

    def _send_update(self, task: ScheduledTask) -> Tuple[bool, str]:
        """Send appointment update"""
        return send_appointment_update(
            task.appointment_id,
            task.message_data.get('update_type', 'update'),
            task.message_data.get('update_message', '')
        )

    def _handle_task_completion(self, task: ScheduledTask, result: Tuple[bool, str]):
        """Handle successful task completion"""
        success, message = result
        
        if success:
            task.status = TaskStatus.COMPLETED
            self.stats['successful'] += 1
            
            # Update database
            admin_client.table("appointment_reminders").update({
                "status": "sent",
                "sent_at": datetime.now().isoformat()
            }).eq("id", task.id).execute()
            
        else:
            self._handle_task_failure(task, message)
        
        # Remove from active tasks
        self.active_tasks.pop(task.id, None)
        self.stats['total_processed'] += 1
        
        # Add to history
        self.task_history.append({
            'task_id': task.id,
            'status': task.status.value,
            'completed_at': datetime.now(),
            'message': message
        })
        
        # Keep only last 1000 entries in history
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]

    def _handle_task_failure(self, task: ScheduledTask, error_message: str):
        """Handle task failure and retry logic"""
        task.error_message = error_message
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # Retry with exponential backoff
            retry_delay = min(300, 30 * (2 ** (task.retry_count - 1)))  # Max 5 minutes
            task.scheduled_time = datetime.now() + timedelta(seconds=retry_delay)
            task.status = TaskStatus.RETRYING
            
            # Put back in queue for retry
            self.task_queue.put(task)
            self.stats['retried'] += 1
            
            logger.warning(f"Task {task.id} failed, retrying in {retry_delay} seconds (attempt {task.retry_count}/{task.max_retries})")
            
            # Update database
            admin_client.table("appointment_reminders").update({
                "status": "failed",
                "error_message": error_message,
                "retry_count": task.retry_count
            }).eq("id", task.id).execute()
            
        else:
            task.status = TaskStatus.FAILED
            self.stats['failed'] += 1
            
            logger.error(f"Task {task.id} failed permanently after {task.max_retries} retries: {error_message}")
            
            # Update database
            admin_client.table("appointment_reminders").update({
                "status": "failed",
                "error_message": error_message
            }).eq("id", task.id).execute()

    def _check_rate_limit(self, delivery_method: str) -> bool:
        """Check if delivery method is within rate limits"""
        if delivery_method not in self.rate_limits:
            return True
            
        limit_data = self.rate_limits[delivery_method]
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=limit_data['window'])
        
        # Count recent sends
        recent_sends = [t for t in limit_data['sent'] if t > window_start]
        
        return len(recent_sends) < limit_data['limit']

    def _cleanup_rate_limits(self):
        """Clean up old rate limit entries"""
        current_time = datetime.now()
        
        for method, data in self.rate_limits.items():
            window_start = current_time - timedelta(seconds=data['window'])
            data['sent'] = [t for t in data['sent'] if t > window_start]

    def _load_pending_reminders(self):
        """Load pending reminders from database on startup"""
        try:
            result = admin_client.table("appointment_reminders").select(
                "*, appointments!inner(*, enhanced_patients!inner(user_id, full_name, phone, email), staff_profiles!inner(user_id, full_name))"
            ).eq("status", "pending").execute()
            
            for reminder in result.data:
                appointment = reminder['appointments']
                patient = appointment['enhanced_patients']
                doctor = appointment['staff_profiles']
                
                task = ScheduledTask(
                    id=reminder['id'],
                    task_type="reminder",
                    priority=TaskPriority.MEDIUM,
                    scheduled_time=datetime.fromisoformat(reminder['scheduled_time']),
                    appointment_id=reminder['appointment_id'],
                    recipient_id=patient['user_id'],
                    delivery_method=reminder['delivery_method'],
                    message_data={
                        'appointment_id': appointment['id'],
                        'patient_name': patient['full_name'],
                        'patient_phone': patient['phone'],
                        'patient_email': patient['email'],
                        'doctor_name': doctor['full_name'],
                        'appointment_date': appointment['date'],
                        'appointment_time': appointment['time'],
                        'location': appointment.get('location', 'Clinic'),
                        'reminder_type': reminder['reminder_type']
                    },
                    retry_count=reminder.get('retry_count', 0)
                )
                
                self.task_queue.put(task)
                
            logger.info(f"Loaded {len(result.data)} pending reminders from database")
            
        except Exception as e:
            logger.error(f"Failed to load pending reminders: {str(e)}")

    def _store_reminder_in_db(self, task: ScheduledTask):
        """Store reminder task in database"""
        try:
            admin_client.table("appointment_reminders").insert({
                "id": task.id,
                "appointment_id": task.appointment_id,
                "reminder_type": task.message_data.get('reminder_type', 'custom'),
                "scheduled_time": task.scheduled_time.isoformat(),
                "status": task.status.value,
                "delivery_method": task.delivery_method,
                "recipient_id": task.recipient_id,
                "message_content": json.dumps(task.message_data),
                "retry_count": task.retry_count,
                "max_retries": task.max_retries
            }).execute()
            
        except Exception as e:
            logger.error(f"Failed to store reminder in database: {str(e)}")

    def _log_notification(self, task: ScheduledTask, success: bool, message: str):
        """Log notification attempt"""
        try:
            # Get recipient contact info
            recipient_contact = ""
            if task.delivery_method == 'sms':
                recipient_contact = task.message_data.get('patient_phone', '')
            elif task.delivery_method == 'email':
                recipient_contact = task.message_data.get('patient_email', '')
            elif task.delivery_method == 'push':
                recipient_contact = task.recipient_id
            
            admin_client.table("notification_logs").insert({
                "user_id": task.recipient_id,
                "appointment_id": task.appointment_id,
                "reminder_id": task.id,
                "notification_type": task.task_type,
                "delivery_method": task.delivery_method,
                "recipient_contact": recipient_contact,
                "message_content": json.dumps(task.message_data),
                "status": "sent" if success else "failed",
                "error_message": None if success else message,
                "sent_at": datetime.now().isoformat() if success else None
            }).execute()
            
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")

# Global scheduler instance
scheduler = NotificationScheduler()

# Auto-start scheduler when module is imported
def start_scheduler():
    """Start the global scheduler instance"""
    if not scheduler.is_running:
        scheduler.start()

def stop_scheduler():
    """Stop the global scheduler instance"""
    if scheduler.is_running:
        scheduler.stop()

def get_scheduler_status():
    """Get status of the global scheduler"""
    return scheduler.get_queue_status()

__all__ = ['scheduler', 'NotificationScheduler', 'TaskPriority', 'TaskStatus', 'start_scheduler', 'stop_scheduler', 'get_scheduler_status']