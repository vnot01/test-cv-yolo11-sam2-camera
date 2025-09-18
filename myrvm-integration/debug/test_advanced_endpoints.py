#!/usr/bin/env python3
"""
Test Advanced API Endpoints from Jetson Orin
Tests the newly working advanced endpoints from server-side testing
"""

import sys
import requests
import json
import time
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

def test_trigger_processing(base_url, token, rvm_id=1):
    """Test trigger processing endpoint"""
    print("⚡ Testing trigger processing endpoint...")
    
    trigger_data = {
        'rvm_id': rvm_id,
        'processing_type': 'detection',
        'priority': 'normal'
    }
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.post(f"{base_url}/api/v2/trigger-processing", 
                               json=trigger_data, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Trigger processing successful")
            print(f"   Processing Request ID: {data.get('data', {}).get('processing_request_id', 'N/A')}")
            print(f"   Status: {data.get('data', {}).get('status', 'N/A')}")
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
    print("\n📊 Testing RVM status endpoint...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{base_url}/api/v2/rvm-status/{rvm_id}", 
                              headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ RVM status retrieved successfully")
            rvm_data = data.get('data', {}).get('rvm', {})
            print(f"   RVM Name: {rvm_data.get('name', 'N/A')}")
            print(f"   RVM Status: {rvm_data.get('status', 'N/A')}")
            return True
        else:
            print(f"   ❌ Failed to get RVM status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_processing_engine_assignment(base_url, token, engine_id=28, rvm_id=1):
    """Test processing engine assignment"""
    print("\n🔗 Testing processing engine assignment...")
    
    assignment_data = {
        'rvm_id': rvm_id,
        'priority': 'primary'
    }
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.post(f"{base_url}/api/v2/processing-engines/{engine_id}/assign", 
                               json=assignment_data, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Processing engine assigned successfully")
            print(f"   Message: {data.get('message', 'N/A')}")
            return True
        else:
            print(f"   ❌ Failed to assign processing engine: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_processing_history(base_url, token, rvm_id=1):
    """Test processing history endpoint"""
    print("\n📜 Testing processing history endpoint...")
    
    headers = {'Authorization': f'Bearer {token}'}
    params = {'rvm_id': rvm_id, 'limit': 5}
    
    try:
        response = requests.get(f"{base_url}/api/v2/detection-results/processing-history", 
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

def test_upload_detection_results(base_url, token, engine_id=28):
    """Test upload detection results with advanced fields"""
    print("\n📸 Testing upload detection results...")
    
    detection_data = {
        'rvm_id': 1,
        'image_path': '/storages/images/output/camera_yolo/results/images/detection_20250918_150800.jpg',
        'detections': [
            {
                'class': 'plastic_bottle',
                'confidence': 0.95,
                'bbox': [100, 100, 200, 200],
                'segmentation_mask': 'base64_encoded_mask_data'
            }
        ],
        'status': 'processed',
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

def main():
    """Main test function"""
    print("🚀 MyRVM Platform - Advanced Endpoints Test from Jetson Orin")
    print("=" * 70)
    
    base_url = "http://172.28.233.83:8001"
    print(f"Testing advanced endpoints with: {base_url}")
    
    # Get authentication token
    print("\n🔐 Getting authentication token...")
    token = get_auth_token(base_url)
    if not token:
        print("❌ Failed to get authentication token. Exiting...")
        return False
    
    print(f"✅ Authentication token obtained: {token[:50]}...")
    
    # Test results
    results = {}
    
    # Test 1: Trigger processing
    results['trigger_processing'] = test_trigger_processing(base_url, token)
    
    # Test 2: RVM status
    results['rvm_status'] = test_rvm_status(base_url, token)
    
    # Test 3: Processing engine assignment
    results['engine_assignment'] = test_processing_engine_assignment(base_url, token)
    
    # Test 4: Processing history
    results['processing_history'] = test_processing_history(base_url, token)
    
    # Test 5: Upload detection results
    result_id = test_upload_detection_results(base_url, token)
    results['upload_detection'] = result_id is not None
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 ADVANCED ENDPOINTS TEST SUMMARY:")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All advanced endpoint tests passed! Ready for real-time integration.")
    else:
        print("⚠️  Some advanced endpoint tests failed. Check the logs above for details.")
    
    # Save test results to log
    log_file = Path("../logs/advanced_endpoints_test_results.log")
    log_file.parent.mkdir(exist_ok=True)
    
    with open(log_file, 'a') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n[{timestamp}] Advanced Endpoints Test Results:\n")
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
