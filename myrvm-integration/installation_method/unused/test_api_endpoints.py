#!/usr/bin/env python3
"""
Test API Endpoints
Script untuk test API endpoints web GUI
"""

import requests
import json
from datetime import datetime

def test_api_endpoints():
    """Test semua API endpoints"""
    base_url = "http://localhost:8080"
    
    print("🧪 TESTING API ENDPOINTS")
    print("=" * 40)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {base_url}")
    print()
    
    endpoints = [
        "/api/status",
        "/api/network/status", 
        "/api/jetson/status",
        "/api/network/scan",
        "/api/server/test"
    ]
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'base_url': base_url,
        'tests': {}
    }
    
    for endpoint in endpoints:
        print(f"Testing: {endpoint}")
        try:
            if endpoint == "/api/server/test":
                # POST request for server test
                response = requests.post(f"{base_url}{endpoint}", 
                                       json={"server_url": "http://100.123.143.87:8001"},
                                       timeout=10)
            else:
                # GET request
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📊 Response: {json.dumps(data, indent=2)[:200]}...")
                results['tests'][endpoint] = {
                    'status': 'success',
                    'status_code': response.status_code,
                    'response': data
                }
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}...")
                results['tests'][endpoint] = {
                    'status': 'error',
                    'status_code': response.status_code,
                    'response': response.text
                }
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error: Web GUI not running")
            results['tests'][endpoint] = {
                'status': 'connection_error',
                'error': 'Web GUI not running'
            }
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results['tests'][endpoint] = {
                'status': 'error',
                'error': str(e)
            }
        
        print()
    
    # Summary
    print("=" * 40)
    print("📊 SUMMARY")
    print("=" * 40)
    
    success_count = sum(1 for test in results['tests'].values() if test['status'] == 'success')
    total_count = len(results['tests'])
    
    print(f"Successful: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 All API endpoints working correctly!")
    else:
        print("⚠️  Some API endpoints have issues")
        for endpoint, result in results['tests'].items():
            if result['status'] != 'success':
                print(f"   ❌ {endpoint}: {result.get('error', 'Unknown error')}")
    
    # Save results
    output_file = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    print("=" * 40)
    
    return results

if __name__ == "__main__":
    test_api_endpoints()



