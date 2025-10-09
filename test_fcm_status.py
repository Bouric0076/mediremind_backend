#!/usr/bin/env python3
"""
Test FCM status and functionality
"""

import requests
import json
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

def test_fcm_status():
    print("🔔 Testing FCM Status and Configuration")
    print("=" * 50)
    
    # Test with valid token
    headers = {
        'Authorization': 'Token 9a495996b6e6e10a0a97b9f3d47ae1c8743c3ee5',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test FCM status endpoint
        response = requests.get('http://127.0.0.1:8000/api/notifications/fcm/status/', headers=headers)
        print(f"FCM Status Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"FCM Configured: {data.get('fcm_configured', 'N/A')}")
            print(f"User Tokens: {len(data.get('user_tokens', []))}")
            print(f"Message: {data.get('message', 'N/A')}")
            
            if data.get('fcm_configured'):
                print("✅ FCM is configured")
            else:
                print("❌ FCM is not configured")
                
            if data.get('user_tokens'):
                print("✅ User has FCM tokens registered")
                for token in data['user_tokens']:
                    print(f"  - Token: {token[:20]}...")
            else:
                print("⚠️  No FCM tokens registered for user")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing FCM status: {e}")

def test_fcm_test_notification():
    print("\n🔔 Testing FCM Test Notification")
    print("=" * 50)
    
    headers = {
        'Authorization': 'Token 9a495996b6e6e10a0a97b9f3d47ae1c8743c3ee5',
        'Content-Type': 'application/json'
    }
    
    try:
        # Send test notification
        response = requests.post(
            'http://127.0.0.1:8000/api/notifications/fcm/test/',
            headers=headers,
            json={
                'title': 'Test Notification',
                'body': 'This is a test FCM notification',
                'data': {'test': 'true', 'timestamp': '2024-01-01T00:00:00Z'}
            }
        )
        
        print(f"Test Notification Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success', 'N/A')}")
            print(f"Message: {data.get('message', 'N/A')}")
            if 'fcm_result' in data:
                print(f"FCM Result: {data['fcm_result']}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error sending test notification: {e}")

if __name__ == "__main__":
    test_fcm_status()
    test_fcm_test_notification()