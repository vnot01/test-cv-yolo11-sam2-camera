#!/usr/bin/env python3
"""
Test Processing Engine Registration with Correct Field Names
Tests the updated API client with proper field validation
"""

import sys
import requests
import json
import time
from pathlib import Path
from datetime import datetime
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "api-client"))

def get_auth_token(base_url):
    """Get authentication token"""
    login_data = {
        'email': 'admin@myrvm.com',
        'password': 'password'
    }
    
    try:
        response = requests.post(f"{base_url}/api/v2/auth/login", 
                               json=login_data, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('token')
    except Exception as e:
        print(f"❌ Login error: {e}")
    return None

def test_processing_engine_registration_with_correct_fields(base_url, token):
    """Test registering Jetson Orin with correct field names"""
    print("🤖 Testing processing engine registration with correct fields...")
    
    # Updated engine data with correct field names
    engine_data = {
        'name': 'Jetson Orin Nano - CV System',
        'type': 'nvidia_cuda',  # Valid type based on existing engines
        'server_address': '172.28.93.97',  # Required field
        'port': 5000,  # Required field
        'gpu_memory_limit': 8,
        'docker_gpu_passthrough': True,
        'model_path': '/models/yolo11n.pt',
        'processing_timeout': 30,
        'auto_failover': True,
        'is_active': True
    }
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.post(f"{base_url}/api/v2/processing-engines", 
                               json=engine_data, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            engine_id = data.get('data', {}).get('id')
            print(f"   ✅ Processing engine registered successfully")
            print(f"   Engine ID: {engine_id}")
            return engine_id
        else:
            print(f"   ❌ Failed to register processing engine: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_get_processing_engines(base_url, token):
    """Test getting list of processing engines"""
    print("\n📋 Testing get processing engines...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{base_url}/api/v2/processing-engines", 
                              headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            engines = data.get('data', [])
            print(f"   ✅ Retrieved {len(engines)} processing engines")
            
            # Show first few engines
            for i, engine in enumerate(engines[:3]):
                print(f"   Engine {i+1}: {engine.get('name', 'N/A')} (ID: {engine.get('id', 'N/A')})")
            
            return engines
        else:
            print(f"   ❌ Failed to get processing engines: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_processing_engine_types(base_url, token):
    """Test what processing engine types are valid"""
    print("\n🔍 Testing processing engine types...")
    
    # Common types to test (based on existing engines)
    types_to_test = [
        'nvidia_cuda',
        'edge_vision',
        'cloud_processing',
        'local_ai',
        'computer_vision',
        'jetson_orin',
        'edge_device'
    ]
    
    headers = {'Authorization': f'Bearer {token}'}
    
    for engine_type in types_to_test:
        test_data = {
            'name': f'Test Engine - {engine_type}',
            'type': engine_type,
            'server_address': '127.0.0.1',
            'port': 8080,
            'gpu_memory_limit': 8,
            'docker_gpu_passthrough': True,
            'model_path': '/models/yolo11n.pt',
            'processing_timeout': 30,
            'auto_failover': True,
            'is_active': True
        }
        
        try:
            response = requests.post(f"{base_url}/api/v2/processing-engines", 
                                   json=test_data, headers=headers, timeout=10)
            print(f"   Type '{engine_type}': {response.status_code}")
            
            if response.status_code == 201:
                print(f"   ✅ Valid type: {engine_type}")
                # Clean up - delete the test engine
                data = response.json()
                engine_id = data.get('data', {}).get('id')
                if engine_id:
                    delete_response = requests.delete(f"{base_url}/api/v2/processing-engines/{engine_id}", 
                                                    headers=headers, timeout=10)
                    print(f"   🗑️  Cleaned up test engine {engine_id}")
                break
            elif response.status_code == 422:
                print(f"   ❌ Invalid type: {engine_type}")
            else:
                print(f"   ⚠️  Unexpected response for {engine_type}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error testing type {engine_type}: {e}")

def main():
    """Main test function"""
    print("🚀 Processing Engine Registration Test")
    print("=" * 60)
    
    base_url = "http://172.28.233.83:8001"
    print(f"Testing with: {base_url}")
    
    # Get authentication token
    print("\n🔐 Getting authentication token...")
    token = get_auth_token(base_url)
    if not token:
        print("❌ Failed to get authentication token. Exiting...")
        return False
    
    print(f"✅ Authentication token obtained: {token[:50]}...")
    
    # Test results
    results = {}
    
    # Test 1: Get existing processing engines
    engines = test_get_processing_engines(base_url, token)
    results['get_engines'] = engines is not None
    
    # Test 2: Test valid engine types
    test_processing_engine_types(base_url, token)
    
    # Test 3: Register processing engine with correct fields
    engine_id = test_processing_engine_registration_with_correct_fields(base_url, token)
    results['register_engine'] = engine_id is not None
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PROCESSING ENGINE TEST SUMMARY:")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All processing engine tests passed!")
    else:
        print("⚠️  Some processing engine tests failed. Check the logs above for details.")
    
    # Save test results to log
    log_file = Path("../logs/processing_engine_test_results.log")
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, 'a') as f:
        timestamp = now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n[{timestamp}] Processing Engine Test Results:\n")
        f.write(f"  Total Tests: {total_tests}\n")
        f.write(f"  Passed: {passed_tests}\n")
        f.write(f"  Failed: {total_tests - passed_tests}\n")
        for test_name, result in results.items():
            f.write(f"  {test_name}: {'PASS' if result else 'FAIL'}\n")
        f.write("\n")
    
    print(f"📝 Test results saved to: {log_file}")
    
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
