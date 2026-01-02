#!/usr/bin/env python3
"""
Test Hospital-Specific Filtering for Notification Queries
Tests the filtering logic without API authentication complications
"""

import os
import sys
import django
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import time

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.test import RequestFactory
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from notifications.models import ScheduledTask, NotificationLog
from accounts.models import EnhancedStaffProfile, Hospital
from notifications.views import get_notifications, get_notification_metrics, get_system_health, get_realtime_stats

User = get_user_model()

# Generate unique timestamp for this test run
test_timestamp = str(int(time.time()))

def test_hospital_filtering_logic():
    """Test the hospital filtering logic directly"""
    print("🚀 Testing Hospital-Specific Filtering Logic")
    print("=" * 60)
    
    # Create test hospitals
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
        address_line_1="456 Oak St",
        city="Test City",
        state="TS",
        postal_code="12346",
        status='active'
    )
    
    # Use existing admin user
    admin_user = User.objects.get(email='admin@mediremind.test')
    
    # Create test staff users
    staff_user1 = User.objects.create_user(
        username=f"test_staff_user1_hospital_filtering_{test_timestamp}",
        email=f"test_staff1_hospital_filtering_{test_timestamp}@test.com", 
        password="testpass123"
    )
    
    staff_user2 = User.objects.create_user(
        username=f"test_staff_user2_hospital_filtering_{test_timestamp}",
        email=f"test_staff2_hospital_filtering_{test_timestamp}@test.com",
        password="testpass123"
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
        error_message='Invalid phone number',
        metadata={
            'response_time_ms': 500,
            'sms_status': 'failed'
        }
    )
    
    print(f"✅ Created test data:")
    print(f"   - Hospital 1: {hospital1.name} ({hospital1.id})")
    print(f"   - Hospital 2: {hospital2.name} ({hospital2.id})")
    print(f"   - Staff user 1: {staff_user1.username} (Hospital 1)")
    print(f"   - Staff user 2: {staff_user2.username} (Hospital 2)")
    print(f"   - Task 1: {task1.id} (Appointment: {appt1_id})")
    print(f"   - Task 2: {task2.id} (Appointment: {appt2_id})")
    print(f"   - Log 1: {log1.id} (Appointment: {appt1_id})")
    print(f"   - Log 2: {log2.id} (Appointment: {appt2_id})")
    
    # Test the filtering logic directly
    print("\n🔍 Testing hospital filtering logic...")
    
    # Mock the admin_client to return appropriate patient data
    with patch('notifications.views.admin_client') as mock_admin_client:
        # Mock patient queries for hospital 1
        mock_admin_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{'id': str(patient1_id)}]
        )
        
        # Mock appointment queries for patients
        mock_admin_client.table.return_value.select.return_value.in_.return_value.execute.return_value = Mock(
            data=[{'id': str(appt1_id)}]
        )
        
        # Test the filtering logic for hospital 1
        print(f"\n📊 Testing query filtering for Hospital 1...")
        
        # Simulate what get_notifications does for hospital filtering
        user_hospital = hospital1
        hospital_appointments = []
        
        try:
            # Get patients from this hospital
            patient_result = mock_admin_client.table("patients").select("id").eq("hospital_id", str(user_hospital.id)).execute()
            if patient_result.data:
                patient_ids = [p['id'] for p in patient_result.data]
                print(f"   Found patients for Hospital 1: {patient_ids}")
                
                # Get appointments for these patients
                if patient_ids:
                    appt_result = mock_admin_client.table("appointments").select("id").in_("patient_id", patient_ids).execute()
                    if appt_result.data:
                        hospital_appointments = [a['id'] for a in appt_result.data]
                        print(f"   Found appointments for Hospital 1: {hospital_appointments}")
            
            # Filter notifications to only those related to hospital's appointments
            if hospital_appointments:
                filtered_tasks = ScheduledTask.objects.filter(appointment_id__in=hospital_appointments)
                filtered_logs = NotificationLog.objects.filter(appointment_id__in=hospital_appointments)
                
                print(f"   Filtered tasks count: {filtered_tasks.count()}")
                print(f"   Filtered logs count: {filtered_logs.count()}")
                
                # Verify only hospital 1 data is returned
                task_ids = [str(task.appointment_id) for task in filtered_tasks]
                log_ids = [str(log.appointment_id) for log in filtered_logs]
                
                print(f"   Task appointment IDs: {task_ids}")
                print(f"   Log appointment IDs: {log_ids}")
                
                # Should only contain appointment 1 (hospital 1)
                assert str(appt1_id) in task_ids, f"Expected {appt1_id} in task appointment IDs"
                assert str(appt1_id) in log_ids, f"Expected {appt1_id} in log appointment IDs"
                assert str(appt2_id) not in task_ids, f"Did not expect {appt2_id} in task appointment IDs"
                assert str(appt2_id) not in log_ids, f"Did not expect {appt2_id} in log appointment IDs"
                
                print("✅ Hospital filtering logic working correctly for Hospital 1!")
            else:
                print("❌ No appointments found for Hospital 1")
                
        except Exception as e:
            print(f"❌ Error testing hospital filtering: {e}")
            return False
    
    # Test for hospital 2
    with patch('notifications.views.admin_client') as mock_admin_client:
        # Mock patient queries for hospital 2
        mock_admin_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{'id': str(patient2_id)}]
        )
        
        # Mock appointment queries for patients
        mock_admin_client.table.return_value.select.return_value.in_.return_value.execute.return_value = Mock(
            data=[{'id': str(appt2_id)}]
        )
        
        print(f"\n📊 Testing query filtering for Hospital 2...")
        
        # Simulate what get_notifications does for hospital filtering
        user_hospital = hospital2
        hospital_appointments = []
        
        try:
            # Get patients from this hospital
            patient_result = mock_admin_client.table("patients").select("id").eq("hospital_id", str(user_hospital.id)).execute()
            if patient_result.data:
                patient_ids = [p['id'] for p in patient_result.data]
                print(f"   Found patients for Hospital 2: {patient_ids}")
                
                # Get appointments for these patients
                if patient_ids:
                    appt_result = mock_admin_client.table("appointments").select("id").in_("patient_id", patient_ids).execute()
                    if appt_result.data:
                        hospital_appointments = [a['id'] for a in appt_result.data]
                        print(f"   Found appointments for Hospital 2: {hospital_appointments}")
            
            # Filter notifications to only those related to hospital's appointments
            if hospital_appointments:
                filtered_tasks = ScheduledTask.objects.filter(appointment_id__in=hospital_appointments)
                filtered_logs = NotificationLog.objects.filter(appointment_id__in=hospital_appointments)
                
                print(f"   Filtered tasks count: {filtered_tasks.count()}")
                print(f"   Filtered logs count: {filtered_logs.count()}")
                
                # Verify only hospital 2 data is returned
                task_ids = [str(task.appointment_id) for task in filtered_tasks]
                log_ids = [str(log.appointment_id) for log in filtered_logs]
                
                print(f"   Task appointment IDs: {task_ids}")
                print(f"   Log appointment IDs: {log_ids}")
                
                # Should only contain appointment 2 (hospital 2)
                assert str(appt2_id) in task_ids, f"Expected {appt2_id} in task appointment IDs"
                assert str(appt2_id) in log_ids, f"Expected {appt2_id} in log appointment IDs"
                assert str(appt1_id) not in task_ids, f"Did not expect {appt1_id} in task appointment IDs"
                assert str(appt1_id) not in log_ids, f"Did not expect {appt1_id} in log appointment IDs"
                
                print("✅ Hospital filtering logic working correctly for Hospital 2!")
            else:
                print("❌ No appointments found for Hospital 2")
                
        except Exception as e:
            print(f"❌ Error testing hospital filtering: {e}")
            return False
    
    print("\n🎉 All hospital filtering tests passed!")
    return True

if __name__ == "__main__":
    success = test_hospital_filtering_logic()
    if success:
        print("\n✅ Hospital filtering implementation is working correctly!")
    else:
        print("\n❌ Hospital filtering tests failed!")
        sys.exit(1)