# TASK 04: NETWORK MANAGEMENT MODULE

**Tanggal**: 2025-09-21  
**Versi**: 1.0.0  
**Status**: 📋 PLANNING  
**Priority**: HIGH  

---

## **🎯 OBJECTIVE**

Membuat Network Management Module untuk WiFi discovery, connection management, captive portal handling, dan server connectivity testing untuk RVM-Jetson.

---

## **📋 REQUIREMENTS**

### **Functional Requirements:**
- **WiFi Network Discovery** dengan signal strength dan security info
- **WiFi Connection Management** dengan password handling
- **Captive Portal Detection** dan handling (Mikrotik, Unifi, OpenWrt)
- **Server Connectivity Testing** dengan ping, speed test, latency
- **VPN Detection** (Tailscale, Zerotier, Twingate)
- **Network Status Monitoring** real-time
- **Network Configuration Backup** dan restore

### **Technical Requirements:**
- **Real-time Network Scanning** dengan auto-refresh
- **Secure Password Storage** dengan encryption
- **Network Profile Management** untuk multiple networks
- **Connection Quality Monitoring** dengan metrics
- **Auto-reconnection** pada network failure
- **Network Troubleshooting** tools

---

## **🔧 IMPLEMENTATION PLAN**

### **1. Network Management Module Structure**
```
network_management/
├── __init__.py
├── wifi_scanner.py           # WiFi network discovery
├── wifi_connector.py         # WiFi connection management
├── captive_portal_handler.py # Captive portal detection & handling
├── server_connectivity.py    # Server connectivity testing
├── vpn_detector.py          # VPN detection (Tailscale, Zerotier, Twingate)
├── network_monitor.py       # Network status monitoring
├── network_config_manager.py # Network configuration management
└── utils/
    ├── network_utils.py
    ├── security_utils.py
    └── performance_monitor.py
```

### **2. Core Features Implementation**

#### **A. WiFi Scanner**
```python
class WiFiScanner:
    def scan_networks(self):
        # Scan available WiFi networks
        
    def get_signal_strength(self):
        # Get signal strength for networks
        
    def get_security_info(self):
        # Get security information
        
    def filter_networks(self):
        # Filter networks by criteria
```

#### **B. WiFi Connector**
```python
class WiFiConnector:
    def connect_to_network(self):
        # Connect to selected network
        
    def disconnect_network(self):
        # Disconnect from current network
        
    def save_network_profile(self):
        # Save network configuration
        
    def load_network_profiles(self):
        # Load saved network profiles
```

#### **C. Captive Portal Handler**
```python
class CaptivePortalHandler:
    def detect_portal(self):
        # Detect captive portal
        
    def handle_mikrotik_portal(self):
        # Handle Mikrotik hotspot
        
    def handle_unifi_portal(self):
        # Handle Unifi controller
        
    def handle_generic_portal(self):
        # Handle generic portal
```

---

## **📝 DETAILED IMPLEMENTATION**

### **1. WiFi Scanner Module**

#### **WiFi Network Discovery:**
```python
import subprocess
import re
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class WiFiNetwork:
    ssid: str
    bssid: str
    signal_strength: int
    security: str
    frequency: int
    channel: int
    encryption: str
    wps: bool
    last_seen: float

class WiFiScanner:
    def __init__(self):
        self.networks = []
        self.scan_interval = 5  # seconds
        self.is_scanning = False
        
    def scan_networks(self) -> List[WiFiNetwork]:
        """Scan for available WiFi networks"""
        networks = []
        
        try:
            # Use nmcli to scan for networks
            result = subprocess.run([
                'nmcli', '-t', '-f', 'SSID,BSSID,SIGNAL,SECURITY,FREQ,CHAN', 'dev', 'wifi', 'list'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 6:
                            network = WiFiNetwork(
                                ssid=parts[0] if parts[0] else 'Hidden',
                                bssid=parts[1],
                                signal_strength=int(parts[2]) if parts[2].isdigit() else 0,
                                security=parts[3],
                                frequency=int(parts[4]) if parts[4].isdigit() else 0,
                                channel=int(parts[5]) if parts[5].isdigit() else 0,
                                encryption=self._parse_encryption(parts[3]),
                                wps=self._check_wps(parts[3]),
                                last_seen=time.time()
                            )
                            networks.append(network)
            
            # Sort by signal strength (strongest first)
            networks.sort(key=lambda x: x.signal_strength, reverse=True)
            self.networks = networks
            
        except subprocess.TimeoutExpired:
            print("WiFi scan timeout")
        except Exception as e:
            print(f"Error scanning WiFi networks: {e}")
        
        return networks
    
    def _parse_encryption(self, security: str) -> str:
        """Parse encryption type from security string"""
        if 'WPA3' in security:
            return 'WPA3'
        elif 'WPA2' in security:
            return 'WPA2'
        elif 'WPA' in security:
            return 'WPA'
        elif 'WEP' in security:
            return 'WEP'
        else:
            return 'Open'
    
    def _check_wps(self, security: str) -> bool:
        """Check if WPS is available"""
        return 'WPS' in security
    
    def get_network_by_ssid(self, ssid: str) -> Optional[WiFiNetwork]:
        """Get network by SSID"""
        for network in self.networks:
            if network.ssid == ssid:
                return network
        return None
    
    def filter_networks(self, 
                       min_signal: int = -80,
                       security_types: List[str] = None,
                       exclude_hidden: bool = True) -> List[WiFiNetwork]:
        """Filter networks by criteria"""
        if security_types is None:
            security_types = ['Open', 'WPA2', 'WPA3']
        
        filtered = []
        for network in self.networks:
            # Signal strength filter
            if network.signal_strength < min_signal:
                continue
            
            # Security type filter
            if network.encryption not in security_types:
                continue
            
            # Hidden network filter
            if exclude_hidden and network.ssid == 'Hidden':
                continue
            
            filtered.append(network)
        
        return filtered
    
    def get_network_statistics(self) -> Dict:
        """Get network statistics"""
        if not self.networks:
            return {}
        
        security_counts = {}
        signal_ranges = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        
        for network in self.networks:
            # Count security types
            security_counts[network.encryption] = security_counts.get(network.encryption, 0) + 1
            
            # Count signal strength ranges
            if network.signal_strength >= -50:
                signal_ranges['excellent'] += 1
            elif network.signal_strength >= -60:
                signal_ranges['good'] += 1
            elif network.signal_strength >= -70:
                signal_ranges['fair'] += 1
            else:
                signal_ranges['poor'] += 1
        
        return {
            'total_networks': len(self.networks),
            'security_distribution': security_counts,
            'signal_distribution': signal_ranges,
            'scan_time': time.time()
        }
    
    def start_continuous_scan(self, callback=None):
        """Start continuous network scanning"""
        self.is_scanning = True
        
        def scan_loop():
            while self.is_scanning:
                networks = self.scan_networks()
                if callback:
                    callback(networks)
                time.sleep(self.scan_interval)
        
        import threading
        scan_thread = threading.Thread(target=scan_loop, daemon=True)
        scan_thread.start()
        return scan_thread
    
    def stop_continuous_scan(self):
        """Stop continuous network scanning"""
        self.is_scanning = False
```

### **2. WiFi Connector Module**

#### **WiFi Connection Management:**
```python
import subprocess
import json
import time
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib
import base64
from cryptography.fernet import Fernet

@dataclass
class NetworkProfile:
    ssid: str
    password: str
    security: str
    priority: int
    auto_connect: bool
    created_at: float
    last_used: float

class WiFiConnector:
    def __init__(self):
        self.current_connection = None
        self.network_profiles = []
        self.encryption_key = self._get_or_create_key()
        
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key for passwords"""
        key_file = '/tmp/wifi_encryption.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt password for storage"""
        f = Fernet(self.encryption_key)
        encrypted = f.encrypt(password.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password from storage"""
        f = Fernet(self.encryption_key)
        encrypted = base64.b64decode(encrypted_password.encode())
        return f.decrypt(encrypted).decode()
    
    def connect_to_network(self, ssid: str, password: str = None, 
                          security: str = 'WPA2') -> Dict:
        """Connect to WiFi network"""
        result = {
            'success': False,
            'ssid': ssid,
            'error': None,
            'connection_time': 0,
            'ip_address': None,
            'signal_strength': 0
        }
        
        try:
            start_time = time.time()
            
            # Disconnect from current network first
            self.disconnect_network()
            
            # Create connection
            if password:
                # Secured network
                cmd = [
                    'nmcli', 'dev', 'wifi', 'connect', ssid,
                    'password', password
                ]
            else:
                # Open network
                cmd = [
                    'nmcli', 'dev', 'wifi', 'connect', ssid
                ]
            
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if process.returncode == 0:
                # Wait for connection to establish
                time.sleep(5)
                
                # Check connection status
                if self.is_connected():
                    result['success'] = True
                    result['connection_time'] = time.time() - start_time
                    result['ip_address'] = self.get_ip_address()
                    result['signal_strength'] = self.get_signal_strength(ssid)
                    
                    # Save network profile
                    if password:
                        self.save_network_profile(ssid, password, security)
                    
                    self.current_connection = {
                        'ssid': ssid,
                        'connected_at': time.time(),
                        'ip_address': result['ip_address']
                    }
                else:
                    result['error'] = 'Connection established but not active'
            else:
                result['error'] = process.stderr.strip()
                
        except subprocess.TimeoutExpired:
            result['error'] = 'Connection timeout'
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def disconnect_network(self) -> bool:
        """Disconnect from current network"""
        try:
            result = subprocess.run([
                'nmcli', 'dev', 'disconnect', 'wlan0'
            ], capture_output=True, text=True, timeout=30)
            
            self.current_connection = None
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error disconnecting: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to WiFi"""
        try:
            result = subprocess.run([
                'nmcli', '-t', '-f', 'STATE', 'dev', 'status'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'wlan0' in line and 'connected' in line:
                        return True
            
            return False
            
        except Exception as e:
            print(f"Error checking connection: {e}")
            return False
    
    def get_ip_address(self) -> Optional[str]:
        """Get current IP address"""
        try:
            result = subprocess.run([
                'nmcli', '-t', '-f', 'IP4.ADDRESS', 'dev', 'show', 'wlan0'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    # Extract IP from format like "192.168.1.100/24"
                    ip = output.split('/')[0]
                    return ip
            
            return None
            
        except Exception as e:
            print(f"Error getting IP address: {e}")
            return None
    
    def get_signal_strength(self, ssid: str = None) -> int:
        """Get signal strength of current or specified network"""
        try:
            if ssid:
                # Get signal strength of specific network
                result = subprocess.run([
                    'nmcli', '-t', '-f', 'SIGNAL', 'dev', 'wifi', 'list'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if ssid in line:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                return int(parts[1]) if parts[1].isdigit() else 0
            else:
                # Get signal strength of current connection
                result = subprocess.run([
                    'nmcli', '-t', '-f', 'SIGNAL', 'dev', 'wifi', 'list'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'connected' in line:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                return int(parts[1]) if parts[1].isdigit() else 0
            
            return 0
            
        except Exception as e:
            print(f"Error getting signal strength: {e}")
            return 0
    
    def save_network_profile(self, ssid: str, password: str, 
                           security: str, priority: int = 0) -> bool:
        """Save network profile"""
        try:
            profile = NetworkProfile(
                ssid=ssid,
                password=self._encrypt_password(password),
                security=security,
                priority=priority,
                auto_connect=True,
                created_at=time.time(),
                last_used=time.time()
            )
            
            # Load existing profiles
            self.load_network_profiles()
            
            # Remove existing profile with same SSID
            self.network_profiles = [p for p in self.network_profiles if p.ssid != ssid]
            
            # Add new profile
            self.network_profiles.append(profile)
            
            # Save to file
            self._save_profiles_to_file()
            
            return True
            
        except Exception as e:
            print(f"Error saving network profile: {e}")
            return False
    
    def load_network_profiles(self) -> List[NetworkProfile]:
        """Load network profiles from file"""
        try:
            profiles_file = '/tmp/wifi_profiles.json'
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r') as f:
                    data = json.load(f)
                    self.network_profiles = []
                    for item in data:
                        profile = NetworkProfile(
                            ssid=item['ssid'],
                            password=item['password'],  # Already encrypted
                            security=item['security'],
                            priority=item['priority'],
                            auto_connect=item['auto_connect'],
                            created_at=item['created_at'],
                            last_used=item['last_used']
                        )
                        self.network_profiles.append(profile)
            else:
                self.network_profiles = []
                
        except Exception as e:
            print(f"Error loading network profiles: {e}")
            self.network_profiles = []
        
        return self.network_profiles
    
    def _save_profiles_to_file(self):
        """Save profiles to file"""
        try:
            profiles_file = '/tmp/wifi_profiles.json'
            data = []
            for profile in self.network_profiles:
                data.append({
                    'ssid': profile.ssid,
                    'password': profile.password,  # Already encrypted
                    'security': profile.security,
                    'priority': profile.priority,
                    'auto_connect': profile.auto_connect,
                    'created_at': profile.created_at,
                    'last_used': profile.last_used
                })
            
            with open(profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving profiles to file: {e}")
    
    def get_connection_status(self) -> Dict:
        """Get detailed connection status"""
        status = {
            'connected': False,
            'ssid': None,
            'ip_address': None,
            'signal_strength': 0,
            'connection_time': 0,
            'data_transferred': {'tx': 0, 'rx': 0}
        }
        
        try:
            if self.is_connected():
                status['connected'] = True
                status['ssid'] = self._get_current_ssid()
                status['ip_address'] = self.get_ip_address()
                status['signal_strength'] = self.get_signal_strength()
                
                if self.current_connection:
                    status['connection_time'] = time.time() - self.current_connection['connected_at']
                
                # Get data transfer stats
                status['data_transferred'] = self._get_data_transfer_stats()
                
        except Exception as e:
            print(f"Error getting connection status: {e}")
        
        return status
    
    def _get_current_ssid(self) -> Optional[str]:
        """Get current SSID"""
        try:
            result = subprocess.run([
                'nmcli', '-t', '-f', 'NAME', 'dev', 'status'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'wlan0' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            return parts[1]
            
            return None
            
        except Exception as e:
            print(f"Error getting current SSID: {e}")
            return None
    
    def _get_data_transfer_stats(self) -> Dict:
        """Get data transfer statistics"""
        try:
            result = subprocess.run([
                'cat', '/proc/net/dev'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'wlan0' in line:
                        parts = line.split()
                        if len(parts) >= 10:
                            return {
                                'rx': int(parts[1]),
                                'tx': int(parts[9])
                            }
            
            return {'tx': 0, 'rx': 0}
            
        except Exception as e:
            print(f"Error getting data transfer stats: {e}")
            return {'tx': 0, 'rx': 0}
```

### **3. Captive Portal Handler Module**

#### **Captive Portal Detection & Handling:**
```python
import requests
import time
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin
import subprocess

class CaptivePortalHandler:
    def __init__(self):
        self.portal_types = {
            'mikrotik': self._detect_mikrotik_portal,
            'unifi': self._detect_unifi_portal,
            'openwrt': self._detect_openwrt_portal,
            'generic': self._detect_generic_portal
        }
        self.test_urls = [
            'http://httpbin.org/ip',
            'http://www.google.com',
            'http://www.microsoft.com',
            'http://www.apple.com'
        ]
    
    def detect_portal(self) -> Dict:
        """Detect captive portal"""
        result = {
            'portal_detected': False,
            'portal_type': None,
            'portal_url': None,
            'login_required': False,
            'error': None
        }
        
        try:
            # Test internet connectivity
            connectivity_result = self._test_internet_connectivity()
            
            if not connectivity_result['connected']:
                # Check if redirected to captive portal
                redirect_result = self._check_redirect()
                
                if redirect_result['redirected']:
                    result['portal_detected'] = True
                    result['portal_url'] = redirect_result['redirect_url']
                    
                    # Detect portal type
                    portal_type = self._detect_portal_type(redirect_result['redirect_url'])
                    result['portal_type'] = portal_type
                    result['login_required'] = True
                else:
                    result['error'] = 'No internet connection and no captive portal detected'
            else:
                result['portal_detected'] = False
                result['login_required'] = False
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _test_internet_connectivity(self) -> Dict:
        """Test internet connectivity"""
        result = {
            'connected': False,
            'response_time': 0,
            'error': None
        }
        
        for url in self.test_urls:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10, allow_redirects=False)
                end_time = time.time()
                
                if response.status_code == 200:
                    result['connected'] = True
                    result['response_time'] = end_time - start_time
                    return result
                    
            except requests.exceptions.RequestException as e:
                continue
        
        result['error'] = 'No internet connectivity'
        return result
    
    def _check_redirect(self) -> Dict:
        """Check for redirect to captive portal"""
        result = {
            'redirected': False,
            'redirect_url': None,
            'redirect_chain': []
        }
        
        for url in self.test_urls:
            try:
                response = requests.get(url, timeout=10, allow_redirects=False)
                
                if response.status_code in [302, 307, 308]:
                    redirect_url = response.headers.get('Location')
                    if redirect_url:
                        result['redirected'] = True
                        result['redirect_url'] = redirect_url
                        result['redirect_chain'].append({
                            'from': url,
                            'to': redirect_url,
                            'status_code': response.status_code
                        })
                        return result
                        
            except requests.exceptions.RequestException:
                continue
        
        return result
    
    def _detect_portal_type(self, portal_url: str) -> str:
        """Detect portal type from URL"""
        try:
            parsed_url = urlparse(portal_url)
            hostname = parsed_url.hostname.lower()
            
            # Check for known portal types
            if 'mikrotik' in hostname or 'hotspot' in hostname:
                return 'mikrotik'
            elif 'unifi' in hostname or 'ubiquiti' in hostname:
                return 'unifi'
            elif 'openwrt' in hostname or 'luci' in hostname:
                return 'openwrt'
            else:
                return 'generic'
                
        except Exception:
            return 'generic'
    
    def _detect_mikrotik_portal(self, portal_url: str) -> Dict:
        """Detect Mikrotik portal specifics"""
        result = {
            'portal_type': 'mikrotik',
            'login_url': None,
            'form_fields': [],
            'error': None
        }
        
        try:
            response = requests.get(portal_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for Mikrotik-specific elements
                if 'mikrotik' in content.lower() or 'hotspot' in content.lower():
                    result['login_url'] = portal_url
                    
                    # Extract form fields
                    form_fields = re.findall(r'<input[^>]*name="([^"]*)"[^>]*>', content)
                    result['form_fields'] = form_fields
                    
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _detect_unifi_portal(self, portal_url: str) -> Dict:
        """Detect Unifi portal specifics"""
        result = {
            'portal_type': 'unifi',
            'login_url': None,
            'form_fields': [],
            'error': None
        }
        
        try:
            response = requests.get(portal_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for Unifi-specific elements
                if 'unifi' in content.lower() or 'ubiquiti' in content.lower():
                    result['login_url'] = portal_url
                    
                    # Extract form fields
                    form_fields = re.findall(r'<input[^>]*name="([^"]*)"[^>]*>', content)
                    result['form_fields'] = form_fields
                    
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _detect_openwrt_portal(self, portal_url: str) -> Dict:
        """Detect OpenWrt portal specifics"""
        result = {
            'portal_type': 'openwrt',
            'login_url': None,
            'form_fields': [],
            'error': None
        }
        
        try:
            response = requests.get(portal_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for OpenWrt-specific elements
                if 'openwrt' in content.lower() or 'luci' in content.lower():
                    result['login_url'] = portal_url
                    
                    # Extract form fields
                    form_fields = re.findall(r'<input[^>]*name="([^"]*)"[^>]*>', content)
                    result['form_fields'] = form_fields
                    
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _detect_generic_portal(self, portal_url: str) -> Dict:
        """Detect generic portal specifics"""
        result = {
            'portal_type': 'generic',
            'login_url': None,
            'form_fields': [],
            'error': None
        }
        
        try:
            response = requests.get(portal_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                result['login_url'] = portal_url
                
                # Extract form fields
                form_fields = re.findall(r'<input[^>]*name="([^"]*)"[^>]*>', content)
                result['form_fields'] = form_fields
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def handle_portal_login(self, portal_type: str, credentials: Dict) -> Dict:
        """Handle portal login"""
        result = {
            'success': False,
            'error': None,
            'response': None
        }
        
        try:
            if portal_type == 'mikrotik':
                result = self._handle_mikrotik_login(credentials)
            elif portal_type == 'unifi':
                result = self._handle_unifi_login(credentials)
            elif portal_type == 'openwrt':
                result = self._handle_openwrt_login(credentials)
            else:
                result = self._handle_generic_login(credentials)
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _handle_mikrotik_login(self, credentials: Dict) -> Dict:
        """Handle Mikrotik portal login"""
        result = {
            'success': False,
            'error': None,
            'response': None
        }
        
        try:
            # Mikrotik hotspot login typically uses POST to /login
            login_url = credentials.get('login_url')
            username = credentials.get('username', 'admin')
            password = credentials.get('password', '')
            
            if not login_url:
                result['error'] = 'Login URL not provided'
                return result
            
            # Prepare login data
            login_data = {
                'username': username,
                'password': password,
                'dst': '',
                'popup': 'true'
            }
            
            # Send login request
            response = requests.post(login_url, data=login_data, timeout=30)
            
            if response.status_code == 200:
                # Check if login was successful
                if 'success' in response.text.lower() or 'welcome' in response.text.lower():
                    result['success'] = True
                else:
                    result['error'] = 'Login failed - invalid credentials'
            else:
                result['error'] = f'Login request failed with status {response.status_code}'
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _handle_unifi_login(self, credentials: Dict) -> Dict:
        """Handle Unifi portal login"""
        result = {
            'success': False,
            'error': None,
            'response': None
        }
        
        try:
            # Unifi controller login
            login_url = credentials.get('login_url')
            username = credentials.get('username', 'admin')
            password = credentials.get('password', '')
            
            if not login_url:
                result['error'] = 'Login URL not provided'
                return result
            
            # Prepare login data
            login_data = {
                'username': username,
                'password': password
            }
            
            # Send login request
            response = requests.post(login_url, data=login_data, timeout=30)
            
            if response.status_code == 200:
                # Check if login was successful
                if 'success' in response.text.lower() or 'dashboard' in response.text.lower():
                    result['success'] = True
                else:
                    result['error'] = 'Login failed - invalid credentials'
            else:
                result['error'] = f'Login request failed with status {response.status_code}'
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _handle_openwrt_login(self, credentials: Dict) -> Dict:
        """Handle OpenWrt portal login"""
        result = {
            'success': False,
            'error': None,
            'response': None
        }
        
        try:
            # OpenWrt LuCI login
            login_url = credentials.get('login_url')
            username = credentials.get('username', 'root')
            password = credentials.get('password', '')
            
            if not login_url:
                result['error'] = 'Login URL not provided'
                return result
            
            # Prepare login data
            login_data = {
                'luci_username': username,
                'luci_password': password
            }
            
            # Send login request
            response = requests.post(login_url, data=login_data, timeout=30)
            
            if response.status_code == 200:
                # Check if login was successful
                if 'success' in response.text.lower() or 'luci' in response.text.lower():
                    result['success'] = True
                else:
                    result['error'] = 'Login failed - invalid credentials'
            else:
                result['error'] = f'Login request failed with status {response.status_code}'
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _handle_generic_login(self, credentials: Dict) -> Dict:
        """Handle generic portal login"""
        result = {
            'success': False,
            'error': None,
            'response': None
        }
        
        try:
            # Generic portal login
            login_url = credentials.get('login_url')
            username = credentials.get('username', '')
            password = credentials.get('password', '')
            
            if not login_url:
                result['error'] = 'Login URL not provided'
                return result
            
            # Prepare login data
            login_data = {
                'username': username,
                'password': password
            }
            
            # Send login request
            response = requests.post(login_url, data=login_data, timeout=30)
            
            if response.status_code == 200:
                # Check if login was successful
                if 'success' in response.text.lower() or 'welcome' in response.text.lower():
                    result['success'] = True
                else:
                    result['error'] = 'Login failed - invalid credentials'
            else:
                result['error'] = f'Login request failed with status {response.status_code}'
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def test_internet_after_login(self) -> Dict:
        """Test internet connectivity after portal login"""
        result = {
            'connected': False,
            'response_time': 0,
            'error': None
        }
        
        try:
            # Wait a moment for connection to establish
            time.sleep(3)
            
            # Test connectivity
            connectivity_result = self._test_internet_connectivity()
            result.update(connectivity_result)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
```

---

## **🧪 TESTING STRATEGY**

### **Unit Testing:**
- **WiFi scanning** testing
- **Connection management** testing
- **Captive portal detection** testing
- **VPN detection** testing

### **Integration Testing:**
- **Network management** integration
- **Web interface** integration
- **Real-time monitoring** testing
- **Error handling** testing

### **Network Testing:**
- **WiFi connectivity** testing
- **Captive portal** handling
- **VPN connectivity** testing
- **Performance monitoring** testing

---

## **📊 SUCCESS CRITERIA**

### **Functional Success:**
- ✅ WiFi network discovery
- ✅ WiFi connection management
- ✅ Captive portal handling
- ✅ Server connectivity testing
- ✅ VPN detection
- ✅ Network status monitoring
- ✅ Network configuration management

### **Technical Success:**
- ✅ Real-time network scanning
- ✅ Secure password storage
- ✅ Network profile management
- ✅ Connection quality monitoring
- ✅ Auto-reconnection
- ✅ Network troubleshooting

### **Integration Success:**
- ✅ Web interface integration
- ✅ Hardware detection integration
- ✅ Real-time monitoring
- ✅ Error handling

---

## **⏱️ ESTIMATED TIMELINE**

### **Week 1: Core Modules**
- **Day 1-2**: WiFi scanner module
- **Day 3-4**: WiFi connector module
- **Day 5**: Network profile management

### **Week 2: Advanced Features**
- **Day 1-2**: Captive portal handler
- **Day 3-4**: Server connectivity testing
- **Day 5**: VPN detection

### **Week 3: Monitoring & Integration**
- **Day 1-2**: Network monitoring
- **Day 3-4**: Network configuration manager
- **Day 5**: Integration testing

### **Week 4: Testing & Documentation**
- **Day 1-2**: Unit testing
- **Day 3-4**: Integration testing
- **Day 5**: Documentation

---

## **📁 DELIVERABLES**

### **Code Files:**
- `wifi_scanner.py`
- `wifi_connector.py`
- `captive_portal_handler.py`
- `server_connectivity.py`
- `vpn_detector.py`
- `network_monitor.py`
- `network_config_manager.py`

### **Documentation:**
- API documentation
- Network configuration guide
- Troubleshooting guide
- Security guide

### **Testing:**
- Unit tests
- Integration tests
- Network tests
- Performance tests

---

**Status**: 📋 **READY FOR IMPLEMENTATION**  
**Estimated Time**: 4 weeks  
**Difficulty**: Advanced  
**Dependencies**: NetworkManager, requests, cryptography, Web interface
