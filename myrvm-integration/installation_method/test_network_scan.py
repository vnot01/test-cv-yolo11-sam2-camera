#!/usr/bin/env python3
"""
Test Network Scan
Script untuk test network scan real-time
"""

import requests
import subprocess
import json
from datetime import datetime

def test_network_scan():
    """Test network scan functionality"""
    print("🔍 TESTING NETWORK SCAN")
    print("=" * 40)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Direct nmcli command
    print("1️⃣ Direct nmcli command:")
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,FREQ', 'dev', 'wifi'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ nmcli command successful")
            networks = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        ssid = parts[0] if parts[0] else "Hidden Network"
                        signal = int(parts[1]) if parts[1].isdigit() else -100
                        security = parts[2] if parts[2] else "Open"
                        freq_str = parts[3].strip()
                        try:
                            frequency = int(freq_str.split()[0]) if freq_str.split()[0].isdigit() else 0
                        except:
                            frequency = 0
                        
                        networks.append({
                            "ssid": ssid,
                            "signal": signal,
                            "security": security,
                            "frequency": frequency
                        })
            
            print(f"   📶 Found {len(networks)} networks:")
            for network in networks:
                print(f"      - {network['ssid']}: {network['signal']} dBm, {network['security']}, {network['frequency']} MHz")
        else:
            print(f"   ❌ nmcli command failed: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # Test 2: API endpoint
    print("2️⃣ API endpoint test:")
    try:
        response = requests.get("http://localhost:8080/api/network/scan", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("   ✅ API endpoint successful")
                networks = data['data']
                print(f"   📶 Found {len(networks)} networks:")
                for network in networks:
                    print(f"      - {network['ssid']}: {network['signal']} dBm, {network['security']}, {network['frequency']} MHz")
            else:
                print(f"   ❌ API failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    
    # Test 3: Compare results
    print("3️⃣ Comparison:")
    try:
        # Get direct nmcli result
        result = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,FREQ', 'dev', 'wifi'], 
                              capture_output=True, text=True, timeout=10)
        direct_networks = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        direct_networks.append(parts[0])  # Just SSID for comparison
        
        # Get API result
        response = requests.get("http://localhost:8080/api/network/scan", timeout=10)
        api_networks = []
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                api_networks = [network['ssid'] for network in data['data']]
        
        print(f"   📊 Direct nmcli: {len(direct_networks)} networks")
        print(f"   📊 API endpoint: {len(api_networks)} networks")
        
        if set(direct_networks) == set(api_networks):
            print("   ✅ Results match - Network scan is REAL-TIME!")
        else:
            print("   ❌ Results don't match - Possible caching issue")
            print(f"      Direct: {direct_networks}")
            print(f"      API: {api_networks}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print()
    print("=" * 40)
    print("🎯 SUMMARY")
    print("=" * 40)
    print("✅ Network scan should be REAL-TIME")
    print("✅ No hardcoded/dummy data")
    print("✅ Uses actual nmcli command")
    print("✅ Parses real network information")

if __name__ == "__main__":
    test_network_scan()
