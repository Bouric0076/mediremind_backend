#!/usr/bin/env python3
"""
Test Dead Letter Queue functionality
"""

import os
import sys
import django
import uuid
from datetime import datetime, timedelta
from django.db.models import Q

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.utils import timezone
from notifications.models import ScheduledTask, NotificationLog
from notifications.dead_letter_queue import DeadLetterQueue, DeadLetterQueueManager, EnhancedRetryMixin

def test_dead_letter_queue_creation():
    """Test creating dead letter queue entries"""
    print("=== Testing Dead Letter Queue Creation ===")
    
    # Create a test scheduled task
    task = ScheduledTask.objects.create(
        task_type='reminder',
        appointment_id=uuid.uuid4(),
        delivery_method='email',
        scheduled_time=timezone.now() + timedelta(hours=1),
        status='failed',
        retry_count=3,
        max_retries=3,
        error_message='Maximum retries exceeded',
        message_data={
            'patient_id': 'test_patient_123',
            'provider_id': 'test_provider_456',
            'appointment_time': '2024-01-15T10:00:00Z',
            'message': 'Appointment reminder'
        }
    )
    
    # Create a notification log entry for the failed task
    NotificationLog.objects.create(
        task_id=task.id,
        appointment_id=task.appointment_id,
        patient_id='test_patient_123',
        provider_id='test_provider_456',
        delivery_method='email',
        status='failed',
        error_message='Maximum retries exceeded',
        metadata=task.message_data
    )
    
    # Add to dead letter queue
    dlq_entry = DeadLetterQueueManager.add_to_dead_letter_queue(
        task, 
        'Maximum retries exceeded after 3 attempts', 
        'max_retries_exceeded'
    )
    
    if dlq_entry:
        print(f"✅ Created DLQ entry: {dlq_entry.id}")
        print(f"   Original task ID: {dlq_entry.original_task_id}")
        print(f"   Failure type: {dlq_entry.failure_type}")
        print(f"   Status: {dlq_entry.status}")
        return True
    else:
        print("❌ Failed to create DLQ entry")
        return False

def test_dead_letter_queue_statistics():
    """Test DLQ statistics"""
    print("\n=== Testing Dead Letter Queue Statistics ===")
    
    try:
        stats = DeadLetterQueueManager.get_statistics()
        print("📊 DLQ Statistics:")
        print(f"   Total entries: {stats['total_entries']}")
        print(f"   Pending review: {stats['pending_review_count']}")
        print(f"   Retry candidates: {stats['retry_candidates_count']}")
        
        print("   Status breakdown:")
        for status, count in stats['status_counts'].items():
            if count > 0:
                print(f"     {status}: {count}")
        
        print("   Failure type breakdown:")
        for failure_type, count in stats['failure_type_counts'].items():
            if count > 0:
                print(f"     {failure_type}: {count}")
        
        return True
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        return False

def test_retry_candidates():
    """Test getting retry candidates"""
    print("\n=== Testing Retry Candidates ===")
    
    try:
        candidates = DeadLetterQueueManager.get_retry_candidates()
        print(f"📋 Found {candidates.count()} retry candidates")
        
        for candidate in candidates[:3]:  # Show first 3
            print(f"   Candidate {candidate.id}:")
            print(f"     Failure type: {candidate.failure_type}")
            print(f"     Can retry: {candidate.can_be_retried()}")
            suggestion = candidate.get_retry_suggestion()
            print(f"     Suggestion: {suggestion['suggestion']}")
            print(f"     Priority: {suggestion['priority']}")
        
        return True
    except Exception as e:
        print(f"❌ Error getting retry candidates: {e}")
        return False

def test_retry_logic():
    """Test enhanced retry logic"""
    print("\n=== Testing Enhanced Retry Logic ===")
    
    # Create a task that should retry
    task = ScheduledTask.objects.create(
        task_type='reminder',
        appointment_id=uuid.uuid4(),
        delivery_method='email',
        scheduled_time=timezone.now() + timedelta(hours=1),
        status='failed',
        retry_count=1,
        max_retries=3,
        error_message='Temporary failure',
        message_data={'test': 'data'}
    )
    
    # Test should_retry
    should_retry = task.should_retry()
    print(f"✅ Task should retry: {should_retry}")
    
    # Test retry_with_backoff
    retry_success = task.retry_with_backoff()
    print(f"✅ Retry with backoff successful: {retry_success}")
    
    # Refresh task from database
    task.refresh_from_db()
    print(f"   New retry count: {task.retry_count}")
    print(f"   New status: {task.status}")
    print(f"   New scheduled time: {task.scheduled_time}")
    
    return should_retry and retry_success

def test_max_retries_handling():
    """Test handling when max retries are exceeded"""
    print("\n=== Testing Max Retries Handling ===")
    
    # Create a task that has exceeded max retries
    task = ScheduledTask.objects.create(
        task_type='reminder',
        appointment_id=uuid.uuid4(),
        delivery_method='email',
        scheduled_time=timezone.now() + timedelta(hours=1),
        status='failed',
        retry_count=3,
        max_retries=3,
        error_message='Maximum retries exceeded',
        message_data={'test': 'data'}
    )
    
    # Handle failure with dead letter queue
    task.handle_failure('Maximum retries exceeded', 'max_retries_exceeded')
    
    # Refresh task from database
    task.refresh_from_db()
    print(f"✅ Task status after max retries: {task.status}")
    
    # Check if DLQ entry was created
    try:
        dlq_entry = DeadLetterQueue.objects.get(original_task_id=task.id)
        print(f"✅ DLQ entry created: {dlq_entry.id}")
        print(f"   Failure type: {dlq_entry.failure_type}")
        print(f"   Status: {dlq_entry.status}")
        return task.status == 'cancelled' and dlq_entry is not None
    except DeadLetterQueue.DoesNotExist:
        print("❌ No DLQ entry found")
        return False

def test_dlq_review_functionality():
    """Test DLQ review functionality"""
    print("\n=== Testing DLQ Review Functionality ===")
    
    # Get a DLQ entry
    dlq_entry = DeadLetterQueue.objects.first()
    if not dlq_entry:
        print("❌ No DLQ entries found")
        return False
    
    # Test mark as reviewed
    dlq_entry.mark_as_reviewed(
        reviewed_by='test_user@example.com',
        resolution_notes='Test resolution',
        resolution_data={'test': 'resolution_data'}
    )
    
    dlq_entry.refresh_from_db()
    print(f"✅ Entry marked as reviewed")
    print(f"   Status: {dlq_entry.status}")
    print(f"   Reviewed by: {dlq_entry.reviewed_by}")
    print(f"   Resolution notes: {dlq_entry.resolution_notes}")
    
    # Test archive
    dlq_entry.archive()
    dlq_entry.refresh_from_db()
    print(f"✅ Entry archived, status: {dlq_entry.status}")
    
    return dlq_entry.status == 'archived'

def test_permanent_failure_handling():
    """Test handling of permanent failures"""
    print("\n=== Testing Permanent Failure Handling ===")
    
    # Create a task with permanent failure
    task = ScheduledTask.objects.create(
        task_type='reminder',
        appointment_id=uuid.uuid4(),
        delivery_method='email',
        scheduled_time=timezone.now() + timedelta(hours=1),
        status='failed',
        retry_count=1,
        max_retries=3,
        error_message='Invalid email address',
        message_data={'email': 'invalid-email-format'}
    )
    
    # Set retry count to max to trigger DLQ
    task.retry_count = task.max_retries
    task.save()
    
    # Handle failure as permanent failure
    task.handle_failure('Invalid email address format', 'invalid_recipient')
    
    # Check DLQ entry
    try:
        dlq_entry = DeadLetterQueue.objects.get(original_task_id=task.id)
        print(f"✅ Permanent failure DLQ entry created: {dlq_entry.id}")
        print(f"   Failure type: {dlq_entry.failure_type}")
        
        # Check if it can be retried
        can_retry = dlq_entry.can_be_retried()
        print(f"   Can be retried: {can_retry}")
        
        suggestion = dlq_entry.get_retry_suggestion()
        print(f"   Suggestion: {suggestion['suggestion']}")
        print(f"   Can retry (from suggestion): {suggestion['can_retry']}")
        
        return dlq_entry.failure_type == 'invalid_recipient' and not can_retry and not suggestion['can_retry']
        
    except DeadLetterQueue.DoesNotExist:
        print("❌ No DLQ entry found for permanent failure")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning Up Test Data ===")
    
    try:
        # Delete test DLQ entries
        DeadLetterQueue.objects.filter(
            Q(original_task_id__isnull=False) |
            Q(patient_id__startswith='test_')
        ).delete()
        
        # Delete test tasks
        ScheduledTask.objects.filter(
            message_data__has_key='test'
        ).delete()
        
        print("✅ Test data cleaned up")
        return True
    except Exception as e:
        print(f"❌ Error cleaning up test data: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Dead Letter Queue Tests")
    print("=" * 50)
    
    tests = [
        ("DLQ Creation", test_dead_letter_queue_creation),
        ("DLQ Statistics", test_dead_letter_queue_statistics),
        ("Retry Candidates", test_retry_candidates),
        ("Retry Logic", test_retry_logic),
        ("Max Retries Handling", test_max_retries_handling),
        ("DLQ Review Functionality", test_dlq_review_functionality),
        ("Permanent Failure Handling", test_permanent_failure_handling),
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
        print("🎉 All tests passed! Dead Letter Queue is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)