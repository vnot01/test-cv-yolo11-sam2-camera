#!/usr/bin/env python3
"""
Test Web GUI
Script untuk test web GUI dan memastikan interface yang benar ditampilkan
"""

import requests
import json
from datetime import datetime

def test_web_gui():
    """Test web GUI endpoints"""
    base_url = "http://localhost:8080"
    
    print("🧪 TESTING WEB GUI")
    print("=" * 40)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {base_url}")
    print()
    
    # Test hardware detection
    print("1️⃣ Testing Hardware Detection...")
    try:
        response = requests.get(f"{base_url}/api/hardware/detect", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                hardware = data['data']
                print("   ✅ Hardware detection successful")
                print(f"   📱 CPU: {hardware.get('cpu', 'Unknown')}")
                print(f"   💾 Memory: {hardware.get('memory', 'Unknown')}")
                print(f"   🎮 GPU: {hardware.get('gpu', 'Unknown')}")
                print(f"   📷 Camera: {hardware.get('camera', 'Unknown')}")
                
                network = hardware.get('network', {})
                print(f"   🌐 Network Interface: {network.get('interface', 'Unknown')}")
                print(f"   📶 Network Status: {network.get('status', 'Unknown')}")
                print(f"   🔗 IP Addresses: {network.get('ip_addresses', [])}")
                
                # Check if interface is correct
                if network.get('interface') == 'wlP1p1s0':
                    print("   ✅ Network interface is correct (wlP1p1s0)")
                else:
                    print(f"   ❌ Network interface is incorrect: {network.get('interface')}")
                
                # Check if status is correct
                if network.get('status') == 'connected':
                    print("   ✅ Network status is correct (connected)")
                else:
                    print(f"   ❌ Network status is incorrect: {network.get('status')}")
                    
            else:
                print(f"   ❌ Hardware detection failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # Test Jetson status
    print("2️⃣ Testing Jetson Status...")
    try:
        response = requests.get(f"{base_url}/api/jetson/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                jetson = data['data']
                print("   ✅ Jetson status successful")
                print(f"   🔌 Current Stage: {jetson.get('current_stage', 'Unknown')}")
                print(f"   🚀 Setup Ready: {jetson.get('setup_ready', False)}")
                
                tests = jetson.get('tests', {})
                for test_name, test_result in tests.items():
                    status = "✅" if test_result.get('connected', test_result.get('reachable', False)) else "❌"
                    print(f"   {status} {test_name}: {test_result.get('description', 'Unknown')}")
                    
            else:
                print(f"   ❌ Jetson status failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # Test network scan
    print("3️⃣ Testing Network Scan...")
    try:
        response = requests.get(f"{base_url}/api/network/scan", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                networks = data['data']
                print(f"   ✅ Network scan successful - Found {len(networks)} networks")
                for network in networks[:3]:  # Show first 3 networks
                    print(f"   📶 {network.get('ssid', 'Unknown')} - Signal: {network.get('signal', 'Unknown')}%")
            else:
                print(f"   ❌ Network scan failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    print("=" * 40)
    print("🎯 SUMMARY")
    print("=" * 40)
    print("✅ Hardware detection should show:")
    print("   - Interface: wlP1p1s0 (not wlan0)")
    print("   - Status: connected")
    print("   - IP: 192.168.1.11")
    print()
    print("✅ Jetson status should show:")
    print("   - Current Stage: PLATFORM_ACCESS")
    print("   - Setup Ready: true")
    print("   - All tests should be successful")
    print()
    print("🌐 Web GUI should now display correct interface names!")

if __name__ == "__main__":
    test_web_gui()



