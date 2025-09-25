#!/usr/bin/env python3
"""
Test using curl to bypass Python SSL issues
"""

import subprocess
import json

def test_with_curl():
    print("🌐 Testing API Endpoint with curl")
    print("=" * 50)
    
    # Test credentials
    email = "admin@mediremind.test"
    password = "TestAdmin123!"
    
    # Test with HTTP
    url = "http://127.0.0.1:8000/api/auth/login/"
    
    print(f"Testing URL: {url}")
    print(f"Credentials: {email}")
    
    # Prepare curl command
    data = json.dumps({
        'email': email,
        'password': password
    })
    
    curl_cmd = [
        'curl',
        '-X', 'POST',
        '-H', 'Content-Type: application/json',
        '-H', 'User-Agent: Test Script',
        '-d', data,
        '--connect-timeout', '10',
        '--max-time', '30',
        '-v',  # verbose output
        url
    ]
    
    try:
        print(f"\nExecuting: {' '.join(curl_cmd)}")
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"\nReturn code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                print("✅ Authentication successful!")
                if 'token' in response_data:
                    print(f"Token: {response_data['token'][:20]}...")
                    print(f"User: {response_data.get('user', {}).get('email', 'N/A')}")
            except json.JSONDecodeError:
                print("Response is not valid JSON")
        else:
            print("❌ curl command failed")
            
    except subprocess.TimeoutExpired:
        print("❌ Request timed out")
    except FileNotFoundError:
        print("❌ curl command not found. Please install curl.")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_with_curl()