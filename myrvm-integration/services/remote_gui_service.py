#!/usr/bin/env python3
"""
Remote GUI Service for MyRVM Platform Integration
Provides web-based control interface for remote RVM management
"""

import json
import time
import logging
import threading
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from flask import Flask, render_template, jsonify, request, Response
import subprocess
import os

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "api-client"))

from myrvm_api_client import MyRVMAPIClient
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now

class RemoteGUIService:
    """Remote GUI service with web interface for RVM control"""
    
    def __init__(self, config: Dict):
        """
        Initialize remote GUI service
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.port = config.get('remote_gui', {}).get('port', 5001)
        self.host = config.get('remote_gui', {}).get('host', '0.0.0.0')
        self.rvm_id = config.get('rvm_id', 1)
        
        # Initialize components
        self.api_client = MyRVMAPIClient(
            base_url=config.get('myrvm_base_url'),
            use_tunnel=config.get('use_tunnel', False)
        )
        
        # Setup Flask app
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # System monitoring
        self.monitoring_data = {
            'start_time': time.time(),
            'last_update': time.time(),
            'system_stats': {},
            'service_status': {}
        }
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for remote GUI service"""
        logger = logging.getLogger('RemoteGUIService')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'remote_gui_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard"""
            return render_template('remote_gui.html', rvm_id=self.rvm_id)
        
        @self.app.route('/dashboard')
        def dashboard():
            """Dashboard data"""
            return jsonify(self.get_dashboard_data())
        
        @self.app.route('/system/status')
        def system_status():
            """Get system status"""
            return jsonify(self.get_system_status())
        
        @self.app.route('/system/metrics')
        def system_metrics():
            """Get system metrics"""
            return jsonify(self.get_system_metrics())
        
        @self.app.route('/system/control', methods=['POST'])
        def system_control():
            """System control endpoint"""
            data = request.get_json()
            action = data.get('action')
            
            if action == 'restart_services':
                return self.restart_services()
            elif action == 'update_system':
                return self.update_system()
            elif action == 'check_connectivity':
                return self.check_connectivity()
            else:
                return jsonify({'success': False, 'message': 'Invalid action'})
        
        @self.app.route('/camera/control')
        def camera_control():
            """Camera control panel"""
            return jsonify(self.get_camera_control_data())
        
        @self.app.route('/camera/control', methods=['POST'])
        def camera_control_action():
            """Camera control actions"""
            data = request.get_json()
            action = data.get('action')
            
            if action == 'start_camera':
                return self.start_camera_service()
            elif action == 'stop_camera':
                return self.stop_camera_service()
            elif action == 'restart_camera':
                return self.restart_camera_service()
            else:
                return jsonify({'success': False, 'message': 'Invalid action'})
        
        @self.app.route('/api/status')
        def api_status():
            """API connectivity status"""
            return jsonify(self.get_api_status())
        
        @self.app.route('/logs')
        def logs():
            """Get system logs"""
            return jsonify(self.get_system_logs())
    
    def get_dashboard_data(self) -> Dict:
        """Get dashboard data"""
        return {
            'rvm_id': self.rvm_id,
            'timestamp': now().isoformat(),
            'system_status': self.get_system_status(),
            'camera_status': self.get_camera_status(),
            'api_status': self.get_api_status(),
            'uptime': time.time() - self.monitoring_data['start_time']
        }
    
    def get_system_status(self) -> Dict:
        """Get system status"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Temperature (if available)
            try:
                temp = psutil.sensors_temperatures()
                gpu_temp = temp.get('gpu_thermal', [{}])[0].get('current', 'N/A')
            except:
                gpu_temp = 'N/A'
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': memory.available,
                'memory_total': memory.total,
                'disk_usage': disk.percent,
                'disk_free': disk.free,
                'disk_total': disk.total,
                'network_sent': network.bytes_sent,
                'network_recv': network.bytes_recv,
                'gpu_temperature': gpu_temp,
                'uptime': time.time() - self.monitoring_data['start_time'],
                'timestamp': now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def get_system_metrics(self) -> Dict:
        """Get system metrics"""
        try:
            # Process information
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Service status
            services = self.get_service_status()
            
            return {
                'processes': processes[:10],  # Top 10 processes
                'services': services,
                'timestamp': now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
            return {'error': str(e)}
    
    def get_service_status(self) -> Dict:
        """Get service status"""
        services = {}
        
        # Check camera service
        try:
            result = subprocess.run(['systemctl', 'is-active', 'rvm-remote-camera'], 
                                  capture_output=True, text=True)
            services['camera_service'] = result.stdout.strip()
        except:
            services['camera_service'] = 'unknown'
        
        # Check GUI service
        try:
            result = subprocess.run(['systemctl', 'is-active', 'rvm-remote-gui'], 
                                  capture_output=True, text=True)
            services['gui_service'] = result.stdout.strip()
        except:
            services['gui_service'] = 'unknown'
        
        # Check main integration service
        try:
            result = subprocess.run(['systemctl', 'is-active', 'myrvm-integration'], 
                                  capture_output=True, text=True)
            services['integration_service'] = result.stdout.strip()
        except:
            services['integration_service'] = 'unknown'
        
        return services
    
    def get_camera_status(self) -> Dict:
        """Get camera service status"""
        try:
            # Check if camera service is running
            result = subprocess.run(['systemctl', 'is-active', 'rvm-remote-camera'], 
                                  capture_output=True, text=True)
            status = result.stdout.strip()
            
            # Check port 5000
            port_status = self.check_port(5000)
            
            return {
                'service_status': status,
                'port_status': port_status,
                'port': 5000,
                'url': f'http://{self.get_local_ip()}:5000'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_camera_control_data(self) -> Dict:
        """Get camera control data"""
        return {
            'camera_status': self.get_camera_status(),
            'controls': [
                {'action': 'start_camera', 'label': 'Start Camera', 'icon': '▶️'},
                {'action': 'stop_camera', 'label': 'Stop Camera', 'icon': '⏹️'},
                {'action': 'restart_camera', 'label': 'Restart Camera', 'icon': '🔄'}
            ]
        }
    
    def get_api_status(self) -> Dict:
        """Get API connectivity status"""
        try:
            if self.api_client:
                success, response = self.api_client.test_connectivity()
                return {
                    'connected': success,
                    'response': response,
                    'base_url': self.api_client.current_url,
                    'timestamp': now().isoformat()
                }
            else:
                return {'connected': False, 'error': 'API client not initialized'}
        except Exception as e:
            return {'connected': False, 'error': str(e)}
    
    def get_system_logs(self) -> Dict:
        """Get system logs"""
        try:
            logs = []
            log_dir = Path(__file__).parent.parent / 'logs'
            
            if log_dir.exists():
                for log_file in log_dir.glob('*.log'):
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            logs.extend([{
                                'file': log_file.name,
                                'line': line.strip(),
                                'timestamp': datetime.now().isoformat()
                            } for line in lines[-50:]])  # Last 50 lines
                    except:
                        continue
            
            return {
                'logs': logs,
                'count': len(logs),
                'timestamp': now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def check_port(self, port: int) -> bool:
        """Check if port is open"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def restart_services(self) -> Dict:
        """Restart all services"""
        try:
            # Restart camera service
            subprocess.run(['sudo', 'systemctl', 'restart', 'rvm-remote-camera'], 
                         capture_output=True, text=True)
            
            # Restart GUI service
            subprocess.run(['sudo', 'systemctl', 'restart', 'rvm-remote-gui'], 
                         capture_output=True, text=True)
            
            return {'success': True, 'message': 'Services restarted successfully'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def update_system(self) -> Dict:
        """Update system packages"""
        try:
            result = subprocess.run(['sudo', 'apt', 'update'], 
                                  capture_output=True, text=True)
            return {'success': True, 'message': 'System updated', 'output': result.stdout}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def check_connectivity(self) -> Dict:
        """Check connectivity to MyRVM Platform"""
        try:
            if self.api_client:
                success, response = self.api_client.test_connectivity()
                return {
                    'success': success,
                    'message': 'Connectivity check completed',
                    'response': response
                }
            else:
                return {'success': False, 'message': 'API client not initialized'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def start_camera_service(self) -> Dict:
        """Start camera service"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'start', 'rvm-remote-camera'], 
                                  capture_output=True, text=True)
            return {'success': True, 'message': 'Camera service started'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def stop_camera_service(self) -> Dict:
        """Stop camera service"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'stop', 'rvm-remote-camera'], 
                                  capture_output=True, text=True)
            return {'success': True, 'message': 'Camera service stopped'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def restart_camera_service(self) -> Dict:
        """Restart camera service"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'rvm-remote-camera'], 
                                  capture_output=True, text=True)
            return {'success': True, 'message': 'Camera service restarted'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def start(self):
        """Start remote GUI service"""
        try:
            self.logger.info(f"Starting Remote GUI Service on {self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
        except Exception as e:
            self.logger.error(f"Error starting remote GUI service: {e}")
            return False
    
    def stop(self):
        """Stop remote GUI service"""
        self.logger.info("Remote GUI Service stopped")

# Main execution
if __name__ == "__main__":
    # Load configuration
    config_path = Path(__file__).parent.parent / 'main' / 'config.json'
    
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Create and start service
    service = RemoteGUIService(config)
    
    try:
        service.start()
    except KeyboardInterrupt:
        print("\n⏹️  Service stopped by user")
    finally:
        service.stop()
