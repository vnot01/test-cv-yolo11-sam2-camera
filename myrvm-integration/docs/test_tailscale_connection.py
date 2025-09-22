#!/usr/bin/env python3
"""
Tailscale Connection Test Script
Tests connectivity between Jetson Orin and MyRVM Platform via Tailscale (primary) and ZeroTier (emergency)
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

# Tailscale Network Configuration (Primary)
TAILSCALE_CONFIG = {
    "rvm_ip": "100.117.234.2",
    "server_ip": "100.123.143.87",
    "server_port": 8001,
    "server_url": "http://100.123.143.87:8001",
    "tailscale_hostname": "myrvm-jetson"
}

# ZeroTier Network Configuration (Emergency)
ZEROTIER_CONFIG = {
    "rvm_ip": "172.28.93.97",
    "server_ip": "172.28.233.83",
    "server_port": 8001,
    "server_url": "http://172.28.233.83:8001"
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

def test_tailscale_network():
    """Test Tailscale network connectivity (Primary)"""
    print("🌐 Tailscale Network Connectivity Test (Primary)")
    print("=" * 50)
    
    # Test ping to RVM (Jetson Orin)
    print(f"\n1. Testing ping to RVM (Jetson Orin): {TAILSCALE_CONFIG['rvm_ip']}")
    rvm_ping_success = test_ping_connectivity(TAILSCALE_CONFIG['rvm_ip'])
    
    # Test ping to MyRVM Platform
    print(f"\n2. Testing ping to MyRVM Platform: {TAILSCALE_CONFIG['server_ip']}")
    platform_ping_success = test_ping_connectivity(TAILSCALE_CONFIG['server_ip'])
    
    # Test HTTP connection to MyRVM Platform
    print(f"\n3. Testing HTTP connection to MyRVM Platform")
    http_success = test_http_connectivity(TAILSCALE_CONFIG['server_url'])
    
    # Test specific API endpoints
    print(f"\n4. Testing API endpoints")
    api_endpoints = [
        "/api/health",
        "/api/v2/deposits",
        "/admin/edge-vision/rvm-status/1"
    ]
    
    api_results = {}
    for endpoint in api_endpoints:
        url = f"{TAILSCALE_CONFIG['server_url']}{endpoint}"
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

def test_zerotier_emergency():
    """Test ZeroTier network connectivity (Emergency)"""
    print("\n🌐 ZeroTier Network Connectivity Test (Emergency)")
    print("=" * 50)
    
    # Test ping to RVM (Jetson Orin)
    print(f"\n1. Testing ping to RVM (Jetson Orin): {ZEROTIER_CONFIG['rvm_ip']}")
    rvm_ping_success = test_ping_connectivity(ZEROTIER_CONFIG['rvm_ip'])
    
    # Test ping to MyRVM Platform
    print(f"\n2. Testing ping to MyRVM Platform: {ZEROTIER_CONFIG['server_ip']}")
    platform_ping_success = test_ping_connectivity(ZEROTIER_CONFIG['server_ip'])
    
    # Test HTTP connection to MyRVM Platform
    print(f"\n3. Testing HTTP connection to MyRVM Platform")
    http_success = test_http_connectivity(ZEROTIER_CONFIG['server_url'])
    
    return {
        "rvm_ping": rvm_ping_success,
        "platform_ping": platform_ping_success,
        "http_connection": http_success
    }

def update_config_with_tailscale():
    """Update config.json with Tailscale settings"""
    config_path = Path("main/config.json")
    
    if not config_path.exists():
        print("❌ config.json not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update with Tailscale settings
        config.update({
            "server_url": TAILSCALE_CONFIG['server_url'],
            "jetson_ip": TAILSCALE_CONFIG['rvm_ip'],
            "use_tunnel": True,
            "tunnel_type": "tailscale",
            "tailscale_network": TAILSCALE_CONFIG,
            "emergency_tunnel": {
                "type": "zerotier",
                "enabled": True,
                "zerotier_network": ZEROTIER_CONFIG
            }
        })
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ config.json updated with Tailscale settings")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config.json: {e}")
        return False

def test_api_client():
    """Test API client with Tailscale configuration"""
    print("\n5. Testing API Client")
    print("-" * 30)
    
    try:
        # Add parent directory to path for imports
        sys.path.append(str(Path(__file__).parent.parent))
        
        from api_client.myrvm_api_client import MyRVMAPIClient
        
        # Initialize API client
        client = MyRVMAPIClient(
            base_url=TAILSCALE_CONFIG['server_url'],
            use_tunnel=True
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
    print("🚀 Tailscale Connection Test for MyRVM Platform")
    print("=" * 60)
    print(f"RVM IP (Jetson Orin): {TAILSCALE_CONFIG['rvm_ip']}")
    print(f"Server IP: {TAILSCALE_CONFIG['server_ip']}:{TAILSCALE_CONFIG['server_port']}")
    print("=" * 60)
    
    # Run Tailscale connectivity tests (Primary)
    tailscale_results = test_tailscale_network()
    
    # Run ZeroTier connectivity tests (Emergency)
    zerotier_results = test_zerotier_emergency()
    
    # Test API client
    api_client_success = test_api_client()
    
    # Update configuration
    config_updated = update_config_with_tailscale()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print("🌐 TAILSCALE (Primary):")
    print(f"   🏓 RVM Ping: {'✅ PASS' if tailscale_results['rvm_ping'] else '❌ FAIL'}")
    print(f"   🏓 Server Ping: {'✅ PASS' if tailscale_results['platform_ping'] else '❌ FAIL'}")
    print(f"   🌐 HTTP Connection: {'✅ PASS' if tailscale_results['http_connection'] else '❌ FAIL'}")
    
    print("\n🌐 ZEROTIER (Emergency):")
    print(f"   🏓 RVM Ping: {'✅ PASS' if zerotier_results['rvm_ping'] else '❌ FAIL'}")
    print(f"   🏓 Server Ping: {'✅ PASS' if zerotier_results['platform_ping'] else '❌ FAIL'}")
    print(f"   🌐 HTTP Connection: {'✅ PASS' if zerotier_results['http_connection'] else '❌ FAIL'}")
    
    print(f"\n🔌 API Client: {'✅ PASS' if api_client_success else '❌ FAIL'}")
    print(f"⚙️  Config Updated: {'✅ PASS' if config_updated else '❌ FAIL'}")
    
    # API endpoints summary
    print(f"\n📡 API Endpoints (Tailscale):")
    for endpoint, result in tailscale_results['api_endpoints'].items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        status_code = result.get('status_code', 'N/A')
        print(f"   {endpoint}: {status} ({status_code})")
    
    # Overall result
    tailscale_primary_ok = (
        tailscale_results['rvm_ping'] and 
        tailscale_results['platform_ping'] and 
        tailscale_results['http_connection']
    )
    
    zerotier_emergency_ok = (
        zerotier_results['rvm_ping'] and 
        zerotier_results['platform_ping'] and 
        zerotier_results['http_connection']
    )
    
    all_tests_passed = tailscale_primary_ok and api_client_success and config_updated
    
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")
    print(f"   🌐 Tailscale (Primary): {'✅ READY' if tailscale_primary_ok else '❌ ISSUES'}")
    print(f"   🌐 ZeroTier (Emergency): {'✅ READY' if zerotier_emergency_ok else '❌ ISSUES'}")
    
    if all_tests_passed:
        print("\n🚀 Tailscale connection is ready!")
        print("Next steps:")
        print("1. Run: python3 debug/test_integration.py")
        print("2. Start: python3 main/jetson_main.py")
        if zerotier_emergency_ok:
            print("3. ZeroTier emergency backup is also ready")
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
