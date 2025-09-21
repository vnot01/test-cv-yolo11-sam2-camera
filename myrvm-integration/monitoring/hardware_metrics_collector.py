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
            
            # Convert process objects to serializable format
            top_cpu_processes = []
            top_memory_processes = []
            
            for proc in processes:
                try:
                    info = proc.info
                    process_data = {
                        'pid': info.get('pid'),
                        'name': info.get('name'),
                        'cpu_percent': info.get('cpu_percent', 0),
                        'memory_percent': info.get('memory_percent', 0)
                    }
                    top_cpu_processes.append(process_data)
                    top_memory_processes.append(process_data)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort and get top 5
            top_cpu_processes = sorted(top_cpu_processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:5]
            top_memory_processes = sorted(top_memory_processes, key=lambda x: x['memory_percent'] or 0, reverse=True)[:5]
            
            return {
                'process_count': len(processes),
                'top_cpu_processes': top_cpu_processes,
                'top_memory_processes': top_memory_processes
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

