#!/usr/bin/env python3
"""
Test API Connection to MyRVM Platform
Tests the updated API endpoints and connectivity
"""

import sys
import requests
import json
import time
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "api-client"))

def test_basic_connectivity(base_url):
    """Test basic connectivity to MyRVM Platform"""
    print("🔍 Testing basic connectivity...")
    
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Basic connectivity successful")
            return True
        else:
            print(f"   ❌ Basic connectivity failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_login(base_url):
    """Test login functionality"""
    print("\n🔐 Testing login...")
    
    login_data = {
        'email': 'admin@myrvm.com',
        'password': 'password'
    }
    
    try:
        response = requests.post(f"{base_url}/api/v2/auth/login", 
                               json=login_data, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'token' in data['data']:
                token = data['data']['token']
                print(f"   ✅ Login successful")
                print(f"   Token: {token[:50]}...")
                return token
            else:
                print(f"   ❌ Login failed: No token in response")
                print(f"   Response: {data}")
                return None
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None

def test_deposits_endpoint(base_url, token=None):
    """Test deposits endpoint"""
    print("\n💰 Testing deposits endpoint...")
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        response = requests.get(f"{base_url}/api/v2/deposits", 
                              headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            deposits = data.get('data', [])
            print(f"   ✅ Deposits endpoint successful")
            print(f"   Found {len(deposits)} deposits")
            return True
        else:
            print(f"   ❌ Deposits endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Deposits error: {e}")
        return False

def test_processing_engines_endpoint(base_url, token=None):
    """Test processing engines endpoint"""
    print("\n🤖 Testing processing engines endpoint...")
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        response = requests.get(f"{base_url}/api/v2/processing-engines", 
                              headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            engines = data.get('data', [])
            print(f"   ✅ Processing engines endpoint successful")
            print(f"   Found {len(engines)} processing engines")
            return True
        else:
            print(f"   ❌ Processing engines endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Processing engines error: {e}")
        return False

def test_detection_results_endpoint(base_url, token=None):
    """Test detection results endpoint"""
    print("\n📸 Testing detection results endpoint...")
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        response = requests.get(f"{base_url}/api/v2/detection-results", 
                              headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', [])
            print(f"   ✅ Detection results endpoint successful")
            print(f"   Found {len(results)} detection results")
            return True
        else:
            print(f"   ❌ Detection results endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Detection results error: {e}")
        return False

def test_create_deposit(base_url, token=None):
    """Test create deposit functionality"""
    print("\n💾 Testing create deposit...")
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    deposit_data = {
        'rvm_id': 1,
        'user_id': 1,
        'waste_type': 'plastic',
        'quantity': 1,
        'weight': 0.5,
        'location': 'Jetson Orin Nano Test',
        'notes': 'Test deposit from updated API client'
    }
    
    try:
        response = requests.post(f"{base_url}/api/v2/deposits", 
                               json=deposit_data, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Create deposit successful")
            print(f"   Deposit ID: {data.get('data', {}).get('id', 'N/A')}")
            return True
        else:
            print(f"   ❌ Create deposit failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Create deposit error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 MyRVM Platform API Connection Test")
    print("=" * 60)
    
    base_url = "http://172.28.233.83:8001"
    print(f"Testing connection to: {base_url}")
    
    # Test results
    results = {}
    
    # Test 1: Basic connectivity
    results['connectivity'] = test_basic_connectivity(base_url)
    
    # Test 2: Login
    token = test_login(base_url)
    results['login'] = token is not None
    
    # Test 3: Deposits endpoint
    results['deposits'] = test_deposits_endpoint(base_url, token)
    
    # Test 4: Processing engines endpoint
    results['processing_engines'] = test_processing_engines_endpoint(base_url, token)
    
    # Test 5: Detection results endpoint
    results['detection_results'] = test_detection_results_endpoint(base_url, token)
    
    # Test 6: Create deposit
    results['create_deposit'] = test_create_deposit(base_url, token)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! API integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
