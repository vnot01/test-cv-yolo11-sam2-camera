#!/usr/bin/env python3
"""
Network Test Script for Jetson Orin
Comprehensive network connectivity testing for RVM-Jetson Installation Method
"""

import subprocess
import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NetworkTester:
    """Comprehensive network testing for Jetson Orin"""
    
    def __init__(self):
        self.test_results = {}
        self.jetson_default_ip = "192.168.55.1"  # USB Type-C to Host default IP
        self.myrvm_platform_url = "http://100.123.143.87:8001"
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all network tests"""
        logger.info("Starting comprehensive network tests...")
        
        start_time = datetime.now()
        
        # Test 1: Network Interface Detection
        logger.info("Test 1: Detecting network interfaces...")
        self.test_results['interfaces'] = self.test_network_interfaces()
        
        # Test 2: USB Type-C Connection Detection
        logger.info("Test 2: Checking USB Type-C connection...")
        self.test_results['usb_connection'] = self.test_usb_connection()
        
        # Test 3: WiFi Status
        logger.info("Test 3: Checking WiFi status...")
        self.test_results['wifi_status'] = self.test_wifi_status()
        
        # Test 4: Internet Connectivity
        logger.info("Test 4: Testing internet connectivity...")
        self.test_results['internet'] = self.test_internet_connectivity()
        
        # Test 5: MyRVM Platform Connection
        logger.info("Test 5: Testing MyRVM Platform connection...")
        self.test_results['myrvm_platform'] = self.test_myrvm_platform()
        
        # Test 6: Network Configuration
        logger.info("Test 6: Checking network configuration...")
        self.test_results['network_config'] = self.test_network_configuration()
        
        # Test 7: DNS Resolution
        logger.info("Test 7: Testing DNS resolution...")
        self.test_results['dns'] = self.test_dns_resolution()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = self.generate_summary()
        
        return {
            'timestamp': start_time.isoformat(),
            'duration_seconds': duration,
            'summary': summary,
            'results': self.test_results
        }
    
    def test_network_interfaces(self) -> Dict[str, Any]:
        """Test network interfaces detection"""
        try:
            # Get network interfaces using ip command
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                interfaces = []
                current_interface = {}
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    
                    # Interface name
                    if line and not line.startswith(' ') and ':' in line:
                        if current_interface:
                            interfaces.append(current_interface)
                        interface_name = line.split(':')[1].strip()
                        current_interface = {
                            'name': interface_name,
                            'status': 'down',
                            'ip_addresses': [],
                            'mac_address': None
                        }
                    
                    # Interface status
                    elif 'state' in line:
                        if 'UP' in line:
                            current_interface['status'] = 'up'
                    
                    # IP addresses
                    elif 'inet ' in line:
                        ip_parts = line.split()
                        for part in ip_parts:
                            if part.startswith('inet '):
                                ip_addr = part.split('/')[0].replace('inet ', '')
                                current_interface['ip_addresses'].append(ip_addr)
                    
                    # MAC address
                    elif 'link/ether' in line:
                        mac_parts = line.split()
                        for part in mac_parts:
                            if ':' in part and len(part) == 17:
                                current_interface['mac_address'] = part
                                break
                
                if current_interface:
                    interfaces.append(current_interface)
                
                return {
                    'success': True,
                    'interfaces': interfaces,
                    'total_interfaces': len(interfaces),
                    'active_interfaces': len([i for i in interfaces if i['status'] == 'up'])
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to get network interfaces',
                    'stderr': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Network interface detection failed'
            }
    
    def test_usb_connection(self) -> Dict[str, Any]:
        """Test USB Type-C connection to host"""
        try:
            # Check if we have USB ethernet interface
            usb_interfaces = []
            
            # Check for USB ethernet adapters
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                usb_devices = result.stdout.split('\n')
                for device in usb_devices:
                    if 'ethernet' in device.lower() or 'network' in device.lower():
                        usb_interfaces.append(device.strip())
            
            # Check for USB ethernet interface in network interfaces
            interface_result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=5)
            usb_network_interface = None
            
            if interface_result.returncode == 0:
                for line in interface_result.stdout.split('\n'):
                    if 'usb' in line.lower() or 'eth' in line.lower():
                        if ':' in line:
                            interface_name = line.split(':')[1].strip()
                            if 'usb' in interface_name.lower() or 'eth' in interface_name.lower():
                                usb_network_interface = interface_name
                                break
            
            # Test connection to default Jetson IP
            jetson_reachable = False
            jetson_response_time = None
            
            try:
                start_time = time.time()
                response = requests.get(f"http://{self.jetson_default_ip}", timeout=5)
                end_time = time.time()
                
                if response.status_code == 200:
                    jetson_reachable = True
                    jetson_response_time = round((end_time - start_time) * 1000, 2)  # ms
            except:
                pass
            
            return {
                'success': True,
                'usb_devices': usb_interfaces,
                'usb_network_interface': usb_network_interface,
                'jetson_default_ip': self.jetson_default_ip,
                'jetson_reachable': jetson_reachable,
                'jetson_response_time_ms': jetson_response_time,
                'connection_type': 'USB Type-C to Host' if jetson_reachable else 'Not connected'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'USB connection test failed'
            }
    
    def test_wifi_status(self) -> Dict[str, Any]:
        """Test WiFi status and connection"""
        try:
            wifi_info = {
                'enabled': False,
                'connected': False,
                'current_network': None,
                'signal_strength': None,
                'ip_address': None
            }
            
            # Check if WiFi is enabled using nmcli
            try:
                result = subprocess.run(['nmcli', 'radio', 'wifi'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    wifi_info['enabled'] = 'enabled' in result.stdout.lower()
            except:
                pass
            
            # Check current WiFi connection
            try:
                result = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL,IP4.ADDRESS', 'dev', 'wifi'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line and 'yes:' in line:
                            parts = line.split(':')
                            if len(parts) >= 4:
                                wifi_info['connected'] = True
                                wifi_info['current_network'] = parts[1] if parts[1] else 'Unknown'
                                wifi_info['signal_strength'] = int(parts[2]) if parts[2].isdigit() else None
                                wifi_info['ip_address'] = parts[3].split('/')[0] if parts[3] else None
                                break
            except:
                pass
            
            # Fallback: Check using iwconfig
            if not wifi_info['connected']:
                try:
                    result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'ESSID:' in line:
                                essid = line.split('ESSID:')[1].strip().strip('"')
                                if essid and essid != 'off/any':
                                    wifi_info['connected'] = True
                                    wifi_info['current_network'] = essid
                            elif 'Signal level=' in line:
                                signal_match = line.split('Signal level=')[1].split()[0]
                                try:
                                    wifi_info['signal_strength'] = int(signal_match)
                                except:
                                    pass
                except:
                    pass
            
            return {
                'success': True,
                'wifi_info': wifi_info
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'WiFi status test failed'
            }
    
    def test_internet_connectivity(self) -> Dict[str, Any]:
        """Test internet connectivity"""
        try:
            test_urls = [
                'https://www.google.com',
                'https://www.cloudflare.com',
                'https://httpbin.org/get'
            ]
            
            results = []
            internet_available = False
            
            for url in test_urls:
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=10)
                    end_time = time.time()
                    
                    response_time = round((end_time - start_time) * 1000, 2)  # ms
                    
                    results.append({
                        'url': url,
                        'status_code': response.status_code,
                        'response_time_ms': response_time,
                        'success': response.status_code == 200
                    })
                    
                    if response.status_code == 200:
                        internet_available = True
                        
                except Exception as e:
                    results.append({
                        'url': url,
                        'error': str(e),
                        'success': False
                    })
            
            return {
                'success': True,
                'internet_available': internet_available,
                'test_results': results,
                'connectivity_status': 'Connected to Internet' if internet_available else 'No Internet Access'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Internet connectivity test failed'
            }
    
    def test_myrvm_platform(self) -> Dict[str, Any]:
        """Test MyRVM Platform connection"""
        try:
            test_endpoints = [
                f"{self.myrvm_platform_url}/api/health-check",
                f"{self.myrvm_platform_url}/api/status",
                f"{self.myrvm_platform_url}/"
            ]
            
            results = []
            platform_reachable = False
            
            for endpoint in test_endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(endpoint, timeout=10)
                    end_time = time.time()
                    
                    response_time = round((end_time - start_time) * 1000, 2)  # ms
                    
                    results.append({
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'response_time_ms': response_time,
                        'success': response.status_code in [200, 404],  # 404 is OK for root endpoint
                        'response_size': len(response.content) if response.content else 0
                    })
                    
                    if response.status_code in [200, 404]:
                        platform_reachable = True
                        
                except Exception as e:
                    results.append({
                        'endpoint': endpoint,
                        'error': str(e),
                        'success': False
                    })
            
            return {
                'success': True,
                'platform_reachable': platform_reachable,
                'platform_url': self.myrvm_platform_url,
                'test_results': results,
                'connection_status': 'Connected to MyRVM Platform' if platform_reachable else 'MyRVM Platform Unreachable'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'MyRVM Platform test failed'
            }
    
    def test_network_configuration(self) -> Dict[str, Any]:
        """Test network configuration"""
        try:
            config = {
                'hostname': None,
                'dns_servers': [],
                'gateway': None,
                'routing_table': []
            }
            
            # Get hostname
            try:
                result = subprocess.run(['hostname'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    config['hostname'] = result.stdout.strip()
            except:
                pass
            
            # Get DNS servers
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns = line.split()[1]
                            config['dns_servers'].append(dns)
            except:
                pass
            
            # Get gateway
            try:
                result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'default via' in line:
                            gateway = line.split('default via')[1].split()[0]
                            config['gateway'] = gateway
                            break
            except:
                pass
            
            # Get routing table
            try:
                result = subprocess.run(['ip', 'route', 'show'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    config['routing_table'] = result.stdout.strip().split('\n')
            except:
                pass
            
            return {
                'success': True,
                'configuration': config
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Network configuration test failed'
            }
    
    def test_dns_resolution(self) -> Dict[str, Any]:
        """Test DNS resolution"""
        try:
            test_domains = [
                'google.com',
                'cloudflare.com',
                '100.123.143.87'  # MyRVM Platform IP
            ]
            
            results = []
            dns_working = False
            
            for domain in test_domains:
                try:
                    result = subprocess.run(['nslookup', domain], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        results.append({
                            'domain': domain,
                            'success': True,
                            'resolved': True,
                            'output': result.stdout
                        })
                        dns_working = True
                    else:
                        results.append({
                            'domain': domain,
                            'success': False,
                            'resolved': False,
                            'error': result.stderr
                        })
                        
                except Exception as e:
                    results.append({
                        'domain': domain,
                        'success': False,
                        'resolved': False,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'dns_working': dns_working,
                'test_results': results,
                'dns_status': 'DNS Resolution Working' if dns_working else 'DNS Resolution Failed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'DNS resolution test failed'
            }
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        summary = {
            'overall_status': 'Unknown',
            'connection_type': 'Unknown',
            'recommendations': [],
            'critical_issues': [],
            'warnings': []
        }
        
        # Analyze results
        usb_connected = self.test_results.get('usb_connection', {}).get('jetson_reachable', False)
        wifi_connected = self.test_results.get('wifi_status', {}).get('wifi_info', {}).get('connected', False)
        internet_available = self.test_results.get('internet', {}).get('internet_available', False)
        platform_reachable = self.test_results.get('myrvm_platform', {}).get('platform_reachable', False)
        
        # Determine connection type and status
        if usb_connected:
            summary['connection_type'] = 'USB Type-C to Host (192.168.55.1)'
            summary['overall_status'] = 'Connected via USB'
            summary['recommendations'].append('Jetson is connected via USB Type-C. This is the default setup mode.')
        elif wifi_connected:
            summary['connection_type'] = 'WiFi Connection'
            summary['overall_status'] = 'Connected via WiFi'
            if internet_available:
                summary['recommendations'].append('WiFi connection is working and internet is available.')
            else:
                summary['warnings'].append('WiFi connected but no internet access.')
        else:
            summary['connection_type'] = 'No Network Connection'
            summary['overall_status'] = 'No Network'
            summary['critical_issues'].append('No network connection detected. Check WiFi or USB connection.')
        
        # Internet connectivity
        if internet_available:
            summary['recommendations'].append('Internet connectivity is working.')
        else:
            summary['warnings'].append('No internet connectivity detected.')
        
        # MyRVM Platform connectivity
        if platform_reachable:
            summary['recommendations'].append('MyRVM Platform is reachable.')
        else:
            summary['critical_issues'].append('MyRVM Platform is not reachable. Check server connectivity.')
        
        # Final status
        if summary['critical_issues']:
            summary['overall_status'] = 'Issues Detected'
        elif summary['warnings']:
            summary['overall_status'] = 'Working with Warnings'
        else:
            summary['overall_status'] = 'All Tests Passed'
        
        return summary

def main():
    """Main function"""
    print("=" * 60)
    print("JETSON ORIN NETWORK TEST SCRIPT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = NetworkTester()
    results = tester.run_all_tests()
    
    # Print summary
    summary = results['summary']
    print("NETWORK TEST SUMMARY")
    print("-" * 30)
    print(f"Overall Status: {summary['overall_status']}")
    print(f"Connection Type: {summary['connection_type']}")
    print(f"Test Duration: {results['duration_seconds']:.2f} seconds")
    print()
    
    if summary['recommendations']:
        print("RECOMMENDATIONS:")
        for rec in summary['recommendations']:
            print(f"  ✓ {rec}")
        print()
    
    if summary['warnings']:
        print("WARNINGS:")
        for warning in summary['warnings']:
            print(f"  ⚠ {warning}")
        print()
    
    if summary['critical_issues']:
        print("CRITICAL ISSUES:")
        for issue in summary['critical_issues']:
            print(f"  ✗ {issue}")
        print()
    
    # Save results to file
    output_file = f"network_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")
    print("=" * 60)
    
    return results

if __name__ == "__main__":
    main()


