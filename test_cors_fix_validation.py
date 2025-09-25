#!/usr/bin/env python3
"""
Test script to validate CORS configuration fixes in production.
This script tests the updated CORS settings to ensure headers are properly returned.
"""

import requests
import json
from urllib.parse import urljoin

# Production URL
BASE_URL = "https://mediremind-backend-cl6r.onrender.com"

def test_cors_headers():
    """Test CORS headers with different origins and methods."""
    print("🔍 Testing CORS Headers Configuration...")
    print("=" * 60)
    
    # Test origins to check
    test_origins = [
        "https://mediremind-frontend.onrender.com",
        "https://mediremind-backend-cl6r.onrender.com",
        "http://localhost:3000",
        "https://example.com",  # Should be rejected
        None  # No origin header
    ]
    
    # Test endpoints
    endpoints = [
        "/health/",
        "/api/auth/login/",
        "/api/health/"  # This should return 404 but still have CORS headers
    ]
    
    for origin in test_origins:
        print(f"\n📍 Testing Origin: {origin or 'No Origin'}")
        print("-" * 40)
        
        for endpoint in endpoints:
            url = urljoin(BASE_URL, endpoint)
            headers = {}
            
            if origin:
                headers['Origin'] = origin
            
            try:
                # Test OPTIONS request (preflight)
                print(f"  OPTIONS {endpoint}:")
                options_response = requests.options(url, headers=headers, timeout=10)
                print(f"    Status: {options_response.status_code}")
                
                cors_headers = {
                    'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': options_response.headers.get('Access-Control-Allow-Credentials'),
                }
                
                for header_name, header_value in cors_headers.items():
                    if header_value:
                        print(f"    ✅ {header_name}: {header_value}")
                    else:
                        print(f"    ❌ {header_name}: Not set")
                
                # Test GET request
                print(f"  GET {endpoint}:")
                get_response = requests.get(url, headers=headers, timeout=10)
                print(f"    Status: {get_response.status_code}")
                
                get_cors_origin = get_response.headers.get('Access-Control-Allow-Origin')
                if get_cors_origin:
                    print(f"    ✅ Access-Control-Allow-Origin: {get_cors_origin}")
                else:
                    print(f"    ❌ Access-Control-Allow-Origin: Not set")
                    
            except requests.exceptions.RequestException as e:
                print(f"    ❌ Error: {e}")
        
        print()

def test_authentication_with_cors():
    """Test authentication endpoint with proper CORS headers."""
    print("\n🔐 Testing Authentication with CORS...")
    print("=" * 60)
    
    url = urljoin(BASE_URL, "/api/auth/login/")
    origin = "https://mediremind-frontend.onrender.com"
    
    headers = {
        'Origin': origin,
        'Content-Type': 'application/json',
    }
    
    # Test data
    test_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        # First, test OPTIONS preflight
        print("📋 Testing preflight request...")
        options_response = requests.options(url, headers=headers, timeout=10)
        print(f"Preflight Status: {options_response.status_code}")
        
        preflight_cors = {
            'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': options_response.headers.get('Access-Control-Allow-Credentials'),
        }
        
        for header_name, header_value in preflight_cors.items():
            if header_value:
                print(f"✅ {header_name}: {header_value}")
            else:
                print(f"❌ {header_name}: Not set")
        
        # Then test actual POST request
        print("\n📤 Testing POST authentication request...")
        post_response = requests.post(url, json=test_data, headers=headers, timeout=10)
        print(f"POST Status: {post_response.status_code}")
        
        post_cors_origin = post_response.headers.get('Access-Control-Allow-Origin')
        if post_cors_origin:
            print(f"✅ Access-Control-Allow-Origin: {post_cors_origin}")
        else:
            print(f"❌ Access-Control-Allow-Origin: Not set")
        
        # Show response content for debugging
        try:
            response_data = post_response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Text: {post_response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")

def test_health_endpoints():
    """Test health endpoints with CORS."""
    print("\n🏥 Testing Health Endpoints with CORS...")
    print("=" * 60)
    
    endpoints = ["/health/", "/api/health/"]
    origin = "https://mediremind-frontend.onrender.com"
    
    for endpoint in endpoints:
        print(f"\n📍 Testing {endpoint}")
        url = urljoin(BASE_URL, endpoint)
        headers = {'Origin': origin}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            if cors_origin:
                print(f"✅ Access-Control-Allow-Origin: {cors_origin}")
            else:
                print(f"❌ Access-Control-Allow-Origin: Not set")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Health Status: {data.get('status', 'Unknown')}")
                except:
                    print("Response is not JSON")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")

def main():
    """Run all CORS validation tests."""
    print("🚀 CORS Configuration Validation Test")
    print("Testing production environment:", BASE_URL)
    print("=" * 80)
    
    try:
        test_cors_headers()
        test_authentication_with_cors()
        test_health_endpoints()
        
        print("\n" + "=" * 80)
        print("✅ CORS validation tests completed!")
        print("Check the output above to verify CORS headers are properly set.")
        
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()