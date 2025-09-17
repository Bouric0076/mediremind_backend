import time
import threading
import pickle
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, OrderedDict
from functools import wraps
import redis
from supabase_client import supabase
from .logging_config import notification_logger, LogCategory
from .monitoring import metrics_collector
from .performance import MemoryCache, CacheConfig, CacheStrategy
from redis_config import get_redis_connection, REDIS_CACHE_DB

class CacheLevel(Enum):
    MEMORY = "memory"        # In-memory cache (fastest)
    REDIS = "redis"          # Redis cache (shared across instances)
    DATABASE = "database"    # Database cache (persistent)

class CacheOperation(Enum):
    GET = "get"
    SET = "set"
    DELETE = "delete"
    INVALIDATE = "invalidate"
    REFRESH = "refresh"

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if not self.ttl_seconds:
            return False
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl_seconds)
    
    def touch(self):
        """Update access information"""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'ttl_seconds': self.ttl_seconds,
            'tags': self.tags,
            'size_bytes': self.size_bytes
        }

@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    errors: int = 0
    total_size_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'evictions': self.evictions,
            'errors': self.errors,
            'hit_rate_percent': self.hit_rate,
            'total_size_bytes': self.total_size_bytes
        }

class RedisCache:
    """Redis-based cache implementation"""
    
    def __init__(self, host: str = None, port: int = None, db: int = None, 
                 password: str = None, prefix: str = 'mediremind'):
        self.prefix = prefix
        self.stats = CacheStats()
        self.lock = threading.RLock()
        
        try:
            # Use cloud Redis configuration by default
            if all(param is None for param in [host, port, password, db]):
                self.redis_client = get_redis_connection(db=REDIS_CACHE_DB)
            else:
                # Fallback to custom configuration if provided
                self.redis_client = redis.Redis(
                    host=host or 'localhost', 
                    port=port or 6379, 
                    db=db or 0, 
                    password=password,
                    decode_responses=True, 
                    socket_timeout=5
                )
            # Test connection
            self.redis_client.ping()
            self.available = True
        except Exception as e:
            notification_logger.warning(
                LogCategory.CACHE,
                f"Redis connection failed: {str(e)}",
                "redis_cache"
            )
            self.redis_client = None
            self.available = False
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.available:
            return None
        
        try:
            prefixed_key = self._make_key(key)
            data = self.redis_client.get(prefixed_key)
            
            if data:
                with self.lock:
                    self.stats.hits += 1
                
                # Deserialize data
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    # Fallback to pickle for complex objects
                    return pickle.loads(data.encode('latin1'))
            else:
                with self.lock:
                    self.stats.misses += 1
                return None
                
        except Exception as e:
            with self.lock:
                self.stats.errors += 1
            
            notification_logger.error(
                LogCategory.CACHE,
                f"Redis get error: {str(e)}",
                "redis_cache",
                metadata={'key': key}
            )
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in Redis cache"""
        if not self.available:
            return False
        
        try:
            prefixed_key = self._make_key(key)
            
            # Serialize data
            try:
                data = json.dumps(value)
            except (TypeError, ValueError):
                # Fallback to pickle for complex objects
                data = pickle.dumps(value).decode('latin1')
            
            # Set with TTL if specified
            if ttl_seconds:
                result = self.redis_client.setex(prefixed_key, ttl_seconds, data)
            else:
                result = self.redis_client.set(prefixed_key, data)
            
            if result:
                with self.lock:
                    self.stats.sets += 1
                    self.stats.total_size_bytes += len(data)
            
            return bool(result)
            
        except Exception as e:
            with self.lock:
                self.stats.errors += 1
            
            notification_logger.error(
                LogCategory.CACHE,
                f"Redis set error: {str(e)}",
                "redis_cache",
                metadata={'key': key}
            )
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        if not self.available:
            return False
        
        try:
            prefixed_key = self._make_key(key)
            result = self.redis_client.delete(prefixed_key)
            
            if result:
                with self.lock:
                    self.stats.deletes += 1
            
            return bool(result)
            
        except Exception as e:
            with self.lock:
                self.stats.errors += 1
            
            notification_logger.error(
                LogCategory.CACHE,
                f"Redis delete error: {str(e)}",
                "redis_cache",
                metadata={'key': key}
            )
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries with prefix"""
        if not self.available:
            return False
        
        try:
            pattern = f"{self.prefix}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                result = self.redis_client.delete(*keys)
                with self.lock:
                    self.stats.deletes += len(keys)
                return bool(result)
            
            return True
            
        except Exception as e:
            with self.lock:
                self.stats.errors += 1
            
            notification_logger.error(
                LogCategory.CACHE,
                f"Redis clear error: {str(e)}",
                "redis_cache"
            )
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        stats = self.stats.to_dict()
        stats['available'] = self.available
        
        if self.available:
            try:
                info = self.redis_client.info('memory')
                stats['redis_memory_used'] = info.get('used_memory', 0)
                stats['redis_memory_peak'] = info.get('used_memory_peak', 0)
            except Exception:
                pass
        
        return stats

class MultiLevelCache:
    """Multi-level cache with memory, Redis, and database layers"""
    
    def __init__(self):
        # Initialize cache layers
        self.memory_cache = MemoryCache(CacheConfig(
            strategy=CacheStrategy.LRU,
            max_size=1000,
            ttl_seconds=300
        ))
        
        self.redis_cache = RedisCache()
        
        # Cache configuration for different data types
        self.cache_configs = {
            'user_profile': {'ttl': 1800, 'levels': [CacheLevel.MEMORY, CacheLevel.REDIS]},
            'appointment': {'ttl': 600, 'levels': [CacheLevel.MEMORY, CacheLevel.REDIS]},
            'notification_template': {'ttl': 3600, 'levels': [CacheLevel.MEMORY, CacheLevel.REDIS]},
            'staff_schedule': {'ttl': 900, 'levels': [CacheLevel.MEMORY, CacheLevel.REDIS]},
            'patient_info': {'ttl': 1200, 'levels': [CacheLevel.MEMORY, CacheLevel.REDIS]},
            'system_settings': {'ttl': 7200, 'levels': [CacheLevel.MEMORY, CacheLevel.REDIS]}
        }
        
        self.lock = threading.RLock()
        self.total_stats = CacheStats()
    
    def get(self, key: str, data_type: str = 'default') -> Optional[Any]:
        """Get value from multi-level cache"""
        config = self.cache_configs.get(data_type, {'levels': [CacheLevel.MEMORY]})
        
        # Try each cache level in order
        for level in config['levels']:
            try:
                if level == CacheLevel.MEMORY:
                    value = self.memory_cache.get(key)
                    if value is not None:
                        with self.lock:
                            self.total_stats.hits += 1
                        metrics_collector.increment_counter('cache.memory.hits')
                        return value
                
                elif level == CacheLevel.REDIS:
                    value = self.redis_cache.get(key)
                    if value is not None:
                        # Promote to higher cache levels
                        self.memory_cache.set(key, value)
                        
                        with self.lock:
                            self.total_stats.hits += 1
                        metrics_collector.increment_counter('cache.redis.hits')
                        return value
                
            except Exception as e:
                notification_logger.error(
                    LogCategory.CACHE,
                    f"Cache get error at level {level.value}: {str(e)}",
                    "multi_level_cache",
                    metadata={'key': key, 'level': level.value}
                )
        
        # Cache miss
        with self.lock:
            self.total_stats.misses += 1
        metrics_collector.increment_counter('cache.misses')
        return None
    
    def set(self, key: str, value: Any, data_type: str = 'default', 
           ttl_seconds: Optional[int] = None) -> bool:
        """Set value in multi-level cache"""
        config = self.cache_configs.get(data_type, {'levels': [CacheLevel.MEMORY]})
        ttl = ttl_seconds or config.get('ttl', 300)
        
        success = False
        
        # Set in all configured cache levels
        for level in config['levels']:
            try:
                if level == CacheLevel.MEMORY:
                    result = self.memory_cache.set(key, value)
                    if result:
                        success = True
                        metrics_collector.increment_counter('cache.memory.sets')
                
                elif level == CacheLevel.REDIS:
                    result = self.redis_cache.set(key, value, ttl)
                    if result:
                        success = True
                        metrics_collector.increment_counter('cache.redis.sets')
                
            except Exception as e:
                notification_logger.error(
                    LogCategory.CACHE,
                    f"Cache set error at level {level.value}: {str(e)}",
                    "multi_level_cache",
                    metadata={'key': key, 'level': level.value}
                )
        
        if success:
            with self.lock:
                self.total_stats.sets += 1
        
        return success
    
    def delete(self, key: str, data_type: str = 'default') -> bool:
        """Delete key from all cache levels"""
        config = self.cache_configs.get(data_type, {'levels': [CacheLevel.MEMORY]})
        
        success = False
        
        # Delete from all cache levels
        for level in config['levels']:
            try:
                if level == CacheLevel.MEMORY:
                    result = self.memory_cache.delete(key)
                    if result:
                        success = True
                
                elif level == CacheLevel.REDIS:
                    result = self.redis_cache.delete(key)
                    if result:
                        success = True
                
            except Exception as e:
                notification_logger.error(
                    LogCategory.CACHE,
                    f"Cache delete error at level {level.value}: {str(e)}",
                    "multi_level_cache",
                    metadata={'key': key, 'level': level.value}
                )
        
        if success:
            with self.lock:
                self.total_stats.deletes += 1
        
        return success
    
    def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate cache entries by tags"""
        # This would require implementing tag tracking
        # For now, we'll implement a basic pattern-based invalidation
        invalidated = 0
        
        for tag in tags:
            # Clear memory cache entries matching tag pattern
            keys_to_delete = []
            for key in self.memory_cache.cache.keys():
                if tag in key:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                if self.memory_cache.delete(key):
                    invalidated += 1
            
            # Clear Redis cache entries matching tag pattern
            if self.redis_cache.available:
                try:
                    pattern = f"{self.redis_cache.prefix}:*{tag}*"
                    keys = self.redis_cache.redis_client.keys(pattern)
                    if keys:
                        self.redis_cache.redis_client.delete(*keys)
                        invalidated += len(keys)
                except Exception as e:
                    notification_logger.error(
                        LogCategory.CACHE,
                        f"Tag invalidation error: {str(e)}",
                        "multi_level_cache",
                        metadata={'tag': tag}
                    )
        
        return invalidated
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            'total': self.total_stats.to_dict(),
            'memory': self.memory_cache.get_statistics(),
            'redis': self.redis_cache.get_stats(),
            'configurations': self.cache_configs
        }

class CacheManager:
    """Central cache management system"""
    
    def __init__(self):
        self.cache = MultiLevelCache()
        self.cache_warmup_tasks = []
        self.lock = threading.RLock()
        
        # Background cache maintenance
        self.maintenance_thread = None
        self.is_running = False
    
    def start_maintenance(self):
        """Start background cache maintenance"""
        if self.is_running:
            return
        
        self.is_running = True
        self.maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.maintenance_thread.start()
        
        notification_logger.info(
            LogCategory.CACHE,
            "Cache maintenance started",
            "cache_manager"
        )
    
    def stop_maintenance(self):
        """Stop background cache maintenance"""
        self.is_running = False
        if self.maintenance_thread:
            self.maintenance_thread.join(timeout=5)
        
        notification_logger.info(
            LogCategory.CACHE,
            "Cache maintenance stopped",
            "cache_manager"
        )
    
    def _maintenance_loop(self):
        """Background maintenance loop"""
        while self.is_running:
            try:
                # Perform cache warmup
                self._perform_cache_warmup()
                
                # Clean expired entries
                self._clean_expired_entries()
                
                # Generate cache reports
                self._generate_cache_reports()
                
                time.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                notification_logger.error(
                    LogCategory.CACHE,
                    f"Cache maintenance error: {str(e)}",
                    "cache_manager",
                    error_details=str(e)
                )
                time.sleep(60)
    
    def _perform_cache_warmup(self):
        """Perform cache warmup for frequently accessed data"""
        try:
            # Warm up user profiles for active users
            self._warmup_user_profiles()
            
            # Warm up today's appointments
            self._warmup_todays_appointments()
            
            # Warm up notification templates
            self._warmup_notification_templates()
            
        except Exception as e:
            notification_logger.error(
                LogCategory.CACHE,
                f"Cache warmup error: {str(e)}",
                "cache_manager"
            )
    
    def _warmup_user_profiles(self):
        """Warm up user profiles cache"""
        try:
            # Get recently active users
            recent_users = supabase.table('users').select('id,email,phone').gte(
                'last_login', (datetime.now() - timedelta(days=7)).isoformat()
            ).limit(100).execute()
            
            for user in recent_users.data:
                cache_key = f"user_profile:{user['id']}"
                if not self.cache.get(cache_key, 'user_profile'):
                    self.cache.set(cache_key, user, 'user_profile')
            
        except Exception as e:
            notification_logger.warning(
                LogCategory.CACHE,
                f"User profile warmup failed: {str(e)}",
                "cache_manager"
            )
    
    def _warmup_todays_appointments(self):
        """Warm up today's appointments cache"""
        try:
            today = datetime.now().date().isoformat()
            appointments = supabase.table('appointments').select(
                'id,patient_id,staff_id,appointment_date,status'
            ).gte('appointment_date', today).lt(
                'appointment_date', (datetime.now().date() + timedelta(days=1)).isoformat()
            ).execute()
            
            for appointment in appointments.data:
                cache_key = f"appointment:{appointment['id']}"
                self.cache.set(cache_key, appointment, 'appointment')
            
        except Exception as e:
            notification_logger.warning(
                LogCategory.CACHE,
                f"Appointments warmup failed: {str(e)}",
                "cache_manager"
            )
    
    def _warmup_notification_templates(self):
        """Warm up notification templates cache"""
        try:
            templates = supabase.table('notification_templates').select('*').execute()
            
            for template in templates.data:
                cache_key = f"notification_template:{template['id']}"
                self.cache.set(cache_key, template, 'notification_template')
            
        except Exception as e:
            notification_logger.warning(
                LogCategory.CACHE,
                f"Notification templates warmup failed: {str(e)}",
                "cache_manager"
            )
    
    def _clean_expired_entries(self):
        """Clean expired cache entries"""
        # This would implement cleanup logic for expired entries
        pass
    
    def _generate_cache_reports(self):
        """Generate cache performance reports"""
        stats = self.cache.get_comprehensive_stats()
        
        # Log cache performance metrics
        metrics_collector.record_gauge('cache.hit_rate', stats['total']['hit_rate_percent'])
        metrics_collector.record_gauge('cache.total_size_bytes', stats['total']['total_size_bytes'])
        
        # Alert on low hit rates
        if stats['total']['hit_rate_percent'] < 70:
            notification_logger.warning(
                LogCategory.CACHE,
                f"Low cache hit rate: {stats['total']['hit_rate_percent']:.1f}%",
                "cache_manager",
                metadata=stats
            )
    
    # Convenience methods for common cache operations
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from cache or database"""
        cache_key = f"user_profile:{user_id}"
        
        # Try cache first
        profile = self.cache.get(cache_key, 'user_profile')
        if profile:
            return profile
        
        # Fetch from database
        try:
            result = supabase.table('users').select('*').eq('id', user_id).single().execute()
            if result.data:
                self.cache.set(cache_key, result.data, 'user_profile')
                return result.data
        except Exception as e:
            notification_logger.error(
                LogCategory.CACHE,
                f"Failed to fetch user profile: {str(e)}",
                "cache_manager",
                metadata={'user_id': user_id}
            )
        
        return None
    
    def get_appointment(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Get appointment from cache or database"""
        cache_key = f"appointment:{appointment_id}"
        
        # Try cache first
        appointment = self.cache.get(cache_key, 'appointment')
        if appointment:
            return appointment
        
        # Fetch from database
        try:
            result = supabase.table('appointments').select('*').eq('id', appointment_id).single().execute()
            if result.data:
                self.cache.set(cache_key, result.data, 'appointment')
                return result.data
        except Exception as e:
            notification_logger.error(
                LogCategory.CACHE,
                f"Failed to fetch appointment: {str(e)}",
                "cache_manager",
                metadata={'appointment_id': appointment_id}
            )
        
        return None
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user"""
        tags = [f"user:{user_id}", f"user_profile:{user_id}"]
        invalidated = self.cache.invalidate_by_tags(tags)
        
        notification_logger.info(
            LogCategory.CACHE,
            f"Invalidated {invalidated} cache entries for user {user_id}",
            "cache_manager"
        )
    
    def invalidate_appointment_cache(self, appointment_id: str):
        """Invalidate cache entries for an appointment"""
        tags = [f"appointment:{appointment_id}"]
        invalidated = self.cache.invalidate_by_tags(tags)
        
        notification_logger.info(
            LogCategory.CACHE,
            f"Invalidated {invalidated} cache entries for appointment {appointment_id}",
            "cache_manager"
        )
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return self.cache.get_comprehensive_stats()

# Global cache manager instance
cache_manager = CacheManager()

# Decorator for automatic caching
def cached(data_type: str = 'default', ttl_seconds: Optional[int] = None, 
          key_func: Optional[Callable] = None):
    """Decorator for automatic function result caching"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__] + [str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()]
                cache_key = hashlib.md5(':'.join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            result = cache_manager.cache.get(cache_key, data_type)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.cache.set(cache_key, result, data_type, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator

# Convenience functions
def get_cached_data(key: str, data_type: str = 'default') -> Optional[Any]:
    """Get data from cache"""
    return cache_manager.cache.get(key, data_type)

def set_cached_data(key: str, value: Any, data_type: str = 'default', ttl_seconds: Optional[int] = None) -> bool:
    """Set data in cache"""
    return cache_manager.cache.set(key, value, data_type, ttl_seconds)

def delete_cached_data(key: str, data_type: str = 'default') -> bool:
    """Delete data from cache"""
    return cache_manager.cache.delete(key, data_type)

def clear_all_cache():
    """Clear all cache data"""
    cache_manager.cache.memory_cache.clear()
    cache_manager.cache.redis_cache.clear()
    
    notification_logger.info(
        LogCategory.CACHE,
        "All cache data cleared",
        "cache_manager"
    )

__all__ = [
    'CacheLevel', 'CacheOperation', 'CacheEntry', 'CacheStats',
    'RedisCache', 'MultiLevelCache', 'CacheManager',
    'cache_manager', 'cached', 'get_cached_data', 'set_cached_data',
    'delete_cached_data', 'clear_all_cache'
]