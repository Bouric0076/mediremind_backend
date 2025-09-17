import unittest
import time
import threading
import asyncio
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable
import psutil
import gc
import sys
import os
from unittest.mock import patch, Mock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_config import BaseTestCase, TestDataFactory, with_timeout
from notifications.scheduler import NotificationScheduler, ScheduledTask, TaskPriority
from notifications.queue_manager import QueueManager, QueueType
from notifications.background_tasks import BackgroundTaskManager
from notifications.failsafe import FailsafeDeliveryManager
from notifications.performance import MemoryCache, QueryOptimizer, CacheStrategy, CacheConfig
from notifications.cache_layer import CacheManager, MultiLevelCache
from notifications.database_optimization import DatabaseOptimizer, BatchProcessor

class PerformanceMetrics:
    """Container for performance metrics"""
    
    def __init__(self):
        self.response_times = []
        self.throughput_rates = []
        self.memory_usage = []
        self.cpu_usage = []
        self.error_rates = []
        self.start_time = None
        self.end_time = None
    
    def add_response_time(self, response_time: float):
        """Add response time measurement"""
        self.response_times.append(response_time)
    
    def add_throughput_rate(self, rate: float):
        """Add throughput rate measurement"""
        self.throughput_rates.append(rate)
    
    def add_memory_usage(self, usage: float):
        """Add memory usage measurement"""
        self.memory_usage.append(usage)
    
    def add_cpu_usage(self, usage: float):
        """Add CPU usage measurement"""
        self.cpu_usage.append(usage)
    
    def add_error_rate(self, rate: float):
        """Add error rate measurement"""
        self.error_rates.append(rate)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        summary = {
            'duration': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0,
            'response_times': self._get_stats(self.response_times),
            'throughput_rates': self._get_stats(self.throughput_rates),
            'memory_usage': self._get_stats(self.memory_usage),
            'cpu_usage': self._get_stats(self.cpu_usage),
            'error_rates': self._get_stats(self.error_rates)
        }
        return summary
    
    def _get_stats(self, data: List[float]) -> Dict[str, float]:
        """Calculate statistics for a data series"""
        if not data:
            return {'min': 0, 'max': 0, 'mean': 0, 'median': 0, 'std': 0, 'p95': 0, 'p99': 0}
        
        return {
            'min': min(data),
            'max': max(data),
            'mean': statistics.mean(data),
            'median': statistics.median(data),
            'std': statistics.stdev(data) if len(data) > 1 else 0,
            'p95': self._percentile(data, 95),
            'p99': self._percentile(data, 99)
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]

class PerformanceTestCase(BaseTestCase):
    """Base class for performance tests"""
    
    def setUp(self):
        super().setUp()
        self.metrics = PerformanceMetrics()
        self.process = psutil.Process()
        
        # Performance test configuration
        self.load_test_duration = 30  # seconds
        self.stress_test_duration = 60  # seconds
        self.concurrent_users = 50
        self.requests_per_second = 100
        
        # Performance thresholds
        self.max_response_time = 1.0  # seconds
        self.min_throughput = 50  # requests per second
        self.max_memory_usage = 500  # MB
        self.max_cpu_usage = 80  # percent
        self.max_error_rate = 5  # percent
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.metrics.start_time = datetime.now()
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_system)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self._monitoring = False
        self.metrics.end_time = datetime.now()
        if hasattr(self, '_monitor_thread'):
            self._monitor_thread.join(timeout=1)
    
    def _monitor_system(self):
        """Monitor system resources"""
        while getattr(self, '_monitoring', False):
            try:
                # Memory usage in MB
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                self.metrics.add_memory_usage(memory_mb)
                
                # CPU usage percentage
                cpu_percent = self.process.cpu_percent()
                self.metrics.add_cpu_usage(cpu_percent)
                
                time.sleep(0.5)  # Monitor every 500ms
            except Exception:
                # Process might have ended
                break
    
    def measure_response_time(self, func: Callable, *args, **kwargs) -> Any:
        """Measure response time of a function call"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
        
        end_time = time.time()
        response_time = end_time - start_time
        self.metrics.add_response_time(response_time)
        
        return result, success, response_time
    
    def run_load_test(self, func: Callable, duration: int, target_rps: int, *args, **kwargs):
        """Run load test with specified RPS for given duration"""
        start_time = time.time()
        end_time = start_time + duration
        request_interval = 1.0 / target_rps
        
        successful_requests = 0
        failed_requests = 0
        
        while time.time() < end_time:
            request_start = time.time()
            
            result, success, response_time = self.measure_response_time(func, *args, **kwargs)
            
            if success:
                successful_requests += 1
            else:
                failed_requests += 1
            
            # Calculate sleep time to maintain target RPS
            elapsed = time.time() - request_start
            sleep_time = max(0, request_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        total_requests = successful_requests + failed_requests
        actual_duration = time.time() - start_time
        actual_rps = total_requests / actual_duration
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        self.metrics.add_throughput_rate(actual_rps)
        self.metrics.add_error_rate(error_rate)
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'actual_rps': actual_rps,
            'error_rate': error_rate,
            'duration': actual_duration
        }
    
    def run_concurrent_test(self, func: Callable, num_threads: int, requests_per_thread: int, *args, **kwargs):
        """Run concurrent test with multiple threads"""
        results = []
        
        def worker():
            thread_results = []
            for _ in range(requests_per_thread):
                result, success, response_time = self.measure_response_time(func, *args, **kwargs)
                thread_results.append((result, success, response_time))
            return thread_results
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            
            for future in as_completed(futures):
                try:
                    thread_results = future.result()
                    results.extend(thread_results)
                except Exception as e:
                    print(f"Thread failed: {e}")
        
        # Calculate statistics
        total_requests = len(results)
        successful_requests = sum(1 for _, success, _ in results if success)
        failed_requests = total_requests - successful_requests
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        self.metrics.add_error_rate(error_rate)
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'error_rate': error_rate
        }
    
    def assert_performance_thresholds(self):
        """Assert that performance meets defined thresholds"""
        summary = self.metrics.get_summary()
        
        # Response time thresholds
        if summary['response_times']['p95'] > 0:
            self.assertLess(
                summary['response_times']['p95'], 
                self.max_response_time,
                f"95th percentile response time ({summary['response_times']['p95']:.3f}s) exceeds threshold ({self.max_response_time}s)"
            )
        
        # Throughput thresholds
        if summary['throughput_rates']['mean'] > 0:
            self.assertGreater(
                summary['throughput_rates']['mean'],
                self.min_throughput,
                f"Average throughput ({summary['throughput_rates']['mean']:.1f} RPS) below threshold ({self.min_throughput} RPS)"
            )
        
        # Memory usage thresholds
        if summary['memory_usage']['max'] > 0:
            self.assertLess(
                summary['memory_usage']['max'],
                self.max_memory_usage,
                f"Peak memory usage ({summary['memory_usage']['max']:.1f} MB) exceeds threshold ({self.max_memory_usage} MB)"
            )
        
        # CPU usage thresholds
        if summary['cpu_usage']['max'] > 0:
            self.assertLess(
                summary['cpu_usage']['max'],
                self.max_cpu_usage,
                f"Peak CPU usage ({summary['cpu_usage']['max']:.1f}%) exceeds threshold ({self.max_cpu_usage}%)"
            )
        
        # Error rate thresholds
        if summary['error_rates']['max'] > 0:
            self.assertLess(
                summary['error_rates']['max'],
                self.max_error_rate,
                f"Peak error rate ({summary['error_rates']['max']:.1f}%) exceeds threshold ({self.max_error_rate}%)"
            )

class TestSchedulerPerformance(PerformanceTestCase):
    """Performance tests for NotificationScheduler"""
    
    def setUp(self):
        super().setUp()
        self.scheduler = NotificationScheduler()
        self.scheduler.start()
    
    def tearDown(self):
        if self.scheduler.is_running:
            self.scheduler.stop()
        super().tearDown()
    
    @with_timeout(120)
    def test_scheduler_load_performance(self):
        """Test scheduler performance under load"""
        self.start_monitoring()
        
        def schedule_reminder():
            return self.scheduler.schedule_reminder(
                appointment_id=f"load_test_{time.time()}_{threading.current_thread().ident}",
                user_id=f"user_{time.time()}",
                scheduled_time=datetime.now() + timedelta(minutes=30),
                message="Load test reminder",
                priority=TaskPriority.MEDIUM
            )
        
        # Run load test
        load_results = self.run_load_test(
            schedule_reminder,
            duration=30,  # 30 seconds
            target_rps=20  # 20 requests per second
        )
        
        self.stop_monitoring()
        
        # Verify load test results
        self.assertGreater(load_results['successful_requests'], 500)  # At least 500 successful requests
        self.assertLess(load_results['error_rate'], 5)  # Less than 5% error rate
        
        # Check performance thresholds
        self.assert_performance_thresholds()
        
        print(f"Scheduler Load Test Results: {load_results}")
        print(f"Performance Summary: {self.metrics.get_summary()}")
    
    @with_timeout(90)
    def test_scheduler_concurrent_performance(self):
        """Test scheduler performance with concurrent requests"""
        self.start_monitoring()
        
        def schedule_reminder():
            return self.scheduler.schedule_reminder(
                appointment_id=f"concurrent_test_{time.time()}_{threading.current_thread().ident}",
                user_id=f"user_{time.time()}",
                scheduled_time=datetime.now() + timedelta(minutes=30),
                message="Concurrent test reminder"
            )
        
        # Run concurrent test
        concurrent_results = self.run_concurrent_test(
            schedule_reminder,
            num_threads=20,
            requests_per_thread=25
        )
        
        self.stop_monitoring()
        
        # Verify concurrent test results
        self.assertGreater(concurrent_results['successful_requests'], 450)  # At least 90% success rate
        self.assertLess(concurrent_results['error_rate'], 10)  # Less than 10% error rate
        
        print(f"Scheduler Concurrent Test Results: {concurrent_results}")
        print(f"Performance Summary: {self.metrics.get_summary()}")
    
    def test_scheduler_memory_usage(self):
        """Test scheduler memory usage with large number of tasks"""
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # Schedule a large number of tasks
        num_tasks = 10000
        for i in range(num_tasks):
            self.scheduler.schedule_reminder(
                appointment_id=f"memory_test_{i}",
                user_id=f"user_{i}",
                scheduled_time=datetime.now() + timedelta(minutes=i % 60),
                message=f"Memory test reminder {i}"
            )
        
        # Force garbage collection
        gc.collect()
        
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 200MB for 10k tasks)
        self.assertLess(memory_increase, 200, f"Memory increase ({memory_increase:.1f} MB) too high for {num_tasks} tasks")
        
        print(f"Memory usage: Initial={initial_memory:.1f}MB, Final={final_memory:.1f}MB, Increase={memory_increase:.1f}MB")

class TestQueueManagerPerformance(PerformanceTestCase):
    """Performance tests for QueueManager"""
    
    def setUp(self):
        super().setUp()
        self.queue_manager = QueueManager()
        self.queue_manager.start()
    
    def tearDown(self):
        if self.queue_manager.is_running:
            self.queue_manager.stop()
        super().tearDown()
    
    @with_timeout(120)
    def test_queue_throughput_performance(self):
        """Test queue manager throughput performance"""
        self.start_monitoring()
        
        def enqueue_message():
            return self.queue_manager.enqueue(
                queue_type=QueueType.EMAIL,
                message={
                    'user_id': f'user_{time.time()}',
                    'message': 'Performance test message',
                    'timestamp': datetime.now().isoformat()
                },
                priority=1
            )
        
        # Run throughput test
        throughput_results = self.run_load_test(
            enqueue_message,
            duration=30,
            target_rps=100  # 100 messages per second
        )
        
        self.stop_monitoring()
        
        # Verify throughput results
        self.assertGreater(throughput_results['successful_requests'], 2500)  # At least 2500 messages
        self.assertLess(throughput_results['error_rate'], 2)  # Less than 2% error rate
        
        print(f"Queue Throughput Test Results: {throughput_results}")
        print(f"Performance Summary: {self.metrics.get_summary()}")
    
    def test_queue_processing_performance(self):
        """Test queue message processing performance"""
        # Mock message processor to avoid actual delivery
        with patch.object(self.queue_manager, '_process_message') as mock_processor:
            mock_processor.return_value = True
            
            start_time = time.time()
            
            # Enqueue a large batch of messages
            num_messages = 1000
            for i in range(num_messages):
                self.queue_manager.enqueue(
                    queue_type=QueueType.SMS,
                    message={'id': i, 'message': f'Test message {i}'},
                    priority=1
                )
            
            # Wait for processing
            time.sleep(10)
            
            processing_time = time.time() - start_time
            processing_rate = num_messages / processing_time
            
            # Should process at least 50 messages per second
            self.assertGreater(processing_rate, 50, f"Processing rate ({processing_rate:.1f} msg/s) too low")
            
            print(f"Queue processing: {num_messages} messages in {processing_time:.2f}s ({processing_rate:.1f} msg/s)")

class TestCachePerformance(PerformanceTestCase):
    """Performance tests for caching components"""
    
    def setUp(self):
        super().setUp()
        self.cache = MemoryCache(CacheConfig(
            strategy=CacheStrategy.LRU,
            max_size=10000,
            ttl_seconds=300
        ))
        self.cache_manager = CacheManager()
    
    @with_timeout(60)
    def test_cache_read_write_performance(self):
        """Test cache read/write performance"""
        self.start_monitoring()
        
        # Test cache writes
        def cache_write():
            key = f"key_{time.time()}_{threading.current_thread().ident}"
            value = f"value_{time.time()}"
            return self.cache.set(key, value)
        
        write_results = self.run_load_test(
            cache_write,
            duration=15,
            target_rps=1000  # 1000 writes per second
        )
        
        # Test cache reads
        def cache_read():
            # Read random existing key
            import random
            key_num = random.randint(0, len(self.cache.cache) - 1) if self.cache.cache else 0
            key = f"key_{key_num}"
            return self.cache.get(key)
        
        read_results = self.run_load_test(
            cache_read,
            duration=15,
            target_rps=2000  # 2000 reads per second
        )
        
        self.stop_monitoring()
        
        # Verify performance
        self.assertGreater(write_results['actual_rps'], 500)  # At least 500 writes/s
        self.assertGreater(read_results['actual_rps'], 1000)  # At least 1000 reads/s
        
        print(f"Cache Write Performance: {write_results}")
        print(f"Cache Read Performance: {read_results}")
        print(f"Performance Summary: {self.metrics.get_summary()}")
    
    def test_cache_eviction_performance(self):
        """Test cache eviction performance under memory pressure"""
        # Fill cache to capacity
        cache_size = 1000
        small_cache = MemoryCache(CacheConfig(
            strategy=CacheStrategy.LRU,
            max_size=cache_size,
            ttl_seconds=300
        ))
        
        start_time = time.time()
        
        # Fill cache
        for i in range(cache_size):
            small_cache.set(f"key_{i}", f"value_{i}")
        
        fill_time = time.time() - start_time
        
        # Test eviction performance
        eviction_start = time.time()
        
        # Add more items to trigger evictions
        for i in range(cache_size, cache_size * 2):
            small_cache.set(f"key_{i}", f"value_{i}")
        
        eviction_time = time.time() - eviction_start
        
        # Verify cache size is maintained
        self.assertEqual(len(small_cache.cache), cache_size)
        
        # Eviction should be reasonably fast
        eviction_rate = cache_size / eviction_time
        self.assertGreater(eviction_rate, 100, f"Eviction rate ({eviction_rate:.1f} ops/s) too slow")
        
        print(f"Cache fill time: {fill_time:.3f}s")
        print(f"Cache eviction time: {eviction_time:.3f}s ({eviction_rate:.1f} ops/s)")

class TestDatabaseOptimizationPerformance(PerformanceTestCase):
    """Performance tests for database optimization"""
    
    def setUp(self):
        super().setUp()
        self.batch_processor = BatchProcessor(batch_size=100, flush_interval_seconds=1)
        self.db_optimizer = DatabaseOptimizer()
    
    def tearDown(self):
        if self.batch_processor.is_running:
            self.batch_processor.stop_processing()
        if self.db_optimizer.is_running:
            self.db_optimizer.stop_optimization()
        super().tearDown()
    
    @with_timeout(60)
    def test_batch_processing_performance(self):
        """Test batch processing performance"""
        self.batch_processor.start_processing()
        self.start_monitoring()
        
        from notifications.database_optimization import BatchOperation, QueryType
        
        def add_batch_operation():
            operation = BatchOperation(
                operation_type=QueryType.INSERT,
                table='test_table',
                data=[{
                    'id': time.time(),
                    'value': f'test_value_{time.time()}',
                    'timestamp': datetime.now().isoformat()
                }]
            )
            return self.batch_processor.add_operation(operation)
        
        # Test batch operation throughput
        batch_results = self.run_load_test(
            add_batch_operation,
            duration=20,
            target_rps=200  # 200 operations per second
        )
        
        self.stop_monitoring()
        
        # Verify batch processing performance
        self.assertGreater(batch_results['successful_requests'], 3000)  # At least 3000 operations
        self.assertLess(batch_results['error_rate'], 1)  # Less than 1% error rate
        
        # Check batch processor statistics
        stats = self.batch_processor.get_statistics()
        self.assertGreater(stats['total_operations'], 3000)
        
        print(f"Batch Processing Performance: {batch_results}")
        print(f"Batch Processor Stats: {stats}")
        print(f"Performance Summary: {self.metrics.get_summary()}")

class TestIntegratedSystemPerformance(PerformanceTestCase):
    """End-to-end performance tests for the complete system"""
    
    def setUp(self):
        super().setUp()
        self.scheduler = NotificationScheduler()
        self.queue_manager = QueueManager()
        self.delivery_manager = FailsafeDeliveryManager()
        
        # Start all services
        self.scheduler.start()
        self.queue_manager.start()
    
    def tearDown(self):
        if self.scheduler.is_running:
            self.scheduler.stop()
        if self.queue_manager.is_running:
            self.queue_manager.stop()
        super().tearDown()
    
    @with_timeout(180)
    def test_end_to_end_performance(self):
        """Test complete notification flow performance"""
        self.start_monitoring()
        
        # Mock delivery providers for testing
        with patch.object(self.delivery_manager, 'email_provider') as mock_email:
            mock_email.send.return_value = True
            
            def complete_notification_flow():
                # Schedule a notification
                appointment_id = f"e2e_test_{time.time()}_{threading.current_thread().ident}"
                success = self.scheduler.schedule_reminder(
                    appointment_id=appointment_id,
                    user_id=f"user_{time.time()}",
                    scheduled_time=datetime.now() + timedelta(seconds=1),
                    message="End-to-end test notification"
                )
                return success
            
            # Run end-to-end performance test
            e2e_results = self.run_load_test(
                complete_notification_flow,
                duration=60,  # 1 minute
                target_rps=10  # 10 complete flows per second
            )
            
            self.stop_monitoring()
            
            # Verify end-to-end performance
            self.assertGreater(e2e_results['successful_requests'], 500)  # At least 500 complete flows
            self.assertLess(e2e_results['error_rate'], 5)  # Less than 5% error rate
            
            # Check system-wide performance
            self.assert_performance_thresholds()
            
            print(f"End-to-End Performance: {e2e_results}")
            print(f"Performance Summary: {self.metrics.get_summary()}")
    
    @with_timeout(300)
    def test_stress_test(self):
        """Stress test the complete system"""
        self.start_monitoring()
        
        # Mock all delivery providers
        with patch.object(self.delivery_manager, 'email_provider') as mock_email, \
             patch.object(self.delivery_manager, 'sms_provider') as mock_sms:
            
            mock_email.send.return_value = True
            mock_sms.send.return_value = True
            
            def stress_test_operation():
                # Mix of different operations
                import random
                operation_type = random.choice(['schedule', 'queue', 'delivery'])
                
                if operation_type == 'schedule':
                    return self.scheduler.schedule_reminder(
                        appointment_id=f"stress_{time.time()}_{threading.current_thread().ident}",
                        user_id=f"user_{time.time()}",
                        scheduled_time=datetime.now() + timedelta(minutes=random.randint(1, 60)),
                        message="Stress test notification"
                    )
                elif operation_type == 'queue':
                    return self.queue_manager.enqueue(
                        queue_type=random.choice(list(QueueType)),
                        message={'stress_test': True, 'timestamp': time.time()},
                        priority=random.randint(1, 5)
                    )
                else:
                    # Delivery operation
                    return self.delivery_manager.deliver_notification(
                        notification={'message': 'Stress test', 'user_id': f'user_{time.time()}'},
                        preferred_methods=['email']
                    )
            
            # Run stress test
            stress_results = self.run_concurrent_test(
                stress_test_operation,
                num_threads=50,  # 50 concurrent threads
                requests_per_thread=100  # 100 operations per thread
            )
            
            self.stop_monitoring()
            
            # Verify stress test results
            self.assertGreater(stress_results['successful_requests'], 4000)  # At least 80% success rate
            self.assertLess(stress_results['error_rate'], 20)  # Less than 20% error rate under stress
            
            print(f"Stress Test Results: {stress_results}")
            print(f"Performance Summary: {self.metrics.get_summary()}")
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during extended operation"""
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # Run operations for extended period
        for cycle in range(10):
            # Schedule many notifications
            for i in range(100):
                self.scheduler.schedule_reminder(
                    appointment_id=f"leak_test_{cycle}_{i}",
                    user_id=f"user_{cycle}_{i}",
                    scheduled_time=datetime.now() + timedelta(minutes=i),
                    message=f"Leak test notification {cycle}_{i}"
                )
            
            # Enqueue many messages
            for i in range(100):
                self.queue_manager.enqueue(
                    queue_type=QueueType.EMAIL,
                    message={'cycle': cycle, 'index': i, 'data': 'x' * 1000},  # 1KB message
                    priority=1
                )
            
            # Force garbage collection
            gc.collect()
            
            # Check memory usage
            current_memory = self.process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory
            
            print(f"Cycle {cycle}: Memory usage = {current_memory:.1f}MB (increase: {memory_increase:.1f}MB)")
            
            # Memory increase should be reasonable (less than 100MB per 1000 operations)
            if cycle > 2:  # Allow some initial memory allocation
                self.assertLess(
                    memory_increase, 
                    100 * (cycle + 1),  # 100MB per cycle
                    f"Potential memory leak detected: {memory_increase:.1f}MB increase after {cycle + 1} cycles"
                )
        
        final_memory = self.process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"Memory leak test: Initial={initial_memory:.1f}MB, Final={final_memory:.1f}MB, Total increase={total_increase:.1f}MB")

if __name__ == '__main__':
    # Run performance tests
    unittest.main(verbosity=2)