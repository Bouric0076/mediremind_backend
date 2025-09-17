import unittest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
import json
import threading

# Import the modules we're testing
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notifications.scheduler import NotificationScheduler, ScheduledTask, TaskPriority, TaskStatus
from notifications.queue_manager import QueueManager, NotificationQueue, QueueType
from notifications.background_tasks import BackgroundTaskManager, TaskType
from notifications.failsafe import FailsafeDeliveryManager, DeliveryStatus, DeliveryMethod
from notifications.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenException
from notifications.error_recovery import ErrorRecoveryManager, ErrorSeverity, RecoveryAction
from notifications.performance import QueryOptimizer, MemoryCache, CacheStrategy, CacheConfig
from notifications.cache_layer import CacheManager, MultiLevelCache
from notifications.database_optimization import DatabaseOptimizer, BatchProcessor, QueryType

class TestNotificationScheduler(unittest.TestCase):
    """Test cases for NotificationScheduler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scheduler = NotificationScheduler()
        self.test_task = ScheduledTask(
            task_id="test_task_1",
            appointment_id="appt_123",
            user_id="user_456",
            scheduled_time=datetime.now() + timedelta(minutes=30),
            message="Test reminder message",
            priority=TaskPriority.MEDIUM
        )
    
    def tearDown(self):
        """Clean up after tests"""
        if self.scheduler.is_running:
            self.scheduler.stop()
    
    def test_scheduler_start_stop(self):
        """Test scheduler start and stop functionality"""
        # Test starting
        self.assertFalse(self.scheduler.is_running)
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running)
        
        # Test stopping
        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running)
    
    def test_schedule_task(self):
        """Test scheduling a task"""
        self.scheduler.start()
        
        # Schedule a task
        success = self.scheduler.schedule_reminder(
            appointment_id=self.test_task.appointment_id,
            user_id=self.test_task.user_id,
            scheduled_time=self.test_task.scheduled_time,
            message=self.test_task.message,
            priority=self.test_task.priority
        )
        
        self.assertTrue(success)
        self.assertGreater(len(self.scheduler.scheduled_tasks), 0)
    
    def test_cancel_task(self):
        """Test canceling a scheduled task"""
        self.scheduler.start()
        
        # Schedule and then cancel a task
        self.scheduler.schedule_reminder(
            appointment_id=self.test_task.appointment_id,
            user_id=self.test_task.user_id,
            scheduled_time=self.test_task.scheduled_time,
            message=self.test_task.message
        )
        
        initial_count = len(self.scheduler.scheduled_tasks)
        success = self.scheduler.cancel_task(self.test_task.appointment_id)
        
        self.assertTrue(success)
        self.assertLess(len(self.scheduler.scheduled_tasks), initial_count)
    
    def test_task_priority_handling(self):
        """Test that tasks are processed according to priority"""
        self.scheduler.start()
        
        # Schedule tasks with different priorities
        high_priority_task = self.scheduler.schedule_reminder(
            appointment_id="high_priority",
            user_id="user_1",
            scheduled_time=datetime.now() + timedelta(seconds=1),
            message="High priority",
            priority=TaskPriority.HIGH
        )
        
        low_priority_task = self.scheduler.schedule_reminder(
            appointment_id="low_priority",
            user_id="user_2",
            scheduled_time=datetime.now() + timedelta(seconds=1),
            message="Low priority",
            priority=TaskPriority.LOW
        )
        
        # Wait for processing
        time.sleep(2)
        
        # Verify tasks were scheduled
        self.assertTrue(high_priority_task)
        self.assertTrue(low_priority_task)
    
    @patch('notifications.scheduler.supabase')
    def test_database_integration(self, mock_supabase):
        """Test database integration for task persistence"""
        # Mock database responses
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock(data=[{'id': 'task_1'}])
        mock_supabase.table.return_value.select.return_value.execute.return_value = Mock(data=[])
        
        self.scheduler.start()
        
        # Schedule a task
        success = self.scheduler.schedule_reminder(
            appointment_id=self.test_task.appointment_id,
            user_id=self.test_task.user_id,
            scheduled_time=self.test_task.scheduled_time,
            message=self.test_task.message
        )
        
        self.assertTrue(success)
        # Verify database was called
        mock_supabase.table.assert_called()

class TestQueueManager(unittest.TestCase):
    """Test cases for QueueManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.queue_manager = QueueManager()
        self.test_message = {
            'user_id': 'user_123',
            'message': 'Test notification',
            'type': 'reminder'
        }
    
    def tearDown(self):
        """Clean up after tests"""
        if self.queue_manager.is_running:
            self.queue_manager.stop()
    
    def test_queue_manager_start_stop(self):
        """Test queue manager start and stop"""
        self.assertFalse(self.queue_manager.is_running)
        self.queue_manager.start()
        self.assertTrue(self.queue_manager.is_running)
        
        self.queue_manager.stop()
        self.assertFalse(self.queue_manager.is_running)
    
    def test_enqueue_message(self):
        """Test enqueueing messages"""
        self.queue_manager.start()
        
        # Enqueue a message
        success = self.queue_manager.enqueue(
            queue_type=QueueType.EMAIL,
            message=self.test_message,
            priority=1
        )
        
        self.assertTrue(success)
        
        # Check queue has the message
        email_queue = self.queue_manager.queues.get(QueueType.EMAIL)
        self.assertIsNotNone(email_queue)
        self.assertGreater(email_queue.queue.qsize(), 0)
    
    def test_queue_processing(self):
        """Test queue message processing"""
        self.queue_manager.start()
        
        # Mock message processor
        with patch.object(self.queue_manager, '_process_message') as mock_processor:
            mock_processor.return_value = True
            
            # Enqueue and process message
            self.queue_manager.enqueue(
                queue_type=QueueType.SMS,
                message=self.test_message,
                priority=1
            )
            
            # Wait for processing
            time.sleep(1)
            
            # Verify processor was called
            mock_processor.assert_called()
    
    def test_queue_metrics(self):
        """Test queue metrics collection"""
        self.queue_manager.start()
        
        # Enqueue some messages
        for i in range(5):
            self.queue_manager.enqueue(
                queue_type=QueueType.PUSH,
                message={'id': i, 'message': f'Test {i}'},
                priority=1
            )
        
        # Get metrics
        metrics = self.queue_manager.get_metrics()
        
        self.assertIn('total_queues', metrics)
        self.assertIn('total_messages', metrics)
        self.assertGreater(metrics['total_messages'], 0)

class TestFailsafeDelivery(unittest.TestCase):
    """Test cases for FailsafeDeliveryManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.delivery_manager = FailsafeDeliveryManager()
        self.test_notification = {
            'user_id': 'user_123',
            'message': 'Test notification',
            'type': 'reminder',
            'appointment_id': 'appt_456'
        }
    
    def test_delivery_attempt(self):
        """Test delivery attempt with fallback"""
        # Mock providers
        with patch.object(self.delivery_manager, 'sms_provider') as mock_sms, \
             patch.object(self.delivery_manager, 'email_provider') as mock_email:
            
            # Configure SMS to fail, email to succeed
            mock_sms.send.return_value = False
            mock_email.send.return_value = True
            
            # Attempt delivery
            success = self.delivery_manager.deliver_notification(
                notification=self.test_notification,
                preferred_methods=[DeliveryMethod.SMS, DeliveryMethod.EMAIL]
            )
            
            self.assertTrue(success)
            # Verify both providers were called
            mock_sms.send.assert_called_once()
            mock_email.send.assert_called_once()
    
    def test_retry_mechanism(self):
        """Test retry mechanism for failed deliveries"""
        with patch.object(self.delivery_manager, 'sms_provider') as mock_sms:
            # Configure to fail initially, then succeed
            mock_sms.send.side_effect = [False, False, True]
            
            # Attempt delivery with retries
            success = self.delivery_manager.deliver_notification(
                notification=self.test_notification,
                preferred_methods=[DeliveryMethod.SMS],
                max_retries=3
            )
            
            self.assertTrue(success)
            # Verify retry attempts
            self.assertEqual(mock_sms.send.call_count, 3)
    
    def test_delivery_status_tracking(self):
        """Test delivery status tracking"""
        with patch.object(self.delivery_manager, 'email_provider') as mock_email:
            mock_email.send.return_value = True
            
            # Deliver notification
            task_id = self.delivery_manager.schedule_delivery(
                notification=self.test_notification,
                delivery_time=datetime.now(),
                preferred_methods=[DeliveryMethod.EMAIL]
            )
            
            self.assertIsNotNone(task_id)
            
            # Check task status
            status = self.delivery_manager.get_task_status(task_id)
            self.assertIsNotNone(status)

class TestCircuitBreaker(unittest.TestCase):
    """Test cases for CircuitBreaker"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.circuit_breaker = CircuitBreaker(
            name="test_service",
            failure_threshold=3,
            timeout_seconds=5,
            success_threshold=2
        )
    
    def test_circuit_breaker_states(self):
        """Test circuit breaker state transitions"""
        # Initially closed
        self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)
        
        # Simulate failures to open circuit
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        self.assertEqual(self.circuit_breaker.state, CircuitState.OPEN)
        
        # Test that calls are rejected when open
        with self.assertRaises(CircuitBreakerOpenException):
            self.circuit_breaker.call(lambda: "test")
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery to closed state"""
        # Open the circuit
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        # Wait for timeout
        time.sleep(6)
        
        # Should be in half-open state
        self.assertEqual(self.circuit_breaker.state, CircuitState.HALF_OPEN)
        
        # Record successes to close circuit
        for _ in range(2):
            self.circuit_breaker.record_success()
        
        self.assertEqual(self.circuit_breaker.state, CircuitState.CLOSED)
    
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator functionality"""
        @self.circuit_breaker.protect
        def test_function():
            return "success"
        
        # Should work normally when closed
        result = test_function()
        self.assertEqual(result, "success")
        
        # Open circuit by recording failures
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        # Should raise exception when open
        with self.assertRaises(CircuitBreakerOpenException):
            test_function()

class TestPerformanceOptimization(unittest.TestCase):
    """Test cases for performance optimization components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cache = MemoryCache(CacheConfig(
            strategy=CacheStrategy.LRU,
            max_size=100,
            ttl_seconds=300
        ))
        self.query_optimizer = QueryOptimizer()
    
    def test_memory_cache_operations(self):
        """Test memory cache basic operations"""
        # Test set and get
        self.assertTrue(self.cache.set("key1", "value1"))
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # Test cache miss
        self.assertIsNone(self.cache.get("nonexistent"))
        
        # Test delete
        self.assertTrue(self.cache.delete("key1"))
        self.assertIsNone(self.cache.get("key1"))
    
    def test_cache_eviction(self):
        """Test cache eviction policies"""
        # Fill cache to capacity
        for i in range(100):
            self.cache.set(f"key{i}", f"value{i}")
        
        # Add one more item to trigger eviction
        self.cache.set("overflow", "overflow_value")
        
        # Verify cache size is maintained
        self.assertEqual(len(self.cache.cache), 100)
        
        # Verify eviction occurred
        self.assertGreater(self.cache.evictions, 0)
    
    def test_cache_statistics(self):
        """Test cache statistics collection"""
        # Perform some operations
        self.cache.set("test", "value")
        self.cache.get("test")  # Hit
        self.cache.get("missing")  # Miss
        
        stats = self.cache.get_statistics()
        
        self.assertIn('hits', stats)
        self.assertIn('misses', stats)
        self.assertIn('hit_rate_percent', stats)
        self.assertGreater(stats['hits'], 0)
        self.assertGreater(stats['misses'], 0)
    
    @patch('notifications.performance.supabase')
    def test_query_optimization(self, mock_supabase):
        """Test query optimization"""
        # Mock database response
        mock_result = Mock()
        mock_result.data = [{'id': 1, 'name': 'test'}]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_result
        
        # Execute optimized query
        result = self.query_optimizer.execute_query(
            table='appointments',
            query_params={'status': 'scheduled'}
        )
        
        self.assertIsNotNone(result)
        self.assertIn('data', result)

class TestDatabaseOptimization(unittest.TestCase):
    """Test cases for database optimization"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.batch_processor = BatchProcessor(batch_size=5, flush_interval_seconds=1)
        self.db_optimizer = DatabaseOptimizer()
    
    def tearDown(self):
        """Clean up after tests"""
        if self.batch_processor.is_running:
            self.batch_processor.stop_processing()
        if self.db_optimizer.is_running:
            self.db_optimizer.stop_optimization()
    
    def test_batch_processing(self):
        """Test batch processing functionality"""
        self.batch_processor.start_processing()
        
        # Add operations to batch
        from notifications.database_optimization import BatchOperation
        
        for i in range(3):
            operation = BatchOperation(
                operation_type=QueryType.INSERT,
                table='test_table',
                data=[{'id': i, 'value': f'test{i}'}]
            )
            self.batch_processor.add_operation(operation)
        
        # Verify operations were added
        stats = self.batch_processor.get_statistics()
        self.assertGreater(stats['total_operations'], 0)
    
    def test_batch_flush(self):
        """Test batch flushing"""
        self.batch_processor.start_processing()
        
        # Add operations
        from notifications.database_optimization import BatchOperation
        
        operation = BatchOperation(
            operation_type=QueryType.INSERT,
            table='test_table',
            data=[{'id': 1, 'value': 'test'}]
        )
        self.batch_processor.add_operation(operation)
        
        # Force flush
        self.batch_processor.flush_all_batches()
        
        # Verify flush occurred
        stats = self.batch_processor.get_statistics()
        self.assertGreater(stats['flush_count'], 0)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete notification system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.scheduler = NotificationScheduler()
        self.queue_manager = QueueManager()
        self.delivery_manager = FailsafeDeliveryManager()
    
    def tearDown(self):
        """Clean up integration test environment"""
        if self.scheduler.is_running:
            self.scheduler.stop()
        if self.queue_manager.is_running:
            self.queue_manager.stop()
    
    def test_end_to_end_notification_flow(self):
        """Test complete notification flow from scheduling to delivery"""
        # Start all services
        self.scheduler.start()
        self.queue_manager.start()
        
        # Mock delivery providers
        with patch.object(self.delivery_manager, 'email_provider') as mock_email:
            mock_email.send.return_value = True
            
            # Schedule a notification
            success = self.scheduler.schedule_reminder(
                appointment_id="integration_test",
                user_id="user_123",
                scheduled_time=datetime.now() + timedelta(seconds=1),
                message="Integration test reminder"
            )
            
            self.assertTrue(success)
            
            # Wait for processing
            time.sleep(3)
            
            # Verify the notification was processed
            # (In a real test, we'd check the database or delivery logs)
    
    def test_system_resilience(self):
        """Test system resilience under failure conditions"""
        self.scheduler.start()
        self.queue_manager.start()
        
        # Simulate various failure scenarios
        with patch('notifications.scheduler.supabase') as mock_db:
            # Simulate database failure
            mock_db.table.side_effect = Exception("Database connection failed")
            
            # System should handle the failure gracefully
            success = self.scheduler.schedule_reminder(
                appointment_id="resilience_test",
                user_id="user_123",
                scheduled_time=datetime.now() + timedelta(minutes=1),
                message="Resilience test"
            )
            
            # Should fail gracefully without crashing
            self.assertFalse(success)
    
    def test_performance_under_load(self):
        """Test system performance under high load"""
        self.scheduler.start()
        self.queue_manager.start()
        
        start_time = time.time()
        
        # Schedule multiple notifications rapidly
        for i in range(100):
            self.scheduler.schedule_reminder(
                appointment_id=f"load_test_{i}",
                user_id=f"user_{i}",
                scheduled_time=datetime.now() + timedelta(minutes=i),
                message=f"Load test reminder {i}"
            )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(processing_time, 10.0)  # 10 seconds
        
        # Verify all tasks were scheduled
        self.assertGreaterEqual(len(self.scheduler.scheduled_tasks), 100)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and recovery mechanisms"""
    
    def test_scheduler_error_recovery(self):
        """Test scheduler recovery from errors"""
        scheduler = NotificationScheduler()
        scheduler.start()
        
        # Simulate an error in task processing
        with patch.object(scheduler, '_process_due_tasks') as mock_process:
            mock_process.side_effect = Exception("Processing error")
            
            # Scheduler should continue running despite errors
            time.sleep(2)
            self.assertTrue(scheduler.is_running)
        
        scheduler.stop()
    
    def test_queue_error_handling(self):
        """Test queue manager error handling"""
        queue_manager = QueueManager()
        queue_manager.start()
        
        # Simulate message processing error
        with patch.object(queue_manager, '_process_message') as mock_process:
            mock_process.side_effect = Exception("Message processing error")
            
            # Enqueue a message
            queue_manager.enqueue(
                queue_type=QueueType.EMAIL,
                message={'test': 'error_handling'},
                priority=1
            )
            
            # Wait for processing attempt
            time.sleep(1)
            
            # Queue should still be running
            self.assertTrue(queue_manager.is_running)
        
        queue_manager.stop()

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestNotificationScheduler,
        TestQueueManager,
        TestFailsafeDelivery,
        TestCircuitBreaker,
        TestPerformanceOptimization,
        TestDatabaseOptimization,
        TestIntegration,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    sys.exit(exit_code)