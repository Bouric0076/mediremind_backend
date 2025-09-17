import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
import logging

from .logging_config import NotificationLogger
from .monitoring import SystemMonitor
from .scalability import LoadBalancer, ServiceType, ServiceInstance


class ServiceStatus(Enum):
    """Service status enumeration."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class MessageType(Enum):
    """Inter-service message types."""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    COMMAND = "command"
    HEARTBEAT = "heartbeat"


class CommunicationProtocol(Enum):
    """Communication protocols between services."""
    HTTP_REST = "http_rest"
    MESSAGE_QUEUE = "message_queue"
    GRPC = "grpc"
    WEBSOCKET = "websocket"


@dataclass
class ServiceMessage:
    """Message structure for inter-service communication."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    source_service: str = ""
    target_service: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds


@dataclass
class ServiceConfig:
    """Configuration for a microservice."""
    service_name: str
    service_type: ServiceType
    host: str = "localhost"
    port: int = 8000
    health_check_endpoint: str = "/health"
    metrics_endpoint: str = "/metrics"
    max_connections: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    circuit_breaker_enabled: bool = True
    load_balancing_enabled: bool = True


class BaseService(ABC):
    """Base class for all microservices."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.service_id = f"{config.service_name}_{uuid.uuid4().hex[:8]}"
        self.status = ServiceStatus.STOPPED
        self.logger = NotificationLogger()
        self.start_time = None
        self.message_handlers: Dict[str, Callable] = {}
        self.health_checks: List[Callable] = []
        self._running = False
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    @abstractmethod
    async def initialize(self):
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def process_message(self, message: ServiceMessage) -> Optional[ServiceMessage]:
        """Process incoming messages."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup resources before shutdown."""
        pass
    
    async def start(self):
        """Start the service."""
        try:
            self.status = ServiceStatus.STARTING
            self.logger.info(f"Starting service {self.service_id}")
            
            await self.initialize()
            
            self.status = ServiceStatus.RUNNING
            self.start_time = datetime.now()
            self._running = True
            
            self.logger.info(f"Service {self.service_id} started successfully")
            
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.logger.error(f"Failed to start service {self.service_id}: {e}")
            raise
    
    async def stop(self):
        """Stop the service."""
        try:
            self.status = ServiceStatus.STOPPING
            self.logger.info(f"Stopping service {self.service_id}")
            
            self._running = False
            await self.cleanup()
            
            self._executor.shutdown(wait=True)
            
            self.status = ServiceStatus.STOPPED
            self.logger.info(f"Service {self.service_id} stopped")
            
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.logger.error(f"Error stopping service {self.service_id}: {e}")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a message handler."""
        self.message_handlers[message_type] = handler
    
    def add_health_check(self, check_func: Callable):
        """Add a health check function."""
        self.health_checks.append(check_func)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health_status = {
            'service_id': self.service_id,
            'service_name': self.config.service_name,
            'status': self.status.value,
            'uptime': self._get_uptime(),
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Run custom health checks
        for i, check in enumerate(self.health_checks):
            try:
                check_result = await check() if asyncio.iscoroutinefunction(check) else check()
                health_status['checks'][f'check_{i}'] = {
                    'status': 'healthy' if check_result else 'unhealthy',
                    'result': check_result
                }
            except Exception as e:
                health_status['checks'][f'check_{i}'] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_status
    
    def _get_uptime(self) -> Optional[float]:
        """Get service uptime in seconds."""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            'service_id': self.service_id,
            'service_name': self.config.service_name,
            'status': self.status.value,
            'uptime': self._get_uptime(),
            'memory_usage': self._get_memory_usage(),
            'cpu_usage': self._get_cpu_usage(),
            'active_connections': getattr(self, 'active_connections', 0),
            'processed_messages': getattr(self, 'processed_messages', 0),
            'error_count': getattr(self, 'error_count', 0)
        }
    
    def _get_memory_usage(self) -> float:
        """Get memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.cpu_percent()
        except:
            return 0.0


class NotificationSchedulerService(BaseService):
    """Microservice for notification scheduling."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.scheduled_tasks = {}
        self.processed_messages = 0
        self.error_count = 0
    
    async def initialize(self):
        """Initialize the scheduler service."""
        # Register message handlers
        self.register_message_handler('schedule_notification', self._handle_schedule_notification)
        self.register_message_handler('cancel_notification', self._handle_cancel_notification)
        self.register_message_handler('get_scheduled_tasks', self._handle_get_scheduled_tasks)
        
        # Add health checks
        self.add_health_check(self._check_scheduler_health)
        
        self.logger.info("Notification scheduler service initialized")
    
    async def process_message(self, message: ServiceMessage) -> Optional[ServiceMessage]:
        """Process incoming messages."""
        try:
            self.processed_messages += 1
            
            handler = self.message_handlers.get(message.payload.get('action'))
            if handler:
                result = await handler(message)
                return ServiceMessage(
                    message_type=MessageType.RESPONSE,
                    source_service=self.service_id,
                    target_service=message.source_service,
                    payload=result,
                    correlation_id=message.message_id
                )
            else:
                self.error_count += 1
                return ServiceMessage(
                    message_type=MessageType.RESPONSE,
                    source_service=self.service_id,
                    target_service=message.source_service,
                    payload={'error': f'Unknown action: {message.payload.get("action")}'},
                    correlation_id=message.message_id
                )
        
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error processing message: {e}")
            return ServiceMessage(
                message_type=MessageType.RESPONSE,
                source_service=self.service_id,
                target_service=message.source_service,
                payload={'error': str(e)},
                correlation_id=message.message_id
            )
    
    async def _handle_schedule_notification(self, message: ServiceMessage) -> Dict[str, Any]:
        """Handle notification scheduling request."""
        payload = message.payload
        task_id = str(uuid.uuid4())
        
        scheduled_task = {
            'task_id': task_id,
            'appointment_id': payload.get('appointment_id'),
            'user_id': payload.get('user_id'),
            'scheduled_time': payload.get('scheduled_time'),
            'message': payload.get('message'),
            'priority': payload.get('priority', 'medium'),
            'created_at': datetime.now().isoformat()
        }
        
        self.scheduled_tasks[task_id] = scheduled_task
        
        return {
            'success': True,
            'task_id': task_id,
            'scheduled_time': scheduled_task['scheduled_time']
        }
    
    async def _handle_cancel_notification(self, message: ServiceMessage) -> Dict[str, Any]:
        """Handle notification cancellation request."""
        task_id = message.payload.get('task_id')
        
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            return {'success': True, 'message': f'Task {task_id} cancelled'}
        else:
            return {'success': False, 'message': f'Task {task_id} not found'}
    
    async def _handle_get_scheduled_tasks(self, message: ServiceMessage) -> Dict[str, Any]:
        """Handle request for scheduled tasks."""
        return {
            'success': True,
            'tasks': list(self.scheduled_tasks.values()),
            'count': len(self.scheduled_tasks)
        }
    
    async def _check_scheduler_health(self) -> bool:
        """Check scheduler health."""
        # Check if we can access scheduled tasks
        try:
            task_count = len(self.scheduled_tasks)
            return task_count >= 0  # Simple check
        except:
            return False
    
    async def cleanup(self):
        """Cleanup scheduler resources."""
        self.scheduled_tasks.clear()
        self.logger.info("Scheduler service cleanup completed")


class NotificationDeliveryService(BaseService):
    """Microservice for notification delivery."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.delivery_queue = []
        self.processed_messages = 0
        self.error_count = 0
        self.delivery_stats = {
            'sms_sent': 0,
            'email_sent': 0,
            'push_sent': 0,
            'failed_deliveries': 0
        }
    
    async def initialize(self):
        """Initialize the delivery service."""
        # Register message handlers
        self.register_message_handler('send_notification', self._handle_send_notification)
        self.register_message_handler('get_delivery_status', self._handle_get_delivery_status)
        self.register_message_handler('get_delivery_stats', self._handle_get_delivery_stats)
        
        # Add health checks
        self.add_health_check(self._check_delivery_health)
        
        self.logger.info("Notification delivery service initialized")
    
    async def process_message(self, message: ServiceMessage) -> Optional[ServiceMessage]:
        """Process incoming messages."""
        try:
            self.processed_messages += 1
            
            handler = self.message_handlers.get(message.payload.get('action'))
            if handler:
                result = await handler(message)
                return ServiceMessage(
                    message_type=MessageType.RESPONSE,
                    source_service=self.service_id,
                    target_service=message.source_service,
                    payload=result,
                    correlation_id=message.message_id
                )
            else:
                self.error_count += 1
                return ServiceMessage(
                    message_type=MessageType.RESPONSE,
                    source_service=self.service_id,
                    target_service=message.source_service,
                    payload={'error': f'Unknown action: {message.payload.get("action")}'},
                    correlation_id=message.message_id
                )
        
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error processing message: {e}")
            return ServiceMessage(
                message_type=MessageType.RESPONSE,
                source_service=self.service_id,
                target_service=message.source_service,
                payload={'error': str(e)},
                correlation_id=message.message_id
            )
    
    async def _handle_send_notification(self, message: ServiceMessage) -> Dict[str, Any]:
        """Handle notification sending request."""
        payload = message.payload
        notification_type = payload.get('type', 'email')
        
        try:
            # Simulate delivery
            delivery_id = str(uuid.uuid4())
            
            # Update stats
            if notification_type == 'sms':
                self.delivery_stats['sms_sent'] += 1
            elif notification_type == 'email':
                self.delivery_stats['email_sent'] += 1
            elif notification_type == 'push':
                self.delivery_stats['push_sent'] += 1
            
            return {
                'success': True,
                'delivery_id': delivery_id,
                'type': notification_type,
                'delivered_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.delivery_stats['failed_deliveries'] += 1
            return {
                'success': False,
                'error': str(e),
                'type': notification_type
            }
    
    async def _handle_get_delivery_status(self, message: ServiceMessage) -> Dict[str, Any]:
        """Handle delivery status request."""
        delivery_id = message.payload.get('delivery_id')
        
        # Simulate status lookup
        return {
            'success': True,
            'delivery_id': delivery_id,
            'status': 'delivered',
            'delivered_at': datetime.now().isoformat()
        }
    
    async def _handle_get_delivery_stats(self, message: ServiceMessage) -> Dict[str, Any]:
        """Handle delivery statistics request."""
        return {
            'success': True,
            'stats': self.delivery_stats
        }
    
    async def _check_delivery_health(self) -> bool:
        """Check delivery service health."""
        # Check if delivery mechanisms are working
        try:
            # Simple health check
            return len(self.delivery_queue) >= 0
        except:
            return False
    
    async def cleanup(self):
        """Cleanup delivery resources."""
        self.delivery_queue.clear()
        self.logger.info("Delivery service cleanup completed")


class ServiceRegistry:
    """Registry for managing microservices."""
    
    def __init__(self):
        self.services: Dict[str, BaseService] = {}
        self.service_instances: Dict[str, List[ServiceInstance]] = {}
        self.logger = NotificationLogger()
        self._lock = threading.Lock()
    
    def register_service(self, service: BaseService):
        """Register a service."""
        with self._lock:
            self.services[service.service_id] = service
            
            service_type_name = service.config.service_name
            if service_type_name not in self.service_instances:
                self.service_instances[service_type_name] = []
            
            instance = ServiceInstance(
                instance_id=service.service_id,
                service_type=ServiceType.SCHEDULER,  # Would be determined dynamically
                host=service.config.host,
                port=service.config.port
            )
            
            self.service_instances[service_type_name].append(instance)
            self.logger.info(f"Registered service {service.service_id}")
    
    def unregister_service(self, service_id: str):
        """Unregister a service."""
        with self._lock:
            if service_id in self.services:
                service = self.services[service_id]
                service_type_name = service.config.service_name
                
                # Remove from services
                del self.services[service_id]
                
                # Remove from instances
                if service_type_name in self.service_instances:
                    self.service_instances[service_type_name] = [
                        inst for inst in self.service_instances[service_type_name]
                        if inst.instance_id != service_id
                    ]
                
                self.logger.info(f"Unregistered service {service_id}")
    
    def get_service(self, service_id: str) -> Optional[BaseService]:
        """Get a service by ID."""
        return self.services.get(service_id)
    
    def get_services_by_type(self, service_type: str) -> List[BaseService]:
        """Get all services of a specific type."""
        return [
            service for service in self.services.values()
            if service.config.service_name == service_type
        ]
    
    def get_healthy_services(self, service_type: str) -> List[BaseService]:
        """Get all healthy services of a specific type."""
        services = self.get_services_by_type(service_type)
        healthy_services = []
        
        for service in services:
            if service.status == ServiceStatus.RUNNING:
                healthy_services.append(service)
        
        return healthy_services
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all services."""
        health_results = {}
        
        for service_id, service in self.services.items():
            try:
                health_results[service_id] = await service.health_check()
            except Exception as e:
                health_results[service_id] = {
                    'service_id': service_id,
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_results
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get registry status."""
        status = {
            'total_services': len(self.services),
            'services_by_type': {},
            'services_by_status': {}
        }
        
        # Count by type
        for service in self.services.values():
            service_type = service.config.service_name
            if service_type not in status['services_by_type']:
                status['services_by_type'][service_type] = 0
            status['services_by_type'][service_type] += 1
        
        # Count by status
        for service in self.services.values():
            service_status = service.status.value
            if service_status not in status['services_by_status']:
                status['services_by_status'][service_status] = 0
            status['services_by_status'][service_status] += 1
        
        return status


class ServiceCommunicator:
    """Handles communication between microservices."""
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self.logger = NotificationLogger()
        self.message_timeout = 30  # seconds
    
    async def send_message(self, target_service: str, message: ServiceMessage) -> Optional[ServiceMessage]:
        """Send a message to a target service."""
        try:
            # Find healthy service instance
            healthy_services = self.service_registry.get_healthy_services(target_service)
            
            if not healthy_services:
                self.logger.error(f"No healthy instances of {target_service} available")
                return None
            
            # Use first available service (could implement load balancing here)
            target_service_instance = healthy_services[0]
            
            # Process message
            response = await target_service_instance.process_message(message)
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error sending message to {target_service}: {e}")
            return None
    
    async def broadcast_message(self, service_type: str, message: ServiceMessage) -> List[ServiceMessage]:
        """Broadcast a message to all instances of a service type."""
        responses = []
        services = self.service_registry.get_healthy_services(service_type)
        
        for service in services:
            try:
                response = await service.process_message(message)
                if response:
                    responses.append(response)
            except Exception as e:
                self.logger.error(f"Error broadcasting to {service.service_id}: {e}")
        
        return responses
    
    async def request_response(self, target_service: str, action: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a request and wait for response."""
        message = ServiceMessage(
            message_type=MessageType.REQUEST,
            target_service=target_service,
            payload={'action': action, **payload}
        )
        
        response = await self.send_message(target_service, message)
        
        if response and response.message_type == MessageType.RESPONSE:
            return response.payload
        
        return None


class MicroservicesManager:
    """Main manager for microservices architecture."""
    
    def __init__(self):
        self.service_registry = ServiceRegistry()
        self.communicator = ServiceCommunicator(self.service_registry)
        self.logger = NotificationLogger()
        self.running_services: List[BaseService] = []
    
    async def start_service(self, service: BaseService):
        """Start a microservice."""
        try:
            await service.start()
            self.service_registry.register_service(service)
            self.running_services.append(service)
            self.logger.info(f"Started service {service.service_id}")
        except Exception as e:
            self.logger.error(f"Failed to start service {service.service_id}: {e}")
            raise
    
    async def stop_service(self, service_id: str):
        """Stop a microservice."""
        service = self.service_registry.get_service(service_id)
        if service:
            try:
                await service.stop()
                self.service_registry.unregister_service(service_id)
                self.running_services = [s for s in self.running_services if s.service_id != service_id]
                self.logger.info(f"Stopped service {service_id}")
            except Exception as e:
                self.logger.error(f"Error stopping service {service_id}: {e}")
    
    async def stop_all_services(self):
        """Stop all running services."""
        for service in self.running_services.copy():
            await self.stop_service(service.service_id)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        registry_status = self.service_registry.get_registry_status()
        health_status = await self.service_registry.health_check_all()
        
        return {
            'registry': registry_status,
            'health': health_status,
            'timestamp': datetime.now().isoformat()
        }
    
    def create_scheduler_service(self, port: int = 8001) -> NotificationSchedulerService:
        """Create a notification scheduler service."""
        config = ServiceConfig(
            service_name="notification_scheduler",
            service_type=ServiceType.SCHEDULER,
            port=port
        )
        return NotificationSchedulerService(config)
    
    def create_delivery_service(self, port: int = 8002) -> NotificationDeliveryService:
        """Create a notification delivery service."""
        config = ServiceConfig(
            service_name="notification_delivery",
            service_type=ServiceType.NOTIFICATION_SENDER,
            port=port
        )
        return NotificationDeliveryService(config)
    
    async def schedule_notification(self, appointment_id: str, user_id: str, 
                                  scheduled_time: str, message: str) -> Optional[Dict[str, Any]]:
        """Schedule a notification through the microservices."""
        return await self.communicator.request_response(
            "notification_scheduler",
            "schedule_notification",
            {
                'appointment_id': appointment_id,
                'user_id': user_id,
                'scheduled_time': scheduled_time,
                'message': message
            }
        )
    
    async def send_notification(self, notification_type: str, recipient: str, 
                              message: str) -> Optional[Dict[str, Any]]:
        """Send a notification through the microservices."""
        return await self.communicator.request_response(
            "notification_delivery",
            "send_notification",
            {
                'type': notification_type,
                'recipient': recipient,
                'message': message
            }
        )