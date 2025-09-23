#!/usr/bin/env python3
"""
Quick Jetson Connection Check
Script sederhana untuk mengecek status koneksi Jetson Orin
"""

import requests
import subprocess
import json
from datetime import datetime

def check_jetson_connection():
    """Quick check status koneksi Jetson"""
    print("🔍 QUICK JETSON CONNECTION CHECK")
    print("=" * 40)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    jetson_ip = "192.168.55.1"
    myrvm_platform = "http://100.123.143.87:8001"
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'jetson_ip': jetson_ip,
        'myrvm_platform': myrvm_platform,
        'status': {}
    }
    
    # 1. Check USB Type-C Connection
    print("1️⃣ USB Type-C Connection (192.168.55.1)")
    try:
        response = requests.get(f"http://{jetson_ip}", timeout=2)
        print(f"   ✅ Jetson terdeteksi via USB Type-C")
        print(f"   📡 Response: {response.status_code} ({response.elapsed.total_seconds()*1000:.0f}ms)")
        results['status']['usb_connection'] = 'connected'
        connection_type = "USB Type-C"
    except:
        print(f"   ❌ Jetson tidak terdeteksi via USB Type-C")
        results['status']['usb_connection'] = 'not_connected'
        connection_type = "Unknown"
    
    # 2. Check WiFi Connection
    print("\n2️⃣ WiFi Connection")
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi'], 
                              capture_output=True, text=True, timeout=3)
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
            print(f"   ✅ WiFi terhubung ke '{current_ssid}'")
            results['status']['wifi_connection'] = 'connected'
            results['status']['wifi_ssid'] = current_ssid
            if connection_type == "Unknown":
                connection_type = "WiFi"
        else:
            print("   ❌ WiFi tidak terhubung")
            results['status']['wifi_connection'] = 'not_connected'
    except:
        print("   ❌ Error checking WiFi")
        results['status']['wifi_connection'] = 'error'
    
    # 3. Check Internet Access
    print("\n3️⃣ Internet Access")
    try:
        response = requests.get("https://www.google.com", timeout=3)
        if response.status_code == 200:
            print("   ✅ Internet tersedia")
            results['status']['internet_access'] = 'available'
        else:
            print("   ❌ Internet tidak tersedia")
            results['status']['internet_access'] = 'not_available'
    except:
        print("   ❌ Internet tidak dapat diakses")
        results['status']['internet_access'] = 'not_available'
    
    # 4. Check MyRVM Platform
    print("\n4️⃣ MyRVM Platform")
    try:
        response = requests.get(f"{myrvm_platform}/api/health-check", timeout=5)
        if response.status_code == 200:
            print("   ✅ MyRVM Platform dapat diakses")
            results['status']['myrvm_platform'] = 'accessible'
        else:
            print("   ❌ MyRVM Platform tidak dapat diakses")
            results['status']['myrvm_platform'] = 'not_accessible'
    except:
        print("   ❌ MyRVM Platform tidak dapat diakses")
        results['status']['myrvm_platform'] = 'not_accessible'
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 SUMMARY")
    print("=" * 40)
    
    usb_ok = results['status'].get('usb_connection') == 'connected'
    wifi_ok = results['status'].get('wifi_connection') == 'connected'
    internet_ok = results['status'].get('internet_access') == 'available'
    platform_ok = results['status'].get('myrvm_platform') == 'accessible'
    
    print(f"Connection Type: {connection_type}")
    
    if usb_ok and not wifi_ok:
        print("Status: 🔌 SETUP MODE (USB Type-C)")
        print("Action: Gunakan web interface untuk setup WiFi")
    elif wifi_ok and not internet_ok:
        print("Status: 📶 WIFI CONNECTED (No Internet)")
        print("Action: Periksa koneksi internet router")
    elif wifi_ok and internet_ok and not platform_ok:
        print("Status: 🌐 INTERNET AVAILABLE (Platform Unreachable)")
        print("Action: Periksa koneksi ke MyRVM Platform")
    elif wifi_ok and internet_ok and platform_ok:
        print("Status: 🚀 READY FOR DEPLOYMENT")
        print("Action: Jetson siap untuk registrasi RVM")
    else:
        print("Status: ❌ NO CONNECTION")
        print("Action: Periksa koneksi USB Type-C atau WiFi")
    
    # Save results
    output_file = f"jetson_connection_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    print("=" * 40)
    
    return results

if __name__ == "__main__":
    check_jetson_connection()
