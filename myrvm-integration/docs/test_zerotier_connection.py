#!/usr/bin/env python3
"""
ZeroTier Connection Test Script
Tests connectivity between Jetson Orin and MyRVM Platform via ZeroTier
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

# ZeroTier Network Configuration
ZEROTIER_CONFIG = {
    "rvm_ip": "172.28.93.97",
    "platform_ip": "172.28.233.83",
    "platform_port": 8001,
    "platform_url": "http://172.28.233.83:8001"
}

def test_ping_connectivity(ip_address, count=4):
    """Test ping connectivity to IP address"""
    print(f"🏓 Testing ping to {ip_address}...")
    
    try:
        result = subprocess.run(
            ['ping', '-c', str(count), ip_address],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ Ping successful to {ip_address}")
            # Extract ping statistics
            lines = result.stdout.split('\n')
            for line in lines:
                if 'packets transmitted' in line:
                    print(f"   📊 {line.strip()}")
                elif 'rtt min/avg/max' in line:
                    print(f"   ⏱️  {line.strip()}")
            return True
        else:
            print(f"❌ Ping failed to {ip_address}")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Ping timeout to {ip_address}")
        return False
    except Exception as e:
        print(f"❌ Ping error: {e}")
        return False

def test_http_connectivity(url, timeout=10):
    """Test HTTP connectivity to URL"""
    print(f"🌐 Testing HTTP connection to {url}...")
    
    try:
        response = requests.get(url, timeout=timeout)
        print(f"✅ HTTP connection successful")
        print(f"   📊 Status: {response.status_code}")
        print(f"   📏 Content-Length: {len(response.content)} bytes")
        
        # Check if it's a valid response
        if response.status_code in [200, 302, 404]:  # 404 is OK for /api/health if not implemented
            return True
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed to {url}")
        return False
    except requests.exceptions.Timeout:
        print(f"⏰ Connection timeout to {url}")
        return False
    except Exception as e:
        print(f"❌ HTTP error: {e}")
        return False

def test_zerotier_network():
    """Test ZeroTier network connectivity"""
    print("🌐 ZeroTier Network Connectivity Test")
    print("=" * 50)
    
    # Test ping to RVM (Jetson Orin)
    print(f"\n1. Testing ping to RVM (Jetson Orin): {ZEROTIER_CONFIG['rvm_ip']}")
    rvm_ping_success = test_ping_connectivity(ZEROTIER_CONFIG['rvm_ip'])
    
    # Test ping to MyRVM Platform
    print(f"\n2. Testing ping to MyRVM Platform: {ZEROTIER_CONFIG['platform_ip']}")
    platform_ping_success = test_ping_connectivity(ZEROTIER_CONFIG['platform_ip'])
    
    # Test HTTP connection to MyRVM Platform
    print(f"\n3. Testing HTTP connection to MyRVM Platform")
    http_success = test_http_connectivity(ZEROTIER_CONFIG['platform_url'])
    
    # Test specific API endpoints
    print(f"\n4. Testing API endpoints")
    api_endpoints = [
        "/api/health",
        "/api/v2/deposits",
        "/admin/edge-vision/rvm-status/1"
    ]
    
    api_results = {}
    for endpoint in api_endpoints:
        url = f"{ZEROTIER_CONFIG['platform_url']}{endpoint}"
        print(f"   Testing {endpoint}...")
        try:
            response = requests.get(url, timeout=5)
            api_results[endpoint] = {
                "status_code": response.status_code,
                "success": response.status_code in [200, 201, 202, 404]  # 404 is OK if not implemented
            }
            print(f"   ✅ {endpoint}: {response.status_code}")
        except Exception as e:
            api_results[endpoint] = {
                "status_code": None,
                "success": False,
                "error": str(e)
            }
            print(f"   ❌ {endpoint}: {e}")
    
    return {
        "rvm_ping": rvm_ping_success,
        "platform_ping": platform_ping_success,
        "http_connection": http_success,
        "api_endpoints": api_results
    }

def update_config_with_zerotier():
    """Update config.json with ZeroTier settings"""
    config_path = Path("main/config.json")
    
    if not config_path.exists():
        print("❌ config.json not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update with ZeroTier settings
        config.update({
            "myrvm_base_url": ZEROTIER_CONFIG['platform_url'],
            "jetson_ip": ZEROTIER_CONFIG['rvm_ip'],
            "use_tunnel": False,
            "tunnel_type": "zerotier",
            "zerotier_network": ZEROTIER_CONFIG
        })
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ config.json updated with ZeroTier settings")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config.json: {e}")
        return False

def test_api_client():
    """Test API client with ZeroTier configuration"""
    print("\n5. Testing API Client")
    print("-" * 30)
    
    try:
        # Add current directory to path for imports
        sys.path.append(str(Path(__file__).parent))
        
        from api_client.myrvm_api_client import MyRVMAPIClient
        
        # Initialize API client
        client = MyRVMAPIClient(
            base_url=ZEROTIER_CONFIG['platform_url'],
            use_tunnel=False
        )
        
        # Test connectivity
        success, response = client.test_connectivity()
        
        if success:
            print("✅ API Client connectivity test successful")
            print(f"   Response: {response}")
        else:
            print("❌ API Client connectivity test failed")
            print(f"   Error: {response}")
        
        return success
        
    except ImportError as e:
        print(f"❌ Cannot import API client: {e}")
        return False
    except Exception as e:
        print(f"❌ API Client test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 ZeroTier Connection Test for MyRVM Platform")
    print("=" * 60)
    print(f"RVM IP (Jetson Orin): {ZEROTIER_CONFIG['rvm_ip']}")
    print(f"Platform IP: {ZEROTIER_CONFIG['platform_ip']}:{ZEROTIER_CONFIG['platform_port']}")
    print("=" * 60)
    
    # Run connectivity tests
    results = test_zerotier_network()
    
    # Test API client
    api_client_success = test_api_client()
    
    # Update configuration
    config_updated = update_config_with_zerotier()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print(f"🏓 RVM Ping: {'✅ PASS' if results['rvm_ping'] else '❌ FAIL'}")
    print(f"🏓 Platform Ping: {'✅ PASS' if results['platform_ping'] else '❌ FAIL'}")
    print(f"🌐 HTTP Connection: {'✅ PASS' if results['http_connection'] else '❌ FAIL'}")
    print(f"🔌 API Client: {'✅ PASS' if api_client_success else '❌ FAIL'}")
    print(f"⚙️  Config Updated: {'✅ PASS' if config_updated else '❌ FAIL'}")
    
    # API endpoints summary
    print(f"\n📡 API Endpoints:")
    for endpoint, result in results['api_endpoints'].items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        status_code = result.get('status_code', 'N/A')
        print(f"   {endpoint}: {status} ({status_code})")
    
    # Overall result
    all_tests_passed = (
        results['rvm_ping'] and 
        results['platform_ping'] and 
        results['http_connection'] and
        api_client_success and
        config_updated
    )
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")
    
    if all_tests_passed:
        print("\n🚀 ZeroTier connection is ready!")
        print("Next steps:")
        print("1. Run: python3 debug/test_integration.py")
        print("2. Start: python3 main/jetson_main.py")
    else:
        print("\n⚠️  Please fix the failed tests before proceeding")
    
    return all_tests_passed

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
