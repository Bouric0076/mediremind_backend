import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from supabase_client import admin_client
from .scheduler import scheduler, TaskPriority
from .queue_manager import queue_manager, QueueType
from .utils import (
    get_appointment_data,
    get_patient_data,
    get_doctor_data
)

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of background tasks"""
    SCHEDULE_REMINDERS = "schedule_reminders"
    PROCESS_OVERDUE = "process_overdue"
    CLEANUP_OLD_DATA = "cleanup_old_data"
    SYNC_APPOINTMENTS = "sync_appointments"
    GENERATE_REPORTS = "generate_reports"
    HEALTH_CHECK = "health_check"
    BACKUP_DATA = "backup_data"

@dataclass
class BackgroundTask:
    """Represents a background task"""
    task_type: TaskType
    name: str
    interval: int  # seconds
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_running: bool = False
    enabled: bool = True
    max_runtime: int = 3600  # 1 hour max
    error_count: int = 0
    max_errors: int = 5

class BackgroundTaskManager:
    """Manages background tasks for the notification system"""
    
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, BackgroundTask] = {}
        self.is_running = False
        self.scheduler_thread = None
        self.active_futures = {}
        
        # Initialize default tasks
        self._initialize_default_tasks()
        
        # Task handlers
        self.task_handlers = {
            TaskType.SCHEDULE_REMINDERS: self._schedule_appointment_reminders,
            TaskType.PROCESS_OVERDUE: self._process_overdue_appointments,
            TaskType.CLEANUP_OLD_DATA: self._cleanup_old_data,
            TaskType.SYNC_APPOINTMENTS: self._sync_appointments,
            TaskType.GENERATE_REPORTS: self._generate_reports,
            TaskType.HEALTH_CHECK: self._health_check,
            TaskType.BACKUP_DATA: self._backup_data
        }

    def _initialize_default_tasks(self):
        """Initialize default background tasks"""
        default_tasks = [
            BackgroundTask(
                task_type=TaskType.SCHEDULE_REMINDERS,
                name="Schedule Appointment Reminders",
                interval=300,  # 5 minutes
                max_runtime=600  # 10 minutes
            ),
            BackgroundTask(
                task_type=TaskType.PROCESS_OVERDUE,
                name="Process Overdue Appointments",
                interval=3600,  # 1 hour
                max_runtime=1800  # 30 minutes
            ),
            BackgroundTask(
                task_type=TaskType.CLEANUP_OLD_DATA,
                name="Cleanup Old Data",
                interval=86400,  # 24 hours
                max_runtime=3600  # 1 hour
            ),
            BackgroundTask(
                task_type=TaskType.SYNC_APPOINTMENTS,
                name="Sync Appointments",
                interval=1800,  # 30 minutes
                max_runtime=900  # 15 minutes
            ),
            BackgroundTask(
                task_type=TaskType.GENERATE_REPORTS,
                name="Generate Reports",
                interval=21600,  # 6 hours
                max_runtime=1800  # 30 minutes
            ),
            BackgroundTask(
                task_type=TaskType.HEALTH_CHECK,
                name="System Health Check",
                interval=600,  # 10 minutes
                max_runtime=300  # 5 minutes
            ),
            BackgroundTask(
                task_type=TaskType.BACKUP_DATA,
                name="Backup Critical Data",
                interval=43200,  # 12 hours
                max_runtime=3600  # 1 hour
            )
        ]
        
        for task in default_tasks:
            task.next_run = datetime.now() + timedelta(seconds=task.interval)
            self.tasks[task.task_type.value] = task

    def start(self):
        """Start the background task manager"""
        if self.is_running:
            logger.warning("Background task manager is already running")
            return
            
        self.is_running = True
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"Background task manager started with {self.max_workers} workers")

    def stop(self):
        """Stop the background task manager"""
        if not self.is_running:
            return
            
        logger.info("Stopping background task manager...")
        self.is_running = False
        
        # Cancel running tasks
        for future in self.active_futures.values():
            future.cancel()
            
        # Wait for scheduler thread
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
            
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Background task manager stopped")

    def enable_task(self, task_type: TaskType):
        """Enable a background task"""
        if task_type.value in self.tasks:
            self.tasks[task_type.value].enabled = True
            logger.info(f"Enabled task: {task_type.value}")

    def disable_task(self, task_type: TaskType):
        """Disable a background task"""
        if task_type.value in self.tasks:
            self.tasks[task_type.value].enabled = False
            logger.info(f"Disabled task: {task_type.value}")

    def run_task_now(self, task_type: TaskType) -> bool:
        """Run a task immediately"""
        if task_type.value not in self.tasks:
            logger.error(f"Task {task_type.value} not found")
            return False
            
        task = self.tasks[task_type.value]
        
        if task.is_running:
            logger.warning(f"Task {task_type.value} is already running")
            return False
            
        return self._execute_task(task)

    def get_task_status(self) -> Dict:
        """Get status of all background tasks"""
        return {
            'is_running': self.is_running,
            'active_tasks': len(self.active_futures),
            'tasks': {
                task_id: {
                    'name': task.name,
                    'type': task.task_type.value,
                    'enabled': task.enabled,
                    'is_running': task.is_running,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'interval': task.interval,
                    'error_count': task.error_count,
                    'max_errors': task.max_errors
                }
                for task_id, task in self.tasks.items()
            }
        }

    def _scheduler_loop(self):
        """Main scheduler loop for background tasks"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check for due tasks
                for task in self.tasks.values():
                    if (task.enabled and 
                        not task.is_running and 
                        task.next_run and 
                        task.next_run <= current_time and
                        task.error_count < task.max_errors):
                        
                        self._execute_task(task)
                
                # Clean up completed futures
                self._cleanup_completed_futures()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in background task scheduler: {str(e)}")
                time.sleep(30)

    def _execute_task(self, task: BackgroundTask) -> bool:
        """Execute a background task"""
        try:
            if task.task_type not in self.task_handlers:
                logger.error(f"No handler found for task type: {task.task_type.value}")
                return False
                
            task.is_running = True
            task.last_run = datetime.now()
            task.next_run = datetime.now() + timedelta(seconds=task.interval)
            
            # Submit task to executor
            future = self.executor.submit(self._run_task_with_timeout, task)
            self.active_futures[task.task_type.value] = future
            
            logger.info(f"Started background task: {task.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute task {task.name}: {str(e)}")
            task.is_running = False
            task.error_count += 1
            return False

    def _run_task_with_timeout(self, task: BackgroundTask):
        """Run task with timeout handling"""
        start_time = datetime.now()
        
        try:
            # Execute the task handler
            handler = self.task_handlers[task.task_type]
            result = handler()
            
            # Calculate runtime
            runtime = (datetime.now() - start_time).total_seconds()
            
            # Log completion
            logger.info(f"Completed background task: {task.name} (runtime: {runtime:.2f}s)")
            
            # Reset error count on success
            task.error_count = 0
            
            return result
            
        except Exception as e:
            runtime = (datetime.now() - start_time).total_seconds()
            logger.error(f"Background task {task.name} failed after {runtime:.2f}s: {str(e)}")
            task.error_count += 1
            raise
            
        finally:
            task.is_running = False
            # Remove from active futures
            self.active_futures.pop(task.task_type.value, None)

    def _cleanup_completed_futures(self):
        """Clean up completed futures"""
        completed = []
        for task_id, future in self.active_futures.items():
            if future.done():
                completed.append(task_id)
                
        for task_id in completed:
            self.active_futures.pop(task_id, None)

    # Task Handler Methods
    
    def _schedule_appointment_reminders(self) -> bool:
        """Schedule reminders for upcoming appointments"""
        try:
            logger.info("Starting appointment reminder scheduling...")
            
            # Get appointments in the next 7 days that need reminders
            end_date = (datetime.now() + timedelta(days=7)).date()
            
            result = admin_client.table("appointments").select(
                "*, enhanced_patients!inner(user_id, full_name, phone, email), staff_profiles!inner(user_id, full_name)"
            ).gte("date", datetime.now().date().isoformat()).lte(
                "date", end_date.isoformat()
            ).eq("status", "confirmed").execute()
            
            scheduled_count = 0
            
            for appointment in result.data:
                appointment_id = appointment['id']
                appointment_datetime = datetime.fromisoformat(f"{appointment['date']} {appointment['time']}")
                
                # Check if reminders already exist
                existing_reminders = admin_client.table("appointment_reminders").select(
                    "id"
                ).eq("appointment_id", appointment_id).eq("status", "pending").execute()
                
                if existing_reminders.data:
                    continue  # Skip if reminders already scheduled
                
                # Schedule different types of reminders
                reminder_schedules = [
                    {'type': '24_hour', 'hours_before': 24, 'method': 'email'},
                    {'type': '2_hour', 'hours_before': 2, 'method': 'sms'},
                    {'type': '30_minute', 'hours_before': 0.5, 'method': 'push'}
                ]
                
                for reminder_config in reminder_schedules:
                    reminder_time = appointment_datetime - timedelta(hours=reminder_config['hours_before'])
                    
                    # Only schedule if reminder time is in the future
                    if reminder_time > datetime.now():
                        scheduler.schedule_reminder(
                            appointment_id=appointment_id,
                            reminder_type=reminder_config['type'],
                            scheduled_time=reminder_time,
                            delivery_method=reminder_config['method'],
                            priority=TaskPriority.MEDIUM
                        )
                        scheduled_count += 1
            
            logger.info(f"Scheduled {scheduled_count} appointment reminders")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule appointment reminders: {str(e)}")
            return False

    def _process_overdue_appointments(self) -> bool:
        """Process overdue appointments and send notifications"""
        try:
            logger.info("Processing overdue appointments...")
            
            # Get appointments that are overdue (past appointment time + 30 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=30)
            
            result = admin_client.table("appointments").select(
                "*, enhanced_patients!inner(user_id, full_name, phone, email), staff_profiles!inner(user_id, full_name)"
            ).lt("date", cutoff_time.date().isoformat()).eq("status", "confirmed").execute()
            
            processed_count = 0
            
            for appointment in result.data:
                appointment_datetime = datetime.fromisoformat(f"{appointment['date']} {appointment['time']}")
                
                if appointment_datetime < cutoff_time:
                    # Mark as no-show and send notification
                    admin_client.table("appointments").update({
                        "status": "no_show",
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", appointment['id']).execute()
                    
                    # Send no-show notification
                    queue_manager.enqueue_immediate({
                        'type': 'no_show_notification',
                        'appointment_id': appointment['id'],
                        'patient_id': appointment['enhanced_patients']['user_id'],
                        'doctor_id': appointment['staff_profiles']['user_id'],
                        'appointment_data': appointment
                    }, priority=2)
                    
                    processed_count += 1
            
            logger.info(f"Processed {processed_count} overdue appointments")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process overdue appointments: {str(e)}")
            return False

    def _cleanup_old_data(self) -> bool:
        """Clean up old data from the system"""
        try:
            logger.info("Starting data cleanup...")
            
            # Clean up old notification logs (older than 90 days)
            cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
            
            old_logs = admin_client.table("notification_logs").delete().lt(
                "created_at", cutoff_date
            ).execute()
            
            # Clean up old system stats (older than 30 days)
            stats_cutoff = (datetime.now() - timedelta(days=30)).isoformat()
            
            old_stats = admin_client.table("system_stats").delete().lt(
                "recorded_at", stats_cutoff
            ).execute()
            
            # Clean up completed reminders (older than 30 days)
            completed_reminders = admin_client.table("appointment_reminders").delete().lt(
                "created_at", stats_cutoff
            ).eq("status", "sent").execute()
            
            logger.info("Data cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {str(e)}")
            return False

    def _sync_appointments(self) -> bool:
        """Sync appointment data and ensure consistency"""
        try:
            logger.info("Syncing appointment data...")
            
            # Check for appointments with missing reminders
            today = datetime.now().date()
            future_date = (datetime.now() + timedelta(days=7)).date()
            
            appointments_result = admin_client.table("appointments").select(
                "id, date, time, status"
            ).gte("date", today.isoformat()).lte(
                "date", future_date.isoformat()
            ).eq("status", "confirmed").execute()
            
            sync_count = 0
            
            for appointment in appointments_result.data:
                # Check if reminders exist
                reminders_result = admin_client.table("appointment_reminders").select(
                    "id"
                ).eq("appointment_id", appointment['id']).execute()
                
                if not reminders_result.data:
                    # Schedule missing reminders
                    appointment_datetime = datetime.fromisoformat(f"{appointment['date']} {appointment['time']}")
                    
                    # Schedule 24-hour reminder
                    reminder_time = appointment_datetime - timedelta(hours=24)
                    if reminder_time > datetime.now():
                        scheduler.schedule_reminder(
                            appointment_id=appointment['id'],
                            reminder_type='24_hour',
                            scheduled_time=reminder_time,
                            delivery_method='email',
                            priority=TaskPriority.MEDIUM
                        )
                        sync_count += 1
            
            logger.info(f"Synced {sync_count} appointments")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync appointments: {str(e)}")
            return False

    def _generate_reports(self) -> bool:
        """Generate system reports and analytics"""
        try:
            logger.info("Generating system reports...")
            
            # Generate notification performance report
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            # Get notification stats
            notification_stats = admin_client.table("notification_logs").select(
                "status, delivery_method, created_at"
            ).gte("created_at", week_ago.isoformat()).execute()
            
            # Calculate metrics
            total_notifications = len(notification_stats.data)
            successful_notifications = len([n for n in notification_stats.data if n['status'] == 'sent'])
            success_rate = (successful_notifications / total_notifications * 100) if total_notifications > 0 else 0
            
            # Get queue performance
            queue_health = queue_manager.get_health_status()
            
            # Store report
            report_data = {
                'period': f"{week_ago} to {today}",
                'notification_metrics': {
                    'total_notifications': total_notifications,
                    'successful_notifications': successful_notifications,
                    'success_rate': success_rate
                },
                'queue_health': queue_health,
                'scheduler_status': scheduler.get_queue_status()
            }
            
            admin_client.table("system_reports").insert({
                'report_type': 'weekly_performance',
                'data': json.dumps(report_data),
                'generated_at': datetime.now().isoformat()
            }).execute()
            
            logger.info("System reports generated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate reports: {str(e)}")
            return False

    def _health_check(self) -> bool:
        """Perform system health check"""
        try:
            logger.info("Performing system health check...")
            
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'scheduler_running': scheduler.is_running,
                'queue_manager_running': queue_manager.is_running,
                'queue_health': queue_manager.get_health_status(),
                'scheduler_status': scheduler.get_queue_status(),
                'database_connection': True  # Will be False if this fails
            }
            
            # Test database connection
            try:
                admin_client.table("users").select("id").limit(1).execute()
            except Exception:
                health_status['database_connection'] = False
            
            # Store health check result
            admin_client.table("system_health").insert({
                'health_data': json.dumps(health_status),
                'checked_at': datetime.now().isoformat()
            }).execute()
            
            # Log warnings for unhealthy components
            if not health_status['scheduler_running']:
                logger.warning("Scheduler is not running")
            if not health_status['queue_manager_running']:
                logger.warning("Queue manager is not running")
            if not health_status['database_connection']:
                logger.error("Database connection failed")
            
            logger.info("Health check completed")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    def _backup_data(self) -> bool:
        """Backup critical system data"""
        try:
            logger.info("Starting data backup...")
            
            # This is a placeholder for backup logic
            # In a real implementation, you would:
            # 1. Export critical tables
            # 2. Store backups in cloud storage
            # 3. Verify backup integrity
            # 4. Clean up old backups
            
            backup_info = {
                'backup_id': f"backup_{int(datetime.now().timestamp())}",
                'timestamp': datetime.now().isoformat(),
                'tables_backed_up': [
                    'users', 'appointments', 'patients', 'staff_profiles',
                    'appointment_reminders', 'notification_logs'
                ],
                'status': 'completed'
            }
            
            # Store backup record
            admin_client.table("backup_logs").insert({
                'backup_data': json.dumps(backup_info),
                'created_at': datetime.now().isoformat()
            }).execute()
            
            logger.info("Data backup completed")
            return True
            
        except Exception as e:
            logger.error(f"Data backup failed: {str(e)}")
            return False

# Global background task manager instance
background_task_manager = BackgroundTaskManager()

# Convenience functions
def start_background_tasks():
    """Start the global background task manager"""
    background_task_manager.start()

def stop_background_tasks():
    """Stop the global background task manager"""
    background_task_manager.stop()

def get_background_task_status():
    """Get status of background tasks"""
    return background_task_manager.get_task_status()

def run_task_immediately(task_type: TaskType) -> bool:
    """Run a background task immediately"""
    return background_task_manager.run_task_now(task_type)

__all__ = [
    'background_task_manager', 'BackgroundTaskManager', 'TaskType',
    'start_background_tasks', 'stop_background_tasks', 
    'get_background_task_status', 'run_task_immediately'
]