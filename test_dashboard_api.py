"""
Test script for Patient Dashboard API
Tests the dashboard endpoint to verify response structure and functionality
"""

import requests
import json
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000"
DASHBOARD_ENDPOINT = f"{BASE_URL}/api/patient/dashboard/"
PROFILE_ENDPOINT = f"{BASE_URL}/api/patient/profile/"

def test_dashboard_api():
    """Test the patient dashboard API endpoint"""
    
    print("=" * 60)
    print("TESTING PATIENT DASHBOARD API")
    print("=" * 60)
    
    # Test without authentication (should fail)
    print("\n1. Testing without authentication...")
    try:
        response = requests.get(DASHBOARD_ENDPOINT)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 401:
            print("✅ Correctly requires authentication")
        else:
            print("❌ Should require authentication")
            print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Please start the Django server first.")
        return
    
    # Test with mock authentication token (this would need a real token in practice)
    print("\n2. Testing with authentication token...")
    headers = {
        'Authorization': 'Bearer mock_token_for_testing',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(DASHBOARD_ENDPOINT, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API endpoint accessible")
            data = response.json()
            
            # Verify response structure
            print("\n3. Verifying response structure...")
            expected_fields = [
                'success', 'data'
            ]
            
            for field in expected_fields:
                if field in data:
                    print(f"✅ {field}: Present")
                else:
                    print(f"❌ {field}: Missing")
            
            if 'data' in data:
                dashboard_data = data['data']
                expected_dashboard_fields = [
                    'patient_name', 'today_stats', 'upcoming_appointments',
                    'current_medications', 'recent_notifications',
                    'health_metrics', 'available_services', 'last_updated'
                ]
                
                print("\nDashboard data structure:")
                for field in expected_dashboard_fields:
                    if field in dashboard_data:
                        print(f"✅ {field}: Present")
                        
                        # Show sample data for key fields
                        if field == 'today_stats':
                            stats = dashboard_data[field]
                            print(f"   - Appointments today: {stats.get('appointments_today', 'N/A')}")
                            print(f"   - Medications due: {stats.get('medications_due', 'N/A')}")
                        elif field == 'available_services':
                            services = dashboard_data[field]
                            print(f"   - Services count: {len(services)}")
                            if services:
                                print(f"   - First service: {services[0].get('name', 'N/A')}")
                    else:
                        print(f"❌ {field}: Missing")
            
            print(f"\nFull Response (formatted):")
            print(json.dumps(data, indent=2, default=str))
            
        else:
            print(f"❌ API request failed")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

def test_profile_api():
    """Test the patient profile API endpoint"""
    
    print("\n" + "=" * 60)
    print("TESTING PATIENT PROFILE API")
    print("=" * 60)
    
    headers = {
        'Authorization': 'Bearer mock_token_for_testing',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(PROFILE_ENDPOINT, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Profile API endpoint accessible")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, default=str)}")
        else:
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("Patient Dashboard API Test Suite")
    print("Make sure the Django server is running on localhost:8000")
    print("Note: This test uses mock authentication - real authentication would be needed for production")
    
    test_dashboard_api()
    test_profile_api()