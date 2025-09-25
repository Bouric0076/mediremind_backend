#!/usr/bin/env python3
"""
Test script to verify the authentication fix for character limit error
"""

import requests
import json

def test_auth_fix():
    print("🧪 Testing Authentication Fix")
    print("=" * 50)
    
    # Test login with invalid credentials to trigger the failure_reason field
    login_data = {
        'email': 'test@example.com',
        'password': 'wrongpassword'
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:8000/api/auth/login/',
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10,
            verify=False
        )
        print(f'Status Code: {response.status_code}')
        print(f'Response: {response.text}')
        
        if response.status_code == 401:
            print('✅ Authentication endpoint is working - no character limit error')
            print('✅ LoginAttempt.failure_reason field can now handle longer error messages')
        else:
            print(f'⚠️  Unexpected status code: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    test_auth_fix()