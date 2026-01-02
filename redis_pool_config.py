#!/usr/bin/env python3
"""
Enhanced Redis Configuration with Connection Pooling for MediRemind Backend
Implements proper connection pooling for better performance and resource management.
"""

import os
import redis
from typing import Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Redis Cloud Connection Details
REDIS_HOST = os.getenv("REDIS_HOST", "redis-12735.crce204.eu-west-2-3.ec2.redns.redis-cloud.com")
REDIS_PORT = int(os.getenv("REDIS_PORT", "12735"))
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "default")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Connection Pool Configuration
REDIS_POOL_MAX_CONNECTIONS = int(os.getenv("REDIS_POOL_MAX_CONNECTIONS", "50"))
REDIS_POOL_TIMEOUT = int(os.getenv("REDIS_POOL_TIMEOUT", "30"))
REDIS_POOL_RETRY_ON_TIMEOUT = os.getenv("REDIS_POOL_RETRY_ON_TIMEOUT", "true").lower() == "true"
REDIS_POOL_HEALTH_CHECK_INTERVAL = int(os.getenv("REDIS_POOL_HEALTH_CHECK_INTERVAL", "30"))

# Redis databases (Redis Cloud typically only supports database 0)
REDIS_CACHE_DB = 0  # For general caching
REDIS_CELERY_DB = 0  # For Celery broker and results (same as cache)
REDIS_SESSION_DB = 0  # For session storage (same as cache)

class RedisConnectionPool:
    """Singleton class to manage Redis connection pools"""
    
    _instance = None
    _pools = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisConnectionPool, cls).__new__(cls)
        return cls._instance
    
    def get_pool(self, db: int = 0, max_connections: int = None) -> redis.ConnectionPool:
        """Get or create a connection pool for the specified database"""
        if db not in self._pools:
            max_conn = max_connections or REDIS_POOL_MAX_CONNECTIONS
            
            self._pools[db] = redis.ConnectionPool(
                host=REDIS_HOST,
                port=REDIS_PORT,
                username=REDIS_USERNAME,
                password=REDIS_PASSWORD,
                db=db,
                max_connections=max_conn,
                socket_connect_timeout=REDIS_POOL_TIMEOUT,
                socket_timeout=REDIS_POOL_TIMEOUT,
                retry_on_timeout=REDIS_POOL_RETRY_ON_TIMEOUT,
                health_check_interval=REDIS_POOL_HEALTH_CHECK_INTERVAL,
                decode_responses=True
            )
            
            logger.info(f"Created Redis connection pool for DB {db} with max {max_conn} connections")
        
        return self._pools[db]
    
    def close_all_pools(self):
        """Close all connection pools"""
        for db, pool in self._pools.items():
            try:
                pool.disconnect()
                logger.info(f"Closed Redis connection pool for DB {db}")
            except Exception as e:
                logger.error(f"Error closing Redis pool for DB {db}: {e}")
        
        self._pools.clear()

# Global connection pool manager
redis_pool_manager = RedisConnectionPool()

def get_redis_url(db: int = 0) -> str:
    """Generate Redis URL for specified database."""
    return f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{db}"

def get_redis_connection(db: int = 0, decode_responses: bool = True, max_connections: int = None) -> redis.Redis:
    """Create Redis connection using connection pooling"""
    pool = redis_pool_manager.get_pool(db, max_connections)
    
    return redis.Redis(
        connection_pool=pool,
        decode_responses=decode_responses
    )

def get_redis_client(db: int = 0, max_connections: int = None) -> redis.Redis:
    """Alias for get_redis_connection for backward compatibility"""
    return get_redis_connection(db, max_connections=max_connections)

def test_redis_connection() -> bool:
    """Test Redis connection and return True if successful."""
    try:
        client = get_redis_connection()
        client.ping()
        logger.info(f"✅ Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        return False

def get_redis_stats() -> dict:
    """Get Redis connection pool statistics"""
    stats = {}
    
    for db, pool in redis_pool_manager._pools.items():
        try:
            client = redis.Redis(connection_pool=pool)
            info = client.info()
            
            stats[f"db_{db}"] = {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                    * 100
                ) if (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)) > 0 else 0,
                "pool_connections": pool._created_connections,
                "pool_available": len(pool._available_connections),
                "pool_in_use": pool._created_connections - len(pool._available_connections)
            }
        except Exception as e:
            logger.error(f"Error getting stats for DB {db}: {e}")
            stats[f"db_{db}"] = {"error": str(e)}
    
    return stats

# Redis configurations for different use cases
REDIS_CONFIGS = {
    'cache': {
        'url': get_redis_url(REDIS_CACHE_DB),
        'db': REDIS_CACHE_DB,
        'max_connections': 20,
        'description': 'General application caching'
    },
    'celery': {
        'broker_url': get_redis_url(REDIS_CELERY_DB),
        'result_backend': get_redis_url(REDIS_CELERY_DB),
        'db': REDIS_CELERY_DB,
        'max_connections': 15,
        'description': 'Celery task queue and results'
    },
    'session': {
        'url': get_redis_url(REDIS_SESSION_DB),
        'db': REDIS_SESSION_DB,
        'max_connections': 10,
        'description': 'User session storage'
    },
    'monitoring': {
        'url': get_redis_url(REDIS_CACHE_DB),
        'db': REDIS_CACHE_DB,
        'max_connections': 5,
        'description': 'Monitoring and metrics storage'
    }
}

# Celery configuration with connection pooling
CELERY_BROKER_URL = REDIS_CONFIGS['celery']['broker_url']
CELERY_RESULT_BACKEND = REDIS_CONFIGS['celery']['result_backend']

# Enhanced Celery configuration for Redis Cloud with connection pooling
celery_config = {
    'broker_url': CELERY_BROKER_URL,
    'result_backend': CELERY_RESULT_BACKEND,
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_track_started': True,
    'task_time_limit': 30 * 60,  # 30 minutes
    'task_soft_time_limit': 25 * 60,  # 25 minutes
    'worker_prefetch_multiplier': 1,
    'task_acks_late': True,
    'worker_disable_rate_limits': False,
    'task_compression': 'gzip',
    'result_compression': 'gzip',
    
    # Redis Cloud specific settings with connection pooling
    'broker_connection_retry_on_startup': True,
    'broker_connection_retry': True,
    'broker_connection_max_retries': 10,
    'broker_pool_limit': 10,  # Connection pool limit for broker
    'result_backend_max_retries': 10,
    'result_backend_pool_limit': 10,  # Connection pool limit for results
    'redis_socket_keepalive': True,
    'redis_socket_keepalive_options': {
        'TCP_KEEPIDLE': 300,
        'TCP_KEEPINTVL': 30,
        'TCP_KEEPCNT': 3,
    },
    
    # Task routing
    'task_routes': {
        'notifications.tasks.send_sms': {'queue': 'sms'},
        'notifications.tasks.send_email': {'queue': 'email'},
        'notifications.tasks.send_push': {'queue': 'push'},
    },
    
    # Connection pooling settings
    'broker_transport_options': {
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.5,
        'visibility_timeout': 3600,  # 1 hour
        'connection_pool_klass': 'redis.BlockingConnectionPool',
        'connection_pool_kwargs': {
            'max_connections': 10,
            'timeout': 30,
        }
    }
}

if __name__ == "__main__":
    print("Testing Enhanced Redis Configuration with Connection Pooling...")
    
    if test_redis_connection():
        print("\nRedis Connection Pool Statistics:")
        stats = get_redis_stats()
        for db_name, db_stats in stats.items():
            print(f"\n{db_name}:")
            for key, value in db_stats.items():
                print(f"  {key}: {value}")
    
    print("\nRedis Configuration:")
    for name, config in REDIS_CONFIGS.items():
        print(f"  {name.upper()}: {config['description']}")
        if 'url' in config:
            print(f"    URL: {config['url']}")
        if 'broker_url' in config:
            print(f"    Broker: {config['broker_url']}")
            print(f"    Backend: {config['result_backend']}")
        print(f"    Database: {config['db']}")
        print(f"    Max Connections: {config.get('max_connections', 'default')}")
        print()