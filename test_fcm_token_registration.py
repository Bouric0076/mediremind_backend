import requests
import json

# Test FCM token registration with the backend
headers = {
    'Authorization': 'Token 9a495996b6e6e10a0a97b9f3d47ae1c8743c3ee5',
    'Content-Type': 'application/json'
}

# Test data for FCM token registration
test_data = {
    "fcm_token": "test_fcm_token_123456789",
    "platform": "android",
    "device_id": "test_device_123",
    "app_version": "1.0.0"
}

try:
    # Test FCM token registration
    response = requests.post(
        'http://127.0.0.1:8000/api/notifications/fcm/register-token/',
        headers=headers,
        json=test_data
    )
    
    print(f'FCM Token Registration Status: {response.status_code}')
    if response.status_code in [200, 201]:
        print('✅ FCM token registered successfully!')
        print(f'Response: {response.json()}')
    else:
        print(f'❌ FCM token registration failed: {response.text}')
        
    # Check FCM status again after registration
    status_response = requests.get(
        'http://127.0.0.1:8000/api/notifications/fcm/status/',
        headers=headers
    )
    
    print(f'\nFCM Status after registration: {status_response.status_code}')
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f'User tokens: {status_data.get("user_tokens", 0)}')
        print(f'FCM configured: {status_data.get("fcm_configured", False)}')
        
except Exception as e:
    print(f'Error: {e}')