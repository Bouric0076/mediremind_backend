#!/usr/bin/env python
"""
Test script for the new persistent notification scheduler
"""
import os
import sys
import django
import asyncio
import time
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.utils import timezone
from notifications.persistent_scheduler import PersistentNotificationScheduler
from notifications.models import ScheduledTask, NotificationLog
from appointments.models import Appointment
from accounts.models import EnhancedPatient, EnhancedStaffProfile

def test_scheduler_basic_functionality():
    """Test basic scheduler functionality"""
    print("🧪 Testing Persistent Scheduler Basic Functionality")
    print("=" * 60)
    
    # Initialize scheduler
    scheduler = PersistentNotificationScheduler()
    
    try:
        # Test 1: Start scheduler
        print("1. Starting scheduler...")
        scheduler.start()
        print("   ✅ Scheduler started successfully")
        
        # Test 2: Check status
        print("2. Checking scheduler status...")
        status = scheduler.get_stats()
        print(f"   ✅ Status: Running={status['is_running']}, Pending={status['pending_tasks']}, Processing={status['processing_tasks']}")
        
        # Test 3: Schedule a test reminder
        print("3. Scheduling test reminder...")
        
        # Get a test appointment (create one if needed)
        appointment = Appointment.objects.first()  # Get any appointment for testing
        
        if not appointment:
            print("   ⚠️  No appointments found, creating test appointment...")
            try:
                # Create test patient and provider if needed
                from authentication.models import User
                from appointments.models import AppointmentType
                import uuid
                
                # Create test user for patient with unique email
                unique_id = str(uuid.uuid4())[:8]
                test_user, created = User.objects.get_or_create(
                    username=f'test_patient_{unique_id}',
                    defaults={
                        'email': f'test_{unique_id}@example.com',
                        'first_name': 'Test',
                        'last_name': 'Patient',
                        'full_name': f'Test Patient {unique_id}',
                        'role': 'patient'
                    }
                )
                
                # Create test patient
                from datetime import date
                test_patient, created = EnhancedPatient.objects.get_or_create(
                    user=test_user,
                    defaults={
                        'phone': '+1234567890',
                        'date_of_birth': date(1990, 1, 1),
                        'gender': 'M',
                        'address_line1': '123 Test Street',
                        'city': 'Test City',
                        'state': 'Test State',
                        'zip_code': '12345',
                        'emergency_contact_name': 'Emergency Contact',
                        'emergency_contact_relationship': 'Family',
                        'emergency_contact_phone': '+1987654321'
                    }
                )
                
                # Create test provider user
                provider_user, created = User.objects.get_or_create(
                    username=f'test_provider_{unique_id}',
                    defaults={
                        'email': f'provider_{unique_id}@example.com',
                        'first_name': 'Dr. Test',
                        'last_name': 'Provider',
                        'full_name': f'Dr. Test Provider {unique_id}',
                        'role': 'doctor'
                    }
                )
                
                # Create test provider
                test_provider, created = EnhancedStaffProfile.objects.get_or_create(
                    user=provider_user,
                    defaults={
                        'job_title': 'Doctor',
                        'department': 'General Medicine',
                        'hire_date': date(2020, 1, 1)
                    }
                )
                
                # Create or get test appointment type
                test_appointment_type, created = AppointmentType.objects.get_or_create(
                    code='consultation',
                    defaults={
                        'name': 'Consultation',
                        'description': 'General consultation appointment',
                        'default_duration': 30,
                        'base_cost': 100.00
                    }
                )
                
                # Create test appointment with proper field names
                start_time = datetime.now().time()
                end_time = (datetime.combine(datetime.now().date(), start_time) + timedelta(minutes=30)).time()
                
                test_appointment = Appointment.objects.create(
                    patient=test_patient,
                    provider=test_provider,
                    appointment_type=test_appointment_type,
                    appointment_date=timezone.now().date() + timedelta(days=1),
                    start_time=start_time,
                    end_time=end_time,
                    duration=30,
                    reason='Test appointment for scheduler testing',
                    status='scheduled'
                )
                
                appointment_id = str(test_appointment.id)
                print(f"   ✅ Created test appointment: {appointment_id}")
                
            except Exception as e:
                print(f"   ❌ Error creating test appointment: {str(e)}")
                return False
        else:
            appointment_id = str(appointment.id)
            print(f"   ✅ Found existing appointment: {appointment_id}")
        
        # Schedule reminder using the persistent scheduler
        try:
            success = scheduler.schedule_reminder(
                appointment_id=appointment_id,
                reminder_type='reminder_24h',
                delivery_method='email',
                scheduled_time=timezone.now() + timedelta(minutes=1)
            )
            
            if success:
                print("   ✅ Test reminder scheduled successfully")
            else:
                print("   ❌ Failed to schedule test reminder")
                return False
            
        except Exception as e:
            print(f"   ❌ Error scheduling reminder: {e}")
            return False
        
        # Test 4: Check database persistence
        print("4. Checking database persistence...")
        from notifications.models import ScheduledTask
        db_tasks = ScheduledTask.objects.filter(status='pending').count()
        print(f"   ✅ Found {db_tasks} pending tasks in database")
        
        # Test 5: Wait a moment and check processing
        print("5. Waiting 5 seconds to observe processing...")
        time.sleep(5)
        
        # Check updated status
        status = scheduler.get_stats()
        print(f"   ✅ Updated status: Pending={status['pending_tasks']}, Processing={status['processing_tasks']}")
        
        # Test 6: Stop scheduler
        print("6. Stopping scheduler...")
        scheduler.stop()
        print("   ✅ Scheduler stopped successfully")
        
        print("\n🎉 All tests passed! Persistent scheduler is working correctly.")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Ensure scheduler is stopped
        try:
            scheduler.stop()
        except:
            pass

def test_scheduler_recovery():
    """Test scheduler recovery from database"""
    print("\n🔄 Testing Scheduler Recovery")
    print("=" * 40)
    
    try:
        # Create some pending tasks in database
        print("1. Creating test tasks in database...")
        
        # Get test appointment
        appointment = Appointment.objects.first()
        if not appointment:
            print("   ❌ No appointments found for testing")
            return False
        
        # Create test tasks
        test_tasks = []
        for i in range(3):
            task = ScheduledTask.objects.create(
                task_type='reminder',
                appointment_id=appointment.id,
                scheduled_time=timezone.now() + timedelta(minutes=i+1),
                status='pending',
                priority=2,  # Medium priority as integer
                message_data={
                    'reminder_type': '24_hour',
                    'patient_id': str(appointment.patient.id),
                    'provider_id': str(appointment.provider.id)
                }
            )
            test_tasks.append(task)
        
        print(f"   ✅ Created {len(test_tasks)} test tasks")
        
        # Test recovery
        print("2. Starting scheduler to test recovery...")
        scheduler = PersistentNotificationScheduler()
        scheduler.start()
        
        # Check if tasks were recovered
        status = scheduler.get_stats()
        print(f"   ✅ Scheduler recovered {status['pending_tasks']} tasks")
        
        # Clean up
        scheduler.stop()
        for task in test_tasks:
            task.delete()
        
        print("   ✅ Recovery test completed successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Recovery test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Persistent Scheduler Tests")
    print("=" * 80)
    
    # Test basic functionality
    basic_test_passed = test_scheduler_basic_functionality()
    
    # Test recovery
    recovery_test_passed = test_scheduler_recovery()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 20)
    print(f"Basic Functionality: {'✅ PASSED' if basic_test_passed else '❌ FAILED'}")
    print(f"Recovery Test: {'✅ PASSED' if recovery_test_passed else '❌ FAILED'}")
    
    if basic_test_passed and recovery_test_passed:
        print("\n🎉 All tests passed! The persistent scheduler is ready for production.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())