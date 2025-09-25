#!/usr/bin/env python3
"""
Production URL Routing and Authentication Diagnostic Script
Tests various URL patterns and authentication flows to identify production issues
"""

import requests
import json
from datetime import datetime
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_url_routing():
    """Test various URL patterns to identify routing issues"""
    
    base_url = "https://mediremind-backend-cl6r.onrender.com"
    
    # Test different URL patterns
    test_urls = [
        "/health/",
        "/api/health/", 
        "/health",
        "/api/health",
        "/api/auth/login/",
        "/auth/login/",
        "/api/auth/register/",
        "/admin/",
        "/static/",
    ]
    
    print("🔍 Testing URL Routing Patterns")
    print("=" * 60)
    
    results = {}
    
    for url_path in test_urls:
        full_url = f"{base_url}{url_path}"
        print(f"\n📍 Testing: {full_url}")
        
        try:
            # Test with different methods
            methods_to_test = ['GET']
            if 'login' in url_path or 'register' in url_path:
                methods_to_test.append('POST')
                
            for method in methods_to_test:
                print(f"   {method}: ", end="")
                
                if method == 'GET':
                    response = requests.get(full_url, timeout=30, allow_redirects=True)
                else:
                    # POST with minimal data for testing
                    response = requests.post(
                        full_url, 
                        json={"test": "data"}, 
                        timeout=30, 
                        allow_redirects=True
                    )
                
                print(f"Status {response.status_code}")
                
                # Store result
                key = f"{url_path}_{method}"
                results[key] = {
                    'status_code': response.status_code,
                    'url': full_url,
                    'final_url': response.url,
                    'redirected': response.url != full_url,
                    'headers': dict(response.headers),
                    'method': method
                }
                
                # Show redirect info
                if response.url != full_url:
                    print(f"      → Redirected to: {response.url}")
                
                # Show response preview for key endpoints
                if response.status_code == 200 and 'health' in url_path:
                    try:
                        data = response.json()
                        print(f"      → Response: {json.dumps(data, indent=8)}")
                    except:
                        print(f"      → Response: {response.text[:100]}...")
                        
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout")
            results[f"{url_path}_timeout"] = True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[f"{url_path}_error"] = str(e)
    
    return results

def test_authentication_endpoints():
    """Test authentication with different URL patterns"""
    
    base_url = "https://mediremind-backend-cl6r.onrender.com"
    
    # Test credentials
    test_credentials = {
        "email": "admin@mediremind.test",
        "password": "TestAdmin123!"
    }
    
    # Different auth endpoint patterns to test
    auth_endpoints = [
        "/api/auth/login/",
        "/auth/login/",
        "/api/auth/login",
        "/auth/login"
    ]
    
    print("\n🔐 Testing Authentication Endpoints")
    print("=" * 60)
    
    results = {}
    
    for endpoint in auth_endpoints:
        full_url = f"{base_url}{endpoint}"
        print(f"\n📍 Testing auth at: {full_url}")
        
        try:
            # Test POST request
            response = requests.post(
                full_url,
                json=test_credentials,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=30,
                allow_redirects=True
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Final URL: {response.url}")
            
            # Store result
            results[endpoint] = {
                'status_code': response.status_code,
                'final_url': response.url,
                'redirected': response.url != full_url,
                'headers': dict(response.headers)
            }
            
            # Show response details
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=6)}")
                results[endpoint]['response'] = data
            except:
                print(f"   Response (text): {response.text[:200]}...")
                results[endpoint]['response_text'] = response.text[:200]
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[endpoint] = {'error': str(e)}
    
    return results

def test_cors_and_headers():
    """Test CORS and security headers"""
    
    base_url = "https://mediremind-backend-cl6r.onrender.com"
    
    print("\n🌐 Testing CORS and Security Headers")
    print("=" * 60)
    
    # Test CORS preflight
    test_url = f"{base_url}/api/auth/login/"
    
    try:
        # OPTIONS request (CORS preflight)
        print(f"📍 Testing CORS preflight: {test_url}")
        
        response = requests.options(
            test_url,
            headers={
                'Origin': 'https://mediremind-staff-portal.vercel.app',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type, Authorization'
            },
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        print("   CORS Headers:")
        
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods', 
            'Access-Control-Allow-Headers',
            'Access-Control-Allow-Credentials'
        ]
        
        for header in cors_headers:
            value = response.headers.get(header, 'Not set')
            print(f"      {header}: {value}")
        
        # Test security headers
        print("\n   Security Headers:")
        security_headers = [
            'Strict-Transport-Security',
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Referrer-Policy',
            'Content-Security-Policy'
        ]
        
        for header in security_headers:
            value = response.headers.get(header, 'Not set')
            print(f"      {header}: {value}")
            
        return {
            'cors_status': response.status_code,
            'cors_headers': {h: response.headers.get(h) for h in cors_headers},
            'security_headers': {h: response.headers.get(h) for h in security_headers}
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {'error': str(e)}

def main():
    """Run all diagnostic tests"""
    
    print("🏥 MediRemind Production Diagnostic Tool")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run all tests
    routing_results = test_url_routing()
    auth_results = test_authentication_endpoints()
    cors_results = test_cors_and_headers()
    
    # Summary
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    # Health endpoint analysis
    health_endpoints = [k for k in routing_results.keys() if 'health' in k and 'GET' in k]
    print(f"\n🏥 Health Endpoints ({len(health_endpoints)} tested):")
    for endpoint in health_endpoints:
        result = routing_results[endpoint]
        status = result['status_code']
        emoji = "✅" if status == 200 else "❌"
        print(f"   {emoji} {endpoint}: {status}")
    
    # Auth endpoint analysis
    print(f"\n🔐 Authentication Endpoints ({len(auth_results)} tested):")
    for endpoint, result in auth_results.items():
        if 'error' in result:
            print(f"   ❌ {endpoint}: Error - {result['error']}")
        else:
            status = result['status_code']
            emoji = "✅" if status in [200, 401] else "❌"  # 401 is expected for invalid creds
            print(f"   {emoji} {endpoint}: {status}")
    
    # CORS analysis
    print(f"\n🌐 CORS Configuration:")
    if 'error' not in cors_results:
        cors_status = cors_results['cors_status']
        emoji = "✅" if cors_status == 200 else "❌"
        print(f"   {emoji} CORS Preflight: {cors_status}")
        
        origin_header = cors_results['cors_headers'].get('Access-Control-Allow-Origin')
        if origin_header:
            print(f"   🌍 Allowed Origins: {origin_header}")
        else:
            print(f"   ❌ No CORS origin header found")
    else:
        print(f"   ❌ CORS test failed: {cors_results['error']}")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()