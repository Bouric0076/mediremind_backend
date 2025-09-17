import asyncio
import threading
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
from queue import Queue, PriorityQueue
import psutil
import logging

from .logging_config import NotificationLogger
from .monitoring import SystemMonitor
from .performance import PerformanceManager


class ScalingStrategy(Enum):
    """Scaling strategies for different components."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    AUTO = "auto"
    MANUAL = "manual"


class LoadBalancingMethod(Enum):
    """Load balancing methods."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    HASH_BASED = "hash_based"
    LEAST_RESPONSE_TIME = "least_response_time"


class ServiceType(Enum):
    """Types of services in the system."""
    SCHEDULER = "scheduler"
    QUEUE_MANAGER = "queue_manager"
    NOTIFICATION_SENDER = "notification_sender"
    DATABASE_HANDLER = "database_handler"
    CACHE_MANAGER = "cache_manager"
    API_GATEWAY = "api_gateway"


@dataclass
class ScalingMetrics:
    """Metrics used for scaling decisions."""
    cpu_usage: float
    memory_usage: float
    request_rate: float
    response_time: float
    queue_length: int
    error_rate: float
    active_connections: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ServiceInstance:
    """Represents a service instance."""
    instance_id: str
    service_type: ServiceType
    host: str
    port: int
    weight: float = 1.0
    active_connections: int = 0
    last_response_time: float = 0.0
    health_status: str = "healthy"
    created_at: datetime = field(default_factory=datetime.now)
    last_health_check: datetime = field(default_factory=datetime.now)


@dataclass
class ScalingRule:
    """Rules for automatic scaling."""
    service_type: ServiceType
    metric_name: str
    threshold_up: float
    threshold_down: float
    scale_up_count: int = 1
    scale_down_count: int = 1
    cooldown_period: int = 300  # seconds
    min_instances: int = 1
    max_instances: int = 10
    enabled: bool = True


class LoadBalancer:
    """Load balancer for distributing requests across service instances."""
    
    def __init__(self, method: LoadBalancingMethod = LoadBalancingMethod.ROUND_ROBIN):
        self.method = method
        self.instances: Dict[ServiceType, List[ServiceInstance]] = {}
        self.current_index: Dict[ServiceType, int] = {}
        self.logger = NotificationLogger()
        self._lock = threading.Lock()
    
    def register_instance(self, instance: ServiceInstance):
        """Register a new service instance."""
        with self._lock:
            if instance.service_type not in self.instances:
                self.instances[instance.service_type] = []
                self.current_index[instance.service_type] = 0
            
            self.instances[instance.service_type].append(instance)
            self.logger.info(f"Registered instance {instance.instance_id} for {instance.service_type.value}")
    
    def unregister_instance(self, service_type: ServiceType, instance_id: str):
        """Unregister a service instance."""
        with self._lock:
            if service_type in self.instances:
                self.instances[service_type] = [
                    inst for inst in self.instances[service_type]
                    if inst.instance_id != instance_id
                ]
                self.logger.info(f"Unregistered instance {instance_id} for {service_type.value}")
    
    def get_instance(self, service_type: ServiceType, request_data: Optional[Dict] = None) -> Optional[ServiceInstance]:
        """Get the next instance based on load balancing method."""
        with self._lock:
            instances = self.instances.get(service_type, [])
            healthy_instances = [inst for inst in instances if inst.health_status == "healthy"]
            
            if not healthy_instances:
                return None
            
            if self.method == LoadBalancingMethod.ROUND_ROBIN:
                return self._round_robin_select(service_type, healthy_instances)
            elif self.method == LoadBalancingMethod.LEAST_CONNECTIONS:
                return self._least_connections_select(healthy_instances)
            elif self.method == LoadBalancingMethod.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_select(healthy_instances)
            elif self.method == LoadBalancingMethod.HASH_BASED:
                return self._hash_based_select(healthy_instances, request_data)
            elif self.method == LoadBalancingMethod.LEAST_RESPONSE_TIME:
                return self._least_response_time_select(healthy_instances)
            
            return healthy_instances[0]  # Fallback
    
    def _round_robin_select(self, service_type: ServiceType, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round-robin selection."""
        current = self.current_index[service_type]
        instance = instances[current % len(instances)]
        self.current_index[service_type] = (current + 1) % len(instances)
        return instance
    
    def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with least active connections."""
        return min(instances, key=lambda x: x.active_connections)
    
    def _weighted_round_robin_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted round-robin selection."""
        total_weight = sum(inst.weight for inst in instances)
        weighted_instances = []
        
        for instance in instances:
            count = int(instance.weight / total_weight * 100)
            weighted_instances.extend([instance] * max(1, count))
        
        return weighted_instances[int(time.time()) % len(weighted_instances)]
    
    def _hash_based_select(self, instances: List[ServiceInstance], request_data: Optional[Dict]) -> ServiceInstance:
        """Hash-based selection for session affinity."""
        if not request_data:
            return instances[0]
        
        hash_key = str(request_data.get('user_id', request_data.get('session_id', 'default')))
        hash_value = int(hashlib.md5(hash_key.encode()).hexdigest(), 16)
        return instances[hash_value % len(instances)]
    
    def _least_response_time_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with least response time."""
        return min(instances, key=lambda x: x.last_response_time)
    
    def update_instance_metrics(self, instance_id: str, connections: int, response_time: float):
        """Update instance metrics."""
        with self._lock:
            for instances in self.instances.values():
                for instance in instances:
                    if instance.instance_id == instance_id:
                        instance.active_connections = connections
                        instance.last_response_time = response_time
                        break


class AutoScaler:
    """Automatic scaling manager."""
    
    def __init__(self, load_balancer: LoadBalancer, system_monitor: SystemMonitor):
        self.load_balancer = load_balancer
        self.system_monitor = system_monitor
        self.scaling_rules: List[ScalingRule] = []
        self.last_scaling_action: Dict[ServiceType, datetime] = {}
        self.logger = NotificationLogger()
        self.running = False
        self._monitor_thread = None
    
    def add_scaling_rule(self, rule: ScalingRule):
        """Add a scaling rule."""
        self.scaling_rules.append(rule)
        self.logger.info(f"Added scaling rule for {rule.service_type.value}")
    
    def start_monitoring(self):
        """Start the auto-scaling monitor."""
        if self.running:
            return
        
        self.running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info("Auto-scaler monitoring started")
    
    def stop_monitoring(self):
        """Stop the auto-scaling monitor."""
        self.running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("Auto-scaler monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                self._check_scaling_rules()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in auto-scaler monitoring: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_scaling_rules(self):
        """Check all scaling rules and take action if needed."""
        current_metrics = self._get_current_metrics()
        
        for rule in self.scaling_rules:
            if not rule.enabled:
                continue
            
            # Check cooldown period
            last_action = self.last_scaling_action.get(rule.service_type)
            if last_action and (datetime.now() - last_action).total_seconds() < rule.cooldown_period:
                continue
            
            current_instances = len(self.load_balancer.instances.get(rule.service_type, []))
            metric_value = getattr(current_metrics, rule.metric_name, 0)
            
            # Scale up check
            if (metric_value > rule.threshold_up and 
                current_instances < rule.max_instances):
                self._scale_up(rule)
            
            # Scale down check
            elif (metric_value < rule.threshold_down and 
                  current_instances > rule.min_instances):
                self._scale_down(rule)
    
    def _get_current_metrics(self) -> ScalingMetrics:
        """Get current system metrics."""
        system_metrics = self.system_monitor.get_system_metrics()
        
        return ScalingMetrics(
            cpu_usage=system_metrics.get('cpu_usage', 0),
            memory_usage=system_metrics.get('memory_usage', 0),
            request_rate=system_metrics.get('request_rate', 0),
            response_time=system_metrics.get('avg_response_time', 0),
            queue_length=system_metrics.get('queue_length', 0),
            error_rate=system_metrics.get('error_rate', 0),
            active_connections=system_metrics.get('active_connections', 0)
        )
    
    def _scale_up(self, rule: ScalingRule):
        """Scale up service instances."""
        for i in range(rule.scale_up_count):
            instance_id = f"{rule.service_type.value}_{int(time.time())}_{i}"
            
            # Create new instance (this would typically involve container orchestration)
            new_instance = ServiceInstance(
                instance_id=instance_id,
                service_type=rule.service_type,
                host="localhost",  # Would be dynamically assigned
                port=8000 + len(self.load_balancer.instances.get(rule.service_type, [])),
                weight=1.0
            )
            
            self.load_balancer.register_instance(new_instance)
            self.last_scaling_action[rule.service_type] = datetime.now()
            
            self.logger.info(f"Scaled up {rule.service_type.value}: added instance {instance_id}")
    
    def _scale_down(self, rule: ScalingRule):
        """Scale down service instances."""
        instances = self.load_balancer.instances.get(rule.service_type, [])
        
        for i in range(min(rule.scale_down_count, len(instances) - rule.min_instances)):
            # Remove instance with least connections
            instance_to_remove = min(instances, key=lambda x: x.active_connections)
            
            self.load_balancer.unregister_instance(
                rule.service_type, 
                instance_to_remove.instance_id
            )
            
            self.last_scaling_action[rule.service_type] = datetime.now()
            
            self.logger.info(f"Scaled down {rule.service_type.value}: removed instance {instance_to_remove.instance_id}")


class HorizontalScaler:
    """Manages horizontal scaling of notification services."""
    
    def __init__(self):
        self.worker_pools: Dict[str, ThreadPoolExecutor] = {}
        self.process_pools: Dict[str, ProcessPoolExecutor] = {}
        self.task_queues: Dict[str, Queue] = {}
        self.logger = NotificationLogger()
        self.running = False
    
    def create_worker_pool(self, pool_name: str, max_workers: int, use_processes: bool = False):
        """Create a worker pool for parallel processing."""
        if use_processes:
            self.process_pools[pool_name] = ProcessPoolExecutor(max_workers=max_workers)
        else:
            self.worker_pools[pool_name] = ThreadPoolExecutor(max_workers=max_workers)
        
        self.task_queues[pool_name] = Queue()
        self.logger.info(f"Created {'process' if use_processes else 'thread'} pool '{pool_name}' with {max_workers} workers")
    
    def submit_task(self, pool_name: str, func: Callable, *args, **kwargs):
        """Submit a task to a worker pool."""
        if pool_name in self.worker_pools:
            return self.worker_pools[pool_name].submit(func, *args, **kwargs)
        elif pool_name in self.process_pools:
            return self.process_pools[pool_name].submit(func, *args, **kwargs)
        else:
            raise ValueError(f"Worker pool '{pool_name}' not found")
    
    def scale_pool(self, pool_name: str, new_size: int):
        """Scale a worker pool to a new size."""
        if pool_name in self.worker_pools:
            old_pool = self.worker_pools[pool_name]
            old_pool.shutdown(wait=True)
            
            self.worker_pools[pool_name] = ThreadPoolExecutor(max_workers=new_size)
            self.logger.info(f"Scaled thread pool '{pool_name}' to {new_size} workers")
        
        elif pool_name in self.process_pools:
            old_pool = self.process_pools[pool_name]
            old_pool.shutdown(wait=True)
            
            self.process_pools[pool_name] = ProcessPoolExecutor(max_workers=new_size)
            self.logger.info(f"Scaled process pool '{pool_name}' to {new_size} workers")
    
    def get_pool_stats(self, pool_name: str) -> Dict[str, Any]:
        """Get statistics for a worker pool."""
        stats = {
            'pool_name': pool_name,
            'pool_type': 'unknown',
            'queue_size': 0
        }
        
        if pool_name in self.task_queues:
            stats['queue_size'] = self.task_queues[pool_name].qsize()
        
        if pool_name in self.worker_pools:
            pool = self.worker_pools[pool_name]
            stats.update({
                'pool_type': 'thread',
                'max_workers': pool._max_workers,
                'active_threads': len(pool._threads)
            })
        
        elif pool_name in self.process_pools:
            pool = self.process_pools[pool_name]
            stats.update({
                'pool_type': 'process',
                'max_workers': pool._max_workers,
                'active_processes': len(pool._processes)
            })
        
        return stats
    
    def shutdown_all_pools(self):
        """Shutdown all worker pools."""
        for pool in self.worker_pools.values():
            pool.shutdown(wait=True)
        
        for pool in self.process_pools.values():
            pool.shutdown(wait=True)
        
        self.worker_pools.clear()
        self.process_pools.clear()
        self.logger.info("All worker pools shut down")


class ScalabilityManager:
    """Main manager for system scalability."""
    
    def __init__(self, system_monitor: SystemMonitor):
        self.system_monitor = system_monitor
        self.load_balancer = LoadBalancer()
        self.auto_scaler = AutoScaler(self.load_balancer, system_monitor)
        self.horizontal_scaler = HorizontalScaler()
        self.performance_manager = PerformanceManager()
        self.logger = NotificationLogger()
        
        # Initialize default scaling rules
        self._setup_default_scaling_rules()
        
        # Initialize worker pools
        self._setup_worker_pools()
    
    def _setup_default_scaling_rules(self):
        """Set up default scaling rules for different services."""
        # Scheduler scaling rules
        self.auto_scaler.add_scaling_rule(ScalingRule(
            service_type=ServiceType.SCHEDULER,
            metric_name='cpu_usage',
            threshold_up=80.0,
            threshold_down=30.0,
            scale_up_count=1,
            scale_down_count=1,
            min_instances=1,
            max_instances=5
        ))
        
        # Queue manager scaling rules
        self.auto_scaler.add_scaling_rule(ScalingRule(
            service_type=ServiceType.QUEUE_MANAGER,
            metric_name='queue_length',
            threshold_up=1000,
            threshold_down=100,
            scale_up_count=2,
            scale_down_count=1,
            min_instances=2,
            max_instances=10
        ))
        
        # Notification sender scaling rules
        self.auto_scaler.add_scaling_rule(ScalingRule(
            service_type=ServiceType.NOTIFICATION_SENDER,
            metric_name='request_rate',
            threshold_up=100.0,
            threshold_down=20.0,
            scale_up_count=2,
            scale_down_count=1,
            min_instances=2,
            max_instances=15
        ))
    
    def _setup_worker_pools(self):
        """Set up worker pools for different tasks."""
        cpu_count = multiprocessing.cpu_count()
        
        # SMS sending pool
        self.horizontal_scaler.create_worker_pool(
            'sms_workers', 
            max_workers=min(cpu_count * 2, 20)
        )
        
        # Email sending pool
        self.horizontal_scaler.create_worker_pool(
            'email_workers', 
            max_workers=min(cpu_count * 2, 20)
        )
        
        # Push notification pool
        self.horizontal_scaler.create_worker_pool(
            'push_workers', 
            max_workers=min(cpu_count * 4, 40)
        )
        
        # Database operations pool
        self.horizontal_scaler.create_worker_pool(
            'db_workers', 
            max_workers=min(cpu_count, 10)
        )
        
        # Heavy processing pool (using processes)
        self.horizontal_scaler.create_worker_pool(
            'heavy_processing', 
            max_workers=min(cpu_count, 8),
            use_processes=True
        )
    
    def start_scaling(self):
        """Start all scaling services."""
        self.auto_scaler.start_monitoring()
        self.logger.info("Scalability manager started")
    
    def stop_scaling(self):
        """Stop all scaling services."""
        self.auto_scaler.stop_monitoring()
        self.horizontal_scaler.shutdown_all_pools()
        self.logger.info("Scalability manager stopped")
    
    def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling status."""
        status = {
            'auto_scaler_running': self.auto_scaler.running,
            'load_balancer_instances': {},
            'worker_pools': {},
            'system_metrics': self.system_monitor.get_system_metrics()
        }
        
        # Load balancer status
        for service_type, instances in self.load_balancer.instances.items():
            status['load_balancer_instances'][service_type.value] = [
                {
                    'instance_id': inst.instance_id,
                    'host': inst.host,
                    'port': inst.port,
                    'health_status': inst.health_status,
                    'active_connections': inst.active_connections
                }
                for inst in instances
            ]
        
        # Worker pool status
        for pool_name in list(self.horizontal_scaler.worker_pools.keys()) + list(self.horizontal_scaler.process_pools.keys()):
            status['worker_pools'][pool_name] = self.horizontal_scaler.get_pool_stats(pool_name)
        
        return status
    
    def scale_service_manually(self, service_type: ServiceType, target_instances: int):
        """Manually scale a service to target number of instances."""
        current_instances = len(self.load_balancer.instances.get(service_type, []))
        
        if target_instances > current_instances:
            # Scale up
            for i in range(target_instances - current_instances):
                instance_id = f"{service_type.value}_manual_{int(time.time())}_{i}"
                new_instance = ServiceInstance(
                    instance_id=instance_id,
                    service_type=service_type,
                    host="localhost",
                    port=8000 + len(self.load_balancer.instances.get(service_type, [])),
                    weight=1.0
                )
                self.load_balancer.register_instance(new_instance)
        
        elif target_instances < current_instances:
            # Scale down
            instances = self.load_balancer.instances.get(service_type, [])
            for i in range(current_instances - target_instances):
                if instances:
                    instance_to_remove = instances.pop()
                    self.load_balancer.unregister_instance(
                        service_type, 
                        instance_to_remove.instance_id
                    )
        
        self.logger.info(f"Manually scaled {service_type.value} to {target_instances} instances")
    
    def optimize_for_load(self, expected_load: Dict[str, float]):
        """Optimize system configuration for expected load."""
        # Adjust worker pool sizes based on expected load
        if 'sms_rate' in expected_load:
            sms_workers = max(5, int(expected_load['sms_rate'] / 10))
            self.horizontal_scaler.scale_pool('sms_workers', sms_workers)
        
        if 'email_rate' in expected_load:
            email_workers = max(5, int(expected_load['email_rate'] / 15))
            self.horizontal_scaler.scale_pool('email_workers', email_workers)
        
        if 'push_rate' in expected_load:
            push_workers = max(10, int(expected_load['push_rate'] / 20))
            self.horizontal_scaler.scale_pool('push_workers', push_workers)
        
        self.logger.info(f"Optimized system for expected load: {expected_load}")


# Utility functions for scalability
def calculate_optimal_workers(task_rate: float, avg_task_duration: float, target_utilization: float = 0.8) -> int:
    """Calculate optimal number of workers for a given task rate."""
    required_capacity = task_rate * avg_task_duration
    optimal_workers = max(1, int(required_capacity / target_utilization))
    return optimal_workers


def estimate_memory_requirements(concurrent_tasks: int, avg_memory_per_task: float) -> float:
    """Estimate memory requirements for concurrent tasks."""
    base_memory = 100  # MB base memory
    task_memory = concurrent_tasks * avg_memory_per_task
    buffer_memory = task_memory * 0.2  # 20% buffer
    return base_memory + task_memory + buffer_memory


def get_system_capacity() -> Dict[str, Any]:
    """Get current system capacity information."""
    return {
        'cpu_cores': multiprocessing.cpu_count(),
        'memory_total_gb': psutil.virtual_memory().total / (1024**3),
        'memory_available_gb': psutil.virtual_memory().available / (1024**3),
        'disk_total_gb': psutil.disk_usage('/').total / (1024**3),
        'disk_free_gb': psutil.disk_usage('/').free / (1024**3)
    }