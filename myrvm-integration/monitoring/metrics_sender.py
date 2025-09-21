import requests
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from .hardware_metrics_collector import HardwareMetricsCollector
from .application_metrics_collector import ApplicationMetricsCollector
from .network_info_collector import NetworkInfoCollector

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

