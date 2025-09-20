#!/usr/bin/env python3
"""
Advanced Monitoring Dashboard Server for MyRVM Platform Integration
Real-time web-based monitoring interface with interactive charts
"""

import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from flask import Flask, render_template, jsonify, request, Response
import psutil
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now

class MonitoringDashboard:
    """Advanced monitoring dashboard server"""
    
    def __init__(self, config: Dict, metrics_collector=None, alerting_engine=None):
        """
        Initialize monitoring dashboard
        
        Args:
            config: Configuration dictionary
            metrics_collector: Metrics collector instance
            alerting_engine: Alerting engine instance
        """
        self.config = config
        self.metrics_collector = metrics_collector
        self.alerting_engine = alerting_engine
        
        # Dashboard settings
        self.host = config.get('dashboard_host', '0.0.0.0')
        self.port = config.get('dashboard_port', 5001)
        self.debug = config.get('dashboard_debug', False)
        self.refresh_interval = config.get('dashboard_refresh_interval', 5)
        
        # Setup Flask app
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent.parent / 'templates'),
                        static_folder=str(Path(__file__).parent.parent / 'static'))
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Dashboard data
        self.dashboard_data = {
            'system_status': 'unknown',
            'last_update': None,
            'uptime': 0,
            'alerts_count': 0
        }
        
        # Setup routes
        self._setup_routes()
        
        # Start background data update
        self._start_data_update_thread()
        
        self.logger.info("Monitoring dashboard initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for dashboard"""
        logger = logging.getLogger('MonitoringDashboard')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'dashboard_server_{now().strftime("%Y%m%d")}.log'
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
        def index():
            """Main dashboard page"""
            return render_template('dashboard.html', 
                                 title='MyRVM Platform Integration - Monitoring Dashboard',
                                 refresh_interval=self.refresh_interval * 1000)
        
        @self.app.route('/api/status')
        def api_status():
            """Get system status"""
            try:
                status = self._get_system_status()
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Error getting system status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """Get current metrics"""
            try:
                if self.metrics_collector:
                    metrics = self.metrics_collector.get_current_metrics()
                else:
                    metrics = self._get_fallback_metrics()
                return jsonify(metrics)
            except Exception as e:
                self.logger.error(f"Error getting metrics: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/metrics/history')
        def api_metrics_history():
            """Get metrics history"""
            try:
                metric_name = request.args.get('metric', 'system.cpu.percent')
                limit = int(request.args.get('limit', 100))
                
                if self.metrics_collector:
                    history = self.metrics_collector.get_metrics_history(metric_name, limit)
                else:
                    history = []
                
                return jsonify(history)
            except Exception as e:
                self.logger.error(f"Error getting metrics history: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """Get alerts"""
            try:
                if self.alerting_engine:
                    active_alerts = self.alerting_engine.get_active_alerts()
                    alert_history = self.alerting_engine.get_alert_history(50)
                else:
                    active_alerts = {}
                    alert_history = []
                
                return jsonify({
                    'active': active_alerts,
                    'history': alert_history
                })
            except Exception as e:
                self.logger.error(f"Error getting alerts: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/health')
        def api_health():
            """Health check endpoint"""
            try:
                health = self._get_health_status()
                return jsonify(health)
            except Exception as e:
                self.logger.error(f"Error getting health status: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config')
        def api_config():
            """Get configuration"""
            try:
                config_data = {
                    'environment': self.config.get('environment', 'unknown'),
                    'refresh_interval': self.refresh_interval,
                    'dashboard_version': '1.0.0',
                    'features': {
                        'metrics_collector': self.metrics_collector is not None,
                        'alerting_engine': self.alerting_engine is not None
                    }
                }
                return jsonify(config_data)
            except Exception as e:
                self.logger.error(f"Error getting config: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/export')
        def api_export():
            """Export metrics data"""
            try:
                format_type = request.args.get('format', 'json')
                
                if self.metrics_collector:
                    if format_type == 'json':
                        data = self.metrics_collector.get_current_metrics()
                        return jsonify(data)
                    elif format_type == 'prometheus':
                        data = self.metrics_collector.export_metrics('prometheus')
                        return Response(data, mimetype='text/plain')
                    else:
                        return jsonify({'error': 'Unsupported format'}), 400
                else:
                    return jsonify({'error': 'Metrics collector not available'}), 503
                    
            except Exception as e:
                self.logger.error(f"Error exporting data: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _get_system_status(self) -> Dict:
        """Get system status"""
        try:
            # Get basic system info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # Determine overall status
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
                status = 'critical'
            elif cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
                status = 'warning'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'timestamp': now().isoformat(),
                'uptime': time.time() - process.create_time(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'process_memory_mb': process_memory.rss / (1024**2),
                'alerts_count': len(self.alerting_engine.get_active_alerts()) if self.alerting_engine else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                'status': 'error',
                'timestamp': now().isoformat(),
                'error': str(e)
            }
    
    def _get_fallback_metrics(self) -> Dict:
        """Get fallback metrics when metrics collector is not available"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            process = psutil.Process()
            
            return {
                'timestamp': now().isoformat(),
                'system': {
                    'cpu': {
                        'percent': cpu_percent,
                        'count': psutil.cpu_count()
                    },
                    'memory': {
                        'total_gb': memory.total / (1024**3),
                        'used_gb': memory.used / (1024**3),
                        'percent': memory.percent
                    },
                    'disk': {
                        'total_gb': disk.total / (1024**3),
                        'used_gb': disk.used / (1024**3),
                        'percent': (disk.used / disk.total) * 100
                    },
                    'process': {
                        'memory_rss_mb': process.memory_info().rss / (1024**2),
                        'cpu_percent': process.cpu_percent()
                    }
                },
                'application': {
                    'uptime_seconds': time.time() - process.create_time()
                },
                'business': {},
                'network': {},
                'gpu': {}
            }
            
        except Exception as e:
            self.logger.error(f"Error getting fallback metrics: {e}")
            return {
                'timestamp': now().isoformat(),
                'error': str(e)
            }
    
    def _get_health_status(self) -> Dict:
        """Get health status"""
        try:
            health = {
                'status': 'healthy',
                'timestamp': now().isoformat(),
                'components': {
                    'dashboard': 'healthy',
                    'metrics_collector': 'healthy' if self.metrics_collector else 'unavailable',
                    'alerting_engine': 'healthy' if self.alerting_engine else 'unavailable'
                },
                'checks': []
            }
            
            # Check metrics collector
            if self.metrics_collector:
                if self.metrics_collector.is_collecting:
                    health['components']['metrics_collector'] = 'healthy'
                else:
                    health['components']['metrics_collector'] = 'unhealthy'
                    health['checks'].append('Metrics collector not running')
            
            # Check alerting engine
            if self.alerting_engine:
                active_alerts = self.alerting_engine.get_active_alerts()
                if len(active_alerts) > 0:
                    health['components']['alerting_engine'] = 'warning'
                    health['checks'].append(f'{len(active_alerts)} active alerts')
                else:
                    health['components']['alerting_engine'] = 'healthy'
            
            # Determine overall health
            component_statuses = list(health['components'].values())
            if 'unhealthy' in component_statuses:
                health['status'] = 'unhealthy'
            elif 'warning' in component_statuses or 'unavailable' in component_statuses:
                health['status'] = 'warning'
            
            return health
            
        except Exception as e:
            self.logger.error(f"Error getting health status: {e}")
            return {
                'status': 'error',
                'timestamp': now().isoformat(),
                'error': str(e)
            }
    
    def _start_data_update_thread(self):
        """Start background data update thread"""
        def update_data():
            while True:
                try:
                    # Update dashboard data
                    self.dashboard_data.update({
                        'system_status': self._get_system_status(),
                        'last_update': now().isoformat(),
                        'uptime': time.time() - psutil.Process().create_time(),
                        'alerts_count': len(self.alerting_engine.get_active_alerts()) if self.alerting_engine else 0
                    })
                    
                    time.sleep(self.refresh_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in data update thread: {e}")
                    time.sleep(5)
        
        update_thread = threading.Thread(target=update_data, daemon=True)
        update_thread.start()
        self.logger.info("Data update thread started")
    
    def start(self):
        """Start dashboard server"""
        try:
            self.logger.info(f"Starting monitoring dashboard on {self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=self.debug, threaded=True)
        except Exception as e:
            self.logger.error(f"Error starting dashboard server: {e}")
            raise
    
    def stop(self):
        """Stop dashboard server"""
        try:
            self.logger.info("Stopping monitoring dashboard")
            # Flask doesn't have a built-in stop method, so we'll just log
            # In a real implementation, you might use a different WSGI server
        except Exception as e:
            self.logger.error(f"Error stopping dashboard server: {e}")
    
    def get_dashboard_info(self) -> Dict:
        """Get dashboard information"""
        try:
            return {
                'host': self.host,
                'port': self.port,
                'url': f"http://{self.host}:{self.port}",
                'refresh_interval': self.refresh_interval,
                'features': {
                    'metrics_collector': self.metrics_collector is not None,
                    'alerting_engine': self.alerting_engine is not None
                },
                'status': 'running'
            }
        except Exception as e:
            self.logger.error(f"Error getting dashboard info: {e}")
            return {}
    
    def get_dashboard_report(self) -> str:
        """Generate dashboard report"""
        try:
            info = self.get_dashboard_info()
            health = self._get_health_status()
            
            report = f"""
Monitoring Dashboard Report
==========================
URL: {info.get('url', 'N/A')}
Host: {info.get('host', 'N/A')}
Port: {info.get('port', 'N/A')}
Refresh Interval: {info.get('refresh_interval', 'N/A')}s

Features:
- Metrics Collector: {'Enabled' if info.get('features', {}).get('metrics_collector') else 'Disabled'}
- Alerting Engine: {'Enabled' if info.get('features', {}).get('alerting_engine') else 'Disabled'}

Health Status: {health.get('status', 'unknown')}
Components:
"""
            
            for component, status in health.get('components', {}).items():
                report += f"- {component}: {status}\n"
            
            if health.get('checks'):
                report += "\nHealth Checks:\n"
                for check in health['checks']:
                    report += f"- {check}\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard report: {e}")
            return f"Error generating dashboard report: {e}"
