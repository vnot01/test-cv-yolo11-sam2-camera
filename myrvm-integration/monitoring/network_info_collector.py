import subprocess
import socket
import psutil
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

class NetworkInfoCollector:
    def __init__(self):
        self.cached_info = {}
        self.cache_timeout = 300  # 5 minutes
        
    def collect_network_info(self) -> Dict[str, Any]:
        """Collect comprehensive network information"""
        try:
            return {
                'local_ip': self._get_local_ip(),
                'virtual_ip': self._get_virtual_ip(),
                'gateway_ip': self._get_gateway_ip(),
                'dns_servers': self._get_dns_servers(),
                'network_interface': self._get_primary_interface(),
                'connection_type': self._get_connection_type(),
                'signal_strength': self._get_signal_strength(),
                'network_interfaces': self._get_all_interfaces(),
                'last_network_check': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error collecting network info: {e}")
            return {}
    
    def _get_local_ip(self) -> Optional[str]:
        """Get local IP address"""
        try:
            # Get primary interface IP
            interfaces = psutil.net_if_addrs()
            for interface_name, addresses in interfaces.items():
                if interface_name.startswith('eth') or interface_name.startswith('wlan'):
                    for addr in addresses:
                        if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                            return addr.address
        except Exception:
            pass
        return None
    
    def _get_virtual_ip(self) -> Optional[str]:
        """Get virtual IP (Tailscale primary, ZeroTier emergency)"""
        try:
            # Check for Tailscale (primary tunnel)
            tailscale_ip = self._get_tailscale_ip()
            if tailscale_ip:
                return tailscale_ip
            
            # Check for ZeroTier (emergency tunnel)
            zerotier_ip = self._get_zerotier_ip()
            if zerotier_ip:
                return zerotier_ip
                
        except Exception:
            pass
        return None
    
    def _get_tailscale_ip(self) -> Optional[str]:
        """Get Tailscale IP address"""
        try:
            result = subprocess.run(['tailscale', 'ip', '-4'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def _get_zerotier_ip(self) -> Optional[str]:
        """Get Zerotier IP address"""
        try:
            result = subprocess.run(['zerotier-cli', 'listnetworks'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 4 and parts[2] == 'OK':
                        return parts[3]
        except Exception:
            pass
        return None
    
    def _get_gateway_ip(self) -> Optional[str]:
        """Get gateway IP address"""
        try:
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'default via' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            return parts[2]
        except Exception:
            pass
        return None
    
    def _get_dns_servers(self) -> List[str]:
        """Get DNS servers"""
        try:
            result = subprocess.run(['cat', '/etc/resolv.conf'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                dns_servers = []
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('nameserver'):
                        dns_servers.append(line.split()[1])
                return dns_servers
        except Exception:
            pass
        return []
    
    def _get_primary_interface(self) -> Optional[str]:
        """Get primary network interface"""
        try:
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'default via' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            return parts[4]
        except Exception:
            pass
        return None
    
    def _get_connection_type(self) -> str:
        """Determine connection type"""
        try:
            # Check for wired connection
            if self._is_wired_connected():
                return 'wired'
            
            # Check for wireless connection
            if self._is_wireless_connected():
                return 'wireless'
            
            # Check for cellular connection
            if self._is_cellular_connected():
                return 'cellular'
                
        except Exception:
            pass
        return 'unknown'
    
    def _is_wired_connected(self) -> bool:
        """Check if wired connection is active"""
        try:
            interfaces = psutil.net_if_stats()
            for interface_name, stats in interfaces.items():
                if interface_name.startswith('eth') and stats.isup:
                    return True
        except Exception:
            pass
        return False
    
    def _is_wireless_connected(self) -> bool:
        """Check if wireless connection is active"""
        try:
            interfaces = psutil.net_if_stats()
            for interface_name, stats in interfaces.items():
                if interface_name.startswith('wlan') and stats.isup:
                    return True
        except Exception:
            pass
        return False
    
    def _is_cellular_connected(self) -> bool:
        """Check if cellular connection is active"""
        try:
            interfaces = psutil.net_if_stats()
            for interface_name, stats in interfaces.items():
                if interface_name.startswith('wwan') and stats.isup:
                    return True
        except Exception:
            pass
        return False
    
    def _get_signal_strength(self) -> Optional[int]:
        """Get wireless signal strength"""
        try:
            result = subprocess.run(['iwconfig'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'Signal level' in line:
                        # Parse signal level (e.g., "Signal level=-45 dBm")
                        parts = line.split('Signal level=')
                        if len(parts) > 1:
                            signal_part = parts[1].split()[0]
                            if signal_part.endswith('dBm'):
                                signal_value = int(signal_part[:-3])
                                # Convert dBm to percentage (rough approximation)
                                if signal_value >= -30:
                                    return 100
                                elif signal_value >= -50:
                                    return 80
                                elif signal_value >= -60:
                                    return 60
                                elif signal_value >= -70:
                                    return 40
                                elif signal_value >= -80:
                                    return 20
                                else:
                                    return 10
        except Exception:
            pass
        return None
    
    def _get_all_interfaces(self) -> Dict[str, Any]:
        """Get information about all network interfaces"""
        try:
            interfaces = {}
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name in net_if_addrs:
                interface_info = {
                    'addresses': [],
                    'is_up': False,
                    'speed': 0,
                    'mtu': 0
                }
                
                # Get addresses
                for addr in net_if_addrs[interface_name]:
                    interface_info['addresses'].append({
                        'family': addr.family.name,
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                
                # Get stats
                if interface_name in net_if_stats:
                    stats = net_if_stats[interface_name]
                    interface_info['is_up'] = stats.isup
                    interface_info['speed'] = stats.speed
                    interface_info['mtu'] = stats.mtu
                
                interfaces[interface_name] = interface_info
            
            return interfaces
        except Exception as e:
            print(f"Error getting all interfaces: {e}")
            return {}

