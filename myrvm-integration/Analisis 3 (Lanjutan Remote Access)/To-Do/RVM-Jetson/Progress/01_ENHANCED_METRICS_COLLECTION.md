# TASK 01: ENHANCED METRICS COLLECTION

**Tanggal**: 2025-01-20  
**Status**: 🔄 **IN PROGRESS**  
**Prioritas**: HIGH  
**Estimasi**: 2-3 hari  
**Assigned**: RVM Jetson Orin (MyRVM-Integration)

---

## **📋 DESKRIPSI TUGAS**

Implementasi Enhanced Metrics Collection di RVM Jetson Orin untuk mengumpulkan dan mengirim comprehensive hardware metrics, application metrics, dan network information ke MyRVM Platform.

### **🎯 TUJUAN:**
- Implementasi comprehensive metrics collection
- Hardware metrics (CPU, GPU, RAM, Disk, Temperature)
- Application metrics (software version, AI model version, uptime)
- Network information (local IP, virtual IP, connectivity)
- Real-time metrics streaming ke server

---

## **🔧 IMPLEMENTASI**

### **1. Enhanced Metrics Collector**

#### **A. Hardware Metrics Collector:**
```python
# File: myrvm-integration/monitoring/hardware_metrics_collector.py

import psutil
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class HardwareMetricsCollector:
    def __init__(self):
        self.last_network_stats = None
        self.last_disk_stats = None
        
    def collect_cpu_metrics(self) -> Dict[str, Any]:
        """Collect CPU usage and temperature metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # CPU temperature (Jetson specific)
            cpu_temp = self._get_jetson_cpu_temperature()
            
            return {
                'cpu_usage': cpu_percent,
                'cpu_count': cpu_count,
                'cpu_frequency': cpu_freq.current if cpu_freq else None,
                'cpu_temperature': cpu_temp,
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
            }
        except Exception as e:
            print(f"Error collecting CPU metrics: {e}")
            return {}
    
    def collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory usage metrics"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'memory_usage': memory.percent,
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_used': memory.used,
                'swap_usage': swap.percent,
                'swap_total': swap.total,
                'swap_used': swap.used
            }
        except Exception as e:
            print(f"Error collecting memory metrics: {e}")
            return {}
    
    def collect_disk_metrics(self) -> Dict[str, Any]:
        """Collect disk usage and I/O metrics"""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Calculate disk I/O speeds
            disk_read_speed = 0
            disk_write_speed = 0
            
            if self.last_disk_stats and disk_io:
                time_diff = time.time() - self.last_disk_stats['timestamp']
                if time_diff > 0:
                    read_diff = disk_io.read_bytes - self.last_disk_stats['read_bytes']
                    write_diff = disk_io.write_bytes - self.last_disk_stats['write_bytes']
                    disk_read_speed = read_diff / time_diff
                    disk_write_speed = write_diff / time_diff
            
            # Update last stats
            self.last_disk_stats = {
                'timestamp': time.time(),
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0
            }
            
            return {
                'disk_usage': (disk_usage.used / disk_usage.total) * 100,
                'disk_total': disk_usage.total,
                'disk_available': disk_usage.free,
                'disk_used': disk_usage.used,
                'disk_read_speed': disk_read_speed,
                'disk_write_speed': disk_write_speed
            }
        except Exception as e:
            print(f"Error collecting disk metrics: {e}")
            return {}
    
    def collect_gpu_metrics(self) -> Dict[str, Any]:
        """Collect GPU usage and temperature metrics"""
        try:
            # GPU usage (Jetson specific)
            gpu_usage = self._get_jetson_gpu_usage()
            gpu_temp = self._get_jetson_gpu_temperature()
            
            return {
                'gpu_usage': gpu_usage,
                'gpu_temperature': gpu_temp,
                'gpu_memory_usage': self._get_jetson_gpu_memory_usage()
            }
        except Exception as e:
            print(f"Error collecting GPU metrics: {e}")
            return {}
    
    def collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network I/O metrics"""
        try:
            network_io = psutil.net_io_counters()
            
            # Calculate network speeds
            network_upload_speed = 0
            network_download_speed = 0
            
            if self.last_network_stats and network_io:
                time_diff = time.time() - self.last_network_stats['timestamp']
                if time_diff > 0:
                    upload_diff = network_io.bytes_sent - self.last_network_stats['bytes_sent']
                    download_diff = network_io.bytes_recv - self.last_network_stats['bytes_recv']
                    network_upload_speed = upload_diff / time_diff
                    network_download_speed = download_diff / time_diff
            
            # Update last stats
            self.last_network_stats = {
                'timestamp': time.time(),
                'bytes_sent': network_io.bytes_sent if network_io else 0,
                'bytes_recv': network_io.bytes_recv if network_io else 0
            }
            
            return {
                'network_upload_speed': network_upload_speed,
                'network_download_speed': network_download_speed,
                'network_bytes_sent': network_io.bytes_sent if network_io else 0,
                'network_bytes_recv': network_io.bytes_recv if network_io else 0
            }
        except Exception as e:
            print(f"Error collecting network metrics: {e}")
            return {}
    
    def collect_process_metrics(self) -> Dict[str, Any]:
        """Collect process-related metrics"""
        try:
            processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']))
            
            return {
                'process_count': len(processes),
                'top_cpu_processes': sorted(processes, key=lambda x: x.info['cpu_percent'] or 0, reverse=True)[:5],
                'top_memory_processes': sorted(processes, key=lambda x: x.info['memory_percent'] or 0, reverse=True)[:5]
            }
        except Exception as e:
            print(f"Error collecting process metrics: {e}")
            return {}
    
    def _get_jetson_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature from Jetson thermal zones"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read().strip()) / 1000.0
                return temp
        except Exception:
            return None
    
    def _get_jetson_gpu_temperature(self) -> Optional[float]:
        """Get GPU temperature from Jetson thermal zones"""
        try:
            with open('/sys/class/thermal/thermal_zone1/temp', 'r') as f:
                temp = int(f.read().strip()) / 1000.0
                return temp
        except Exception:
            return None
    
    def _get_jetson_gpu_usage(self) -> Optional[float]:
        """Get GPU usage from tegrastats"""
        try:
            result = subprocess.run(['tegrastats', '--interval', '1000', '--logfile', '/tmp/tegrastats.log'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                # Parse tegrastats output for GPU usage
                # This is a simplified example - actual parsing would be more complex
                return 0.0  # Placeholder
        except Exception:
            pass
        return None
    
    def _get_jetson_gpu_memory_usage(self) -> Optional[float]:
        """Get GPU memory usage from tegrastats"""
        try:
            # Similar to GPU usage, parse tegrastats for memory info
            return 0.0  # Placeholder
        except Exception:
            return None
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all hardware metrics"""
        return {
            'cpu': self.collect_cpu_metrics(),
            'memory': self.collect_memory_metrics(),
            'disk': self.collect_disk_metrics(),
            'gpu': self.collect_gpu_metrics(),
            'network': self.collect_network_metrics(),
            'processes': self.collect_process_metrics(),
            'timestamp': datetime.now().isoformat()
        }
```

#### **B. Application Metrics Collector:**
```python
# File: myrvm-integration/monitoring/application_metrics_collector.py

import os
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, Optional

class ApplicationMetricsCollector:
    def __init__(self):
        self.start_time = time.time()
        self.deposit_count = 0
        self.error_count = 0
        self.warning_count = 0
        
    def collect_software_version(self) -> Dict[str, Any]:
        """Collect software version information"""
        try:
            # Get Git commit hash
            git_hash = self._get_git_commit_hash()
            
            # Get package versions
            package_versions = self._get_package_versions()
            
            return {
                'software_version': git_hash,
                'package_versions': package_versions,
                'build_date': self._get_build_date()
            }
        except Exception as e:
            print(f"Error collecting software version: {e}")
            return {}
    
    def collect_ai_model_info(self) -> Dict[str, Any]:
        """Collect AI model information"""
        try:
            model_path = os.path.join(os.getcwd(), 'models', 'best.pt')
            
            if os.path.exists(model_path):
                stat = os.stat(model_path)
                return {
                    'model_name': 'best.pt',
                    'model_version': self._get_model_version(model_path),
                    'model_path': model_path,
                    'model_size': stat.st_size,
                    'model_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                return {
                    'model_name': 'best.pt',
                    'model_version': 'not_found',
                    'model_path': model_path,
                    'model_size': 0,
                    'model_modified': None
                }
        except Exception as e:
            print(f"Error collecting AI model info: {e}")
            return {}
    
    def collect_uptime_metrics(self) -> Dict[str, Any]:
        """Collect application uptime metrics"""
        try:
            current_time = time.time()
            uptime_seconds = current_time - self.start_time
            
            return {
                'uptime_seconds': uptime_seconds,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'current_time': datetime.fromtimestamp(current_time).isoformat()
            }
        except Exception as e:
            print(f"Error collecting uptime metrics: {e}")
            return {}
    
    def collect_deposit_metrics(self) -> Dict[str, Any]:
        """Collect deposit-related metrics"""
        try:
            return {
                'deposit_count_since_restart': self.deposit_count,
                'last_deposit_time': self._get_last_deposit_time(),
                'deposit_rate_per_hour': self._calculate_deposit_rate()
            }
        except Exception as e:
            print(f"Error collecting deposit metrics: {e}")
            return {}
    
    def collect_error_metrics(self) -> Dict[str, Any]:
        """Collect error and warning metrics"""
        try:
            return {
                'error_count': self.error_count,
                'warning_count': self.warning_count,
                'last_error_time': self._get_last_error_time(),
                'last_warning_time': self._get_last_warning_time()
            }
        except Exception as e:
            print(f"Error collecting error metrics: {e}")
            return {}
    
    def increment_deposit_count(self):
        """Increment deposit count"""
        self.deposit_count += 1
    
    def increment_error_count(self):
        """Increment error count"""
        self.error_count += 1
    
    def increment_warning_count(self):
        """Increment warning count"""
        self.warning_count += 1
    
    def _get_git_commit_hash(self) -> Optional[str]:
        """Get current Git commit hash"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            if result.returncode == 0:
                return result.stdout.strip()[:8]  # Short hash
        except Exception:
            pass
        return None
    
    def _get_package_versions(self) -> Dict[str, str]:
        """Get installed package versions"""
        try:
            packages = ['torch', 'ultralytics', 'opencv-python', 'numpy', 'pillow']
            versions = {}
            
            for package in packages:
                try:
                    result = subprocess.run(['pip', 'show', package], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.startswith('Version:'):
                                versions[package] = line.split(':', 1)[1].strip()
                                break
                except Exception:
                    versions[package] = 'unknown'
            
            return versions
        except Exception as e:
            print(f"Error getting package versions: {e}")
            return {}
    
    def _get_build_date(self) -> Optional[str]:
        """Get build date from Git"""
        try:
            result = subprocess.run(['git', 'log', '-1', '--format=%ci'], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def _get_model_version(self, model_path: str) -> str:
        """Get model version (simplified)"""
        try:
            # This would typically involve loading the model and checking metadata
            # For now, we'll use file modification time as version
            stat = os.stat(model_path)
            return datetime.fromtimestamp(stat.st_mtime).strftime('%Y%m%d_%H%M%S')
        except Exception:
            return 'unknown'
    
    def _get_last_deposit_time(self) -> Optional[str]:
        """Get last deposit time"""
        try:
            # This would read from your deposit log or database
            return None  # Placeholder
        except Exception:
            return None
    
    def _calculate_deposit_rate(self) -> float:
        """Calculate deposit rate per hour"""
        try:
            uptime_hours = (time.time() - self.start_time) / 3600
            if uptime_hours > 0:
                return self.deposit_count / uptime_hours
            return 0.0
        except Exception:
            return 0.0
    
    def _get_last_error_time(self) -> Optional[str]:
        """Get last error time"""
        try:
            # This would read from your error log
            return None  # Placeholder
        except Exception:
            return None
    
    def _get_last_warning_time(self) -> Optional[str]:
        """Get last warning time"""
        try:
            # This would read from your warning log
            return None  # Placeholder
        except Exception:
            return None
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all application metrics"""
        return {
            'software': self.collect_software_version(),
            'ai_model': self.collect_ai_model_info(),
            'uptime': self.collect_uptime_metrics(),
            'deposits': self.collect_deposit_metrics(),
            'errors': self.collect_error_metrics(),
            'timestamp': datetime.now().isoformat()
        }
```

#### **C. Network Information Collector:**
```python
# File: myrvm-integration/monitoring/network_info_collector.py

import subprocess
import socket
import psutil
import json
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
        """Get virtual IP (Tailscale/Zerotier)"""
        try:
            # Check for Tailscale
            tailscale_ip = self._get_tailscale_ip()
            if tailscale_ip:
                return tailscale_ip
            
            # Check for Zerotier
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
```

### **2. Metrics Sender**

#### **A. Metrics Sender Service:**
```python
# File: myrvm-integration/monitoring/metrics_sender.py

import requests
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from hardware_metrics_collector import HardwareMetricsCollector
from application_metrics_collector import ApplicationMetricsCollector
from network_info_collector import NetworkInfoCollector

class MetricsSender:
    def __init__(self, server_url: str, rvm_id: int, api_key: str):
        self.server_url = server_url
        self.rvm_id = rvm_id
        self.api_key = api_key
        self.hardware_collector = HardwareMetricsCollector()
        self.app_collector = ApplicationMetricsCollector()
        self.network_collector = NetworkInfoCollector()
        self.is_running = False
        self.send_thread = None
        self.send_interval = 60  # Send every 60 seconds
        
    def start(self):
        """Start metrics sending service"""
        if self.is_running:
            return
        
        self.is_running = True
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        self.send_thread.start()
        print(f"Metrics sender started for RVM {self.rvm_id}")
    
    def stop(self):
        """Stop metrics sending service"""
        self.is_running = False
        if self.send_thread:
            self.send_thread.join(timeout=5)
        print(f"Metrics sender stopped for RVM {self.rvm_id}")
    
    def _send_loop(self):
        """Main sending loop"""
        while self.is_running:
            try:
                self._send_metrics()
                time.sleep(self.send_interval)
            except Exception as e:
                print(f"Error in metrics send loop: {e}")
                time.sleep(10)  # Wait 10 seconds before retry
    
    def _send_metrics(self):
        """Send metrics to server"""
        try:
            # Collect all metrics
            hardware_metrics = self.hardware_collector.collect_all_metrics()
            app_metrics = self.app_collector.collect_all_metrics()
            network_info = self.network_collector.collect_network_info()
            
            # Prepare payload
            payload = {
                'rvm_id': self.rvm_id,
                'system_metrics': {
                    'cpu_usage': hardware_metrics.get('cpu', {}).get('cpu_usage', 0),
                    'memory_usage': hardware_metrics.get('memory', {}).get('memory_usage', 0),
                    'disk_usage': hardware_metrics.get('disk', {}).get('disk_usage', 0),
                    'gpu_usage': hardware_metrics.get('gpu', {}).get('gpu_usage', 0),
                    'temperature': hardware_metrics.get('cpu', {}).get('cpu_temperature', 0),
                    'gpu_temperature': hardware_metrics.get('gpu', {}).get('gpu_temperature', 0),
                    'disk_read_speed': hardware_metrics.get('disk', {}).get('disk_read_speed', 0),
                    'disk_write_speed': hardware_metrics.get('disk', {}).get('disk_write_speed', 0),
                    'network_upload_speed': hardware_metrics.get('network', {}).get('network_upload_speed', 0),
                    'network_download_speed': hardware_metrics.get('network', {}).get('network_download_speed', 0),
                    'memory_available': hardware_metrics.get('memory', {}).get('memory_available', 0),
                    'disk_available': hardware_metrics.get('disk', {}).get('disk_available', 0),
                    'process_count': hardware_metrics.get('processes', {}).get('process_count', 0),
                    'load_average': hardware_metrics.get('cpu', {}).get('load_average', 0),
                    'uptime': app_metrics.get('uptime', {}).get('uptime_seconds', 0)
                },
                'application_metrics': {
                    'software_version': app_metrics.get('software', {}).get('software_version', 'unknown'),
                    'ai_model_version': app_metrics.get('ai_model', {}).get('model_version', 'unknown'),
                    'ai_model_path': app_metrics.get('ai_model', {}).get('model_path', ''),
                    'uptime_seconds': app_metrics.get('uptime', {}).get('uptime_seconds', 0),
                    'deposit_count_since_restart': app_metrics.get('deposits', {}).get('deposit_count_since_restart', 0),
                    'last_deposit_time': app_metrics.get('deposits', {}).get('last_deposit_time'),
                    'error_count': app_metrics.get('errors', {}).get('error_count', 0),
                    'warning_count': app_metrics.get('errors', {}).get('warning_count', 0)
                },
                'network_information': {
                    'local_ip': network_info.get('local_ip'),
                    'virtual_ip': network_info.get('virtual_ip'),
                    'gateway_ip': network_info.get('gateway_ip'),
                    'dns_servers': json.dumps(network_info.get('dns_servers', [])),
                    'network_interface': network_info.get('network_interface'),
                    'connection_type': network_info.get('connection_type'),
                    'signal_strength': network_info.get('signal_strength'),
                    'last_network_check': network_info.get('last_network_check')
                }
            }
            
            # Send to server
            response = requests.post(
                f"{self.server_url}/admin/rvm/{self.rvm_id}/store-metrics",
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}',
                    'X-RVM-ID': str(self.rvm_id)
                },
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"Metrics sent successfully for RVM {self.rvm_id}")
            else:
                print(f"Failed to send metrics: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error sending metrics: {e}")
    
    def send_immediate_metrics(self):
        """Send metrics immediately (for testing)"""
        self._send_metrics()
```

### **3. Integration with Main Application**

#### **A. Main Application Integration:**
```python
# File: myrvm-integration/main_application.py

# Add to existing imports
from monitoring.metrics_sender import MetricsSender
from monitoring.application_metrics_collector import ApplicationMetricsCollector

class MyRVMApplication:
    def __init__(self):
        # ... existing initialization ...
        
        # Initialize metrics collection
        self.app_metrics_collector = ApplicationMetricsCollector()
        self.metrics_sender = None
        
    def start_metrics_collection(self, server_url: str, rvm_id: int, api_key: str):
        """Start metrics collection and sending"""
        try:
            self.metrics_sender = MetricsSender(server_url, rvm_id, api_key)
            self.metrics_sender.start()
            print("Metrics collection started")
        except Exception as e:
            print(f"Failed to start metrics collection: {e}")
    
    def stop_metrics_collection(self):
        """Stop metrics collection"""
        if self.metrics_sender:
            self.metrics_sender.stop()
            self.metrics_sender = None
            print("Metrics collection stopped")
    
    def increment_deposit_count(self):
        """Increment deposit count in metrics"""
        if self.app_metrics_collector:
            self.app_metrics_collector.increment_deposit_count()
    
    def increment_error_count(self):
        """Increment error count in metrics"""
        if self.app_metrics_collector:
            self.app_metrics_collector.increment_error_count()
    
    def increment_warning_count(self):
        """Increment warning count in metrics"""
        if self.app_metrics_collector:
            self.app_metrics_collector.increment_warning_count()
```

---

## **🧪 TESTING**

### **1. Hardware Metrics Testing:**
- Test CPU metrics collection
- Test memory metrics collection
- Test disk metrics collection
- Test GPU metrics collection
- Test network metrics collection

### **2. Application Metrics Testing:**
- Test software version collection
- Test AI model info collection
- Test uptime metrics collection
- Test deposit metrics collection
- Test error metrics collection

### **3. Network Info Testing:**
- Test local IP detection
- Test virtual IP detection
- Test gateway IP detection
- Test DNS servers detection
- Test connection type detection

### **4. Metrics Sender Testing:**
- Test metrics sending to server
- Test error handling
- Test retry mechanism
- Test threading

---

## **📋 CHECKLIST**

- [ ] Implement HardwareMetricsCollector
- [ ] Implement ApplicationMetricsCollector
- [ ] Implement NetworkInfoCollector
- [ ] Implement MetricsSender
- [ ] Integrate with main application
- [ ] Test hardware metrics collection
- [ ] Test application metrics collection
- [ ] Test network info collection
- [ ] Test metrics sending
- [ ] Test error handling
- [ ] Test threading
- [ ] Performance testing
- [ ] Documentation update

---

## **📝 NOTES**

- Metrics collected every 60 seconds
- Comprehensive hardware and application monitoring
- Network information tracking
- Error handling and retry mechanism
- Threading for non-blocking operation
- Integration with existing application

---

**Status**: 🔄 **IN PROGRESS**  
**Next**: Implement hardware metrics collector
