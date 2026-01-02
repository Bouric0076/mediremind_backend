#!/usr/bin/env python3
"""
Test Dead Letter Queue API endpoints
"""

import os
import sys
import django
import json
import uuid
from datetime import datetime, timedelta

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.test import Client
from django.utils import timezone
from notifications.models import ScheduledTask, NotificationLog
from notifications.dead_letter_queue import DeadLetterQueue, DeadLetterQueueManager

def test_dlq_api_endpoints():
    """Test all DLQ API endpoints"""
    print("🚀 Testing Dead Letter Queue API Endpoints")
    print("=" * 50)
    
    client = Client(HTTP_HOST='localhost')
    
    # Create test data
    print("=== Creating test data ===")
    
    # Create a test task that failed
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
    
    # Create DLQ entry
    dlq_entry = DeadLetterQueueManager.add_to_dead_letter_queue(
        task, 
        'Maximum retries exceeded after 3 attempts', 
        'max_retries_exceeded'
    )
    
    print(f"✅ Created test DLQ entry: {dlq_entry.id}")
    
    # Test 1: Get dead letter queue entries
    print("\n=== Test 1: Get DLQ entries ===")
    try:
        response = client.get('/api/notifications/dead-letter-queue/')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication required (expected)")
            print("Response:", response.json())
        else:
            data = response.json()
            print(f"Found {data.get('pagination', {}).get('total_entries', 0)} entries")
            if 'entries' in data and data['entries']:
                print(f"First entry ID: {data['entries'][0]['id']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get DLQ statistics
    print("\n=== Test 2: Get DLQ statistics ===")
    try:
        response = client.get('/api/notifications/dead-letter-queue/statistics/')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication required (expected)")
        else:
            data = response.json()
            print(f"Statistics: {data.get('statistics', {})}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Review DLQ entry (requires POST)
    print("\n=== Test 3: Review DLQ entry ===")
    try:
        review_data = {
            'action': 'mark_resolved',
            'reviewed_by': 'test_user@example.com',
            'resolution_notes': 'Test resolution'
        }
        response = client.post(
            f'/api/notifications/dead-letter-queue/{dlq_entry.id}/review/',
            data=json.dumps(review_data),
            content_type='application/json'
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication required (expected)")
        else:
            data = response.json()
            print(f"Response: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Test with query parameters
    print("\n=== Test 4: Test with query parameters ===")
    try:
        response = client.get('/api/notifications/dead-letter-queue/?status=pending_review&page_size=10')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication required (expected)")
        else:
            data = response.json()
            print(f"Filtered results: {data.get('pagination', {}).get('total_entries', 0)} entries")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Cleanup
    print("\n=== Cleaning up test data ===")
    try:
        DeadLetterQueue.objects.filter(id=dlq_entry.id).delete()
        task.delete()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ API endpoint tests completed")
    print("Note: 401 responses are expected as authentication is required")

if __name__ == '__main__':
    test_dlq_api_endpoints()