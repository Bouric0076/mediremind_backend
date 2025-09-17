import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import statistics
from collections import defaultdict, deque
from functools import wraps, lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from supabase_client import supabase
from .logging_config import notification_logger, LogCategory
from .monitoring import metrics_collector

class CacheStrategy(Enum):
    LRU = "lru"              # Least Recently Used
    TTL = "ttl"              # Time To Live
    LFU = "lfu"              # Least Frequently Used
    FIFO = "fifo"            # First In First Out

class QueryOptimizationLevel(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class CacheConfig:
    """Configuration for caching"""
    strategy: CacheStrategy = CacheStrategy.LRU
    max_size: int = 1000
    ttl_seconds: int = 300
    enable_compression: bool = False
    enable_encryption: bool = False
    
@dataclass
class QueryMetrics:
    """Metrics for database queries"""
    query_hash: str
    execution_time_ms: float
    timestamp: datetime
    row_count: int
    cache_hit: bool = False
    optimization_applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query_hash': self.query_hash,
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat(),
            'row_count': self.row_count,
            'cache_hit': self.cache_hit,
            'optimization_applied': self.optimization_applied
        }

class MemoryCache:
    """High-performance in-memory cache with multiple strategies"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache = {}
        self.access_times = {}
        self.access_counts = defaultdict(int)
        self.insertion_order = deque()
        self.lock = threading.RLock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                # Update access tracking
                self.access_times[key] = datetime.now()
                self.access_counts[key] += 1
                self.hits += 1
                
                # Check TTL if applicable
                if self.config.strategy == CacheStrategy.TTL:
                    entry_time, value = self.cache[key]
                    if datetime.now() - entry_time > timedelta(seconds=self.config.ttl_seconds):
                        self._remove_key(key)
                        self.misses += 1
                        return None
                    return value
                
                return self.cache[key]
            else:
                self.misses += 1
                return None
    
    def set(self, key: str, value: Any) -> bool:
        """Set value in cache"""
        with self.lock:
            # Check if we need to evict
            if len(self.cache) >= self.config.max_size and key not in self.cache:
                self._evict()
            
            # Store value based on strategy
            if self.config.strategy == CacheStrategy.TTL:
                self.cache[key] = (datetime.now(), value)
            else:
                self.cache[key] = value
            
            # Update tracking
            self.access_times[key] = datetime.now()
            self.access_counts[key] += 1
            
            if key not in self.insertion_order:
                self.insertion_order.append(key)
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                self._remove_key(key)
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.access_counts.clear()
            self.insertion_order.clear()
    
    def _evict(self):
        """Evict entries based on strategy"""
        if not self.cache:
            return
        
        if self.config.strategy == CacheStrategy.LRU:
            # Remove least recently used
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            self._remove_key(oldest_key)
        
        elif self.config.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            least_used_key = min(self.access_counts.keys(), key=lambda k: self.access_counts[k])
            self._remove_key(least_used_key)
        
        elif self.config.strategy == CacheStrategy.FIFO:
            # Remove first inserted
            if self.insertion_order:
                oldest_key = self.insertion_order.popleft()
                self._remove_key(oldest_key)
        
        elif self.config.strategy == CacheStrategy.TTL:
            # Remove expired entries
            current_time = datetime.now()
            expired_keys = []
            for key, (entry_time, _) in self.cache.items():
                if current_time - entry_time > timedelta(seconds=self.config.ttl_seconds):
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_key(key)
            
            # If no expired entries, fall back to LRU
            if not expired_keys and self.cache:
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                self._remove_key(oldest_key)
        
        self.evictions += 1
    
    def _remove_key(self, key: str):
        """Remove key and all associated tracking"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.access_counts.pop(key, None)
        
        if key in self.insertion_order:
            self.insertion_order.remove(key)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate_percent': hit_rate,
                'evictions': self.evictions,
                'current_size': len(self.cache),
                'max_size': self.config.max_size,
                'strategy': self.config.strategy.value
            }

class QueryOptimizer:
    """Database query optimizer"""
    
    def __init__(self):
        self.query_cache = MemoryCache(CacheConfig(max_size=500, ttl_seconds=600))
        self.query_metrics = deque(maxlen=10000)
        self.slow_queries = deque(maxlen=1000)
        self.optimization_rules = []
        self.lock = threading.RLock()
        
        # Performance thresholds
        self.slow_query_threshold_ms = 1000
        self.cache_threshold_ms = 100
        
        # Initialize optimization rules
        self._initialize_optimization_rules()
    
    def _initialize_optimization_rules(self):
        """Initialize query optimization rules"""
        self.optimization_rules = [
            self._add_limit_clause,
            self._optimize_select_fields,
            self._add_indexes_hint,
            self._optimize_joins,
            self._add_where_conditions
        ]
    
    def execute_query(self, table: str, query_params: Dict[str, Any], 
                     cache_key: str = None, enable_cache: bool = True) -> Dict[str, Any]:
        """Execute optimized database query"""
        start_time = time.time()
        
        # Generate cache key if not provided
        if not cache_key:
            cache_key = self._generate_cache_key(table, query_params)
        
        # Check cache first
        if enable_cache:
            cached_result = self.query_cache.get(cache_key)
            if cached_result:
                execution_time = (time.time() - start_time) * 1000
                
                # Record cache hit metrics
                metrics = QueryMetrics(
                    query_hash=cache_key,
                    execution_time_ms=execution_time,
                    timestamp=datetime.now(),
                    row_count=len(cached_result.get('data', [])),
                    cache_hit=True
                )
                
                with self.lock:
                    self.query_metrics.append(metrics)
                
                metrics_collector.increment_counter('database.cache.hits')
                return cached_result
        
        # Apply optimizations
        optimized_params = self._apply_optimizations(table, query_params)
        
        try:
            # Execute query
            result = self._execute_supabase_query(table, optimized_params)
            execution_time = (time.time() - start_time) * 1000
            
            # Record metrics
            metrics = QueryMetrics(
                query_hash=cache_key,
                execution_time_ms=execution_time,
                timestamp=datetime.now(),
                row_count=len(result.get('data', [])),
                cache_hit=False,
                optimization_applied=optimized_params != query_params
            )
            
            with self.lock:
                self.query_metrics.append(metrics)
                
                # Track slow queries
                if execution_time > self.slow_query_threshold_ms:
                    self.slow_queries.append({
                        'table': table,
                        'params': query_params,
                        'execution_time_ms': execution_time,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Cache result if appropriate
            if enable_cache and execution_time > self.cache_threshold_ms:
                self.query_cache.set(cache_key, result)
            
            # Record performance metrics
            metrics_collector.record_timer('database.query.execution_time', execution_time)
            metrics_collector.increment_counter('database.queries.total')
            
            if execution_time > self.slow_query_threshold_ms:
                metrics_collector.increment_counter('database.queries.slow')
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            notification_logger.error(
                LogCategory.DATABASE,
                f"Query execution failed: {str(e)}",
                "query_optimizer",
                metadata={'table': table, 'params': query_params, 'execution_time_ms': execution_time}
            )
            
            metrics_collector.increment_counter('database.queries.errors')
            raise
    
    def _generate_cache_key(self, table: str, query_params: Dict[str, Any]) -> str:
        """Generate cache key for query"""
        key_data = f"{table}:{json.dumps(query_params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _apply_optimizations(self, table: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply optimization rules to query parameters"""
        optimized_params = query_params.copy()
        
        for rule in self.optimization_rules:
            try:
                optimized_params = rule(table, optimized_params)
            except Exception as e:
                notification_logger.warning(
                    LogCategory.DATABASE,
                    f"Optimization rule failed: {str(e)}",
                    "query_optimizer"
                )
        
        return optimized_params
    
    def _add_limit_clause(self, table: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add reasonable limit to queries without one"""
        if 'limit' not in params and 'count' not in params:
            # Add default limit based on table type
            if table in ['appointments', 'notifications']:
                params['limit'] = 100
            else:
                params['limit'] = 50
        
        return params
    
    def _optimize_select_fields(self, table: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize select fields to reduce data transfer"""
        if 'select' not in params:
            # Define essential fields for common tables
            essential_fields = {
                'appointments': 'id,patient_id,staff_id,appointment_date,status,notes',
                'patients': 'id,first_name,last_name,email,phone,date_of_birth',
                'staff_profiles': 'id,user_id,first_name,last_name,specialization,department',
                'notifications': 'id,user_id,type,message,status,created_at',
                'users': 'id,email,phone,created_at,last_login'
            }
            
            if table in essential_fields:
                params['select'] = essential_fields[table]
        
        return params
    
    def _add_indexes_hint(self, table: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add index hints for better performance"""
        # This would be implemented based on your specific database indexes
        # For now, we'll add ordering hints for common queries
        
        if table == 'appointments' and 'order' not in params:
            params['order'] = 'appointment_date.desc'
        elif table == 'notifications' and 'order' not in params:
            params['order'] = 'created_at.desc'
        
        return params
    
    def _optimize_joins(self, table: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize join operations"""
        # Suggest using foreign key relationships efficiently
        if table == 'appointments' and 'select' in params:
            select_fields = params['select']
            if 'patient' in select_fields or 'staff' in select_fields:
                # Ensure we're using efficient joins
                if 'patient(' not in select_fields and 'staff(' not in select_fields:
                    # Add specific field selections for related tables
                    params['select'] = select_fields + ',patients(first_name,last_name,email),staff_profiles(first_name,last_name)'
        
        return params
    
    def _add_where_conditions(self, table: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add efficient where conditions"""
        # Add date range filters for time-sensitive data
        if table in ['appointments', 'notifications'] and 'gte' not in params and 'lte' not in params:
            # Default to last 30 days for performance
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            
            if table == 'appointments':
                params['appointment_date'] = f'gte.{thirty_days_ago}'
            elif table == 'notifications':
                params['created_at'] = f'gte.{thirty_days_ago}'
        
        return params
    
    def _execute_supabase_query(self, table: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute query using Supabase client"""
        query = supabase.table(table)
        
        # Apply select
        if 'select' in params:
            query = query.select(params['select'])
        else:
            query = query.select('*')
        
        # Apply filters
        for key, value in params.items():
            if key in ['select', 'order', 'limit', 'offset']:
                continue
            
            if isinstance(value, str) and '.' in value:
                # Handle operators like gte.2023-01-01
                operator, operand = value.split('.', 1)
                if operator == 'eq':
                    query = query.eq(key, operand)
                elif operator == 'gte':
                    query = query.gte(key, operand)
                elif operator == 'lte':
                    query = query.lte(key, operand)
                elif operator == 'gt':
                    query = query.gt(key, operand)
                elif operator == 'lt':
                    query = query.lt(key, operand)
                elif operator == 'like':
                    query = query.like(key, operand)
                elif operator == 'ilike':
                    query = query.ilike(key, operand)
            else:
                query = query.eq(key, value)
        
        # Apply ordering
        if 'order' in params:
            order_clause = params['order']
            if '.desc' in order_clause:
                field = order_clause.replace('.desc', '')
                query = query.order(field, desc=True)
            elif '.asc' in order_clause:
                field = order_clause.replace('.asc', '')
                query = query.order(field, desc=False)
            else:
                query = query.order(order_clause)
        
        # Apply limit and offset
        if 'limit' in params:
            query = query.limit(params['limit'])
        
        if 'offset' in params:
            query = query.offset(params['offset'])
        
        # Execute query
        result = query.execute()
        return {'data': result.data, 'count': len(result.data)}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        with self.lock:
            if not self.query_metrics:
                return {'message': 'No query metrics available'}
            
            execution_times = [m.execution_time_ms for m in self.query_metrics]
            cache_hits = sum(1 for m in self.query_metrics if m.cache_hit)
            total_queries = len(self.query_metrics)
            
            return {
                'total_queries': total_queries,
                'cache_hit_rate': (cache_hits / total_queries * 100) if total_queries > 0 else 0,
                'avg_execution_time_ms': statistics.mean(execution_times),
                'median_execution_time_ms': statistics.median(execution_times),
                'p95_execution_time_ms': statistics.quantiles(execution_times, n=20)[18] if len(execution_times) > 1 else 0,
                'slow_queries_count': len(self.slow_queries),
                'cache_statistics': self.query_cache.get_statistics(),
                'recent_slow_queries': list(self.slow_queries)[-10:]
            }
    
    def clear_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        notification_logger.info(
            LogCategory.SYSTEM,
            "Query cache cleared",
            "query_optimizer"
        )

class ConnectionPool:
    """Database connection pool for improved performance"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.active_connections = 0
        self.connection_queue = deque()
        self.lock = threading.RLock()
        
        # Statistics
        self.total_requests = 0
        self.successful_connections = 0
        self.failed_connections = 0
        self.avg_wait_time_ms = 0
    
    def get_connection(self, timeout_seconds: int = 30):
        """Get database connection from pool"""
        start_time = time.time()
        
        with self.lock:
            self.total_requests += 1
            
            # Check if we can create a new connection
            if self.active_connections < self.max_connections:
                self.active_connections += 1
                self.successful_connections += 1
                
                wait_time = (time.time() - start_time) * 1000
                self._update_avg_wait_time(wait_time)
                
                return DatabaseConnection(self)
            
            # Wait for available connection
            end_time = start_time + timeout_seconds
            
            while time.time() < end_time:
                if self.connection_queue:
                    connection = self.connection_queue.popleft()
                    self.successful_connections += 1
                    
                    wait_time = (time.time() - start_time) * 1000
                    self._update_avg_wait_time(wait_time)
                    
                    return connection
                
                time.sleep(0.1)
            
            # Timeout reached
            self.failed_connections += 1
            raise TimeoutError("Connection pool timeout")
    
    def return_connection(self, connection):
        """Return connection to pool"""
        with self.lock:
            if len(self.connection_queue) < self.max_connections:
                self.connection_queue.append(connection)
            else:
                self.active_connections -= 1
    
    def _update_avg_wait_time(self, wait_time_ms: float):
        """Update average wait time"""
        if self.successful_connections == 1:
            self.avg_wait_time_ms = wait_time_ms
        else:
            # Exponential moving average
            alpha = 0.1
            self.avg_wait_time_ms = (alpha * wait_time_ms) + ((1 - alpha) * self.avg_wait_time_ms)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self.lock:
            success_rate = (self.successful_connections / self.total_requests * 100) if self.total_requests > 0 else 0
            
            return {
                'max_connections': self.max_connections,
                'active_connections': self.active_connections,
                'queued_connections': len(self.connection_queue),
                'total_requests': self.total_requests,
                'successful_connections': self.successful_connections,
                'failed_connections': self.failed_connections,
                'success_rate_percent': success_rate,
                'avg_wait_time_ms': self.avg_wait_time_ms
            }

class DatabaseConnection:
    """Database connection wrapper"""
    
    def __init__(self, pool: ConnectionPool):
        self.pool = pool
        self.created_at = datetime.now()
        self.last_used = datetime.now()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pool.return_connection(self)
    
    def execute_query(self, table: str, params: Dict[str, Any]):
        """Execute query using this connection"""
        self.last_used = datetime.now()
        # This would use the actual database connection
        # For now, we'll use the global query optimizer
        return query_optimizer.execute_query(table, params)

class PerformanceManager:
    """Central performance management system"""
    
    def __init__(self):
        self.query_optimizer = QueryOptimizer()
        self.connection_pool = ConnectionPool()
        self.performance_cache = MemoryCache(CacheConfig(max_size=2000, ttl_seconds=1800))
        
        # Performance monitoring
        self.performance_metrics = deque(maxlen=10000)
        self.lock = threading.RLock()
        
        # Background optimization thread
        self.optimization_thread = None
        self.is_running = False
    
    def start_optimization_monitoring(self):
        """Start background performance monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self.optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.optimization_thread.start()
        
        notification_logger.info(
            LogCategory.SYSTEM,
            "Performance optimization monitoring started",
            "performance_manager"
        )
    
    def stop_optimization_monitoring(self):
        """Stop background performance monitoring"""
        self.is_running = False
        if self.optimization_thread:
            self.optimization_thread.join(timeout=5)
        
        notification_logger.info(
            LogCategory.SYSTEM,
            "Performance optimization monitoring stopped",
            "performance_manager"
        )
    
    def _optimization_loop(self):
        """Background optimization monitoring loop"""
        while self.is_running:
            try:
                # Analyze performance metrics
                self._analyze_performance()
                
                # Clean up expired cache entries
                self._cleanup_caches()
                
                # Generate performance reports
                self._generate_performance_alerts()
                
                time.sleep(60)  # Run every minute
                
            except Exception as e:
                notification_logger.error(
                    LogCategory.SYSTEM,
                    f"Error in optimization loop: {str(e)}",
                    "performance_manager",
                    error_details=str(e)
                )
                time.sleep(30)
    
    def _analyze_performance(self):
        """Analyze current performance metrics"""
        report = self.query_optimizer.get_performance_report()
        
        if 'avg_execution_time_ms' in report:
            avg_time = report['avg_execution_time_ms']
            
            # Record performance metrics
            metrics_collector.record_gauge('database.avg_query_time_ms', avg_time)
            metrics_collector.record_gauge('database.cache_hit_rate', report.get('cache_hit_rate', 0))
            
            # Alert on performance degradation
            if avg_time > 2000:  # 2 seconds
                notification_logger.warning(
                    LogCategory.PERFORMANCE,
                    f"High average query execution time: {avg_time:.2f}ms",
                    "performance_manager",
                    metadata=report
                )
    
    def _cleanup_caches(self):
        """Clean up expired cache entries"""
        # This would implement cache cleanup logic
        pass
    
    def _generate_performance_alerts(self):
        """Generate alerts for performance issues"""
        pool_stats = self.connection_pool.get_statistics()
        
        # Alert on high connection pool usage
        if pool_stats['success_rate_percent'] < 95:
            notification_logger.warning(
                LogCategory.PERFORMANCE,
                f"Low connection pool success rate: {pool_stats['success_rate_percent']:.1f}%",
                "performance_manager",
                metadata=pool_stats
            )
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            'query_performance': self.query_optimizer.get_performance_report(),
            'connection_pool': self.connection_pool.get_statistics(),
            'cache_performance': self.performance_cache.get_statistics(),
            'system_status': {
                'optimization_monitoring': self.is_running,
                'timestamp': datetime.now().isoformat()
            }
        }

# Global instances
query_optimizer = QueryOptimizer()
connection_pool = ConnectionPool()
performance_manager = PerformanceManager()

# Decorator for performance monitoring
def monitor_performance(cache_key: str = None, enable_cache: bool = True):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                
                # Record performance metrics
                metrics_collector.record_timer(f'function.{func.__name__}.execution_time', execution_time)
                metrics_collector.increment_counter(f'function.{func.__name__}.calls')
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                metrics_collector.increment_counter(f'function.{func.__name__}.errors')
                raise
        
        return wrapper
    return decorator

# Convenience functions
def execute_optimized_query(table: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Execute an optimized database query"""
    return query_optimizer.execute_query(table, params, **kwargs)

def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report"""
    return performance_manager.get_comprehensive_report()

def clear_all_caches():
    """Clear all performance caches"""
    query_optimizer.clear_cache()
    performance_manager.performance_cache.clear()
    notification_logger.info(
        LogCategory.SYSTEM,
        "All performance caches cleared",
        "performance_manager"
    )

__all__ = [
    'CacheStrategy', 'QueryOptimizationLevel', 'CacheConfig', 'QueryMetrics',
    'MemoryCache', 'QueryOptimizer', 'ConnectionPool', 'DatabaseConnection',
    'PerformanceManager', 'query_optimizer', 'connection_pool', 'performance_manager',
    'monitor_performance', 'execute_optimized_query', 'get_performance_report', 'clear_all_caches'
]