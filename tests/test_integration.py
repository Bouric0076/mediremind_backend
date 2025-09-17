import unittest
import time
import threading
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, List, Any, Optional
import json
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_config import BaseTestCase, TestDataFactory, with_timeout
from notifications.scheduler import NotificationScheduler, ScheduledTask, TaskPriority, TaskStatus
from notifications.queue_manager import QueueManager, QueueType, QueueStatus
from notifications.background_tasks import BackgroundTaskManager, TaskType
from notifications.failsafe import FailsafeDeliveryManager, DeliveryStatus, DeliveryMethod
from notifications.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerManager
from notifications.error_recovery import ErrorRecoveryManager, ErrorSeverity, RecoveryAction
from notifications.performance import PerformanceManager
from notifications.cache_layer import CacheManager
from notifications.database_optimization import DatabaseOptimizer
from notifications.logging_config import NotificationLogger
from notifications.monitoring import SystemMonitor, AlertManager

class IntegrationTestCase(BaseTestCase):
    """Base class for integration tests"""
    
    def setUp(self):
        super().setUp()
        
        # Initialize all system components
        self.scheduler = NotificationScheduler()
        self.queue_manager = QueueManager()
        self.background_task_manager = BackgroundTaskManager()
        self.delivery_manager = FailsafeDeliveryManager()
        self.circuit_breaker_manager = CircuitBreakerManager()
        self.error_recovery_manager = ErrorRecoveryManager()
        self.performance_manager = PerformanceManager()
        self.cache_manager = CacheManager()
        self.db_optimizer = DatabaseOptimizer()
        self.logger = NotificationLogger()
        self.system_monitor = SystemMonitor()
        self.alert_manager = AlertManager()
        
        # Track started services for cleanup
        self.started_services = []
    
    def tearDown(self):
        """Clean up all started services"""
        # Stop all services in reverse order
        for service in reversed(self.started_services):
            try:
                if hasattr(service, 'stop') and hasattr(service, 'is_running'):
                    if service.is_running:
                        service.stop()
                elif hasattr(service, 'stop_monitoring'):
                    service.stop_monitoring()
                elif hasattr(service, 'stop_optimization'):
                    service.stop_optimization()
            except Exception as e:
                print(f"Error stopping service {service}: {e}")
        
        super().tearDown()
    
    def start_service(self, service):
        """Start a service and track it for cleanup"""
        if hasattr(service, 'start'):
            service.start()
        elif hasattr(service, 'start_monitoring'):
            service.start_monitoring()
        elif hasattr(service, 'start_optimization'):
            service.start_optimization()
        
        self.started_services.append(service)
        return service
    
    def wait_for_processing(self, timeout: float = 5.0):
        """Wait for background processing to complete"""
        time.sleep(timeout)

class TestSchedulerQueueIntegration(IntegrationTestCase):
    """Test integration between scheduler and queue manager"""
    
    def test_scheduler_to_queue_flow(self):
        """Test notification flow from scheduler to queue"""
        # Start services
        self.start_service(self.scheduler)
        self.start_service(self.queue_manager)
        
        # Mock queue processing to capture messages
        processed_messages = []
        
        def mock_process_message(queue_type, message):
            processed_messages.append((queue_type, message))
            return True
        
        with patch.object(self.queue_manager, '_process_message', side_effect=mock_process_message):
            # Schedule a notification
            success = self.scheduler.schedule_reminder(
                appointment_id="integration_test_1",
                user_id="user_123",
                scheduled_time=datetime.now() + timedelta(seconds=1),
                message="Integration test reminder",
                priority=TaskPriority.HIGH
            )
            
            self.assertTrue(success)
            
            # Wait for processing
            self.wait_for_processing(3)
            
            # Verify message was processed
            self.assertGreater(len(processed_messages), 0)
            
            # Verify message content
            queue_type, message = processed_messages[0]
            self.assertIn('appointment_id', message)
            self.assertEqual(message['appointment_id'], "integration_test_1")
    
    def test_queue_priority_handling(self):
        """Test that queue manager respects message priorities"""
        self.start_service(self.queue_manager)
        
        processed_order = []
        
        def mock_process_message(queue_type, message):
            processed_order.append(message.get('priority', 'unknown'))
            return True
        
        with patch.object(self.queue_manager, '_process_message', side_effect=mock_process_message):
            # Enqueue messages with different priorities
            self.queue_manager.enqueue(
                queue_type=QueueType.EMAIL,
                message={'id': 'low', 'priority': 'low'},
                priority=3
            )
            
            self.queue_manager.enqueue(
                queue_type=QueueType.EMAIL,
                message={'id': 'high', 'priority': 'high'},
                priority=1
            )
            
            self.queue_manager.enqueue(
                queue_type=QueueType.EMAIL,
                message={'id': 'medium', 'priority': 'medium'},
                priority=2
            )
            
            # Wait for processing
            self.wait_for_processing(2)
            
            # Verify high priority was processed first
            self.assertGreater(len(processed_order), 0)
            self.assertEqual(processed_order[0], 'high')
    
    def test_scheduler_queue_error_handling(self):
        """Test error handling between scheduler and queue"""
        self.start_service(self.scheduler)
        self.start_service(self.queue_manager)
        
        # Mock queue to fail initially
        call_count = 0
        
        def mock_enqueue(queue_type, message, priority):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Queue temporarily unavailable")
            return True
        
        with patch.object(self.queue_manager, 'enqueue', side_effect=mock_enqueue):
            # Schedule a notification
            success = self.scheduler.schedule_reminder(
                appointment_id="error_test_1",
                user_id="user_123",
                scheduled_time=datetime.now() + timedelta(seconds=1),
                message="Error handling test"
            )
            
            # Should handle the error gracefully
            self.assertTrue(success)
            
            # Wait for retry attempts
            self.wait_for_processing(5)
            
            # Verify retry attempts were made
            self.assertGreaterEqual(call_count, 2)

class TestFailsafeDeliveryIntegration(IntegrationTestCase):
    """Test integration of failsafe delivery mechanisms"""
    
    def test_delivery_fallback_chain(self):
        """Test delivery fallback from SMS to Email to Push"""
        # Mock all delivery providers
        with patch.object(self.delivery_manager, 'sms_provider') as mock_sms, \
             patch.object(self.delivery_manager, 'email_provider') as mock_email, \
             patch.object(self.delivery_manager, 'push_provider') as mock_push:
            
            # Configure SMS to fail, Email to succeed
            mock_sms.send.return_value = False
            mock_email.send.return_value = True
            mock_push.send.return_value = True
            
            # Attempt delivery with fallback chain
            notification = {
                'user_id': 'user_123',
                'message': 'Fallback test notification',
                'appointment_id': 'appt_456'
            }
            
            success = self.delivery_manager.deliver_notification(
                notification=notification,
                preferred_methods=[DeliveryMethod.SMS, DeliveryMethod.EMAIL, DeliveryMethod.PUSH]
            )
            
            self.assertTrue(success)
            
            # Verify fallback sequence
            mock_sms.send.assert_called_once()
            mock_email.send.assert_called_once()
            # Push should not be called since email succeeded
            mock_push.send.assert_not_called()
    
    def test_delivery_retry_mechanism(self):
        """Test delivery retry mechanism with exponential backoff"""
        with patch.object(self.delivery_manager, 'email_provider') as mock_email:
            # Configure to fail twice, then succeed
            mock_email.send.side_effect = [False, False, True]
            
            notification = {
                'user_id': 'user_123',
                'message': 'Retry test notification',
                'appointment_id': 'appt_789'
            }
            
            start_time = time.time()
            
            success = self.delivery_manager.deliver_notification(
                notification=notification,
                preferred_methods=[DeliveryMethod.EMAIL],
                max_retries=3
            )
            
            end_time = time.time()
            
            self.assertTrue(success)
            
            # Verify retry attempts
            self.assertEqual(mock_email.send.call_count, 3)
            
            # Verify exponential backoff (should take some time)
            self.assertGreater(end_time - start_time, 1)  # At least 1 second for backoff
    
    def test_delivery_status_tracking(self):
        """Test delivery status tracking and logging"""
        with patch.object(self.delivery_manager, 'email_provider') as mock_email:
            mock_email.send.return_value = True
            
            notification = {
                'user_id': 'user_123',
                'message': 'Status tracking test',
                'appointment_id': 'appt_status'
            }
            
            # Schedule delivery
            task_id = self.delivery_manager.schedule_delivery(
                notification=notification,
                delivery_time=datetime.now(),
                preferred_methods=[DeliveryMethod.EMAIL]
            )
            
            self.assertIsNotNone(task_id)
            
            # Wait for delivery
            self.wait_for_processing(2)
            
            # Check delivery status
            status = self.delivery_manager.get_task_status(task_id)
            self.assertIsNotNone(status)
            
            # Verify database logging
            self.assert_supabase_called_with('insert', 'delivery_attempts')

class TestCircuitBreakerIntegration(IntegrationTestCase):
    """Test circuit breaker integration with services"""
    
    def test_circuit_breaker_protection(self):
        """Test circuit breaker protecting services from failures"""
        # Get circuit breaker for email service
        email_circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker('email_service')
        
        # Mock email provider to fail
        with patch.object(self.delivery_manager, 'email_provider') as mock_email:
            mock_email.send.side_effect = Exception("Email service down")
            
            # Attempt multiple deliveries to trigger circuit breaker
            for i in range(5):
                try:
                    self.delivery_manager.deliver_notification(
                        notification={'user_id': f'user_{i}', 'message': f'Test {i}'},
                        preferred_methods=[DeliveryMethod.EMAIL]
                    )
                except Exception:
                    pass
            
            # Circuit breaker should be open
            self.assertEqual(email_circuit_breaker.state, CircuitState.OPEN)
            
            # Further calls should be rejected quickly
            start_time = time.time()
            try:
                self.delivery_manager.deliver_notification(
                    notification={'user_id': 'user_test', 'message': 'Should be rejected'},
                    preferred_methods=[DeliveryMethod.EMAIL]
                )
            except Exception:
                pass
            end_time = time.time()
            
            # Should fail quickly (circuit breaker rejection)
            self.assertLess(end_time - start_time, 0.1)
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after service restoration"""
        email_circuit_breaker = self.circuit_breaker_manager.get_circuit_breaker('email_service')
        
        with patch.object(self.delivery_manager, 'email_provider') as mock_email:
            # First, trigger circuit breaker to open
            mock_email.send.side_effect = Exception("Service down")
            
            for i in range(3):
                try:
                    email_circuit_breaker.call(lambda: mock_email.send('test', 'test', 'test'))
                except Exception:
                    pass
            
            self.assertEqual(email_circuit_breaker.state, CircuitState.OPEN)
            
            # Wait for circuit breaker timeout
            time.sleep(6)  # Default timeout is 5 seconds
            
            # Service is restored
            mock_email.send.side_effect = None
            mock_email.send.return_value = True
            
            # Circuit breaker should transition to half-open
            self.assertEqual(email_circuit_breaker.state, CircuitState.HALF_OPEN)
            
            # Successful calls should close the circuit
            for i in range(2):
                email_circuit_breaker.call(lambda: mock_email.send('test', 'test', 'test'))
            
            self.assertEqual(email_circuit_breaker.state, CircuitState.CLOSED)

class TestErrorRecoveryIntegration(IntegrationTestCase):
    """Test error recovery mechanisms across the system"""
    
    def test_automatic_error_recovery(self):
        """Test automatic error recovery strategies"""
        self.start_service(self.scheduler)
        
        # Mock database to fail initially
        call_count = 0
        
        def mock_database_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Database connection failed")
            return Mock(data=[{'id': 'recovered'}])
        
        with patch.object(self.mock_supabase, 'table') as mock_table:
            mock_table.return_value.insert.return_value.execute.side_effect = mock_database_call
            
            # Schedule a reminder (should trigger error recovery)
            success = self.scheduler.schedule_reminder(
                appointment_id="recovery_test",
                user_id="user_123",
                scheduled_time=datetime.now() + timedelta(minutes=30),
                message="Error recovery test"
            )
            
            # Should eventually succeed after recovery
            self.assertTrue(success)
            
            # Verify retry attempts were made
            self.assertGreaterEqual(call_count, 2)
    
    def test_error_escalation(self):
        """Test error escalation to administrators"""
        # Mock alert manager
        with patch.object(self.alert_manager, 'trigger_alert') as mock_alert:
            # Simulate critical error
            self.error_recovery_manager.handle_error(
                error=Exception("Critical system failure"),
                context={
                    'component': 'scheduler',
                    'operation': 'schedule_reminder',
                    'severity': ErrorSeverity.CRITICAL
                }
            )
            
            # Verify alert was triggered
            mock_alert.assert_called()
            
            # Verify alert details
            call_args = mock_alert.call_args[1]
            self.assertEqual(call_args['severity'], 'critical')
            self.assertIn('scheduler', call_args['message'])
    
    def test_graceful_degradation(self):
        """Test graceful degradation when services are unavailable"""
        self.start_service(self.scheduler)
        
        # Mock queue manager to be unavailable
        with patch.object(self.queue_manager, 'enqueue') as mock_enqueue:
            mock_enqueue.side_effect = Exception("Queue service unavailable")
            
            # Schedule a reminder
            success = self.scheduler.schedule_reminder(
                appointment_id="degradation_test",
                user_id="user_123",
                scheduled_time=datetime.now() + timedelta(minutes=30),
                message="Graceful degradation test"
            )
            
            # Should handle gracefully (might store locally or use fallback)
            # The exact behavior depends on implementation
            self.assertIsNotNone(success)  # Should not crash

class TestPerformanceIntegration(IntegrationTestCase):
    """Test performance optimization integration"""
    
    def test_cache_integration(self):
        """Test cache integration across components"""
        self.start_service(self.cache_manager)
        
        # Test cache usage in scheduler
        with patch.object(self.scheduler, '_get_user_preferences') as mock_get_prefs:
            mock_get_prefs.return_value = {'email': True, 'sms': False}
            
            # First call should hit the database
            prefs1 = self.scheduler._get_user_preferences('user_123')
            
            # Second call should hit the cache
            prefs2 = self.scheduler._get_user_preferences('user_123')
            
            self.assertEqual(prefs1, prefs2)
            
            # Database should only be called once
            self.assertEqual(mock_get_prefs.call_count, 1)
    
    def test_database_optimization_integration(self):
        """Test database optimization integration"""
        self.start_service(self.db_optimizer)
        
        # Mock batch processor
        with patch.object(self.db_optimizer.batch_processor, 'add_operation') as mock_add_op:
            # Perform multiple database operations
            for i in range(10):
                self.scheduler.schedule_reminder(
                    appointment_id=f"batch_test_{i}",
                    user_id=f"user_{i}",
                    scheduled_time=datetime.now() + timedelta(minutes=i),
                    message=f"Batch test {i}"
                )
            
            # Verify operations were batched
            self.assertGreater(mock_add_op.call_count, 0)
    
    def test_performance_monitoring_integration(self):
        """Test performance monitoring across all components"""
        self.start_service(self.performance_manager)
        self.start_service(self.system_monitor)
        
        # Perform various operations
        self.start_service(self.scheduler)
        self.start_service(self.queue_manager)
        
        # Schedule multiple reminders
        for i in range(5):
            self.scheduler.schedule_reminder(
                appointment_id=f"perf_test_{i}",
                user_id=f"user_{i}",
                scheduled_time=datetime.now() + timedelta(minutes=i),
                message=f"Performance test {i}"
            )
        
        # Enqueue multiple messages
        for i in range(5):
            self.queue_manager.enqueue(
                queue_type=QueueType.EMAIL,
                message={'test': f'performance_{i}'},
                priority=1
            )
        
        # Wait for processing
        self.wait_for_processing(3)
        
        # Check performance metrics
        metrics = self.performance_manager.get_performance_report()
        self.assertIsNotNone(metrics)
        self.assertIn('scheduler', metrics)
        self.assertIn('queue_manager', metrics)

class TestEndToEndWorkflows(IntegrationTestCase):
    """Test complete end-to-end workflows"""
    
    @with_timeout(30)
    def test_complete_notification_workflow(self):
        """Test complete notification workflow from scheduling to delivery"""
        # Start all necessary services
        self.start_service(self.scheduler)
        self.start_service(self.queue_manager)
        self.start_service(self.background_task_manager)
        
        # Mock delivery providers
        with patch.object(self.delivery_manager, 'email_provider') as mock_email, \
             patch.object(self.delivery_manager, 'sms_provider') as mock_sms:
            
            mock_email.send.return_value = True
            mock_sms.send.return_value = True
            
            # Create test data
            user_data = TestDataFactory.create_test_user()
            appointment_data = TestDataFactory.create_test_appointment()
            
            # Schedule a reminder
            success = self.scheduler.schedule_reminder(
                appointment_id=appointment_data['id'],
                user_id=user_data['id'],
                scheduled_time=datetime.now() + timedelta(seconds=2),
                message=f"Reminder: Appointment with {appointment_data['doctor_name']} at {appointment_data['appointment_time']}",
                priority=TaskPriority.HIGH
            )
            
            self.assertTrue(success)
            
            # Wait for complete processing
            self.wait_for_processing(5)
            
            # Verify the workflow completed
            # Check that database operations occurred
            self.assert_supabase_called_with('insert', 'scheduled_reminders')
            
            # Verify delivery was attempted
            self.assertTrue(mock_email.send.called or mock_sms.send.called)
    
    def test_appointment_reminder_lifecycle(self):
        """Test complete appointment reminder lifecycle"""
        self.start_service(self.scheduler)
        self.start_service(self.queue_manager)
        self.start_service(self.background_task_manager)
        
        # Mock delivery
        with patch.object(self.delivery_manager, 'email_provider') as mock_email:
            mock_email.send.return_value = True
            
            appointment_time = datetime.now() + timedelta(hours=24)
            
            # Schedule multiple reminders for the same appointment
            reminder_times = [
                appointment_time - timedelta(hours=24),  # 24 hours before
                appointment_time - timedelta(hours=2),   # 2 hours before
                appointment_time - timedelta(minutes=30) # 30 minutes before
            ]
            
            scheduled_reminders = []
            for i, reminder_time in enumerate(reminder_times):
                success = self.scheduler.schedule_reminder(
                    appointment_id="lifecycle_test_appt",
                    user_id="lifecycle_test_user",
                    scheduled_time=reminder_time,
                    message=f"Reminder {i+1}: Your appointment is coming up",
                    priority=TaskPriority.MEDIUM
                )
                scheduled_reminders.append(success)
            
            # All reminders should be scheduled successfully
            self.assertTrue(all(scheduled_reminders))
            
            # Verify reminders are stored
            self.assertGreaterEqual(len(self.scheduler.scheduled_tasks), 3)
            
            # Test cancellation of all reminders for the appointment
            cancel_success = self.scheduler.cancel_task("lifecycle_test_appt")
            self.assertTrue(cancel_success)
            
            # Verify reminders were cancelled
            remaining_tasks = [
                task for task in self.scheduler.scheduled_tasks 
                if task.appointment_id == "lifecycle_test_appt"
            ]
            self.assertEqual(len(remaining_tasks), 0)
    
    def test_system_resilience_workflow(self):
        """Test system resilience under various failure conditions"""
        self.start_service(self.scheduler)
        self.start_service(self.queue_manager)
        
        # Test database failure resilience
        with patch.object(self.mock_supabase, 'table') as mock_table:
            # Simulate intermittent database failures
            call_count = 0
            
            def intermittent_failure(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 3 == 0:  # Fail every 3rd call
                    raise Exception("Database temporarily unavailable")
                return Mock(data=[{'id': f'success_{call_count}'}])
            
            mock_table.return_value.insert.return_value.execute.side_effect = intermittent_failure
            
            # Schedule multiple reminders
            successful_schedules = 0
            for i in range(10):
                try:
                    success = self.scheduler.schedule_reminder(
                        appointment_id=f"resilience_test_{i}",
                        user_id=f"user_{i}",
                        scheduled_time=datetime.now() + timedelta(minutes=i),
                        message=f"Resilience test {i}"
                    )
                    if success:
                        successful_schedules += 1
                except Exception:
                    pass
            
            # Should have some successful schedules despite failures
            self.assertGreater(successful_schedules, 5)
    
    def test_high_load_workflow(self):
        """Test system behavior under high load"""
        self.start_service(self.scheduler)
        self.start_service(self.queue_manager)
        
        # Mock delivery to avoid actual sending
        with patch.object(self.delivery_manager, 'email_provider') as mock_email:
            mock_email.send.return_value = True
            
            # Schedule a large number of reminders rapidly
            start_time = time.time()
            scheduled_count = 0
            
            for i in range(100):
                try:
                    success = self.scheduler.schedule_reminder(
                        appointment_id=f"load_test_{i}",
                        user_id=f"user_{i % 20}",  # 20 different users
                        scheduled_time=datetime.now() + timedelta(seconds=i % 60),
                        message=f"Load test reminder {i}",
                        priority=TaskPriority.MEDIUM
                    )
                    if success:
                        scheduled_count += 1
                except Exception as e:
                    print(f"Failed to schedule reminder {i}: {e}")
            
            end_time = time.time()
            
            # Verify performance
            total_time = end_time - start_time
            self.assertLess(total_time, 10)  # Should complete within 10 seconds
            self.assertGreater(scheduled_count, 80)  # At least 80% success rate
            
            # Wait for processing
            self.wait_for_processing(5)
            
            # Verify queue processed messages
            queue_metrics = self.queue_manager.get_metrics()
            self.assertGreater(queue_metrics.get('total_messages', 0), 0)

class TestSystemHealthIntegration(IntegrationTestCase):
    """Test system health monitoring and alerting integration"""
    
    def test_health_check_integration(self):
        """Test health checks across all components"""
        # Start monitoring
        self.start_service(self.system_monitor)
        
        # Start services to monitor
        self.start_service(self.scheduler)
        self.start_service(self.queue_manager)
        
        # Wait for health checks
        self.wait_for_processing(2)
        
        # Get health status
        health_status = self.system_monitor.get_health_status()
        
        self.assertIsNotNone(health_status)
        self.assertIn('scheduler', health_status)
        self.assertIn('queue_manager', health_status)
        
        # All services should be healthy
        for service, status in health_status.items():
            self.assertEqual(status.get('status'), 'healthy')
    
    def test_alert_integration(self):
        """Test alert system integration"""
        # Mock alert handlers
        with patch.object(self.alert_manager, '_send_email_alert') as mock_email_alert, \
             patch.object(self.alert_manager, '_send_sms_alert') as mock_sms_alert:
            
            # Trigger a critical alert
            self.alert_manager.trigger_alert(
                alert_type='system_failure',
                severity='critical',
                message='Test critical system failure',
                component='scheduler'
            )
            
            # Verify alerts were sent
            mock_email_alert.assert_called()
            mock_sms_alert.assert_called()
    
    def test_performance_alert_integration(self):
        """Test performance-based alerting"""
        self.start_service(self.system_monitor)
        
        # Mock performance metrics to trigger alerts
        with patch.object(self.system_monitor, 'get_system_metrics') as mock_metrics:
            mock_metrics.return_value = {
                'cpu_usage': 95.0,  # High CPU usage
                'memory_usage': 90.0,  # High memory usage
                'disk_usage': 85.0,
                'response_time': 2.5  # Slow response time
            }
            
            # Check for performance alerts
            alerts = self.alert_manager.check_performance_thresholds(
                self.system_monitor.get_system_metrics()
            )
            
            # Should trigger alerts for high resource usage
            self.assertGreater(len(alerts), 0)
            
            # Verify alert types
            alert_types = [alert['type'] for alert in alerts]
            self.assertIn('high_cpu_usage', alert_types)
            self.assertIn('high_memory_usage', alert_types)

if __name__ == '__main__':
    # Run integration tests
    unittest.main(verbosity=2)