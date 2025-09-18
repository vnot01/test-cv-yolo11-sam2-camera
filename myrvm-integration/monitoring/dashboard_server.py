#!/usr/bin/env python3
"""
Monitoring Dashboard Server for MyRVM Platform Integration
Real-time web-based monitoring dashboard
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from flask import Flask, render_template, jsonify, request, send_from_directory
import psutil

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "utils"))
sys.path.append(str(Path(__file__).parent.parent / "services"))

from performance_monitor import PerformanceMonitor
from monitoring_service import MonitoringService

class MonitoringDashboard:
    """Real-time monitoring dashboard server"""
    
    def __init__(self, config: Dict):
        """
        Initialize monitoring dashboard
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.host = config.get('dashboard_host', '0.0.0.0')
        self.port = config.get('dashboard_port', 5001)
        self.refresh_interval = config.get('dashboard_refresh_interval', 5)
        
        # Initialize Flask app
        self.app = Flask(__name__, 
                        template_folder='dashboard_templates',
                        static_folder='static')
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize monitoring components
        self.performance_monitor = PerformanceMonitor(config)
        self.monitoring_service = MonitoringService(config)
        
        # Dashboard data cache
        self.dashboard_data = {
            'system_metrics': {},
            'performance_metrics': {},
            'service_status': {},
            'alerts': [],
            'last_update': None
        }
        
        # Data collection thread
        self.data_collection_thread = None
        self.is_running = False
        
        # Setup Flask routes
        self._setup_routes()
        
        self.logger.info("Monitoring dashboard initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for monitoring dashboard"""
        logger = logging.getLogger('MonitoringDashboard')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'monitoring_dashboard_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get current metrics"""
            return jsonify(self.dashboard_data)
        
        @self.app.route('/api/system')
        def get_system_metrics():
            """Get system metrics"""
            return jsonify(self.dashboard_data.get('system_metrics', {}))
        
        @self.app.route('/api/performance')
        def get_performance_metrics():
            """Get performance metrics"""
            return jsonify(self.dashboard_data.get('performance_metrics', {}))
        
        @self.app.route('/api/services')
        def get_service_status():
            """Get service status"""
            return jsonify(self.dashboard_data.get('service_status', {}))
        
        @self.app.route('/api/alerts')
        def get_alerts():
            """Get current alerts"""
            return jsonify(self.dashboard_data.get('alerts', []))
        
        @self.app.route('/api/history/<metric>')
        def get_metric_history(metric):
            """Get metric history"""
            hours = request.args.get('hours', 24, type=int)
            return jsonify(self._get_metric_history(metric, hours))
        
        @self.app.route('/api/health')
        def get_health_status():
            """Get overall health status"""
            return jsonify(self._get_health_status())
        
        @self.app.route('/api/config')
        def get_config():
            """Get dashboard configuration"""
            return jsonify({
                'refresh_interval': self.refresh_interval,
                'host': self.host,
                'port': self.port
            })
    
    def _collect_dashboard_data(self):
        """Collect data for dashboard"""
        try:
            # System metrics
            system_metrics = self.performance_monitor.get_system_metrics()
            
            # Performance metrics
            performance_summary = self.performance_monitor.get_performance_summary()
            
            # Service status
            service_status = self.monitoring_service.get_status()
            
            # Alerts
            alerts = self._get_current_alerts()
            
            # Update dashboard data
            self.dashboard_data.update({
                'system_metrics': system_metrics,
                'performance_metrics': performance_summary,
                'service_status': service_status,
                'alerts': alerts,
                'last_update': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to collect dashboard data: {e}")
    
    def _get_current_alerts(self) -> List[Dict]:
        """Get current alerts"""
        alerts = []
        
        try:
            # Get performance summary for alert checking
            performance_summary = self.performance_monitor.get_performance_summary()
            current = performance_summary.get('current', {})
            averages = performance_summary.get('averages', {})
            
            # CPU alert
            cpu_percent = current.get('cpu', {}).get('percent', 0)
            if cpu_percent > 80:
                alerts.append({
                    'type': 'high_cpu',
                    'severity': 'warning' if cpu_percent < 90 else 'critical',
                    'message': f'High CPU usage: {cpu_percent:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Memory alert
            memory_percent = current.get('memory', {}).get('percent', 0)
            if memory_percent > 80:
                alerts.append({
                    'type': 'high_memory',
                    'severity': 'warning' if memory_percent < 90 else 'critical',
                    'message': f'High memory usage: {memory_percent:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Disk alert
            disk_percent = current.get('disk', {}).get('percent', 0)
            if disk_percent > 85:
                alerts.append({
                    'type': 'high_disk',
                    'severity': 'warning' if disk_percent < 95 else 'critical',
                    'message': f'High disk usage: {disk_percent:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Temperature alert
            cpu_temp = current.get('temperature', {}).get('cpu_celsius')
            if cpu_temp and cpu_temp > 75:
                alerts.append({
                    'type': 'high_temperature',
                    'severity': 'warning' if cpu_temp < 85 else 'critical',
                    'message': f'High CPU temperature: {cpu_temp:.1f}°C',
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            self.logger.error(f"Failed to get current alerts: {e}")
        
        return alerts
    
    def _get_metric_history(self, metric: str, hours: int) -> List[Dict]:
        """Get metric history"""
        try:
            # This is a simplified implementation
            # In production, you'd query a time-series database
            history = []
            
            # Generate sample historical data
            end_time = datetime.now()
            for i in range(hours * 12):  # 5-minute intervals
                timestamp = end_time - timedelta(minutes=i*5)
                
                # Generate sample data based on metric type
                if metric == 'cpu':
                    value = 30 + (i % 20)  # Sample CPU data
                elif metric == 'memory':
                    value = 40 + (i % 15)  # Sample memory data
                elif metric == 'disk':
                    value = 20 + (i % 10)  # Sample disk data
                else:
                    value = 50 + (i % 30)  # Default sample data
                
                history.append({
                    'timestamp': timestamp.isoformat(),
                    'value': value
                })
            
            return history[::-1]  # Reverse to get chronological order
            
        except Exception as e:
            self.logger.error(f"Failed to get metric history: {e}")
            return []
    
    def _get_health_status(self) -> Dict:
        """Get overall health status"""
        try:
            performance_summary = self.performance_monitor.get_performance_summary()
            current = performance_summary.get('current', {})
            alerts = self._get_current_alerts()
            
            # Calculate overall health score
            health_score = 100
            
            # Deduct points for high resource usage
            cpu_percent = current.get('cpu', {}).get('percent', 0)
            if cpu_percent > 80:
                health_score -= 20
            elif cpu_percent > 60:
                health_score -= 10
            
            memory_percent = current.get('memory', {}).get('percent', 0)
            if memory_percent > 80:
                health_score -= 20
            elif memory_percent > 60:
                health_score -= 10
            
            disk_percent = current.get('disk', {}).get('percent', 0)
            if disk_percent > 85:
                health_score -= 15
            elif disk_percent > 70:
                health_score -= 5
            
            # Deduct points for alerts
            critical_alerts = len([a for a in alerts if a.get('severity') == 'critical'])
            warning_alerts = len([a for a in alerts if a.get('severity') == 'warning'])
            
            health_score -= critical_alerts * 25
            health_score -= warning_alerts * 10
            
            # Ensure health score is not negative
            health_score = max(0, health_score)
            
            # Determine health status
            if health_score >= 90:
                status = 'healthy'
            elif health_score >= 70:
                status = 'warning'
            elif health_score >= 50:
                status = 'degraded'
            else:
                status = 'critical'
            
            return {
                'status': status,
                'score': health_score,
                'alerts': {
                    'critical': critical_alerts,
                    'warning': warning_alerts,
                    'total': len(alerts)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {e}")
            return {
                'status': 'unknown',
                'score': 0,
                'alerts': {'critical': 0, 'warning': 0, 'total': 0},
                'timestamp': datetime.now().isoformat()
            }
    
    def _data_collection_worker(self):
        """Data collection worker thread"""
        self.logger.info("Data collection worker started")
        
        while self.is_running:
            try:
                self._collect_dashboard_data()
                time.sleep(self.refresh_interval)
            except Exception as e:
                self.logger.error(f"Data collection worker error: {e}")
                time.sleep(5)
        
        self.logger.info("Data collection worker stopped")
    
    def start(self):
        """Start monitoring dashboard"""
        try:
            # Start monitoring components
            self.performance_monitor.start_monitoring()
            self.monitoring_service.start()
            
            # Start data collection
            self.is_running = True
            self.data_collection_thread = threading.Thread(target=self._data_collection_worker)
            self.data_collection_thread.start()
            
            # Start Flask app
            self.logger.info(f"Starting monitoring dashboard on {self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring dashboard: {e}")
            raise
    
    def stop(self):
        """Stop monitoring dashboard"""
        self.logger.info("Stopping monitoring dashboard...")
        
        # Stop data collection
        self.is_running = False
        if self.data_collection_thread:
            self.data_collection_thread.join(timeout=5)
        
        # Stop monitoring components
        self.performance_monitor.stop_monitoring()
        self.monitoring_service.stop()
        
        self.logger.info("Monitoring dashboard stopped")
    
    def get_dashboard_status(self) -> Dict:
        """Get dashboard status"""
        return {
            'is_running': self.is_running,
            'host': self.host,
            'port': self.port,
            'refresh_interval': self.refresh_interval,
            'last_update': self.dashboard_data.get('last_update'),
            'data_collection_active': self.data_collection_thread and self.data_collection_thread.is_alive()
        }
