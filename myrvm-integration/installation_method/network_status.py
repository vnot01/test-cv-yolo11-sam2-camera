#!/usr/bin/env python3
"""
Network Status Module for Web GUI
Real-time network status checking for RVM-Jetson Installation Method
"""

import subprocess
import requests
import time
from typing import Dict, Any

class NetworkStatus:
    """Real-time network status checker"""
    
    def __init__(self):
        self.jetson_default_ip = "192.168.55.1"
        self.myrvm_platform_url = "http://100.123.143.87:8001"
        self.cache_duration = 5  # seconds
        self._cache = {}
        self._cache_timestamp = {}
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache is still valid"""
        if key not in self._cache_timestamp:
            return False
        return time.time() - self._cache_timestamp[key] < self.cache_duration
    
    def _set_cache(self, key: str, value: Any):
        """Set cache value"""
        self._cache[key] = value
        self._cache_timestamp[key] = time.time()
    
    def _get_cache(self, key: str) -> Any:
        """Get cache value"""
        return self._cache.get(key)
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get comprehensive network status"""
        cache_key = "network_status"
        if self._is_cache_valid(cache_key):
            return self._get_cache(cache_key)
        
        status = {
            'timestamp': time.time(),
            'usb_connection': self.check_usb_connection(),
            'wifi_status': self.check_wifi_status(),
            'internet_connectivity': self.check_internet_connectivity(),
            'myrvm_platform': self.check_myrvm_platform(),
            'network_interfaces': self.get_network_interfaces()
        }
        
        # Determine overall connection type
        status['connection_type'] = self._determine_connection_type(status)
        status['overall_status'] = self._determine_overall_status(status)
        
        self._set_cache(cache_key, status)
        return status
    
    def check_usb_connection(self) -> Dict[str, Any]:
        """Check USB Type-C connection"""
        try:
            response = requests.get(f"http://{self.jetson_default_ip}", timeout=2)
            return {
                'connected': True,
                'ip': self.jetson_default_ip,
                'status_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        except:
            return {
                'connected': False,
                'ip': self.jetson_default_ip,
                'error': 'Connection failed'
            }
    
    def check_wifi_status(self) -> Dict[str, Any]:
        """Check WiFi connection status"""
        try:
            # Try nmcli first
            result = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID,SIGNAL,IP4.ADDRESS', 'dev', 'wifi'], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line and 'yes:' in line:
                        parts = line.split(':')
                        if len(parts) >= 4:
                            return {
                                'connected': True,
                                'ssid': parts[1] if parts[1] else 'Unknown',
                                'signal_strength': int(parts[2]) if parts[2].isdigit() else None,
                                'ip_address': parts[3].split('/')[0] if parts[3] else None,
                                'method': 'nmcli'
                            }
            
            # Fallback to iwconfig
            result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=3)
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
                                'method': 'iwconfig'
                            }
            
            return {
                'connected': False,
                'error': 'No WiFi connection found'
            }
            
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    def check_internet_connectivity(self) -> Dict[str, Any]:
        """Check internet connectivity"""
        test_urls = [
            'https://www.google.com',
            'https://httpbin.org/get'
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    return {
                        'connected': True,
                        'test_url': url,
                        'response_time_ms': response.elapsed.total_seconds() * 1000,
                        'status_code': response.status_code
                    }
            except:
                continue
        
        return {
            'connected': False,
            'error': 'No internet connectivity'
        }
    
    def check_myrvm_platform(self) -> Dict[str, Any]:
        """Check MyRVM Platform connectivity"""
        try:
            response = requests.get(f"{self.myrvm_platform_url}/api/health-check", timeout=5)
            return {
                'reachable': True,
                'url': self.myrvm_platform_url,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'reachable': False,
                'url': self.myrvm_platform_url,
                'error': str(e)
            }
    
    def get_network_interfaces(self) -> Dict[str, Any]:
        """Get network interfaces information"""
        try:
            result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=3)
            
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
                            'ip_addresses': []
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
                
                if current_interface:
                    interfaces.append(current_interface)
                
                return {
                    'interfaces': interfaces,
                    'total_interfaces': len(interfaces),
                    'active_interfaces': len([i for i in interfaces if i['status'] == 'up'])
                }
            else:
                return {
                    'error': 'Failed to get network interfaces'
                }
                
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def _determine_connection_type(self, status: Dict[str, Any]) -> str:
        """Determine the type of network connection"""
        usb_connected = status.get('usb_connection', {}).get('connected', False)
        wifi_connected = status.get('wifi_status', {}).get('connected', False)
        
        if usb_connected:
            return 'USB Type-C to Host (192.168.55.1)'
        elif wifi_connected:
            return 'WiFi Connection'
        else:
            return 'No Network Connection'
    
    def _determine_overall_status(self, status: Dict[str, Any]) -> str:
        """Determine overall network status"""
        usb_connected = status.get('usb_connection', {}).get('connected', False)
        wifi_connected = status.get('wifi_status', {}).get('connected', False)
        internet_available = status.get('internet_connectivity', {}).get('connected', False)
        platform_reachable = status.get('myrvm_platform', {}).get('reachable', False)
        
        if usb_connected:
            return 'Connected via USB (Setup Mode)'
        elif wifi_connected and internet_available and platform_reachable:
            return 'Fully Connected (Ready for RVM Registration)'
        elif wifi_connected and internet_available:
            return 'Connected with Internet (Platform Unreachable)'
        elif wifi_connected:
            return 'WiFi Connected (No Internet)'
        else:
            return 'No Network Connection'
    
    def get_connection_recommendations(self, status: Dict[str, Any]) -> list:
        """Get connection recommendations based on status"""
        recommendations = []
        
        usb_connected = status.get('usb_connection', {}).get('connected', False)
        wifi_connected = status.get('wifi_status', {}).get('connected', False)
        internet_available = status.get('internet_connectivity', {}).get('connected', False)
        platform_reachable = status.get('myrvm_platform', {}).get('reachable', False)
        
        if usb_connected:
            recommendations.extend([
                "Jetson is connected via USB Type-C (192.168.55.1)",
                "This is the default setup mode for initial configuration",
                "Use the web interface to configure WiFi connection",
                "After WiFi setup, Jetson can register to MyRVM Platform"
            ])
        elif wifi_connected and internet_available and platform_reachable:
            recommendations.extend([
                "WiFi connection is working properly",
                "Internet connectivity is available",
                "MyRVM Platform is reachable",
                "Jetson is ready for RVM registration and deployment"
            ])
        elif wifi_connected and internet_available:
            recommendations.extend([
                "WiFi connection is working",
                "Internet connectivity is available",
                "MyRVM Platform is not reachable - check server connectivity",
                "Verify firewall settings and network routing"
            ])
        elif wifi_connected:
            recommendations.extend([
                "WiFi is connected but no internet access",
                "Check WiFi router internet connection",
                "Verify DNS settings and network configuration"
            ])
        else:
            recommendations.extend([
                "No network connection detected",
                "Connect via USB Type-C for initial setup",
                "Or configure WiFi connection manually"
            ])
        
        return recommendations


