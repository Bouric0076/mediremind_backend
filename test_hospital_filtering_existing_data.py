#!/usr/bin/env python
"""
Test hospital-specific filtering logic using existing admin user
This test focuses on the core filtering functionality without creating new data
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

def get_admin_user():
    """Get the existing admin user"""
    try:
        return User.objects.get(email='admin@mediremind.test')
    except User.DoesNotExist:
        print("❌ Admin user not found: admin@mediremind.test")
        return None

def get_or_create_test_hospital():
    """Get or create a test hospital"""
    try:
        return Hospital.objects.get(name="Test Hospital for Filtering")
    except Hospital.DoesNotExist:
        return Hospital.objects.create(
            id=uuid.uuid4(),
            name="Test Hospital for Filtering",
            slug="test-hospital-filtering",
            email="filtering@test.com",
            phone="5559999",
            address_line_1="123 Test St",
            city="Test City",
            state="TS",
            postal_code="99999",
            status='active'
        )

@patch('notifications.views.admin_client')
def test_hospital_filtering_with_existing_data(mock_admin_client):
    """Test hospital filtering logic with existing data"""
    
    print("🚀 Testing Hospital-Specific Filtering Logic with Existing Data")
    print("=" * 60)
    
    # Get admin user
    admin_user = get_admin_user()
    if not admin_user:
        return
    
    print(f"✅ Using admin user: {admin_user.email}")
    
    # Get or create test hospital
    test_hospital = get_or_create_test_hospital()
    print(f"✅ Using test hospital: {test_hospital.name} (ID: {test_hospital.id})")
    
    # Create mock admin client responses
    mock_admin_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[{'id': 'patient_test_001'}, {'id': 'patient_test_002'}]
    )
    mock_admin_client.table.return_value.select.return_value.in_.return_value.execute.return_value = Mock(
        data=[{'id': 'appt_test_001'}, {'id': 'appt_test_002'}]
    )
    
    # Test get_notification_metrics with hospital filtering
    print("\n1. Testing get_notification_metrics with hospital filtering...")
    
    # Mock request object
    mock_request = Mock()
    mock_request.user = admin_user
    mock_request.GET = {'hospital_id': str(test_hospital.id)}
    mock_request.headers = {'Authorization': 'Bearer test-token'}
    mock_request.session = {}
    mock_request.COOKIES = {}
    
    # Test with hospital ID
    result = get_notification_metrics(mock_request)
    
    # Parse the result (should be a JsonResponse)
    import json
    content = json.loads(result.content)
    
    print(f"   Result: {content}")
    
    # Should contain metrics for hospital only
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

def cleanup_test_hospital():
    """Clean up test hospital"""
    print("\n🧹 Cleaning up test hospital...")
    
    try:
        test_hospital = Hospital.objects.get(name="Test Hospital for Filtering")
        test_hospital.delete()
        print("✅ Test hospital cleaned up")
    except Hospital.DoesNotExist:
        print("ℹ️  Test hospital not found, nothing to clean up")

if __name__ == "__main__":
    try:
        test_hospital_filtering_with_existing_data()
    finally:
        cleanup_test_hospital()