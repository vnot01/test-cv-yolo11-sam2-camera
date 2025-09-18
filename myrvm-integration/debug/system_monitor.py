#!/usr/bin/env python3
"""
System Monitor for Jetson Orin
Monitors system resources, performance, and logs
"""

import psutil
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import subprocess
import os

class SystemMonitor:
    """System monitoring and debugging tool"""
    
    def __init__(self, log_dir: str = "../logs"):
        """
        Initialize system monitor
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Monitoring data
        self.monitoring_data = []
        self.max_data_points = 1000  # Keep last 1000 data points
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for system monitor"""
        logger = logging.getLogger('SystemMonitor')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = self.log_dir / f'system_monitor_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_system_info(self) -> Dict:
        """Get basic system information"""
        try:
            # CPU information
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk information
            disk = psutil.disk_usage('/')
            
            # Network information
            network = psutil.net_io_counters()
            
            # GPU information (if available)
            gpu_info = self._get_gpu_info()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'count': cpu_count,
                    'frequency': {
                        'current': cpu_freq.current if cpu_freq else None,
                        'min': cpu_freq.min if cpu_freq else None,
                        'max': cpu_freq.max if cpu_freq else None
                    },
                    'usage_percent': psutil.cpu_percent(interval=1)
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percentage': memory.percent
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percentage': swap.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percentage': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'gpu': gpu_info
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {'error': str(e)}
    
    def _get_gpu_info(self) -> Dict:
        """Get GPU information using nvidia-smi"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu', 
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 6:
                            gpu = {
                                'name': parts[0],
                                'memory_total': int(parts[1]) if parts[1].isdigit() else 0,
                                'memory_used': int(parts[2]) if parts[2].isdigit() else 0,
                                'memory_free': int(parts[3]) if parts[3].isdigit() else 0,
                                'temperature': int(parts[4]) if parts[4].isdigit() else 0,
                                'utilization': int(parts[5]) if parts[5].isdigit() else 0
                            }
                            gpus.append(gpu)
                
                return {'gpus': gpus, 'count': len(gpus)}
            else:
                return {'error': 'nvidia-smi not available'}
                
        except subprocess.TimeoutExpired:
            return {'error': 'nvidia-smi timeout'}
        except FileNotFoundError:
            return {'error': 'nvidia-smi not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_process_info(self, process_name: str = None) -> List[Dict]:
        """Get information about running processes"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    
                    # Filter by process name if specified
                    if process_name and process_name.lower() not in proc_info['name'].lower():
                        continue
                    
                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cpu_percent': proc_info['cpu_percent'],
                        'memory_percent': proc_info['memory_percent'],
                        'status': proc_info['status']
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            return processes[:20]  # Return top 20 processes
            
        except Exception as e:
            self.logger.error(f"Failed to get process info: {e}")
            return []
    
    def get_network_connections(self) -> List[Dict]:
        """Get network connections"""
        try:
            connections = []
            
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    connections.append({
                        'family': str(conn.family),
                        'type': str(conn.type),
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'status': conn.status,
                        'pid': conn.pid
                    })
            
            return connections
            
        except Exception as e:
            self.logger.error(f"Failed to get network connections: {e}")
            return []
    
    def collect_monitoring_data(self):
        """Collect current monitoring data"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'system': self.get_system_info(),
                'processes': self.get_process_info(),
                'network': self.get_network_connections()
            }
            
            # Add to monitoring data
            self.monitoring_data.append(data)
            
            # Keep only last N data points
            if len(self.monitoring_data) > self.max_data_points:
                self.monitoring_data = self.monitoring_data[-self.max_data_points:]
            
            self.logger.info(f"Collected monitoring data: CPU {data['system'].get('cpu', {}).get('usage_percent', 0):.1f}%, "
                           f"Memory {data['system'].get('memory', {}).get('percentage', 0):.1f}%")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to collect monitoring data: {e}")
            return None
    
    def save_monitoring_data(self, filename: str = None) -> str:
        """Save monitoring data to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitoring_data_{timestamp}.json"
        
        filepath = self.log_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.monitoring_data, f, indent=2)
            
            self.logger.info(f"✅ Monitoring data saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save monitoring data: {e}")
            raise
    
    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        try:
            system_info = self.get_system_info()
            
            if 'error' in system_info:
                return {'status': 'error', 'message': system_info['error']}
            
            # Check CPU usage
            cpu_usage = system_info.get('cpu', {}).get('usage_percent', 0)
            cpu_status = 'good' if cpu_usage < 80 else 'warning' if cpu_usage < 95 else 'critical'
            
            # Check memory usage
            memory_usage = system_info.get('memory', {}).get('percentage', 0)
            memory_status = 'good' if memory_usage < 80 else 'warning' if memory_usage < 95 else 'critical'
            
            # Check disk usage
            disk_usage = system_info.get('disk', {}).get('percentage', 0)
            disk_status = 'good' if disk_usage < 80 else 'warning' if disk_usage < 95 else 'critical'
            
            # Overall status
            statuses = [cpu_status, memory_status, disk_status]
            if 'critical' in statuses:
                overall_status = 'critical'
            elif 'warning' in statuses:
                overall_status = 'warning'
            else:
                overall_status = 'good'
            
            return {
                'status': overall_status,
                'timestamp': datetime.now().isoformat(),
                'cpu': {'usage': cpu_usage, 'status': cpu_status},
                'memory': {'usage': memory_usage, 'status': memory_status},
                'disk': {'usage': disk_usage, 'status': disk_status},
                'gpu': system_info.get('gpu', {})
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system health: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def monitor_continuously(self, interval: float = 10.0, duration: float = None):
        """
        Monitor system continuously
        
        Args:
            interval: Monitoring interval in seconds
            duration: Total monitoring duration in seconds (None for infinite)
        """
        self.logger.info(f"Starting continuous monitoring (interval: {interval}s)")
        
        start_time = time.time()
        
        try:
            while True:
                self.collect_monitoring_data()
                
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            # Save final data
            if self.monitoring_data:
                self.save_monitoring_data()
                self.logger.info("✅ Monitoring data saved")

# Example usage and testing
if __name__ == "__main__":
    monitor = SystemMonitor()
    
    # Get current system info
    print("=== System Information ===")
    system_info = monitor.get_system_info()
    print(json.dumps(system_info, indent=2))
    
    # Get system health
    print("\n=== System Health ===")
    health = monitor.get_system_health()
    print(json.dumps(health, indent=2))
    
    # Get top processes
    print("\n=== Top Processes ===")
    processes = monitor.get_process_info()
    for proc in processes[:10]:
        print(f"{proc['name']}: CPU {proc['cpu_percent']:.1f}%, Memory {proc['memory_percent']:.1f}%")
    
    # Get network connections
    print("\n=== Network Connections ===")
    connections = monitor.get_network_connections()
    for conn in connections[:10]:
        print(f"{conn['local_address']} - {conn['status']}")
    
    # Start continuous monitoring for 30 seconds
    print("\n=== Starting Continuous Monitoring (30 seconds) ===")
    monitor.monitor_continuously(interval=5.0, duration=30.0)
