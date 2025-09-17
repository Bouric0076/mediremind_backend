import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from queue import PriorityQueue, Queue, Empty
import json
from collections import defaultdict, deque
from supabase_client import admin_client
from celery import Celery
from celery.result import AsyncResult
from redis_config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

logger = logging.getLogger(__name__)

# Celery configuration with Redis Cloud
celery_app = Celery('mediremind_notifications')
celery_app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
    task_routes={
        'notifications.tasks.send_sms': {'queue': 'sms'},
        'notifications.tasks.send_email': {'queue': 'email'},
        'notifications.tasks.send_push': {'queue': 'push'},
    },
    # Redis Cloud specific settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10
)

class QueueType(Enum):
    """Types of notification queues"""
    IMMEDIATE = "immediate"  # For urgent notifications
    SCHEDULED = "scheduled"  # For scheduled reminders
    RETRY = "retry"  # For failed notifications
    BULK = "bulk"  # For bulk notifications
    LOW_PRIORITY = "low_priority"  # For non-critical notifications

class QueueStatus(Enum):
    """Queue status"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class QueueMetrics:
    """Metrics for queue performance"""
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    average_processing_time: float = 0.0
    peak_queue_size: int = 0
    current_queue_size: int = 0
    last_processed: Optional[datetime] = None
    processing_times: deque = field(default_factory=lambda: deque(maxlen=100))

@dataclass
class QueueConfig:
    """Configuration for a queue"""
    max_size: int = 1000
    max_workers: int = 5
    batch_size: int = 10
    processing_timeout: int = 300  # 5 minutes
    retry_delay: int = 60  # 1 minute
    max_retries: int = 3
    rate_limit: Optional[int] = None  # messages per minute
    priority_weight: float = 1.0

class NotificationQueue:
    """Individual notification queue with specific configuration"""
    
    def __init__(self, queue_type: QueueType, config: QueueConfig):
        self.queue_type = queue_type
        self.config = config
        self.queue = PriorityQueue(maxsize=config.max_size)
        self.processing_queue = Queue()
        self.status = QueueStatus.ACTIVE
        self.metrics = QueueMetrics()
        self.workers = []
        self.is_running = False
        self.lock = threading.RLock()
        self.last_rate_check = datetime.now()
        self.rate_counter = 0
        self.error_count = 0
        self.max_errors = 10
        
        # Callbacks
        self.on_message_processed: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_queue_full: Optional[Callable] = None

    def start(self):
        """Start the queue processing"""
        with self.lock:
            if self.is_running:
                return
                
            self.is_running = True
            self.status = QueueStatus.ACTIVE
            
            # Start worker threads
            for i in range(self.config.max_workers):
                worker = threading.Thread(
                    target=self._worker_loop,
                    name=f"{self.queue_type.value}_worker_{i}",
                    daemon=True
                )
                worker.start()
                self.workers.append(worker)
                
            logger.info(f"Started {self.queue_type.value} queue with {self.config.max_workers} workers")

    def stop(self):
        """Stop the queue processing"""
        with self.lock:
            if not self.is_running:
                return
                
            self.is_running = False
            self.status = QueueStatus.STOPPED
            
            # Wait for workers to finish
            for worker in self.workers:
                worker.join(timeout=5)
                
            self.workers.clear()
            logger.info(f"Stopped {self.queue_type.value} queue")

    def pause(self):
        """Pause queue processing"""
        with self.lock:
            if self.status == QueueStatus.ACTIVE:
                self.status = QueueStatus.PAUSED
                logger.info(f"Paused {self.queue_type.value} queue")

    def resume(self):
        """Resume queue processing"""
        with self.lock:
            if self.status == QueueStatus.PAUSED:
                self.status = QueueStatus.ACTIVE
                logger.info(f"Resumed {self.queue_type.value} queue")

    def enqueue(self, message: Dict, priority: int = 5) -> bool:
        """Add message to queue"""
        try:
            with self.lock:
                # Check rate limit
                if not self._check_rate_limit():
                    logger.warning(f"Rate limit exceeded for {self.queue_type.value} queue")
                    return False
                
                # Check queue size
                if self.queue.full():
                    if self.on_queue_full:
                        self.on_queue_full(self.queue_type, message)
                    logger.warning(f"{self.queue_type.value} queue is full")
                    return False
                
                # Add timestamp and queue info
                message['_enqueued_at'] = datetime.now().isoformat()
                message['_queue_type'] = self.queue_type.value
                message['_priority'] = priority
                
                # Put in queue
                self.queue.put((priority, datetime.now(), message))
                
                # Update metrics
                self.metrics.current_queue_size = self.queue.qsize()
                if self.metrics.current_queue_size > self.metrics.peak_queue_size:
                    self.metrics.peak_queue_size = self.metrics.current_queue_size
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to enqueue message in {self.queue_type.value}: {str(e)}")
            return False

    def get_status(self) -> Dict:
        """Get queue status and metrics"""
        with self.lock:
            return {
                'queue_type': self.queue_type.value,
                'status': self.status.value,
                'is_running': self.is_running,
                'queue_size': self.queue.qsize(),
                'processing_size': self.processing_queue.qsize(),
                'worker_count': len(self.workers),
                'error_count': self.error_count,
                'metrics': {
                    'total_processed': self.metrics.total_processed,
                    'successful': self.metrics.successful,
                    'failed': self.metrics.failed,
                    'average_processing_time': self.metrics.average_processing_time,
                    'peak_queue_size': self.metrics.peak_queue_size,
                    'current_queue_size': self.metrics.current_queue_size,
                    'last_processed': self.metrics.last_processed.isoformat() if self.metrics.last_processed else None
                },
                'config': {
                    'max_size': self.config.max_size,
                    'max_workers': self.config.max_workers,
                    'batch_size': self.config.batch_size,
                    'rate_limit': self.config.rate_limit
                }
            }

    def _worker_loop(self):
        """Main worker loop for processing messages"""
        while self.is_running:
            try:
                if self.status != QueueStatus.ACTIVE:
                    time.sleep(1)
                    continue
                
                # Get messages in batch
                batch = self._get_batch()
                if not batch:
                    time.sleep(0.1)
                    continue
                
                # Process batch
                self._process_batch(batch)
                
            except Exception as e:
                logger.error(f"Error in {self.queue_type.value} worker: {str(e)}")
                self._handle_worker_error(e)
                time.sleep(1)

    def _get_batch(self) -> List[Dict]:
        """Get a batch of messages to process"""
        batch = []
        batch_size = min(self.config.batch_size, self.queue.qsize())
        
        for _ in range(batch_size):
            try:
                priority, enqueued_time, message = self.queue.get_nowait()
                batch.append(message)
                self.metrics.current_queue_size = self.queue.qsize()
            except Empty:
                break
                
        return batch

    def _process_batch(self, batch: List[Dict]):
        """Process a batch of messages"""
        start_time = datetime.now()
        
        for message in batch:
            try:
                # Process individual message
                success = self._process_message(message)
                
                # Update metrics
                self.metrics.total_processed += 1
                if success:
                    self.metrics.successful += 1
                else:
                    self.metrics.failed += 1
                
                # Call callback
                if self.on_message_processed:
                    self.on_message_processed(message, success)
                    
            except Exception as e:
                logger.error(f"Error processing message in {self.queue_type.value}: {str(e)}")
                self.metrics.failed += 1
                
                if self.on_error:
                    self.on_error(message, e)
        
        # Update processing time metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        self.metrics.processing_times.append(processing_time)
        self.metrics.average_processing_time = sum(self.metrics.processing_times) / len(self.metrics.processing_times)
        self.metrics.last_processed = datetime.now()

    def _process_message(self, message: Dict) -> bool:
        """Process individual message - to be implemented by subclasses or callbacks"""
        # This is a placeholder - actual processing logic should be injected
        logger.info(f"Processing message in {self.queue_type.value} queue: {message.get('id', 'unknown')}")
        return True

    def _check_rate_limit(self) -> bool:
        """Check if rate limit allows processing"""
        if not self.config.rate_limit:
            return True
            
        now = datetime.now()
        
        # Reset counter every minute
        if (now - self.last_rate_check).total_seconds() >= 60:
            self.rate_counter = 0
            self.last_rate_check = now
            
        return self.rate_counter < self.config.rate_limit

    def _handle_worker_error(self, error: Exception):
        """Handle worker errors"""
        self.error_count += 1
        
        if self.error_count >= self.max_errors:
            logger.error(f"Too many errors in {self.queue_type.value} queue, stopping")
            self.status = QueueStatus.ERROR
            self.stop()

class QueueManager:
    """Manages multiple notification queues with different priorities and configurations"""
    
    def __init__(self):
        self.queues: Dict[QueueType, NotificationQueue] = {}
        self.is_running = False
        self.monitor_thread = None
        self.stats_thread = None
        self.global_metrics = {
            'total_messages': 0,
            'successful_messages': 0,
            'failed_messages': 0,
            'queues_active': 0,
            'average_queue_size': 0
        }
        
        # Initialize default queues
        self._initialize_default_queues()

    def _initialize_default_queues(self):
        """Initialize default queue configurations"""
        configs = {
            QueueType.IMMEDIATE: QueueConfig(
                max_size=500,
                max_workers=10,
                batch_size=5,
                processing_timeout=60,
                rate_limit=100,  # 100 per minute
                priority_weight=1.0
            ),
            QueueType.SCHEDULED: QueueConfig(
                max_size=2000,
                max_workers=5,
                batch_size=20,
                processing_timeout=300,
                rate_limit=200,  # 200 per minute
                priority_weight=0.8
            ),
            QueueType.RETRY: QueueConfig(
                max_size=1000,
                max_workers=3,
                batch_size=10,
                processing_timeout=600,
                retry_delay=300,  # 5 minutes
                max_retries=5,
                rate_limit=50,  # 50 per minute
                priority_weight=0.6
            ),
            QueueType.BULK: QueueConfig(
                max_size=5000,
                max_workers=8,
                batch_size=50,
                processing_timeout=900,
                rate_limit=500,  # 500 per minute
                priority_weight=0.4
            ),
            QueueType.LOW_PRIORITY: QueueConfig(
                max_size=1000,
                max_workers=2,
                batch_size=25,
                processing_timeout=1800,
                rate_limit=100,  # 100 per minute
                priority_weight=0.2
            )
        }
        
        for queue_type, config in configs.items():
            self.queues[queue_type] = NotificationQueue(queue_type, config)

    def start(self):
        """Start all queues and monitoring"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start all queues
        for queue in self.queues.values():
            queue.start()
            
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start stats collection thread
        self.stats_thread = threading.Thread(target=self._stats_loop, daemon=True)
        self.stats_thread.start()
        
        logger.info("Queue manager started with all queues active")

    def stop(self):
        """Stop all queues and monitoring"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Stop all queues
        for queue in self.queues.values():
            queue.stop()
            
        # Wait for monitoring threads
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        if self.stats_thread:
            self.stats_thread.join(timeout=5)
            
        logger.info("Queue manager stopped")

    def enqueue_message(self, queue_type: QueueType, message: Dict, priority: int = 5) -> bool:
        """Enqueue message to specific queue"""
        if queue_type not in self.queues:
            logger.error(f"Queue type {queue_type.value} not found")
            return False
            
        return self.queues[queue_type].enqueue(message, priority)

    def enqueue_immediate(self, message: Dict, priority: int = 1) -> bool:
        """Enqueue immediate notification"""
        return self.enqueue_message(QueueType.IMMEDIATE, message, priority)

    def enqueue_scheduled(self, message: Dict, priority: int = 3) -> bool:
        """Enqueue scheduled notification"""
        return self.enqueue_message(QueueType.SCHEDULED, message, priority)

    def enqueue_retry(self, message: Dict, priority: int = 2) -> bool:
        """Enqueue retry notification"""
        return self.enqueue_message(QueueType.RETRY, message, priority)

    def enqueue_bulk(self, messages: List[Dict], priority: int = 4) -> int:
        """Enqueue multiple messages for bulk processing"""
        successful = 0
        for message in messages:
            if self.enqueue_message(QueueType.BULK, message, priority):
                successful += 1
        return successful

    def pause_queue(self, queue_type: QueueType):
        """Pause specific queue"""
        if queue_type in self.queues:
            self.queues[queue_type].pause()

    def resume_queue(self, queue_type: QueueType):
        """Resume specific queue"""
        if queue_type in self.queues:
            self.queues[queue_type].resume()

    def get_queue_status(self, queue_type: Optional[QueueType] = None) -> Dict:
        """Get status of specific queue or all queues"""
        if queue_type:
            if queue_type in self.queues:
                return self.queues[queue_type].get_status()
            else:
                return {}
        else:
            return {
                'global_metrics': self.global_metrics.copy(),
                'queues': {qt.value: queue.get_status() for qt, queue in self.queues.items()},
                'is_running': self.is_running
            }

    def get_health_status(self) -> Dict:
        """Get overall health status of queue system"""
        total_queues = len(self.queues)
        active_queues = sum(1 for q in self.queues.values() if q.status == QueueStatus.ACTIVE)
        error_queues = sum(1 for q in self.queues.values() if q.status == QueueStatus.ERROR)
        
        health_score = (active_queues / total_queues) * 100 if total_queues > 0 else 0
        
        return {
            'health_score': health_score,
            'status': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 50 else 'critical',
            'total_queues': total_queues,
            'active_queues': active_queues,
            'error_queues': error_queues,
            'total_messages_processed': sum(q.metrics.total_processed for q in self.queues.values()),
            'total_messages_pending': sum(q.queue.qsize() for q in self.queues.values()),
            'average_processing_time': sum(q.metrics.average_processing_time for q in self.queues.values()) / total_queues if total_queues > 0 else 0
        }

    def set_message_processor(self, queue_type: QueueType, processor: Callable[[Dict], bool]):
        """Set custom message processor for specific queue"""
        if queue_type in self.queues:
            self.queues[queue_type]._process_message = processor

    def set_error_handler(self, queue_type: QueueType, handler: Callable[[Dict, Exception], None]):
        """Set custom error handler for specific queue"""
        if queue_type in self.queues:
            self.queues[queue_type].on_error = handler

    def _monitor_loop(self):
        """Monitor queue health and performance"""
        while self.is_running:
            try:
                # Check queue health
                for queue_type, queue in self.queues.items():
                    # Auto-restart failed queues
                    if queue.status == QueueStatus.ERROR and queue.error_count < queue.max_errors:
                        logger.info(f"Attempting to restart {queue_type.value} queue")
                        queue.error_count = 0
                        queue.status = QueueStatus.ACTIVE
                        queue.start()
                
                # Log health status
                health = self.get_health_status()
                if health['health_score'] < 80:
                    logger.warning(f"Queue system health degraded: {health['health_score']:.1f}%")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in queue monitor: {str(e)}")
                time.sleep(30)

    def _stats_loop(self):
        """Collect and update global statistics"""
        while self.is_running:
            try:
                # Update global metrics
                self.global_metrics['total_messages'] = sum(q.metrics.total_processed for q in self.queues.values())
                self.global_metrics['successful_messages'] = sum(q.metrics.successful for q in self.queues.values())
                self.global_metrics['failed_messages'] = sum(q.metrics.failed for q in self.queues.values())
                self.global_metrics['queues_active'] = sum(1 for q in self.queues.values() if q.status == QueueStatus.ACTIVE)
                self.global_metrics['average_queue_size'] = sum(q.queue.qsize() for q in self.queues.values()) / len(self.queues) if self.queues else 0
                
                # Store stats in database periodically
                self._store_stats_in_db()
                
                time.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in stats collection: {str(e)}")
                time.sleep(300)

    def _store_stats_in_db(self):
        """Store queue statistics in database"""
        try:
            stats_data = {
                'timestamp': datetime.now().isoformat(),
                'global_metrics': self.global_metrics,
                'queue_metrics': {qt.value: q.get_status() for qt, q in self.queues.items()},
                'health_status': self.get_health_status()
            }
            
            admin_client.table("system_stats").insert({
                'metric_type': 'queue_performance',
                'data': json.dumps(stats_data),
                'recorded_at': datetime.now().isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Failed to store queue stats: {str(e)}")

# Global queue manager instance
queue_manager = QueueManager()

# Convenience functions
def start_queue_manager():
    """Start the global queue manager"""
    queue_manager.start()

def stop_queue_manager():
    """Stop the global queue manager"""
    queue_manager.stop()

def enqueue_immediate_notification(message: Dict, priority: int = 1) -> bool:
    """Enqueue immediate notification"""
    return queue_manager.enqueue_immediate(message, priority)

def enqueue_scheduled_notification(message: Dict, priority: int = 3) -> bool:
    """Enqueue scheduled notification"""
    return queue_manager.enqueue_scheduled(message, priority)

def get_queue_health() -> Dict:
    """Get queue system health status"""
    return queue_manager.get_health_status()

__all__ = [
    'queue_manager', 'QueueManager', 'QueueType', 'QueueStatus',
    'start_queue_manager', 'stop_queue_manager', 
    'enqueue_immediate_notification', 'enqueue_scheduled_notification',
    'get_queue_health'
]