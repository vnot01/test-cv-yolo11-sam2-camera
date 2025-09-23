#!/usr/bin/env python3
"""
Quick Network Test for Jetson Orin
Simple network connectivity check for RVM-Jetson Installation Method
"""

import subprocess
import requests
import json
from datetime import datetime

def quick_network_test():
    """Quick network connectivity test"""
    print("🔍 JETSON ORIN QUICK NETWORK TEST")
    print("=" * 50)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # Test 1: USB Type-C Connection (192.168.55.1)
    print("1️⃣ Testing USB Type-C Connection (192.168.55.1)...")
    try:
        response = requests.get("http://192.168.55.1", timeout=3)
        if response.status_code == 200:
            print("   ✅ USB Type-C connection: ACTIVE")
            results['tests']['usb_connection'] = {'status': 'active', 'ip': '192.168.55.1'}
        else:
            print("   ❌ USB Type-C connection: INACTIVE")
            results['tests']['usb_connection'] = {'status': 'inactive', 'ip': '192.168.55.1'}
    except:
        print("   ❌ USB Type-C connection: NOT DETECTED")
        results['tests']['usb_connection'] = {'status': 'not_detected', 'ip': '192.168.55.1'}
    
    # Test 2: WiFi Connection
    print("2️⃣ Testing WiFi Connection...")
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi'], 
                              capture_output=True, text=True, timeout=5)
        wifi_connected = False
        current_ssid = None
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line and 'yes:' in line:
                    parts = line.split(':')
                    if len(parts) >= 2 and parts[1]:
                        wifi_connected = True
                        current_ssid = parts[1]
                        break
        
        if wifi_connected:
            print(f"   ✅ WiFi connection: CONNECTED to '{current_ssid}'")
            results['tests']['wifi'] = {'status': 'connected', 'ssid': current_ssid}
        else:
            print("   ❌ WiFi connection: NOT CONNECTED")
            results['tests']['wifi'] = {'status': 'not_connected'}
    except:
        print("   ❌ WiFi connection: ERROR")
        results['tests']['wifi'] = {'status': 'error'}
    
    # Test 3: Internet Connectivity
    print("3️⃣ Testing Internet Connectivity...")
    try:
        response = requests.get("https://www.google.com", timeout=5)
        if response.status_code == 200:
            print("   ✅ Internet: CONNECTED")
            results['tests']['internet'] = {'status': 'connected'}
        else:
            print("   ❌ Internet: NO ACCESS")
            results['tests']['internet'] = {'status': 'no_access'}
    except:
        print("   ❌ Internet: NOT AVAILABLE")
        results['tests']['internet'] = {'status': 'not_available'}
    
    # Test 4: MyRVM Platform Connection
    print("4️⃣ Testing MyRVM Platform Connection...")
    try:
        response = requests.get("http://100.123.143.87:8001/api/health-check", timeout=5)
        if response.status_code == 200:
            print("   ✅ MyRVM Platform: REACHABLE")
            results['tests']['myrvm_platform'] = {'status': 'reachable', 'url': 'http://100.123.143.87:8001'}
        else:
            print("   ❌ MyRVM Platform: UNREACHABLE")
            results['tests']['myrvm_platform'] = {'status': 'unreachable', 'url': 'http://100.123.143.87:8001'}
    except:
        print("   ❌ MyRVM Platform: CONNECTION FAILED")
        results['tests']['myrvm_platform'] = {'status': 'connection_failed', 'url': 'http://100.123.143.87:8001'}
    
    # Test 5: Network Interfaces
    print("5️⃣ Checking Network Interfaces...")
    try:
        result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            interfaces = []
            for line in result.stdout.split('\n'):
                if ':' in line and not line.startswith(' '):
                    interface_name = line.split(':')[1].strip()
                    if interface_name and interface_name != 'lo':
                        interfaces.append(interface_name)
            
            print(f"   📡 Active interfaces: {', '.join(interfaces)}")
            results['tests']['interfaces'] = {'status': 'detected', 'interfaces': interfaces}
        else:
            print("   ❌ Network interfaces: ERROR")
            results['tests']['interfaces'] = {'status': 'error'}
    except:
        print("   ❌ Network interfaces: ERROR")
        results['tests']['interfaces'] = {'status': 'error'}
    
    print()
    print("📊 SUMMARY")
    print("-" * 20)
    
    # Determine overall status
    usb_active = results['tests'].get('usb_connection', {}).get('status') == 'active'
    wifi_connected = results['tests'].get('wifi', {}).get('status') == 'connected'
    internet_available = results['tests'].get('internet', {}).get('status') == 'connected'
    platform_reachable = results['tests'].get('myrvm_platform', {}).get('status') == 'reachable'
    
    if usb_active:
        print("🔌 Connection Type: USB Type-C to Host (192.168.55.1)")
        print("   → Jetson is in setup mode via USB connection")
        print("   → Ready for initial configuration")
    elif wifi_connected:
        print("📶 Connection Type: WiFi Connection")
        if internet_available:
            print("   → WiFi connected with internet access")
            if platform_reachable:
                print("   → MyRVM Platform is reachable")
                print("   → Ready for RVM registration")
            else:
                print("   → MyRVM Platform is not reachable")
        else:
            print("   → WiFi connected but no internet access")
    else:
        print("❌ Connection Type: No Network Connection")
        print("   → No USB or WiFi connection detected")
        print("   → Check network configuration")
    
    print()
    print("💡 RECOMMENDATIONS:")
    
    if usb_active:
        print("   • Jetson is connected via USB Type-C")
        print("   • This is the default setup mode")
        print("   • Use web interface to configure WiFi")
        print("   • After WiFi setup, Jetson can register to MyRVM Platform")
    elif wifi_connected and internet_available:
        print("   • WiFi connection is working")
        print("   • Internet access is available")
        if platform_reachable:
            print("   • MyRVM Platform is reachable")
            print("   • Jetson is ready for RVM registration")
        else:
            print("   • MyRVM Platform is not reachable")
            print("   • Check server connectivity or firewall settings")
    elif wifi_connected and not internet_available:
        print("   • WiFi is connected but no internet access")
        print("   • Check WiFi router internet connection")
        print("   • Verify DNS settings")
    else:
        print("   • No network connection detected")
        print("   • Connect via USB Type-C for initial setup")
        print("   • Or configure WiFi connection")
    
    # Save results
    output_file = f"quick_network_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print()
    print(f"📄 Results saved to: {output_file}")
    print("=" * 50)
    
    return results

if __name__ == "__main__":
    quick_network_test()



