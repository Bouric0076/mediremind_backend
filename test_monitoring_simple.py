#!/usr/bin/env python
"""
Simple test to verify the new monitoring endpoints are accessible and return proper responses.
"""

import os
import sys
import django
import requests
import json

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

def test_endpoints():
    """Test that the monitoring endpoints are accessible"""
    base_url = "http://localhost:8000/api/notifications"
    
    endpoints = [
        '/metrics/',
        '/health/',
        '/realtime/'
    ]
    
    print("Testing monitoring endpoints...")
    
    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"\nTesting {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ {endpoint} - Success")
                    print(f"Response keys: {list(data.keys())}")
                except json.JSONDecodeError:
                    print(f"❌ {endpoint} - Invalid JSON response")
            elif response.status_code == 401:
                print(f"✅ {endpoint} - Authentication required (expected)")
            else:
                print(f"❌ {endpoint} - Unexpected status code: {response.status_code}")
                if response.text:
                    print(f"Response: {response.text[:200]}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Request failed: {e}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

if __name__ == '__main__':
    test_endpoints()