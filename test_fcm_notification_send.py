import requests
import json

# Test sending FCM notification
headers = {
    'Authorization': 'Token 9a495996b6e6e10a0a97b9f3d47ae1c8743c3ee5',
    'Content-Type': 'application/json'
}

# Test notification data
test_notification = {
    "title": "Test FCM Notification",
    "body": "This is a test notification from the backend to verify FCM is working correctly.",
    "data": {
        "type": "test_notification",
        "timestamp": "2024-01-01T12:00:00Z",
        "priority": "high"
    }
}

try:
    # Send test notification
    response = requests.post(
        'http://127.0.0.1:8000/api/notifications/fcm/test/',
        headers=headers,
        json=test_notification
    )
    
    print(f'Test Notification Status: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print('✅ Test notification sent successfully!')
        print(f'Success count: {result.get("result", {}).get("success", 0)}')
        print(f'Failure count: {result.get("result", {}).get("failure", 0)}')
        if result.get("result", {}).get("errors"):
            print(f'Errors: {result.get("result", {}).get("errors")}')
    else:
        print(f'❌ Test notification failed: {response.text}')
        
    # Check FCM status again
    status_response = requests.get(
        'http://127.0.0.1:8000/api/notifications/fcm/status/',
        headers=headers
    )
    
    print(f'\nFinal FCM Status:')
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f'User tokens: {status_data.get("user_tokens", 0)}')
        print(f'FCM configured: {status_data.get("fcm_configured", False)}')
        
except Exception as e:
    print(f'Error: {e}')