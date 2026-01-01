#!/usr/bin/env python
"""
Test the API endpoint with the new encryption system
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

import requests
import json
from encryption.key_manager import key_manager

def test_patient_api():
    """Test the patient detail API endpoint"""
    
    # Use the patient ID from the previous test
    patient_id = "6fe9d5da-05fa-4469-8f7f-f423949361c4"
    
    # Test the API endpoint
    base_url = "http://localhost:8000"  # Adjust if different
    api_url = f"{base_url}/api/accounts/patients/{patient_id}/"
    
    print(f"Testing API endpoint: {api_url}")
    
    try:
        response = requests.get(api_url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("API Response:")
            print(json.dumps(data, indent=2))
            
            # Check if encrypted fields are properly decrypted
            patient_data = data.get('patient', {})
            print(f"\nDecrypted fields from API:")
            print(f"Phone: {patient_data.get('phone', 'N/A')}")
            print(f"Address: {patient_data.get('address_line1', 'N/A')}")
            print(f"Allergies: {patient_data.get('allergies', 'N/A')}")
            print(f"Insurance: {patient_data.get('insurance_provider', 'N/A')}")
            
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Make sure Django is running.")
        print("You can start it with: python manage.py runserver")
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_patient_api()