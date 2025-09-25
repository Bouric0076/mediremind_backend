#!/usr/bin/env python3
"""
Test script to diagnose SSL redirect issues in production authentication
"""
import requests
import json
import sys
from urllib.parse import urlparse

def test_ssl_redirect_behavior():
    """Test how the production server handles HTTP vs HTTPS requests"""
    base_url = "https://mediremind-backend-cl6r.onrender.com"
    
    print("🔍 Testing SSL redirect behavior...")
    print("=" * 60)
    
    # Test 1: Check if HTTP requests get redirected
    print("\n1. Testing HTTP redirect behavior:")
    try:
        http_url = base_url.replace('https://', 'http://')
        response = requests.get(f"{http_url}/api/health/", 
                              allow_redirects=False, 
                              timeout=30)
        print(f"   HTTP request status: {response.status_code}")
        if response.status_code in [301, 302, 307, 308]:
            print(f"   Redirect location: {response.headers.get('Location', 'Not specified')}")
            print("   ❌ HTTP requests are being redirected to HTTPS")
        else:
            print("   ✅ HTTP requests are allowed")
    except Exception as e:
        print(f"   ❌ HTTP request failed: {e}")
    
    # Test 2: Test HTTPS health check
    print("\n2. Testing HTTPS health check:")
    try:
        response = requests.get(f"{base_url}/api/health/", timeout=30)
        print(f"   HTTPS health status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Environment: {data.get('environment', 'unknown')}")
            print(f"   Debug mode: {data.get('debug', 'unknown')}")
            print("   ✅ HTTPS health check successful")
        else:
            print(f"   ❌ HTTPS health check failed: {response.text}")
    except Exception as e:
        print(f"   ❌ HTTPS health check failed: {e}")
    
    # Test 3: Test authentication with proper HTTPS
    print("\n3. Testing HTTPS authentication:")
    try:
        auth_data = {
            "email": "admin@mediremind.test",
            "password": "TestAdmin123!"
        }
        
        response = requests.post(
            f"{base_url}/api/auth/login/",
            json=auth_data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'MediRemind-Test/1.0'
            },
            timeout=30
        )
        
        print(f"   HTTPS auth status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ HTTPS authentication successful")
            print(f"   Token received: {'Yes' if data.get('token') else 'No'}")
        else:
            print(f"   ❌ HTTPS authentication failed")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text[:200]}")
                
    except Exception as e:
        print(f"   ❌ HTTPS authentication failed: {e}")
    
    # Test 4: Check if mixed HTTP/HTTPS causes issues
    print("\n4. Testing mixed protocol behavior:")
    try:
        # Try to authenticate via HTTP (should redirect)
        http_url = base_url.replace('https://', 'http://')
        auth_data = {
            "email": "admin@mediremind.test", 
            "password": "TestAdmin123!"
        }
        
        response = requests.post(
            f"{http_url}/api/auth/login/",
            json=auth_data,
            headers={'Content-Type': 'application/json'},
            allow_redirects=True,  # Follow redirects
            timeout=30
        )
        
        print(f"   HTTP auth with redirects status: {response.status_code}")
        print(f"   Final URL: {response.url}")
        
        if response.status_code == 200:
            print("   ✅ HTTP auth with redirects worked")
        else:
            print("   ❌ HTTP auth with redirects failed")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Mixed protocol test failed: {e}")

def main():
    print("🚀 MediRemind SSL Redirect Diagnosis")
    print("Testing production authentication with SSL redirect settings")
    print()
    
    test_ssl_redirect_behavior()
    
    print("\n" + "=" * 60)
    print("📋 DIAGNOSIS SUMMARY:")
    print("If HTTP requests are being redirected to HTTPS, this could")
    print("interfere with authentication flows that don't handle redirects properly.")
    print("\nPossible solutions:")
    print("1. Always use HTTPS URLs in production requests")
    print("2. Temporarily disable SECURE_SSL_REDIRECT for testing")
    print("3. Ensure authentication clients handle redirects properly")

if __name__ == "__main__":
    main()