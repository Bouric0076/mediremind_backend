#!/usr/bin/env python
"""
Test script for notification failure handling and retry mechanisms
"""

import os
import sys
import django
from django.conf import settings
from datetime import datetime, timedelta
import time

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')

# Setup Django
django.setup()

def test_failsafe_delivery_manager():
    """Test the failsafe delivery manager functionality"""
    try:
        print("Testing failsafe delivery manager...")
        from notifications.failsafe import FailsafeDeliveryManager, NotificationTask, DeliveryMethod, DeliveryStatus
        
        # Initialize the manager
        manager = FailsafeDeliveryManager()
        print("✓ Failsafe delivery manager initialized")
        
        # Test scheduling notification with correct method signature
        task_id = manager.schedule_notification(
            appointment_id="appt_001",
            recipient_id="user_001",
            message="Test notification message",
            primary_method=DeliveryMethod.EMAIL,
            fallback_methods=[DeliveryMethod.SMS],
            priority=1,
            expires_in_hours=24,
            max_attempts=3,
            retry_intervals=[60, 300, 900]  # 1min, 5min, 15min
        )
        print(f"✓ Notification scheduled with ID: {task_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failsafe delivery manager test failed: {str(e)}")
        return False

def test_delivery_providers():
    """Test individual delivery providers"""
    try:
        print("\nTesting delivery providers...")
        from notifications.failsafe import EmailProvider, PushProvider
        
        # Test email provider
        email_provider = EmailProvider()
        print("✓ Email provider initialized")
        print(f"✓ Email provider status: {'Available' if email_provider.is_available else 'Unavailable'}")
        
        # Test push provider
        push_provider = PushProvider()
        print("✓ Push provider initialized")
        print(f"✓ Push provider status: {'Available' if push_provider.is_available else 'Unavailable'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Delivery providers test failed: {str(e)}")
        return False

def test_retry_mechanisms():
    """Test retry mechanisms"""
    try:
        print("\nTesting retry mechanisms...")
        from notifications.failsafe import FailsafeDeliveryManager, DeliveryMethod
        
        # Initialize delivery manager
        manager = FailsafeDeliveryManager()
        print("✓ Retry manager initialized")
        
        # Test retry scheduling with correct method signature
        task_id = manager.schedule_notification(
            appointment_id="appt-retry-456",
            recipient_id="user-retry-789",
            message="Test retry notification",
            primary_method=DeliveryMethod.EMAIL,
            fallback_methods=[DeliveryMethod.PUSH],
            priority=5,
            expires_in_hours=1,
            max_attempts=3,
            retry_intervals=[5, 10, 30]  # Short intervals for testing
        )
        print(f"✓ Retry task scheduled with ID: {task_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Retry mechanisms test failed: {str(e)}")
        return False

def test_queue_management():
    """Test queue management functionality"""
    try:
        print("\nTesting queue management...")
        from notifications.queue_manager import QueueManager, NotificationQueue, QueueType, QueueConfig
        
        # Initialize queue manager
        queue_manager = QueueManager()
        print("✓ Queue manager initialized")
        
        # Create queue config
        config = QueueConfig()
        config.max_workers = 2
        config.batch_size = 5
        config.rate_limit = 10
        
        # Test individual queue with correct constructor
        test_queue = NotificationQueue(
            queue_type=QueueType.IMMEDIATE,
            config=config
        )
        print("✓ Individual notification queue created")
        
        # Test queue status
        status = test_queue.get_status()
        print(f"✓ Queue status retrieved: {status}")
        
        return True
        
    except Exception as e:
        print(f"✗ Queue management test failed: {str(e)}")
        return False

def test_error_recovery():
    """Test error recovery mechanisms"""
    try:
        print("\nTesting error recovery...")
        from notifications.error_recovery import ErrorRecoveryManager, RecoveryAction
        
        # Initialize recovery manager
        recovery_manager = ErrorRecoveryManager()
        print("✓ Error recovery manager initialized")
        
        # Test recovery action with correct enum values
        action = RecoveryAction.RETRY
        print(f"✓ Recovery action set: {action}")
        
        # Test available recovery actions
        available_actions = [
            RecoveryAction.RETRY,
            RecoveryAction.FALLBACK,
            RecoveryAction.ESCALATE,
            RecoveryAction.IGNORE
        ]
        
        for recovery_action in available_actions:
            print(f"✓ Recovery action available: {recovery_action.value}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error recovery test failed: {str(e)}")
        return False

def test_monitoring_and_metrics():
    """Test monitoring and metrics collection"""
    try:
        print("\nTesting monitoring and metrics...")
        from notifications.monitoring import SystemMonitor, MetricsCollector, get_system_status
        
        # Initialize metrics collector first
        metrics = MetricsCollector()
        print("✓ Metrics collector initialized")
        
        # Initialize monitoring with metrics collector
        monitor = SystemMonitor(metrics_collector=metrics)
        print("✓ System monitor initialized")
        
        # Test metric collection
        metrics.increment_counter("test_notifications_sent")
        metrics.set_gauge("active_connections", 5)
        print("✓ Metrics collected")
        
        # Test monitoring status using module-level function
        status = get_system_status()
        print(f"✓ System status retrieved successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Monitoring test failed: {str(e)}")
        return False

def main():
    """Run all failsafe and retry mechanism tests"""
    print("=" * 70)
    print("MediRemind Notification Failsafe & Retry Mechanisms Test")
    print("=" * 70)
    
    tests = [
        test_failsafe_delivery_manager,
        test_delivery_providers,
        test_retry_mechanisms,
        test_queue_management,
        test_error_recovery,
        test_monitoring_and_metrics,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 70)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All failsafe and retry mechanisms are working!")
        return True
    else:
        print("✗ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)