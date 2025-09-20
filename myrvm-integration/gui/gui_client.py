#!/usr/bin/env python3
"""
GUI Client for LED Touch Screen
Main GUI application for user interaction on Jetson Orin
"""

import json
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import io
import base64

from gui.qr_code_generator import QRCodeGenerator
from gui.user_authentication import UserAuthenticationHandler, UserSession

class GUIClient:
    """Main GUI Client for LED Touch Screen"""
    
    def __init__(self, rvm_id: str = "jetson_orin_nano_001", 
                 host: str = "0.0.0.0", port: int = 5001,
                 api_client=None, service_integration=None):
        """
        Initialize GUI Client
        
        Args:
            rvm_id: RVM identifier
            host: Host address for Flask app
            port: Port for Flask app
            api_client: API client instance
            service_integration: Service integration instance
        """
        self.rvm_id = rvm_id
        self.host = host
        self.port = port
        self.api_client = api_client
        self.service_integration = service_integration
        
        # Initialize components
        self.qr_generator = QRCodeGenerator(rvm_id)
        self.auth_handler = UserAuthenticationHandler(api_client, rvm_id)
        
        # Current state
        self.current_user_session = None
        self.current_screen = "login"  # login, main, profile, settings
        self.system_info = {}
        self.detection_results = []
        
        # Flask app
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        CORS(self.app)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Setup Flask routes
        self._setup_routes()
        
        # Setup callbacks
        self._setup_callbacks()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for GUI client"""
        logger = logging.getLogger('GUIClient')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'gui_client_{datetime.now().strftime("%Y%m%d")}.log'
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
            """Main page"""
            return render_template('index.html', 
                                 rvm_id=self.rvm_id,
                                 current_screen=self.current_screen)
        
        @self.app.route('/api/qr-code')
        def get_qr_code():
            """Get QR code for login"""
            try:
                qr_base64, qr_data = self.qr_generator.generate_qr_code_base64("login")
                return jsonify({
                    'success': True,
                    'qr_code': qr_base64,
                    'qr_data': qr_data
                })
            except Exception as e:
                self.logger.error(f"Failed to generate QR code: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/authenticate', methods=['POST'])
        def authenticate():
            """Authenticate user via QR code"""
            try:
                data = request.get_json()
                qr_data = data.get('qr_data', {})
                
                success, session = self.auth_handler.authenticate_user(qr_data)
                
                if success:
                    self.current_user_session = session
                    self.current_screen = "main"
                    
                    return jsonify({
                        'success': True,
                        'session': {
                            'session_id': session.session_id,
                            'user': {
                                'name': session.user_profile.name,
                                'email': session.user_profile.email,
                                'balance': session.user_profile.balance
                            }
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Authentication failed'
                    }), 401
                    
            except Exception as e:
                self.logger.error(f"Authentication error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/logout', methods=['POST'])
        def logout():
            """Logout user"""
            try:
                if self.current_user_session:
                    self.auth_handler.terminate_session(
                        self.current_user_session.session_id, 
                        "User logout"
                    )
                    self.current_user_session = None
                    self.current_screen = "login"
                
                return jsonify({
                    'success': True,
                    'message': 'Logged out successfully'
                })
                
            except Exception as e:
                self.logger.error(f"Logout error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/status')
        def get_status():
            """Get system status"""
            try:
                status = {
                    'rvm_id': self.rvm_id,
                    'current_screen': self.current_screen,
                    'user_session': None,
                    'system_info': self.system_info,
                    'detection_results': self.detection_results[-10:],  # Last 10 results
                    'auth_status': self.auth_handler.get_authentication_status()
                }
                
                if self.current_user_session:
                    status['user_session'] = {
                        'session_id': self.current_user_session.session_id,
                        'user': {
                            'name': self.current_user_session.user_profile.name,
                            'email': self.current_user_session.user_profile.email,
                            'balance': self.current_user_session.user_profile.balance
                        },
                        'start_time': self.current_user_session.start_time.isoformat(),
                        'last_activity': self.current_user_session.last_activity.isoformat()
                    }
                
                return jsonify({
                    'success': True,
                    'status': status
                })
                
            except Exception as e:
                self.logger.error(f"Status error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/detection-results')
        def get_detection_results():
            """Get detection results"""
            try:
                return jsonify({
                    'success': True,
                    'results': self.detection_results[-20:]  # Last 20 results
                })
                
            except Exception as e:
                self.logger.error(f"Detection results error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/system-info')
        def get_system_info():
            """Get system information"""
            try:
                system_info = self._get_system_info()
                return jsonify({
                    'success': True,
                    'system_info': system_info
                })
                
            except Exception as e:
                self.logger.error(f"System info error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/change-screen', methods=['POST'])
        def change_screen():
            """Change current screen"""
            try:
                data = request.get_json()
                screen = data.get('screen', 'login')
                
                if screen in ['login', 'main', 'profile', 'settings']:
                    self.current_screen = screen
                    return jsonify({
                        'success': True,
                        'current_screen': self.current_screen
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid screen'
                    }), 400
                    
            except Exception as e:
                self.logger.error(f"Change screen error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def _setup_callbacks(self):
        """Setup callbacks for real-time updates"""
        
        def auth_callback(session: UserSession, action: str):
            """Authentication callback"""
            if action == "login":
                self.logger.info(f"User logged in: {session.user_profile.name}")
            elif action == "logout":
                self.logger.info(f"User logged out: {session.user_profile.name}")
        
        self.auth_handler.register_authentication_callback(auth_callback)
    
    def _start_background_tasks(self):
        """Start background tasks"""
        # Start system info update thread
        self.system_info_thread = threading.Thread(
            target=self._update_system_info_loop,
            daemon=True,
            name="SystemInfoThread"
        )
        self.system_info_thread.start()
        
        # Start detection results update thread
        self.detection_thread = threading.Thread(
            target=self._update_detection_results_loop,
            daemon=True,
            name="DetectionResultsThread"
        )
        self.detection_thread.start()
        
        self.logger.info("Background tasks started")
    
    def _update_system_info_loop(self):
        """Update system information loop"""
        while True:
            try:
                self.system_info = self._get_system_info()
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                self.logger.error(f"System info update error: {e}")
                time.sleep(10)
    
    def _update_detection_results_loop(self):
        """Update detection results loop"""
        while True:
            try:
                if self.service_integration and 'detection' in self.service_integration.services:
                    # Get detection results from service integration
                    detection_service = self.service_integration.services['detection']
                    if hasattr(detection_service, 'get_recent_results'):
                        results = detection_service.get_recent_results()
                        self.detection_results.extend(results)
                        
                        # Keep only last 100 results
                        if len(self.detection_results) > 100:
                            self.detection_results = self.detection_results[-100:]
                
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                self.logger.error(f"Detection results update error: {e}")
                time.sleep(10)
    
    def _get_system_info(self) -> Dict:
        """Get system information"""
        try:
            system_info = {
                'timestamp': datetime.now().isoformat(),
                'rvm_id': self.rvm_id,
                'uptime': 'N/A',
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'gpu_usage': 0.0,
                'temperature': 0.0,
                'services_status': {}
            }
            
            # Get service integration status if available
            if self.service_integration:
                integration_status = self.service_integration.get_integration_status()
                system_info.update({
                    'uptime': integration_status.get('uptime', 'N/A'),
                    'services_status': integration_status
                })
                
                # Get service metrics
                service_metrics = self.service_integration.get_service_metrics()
                for service_name, metrics in service_metrics.items():
                    system_info['services_status'][service_name] = {
                        'cpu_usage': metrics.get('cpu_usage', 0.0),
                        'memory_usage': metrics.get('memory_usage', 0.0),
                        'status': 'running' if metrics.get('cpu_usage', 0) > 0 else 'stopped'
                    }
            
            return system_info
            
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'rvm_id': self.rvm_id,
                'error': str(e)
            }
    
    def start(self):
        """Start GUI client"""
        try:
            self.logger.info(f"Starting GUI Client on {self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
        except Exception as e:
            self.logger.error(f"Failed to start GUI client: {e}")
            raise
    
    def stop(self):
        """Stop GUI client"""
        try:
            self.logger.info("Stopping GUI Client...")
            
            # Stop background tasks
            if hasattr(self, 'system_info_thread'):
                # Threads will stop when daemon=True and main thread exits
                pass
            
            # Shutdown components
            self.auth_handler.shutdown()
            
            self.logger.info("GUI Client stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping GUI client: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test GUI client
    gui_client = GUIClient("jetson_orin_nano_001")
    
    try:
        print("Starting GUI Client...")
        print(f"Access the GUI at: http://localhost:5001")
        print("Press Ctrl+C to stop")
        
        gui_client.start()
        
    except KeyboardInterrupt:
        print("\nStopping GUI Client...")
        gui_client.stop()
        print("GUI Client stopped")
    except Exception as e:
        print(f"Error: {e}")
        gui_client.stop()

