#!/usr/bin/env python3
"""
Test script to validate production fixes for Token import and EnhancedPatient model
"""

import requests
import json
import sys

def test_production_fixes():
    """Test the fixes in production environment"""
    
    base_url = "https://mediremind-backend-cl6r.onrender.com"
    
    print("🔧 Testing Production Fixes")
    print("=" * 60)
    
    # Test 1: Health check to ensure service is running
    print("\n1. Testing service health...")
    try:
        health_response = requests.get(f"{base_url}/health/", timeout=30)
        print(f"   Status: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   ✅ Service is healthy")
            print(f"   Database: {health_data.get('database', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {health_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {str(e)}")
        return False
    
    # Test 2: Test CORS headers are working
    print("\n2. Testing CORS configuration...")
    try:
        cors_response = requests.options(
            f"{base_url}/api/accounts/patients/create/",
            headers={
                'Origin': 'https://mediremind-frontend.onrender.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            },
            timeout=30
        )
        
        print(f"   Status: {cors_response.status_code}")
        cors_headers = cors_response.headers
        
        if 'Access-Control-Allow-Origin' in cors_headers:
            print(f"   ✅ CORS headers present")
            print(f"   Allow-Origin: {cors_headers.get('Access-Control-Allow-Origin')}")
            print(f"   Allow-Methods: {cors_headers.get('Access-Control-Allow-Methods')}")
            print(f"   Allow-Headers: {cors_headers.get('Access-Control-Allow-Headers')}")
        else:
            print(f"   ❌ CORS headers missing")
            
    except Exception as e:
        print(f"   ❌ CORS test error: {str(e)}")
    
    # Test 3: Test authentication (should work now without Token import error)
    print("\n3. Testing authentication...")
    test_credentials = {
        "email": "admin@mediremind.test",
        "password": "TestAdmin123!"
    }
    
    try:
        auth_response = requests.post(
            f"{base_url}/api/auth/login/",
            json=test_credentials,
            headers={
                'Content-Type': 'application/json',
                'Origin': 'https://mediremind-frontend.onrender.com'
            },
            timeout=30
        )
        
        print(f"   Status: {auth_response.status_code}")
        
        if auth_response.status_code == 200:
            print("   ✅ Authentication successful (no Token import error)")
            auth_data = auth_response.json()
            if auth_data.get('success'):
                user_info = auth_data.get('user', {})
                print(f"   User ID: {user_info.get('id', 'N/A')}")
                print(f"   Email: {user_info.get('email', 'N/A')}")
                print(f"   Role: {user_info.get('role', 'N/A')}")
                
                # Get the access token for patient creation test
                access_token = auth_data.get('access_token')
                
                # Test 4: Test patient creation (should work now without hospital parameter error)
                print("\n4. Testing patient creation...")
                patient_data = {
                    "firstName": "Test",
                    "lastName": "Patient",
                    "email": "test.patient@example.com",
                    "phone": "+1234567890",
                    "dateOfBirth": "1990-01-01",
                    "gender": "M",
                    "address": {
                        "street": "123 Test Street",
                        "city": "Test City",
                        "state": "Test State",
                        "zipCode": "12345"
                    },
                    "emergencyContact": {
                        "name": "Emergency Contact",
                        "relationship": "Family",
                        "phone": "+1987654321"
                    },
                    "account": {
                        "createAccount": True,
                        "sendWelcomeEmail": False
                    }
                }
                
                try:
                    patient_response = requests.post(
                        f"{base_url}/api/accounts/patients/create/",
                        json=patient_data,
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {access_token}',
                            'Origin': 'https://mediremind-frontend.onrender.com'
                        },
                        timeout=30
                    )
                    
                    print(f"   Status: {patient_response.status_code}")
                    
                    if patient_response.status_code == 201:
                        print("   ✅ Patient creation successful (no hospital parameter error)")
                        patient_result = patient_response.json()
                        print(f"   Patient ID: {patient_result.get('patient', {}).get('id', 'N/A')}")
                    elif patient_response.status_code == 400:
                        print("   ⚠️  Patient creation failed with validation error")
                        try:
                            error_data = patient_response.json()
                            print(f"   Error: {error_data.get('error', 'Unknown error')}")
                        except:
                            print(f"   Raw response: {patient_response.text}")
                    elif patient_response.status_code == 500:
                        print("   ❌ Patient creation failed with server error")
                        print("   This indicates the fixes may not be deployed yet")
                    else:
                        print(f"   ❌ Unexpected response: {patient_response.status_code}")
                        print(f"   Response: {patient_response.text}")
                        
                except Exception as e:
                    print(f"   ❌ Patient creation test error: {str(e)}")
                
            else:
                print(f"   ❌ Authentication failed: {auth_data.get('error', 'Unknown error')}")
                
        elif auth_response.status_code == 401:
            print("   ❌ Authentication failed - user may not exist in production")
            try:
                error_data = auth_response.json()
                print(f"   Error: {error_data.get('error', 'Authentication failed')}")
            except:
                print(f"   Raw response: {auth_response.text}")
        else:
            print(f"   ❌ Unexpected auth response: {auth_response.status_code}")
            print(f"   Response: {auth_response.text}")
            
    except Exception as e:
        print(f"   ❌ Authentication test error: {str(e)}")
    
    print("\n📋 Summary:")
    print("   - Tested service health")
    print("   - Tested CORS configuration")
    print("   - Tested authentication (Token import fix)")
    print("   - Tested patient creation (EnhancedPatient hospital parameter fix)")
    print("\n   If patient creation still fails with 500 error, the fixes need to be deployed to production.")

if __name__ == "__main__":
    test_production_fixes()