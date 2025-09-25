#!/usr/bin/env python3
"""
CORS Configuration Test and Authentication Fix
Tests CORS with different origins and fixes authentication issues
"""

import requests
import json
from datetime import datetime

def test_cors_with_different_origins():
    """Test CORS with different origin headers"""
    
    base_url = "https://mediremind-backend-cl6r.onrender.com"
    test_url = f"{base_url}/api/auth/login/"
    
    # Different origins to test
    test_origins = [
        "https://mediremind-frontend.onrender.com",
        "https://mediremind-staff-portal.vercel.app", 
        "https://localhost:3000",
        "http://localhost:3000",
        "https://127.0.0.1:3000",
        None  # No origin header
    ]
    
    print("🌐 Testing CORS with Different Origins")
    print("=" * 60)
    
    for origin in test_origins:
        print(f"\n📍 Testing with Origin: {origin or 'None'}")
        
        headers = {
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, Authorization'
        }
        
        if origin:
            headers['Origin'] = origin
        
        try:
            # OPTIONS request (CORS preflight)
            response = requests.options(test_url, headers=headers, timeout=30)
            
            print(f"   Status: {response.status_code}")
            
            # Check CORS response headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            print("   CORS Headers:")
            for header, value in cors_headers.items():
                status = "✅" if value else "❌"
                print(f"      {status} {header}: {value or 'Not set'}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_authentication_with_cors():
    """Test authentication with proper CORS headers"""
    
    base_url = "https://mediremind-backend-cl6r.onrender.com"
    auth_url = f"{base_url}/api/auth/login/"
    
    # Test credentials
    credentials = {
        "email": "admin@mediremind.test",
        "password": "TestAdmin123!"
    }
    
    print("\n🔐 Testing Authentication with CORS Headers")
    print("=" * 60)
    
    # Test with different origin headers
    test_origins = [
        "https://mediremind-frontend.onrender.com",
        "https://mediremind-staff-portal.vercel.app"
    ]
    
    for origin in test_origins:
        print(f"\n📍 Testing auth with Origin: {origin}")
        
        try:
            # First, do CORS preflight
            preflight_response = requests.options(
                auth_url,
                headers={
                    'Origin': origin,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type, Authorization'
                },
                timeout=30
            )
            
            print(f"   Preflight Status: {preflight_response.status_code}")
            
            # Then, do actual POST request
            auth_response = requests.post(
                auth_url,
                json=credentials,
                headers={
                    'Origin': origin,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=30
            )
            
            print(f"   Auth Status: {auth_response.status_code}")
            
            # Check response
            try:
                data = auth_response.json()
                print(f"   Response: {json.dumps(data, indent=6)}")
                
                # If successful, test a protected endpoint
                if auth_response.status_code == 200 and 'token' in data:
                    token = data['token']
                    print(f"   🎉 Authentication successful! Token: {token[:20]}...")
                    
                    # Test protected endpoint
                    profile_url = f"{base_url}/api/auth/profile/"
                    profile_response = requests.get(
                        profile_url,
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Origin': origin
                        },
                        timeout=30
                    )
                    
                    print(f"   Profile Status: {profile_response.status_code}")
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        print(f"   Profile: {json.dumps(profile_data, indent=6)}")
                    
            except json.JSONDecodeError:
                print(f"   Response (text): {auth_response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_health_endpoints():
    """Test health endpoints to confirm they work"""
    
    base_url = "https://mediremind-backend-cl6r.onrender.com"
    
    health_endpoints = [
        "/health/",
        "/api/health/"  # This should return 404 based on our findings
    ]
    
    print("\n🏥 Testing Health Endpoints")
    print("=" * 60)
    
    for endpoint in health_endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n📍 Testing: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=6)}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"   Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_user_creation():
    """Test creating a user in production to fix authentication"""
    
    base_url = "https://mediremind-backend-cl6r.onrender.com"
    register_url = f"{base_url}/api/auth/register/"
    
    print("\n👤 Testing User Registration")
    print("=" * 60)
    
    # Test user data
    user_data = {
        "email": "admin@mediremind.test",
        "password": "TestAdmin123!",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin"
    }
    
    try:
        response = requests.post(
            register_url,
            json=user_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        try:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=6)}")
        except:
            print(f"   Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Run all tests"""
    
    print("🔧 CORS and Authentication Fix Tool")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run tests
    test_cors_with_different_origins()
    test_authentication_with_cors()
    test_health_endpoints()
    test_user_creation()
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()