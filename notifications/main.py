import asyncio
import os
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn
from redis_config import test_redis_connection, REDIS_CONFIGS

# Import all notification system components
from .logging_config import NotificationLogger
from .monitoring import SystemMonitor, AlertManager
from .persistent_scheduler import PersistentNotificationScheduler
from .scheduler import ScheduleConfig
from .queue_manager import QueueManager, QueueConfig
from .failsafe_delivery import FailsafeDeliveryManager, DeliveryConfig
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .error_recovery import ErrorRecoveryManager, ErrorSeverity
from .performance import PerformanceManager, CacheStrategy
from .cache_layer import CacheManager, CacheLevel
from .database_optimization import DatabaseOptimizer
from .scalability import ScalabilityManager, ScalingStrategy
from .microservices import MicroservicesManager
from .distributed_architecture import DistributedArchitectureManager
from .backup_recovery import BackupRecoveryManager, BackupConfig, StorageProvider, BackupType


# Pydantic models for API requests
class NotificationRequest(BaseModel):
    user_id: str
    message: str
    notification_type: str = "general"
    scheduled_time: Optional[datetime] = None
    priority: str = "medium"
    channels: List[str] = ["email"]
    metadata: Dict[str, Any] = {}


class ScheduleRequest(BaseModel):
    user_id: str
    appointment_id: str
    appointment_time: datetime
    reminder_intervals: List[int] = [24, 1]  # hours before appointment
    notification_channels: List[str] = ["email", "sms"]
    custom_message: Optional[str] = None


class SystemStatusResponse(BaseModel):
    status: str
    timestamp: datetime
    components: Dict[str, Any]
    metrics: Dict[str, Any]


class NotificationResponse(BaseModel):
    notification_id: str
    status: str
    message: str
    scheduled_time: Optional[datetime] = None


# Global application state
class ApplicationState:
    def __init__(self):
        self.logger = NotificationLogger()
        self.monitor = SystemMonitor()
        self.alert_manager = AlertManager()
        
        # Core notification components
        self.scheduler = None
        self.queue_manager = None
        self.failsafe_manager = None
        self.circuit_breaker = None
        self.error_recovery = None
        
        # Performance and optimization
        self.performance_manager = None
        self.cache_manager = None
        self.db_optimizer = None
        
        # Scalability and distributed systems
        self.scalability_manager = None
        self.microservices_manager = None
        self.distributed_manager = None
        
        # Backup and recovery
        self.backup_manager = None
        
        self.running = False
    
    async def initialize(self):
        """Initialize all system components."""
        try:
            self.logger.info("Initializing notification system...")
            
            # Initialize core components
            await self._initialize_core_components()
            
            # Initialize performance components
            await self._initialize_performance_components()
            
            # Initialize scalability components
            await self._initialize_scalability_components()
            
            # Initialize backup system
            await self._initialize_backup_system()
            
            # Start all components
            await self._start_components()
            
            self.running = True
            self.logger.info("Notification system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize notification system: {e}")
            raise
    
    async def _initialize_core_components(self):
        """Initialize core notification components."""
        # Circuit breaker
        circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )
        self.circuit_breaker = CircuitBreaker(circuit_config)
        
        # Error recovery
        self.error_recovery = ErrorRecoveryManager()
        
        # Queue manager
        queue_config = QueueConfig(
            max_size=10000,
            batch_size=100,
            processing_interval=1.0,
            priority_levels=5
        )
        self.queue_manager = QueueManager(queue_config)
        
        # Failsafe delivery
        delivery_config = DeliveryConfig(
            max_retries=3,
            retry_delays=[1, 5, 15],
            fallback_channels=["email", "sms"],
            circuit_breaker_threshold=10
        )
        self.failsafe_manager = FailsafeDeliveryManager(delivery_config)
        
        # Scheduler
        schedule_config = ScheduleConfig(
            check_interval=30,
            batch_size=50,
            max_concurrent_jobs=20
        )
        self.scheduler = PersistentNotificationScheduler()
    
    async def _initialize_performance_components(self):
        """Initialize performance optimization components."""
        # Cache manager with cloud Redis
        self.cache_manager = CacheManager(
            memory_config=CacheConfig(max_size=1000, ttl=300),
            redis_config={}  # Uses cloud Redis configuration by default
        )
        
        # Performance manager
        self.performance_manager = PerformanceManager()
        
        # Database optimizer
        self.db_optimizer = DatabaseOptimizer()
    
    async def _initialize_scalability_components(self):
        """Initialize scalability components."""
        # Scalability manager
        self.scalability_manager = ScalabilityManager()
        
        # Microservices manager
        self.microservices_manager = MicroservicesManager()
        
        # Distributed architecture (if running in distributed mode)
        node_id = os.getenv('NODE_ID', 'node_1')
        host = os.getenv('NODE_HOST', 'localhost')
        port = int(os.getenv('NODE_PORT', '8001'))
        
        self.distributed_manager = DistributedArchitectureManager(node_id, host, port)
    
    async def _initialize_backup_system(self):
        """Initialize backup and recovery system."""
        # Backup configuration
        backup_config = BackupConfig(
            backup_type=BackupType.INCREMENTAL,
            storage_provider=StorageProvider.LOCAL,
            destination_path=os.getenv('BACKUP_PATH', './backups'),
            retention_days=30,
            compression_enabled=True,
            encryption_enabled=True,
            verify_after_backup=True
        )
        
        self.backup_manager = BackupRecoveryManager(backup_config)
    
    async def _start_components(self):
        """Start all system components."""
        # Test Redis connection
        try:
            if not test_redis_connection():
                raise Exception("Redis connection failed")
            self.logger.info("Redis connection successful")
        except Exception as e:
            self.logger.error(f"Redis connection test failed: {e}")
            raise
        
        # Start monitoring
        self.monitor.start()
        self.alert_manager.start()
        
        # Start core components
        self.queue_manager.start()
        self.scheduler.start()
        
        # Start performance components
        await self.performance_manager.start()
        await self.cache_manager.start()
        
        # Start scalability components
        await self.scalability_manager.start()
        await self.microservices_manager.start()
        
        # Start distributed system (if configured)
        seed_nodes_str = os.getenv('SEED_NODES', '')
        seed_nodes = []
        if seed_nodes_str:
            for node in seed_nodes_str.split(','):
                host, port = node.strip().split(':')
                seed_nodes.append((host, int(port)))
        
        await self.distributed_manager.start(seed_nodes if seed_nodes else None)
        
        # Start backup system
        self.backup_manager.start()
    
    async def shutdown(self):
        """Shutdown all system components gracefully."""
        try:
            self.logger.info("Shutting down notification system...")
            self.running = False
            
            # Stop components in reverse order
            if self.backup_manager:
                self.backup_manager.stop()
            
            if self.distributed_manager:
                await self.distributed_manager.stop()
            
            if self.microservices_manager:
                await self.microservices_manager.stop()
            
            if self.scalability_manager:
                await self.scalability_manager.stop()
            
            if self.cache_manager:
                await self.cache_manager.stop()
            
            if self.performance_manager:
                await self.performance_manager.stop()
            
            if self.scheduler:
                self.scheduler.stop()
            
            if self.queue_manager:
                self.queue_manager.stop()
            
            if self.alert_manager:
                self.alert_manager.stop()
            
            if self.monitor:
                self.monitor.stop()
            
            self.logger.info("Notification system shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Global application state instance
app_state = ApplicationState()


# FastAPI lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await app_state.initialize()
    yield
    # Shutdown
    await app_state.shutdown()


# Create FastAPI application
app = FastAPI(
    title="MediRemind Notification System",
    description="Comprehensive notification system for medical appointment reminders",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token (simplified implementation)."""
    # In production, implement proper JWT verification
    token = credentials.credentials
    if not token or token == "invalid":
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return token


# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if app_state.running else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/status", response_model=SystemStatusResponse)
async def get_system_status(token: str = Depends(verify_token)):
    """Get comprehensive system status."""
    try:
        # Collect status from all components
        components = {}
        metrics = {}
        
        if app_state.scheduler:
            components["scheduler"] = app_state.scheduler.get_status()
        
        if app_state.queue_manager:
            components["queue_manager"] = app_state.queue_manager.get_status()
        
        if app_state.performance_manager:
            components["performance"] = app_state.performance_manager.get_status()
        
        if app_state.cache_manager:
            components["cache"] = app_state.cache_manager.get_status()
        
        if app_state.scalability_manager:
            components["scalability"] = app_state.scalability_manager.get_status()
        
        if app_state.distributed_manager:
            components["distributed"] = app_state.distributed_manager.get_system_status()
        
        if app_state.backup_manager:
            components["backup"] = app_state.backup_manager.get_system_status()
        
        # System metrics
        if app_state.monitor:
            metrics = app_state.monitor.get_current_metrics()
        
        return SystemStatusResponse(
            status="operational" if app_state.running else "down",
            timestamp=datetime.now(),
            components=components,
            metrics=metrics
        )
    
    except Exception as e:
        app_state.logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


@app.post("/notifications", response_model=NotificationResponse)
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Send a notification."""
    try:
        notification_id = f"notif_{int(datetime.now().timestamp())}_{request.user_id}"
        
        # Create notification data
        notification_data = {
            "notification_id": notification_id,
            "user_id": request.user_id,
            "message": request.message,
            "notification_type": request.notification_type,
            "channels": request.channels,
            "priority": request.priority,
            "metadata": request.metadata,
            "created_at": datetime.now().isoformat()
        }
        
        if request.scheduled_time:
            # Schedule for later delivery
            await app_state.scheduler.schedule_notification(
                notification_id=notification_id,
                user_id=request.user_id,
                scheduled_time=request.scheduled_time,
                notification_data=notification_data
            )
            
            return NotificationResponse(
                notification_id=notification_id,
                status="scheduled",
                message="Notification scheduled successfully",
                scheduled_time=request.scheduled_time
            )
        else:
            # Send immediately
            await app_state.queue_manager.add_notification(notification_data)
            
            return NotificationResponse(
                notification_id=notification_id,
                status="queued",
                message="Notification queued for immediate delivery"
            )
    
    except Exception as e:
        app_state.logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")


@app.post("/schedule", response_model=NotificationResponse)
async def schedule_appointment_reminders(
    request: ScheduleRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Schedule appointment reminder notifications."""
    try:
        scheduled_notifications = []
        
        for hours_before in request.reminder_intervals:
            reminder_time = request.appointment_time - timedelta(hours=hours_before)
            
            # Skip if reminder time is in the past
            if reminder_time <= datetime.now():
                continue
            
            notification_id = f"reminder_{request.appointment_id}_{hours_before}h"
            
            message = request.custom_message or f"Reminder: You have an appointment in {hours_before} hour(s)"
            
            notification_data = {
                "notification_id": notification_id,
                "user_id": request.user_id,
                "message": message,
                "notification_type": "appointment_reminder",
                "channels": request.notification_channels,
                "priority": "high",
                "metadata": {
                    "appointment_id": request.appointment_id,
                    "appointment_time": request.appointment_time.isoformat(),
                    "hours_before": hours_before
                },
                "created_at": datetime.now().isoformat()
            }
            
            await app_state.scheduler.schedule_notification(
                notification_id=notification_id,
                user_id=request.user_id,
                scheduled_time=reminder_time,
                notification_data=notification_data
            )
            
            scheduled_notifications.append({
                "notification_id": notification_id,
                "scheduled_time": reminder_time,
                "hours_before": hours_before
            })
        
        return NotificationResponse(
            notification_id=f"appointment_{request.appointment_id}",
            status="scheduled",
            message=f"Scheduled {len(scheduled_notifications)} reminder notifications",
            scheduled_time=None
        )
    
    except Exception as e:
        app_state.logger.error(f"Error scheduling appointment reminders: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule appointment reminders")


@app.get("/notifications/{notification_id}")
async def get_notification_status(
    notification_id: str,
    token: str = Depends(verify_token)
):
    """Get the status of a specific notification."""
    try:
        # Check scheduler first
        if app_state.scheduler:
            scheduled_status = app_state.scheduler.get_notification_status(notification_id)
            if scheduled_status:
                return scheduled_status
        
        # Check queue manager
        if app_state.queue_manager:
            queue_status = app_state.queue_manager.get_notification_status(notification_id)
            if queue_status:
                return queue_status
        
        # Check failsafe manager
        if app_state.failsafe_manager:
            delivery_status = app_state.failsafe_manager.get_delivery_status(notification_id)
            if delivery_status:
                return delivery_status
        
        raise HTTPException(status_code=404, detail="Notification not found")
    
    except HTTPException:
        raise
    except Exception as e:
        app_state.logger.error(f"Error getting notification status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification status")


@app.post("/backup")
async def create_backup(
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Create a system backup."""
    try:
        if not app_state.backup_manager:
            raise HTTPException(status_code=503, detail="Backup system not available")
        
        backup_id = await app_state.backup_manager.create_notification_backup()
        
        return {
            "backup_id": backup_id,
            "status": "initiated",
            "message": "Backup process started"
        }
    
    except Exception as e:
        app_state.logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create backup")


@app.post("/restore/{backup_id}")
async def restore_backup(
    backup_id: str,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Restore from a backup."""
    try:
        if not app_state.backup_manager:
            raise HTTPException(status_code=503, detail="Backup system not available")
        
        recovery_id = await app_state.backup_manager.restore_notification_backup(backup_id)
        
        return {
            "recovery_id": recovery_id,
            "status": "initiated",
            "message": "Restore process started"
        }
    
    except Exception as e:
        app_state.logger.error(f"Error restoring backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore backup")


@app.get("/metrics")
async def get_metrics(token: str = Depends(verify_token)):
    """Get system metrics."""
    try:
        metrics = {}
        
        if app_state.monitor:
            metrics["system"] = app_state.monitor.get_current_metrics()
        
        if app_state.performance_manager:
            metrics["performance"] = app_state.performance_manager.get_performance_report()
        
        if app_state.queue_manager:
            metrics["queue"] = app_state.queue_manager.get_metrics()
        
        if app_state.scheduler:
            metrics["scheduler"] = app_state.scheduler.get_metrics()
        
        return metrics
    
    except Exception as e:
        app_state.logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals."""
    app_state.logger.info(f"Received signal {signum}, initiating shutdown...")
    asyncio.create_task(app_state.shutdown())
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    # Configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    # Run the application
    uvicorn.run(
        "notifications.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        reload=False  # Set to True for development
    )