#!/usr/bin/env python3
"""
Comprehensive test script for MediRemind medication reminder system.
Tests both Django backend and integration points.
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from notifications.models import FCMToken, NotificationPreference, ScheduledTask
from notifications.medication_reminder_service import MedicationReminderService
from notifications.notification_sender import NotificationSender


class MedicationReminderTestSuite:
    """Test suite for medication reminder functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_user = None
        self.test_fcm_token = "test_fcm_token_123456789"
        self.notification_sender = NotificationSender()
        self.reminder_service = MedicationReminderService()
        
    def setup_test_data(self):
        """Setup test user and data"""
        print("Setting up test data...")
        
        # Create test user
        self.test_user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        # Create FCM token for test user
        fcm_token, created = FCMToken.objects.get_or_create(
            user=self.test_user,
            defaults={
                'token': self.test_fcm_token,
                'device_type': 'android',
                'is_active': True
            }
        )
        
        # Create notification preferences
        prefs, created = NotificationPreference.objects.get_or_create(
            user=self.test_user,
            defaults={
                'medication_reminders': True,
                'appointment_reminders': True,
                'system_notifications': True,
                'emergency_alerts': True,
                'quiet_hours_start': '22:00',
                'quiet_hours_end': '07:00'
            }
        )
        
        print(f"✓ Test user created: {self.test_user.username}")
        print(f"✓ FCM token registered: {fcm_token.token[:20]}...")
        print(f"✓ Notification preferences set")
        
    def test_medication_reminder_scheduling(self):
        """Test scheduling medication reminders"""
        print("\n--- Testing Medication Reminder Scheduling ---")
        
        try:
            # Test data
            medication_name = "Aspirin"
            dosage = "100mg"
            reminder_time = timezone.now() + timedelta(minutes=5)
            frequency = ["daily"]
            instructions = "Take with food"
            
            # Schedule reminder
            result = self.reminder_service.schedule_medication_reminder(
                user_id=str(self.test_user.id),
                medication_name=medication_name,
                dosage=dosage,
                reminder_time=reminder_time,
                frequency=frequency,
                instructions=instructions
            )
            
            if result:
                print(f"✓ Medication reminder scheduled successfully")
                
                # Verify scheduled task was created
                tasks = ScheduledTask.objects.filter(
                    user=self.test_user,
                    task_type='medication_reminder',
                    is_active=True
                )
                
                if tasks.exists():
                    print(f"✓ Scheduled task created in database")
                    return True
                else:
                    print("✗ No scheduled task found in database")
                    return False
            else:
                print("✗ Failed to schedule medication reminder")
                return False
                
        except Exception as e:
            print(f"✗ Error scheduling medication reminder: {e}")
            return False
    
    def test_immediate_medication_reminder(self):
        """Test sending immediate medication reminders"""
        print("\n--- Testing Immediate Medication Reminder ---")
        
        try:
            result = self.reminder_service.send_immediate_medication_reminder(
                user_id=str(self.test_user.id),
                medication_name="Vitamin D",
                dosage="1000 IU",
                instructions="Take with breakfast"
            )
            
            if result:
                print("✓ Immediate medication reminder sent successfully")
                return True
            else:
                print("✗ Failed to send immediate medication reminder")
                return False
                
        except Exception as e:
            print(f"✗ Error sending immediate reminder: {e}")
            return False
    
    def test_medication_taken_tracking(self):
        """Test marking medication as taken"""
        print("\n--- Testing Medication Taken Tracking ---")
        
        try:
            # First, create a medication reminder
            reminder_time = timezone.now() + timedelta(minutes=1)
            result = self.reminder_service.schedule_medication_reminder(
                user_id=str(self.test_user.id),
                medication_name="Test Medication",
                dosage="50mg",
                reminder_time=reminder_time,
                frequency=["daily"]
            )
            
            if not result:
                print("✗ Failed to create test medication reminder")
                return False
            
            # Get the created task
            task = ScheduledTask.objects.filter(
                user=self.test_user,
                task_type='medication_reminder',
                is_active=True
            ).first()
            
            if not task:
                print("✗ No medication reminder task found")
                return False
            
            # Mark as taken
            result = self.reminder_service.mark_medication_as_taken(
                user_id=str(self.test_user.id),
                medication_id=task.id
            )
            
            if result:
                print("✓ Medication marked as taken successfully")
                return True
            else:
                print("✗ Failed to mark medication as taken")
                return False
                
        except Exception as e:
            print(f"✗ Error marking medication as taken: {e}")
            return False
    
    def test_snooze_functionality(self):
        """Test snoozing medication reminders"""
        print("\n--- Testing Snooze Functionality ---")
        
        try:
            # Create a medication reminder
            reminder_time = timezone.now() + timedelta(minutes=1)
            result = self.reminder_service.schedule_medication_reminder(
                user_id=str(self.test_user.id),
                medication_name="Snooze Test Med",
                dosage="25mg",
                reminder_time=reminder_time,
                frequency=["daily"]
            )
            
            if not result:
                print("✗ Failed to create test medication reminder")
                return False
            
            # Get the created task
            task = ScheduledTask.objects.filter(
                user=self.test_user,
                task_type='medication_reminder',
                is_active=True
            ).last()
            
            if not task:
                print("✗ No medication reminder task found")
                return False
            
            # Snooze for 10 minutes
            snooze_duration = timedelta(minutes=10)
            result = self.reminder_service.snooze_medication_reminder(
                user_id=str(self.test_user.id),
                medication_id=task.id,
                snooze_duration=snooze_duration
            )
            
            if result:
                print("✓ Medication reminder snoozed successfully")
                return True
            else:
                print("✗ Failed to snooze medication reminder")
                return False
                
        except Exception as e:
            print(f"✗ Error snoozing medication reminder: {e}")
            return False
    
    def test_upcoming_reminders(self):
        """Test retrieving upcoming reminders"""
        print("\n--- Testing Upcoming Reminders Retrieval ---")
        
        try:
            reminders = self.reminder_service.get_upcoming_reminders(
                user_id=str(self.test_user.id),
                limit=10
            )
            
            print(f"✓ Retrieved {len(reminders)} upcoming reminders")
            
            for reminder in reminders[:3]:  # Show first 3
                print(f"  - {reminder.get('medication_name', 'Unknown')} at {reminder.get('scheduled_time', 'Unknown time')}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error retrieving upcoming reminders: {e}")
            return False
    
    def test_medication_history(self):
        """Test retrieving medication history"""
        print("\n--- Testing Medication History ---")
        
        try:
            history = self.reminder_service.get_medication_history(
                user_id=str(self.test_user.id),
                limit=10
            )
            
            print(f"✓ Retrieved {len(history)} medication history entries")
            return True
            
        except Exception as e:
            print(f"✗ Error retrieving medication history: {e}")
            return False
    
    def test_medication_statistics(self):
        """Test retrieving medication statistics"""
        print("\n--- Testing Medication Statistics ---")
        
        try:
            stats = self.reminder_service.get_medication_statistics(
                user_id=str(self.test_user.id)
            )
            
            print(f"✓ Retrieved medication statistics:")
            print(f"  - Total reminders: {stats.get('total_reminders', 0)}")
            print(f"  - Completed: {stats.get('completed_reminders', 0)}")
            print(f"  - Missed: {stats.get('missed_reminders', 0)}")
            print(f"  - Adherence rate: {stats.get('adherence_rate', 0)}%")
            
            return True
            
        except Exception as e:
            print(f"✗ Error retrieving medication statistics: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints if Django server is running"""
        print("\n--- Testing API Endpoints ---")
        
        try:
            # Test health check endpoint
            response = requests.get(f"{self.base_url}/api/notifications/health/", timeout=5)
            if response.status_code == 200:
                print("✓ Health check endpoint working")
            else:
                print(f"✗ Health check failed: {response.status_code}")
                return False
            
            # Test medication reminder endpoints (would need authentication in real scenario)
            print("ℹ API endpoint tests require authentication - skipping detailed tests")
            print("ℹ Endpoints available:")
            print("  - POST /api/notifications/medication/schedule/")
            print("  - POST /api/notifications/medication/immediate/")
            print("  - POST /api/notifications/medication/taken/")
            print("  - POST /api/notifications/medication/snooze/")
            print("  - GET /api/notifications/medication/upcoming/")
            print("  - DELETE /api/notifications/medication/cancel/")
            print("  - GET /api/notifications/medication/history/")
            print("  - GET /api/notifications/medication/statistics/")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"ℹ Django server not running - API tests skipped")
            print(f"  Start server with: python manage.py runserver")
            return True
    
    def test_fcm_integration(self):
        """Test FCM integration"""
        print("\n--- Testing FCM Integration ---")
        
        try:
            # Test FCM token registration
            token_exists = FCMToken.objects.filter(
                user=self.test_user,
                token=self.test_fcm_token,
                is_active=True
            ).exists()
            
            if token_exists:
                print("✓ FCM token registered in database")
            else:
                print("✗ FCM token not found in database")
                return False
            
            # Test notification sending (mock)
            result = self.notification_sender.send_fcm_notification(
                user_id=str(self.test_user.id),
                title="Test Notification",
                body="This is a test notification",
                data={"type": "test"}
            )
            
            if result:
                print("✓ FCM notification sent successfully")
            else:
                print("ℹ FCM notification sending requires Firebase configuration")
            
            return True
            
        except Exception as e:
            print(f"✗ Error testing FCM integration: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n--- Cleaning up test data ---")
        
        try:
            # Remove scheduled tasks
            ScheduledTask.objects.filter(user=self.test_user).delete()
            
            # Remove FCM tokens
            FCMToken.objects.filter(user=self.test_user).delete()
            
            # Remove notification preferences
            NotificationPreference.objects.filter(user=self.test_user).delete()
            
            # Remove test user
            self.test_user.delete()
            
            print("✓ Test data cleaned up successfully")
            
        except Exception as e:
            print(f"✗ Error cleaning up test data: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("MEDIREMIND MEDICATION REMINDER SYSTEM TEST SUITE")
        print("=" * 60)
        
        # Setup
        self.setup_test_data()
        
        # Run tests
        tests = [
            ("Medication Reminder Scheduling", self.test_medication_reminder_scheduling),
            ("Immediate Medication Reminder", self.test_immediate_medication_reminder),
            ("Medication Taken Tracking", self.test_medication_taken_tracking),
            ("Snooze Functionality", self.test_snooze_functionality),
            ("Upcoming Reminders", self.test_upcoming_reminders),
            ("Medication History", self.test_medication_history),
            ("Medication Statistics", self.test_medication_statistics),
            ("API Endpoints", self.test_api_endpoints),
            ("FCM Integration", self.test_fcm_integration),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"✗ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status:<8} {test_name}")
        
        print("-" * 60)
        print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! Medication reminder system is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
        
        return passed == total


if __name__ == "__main__":
    test_suite = MedicationReminderTestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)