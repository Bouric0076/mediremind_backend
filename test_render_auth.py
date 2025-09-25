#!/usr/bin/env python3
"""
Test authentication flow on the deployed Render environment
"""

import requests
import json
import sys

def test_render_authentication():
    """Test authentication on the deployed Render backend"""
    
    # Render backend URL from the render.yaml configuration
    render_url = "https://mediremind-backend-cl6r.onrender.com"
    login_endpoint = f"{render_url}/api/auth/login/"
    
    # Test credentials
    credentials = {
        "email": "admin@mediremind.test",
        "password": "admin123"
    }
    
    print(f"🔍 Testing authentication on Render deployment...")
    print(f"📍 URL: {login_endpoint}")
    print(f"👤 Email: {credentials['email']}")
    print("-" * 50)
    
    try:
        # Make the authentication request
        response = requests.post(
            login_endpoint,
            json=credentials,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=30  # Render free tier can have cold starts
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Authentication successful!")
                print(f"🔑 Token: {data.get('access_token', 'N/A')[:20]}...")
                print(f"👤 User: {data.get('user', {}).get('email', 'N/A')}")
                print(f"🆔 User ID: {data.get('user', {}).get('id', 'N/A')}")
                print(f"👥 Role: {data.get('user', {}).get('role', 'N/A')}")
                return True
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
                print(f"📄 Raw response: {response.text}")
                return False
        else:
            print(f"❌ Authentication failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"📄 Error details: {json.dumps(error_data, indent=2)}")
            except json.JSONDecodeError:
                print(f"📄 Raw response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - Render service might be sleeping (cold start)")
        print("💡 Try again in a few seconds as the service wakes up")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Connection error: {e}")
        print("💡 Check if the Render service is deployed and running")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint to verify service is running"""
    
    render_url = "https://mediremind-backend-cl6r.onrender.com"
    health_endpoint = f"{render_url}/health/"
    
    print(f"🏥 Testing health endpoint...")
    print(f"📍 URL: {health_endpoint}")
    print("-" * 50)
    
    try:
        response = requests.get(health_endpoint, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ Health check passed!")
                print(f"📄 Response: {json.dumps(data, indent=2)}")
                return True
            except json.JSONDecodeError:
                print("✅ Health check passed (non-JSON response)")
                print(f"📄 Response: {response.text}")
                return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Health check timed out - service might be sleeping")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing MediRemind Render Deployment")
    print("=" * 50)
    
    # Test health endpoint first
    health_ok = test_health_endpoint()
    print()
    
    # Test authentication
    auth_ok = test_render_authentication()
    print()
    
    # Summary
    print("📋 Test Summary:")
    print(f"   Health Endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   Authentication: {'✅ PASS' if auth_ok else '❌ FAIL'}")
    
    if health_ok and auth_ok:
        print("\n🎉 All tests passed! Render deployment is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the deployment status.")
        sys.exit(1)