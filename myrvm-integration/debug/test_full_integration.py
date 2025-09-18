#!/usr/bin/env python3
"""
Full Integration Test for MyRVM Platform
Tests complete workflow from Jetson Orin to MyRVM Platform
"""

import sys
import requests
import json
import time
import os
from pathlib import Path
from datetime import datetime

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
                               json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('token')
    except Exception as e:
        print(f"❌ Login error: {e}")
    return None

def test_register_processing_engine(base_url, token):
    """Test registering Jetson Orin as processing engine"""
    print("🤖 Testing register processing engine...")
    
    engine_data = {
        'name': 'Jetson Orin Nano - CV System',
        'type': 'nvidia_cuda',
        'server_address': '172.28.93.97',
        'port': 5000,
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
                               json=engine_data, headers=headers, timeout=10)
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

def test_upload_detection_results(base_url, token, engine_id):
    """Test uploading detection results"""
    print("\n📸 Testing upload detection results...")
    
    # Create sample detection data
    detection_data = {
        'processing_engine_id': engine_id,
        'rvm_id': 1,
        'deposit_id': 1,
        'detection_type': 'yolo11',
        'confidence': 0.95,
        'objects_detected': [
            {
                'class': 'plastic_bottle',
                'confidence': 0.95,
                'bbox': [100, 100, 200, 200],
                'segmentation_mask': 'base64_encoded_mask_data'
            }
        ],
        'image_path': '/storages/images/output/camera_yolo/results/images/detection_20250918_150800.jpg',
        'processing_time': 1.5,
        'model_version': 'yolo11n.pt',
        'timestamp': datetime.now().isoformat()
    }
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.post(f"{base_url}/api/v2/detection-results", 
                               json=detection_data, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            result_id = data.get('data', {}).get('id')
            print(f"   ✅ Detection results uploaded successfully")
            print(f"   Result ID: {result_id}")
            return result_id
        else:
            print(f"   ❌ Failed to upload detection results: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_trigger_processing(base_url, token, rvm_id=1):
    """Test triggering processing workflow"""
    print("\n⚡ Testing trigger processing...")
    
    trigger_data = {
        'rvm_id': rvm_id,
        'trigger_type': 'manual',
        'source': 'jetson_orin_nano'
    }
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.post(f"{base_url}/api/v2/trigger-processing", 
                               json=trigger_data, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Processing triggered successfully")
            print(f"   Response: {data.get('message', 'N/A')}")
            return True
        else:
            print(f"   ❌ Failed to trigger processing: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_rvm_status(base_url, token, rvm_id=1):
    """Test RVM status endpoint"""
    print("\n📊 Testing RVM status...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{base_url}/api/v2/rvm-status/{rvm_id}", 
                              headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ RVM status retrieved successfully")
            print(f"   RVM Status: {data.get('data', {}).get('status', 'N/A')}")
            return True
        else:
            print(f"   ❌ Failed to get RVM status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_processing_history(base_url, token, rvm_id=1):
    """Test processing history endpoint"""
    print("\n📜 Testing processing history...")
    
    headers = {'Authorization': f'Bearer {token}'}
    params = {'rvm_id': rvm_id, 'limit': 5}
    
    try:
        response = requests.get(f"{base_url}/api/v2/processing-history", 
                              headers=headers, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            history = data.get('data', [])
            print(f"   ✅ Processing history retrieved successfully")
            print(f"   Found {len(history)} history records")
            return True
        else:
            print(f"   ❌ Failed to get processing history: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main integration test function"""
    print("🚀 MyRVM Platform - Full Integration Test")
    print("=" * 60)
    
    base_url = "http://172.28.233.83:8001"
    print(f"Testing complete workflow with: {base_url}")
    
    # Get authentication token
    print("\n🔐 Getting authentication token...")
    token = get_auth_token(base_url)
    if not token:
        print("❌ Failed to get authentication token. Exiting...")
        return False
    
    print(f"✅ Authentication token obtained: {token[:50]}...")
    
    # Test results
    results = {}
    
    # Test 1: Register processing engine
    engine_id = test_register_processing_engine(base_url, token)
    results['register_engine'] = engine_id is not None
    
    # Test 2: Upload detection results
    if engine_id:
        result_id = test_upload_detection_results(base_url, token, engine_id)
        results['upload_results'] = result_id is not None
    else:
        results['upload_results'] = False
    
    # Test 3: Trigger processing
    results['trigger_processing'] = test_trigger_processing(base_url, token)
    
    # Test 4: RVM status
    results['rvm_status'] = test_rvm_status(base_url, token)
    
    # Test 5: Processing history
    results['processing_history'] = test_processing_history(base_url, token)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST SUMMARY:")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All integration tests passed! Complete workflow is working.")
    else:
        print("⚠️  Some integration tests failed. Check the logs above for details.")
    
    # Save test results to log
    log_file = Path("../logs/integration_test_results.log")
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, 'a') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n[{timestamp}] Integration Test Results:\n")
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
