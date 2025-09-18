#!/usr/bin/env python3
"""
Performance Monitor for MyRVM Platform Integration
Real-time performance monitoring and optimization
"""

import time
import psutil
import logging
import threading
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np

class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""
    
    def __init__(self, config: Dict):
        """
        Initialize performance monitor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.monitoring_interval = config.get('monitoring_interval', 5.0)  # 5 seconds
        self.history_size = config.get('history_size', 1000)  # Keep last 1000 records
        self.alert_thresholds = config.get('alert_thresholds', {
            'cpu_percent': 80.0,
            'memory_percent': 80.0,
            'disk_percent': 90.0,
            'temperature': 80.0,
            'processing_time': 5.0
        })
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Performance history
        self.performance_history = []
        self.alerts = []
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Statistics
        self.stats = {
            'monitoring_start_time': None,
            'total_samples': 0,
            'alerts_generated': 0,
            'performance_issues': 0
        }
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for performance monitor"""
        logger = logging.getLogger('PerformanceMonitor')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'performance_monitor_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def get_system_metrics(self) -> Dict:
        """Get comprehensive system metrics"""
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
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            # Temperature (if available)
            try:
                temperatures = psutil.sensors_temperatures()
                cpu_temp = None
                if 'cpu_thermal' in temperatures:
                    cpu_temp = temperatures['cpu_thermal'][0].current
                elif 'coretemp' in temperatures:
                    cpu_temp = temperatures['coretemp'][0].current
            except:
                cpu_temp = None
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None,
                    'process_percent': process_cpu
                },
                'memory': {
                    'total_mb': memory.total / 1024 / 1024,
                    'available_mb': memory.available / 1024 / 1024,
                    'used_mb': memory.used / 1024 / 1024,
                    'percent': memory.percent,
                    'process_rss_mb': process_memory.rss / 1024 / 1024,
                    'process_vms_mb': process_memory.vms / 1024 / 1024
                },
                'swap': {
                    'total_mb': swap.total / 1024 / 1024,
                    'used_mb': swap.used / 1024 / 1024,
                    'percent': swap.percent
                },
                'disk': {
                    'total_gb': disk.total / 1024 / 1024 / 1024,
                    'used_gb': disk.used / 1024 / 1024 / 1024,
                    'free_gb': disk.free / 1024 / 1024 / 1024,
                    'percent': (disk.used / disk.total) * 100,
                    'read_mb': disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
                    'write_mb': disk_io.write_bytes / 1024 / 1024 if disk_io else 0
                },
                'network': {
                    'bytes_sent_mb': network_io.bytes_sent / 1024 / 1024,
                    'bytes_recv_mb': network_io.bytes_recv / 1024 / 1024,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv
                },
                'temperature': {
                    'cpu_celsius': cpu_temp
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    def check_alerts(self, metrics: Dict) -> List[Dict]:
        """Check for performance alerts"""
        alerts = []
        
        try:
            # CPU alert
            if metrics.get('cpu', {}).get('percent', 0) > self.alert_thresholds['cpu_percent']:
                alerts.append({
                    'type': 'high_cpu',
                    'severity': 'warning',
                    'message': f"High CPU usage: {metrics['cpu']['percent']:.1f}%",
                    'value': metrics['cpu']['percent'],
                    'threshold': self.alert_thresholds['cpu_percent']
                })
            
            # Memory alert
            if metrics.get('memory', {}).get('percent', 0) > self.alert_thresholds['memory_percent']:
                alerts.append({
                    'type': 'high_memory',
                    'severity': 'warning',
                    'message': f"High memory usage: {metrics['memory']['percent']:.1f}%",
                    'value': metrics['memory']['percent'],
                    'threshold': self.alert_thresholds['memory_percent']
                })
            
            # Disk alert
            if metrics.get('disk', {}).get('percent', 0) > self.alert_thresholds['disk_percent']:
                alerts.append({
                    'type': 'high_disk',
                    'severity': 'critical',
                    'message': f"High disk usage: {metrics['disk']['percent']:.1f}%",
                    'value': metrics['disk']['percent'],
                    'threshold': self.alert_thresholds['disk_percent']
                })
            
            # Temperature alert
            cpu_temp = metrics.get('temperature', {}).get('cpu_celsius')
            if cpu_temp and cpu_temp > self.alert_thresholds['temperature']:
                alerts.append({
                    'type': 'high_temperature',
                    'severity': 'critical',
                    'message': f"High CPU temperature: {cpu_temp:.1f}°C",
                    'value': cpu_temp,
                    'threshold': self.alert_thresholds['temperature']
                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to check alerts: {e}")
            return []
    
    def monitor_performance(self):
        """Performance monitoring worker"""
        self.logger.info("Performance monitoring started")
        
        while self.is_monitoring:
            try:
                # Get system metrics
                metrics = self.get_system_metrics()
                
                if metrics:
                    # Check for alerts
                    alerts = self.check_alerts(metrics)
                    
                    # Add alerts to history
                    if alerts:
                        for alert in alerts:
                            alert['timestamp'] = datetime.now().isoformat()
                            self.alerts.append(alert)
                            self.stats['alerts_generated'] += 1
                            
                            # Log alert
                            if alert['severity'] == 'critical':
                                self.logger.critical(f"ALERT: {alert['message']}")
                            else:
                                self.logger.warning(f"ALERT: {alert['message']}")
                    
                    # Add metrics to history
                    with self.lock:
                        self.performance_history.append(metrics)
                        self.stats['total_samples'] += 1
                        
                        # Keep only recent history
                        if len(self.performance_history) > self.history_size:
                            self.performance_history = self.performance_history[-self.history_size:]
                    
                    # Log performance summary periodically
                    if self.stats['total_samples'] % 12 == 0:  # Every minute (12 * 5s)
                        self.logger.info(f"Performance: CPU {metrics['cpu']['percent']:.1f}%, "
                                       f"Memory {metrics['memory']['percent']:.1f}%, "
                                       f"Disk {metrics['disk']['percent']:.1f}%")
                
                # Wait for next check
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")
                time.sleep(5)
        
        self.logger.info("Performance monitoring stopped")
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.stats['monitoring_start_time'] = datetime.now()
            self.monitor_thread = threading.Thread(target=self.monitor_performance)
            self.monitor_thread.start()
            self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            self.logger.info("Performance monitoring stopped")
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        with self.lock:
            if not self.performance_history:
                return {}
            
            # Get recent metrics (last 10 samples)
            recent_metrics = self.performance_history[-10:]
            
            # Calculate averages
            cpu_avg = np.mean([m['cpu']['percent'] for m in recent_metrics])
            memory_avg = np.mean([m['memory']['percent'] for m in recent_metrics])
            disk_avg = np.mean([m['disk']['percent'] for m in recent_metrics])
            
            # Get current metrics
            current_metrics = self.performance_history[-1] if self.performance_history else {}
            
            return {
                'current': current_metrics,
                'averages': {
                    'cpu_percent': cpu_avg,
                    'memory_percent': memory_avg,
                    'disk_percent': disk_avg
                },
                'alerts': self.alerts[-10:] if self.alerts else [],
                'stats': self.stats.copy()
            }
    
    def get_performance_report(self) -> str:
        """Generate performance report"""
        summary = self.get_performance_summary()
        
        if not summary:
            return "No performance data available"
        
        current = summary.get('current', {})
        averages = summary.get('averages', {})
        alerts = summary.get('alerts', [])
        stats = summary.get('stats', {})
        
        uptime = 0
        if stats.get('monitoring_start_time'):
            uptime = (datetime.now() - stats['monitoring_start_time']).total_seconds()
        
        report = f"""
Performance Monitor Report
=========================
Monitoring Uptime: {uptime:.0f} seconds
Total Samples: {stats.get('total_samples', 0)}
Alerts Generated: {stats.get('alerts_generated', 0)}

Current Performance:
- CPU Usage: {current.get('cpu', {}).get('percent', 0):.1f}%
- Memory Usage: {current.get('memory', {}).get('percent', 0):.1f}%
- Disk Usage: {current.get('disk', {}).get('percent', 0):.1f}%
- CPU Temperature: {current.get('temperature', {}).get('cpu_celsius', 'N/A')}°C

Average Performance (Last 10 samples):
- CPU Usage: {averages.get('cpu_percent', 0):.1f}%
- Memory Usage: {averages.get('memory_percent', 0):.1f}%
- Disk Usage: {averages.get('disk_percent', 0):.1f}%

Recent Alerts ({len(alerts)}):
"""
        
        for alert in alerts[-5:]:  # Show last 5 alerts
            report += f"- {alert['severity'].upper()}: {alert['message']}\n"
        
        return report
    
    def save_performance_data(self, filename: str = None):
        """Save performance data to file"""
        try:
            if filename is None:
                filename = f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            log_dir = Path(__file__).parent.parent.parent / 'logs'
            file_path = log_dir / filename
            
            data = {
                'performance_history': self.performance_history,
                'alerts': self.alerts,
                'stats': self.stats,
                'exported_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Performance data saved to: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save performance data: {e}")
    
    def optimize_system(self) -> Dict:
        """Provide system optimization recommendations"""
        recommendations = []
        
        try:
            summary = self.get_performance_summary()
            current = summary.get('current', {})
            averages = summary.get('averages', {})
            
            # CPU optimization
            if averages.get('cpu_percent', 0) > 70:
                recommendations.append({
                    'type': 'cpu',
                    'priority': 'high',
                    'message': 'High CPU usage detected. Consider reducing processing frequency or optimizing algorithms.',
                    'action': 'Reduce batch size or increase processing intervals'
                })
            
            # Memory optimization
            if averages.get('memory_percent', 0) > 80:
                recommendations.append({
                    'type': 'memory',
                    'priority': 'high',
                    'message': 'High memory usage detected. Consider implementing memory pooling or reducing cache sizes.',
                    'action': 'Enable memory cleanup or reduce batch size'
                })
            
            # Disk optimization
            if averages.get('disk_percent', 0) > 85:
                recommendations.append({
                    'type': 'disk',
                    'priority': 'critical',
                    'message': 'High disk usage detected. Consider cleaning up old logs and temporary files.',
                    'action': 'Clean up logs and temporary files'
                })
            
            # Temperature optimization
            cpu_temp = current.get('temperature', {}).get('cpu_celsius')
            if cpu_temp and cpu_temp > 75:
                recommendations.append({
                    'type': 'temperature',
                    'priority': 'high',
                    'message': 'High CPU temperature detected. Consider improving cooling or reducing CPU load.',
                    'action': 'Check cooling system or reduce processing load'
                })
            
            return {
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate optimization recommendations: {e}")
            return {'recommendations': [], 'error': str(e)}
