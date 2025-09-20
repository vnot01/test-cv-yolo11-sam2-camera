#!/usr/bin/env python3
"""
Comprehensive Metrics Collector for MyRVM Platform Integration
Real-time system, application, and business metrics collection
"""

import os
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import psutil
import GPUtil
from collections import defaultdict, deque
import statistics
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now

class MetricsCollector:
    """Comprehensive metrics collection system"""
    
    def __init__(self, config: Dict):
        """
        Initialize metrics collector
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.collection_interval = config.get('monitoring_interval', 30.0)
        self.metrics_history_size = config.get('metrics_history_size', 1000)
        self.enable_gpu_monitoring = config.get('enable_gpu_monitoring', True)
        
        # Metrics storage
        self.metrics_history = defaultdict(lambda: deque(maxlen=self.metrics_history_size))
        self.current_metrics = {}
        self.custom_metrics = {}
        
        # Collection control
        self.is_collecting = False
        self.collection_thread = None
        self.collection_lock = threading.Lock()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Metrics callbacks
        self.metrics_callbacks = []
        
        # Initialize metrics
        self._initialize_metrics()
        
        self.logger.info("Metrics collector initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for metrics collector"""
        logger = logging.getLogger('MetricsCollector')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'metrics_collector_{now().strftime("%Y%m%d")}.log'
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
    
    def _initialize_metrics(self):
        """Initialize metrics structure"""
        self.current_metrics = {
            'timestamp': now().isoformat(),
            'system': {},
            'application': {},
            'business': {},
            'network': {},
            'gpu': {}
        }
    
    def start_collection(self):
        """Start metrics collection"""
        if not self.is_collecting:
            self.is_collecting = True
            self.collection_thread = threading.Thread(target=self._collection_loop)
            self.collection_thread.daemon = True
            self.collection_thread.start()
            self.logger.info("Metrics collection started")
    
    def stop_collection(self):
        """Stop metrics collection"""
        if self.is_collecting:
            self.is_collecting = False
            if self.collection_thread:
                self.collection_thread.join(timeout=5)
            self.logger.info("Metrics collection stopped")
    
    def _collection_loop(self):
        """Main metrics collection loop"""
        while self.is_collecting:
            try:
                start_time = time.time()
                
                # Collect all metrics
                with self.collection_lock:
                    self._collect_system_metrics()
                    self._collect_application_metrics()
                    self._collect_business_metrics()
                    self._collect_network_metrics()
                    
                    if self.enable_gpu_monitoring:
                        self._collect_gpu_metrics()
                    
                    # Update timestamp
                    self.current_metrics['timestamp'] = now().isoformat()
                    
                    # Store in history
                    self._store_metrics_history()
                    
                    # Notify callbacks
                    self._notify_callbacks()
                
                # Calculate sleep time
                collection_time = time.time() - start_time
                sleep_time = max(0, self.collection_interval - collection_time)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Metrics collection took {collection_time:.2f}s, longer than interval {self.collection_interval}s")
                
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            self.current_metrics['system'] = {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None,
                    'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percent': memory.percent,
                    'swap_total_gb': swap.total / (1024**3),
                    'swap_used_gb': swap.used / (1024**3),
                    'swap_percent': swap.percent
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'used_gb': disk.used / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'percent': (disk.used / disk.total) * 100,
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0
                },
                'process': {
                    'memory_rss_mb': process_memory.rss / (1024**2),
                    'memory_vms_mb': process_memory.vms / (1024**2),
                    'cpu_percent': process_cpu,
                    'num_threads': process.num_threads(),
                    'create_time': process.create_time()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            self.current_metrics['system'] = {}
    
    def _collect_application_metrics(self):
        """Collect application metrics"""
        try:
            # Get application-specific metrics
            app_metrics = {
                'uptime_seconds': time.time() - psutil.Process().create_time(),
                'active_connections': 0,  # Placeholder
                'processing_queue_size': 0,  # Placeholder
                'error_count': 0,  # Placeholder
                'success_count': 0,  # Placeholder
                'last_processing_time': 0,  # Placeholder
                'average_processing_time': 0,  # Placeholder
                'throughput_per_minute': 0  # Placeholder
            }
            
            # Update with custom metrics if available
            app_metrics.update(self.custom_metrics.get('application', {}))
            
            self.current_metrics['application'] = app_metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {e}")
            self.current_metrics['application'] = {}
    
    def _collect_business_metrics(self):
        """Collect business metrics"""
        try:
            business_metrics = {
                'detection_accuracy': 0.0,  # Placeholder
                'detection_success_rate': 0.0,  # Placeholder
                'total_detections': 0,  # Placeholder
                'successful_detections': 0,  # Placeholder
                'failed_detections': 0,  # Placeholder
                'average_confidence': 0.0,  # Placeholder
                'processing_volume_per_hour': 0,  # Placeholder
                'user_satisfaction_score': 0.0  # Placeholder
            }
            
            # Update with custom metrics if available
            business_metrics.update(self.custom_metrics.get('business', {}))
            
            self.current_metrics['business'] = business_metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting business metrics: {e}")
            self.current_metrics['business'] = {}
    
    def _collect_network_metrics(self):
        """Collect network metrics"""
        try:
            network_io = psutil.net_io_counters()
            network_connections = len(psutil.net_connections())
            
            self.current_metrics['network'] = {
                'bytes_sent': network_io.bytes_sent if network_io else 0,
                'bytes_recv': network_io.bytes_recv if network_io else 0,
                'packets_sent': network_io.packets_sent if network_io else 0,
                'packets_recv': network_io.packets_recv if network_io else 0,
                'active_connections': network_connections,
                'connection_errors': 0,  # Placeholder
                'latency_ms': 0,  # Placeholder
                'bandwidth_utilization': 0.0  # Placeholder
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting network metrics: {e}")
            self.current_metrics['network'] = {}
    
    def _collect_gpu_metrics(self):
        """Collect GPU metrics"""
        try:
            gpu_metrics = {}
            
            # Try to get GPU information
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use first GPU
                    gpu_metrics = {
                        'name': gpu.name,
                        'load_percent': gpu.load * 100,
                        'memory_used_mb': gpu.memoryUsed,
                        'memory_total_mb': gpu.memoryTotal,
                        'memory_percent': (gpu.memoryUsed / gpu.memoryTotal) * 100,
                        'temperature_c': gpu.temperature,
                        'uuid': gpu.uuid
                    }
                else:
                    gpu_metrics = {
                        'name': 'No GPU detected',
                        'load_percent': 0,
                        'memory_used_mb': 0,
                        'memory_total_mb': 0,
                        'memory_percent': 0,
                        'temperature_c': 0,
                        'uuid': None
                    }
            except Exception as e:
                self.logger.warning(f"Could not get GPU metrics: {e}")
                gpu_metrics = {
                    'name': 'GPU monitoring unavailable',
                    'load_percent': 0,
                    'memory_used_mb': 0,
                    'memory_total_mb': 0,
                    'memory_percent': 0,
                    'temperature_c': 0,
                    'uuid': None
                }
            
            self.current_metrics['gpu'] = gpu_metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting GPU metrics: {e}")
            self.current_metrics['gpu'] = {}
    
    def _store_metrics_history(self):
        """Store current metrics in history"""
        try:
            timestamp = self.current_metrics['timestamp']
            
            # Store each metric category
            for category, metrics in self.current_metrics.items():
                if category != 'timestamp':
                    for metric_name, value in metrics.items():
                        if isinstance(value, dict):
                            for sub_metric, sub_value in value.items():
                                key = f"{category}.{metric_name}.{sub_metric}"
                                self.metrics_history[key].append({
                                    'timestamp': timestamp,
                                    'value': sub_value
                                })
                        else:
                            key = f"{category}.{metric_name}"
                            self.metrics_history[key].append({
                                'timestamp': timestamp,
                                'value': value
                            })
            
        except Exception as e:
            self.logger.error(f"Error storing metrics history: {e}")
    
    def _notify_callbacks(self):
        """Notify registered callbacks"""
        try:
            for callback in self.metrics_callbacks:
                try:
                    callback(self.current_metrics)
                except Exception as e:
                    self.logger.error(f"Error in metrics callback: {e}")
        except Exception as e:
            self.logger.error(f"Error notifying callbacks: {e}")
    
    def add_metrics_callback(self, callback: Callable):
        """Add metrics callback"""
        self.metrics_callbacks.append(callback)
        self.logger.info(f"Added metrics callback: {callback.__name__}")
    
    def remove_metrics_callback(self, callback: Callable):
        """Remove metrics callback"""
        if callback in self.metrics_callbacks:
            self.metrics_callbacks.remove(callback)
            self.logger.info(f"Removed metrics callback: {callback.__name__}")
    
    def update_custom_metric(self, category: str, metric_name: str, value: Any):
        """Update custom metric"""
        try:
            if category not in self.custom_metrics:
                self.custom_metrics[category] = {}
            
            self.custom_metrics[category][metric_name] = value
            self.logger.debug(f"Updated custom metric: {category}.{metric_name} = {value}")
            
        except Exception as e:
            self.logger.error(f"Error updating custom metric: {e}")
    
    def get_current_metrics(self) -> Dict:
        """Get current metrics"""
        with self.collection_lock:
            return self.current_metrics.copy()
    
    def get_metrics_history(self, metric_name: str, limit: int = 100) -> List[Dict]:
        """Get metrics history for specific metric"""
        try:
            if metric_name in self.metrics_history:
                history = list(self.metrics_history[metric_name])
                return history[-limit:] if limit else history
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error getting metrics history: {e}")
            return []
    
    def get_metrics_summary(self) -> Dict:
        """Get metrics summary with statistics"""
        try:
            summary = {
                'collection_status': 'active' if self.is_collecting else 'inactive',
                'collection_interval': self.collection_interval,
                'metrics_count': len(self.metrics_history),
                'history_size': self.metrics_history_size,
                'custom_metrics_count': len(self.custom_metrics),
                'callbacks_count': len(self.metrics_callbacks),
                'last_collection': self.current_metrics.get('timestamp', 'never')
            }
            
            # Add statistics for key metrics
            key_metrics = [
                'system.cpu.percent',
                'system.memory.percent',
                'system.disk.percent'
            ]
            
            for metric in key_metrics:
                if metric in self.metrics_history:
                    values = [item['value'] for item in self.metrics_history[metric] if item['value'] is not None]
                    if values:
                        summary[f"{metric}_stats"] = {
                            'current': values[-1] if values else None,
                            'average': statistics.mean(values),
                            'min': min(values),
                            'max': max(values),
                            'count': len(values)
                        }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting metrics summary: {e}")
            return {}
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        try:
            if format.lower() == 'json':
                return json.dumps(self.current_metrics, indent=2)
            elif format.lower() == 'prometheus':
                return self._export_prometheus_format()
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Error exporting metrics: {e}")
            return ""
    
    def _export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        try:
            lines = []
            timestamp = int(time.time() * 1000)  # milliseconds
            
            for category, metrics in self.current_metrics.items():
                if category == 'timestamp':
                    continue
                
                for metric_name, value in metrics.items():
                    if isinstance(value, dict):
                        for sub_metric, sub_value in value.items():
                            if isinstance(sub_value, (int, float)):
                                metric_line = f"myrvm_{category}_{metric_name}_{sub_metric} {sub_value} {timestamp}"
                                lines.append(metric_line)
                    else:
                        if isinstance(value, (int, float)):
                            metric_line = f"myrvm_{category}_{metric_name} {value} {timestamp}"
                            lines.append(metric_line)
            
            return '\n'.join(lines)
            
        except Exception as e:
            self.logger.error(f"Error exporting Prometheus format: {e}")
            return ""
    
    def get_metrics_report(self) -> str:
        """Generate metrics report"""
        try:
            summary = self.get_metrics_summary()
            current = self.get_current_metrics()
            
            report = f"""
Metrics Collector Report
========================
Collection Status: {summary.get('collection_status', 'unknown')}
Collection Interval: {summary.get('collection_interval', 0)}s
Metrics Count: {summary.get('metrics_count', 0)}
History Size: {summary.get('history_size', 0)}
Custom Metrics: {summary.get('custom_metrics_count', 0)}
Callbacks: {summary.get('callbacks_count', 0)}
Last Collection: {summary.get('last_collection', 'never')}

Current System Metrics:
- CPU Usage: {current.get('system', {}).get('cpu', {}).get('percent', 'N/A')}%
- Memory Usage: {current.get('system', {}).get('memory', {}).get('percent', 'N/A')}%
- Disk Usage: {current.get('system', {}).get('disk', {}).get('percent', 'N/A')}%
- Process Memory: {current.get('system', {}).get('process', {}).get('memory_rss_mb', 'N/A')}MB

Current GPU Metrics:
- GPU Name: {current.get('gpu', {}).get('name', 'N/A')}
- GPU Load: {current.get('gpu', {}).get('load_percent', 'N/A')}%
- GPU Memory: {current.get('gpu', {}).get('memory_percent', 'N/A')}%
- GPU Temperature: {current.get('gpu', {}).get('temperature_c', 'N/A')}°C

Application Metrics:
- Uptime: {current.get('application', {}).get('uptime_seconds', 'N/A')}s
- Processing Queue: {current.get('application', {}).get('processing_queue_size', 'N/A')}
- Error Count: {current.get('application', {}).get('error_count', 'N/A')}
- Success Count: {current.get('application', {}).get('success_count', 'N/A')}

Business Metrics:
- Detection Accuracy: {current.get('business', {}).get('detection_accuracy', 'N/A')}%
- Success Rate: {current.get('business', {}).get('detection_success_rate', 'N/A')}%
- Total Detections: {current.get('business', {}).get('total_detections', 'N/A')}
- Average Confidence: {current.get('business', {}).get('average_confidence', 'N/A')}%
"""
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating metrics report: {e}")
            return f"Error generating metrics report: {e}"
