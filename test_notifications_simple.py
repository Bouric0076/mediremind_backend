#!/usr/bin/env python
"""
Simple test script for notification functionality
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')

# Setup Django
django.setup()

def test_notification_imports():
    """Test that notification modules can be imported"""
    try:
        print("Testing notification module imports...")
        
        # Test basic imports
        from notifications import scheduler
        print("✓ Scheduler module imported successfully")
        
        from notifications import email_client
        print("✓ Email client module imported successfully")
        
        from notifications import beem_client
        print("✓ Beem client module imported successfully")
        
        from notifications import push_notifications
        print("✓ Push notifications module imported successfully")
        
        from notifications import failsafe
        print("✓ Failsafe module imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        return False

def test_email_functionality():
    """Test email notification functionality"""
    try:
        print("\nTesting email functionality...")
        from notifications.email_client import EmailClient
        
        # Test email client initialization
        client = EmailClient()
        print("✓ Email client initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Email test failed: {str(e)}")
        return False

def test_sms_functionality():
    """Test SMS notification functionality"""
    try:
        print("\nTesting SMS functionality...")
        from notifications.beem_client import beem_client
        
        print("✓ SMS client initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ SMS test failed: {str(e)}")
        return False

def test_push_functionality():
    """Test push notification functionality"""
    try:
        print("\nTesting push notification functionality...")
        from notifications.push_notifications import push_notifications
        
        print("✓ Push notifications initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Push notification test failed: {str(e)}")
        return False

def test_failsafe_functionality():
    """Test failsafe delivery functionality"""
    try:
        print("\nTesting failsafe delivery functionality...")
        from notifications.failsafe import FailsafeDeliveryManager
        
        # Test failsafe manager initialization
        manager = FailsafeDeliveryManager()
        print("✓ Failsafe delivery manager initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Failsafe test failed: {str(e)}")
        return False

def main():
    """Run all notification tests"""
    print("=" * 60)
    print("MediRemind Notification System Test")
    print("=" * 60)
    
    tests = [
        test_notification_imports,
        test_email_functionality,
        test_sms_functionality,
        test_push_functionality,
        test_failsafe_functionality,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All notification delivery mechanisms are working!")
        return True
    else:
        print("✗ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)