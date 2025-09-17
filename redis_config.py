#!/usr/bin/env python3
"""
Redis Configuration for MediRemind Backend
Configures connection to Redis Cloud instance for caching and Celery task queue.
"""

import os
import redis
from typing import Optional
from urllib.parse import urlparse

# Redis Cloud Connection Details
REDIS_HOST = "redis-12735.crce204.eu-west-2-3.ec2.redns.redis-cloud.com"
REDIS_PORT = 12735
REDIS_USERNAME = "default"
REDIS_PASSWORD = "oE1Gh8TkVwGkuihbKt43XrQeZVTLbl4p"

# Redis URL for different databases
# Note: Redis Cloud typically only supports database 0
REDIS_CACHE_DB = 0  # For general caching
REDIS_CELERY_DB = 0  # For Celery broker and results (same as cache)
REDIS_SESSION_DB = 0  # For session storage (same as cache)

def get_redis_url(db: int = 0) -> str:
    """Generate Redis URL for specified database."""
    return f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{db}"

def get_redis_connection(db: int = 0, decode_responses: bool = True) -> redis.Redis:
    """Create Redis connection with proper configuration."""
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
        db=db,
        decode_responses=decode_responses,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )

def test_redis_connection() -> bool:
    """Test Redis connection and return True if successful."""
    try:
        client = get_redis_connection()
        client.ping()
        print(f"✅ Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        return False

# Redis configurations for different use cases
REDIS_CONFIGS = {
    'cache': {
        'url': get_redis_url(REDIS_CACHE_DB),
        'db': REDIS_CACHE_DB,
        'description': 'General application caching'
    },
    'celery': {
        'broker_url': get_redis_url(REDIS_CELERY_DB),
        'result_backend': get_redis_url(REDIS_CELERY_DB),
        'db': REDIS_CELERY_DB,
        'description': 'Celery task queue and results'
    },
    'session': {
        'url': get_redis_url(REDIS_SESSION_DB),
        'db': REDIS_SESSION_DB,
        'description': 'User session storage'
    }
}

# Celery configuration
CELERY_BROKER_URL = REDIS_CONFIGS['celery']['broker_url']
CELERY_RESULT_BACKEND = REDIS_CONFIGS['celery']['result_backend']

if __name__ == "__main__":
    print("Testing Redis Cloud connection...")
    test_redis_connection()
    
    print("\nRedis Configuration:")
    for name, config in REDIS_CONFIGS.items():
        print(f"  {name.upper()}: {config['description']}")
        if 'url' in config:
            print(f"    URL: {config['url']}")
        if 'broker_url' in config:
            print(f"    Broker: {config['broker_url']}")
            print(f"    Backend: {config['result_backend']}")
        print(f"    Database: {config['db']}")
        print()