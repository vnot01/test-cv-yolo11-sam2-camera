#!/usr/bin/env python3
"""
Jetson Orin Network Detector
Script untuk mendeteksi status koneksi Jetson Orin dalam skenario setup RVM
"""

import subprocess
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class JetsonNetworkDetector:
    """Detector untuk status koneksi Jetson Orin"""
    
    def __init__(self):
        self.jetson_usb_ip = "192.168.55.1"  # Default IP USB Type-C to Host
        self.myrvm_platform_url = "http://100.123.143.87:8001"
        self.setup_stages = [
            "USB_CONNECTION",      # Stage 1: Koneksi USB Type-C ke laptop teknisi
            "WIFI_CONNECTION",     # Stage 2: Koneksi WiFi (tanpa internet)
            "INTERNET_ACCESS",     # Stage 3: Koneksi WiFi dengan internet
            "PLATFORM_ACCESS"      # Stage 4: Akses ke MyRVM Platform
        ]
    
    def detect_jetson_status(self) -> Dict[str, Any]:
        """Deteksi status koneksi Jetson secara menyeluruh"""
        print("🔍 JETSON ORIN NETWORK DETECTOR")
        print("=" * 50)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'jetson_ip': self.jetson_usb_ip,
            'myrvm_platform': self.myrvm_platform_url,
            'current_stage': None,
            'setup_ready': False,
            'tests': {}
        }
        
        # Test 1: USB Type-C Connection (Stage 1)
        print("1️⃣ STAGE 1: USB Type-C Connection")
        print(f"   Testing connection to Jetson at {self.jetson_usb_ip}...")
        usb_result = self._test_usb_connection()
        results['tests']['usb_connection'] = usb_result
        self._print_test_result("USB Type-C", usb_result)
        
        # Test 2: WiFi Connection (Stage 2)
        print("\n2️⃣ STAGE 2: WiFi Connection")
        print("   Checking WiFi connection status...")
        wifi_result = self._test_wifi_connection()
        results['tests']['wifi_connection'] = wifi_result
        self._print_test_result("WiFi Connection", wifi_result)
        
        # Test 3: Internet Access (Stage 3)
        print("\n3️⃣ STAGE 3: Internet Access")
        print("   Testing internet connectivity...")
        internet_result = self._test_internet_access()
        results['tests']['internet_access'] = internet_result
        self._print_test_result("Internet Access", internet_result)
        
        # Test 4: MyRVM Platform Access (Stage 4)
        print("\n4️⃣ STAGE 4: MyRVM Platform Access")
        print(f"   Testing connection to MyRVM Platform...")
        platform_result = self._test_platform_access()
        results['tests']['platform_access'] = platform_result
        self._print_test_result("MyRVM Platform", platform_result)
        
        # Determine current stage and setup readiness
        current_stage, setup_ready = self._determine_setup_stage(results['tests'])
        results['current_stage'] = current_stage
        results['setup_ready'] = setup_ready
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _test_usb_connection(self) -> Dict[str, Any]:
        """Test koneksi USB Type-C ke Jetson"""
        try:
            # Test HTTP connection to Jetson
            response = requests.get(f"http://{self.jetson_usb_ip}", timeout=3)
            
            return {
                'connected': True,
                'ip': self.jetson_usb_ip,
                'status_code': response.status_code,
                'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2),
                'stage': 'USB_CONNECTION',
                'description': 'Jetson terhubung via USB Type-C ke laptop teknisi'
            }
        except requests.exceptions.ConnectTimeout:
            return {
                'connected': False,
                'ip': self.jetson_usb_ip,
                'error': 'Connection timeout',
                'stage': 'USB_CONNECTION',
                'description': 'Jetson tidak terdeteksi via USB Type-C'
            }
        except requests.exceptions.ConnectionError:
            return {
                'connected': False,
                'ip': self.jetson_usb_ip,
                'error': 'Connection refused',
                'stage': 'USB_CONNECTION',
                'description': 'Jetson tidak terhubung via USB Type-C'
            }
        except Exception as e:
            return {
                'connected': False,
                'ip': self.jetson_usb_ip,
                'error': str(e),
                'stage': 'USB_CONNECTION',
                'description': 'Error testing USB connection'
            }
    
    def _test_wifi_connection(self) -> Dict[str, Any]:
        """Test koneksi WiFi"""
        try:
            # Check WiFi status using nmcli
            result = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL,IP4.ADDRESS', 'dev', 'wifi'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line and 'yes:' in line:
                        parts = line.split(':')
                        if len(parts) >= 4 and parts[1]:  # SSID exists
                            return {
                                'connected': True,
                                'ssid': parts[1],
                                'signal_strength': int(parts[2]) if parts[2].isdigit() else None,
                                'ip_address': parts[3].split('/')[0] if parts[3] else None,
                                'stage': 'WIFI_CONNECTION',
                                'description': f'WiFi terhubung ke "{parts[1]}"'
                            }
            
            # Fallback: check using iwconfig
            result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'ESSID:' in line:
                        essid = line.split('ESSID:')[1].strip().strip('"')
                        if essid and essid != 'off/any':
                            return {
                                'connected': True,
                                'ssid': essid,
                                'signal_strength': None,
                                'ip_address': None,
                                'stage': 'WIFI_CONNECTION',
                                'description': f'WiFi terhubung ke "{essid}"'
                            }
            
            return {
                'connected': False,
                'error': 'No WiFi connection found',
                'stage': 'WIFI_CONNECTION',
                'description': 'WiFi tidak terhubung ke jaringan apapun'
            }
            
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'stage': 'WIFI_CONNECTION',
                'description': 'Error checking WiFi connection'
            }
    
    def _test_internet_access(self) -> Dict[str, Any]:
        """Test akses internet"""
        test_urls = [
            'https://www.google.com',
            'https://httpbin.org/get',
            'https://www.cloudflare.com'
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return {
                        'connected': True,
                        'test_url': url,
                        'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2),
                        'stage': 'INTERNET_ACCESS',
                        'description': 'Internet tersedia dan dapat diakses'
                    }
            except:
                continue
        
        return {
            'connected': False,
            'error': 'No internet connectivity',
            'stage': 'INTERNET_ACCESS',
            'description': 'WiFi terhubung tapi tidak ada akses internet'
        }
    
    def _test_platform_access(self) -> Dict[str, Any]:
        """Test akses ke MyRVM Platform"""
        try:
            response = requests.get(f"{self.myrvm_platform_url}/api/health-check", timeout=10)
            
            return {
                'connected': True,
                'url': self.myrvm_platform_url,
                'response_time_ms': round(response.elapsed.total_seconds() * 1000, 2),
                'status_code': response.status_code,
                'stage': 'PLATFORM_ACCESS',
                'description': 'MyRVM Platform dapat diakses'
            }
        except requests.exceptions.ConnectTimeout:
            return {
                'connected': False,
                'url': self.myrvm_platform_url,
                'error': 'Connection timeout',
                'stage': 'PLATFORM_ACCESS',
                'description': 'MyRVM Platform tidak dapat diakses (timeout)'
            }
        except requests.exceptions.ConnectionError:
            return {
                'connected': False,
                'url': self.myrvm_platform_url,
                'error': 'Connection refused',
                'stage': 'PLATFORM_ACCESS',
                'description': 'MyRVM Platform tidak dapat diakses (connection refused)'
            }
        except Exception as e:
            return {
                'connected': False,
                'url': self.myrvm_platform_url,
                'error': str(e),
                'stage': 'PLATFORM_ACCESS',
                'description': 'Error testing MyRVM Platform access'
            }
    
    def _print_test_result(self, test_name: str, result: Dict[str, Any]):
        """Print hasil test dengan format yang jelas"""
        if result.get('connected', False):
            print(f"   ✅ {test_name}: BERHASIL")
            if 'description' in result:
                print(f"      {result['description']}")
            if 'ssid' in result:
                print(f"      SSID: {result['ssid']}")
            if 'ip_address' in result and result['ip_address']:
                print(f"      IP: {result['ip_address']}")
            if 'response_time_ms' in result:
                print(f"      Response Time: {result['response_time_ms']}ms")
        else:
            print(f"   ❌ {test_name}: GAGAL")
            if 'description' in result:
                print(f"      {result['description']}")
            if 'error' in result:
                print(f"      Error: {result['error']}")
    
    def _determine_setup_stage(self, tests: Dict[str, Any]) -> tuple:
        """Tentukan stage setup saat ini dan apakah siap untuk deployment"""
        usb_connected = tests.get('usb_connection', {}).get('connected', False)
        wifi_connected = tests.get('wifi_connection', {}).get('connected', False)
        internet_available = tests.get('internet_access', {}).get('connected', False)
        platform_accessible = tests.get('platform_access', {}).get('connected', False)
        
        if platform_accessible and internet_available and wifi_connected:
            return "PLATFORM_ACCESS", True  # Siap untuk deployment
        elif internet_available and wifi_connected:
            return "INTERNET_ACCESS", False  # Internet ada, tapi platform tidak bisa diakses
        elif wifi_connected:
            return "WIFI_CONNECTION", False  # WiFi terhubung tapi tidak ada internet
        elif usb_connected:
            return "USB_CONNECTION", False  # Hanya USB connection
        else:
            return "NO_CONNECTION", False  # Tidak ada koneksi sama sekali
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print ringkasan status setup"""
        print("\n" + "=" * 50)
        print("📊 RINGKASAN STATUS SETUP JETSON")
        print("=" * 50)
        
        current_stage = results['current_stage']
        setup_ready = results['setup_ready']
        
        # Status berdasarkan stage
        stage_descriptions = {
            "NO_CONNECTION": "❌ TIDAK ADA KONEKSI",
            "USB_CONNECTION": "🔌 KONEKSI USB TYPE-C",
            "WIFI_CONNECTION": "📶 KONEKSI WIFI (TANPA INTERNET)",
            "INTERNET_ACCESS": "🌐 AKSES INTERNET (PLATFORM TIDAK TERSEDIA)",
            "PLATFORM_ACCESS": "🚀 SIAP DEPLOYMENT"
        }
        
        print(f"Status Saat Ini: {stage_descriptions.get(current_stage, 'UNKNOWN')}")
        print(f"Setup Ready: {'✅ YA' if setup_ready else '❌ BELUM'}")
        print()
        
        # Rekomendasi berdasarkan stage
        print("💡 REKOMENDASI:")
        
        if current_stage == "NO_CONNECTION":
            print("   • Jetson tidak terdeteksi sama sekali")
            print("   • Pastikan kabel USB Type-C terhubung dengan benar")
            print("   • Periksa apakah Jetson dalam mode USB gadget")
            print("   • Restart Jetson jika diperlukan")
            
        elif current_stage == "USB_CONNECTION":
            print("   • Jetson terhubung via USB Type-C (192.168.55.1)")
            print("   • Ini adalah mode setup awal")
            print("   • Gunakan web interface untuk konfigurasi WiFi")
            print("   • Setelah WiFi dikonfigurasi, Jetson akan terhubung ke internet")
            
        elif current_stage == "WIFI_CONNECTION":
            print("   • WiFi sudah terhubung tapi tidak ada internet")
            print("   • Periksa koneksi internet router WiFi")
            print("   • Periksa pengaturan DNS")
            print("   • Pastikan router terhubung ke internet")
            
        elif current_stage == "INTERNET_ACCESS":
            print("   • Internet tersedia tapi MyRVM Platform tidak dapat diakses")
            print("   • Periksa koneksi ke server MyRVM Platform")
            print("   • Periksa firewall dan routing")
            print("   • Pastikan server MyRVM Platform sedang berjalan")
            
        elif current_stage == "PLATFORM_ACCESS":
            print("   • Semua koneksi berfungsi dengan baik")
            print("   • Jetson siap untuk registrasi ke MyRVM Platform")
            print("   • Dapat melanjutkan ke tahap deployment")
            print("   • RVM dapat didaftarkan dengan identitas yang unik")
        
        print()
        print("🔄 ALUR SETUP YANG BENAR:")
        print("   1. USB Type-C → 2. WiFi → 3. Internet → 4. MyRVM Platform → 5. Deployment")
        
        # Save results
        output_file = f"jetson_network_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Hasil detail disimpan ke: {output_file}")
        print("=" * 50)

def main():
    """Main function"""
    detector = JetsonNetworkDetector()
    results = detector.detect_jetson_status()
    
    # Return exit code based on setup readiness
    return 0 if results['setup_ready'] else 1

if __name__ == "__main__":
    exit(main())





