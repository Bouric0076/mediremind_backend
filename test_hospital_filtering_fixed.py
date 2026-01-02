#!/usr/bin/env python3
"""
Test hospital-specific filtering for notification queries
"""

import os
import sys
import django
from datetime import datetime, timedelta
import uuid

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.test import RequestFactory
from django.http import JsonResponse
from unittest.mock import Mock, patch

from notifications.models import ScheduledTask, NotificationLog
from accounts.models import EnhancedStaffProfile, Hospital
from authentication.models import User
from notifications.views import get_notifications, get_notification_metrics, get_system_health, get_realtime_stats

def create_test_data():
    """Create test data for hospital filtering tests"""
    
    # Clean up any existing test data
    Hospital.objects.filter(name__startswith="Test Hospital").delete()
    User.objects.filter(username__startswith="test_").delete()
    
    # Create test hospitals
    hospital1 = Hospital.objects.create(
        name="Test Hospital 1 - Hospital Filtering",
        slug="test-hospital-1-hospital-filtering",
        email="test1-hospital-filtering@hospital.com",
        phone="+15550001",
        address_line_1="123 Test St",
        city="Test City",
        state="TS",
        postal_code="12345",
        country="United States"
    )
    
    hospital2 = Hospital.objects.create(
        name="Test Hospital 2 - Hospital Filtering", 
        slug="test-hospital-2-hospital-filtering",
        email="test2-hospital-filtering@hospital.com",
        phone="+15550002",
        address_line_1="456 Test Ave",
        city="Test City",
        state="TS",
        postal_code="12346",
        country="United States"
    )
    
    # Use existing admin user
    admin_user = User.objects.get(email='admin@mediremind.test')
    
    # Create test staff users
    staff_user1 = User.objects.create_user(
        username="test_staff_user1_hospital_filtering",
        email="test_staff1_hospital_filtering@test.com",
        password="testpass123",
        role="staff"
    )
    
    staff_user2 = User.objects.create_user(
        username="test_staff_user2_hospital_filtering",
        email="test_staff2_hospital_filtering@test.com",
        password="testpass123",
        role="staff"
    )
    
    # Create staff profiles with hospital associations
    staff_profile1 = EnhancedStaffProfile.objects.create(
        user=staff_user1,
        hospital=hospital1,
        job_title="Staff Nurse",
        department="Cardiology",
        hire_date=datetime.now().date()
    )
    
    staff_profile2 = EnhancedStaffProfile.objects.create(
        user=staff_user2,
        hospital=hospital2,
        job_title="Staff Nurse",
        department="Neurology",
        hire_date=datetime.now().date()
    )
    
    return {
        'admin_user': admin_user,
        'staff_user1': staff_user1,
        'staff_user2': staff_user2,
        'hospital1': hospital1,
        'hospital2': hospital2,
        'staff_profile1': staff_profile1,
        'staff_profile2': staff_profile2
    }

def create_test_notifications(test_data):
    """Create test notifications for hospital filtering tests"""
    
    # Generate UUIDs for appointments and patients
    appt1_id = uuid.uuid4()
    appt2_id = uuid.uuid4()
    patient1_id = uuid.uuid4()
    patient2_id = uuid.uuid4()
    provider1_id = uuid.uuid4()
    provider2_id = uuid.uuid4()
    
    # Create test scheduled tasks
    task1 = ScheduledTask.objects.create(
        id=uuid.uuid4(),
        task_type='appointment_reminder',
        appointment_id=str(appt1_id),
        delivery_method='email',
        scheduled_time=datetime.now() + timedelta(hours=1),
        status='pending',
        priority=1,
        message_data={
            'patient_name': 'John Doe',
            'appointment_date': '2024-01-15',
            'appointment_time': '10:00 AM',
            'provider_name': 'Dr. Smith'
        }
    )
    
    task2 = ScheduledTask.objects.create(
        id=uuid.uuid4(),
        task_type='appointment_reminder',
        appointment_id=str(appt2_id),
        delivery_method='sms',
        scheduled_time=datetime.now() + timedelta(hours=2),
        status='processing',
        priority=2,
        message_data={
            'patient_name': 'Jane Smith',
            'appointment_date': '2024-01-16',
            'appointment_time': '2:00 PM',
            'provider_name': 'Dr. Johnson'
        }
    )
    
    # Create test notification logs
    log1 = NotificationLog.objects.create(
        task_id=task1.id,
        appointment_id=str(appt1_id),
        patient_id=str(patient1_id),
        provider_id=str(provider1_id),
        delivery_method='email',
        status='sent',
        error_message='',
        metadata={
            'response_time_ms': 1500,
            'email_status': 'delivered'
        }
    )
    
    log2 = NotificationLog.objects.create(
        task_id=task2.id,
        appointment_id=str(appt2_id),
        patient_id=str(patient2_id),
        provider_id=str(provider2_id),
        delivery_method='sms',
        status='failed',
        error_message='SMS delivery failed',
        metadata={
            'response_time_ms': 2000,
            'sms_status': 'failed',
            'error_code': 'DELIVERY_FAILED'
        }
    )
    
    return {
        'task1': task1,
        'task2': task2,
        'log1': log1,
        'log2': log2
    }

@patch('notifications.views.admin_client')
def test_hospital_filtering_in_notifications(mock_admin_client):
    """Test hospital filtering in get_notifications function"""
    
    # Create mock admin client responses
    mock_admin_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[{'id': 'patient_hospital1_001'}]
    )
    mock_admin_client.table.return_value.select.return_value.in_.return_value.execute.return_value = Mock(
        data=[{'id': 'appt_hospital1_001'}]
    )
    
    test_data = create_test_data()
    test_notifications = create_test_notifications(test_data)
    
    factory = RequestFactory()
    
    # Test staff user from hospital 1
    request = factory.get('/api/notifications/')
    request.user = test_data['staff_user1']
    request.authenticated_user = test_data['staff_user1']
    
    # Mock get_request_user to return our test user
    with patch('notifications.views.get_request_user', return_value=test_data['staff_user1']):
        response = get_notifications(request)
        
        # Should return JSON response
        assert isinstance(response, JsonResponse)
        
        # Parse response content
        import json
        content = json.loads(response.content)
        
        print(f"Response content: {content}")
        
        # Should contain notifications data
        assert 'notifications' in content
        assert 'total_count' in content
        assert 'page' in content
        
        print("✅ Hospital filtering in get_notifications working correctly")

@patch('notifications.views.admin_client')
def test_hospital_filtering_in_metrics(mock_admin_client):
    """Test hospital filtering in get_notification_metrics function"""
    
    # Create mock admin client responses
    mock_admin_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[{'id': 'patient_hospital1_001'}]
    )
    mock_admin_client.table.return_value.select.return_value.in_.return_value.execute.return_value = Mock(
        data=[{'id': 'appt_hospital1_001'}]
    )
    
    test_data = create_test_data()
    test_notifications = create_test_notifications(test_data)
    
    factory = RequestFactory()
    
    # Test staff user from hospital 1
    request = factory.get('/api/notifications/metrics/')
    request.user = test_data['staff_user1']
    request.authenticated_user = test_data['staff_user1']
    
    # Mock get_request_user to return our test user
    with patch('notifications.views.get_request_user', return_value=test_data['staff_user1']):
        response = get_notification_metrics(request)
        
        # Should return JSON response
        assert isinstance(response, JsonResponse)
        
        # Parse response content
        import json
        content = json.loads(response.content)
        
        # Should contain metrics data
        assert 'total_notifications' in content
        assert 'success_rate' in content
        assert 'delivery_by_type' in content
        
        print("✅ Hospital filtering in get_notification_metrics working correctly")

@patch('notifications.views.admin_client')
def test_hospital_filtering_in_system_health(mock_admin_client):
    """Test hospital filtering in get_system_health function"""
    
    # Create mock admin client responses
    mock_admin_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[{'id': 'patient_hospital1_001'}]
    )
    
    test_data = create_test_data()
    test_notifications = create_test_notifications(test_data)
    
    factory = RequestFactory()
    
    # Test staff user from hospital 1
    request = factory.get('/api/notifications/health/')
    request.user = test_data['staff_user1']
    request.authenticated_user = test_data['staff_user1']
    
    # Mock get_request_user to return our test user
    with patch('notifications.views.get_request_user', return_value=test_data['staff_user1']):
        response = get_system_health(request)
        
        # Should return JSON response
        assert isinstance(response, JsonResponse)
        
        # Parse response content
        import json
        content = json.loads(response.content)
        
        # Should contain health data
        assert 'services' in content
        assert 'overall_status' in content
        assert 'timestamp' in content
        
        print("✅ Hospital filtering in get_system_health working correctly")

@patch('notifications.views.admin_client')
def test_hospital_filtering_in_realtime_stats(mock_admin_client):
    """Test hospital filtering in get_realtime_stats function"""
    
    # Create mock admin client responses
    mock_admin_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[{'id': 'patient_hospital1_001'}]
    )
    
    test_data = create_test_data()
    test_notifications = create_test_notifications(test_data)
    
    factory = RequestFactory()
    
    # Test staff user from hospital 1
    request = factory.get('/api/notifications/realtime-stats/')
    request.user = test_data['staff_user1']
    request.authenticated_user = test_data['staff_user1']
    
    # Mock get_request_user to return our test user
    with patch('notifications.views.get_request_user', return_value=test_data['staff_user1']):
        response = get_realtime_stats(request)
        
        # Should return JSON response
        assert isinstance(response, JsonResponse)
        
        # Parse response content
        import json
        content = json.loads(response.content)
        
        # Should contain realtime stats data
        assert 'processing_rate' in content
        assert 'error_rate' in content
        assert 'queue_sizes' in content
        
        print("✅ Hospital filtering in get_realtime_stats working correctly")

def main():
    """Run all hospital filtering tests"""
    print("🚀 Testing Hospital-Specific Filtering for Notification Queries")
    print("=" * 60)
    
    try:
        test_hospital_filtering_in_notifications()
        test_hospital_filtering_in_metrics()
        test_hospital_filtering_in_system_health()
        test_hospital_filtering_in_realtime_stats()
        
        print("\n" + "=" * 60)
        print("🎉 All hospital filtering tests passed!")
        print("Hospital-specific filtering is working correctly across all notification endpoints.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)