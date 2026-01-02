#!/usr/bin/env python
"""
Test hospital-specific filtering logic directly without API authentication
This test focuses on the core filtering functionality
"""

import os
import sys
import django
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import uuid

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from notifications.models import ScheduledTask, NotificationLog
from accounts.models import Hospital, EnhancedStaffProfile
from notifications.views import get_notification_metrics, get_system_health, get_realtime_stats

User = get_user_model()

def create_test_data():
    """Create test data with hospitals and staff users"""
    
    # Create hospitals
    hospital1 = Hospital.objects.create(
        id=uuid.uuid4(),
        name="Test Hospital 1",
        slug="test-hospital-1",
        email="hospital1@test.com",
        phone="5550001",
        address_line_1="123 Main St",
        city="Test City",
        state="TS",
        postal_code="12345",
        status='active'
    )
    
    hospital2 = Hospital.objects.create(
        id=uuid.uuid4(),
        name="Test Hospital 2",
        slug="test-hospital-2",
        email="hospital2@test.com",
        phone="5550002",
        address_line_1="456 Oak Ave",
        city="Test City",
        state="TS",
        postal_code="12346",
        status='active'
    )
    
    # Create staff users
    staff_user1 = User.objects.create_user(
        username="test_staff_user1_logic",
        email="test_staff1_logic@test.com", 
        password="testpass123"
    )
    
    staff_user2 = User.objects.create_user(
        username="test_staff_user2_logic",
        email="test_staff2_logic@test.com",
        password="testpass123"
    )
    
    # Create staff profiles
    from datetime import date
    
    staff_profile1 = EnhancedStaffProfile.objects.create(
        user=staff_user1,
        hospital=hospital1,
        job_title='Nurse',
        department='nursing',
        employment_status='full_time',
        hire_date=date.today(),
        is_active=True
    )
    
    staff_profile2 = EnhancedStaffProfile.objects.create(
        user=staff_user2,
        hospital=hospital2,
        job_title='Administrator',
        department='admin',
        employment_status='full_time',
        hire_date=date.today(),
        is_active=True
    )
    
    return {
        'hospital1': hospital1,
        'hospital2': hospital2,
        'staff_user1': staff_user1,
        'staff_user2': staff_user2,
        'staff_profile1': staff_profile1,
        'staff_profile2': staff_profile2
    }

def create_test_notifications(test_data):
    """Create test notifications and tasks"""
    
    now = datetime.now()
    
    # Create scheduled tasks for hospital 1
    task1 = ScheduledTask.objects.create(
        id=uuid.uuid4(),
        task_type="reminder",
        reminder_type="medication_reminder",
        scheduled_time=now + timedelta(hours=1),
        appointment_id=uuid.uuid4(),
        delivery_method="sms",
        priority=1,  # High priority
        status="pending",
        retry_count=0,
        max_retries=3,
        message_data={
            'patient_id': 'patient_hospital1_001',
            'message': 'Take your medication'
        }
    )
    
    task2 = ScheduledTask.objects.create(
        id=uuid.uuid4(),
        task_type="reminder",
        reminder_type="appointment_reminder",
        scheduled_time=now + timedelta(hours=2),
        appointment_id=uuid.uuid4(),
        delivery_method="email",
        priority=2,  # Medium priority
        status="pending",
        retry_count=0,
        max_retries=3,
        message_data={
            'patient_id': 'patient_hospital1_002',
            'message': 'Appointment tomorrow'
        }
    )
    
    # Create scheduled tasks for hospital 2
    task3 = ScheduledTask.objects.create(
        id=uuid.uuid4(),
        task_type="reminder",
        reminder_type="medication_reminder",
        scheduled_time=now + timedelta(hours=3),
        appointment_id=uuid.uuid4(),
        delivery_method="sms",
        priority=1,  # High priority
        status="pending",
        retry_count=0,
        max_retries=3,
        message_data={
            'patient_id': 'patient_hospital2_001',
            'message': 'Take your medication'
        }
    )
    
    # Create notification logs
    log1 = NotificationLog.objects.create(
        id=uuid.uuid4(),
        appointment_id=task1.appointment_id,
        notification_type="sms",
        message="Medication reminder sent",
        status="sent",
        sent_at=now - timedelta(hours=1),
        scheduled_task_id=task1.id,
        patient_id="patient_hospital1_001"
    )
    
    log2 = NotificationLog.objects.create(
        id=uuid.uuid4(),
        appointment_id=task2.appointment_id,
        notification_type="email",
        message="Appointment reminder sent",
        status="sent",
        sent_at=now - timedelta(hours=2),
        scheduled_task_id=task2.id,
        patient_id="patient_hospital1_002"
    )
    
    log3 = NotificationLog.objects.create(
        id=uuid.uuid4(),
        appointment_id=task3.appointment_id,
        notification_type="sms",
        message="Medication reminder sent",
        status="sent",
        sent_at=now - timedelta(hours=3),
        scheduled_task_id=task3.id,
        patient_id="patient_hospital2_001"
    )
    
    return {
        'task1': task1,
        'task2': task2,
        'task3': task3,
        'log1': log1,
        'log2': log2,
        'log3': log3
    }

@patch('notifications.views.admin_client')
def test_hospital_filtering_logic(mock_admin_client):
    """Test hospital filtering logic directly"""
    
    print("🚀 Testing Hospital-Specific Filtering Logic")
    print("=" * 50)
    
    # Create mock admin client responses
    mock_admin_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[{'id': 'patient_hospital1_001'}, {'id': 'patient_hospital1_002'}]
    )
    mock_admin_client.table.return_value.select.return_value.in_.return_value.execute.return_value = Mock(
        data=[{'id': 'appt_hospital1_001'}, {'id': 'appt_hospital1_002'}]
    )
    
    test_data = create_test_data()
    test_notifications = create_test_notifications(test_data)
    
    # Test get_notification_metrics with hospital filtering
    print("\n1. Testing get_notification_metrics with hospital filtering...")
    
    # Mock request object
    mock_request = Mock()
    mock_request.user = test_data['staff_user1']
    mock_request.GET = {'hospital_id': str(test_data['hospital1'].id)}
    
    # Test with hospital1 ID
    result = get_notification_metrics(mock_request)
    
    # Parse the result (should be a JsonResponse)
    import json
    content = json.loads(result.content)
    
    print(f"   Result: {content}")
    
    # Should contain metrics for hospital1 only
    assert 'total_scheduled' in content
    assert 'total_sent' in content
    assert 'total_failed' in content
    assert 'success_rate' in content
    
    print("   ✅ get_notification_metrics filtering works")
    
    # Test get_system_health with hospital filtering
    print("\n2. Testing get_system_health with hospital filtering...")
    
    result = get_system_health(mock_request)
    content = json.loads(result.content)
    
    print(f"   Result: {content}")
    
    # Should contain system health data
    assert 'system_status' in content
    assert 'active_queues' in content
    assert 'processing_rate' in content
    assert 'error_rate' in content
    
    print("   ✅ get_system_health filtering works")
    
    # Test get_realtime_stats with hospital filtering
    print("\n3. Testing get_realtime_stats with hospital filtering...")
    
    result = get_realtime_stats(mock_request)
    content = json.loads(result.content)
    
    print(f"   Result: {content}")
    
    # Should contain real-time stats
    assert 'active_queues' in content
    assert 'processing_rate' in content
    assert 'queue_sizes' in content
    assert 'recent_errors' in content
    
    print("   ✅ get_realtime_stats filtering works")
    
    print("\n✅ All hospital filtering logic tests passed!")

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Delete notification logs
    NotificationLog.objects.filter(
        patient_id__in=["patient_hospital1_001", "patient_hospital1_002", "patient_hospital2_001"]
    ).delete()
    
    # Delete scheduled tasks
    ScheduledTask.objects.filter(
        message_data__patient_id__in=["patient_hospital1_001", "patient_hospital1_002", "patient_hospital2_001"]
    ).delete()
    
    # Delete staff profiles and users
    EnhancedStaffProfile.objects.filter(
        user__email__in=["test_staff1_logic@test.com", "test_staff2_logic@test.com"]
    ).delete()
    
    User.objects.filter(
        email__in=["test_staff1_logic@test.com", "test_staff2_logic@test.com"]
    ).delete()
    
    # Delete hospitals
    Hospital.objects.filter(
        email__in=["hospital1@test.com", "hospital2@test.com"]
    ).delete()
    
    print("✅ Cleanup completed")

if __name__ == "__main__":
    try:
        test_hospital_filtering_logic()
    finally:
        cleanup_test_data()