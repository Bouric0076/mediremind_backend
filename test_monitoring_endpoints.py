#!/usr/bin/env python
"""
Simple test script to verify the new monitoring endpoints work correctly.
"""

import os
import sys
import django
from django.test import TestCase
from django.urls import reverse
from django.test.client import Client
from unittest.mock import patch, MagicMock

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from notifications.models import NotificationLog, ScheduledTask
from authentication.models import User
from django.utils import timezone
from datetime import datetime, timedelta

class MonitoringEndpointsTest(TestCase):
    def setUp(self):
        self.client = Client(HTTP_HOST='localhost')
        
        # Create test data
        import uuid
        self.user = User.objects.create_user(
            username=f'testuser_{uuid.uuid4().hex[:8]}', 
            email=f'test_{uuid.uuid4().hex[:8]}@example.com'
        )
        
        # Create some test notification logs
        import uuid
        for i in range(5):
            appointment_id = str(uuid.uuid4())
            patient_id = str(uuid.uuid4())
            task_id = str(uuid.uuid4())
            
            # Create scheduled task first
            scheduled_task = ScheduledTask.objects.create(
                id=task_id,
                task_type='reminder',
                appointment_id=appointment_id,
                delivery_method='email',
                status='pending' if i % 2 == 0 else 'completed',
                scheduled_time=timezone.now() + timedelta(hours=i)
            )
            
            # Create notification log with reference to the task
            NotificationLog.objects.create(
                appointment_id=appointment_id,
                patient_id=patient_id,
                task_id=task_id,
                delivery_method='email',
                status='sent' if i % 2 == 0 else 'failed',
                metadata={'test': 'data'}
            )

    @patch('notifications.views.get_request_user')
    def test_metrics_endpoint(self, mock_get_user):
        """Test the metrics endpoint returns correct data"""
        mock_user = MagicMock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        
        with patch('notifications.views.admin_client') as mock_admin:
            mock_admin.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{'id': 'test-patient-1'}, {'id': 'test-patient-2'}]
            )
            
            response = self.client.get('/api/notifications/metrics/')
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('total_notifications', data)
            self.assertIn('success_rate', data)
            self.assertIn('delivery_by_type', data)
            self.assertIn('hourly_stats', data)
            print("✅ Metrics endpoint test passed")

    @patch('notifications.views.get_request_user')
    def test_health_endpoint(self, mock_get_user):
        """Test the health endpoint returns correct data"""
        mock_user = MagicMock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        
        response = self.client.get('/api/notifications/health/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('services', data)
        self.assertIn('summary', data)
        self.assertIn('database', data['services'])
        self.assertIn('redis', data['services'])
        self.assertIn('email', data['services'])
        print("✅ Health endpoint test passed")

    @patch('notifications.views.get_request_user')
    def test_realtime_endpoint(self, mock_get_user):
        """Test the realtime stats endpoint returns correct data"""
        mock_user = MagicMock()
        mock_user.id = 'test-user-id'
        mock_get_user.return_value = mock_user
        
        response = self.client.get('/api/notifications/realtime/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('active_queues', data)
        self.assertIn('processing_rate', data)
        self.assertIn('error_rate', data)
        self.assertIn('queue_sizes', data)
        self.assertIn('recent_errors', data)
        print("✅ Realtime endpoint test passed")

if __name__ == '__main__':
    test = MonitoringEndpointsTest()
    test.setUp()
    
    try:
        test.test_metrics_endpoint()
        test.test_health_endpoint()
        test.test_realtime_endpoint()
        print("\n🎉 All monitoring endpoint tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()