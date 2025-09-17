import asyncio
import json
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import threading
from concurrent.futures import ThreadPoolExecutor
import socket
import pickle
import zlib
from collections import defaultdict, deque

from .logging_config import NotificationLogger
from .monitoring import SystemMonitor
from .cache_layer import CacheManager


class NodeRole(Enum):
    """Roles that nodes can have in the distributed system."""
    MASTER = "master"
    WORKER = "worker"
    COORDINATOR = "coordinator"
    REPLICA = "replica"
    GATEWAY = "gateway"


class NodeStatus(Enum):
    """Status of nodes in the cluster."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    JOINING = "joining"
    LEAVING = "leaving"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class PartitionStrategy(Enum):
    """Data partitioning strategies."""
    HASH_BASED = "hash_based"
    RANGE_BASED = "range_based"
    ROUND_ROBIN = "round_robin"
    CONSISTENT_HASH = "consistent_hash"
    GEOGRAPHIC = "geographic"


class ReplicationStrategy(Enum):
    """Data replication strategies."""
    MASTER_SLAVE = "master_slave"
    MASTER_MASTER = "master_master"
    QUORUM = "quorum"
    EVENTUAL_CONSISTENCY = "eventual_consistency"


@dataclass
class ClusterNode:
    """Represents a node in the distributed cluster."""
    node_id: str
    host: str
    port: int
    role: NodeRole
    status: NodeStatus = NodeStatus.INACTIVE
    last_heartbeat: datetime = field(default_factory=datetime.now)
    load_factor: float = 0.0
    capacity: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    joined_at: datetime = field(default_factory=datetime.now)


@dataclass
class DataPartition:
    """Represents a data partition."""
    partition_id: str
    start_key: str
    end_key: str
    primary_node: str
    replica_nodes: List[str] = field(default_factory=list)
    size: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DistributedTask:
    """Represents a task in the distributed system."""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    assigned_node: Optional[str] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ConsistentHashRing:
    """Consistent hashing implementation for distributed data placement."""
    
    def __init__(self, replicas: int = 150):
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        self.nodes: set = set()
    
    def _hash(self, key: str) -> int:
        """Hash function for the ring."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_node(self, node: str):
        """Add a node to the hash ring."""
        if node in self.nodes:
            return
        
        self.nodes.add(node)
        
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            self.ring[hash_value] = node
        
        self.sorted_keys = sorted(self.ring.keys())
    
    def remove_node(self, node: str):
        """Remove a node from the hash ring."""
        if node not in self.nodes:
            return
        
        self.nodes.remove(node)
        
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            if hash_value in self.ring:
                del self.ring[hash_value]
        
        self.sorted_keys = sorted(self.ring.keys())
    
    def get_node(self, key: str) -> Optional[str]:
        """Get the node responsible for a key."""
        if not self.ring:
            return None
        
        hash_value = self._hash(key)
        
        # Find the first node clockwise from the hash
        for ring_key in self.sorted_keys:
            if hash_value <= ring_key:
                return self.ring[ring_key]
        
        # Wrap around to the first node
        return self.ring[self.sorted_keys[0]]
    
    def get_nodes(self, key: str, count: int) -> List[str]:
        """Get multiple nodes for replication."""
        if not self.ring or count <= 0:
            return []
        
        hash_value = self._hash(key)
        nodes = []
        seen_nodes = set()
        
        # Start from the position in the ring
        start_index = 0
        for i, ring_key in enumerate(self.sorted_keys):
            if hash_value <= ring_key:
                start_index = i
                break
        
        # Collect unique nodes
        for i in range(len(self.sorted_keys)):
            index = (start_index + i) % len(self.sorted_keys)
            node = self.ring[self.sorted_keys[index]]
            
            if node not in seen_nodes:
                nodes.append(node)
                seen_nodes.add(node)
                
                if len(nodes) >= count:
                    break
        
        return nodes


class ClusterManager:
    """Manages the distributed cluster of nodes."""
    
    def __init__(self, node_id: str, host: str, port: int):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.nodes: Dict[str, ClusterNode] = {}
        self.local_node = ClusterNode(
            node_id=node_id,
            host=host,
            port=port,
            role=NodeRole.WORKER,
            status=NodeStatus.ACTIVE
        )
        self.nodes[node_id] = self.local_node
        
        self.logger = NotificationLogger()
        self.heartbeat_interval = 30  # seconds
        self.failure_timeout = 90  # seconds
        self.running = False
        self._heartbeat_thread = None
        self._failure_detector_thread = None
        self._lock = threading.Lock()
    
    def start(self):
        """Start the cluster manager."""
        self.running = True
        
        # Start heartbeat thread
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        
        # Start failure detector thread
        self._failure_detector_thread = threading.Thread(target=self._failure_detector_loop, daemon=True)
        self._failure_detector_thread.start()
        
        self.logger.info(f"Cluster manager started for node {self.node_id}")
    
    def stop(self):
        """Stop the cluster manager."""
        self.running = False
        
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        
        if self._failure_detector_thread:
            self._failure_detector_thread.join(timeout=5)
        
        self.logger.info(f"Cluster manager stopped for node {self.node_id}")
    
    def join_cluster(self, seed_nodes: List[Tuple[str, int]]):
        """Join an existing cluster."""
        self.local_node.status = NodeStatus.JOINING
        
        for host, port in seed_nodes:
            try:
                # Send join request to seed node
                self._send_join_request(host, port)
                break
            except Exception as e:
                self.logger.warning(f"Failed to join via {host}:{port}: {e}")
        
        self.local_node.status = NodeStatus.ACTIVE
        self.logger.info(f"Node {self.node_id} joined cluster")
    
    def leave_cluster(self):
        """Leave the cluster gracefully."""
        self.local_node.status = NodeStatus.LEAVING
        
        # Notify other nodes
        for node in self.nodes.values():
            if node.node_id != self.node_id and node.status == NodeStatus.ACTIVE:
                try:
                    self._send_leave_notification(node.host, node.port)
                except Exception as e:
                    self.logger.warning(f"Failed to notify {node.node_id}: {e}")
        
        self.local_node.status = NodeStatus.INACTIVE
        self.logger.info(f"Node {self.node_id} left cluster")
    
    def add_node(self, node: ClusterNode):
        """Add a node to the cluster."""
        with self._lock:
            self.nodes[node.node_id] = node
            self.logger.info(f"Added node {node.node_id} to cluster")
    
    def remove_node(self, node_id: str):
        """Remove a node from the cluster."""
        with self._lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
                self.logger.info(f"Removed node {node_id} from cluster")
    
    def get_active_nodes(self) -> List[ClusterNode]:
        """Get all active nodes in the cluster."""
        with self._lock:
            return [node for node in self.nodes.values() if node.status == NodeStatus.ACTIVE]
    
    def get_node_by_role(self, role: NodeRole) -> List[ClusterNode]:
        """Get nodes by their role."""
        with self._lock:
            return [node for node in self.nodes.values() 
                   if node.role == role and node.status == NodeStatus.ACTIVE]
    
    def elect_master(self) -> Optional[str]:
        """Elect a master node using a simple algorithm."""
        active_nodes = self.get_active_nodes()
        
        if not active_nodes:
            return None
        
        # Simple election: node with lowest ID becomes master
        master_node = min(active_nodes, key=lambda x: x.node_id)
        master_node.role = NodeRole.MASTER
        
        self.logger.info(f"Elected {master_node.node_id} as master")
        return master_node.node_id
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats to other nodes."""
        while self.running:
            try:
                self._send_heartbeats()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(self.heartbeat_interval)
    
    def _failure_detector_loop(self):
        """Detect failed nodes based on missed heartbeats."""
        while self.running:
            try:
                self._detect_failures()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                self.logger.error(f"Error in failure detector: {e}")
                time.sleep(self.heartbeat_interval)
    
    def _send_heartbeats(self):
        """Send heartbeats to all active nodes."""
        self.local_node.last_heartbeat = datetime.now()
        
        for node in self.get_active_nodes():
            if node.node_id != self.node_id:
                try:
                    self._send_heartbeat(node.host, node.port)
                except Exception as e:
                    self.logger.warning(f"Failed to send heartbeat to {node.node_id}: {e}")
    
    def _detect_failures(self):
        """Detect and handle node failures."""
        current_time = datetime.now()
        failed_nodes = []
        
        with self._lock:
            for node in list(self.nodes.values()):
                if (node.node_id != self.node_id and 
                    node.status == NodeStatus.ACTIVE and
                    (current_time - node.last_heartbeat).total_seconds() > self.failure_timeout):
                    
                    node.status = NodeStatus.FAILED
                    failed_nodes.append(node.node_id)
        
        for node_id in failed_nodes:
            self.logger.warning(f"Detected failure of node {node_id}")
            self._handle_node_failure(node_id)
    
    def _handle_node_failure(self, node_id: str):
        """Handle a node failure."""
        # Remove failed node
        self.remove_node(node_id)
        
        # Trigger rebalancing if needed
        self._trigger_rebalancing()
    
    def _trigger_rebalancing(self):
        """Trigger cluster rebalancing after node changes."""
        # This would trigger data redistribution, partition reassignment, etc.
        self.logger.info("Triggering cluster rebalancing")
    
    def _send_join_request(self, host: str, port: int):
        """Send a join request to a seed node."""
        # Simulate network communication
        pass
    
    def _send_leave_notification(self, host: str, port: int):
        """Send leave notification to a node."""
        # Simulate network communication
        pass
    
    def _send_heartbeat(self, host: str, port: int):
        """Send heartbeat to a node."""
        # Simulate network communication
        pass
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get cluster status information."""
        with self._lock:
            return {
                'local_node_id': self.node_id,
                'total_nodes': len(self.nodes),
                'active_nodes': len(self.get_active_nodes()),
                'nodes': {
                    node_id: {
                        'host': node.host,
                        'port': node.port,
                        'role': node.role.value,
                        'status': node.status.value,
                        'last_heartbeat': node.last_heartbeat.isoformat(),
                        'load_factor': node.load_factor
                    }
                    for node_id, node in self.nodes.items()
                }
            }


class DistributedDataManager:
    """Manages distributed data storage and retrieval."""
    
    def __init__(self, cluster_manager: ClusterManager, 
                 partition_strategy: PartitionStrategy = PartitionStrategy.CONSISTENT_HASH,
                 replication_factor: int = 3):
        self.cluster_manager = cluster_manager
        self.partition_strategy = partition_strategy
        self.replication_factor = replication_factor
        self.partitions: Dict[str, DataPartition] = {}
        self.consistent_hash = ConsistentHashRing()
        self.logger = NotificationLogger()
        
        # Initialize hash ring with active nodes
        for node in cluster_manager.get_active_nodes():
            self.consistent_hash.add_node(node.node_id)
    
    def create_partition(self, partition_id: str, start_key: str, end_key: str) -> DataPartition:
        """Create a new data partition."""
        # Determine primary and replica nodes
        nodes = self.consistent_hash.get_nodes(partition_id, self.replication_factor)
        
        if not nodes:
            raise ValueError("No nodes available for partition")
        
        primary_node = nodes[0]
        replica_nodes = nodes[1:] if len(nodes) > 1 else []
        
        partition = DataPartition(
            partition_id=partition_id,
            start_key=start_key,
            end_key=end_key,
            primary_node=primary_node,
            replica_nodes=replica_nodes
        )
        
        self.partitions[partition_id] = partition
        self.logger.info(f"Created partition {partition_id} on node {primary_node}")
        
        return partition
    
    def get_partition_for_key(self, key: str) -> Optional[DataPartition]:
        """Get the partition responsible for a key."""
        if self.partition_strategy == PartitionStrategy.CONSISTENT_HASH:
            node = self.consistent_hash.get_node(key)
            if node:
                # Find partition on this node
                for partition in self.partitions.values():
                    if partition.primary_node == node:
                        return partition
        
        elif self.partition_strategy == PartitionStrategy.HASH_BASED:
            hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
            partition_count = len(self.partitions)
            if partition_count > 0:
                partition_index = hash_value % partition_count
                partition_id = list(self.partitions.keys())[partition_index]
                return self.partitions[partition_id]
        
        return None
    
    async def store_data(self, key: str, value: Any) -> bool:
        """Store data in the distributed system."""
        partition = self.get_partition_for_key(key)
        
        if not partition:
            self.logger.error(f"No partition found for key {key}")
            return False
        
        try:
            # Store on primary node
            success = await self._store_on_node(partition.primary_node, key, value)
            
            if success:
                # Replicate to replica nodes
                replication_tasks = [
                    self._store_on_node(replica_node, key, value)
                    for replica_node in partition.replica_nodes
                ]
                
                if replication_tasks:
                    await asyncio.gather(*replication_tasks, return_exceptions=True)
                
                partition.size += 1
                partition.last_updated = datetime.now()
                
                self.logger.debug(f"Stored data for key {key} in partition {partition.partition_id}")
                return True
        
        except Exception as e:
            self.logger.error(f"Error storing data for key {key}: {e}")
        
        return False
    
    async def retrieve_data(self, key: str) -> Optional[Any]:
        """Retrieve data from the distributed system."""
        partition = self.get_partition_for_key(key)
        
        if not partition:
            self.logger.error(f"No partition found for key {key}")
            return None
        
        # Try primary node first
        try:
            data = await self._retrieve_from_node(partition.primary_node, key)
            if data is not None:
                return data
        except Exception as e:
            self.logger.warning(f"Failed to retrieve from primary node {partition.primary_node}: {e}")
        
        # Try replica nodes
        for replica_node in partition.replica_nodes:
            try:
                data = await self._retrieve_from_node(replica_node, key)
                if data is not None:
                    return data
            except Exception as e:
                self.logger.warning(f"Failed to retrieve from replica node {replica_node}: {e}")
        
        return None
    
    async def delete_data(self, key: str) -> bool:
        """Delete data from the distributed system."""
        partition = self.get_partition_for_key(key)
        
        if not partition:
            return False
        
        try:
            # Delete from all nodes
            deletion_tasks = [self._delete_from_node(partition.primary_node, key)]
            deletion_tasks.extend([
                self._delete_from_node(replica_node, key)
                for replica_node in partition.replica_nodes
            ])
            
            results = await asyncio.gather(*deletion_tasks, return_exceptions=True)
            
            # Consider successful if deleted from majority of nodes
            successful_deletions = sum(1 for result in results if result is True)
            total_nodes = len(deletion_tasks)
            
            if successful_deletions > total_nodes // 2:
                partition.size = max(0, partition.size - 1)
                partition.last_updated = datetime.now()
                return True
        
        except Exception as e:
            self.logger.error(f"Error deleting data for key {key}: {e}")
        
        return False
    
    async def _store_on_node(self, node_id: str, key: str, value: Any) -> bool:
        """Store data on a specific node."""
        # Simulate network storage operation
        # In a real implementation, this would make network calls
        try:
            # Simulate some processing time
            await asyncio.sleep(0.01)
            return True
        except Exception:
            return False
    
    async def _retrieve_from_node(self, node_id: str, key: str) -> Optional[Any]:
        """Retrieve data from a specific node."""
        # Simulate network retrieval operation
        try:
            await asyncio.sleep(0.01)
            return f"data_for_{key}"  # Simulated data
        except Exception:
            return None
    
    async def _delete_from_node(self, node_id: str, key: str) -> bool:
        """Delete data from a specific node."""
        # Simulate network deletion operation
        try:
            await asyncio.sleep(0.01)
            return True
        except Exception:
            return False
    
    def rebalance_partitions(self):
        """Rebalance partitions across nodes."""
        active_nodes = self.cluster_manager.get_active_nodes()
        
        if not active_nodes:
            return
        
        # Update consistent hash ring
        current_nodes = set(self.consistent_hash.nodes)
        new_nodes = set(node.node_id for node in active_nodes)
        
        # Add new nodes
        for node_id in new_nodes - current_nodes:
            self.consistent_hash.add_node(node_id)
        
        # Remove old nodes
        for node_id in current_nodes - new_nodes:
            self.consistent_hash.remove_node(node_id)
        
        # Reassign partitions
        for partition in self.partitions.values():
            nodes = self.consistent_hash.get_nodes(partition.partition_id, self.replication_factor)
            if nodes:
                partition.primary_node = nodes[0]
                partition.replica_nodes = nodes[1:] if len(nodes) > 1 else []
        
        self.logger.info("Completed partition rebalancing")
    
    def get_partition_status(self) -> Dict[str, Any]:
        """Get status of all partitions."""
        return {
            'total_partitions': len(self.partitions),
            'replication_factor': self.replication_factor,
            'partition_strategy': self.partition_strategy.value,
            'partitions': {
                partition_id: {
                    'start_key': partition.start_key,
                    'end_key': partition.end_key,
                    'primary_node': partition.primary_node,
                    'replica_nodes': partition.replica_nodes,
                    'size': partition.size,
                    'last_updated': partition.last_updated.isoformat()
                }
                for partition_id, partition in self.partitions.items()
            }
        }


class DistributedTaskManager:
    """Manages distributed task execution."""
    
    def __init__(self, cluster_manager: ClusterManager):
        self.cluster_manager = cluster_manager
        self.tasks: Dict[str, DistributedTask] = {}
        self.task_queue = deque()
        self.logger = NotificationLogger()
        self.running = False
        self._task_processor_thread = None
        self._lock = threading.Lock()
    
    def start(self):
        """Start the task manager."""
        self.running = True
        self._task_processor_thread = threading.Thread(target=self._process_tasks, daemon=True)
        self._task_processor_thread.start()
        self.logger.info("Distributed task manager started")
    
    def stop(self):
        """Stop the task manager."""
        self.running = False
        if self._task_processor_thread:
            self._task_processor_thread.join(timeout=5)
        self.logger.info("Distributed task manager stopped")
    
    def submit_task(self, task_type: str, payload: Dict[str, Any]) -> str:
        """Submit a task for distributed execution."""
        task_id = str(uuid.uuid4())
        
        task = DistributedTask(
            task_id=task_id,
            task_type=task_type,
            payload=payload
        )
        
        with self._lock:
            self.tasks[task_id] = task
            self.task_queue.append(task_id)
        
        self.logger.info(f"Submitted task {task_id} of type {task_type}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status,
            'assigned_node': task.assigned_node,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'result': task.result,
            'error': task.error
        }
    
    def _process_tasks(self):
        """Process tasks from the queue."""
        while self.running:
            try:
                if self.task_queue:
                    with self._lock:
                        if self.task_queue:
                            task_id = self.task_queue.popleft()
                            task = self.tasks.get(task_id)
                            
                            if task and task.status == "pending":
                                self._assign_and_execute_task(task)
                
                time.sleep(1)  # Check for new tasks every second
            
            except Exception as e:
                self.logger.error(f"Error in task processing: {e}")
                time.sleep(5)
    
    def _assign_and_execute_task(self, task: DistributedTask):
        """Assign and execute a task on an available node."""
        # Find the best node for the task
        available_nodes = self.cluster_manager.get_active_nodes()
        
        if not available_nodes:
            self.logger.warning(f"No available nodes for task {task.task_id}")
            return
        
        # Simple load balancing: choose node with lowest load factor
        best_node = min(available_nodes, key=lambda x: x.load_factor)
        
        task.assigned_node = best_node.node_id
        task.status = "running"
        task.started_at = datetime.now()
        
        # Execute task (simulate)
        try:
            result = self._execute_task_on_node(task, best_node)
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now()
            
            self.logger.info(f"Task {task.task_id} completed on node {best_node.node_id}")
        
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            task.completed_at = datetime.now()
            
            self.logger.error(f"Task {task.task_id} failed on node {best_node.node_id}: {e}")
    
    def _execute_task_on_node(self, task: DistributedTask, node: ClusterNode) -> Dict[str, Any]:
        """Execute a task on a specific node."""
        # Simulate task execution
        time.sleep(0.1)  # Simulate processing time
        
        return {
            'task_id': task.task_id,
            'node_id': node.node_id,
            'execution_time': 0.1,
            'result': f"Task {task.task_type} completed successfully"
        }
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task execution statistics."""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for task in self.tasks.values() if task.status == "completed")
        failed_tasks = sum(1 for task in self.tasks.values() if task.status == "failed")
        running_tasks = sum(1 for task in self.tasks.values() if task.status == "running")
        pending_tasks = sum(1 for task in self.tasks.values() if task.status == "pending")
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'running_tasks': running_tasks,
            'pending_tasks': pending_tasks,
            'success_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
            'queue_length': len(self.task_queue)
        }


class DistributedArchitectureManager:
    """Main manager for distributed architecture."""
    
    def __init__(self, node_id: str, host: str, port: int):
        self.node_id = node_id
        self.cluster_manager = ClusterManager(node_id, host, port)
        self.data_manager = DistributedDataManager(self.cluster_manager)
        self.task_manager = DistributedTaskManager(self.cluster_manager)
        self.logger = NotificationLogger()
    
    async def start(self, seed_nodes: Optional[List[Tuple[str, int]]] = None):
        """Start the distributed architecture."""
        # Start cluster manager
        self.cluster_manager.start()
        
        # Join cluster if seed nodes provided
        if seed_nodes:
            self.cluster_manager.join_cluster(seed_nodes)
        
        # Start task manager
        self.task_manager.start()
        
        self.logger.info(f"Distributed architecture started for node {self.node_id}")
    
    async def stop(self):
        """Stop the distributed architecture."""
        # Stop task manager
        self.task_manager.stop()
        
        # Leave cluster
        self.cluster_manager.leave_cluster()
        
        # Stop cluster manager
        self.cluster_manager.stop()
        
        self.logger.info(f"Distributed architecture stopped for node {self.node_id}")
    
    async def store_notification_data(self, notification_id: str, data: Dict[str, Any]) -> bool:
        """Store notification data in the distributed system."""
        return await self.data_manager.store_data(notification_id, data)
    
    async def retrieve_notification_data(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve notification data from the distributed system."""
        return await self.data_manager.retrieve_data(notification_id)
    
    def submit_notification_task(self, task_type: str, payload: Dict[str, Any]) -> str:
        """Submit a notification task for distributed processing."""
        return self.task_manager.submit_task(task_type, payload)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'node_id': self.node_id,
            'cluster': self.cluster_manager.get_cluster_status(),
            'data_partitions': self.data_manager.get_partition_status(),
            'tasks': self.task_manager.get_task_statistics(),
            'timestamp': datetime.now().isoformat()
        }