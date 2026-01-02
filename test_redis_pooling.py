#!/usr/bin/env python3
"""
Test Redis Connection Pooling functionality
"""

import os
import sys
import django
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from redis_pool_config import RedisConnectionPool, get_redis_connection, get_redis_client, REDIS_CACHE_DB
from notifications.cache_layer import RedisCache
from notifications.queue_manager import celery_app

def test_redis_connection_pool_singleton():
    """Test that RedisConnectionPool is a singleton"""
    print("=== Testing Redis Connection Pool Singleton ===")
    
    pool1 = RedisConnectionPool()
    pool2 = RedisConnectionPool()
    
    print(f"Pool 1 ID: {id(pool1)}")
    print(f"Pool 2 ID: {id(pool2)}")
    print(f"Same instance: {pool1 is pool2}")
    
    return pool1 is pool2

def test_redis_pool_creation():
    """Test Redis pool creation"""
    print("\n=== Testing Redis Pool Creation ===")
    
    pool = RedisConnectionPool()
    
    # Test different databases
    cache_pool = pool.get_pool(db=REDIS_CACHE_DB)
    default_pool = pool.get_pool(db=0)
    
    print(f"Cache pool created: {cache_pool is not None}")
    print(f"Default pool created: {default_pool is not None}")
    print(f"Same pool manager (expected): {cache_pool is default_pool}")
    print(f"Cache pool max connections: {cache_pool.max_connections}")
    print(f"Default pool max connections: {default_pool.max_connections}")
    
    return cache_pool is not None and default_pool is not None and cache_pool is default_pool

def test_redis_connection_reuse():
    """Test that connections are reused from the pool"""
    print("\n=== Testing Redis Connection Reuse ===")
    
    pool = RedisConnectionPool()
    redis_client = get_redis_client(db=REDIS_CACHE_DB)
    
    # Test basic operations
    test_key = "test_pool_reuse_key"
    test_value = "test_pool_reuse_value"
    
    # Set value
    result1 = redis_client.set(test_key, test_value)
    print(f"Set operation successful: {result1}")
    
    # Get value
    result2 = redis_client.get(test_key)
    print(f"Get operation successful: {result2 == test_value}")
    
    # Delete value
    result3 = redis_client.delete(test_key)
    print(f"Delete operation successful: {result3 == 1}")
    
    # Check connection info
    pool_info = redis_client.connection_pool
    print(f"Pool max connections: {pool_info.max_connections}")
    print(f"Pool current connections: {len(pool_info._in_use_connections)}")
    
    return result1 and result2 and result3

def test_concurrent_redis_operations():
    """Test concurrent Redis operations using the pool"""
    print("\n=== Testing Concurrent Redis Operations ===")
    
    def worker_operation(worker_id):
        """Worker function for concurrent operations"""
        try:
            redis_client = get_redis_client(db=REDIS_CACHE_DB)
            
            # Perform multiple operations
            for i in range(10):
                key = f"concurrent_test_{worker_id}_{i}"
                value = f"worker_{worker_id}_value_{i}"
                
                # Set
                redis_client.set(key, value)
                
                # Get
                retrieved = redis_client.get(key)
                if retrieved != value:
                    return False, f"Value mismatch for {key}"
                
                # Delete
                redis_client.delete(key)
            
            return True, f"Worker {worker_id} completed successfully"
        except Exception as e:
            return False, f"Worker {worker_id} failed: {str(e)}"
    
    # Test with multiple workers
    num_workers = 5
    results = []
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_operation, i) for i in range(num_workers)]
        
        for future in as_completed(futures):
            success, message = future.result()
            results.append((success, message))
            print(f"Worker result: {message}")
    
    # Check results
    all_success = all(success for success, _ in results)
    success_count = sum(1 for success, _ in results if success)
    
    print(f"All workers successful: {all_success}")
    print(f"Successful workers: {success_count}/{num_workers}")
    
    return all_success

def test_redis_cache_layer():
    """Test Redis cache layer with connection pooling"""
    print("\n=== Testing Redis Cache Layer ===")
    
    cache = RedisCache()
    
    # Test cache operations
    test_key = "test_cache_key"
    test_data = {"message": "test message", "timestamp": time.time()}
    
    # Set cache
    cache.set(test_key, test_data, ttl_seconds=60)
    print("✅ Cache set operation successful")
    
    # Get cache
    cached_data = cache.get(test_key)
    print(f"✅ Cache get operation successful: {cached_data == test_data}")
    
    # Delete cache
    cache.delete(test_key)
    deleted_data = cache.get(test_key)
    print(f"✅ Cache delete operation successful: {deleted_data is None}")
    
    return cached_data == test_data and deleted_data is None

def test_celery_redis_integration():
    """Test Celery integration with Redis pooling"""
    print("\n=== Testing Celery Redis Integration ===")
    
    try:
        # Test Celery connection
        result = celery_app.control.inspect()
        print(f"✅ Celery inspect available: {result is not None}")
        
        # Test Celery configuration
        broker_url = celery_app.conf.broker_url
        result_backend = celery_app.conf.result_backend
        
        print(f"✅ Broker URL configured: {broker_url is not None}")
        print(f"✅ Result backend configured: {result_backend is not None}")
        
        # Check if pool settings are applied
        pool_settings = celery_app.conf.worker_pool
        print(f"✅ Worker pool settings: {pool_settings}")
        
        return broker_url is not None and result_backend is not None
    except Exception as e:
        print(f"❌ Celery integration test failed: {e}")
        return False

def test_pool_performance():
    """Test pool performance with multiple operations"""
    print("\n=== Testing Pool Performance ===")
    
    # Test with pool
    start_time = time.time()
    pool_results = []
    
    for i in range(100):
        redis_client = get_redis_client(db=REDIS_CACHE_DB)
        key = f"perf_test_pool_{i}"
        redis_client.set(key, f"value_{i}")
        redis_client.get(key)
        redis_client.delete(key)
        pool_results.append(True)
    
    pool_time = time.time() - start_time
    
    print(f"✅ Pool operations completed in: {pool_time:.3f}s")
    print(f"✅ Total operations: {len(pool_results)}")
    print(f"✅ Operations per second: {len(pool_results)/pool_time:.2f}")
    
    return len(pool_results) > 0

def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning Up Test Data ===")
    
    try:
        redis_client = get_redis_client(db=REDIS_CACHE_DB)
        
        # Clean up test keys
        test_keys = redis_client.keys("test_*") + redis_client.keys("concurrent_test_*") + redis_client.keys("perf_test_*")
        if test_keys:
            redis_client.delete(*test_keys)
            print(f"✅ Cleaned up {len(test_keys)} test keys")
        else:
            print("✅ No test keys to clean up")
        
        return True
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return False

def main():
    """Run all Redis connection pooling tests"""
    print("🚀 Testing Redis Connection Pooling")
    print("=" * 50)
    
    tests = [
        ("Pool Singleton", test_redis_connection_pool_singleton),
        ("Pool Creation", test_redis_pool_creation),
        ("Connection Reuse", test_redis_connection_reuse),
        ("Concurrent Operations", test_concurrent_redis_operations),
        ("Cache Layer", test_redis_cache_layer),
        ("Celery Integration", test_celery_redis_integration),
        ("Pool Performance", test_pool_performance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Cleanup
    cleanup_result = cleanup_test_data()
    results.append(("Cleanup", cleanup_result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All Redis connection pooling tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)