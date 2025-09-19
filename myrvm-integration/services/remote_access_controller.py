#!/usr/bin/env python3
"""
Remote Access Controller for MyRVM Platform Integration
Manages remote access sessions and provides API endpoints
"""

import os
import sys
import json
import time
import logging
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from flask import Flask, request, jsonify, render_template

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "api-client"))

from myrvm_api_client import MyRVMAPIClient
from services.ondemand_camera_manager import OnDemandCameraManager
from utils.timezone_manager import get_timezone_manager, now, format_datetime

class RemoteAccessController:
    """
    Remote access controller for managing remote access sessions.
    Provides API endpoints for MyRVM Platform integration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.rvm_id = config.get('rvm_id', 1)
        self.port = config.get('remote_access', {}).get('controller_port', 5001)
        self.host = config.get('remote_access', {}).get('host', '0.0.0.0')
        self.authentication_required = config.get('remote_access', {}).get('authentication_required', True)
        self.session_timeout = config.get('remote_access', {}).get('session_timeout', 3600)
        
        # Initialize components
        self.api_client = MyRVMAPIClient(
            base_url=config.get('myrvm_base_url'),
            use_tunnel=config.get('use_tunnel', False)
        )
        
        self.camera_manager = OnDemandCameraManager(config)
        
        # Session management
        self.active_sessions = {}
        self.session_lock = threading.Lock()
        
        # Setup Flask app
        self.app = Flask(__name__, template_folder=str(project_root / "templates"))
        self.setup_routes()
        
        # Setup logging
        self._setup_logger()
        
        # Load session data
        self.session_file = project_root / "data" / "remote_sessions.json"
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_sessions()
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
    def _setup_logger(self):
        """Setup logger for remote access controller."""
        log_dir = project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'remote_access_{now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def _load_sessions(self):
        """Load active sessions from file."""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    self.active_sessions = data.get('sessions', {})
                    self.logger.info(f"Loaded {len(self.active_sessions)} active sessions")
        except Exception as e:
            self.logger.warning(f"Could not load sessions: {e}")
            
    def _save_sessions(self):
        """Save active sessions to file."""
        try:
            data = {
                'sessions': self.active_sessions,
                'last_updated': now().isoformat()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Could not save sessions: {e}")
    
    def _start_cleanup_thread(self):
        """Start cleanup thread for expired sessions."""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Check every 5 minutes
                    self._cleanup_expired_sessions()
                except Exception as e:
                    self.logger.error(f"Cleanup thread error: {e}")
        
        thread = threading.Thread(target=cleanup_worker, daemon=True)
        thread.start()
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            current_time = now()
            expired_sessions = []
            
            with self.session_lock:
                for session_id, session in self.active_sessions.items():
                    start_time = datetime.fromisoformat(session['start_time'])
                    duration = session.get('duration', self.session_timeout)
                    
                    if (current_time - start_time).total_seconds() > duration:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    self.logger.info(f"Cleaning up expired session: {session_id}")
                    self._end_session(session_id)
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
    
    def _authenticate_request(self, request) -> Tuple[bool, str]:
        """Authenticate incoming request."""
        try:
            if not self.authentication_required:
                return True, "Authentication disabled"
            
            # Check for API key in headers
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return False, "Missing API key"
            
            # Validate API key (simplified - in production, use proper validation)
            valid_keys = ['myrvm-platform-key', 'admin-key', 'operator-key']
            if api_key not in valid_keys:
                return False, "Invalid API key"
            
            return True, "Authentication successful"
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False, f"Authentication error: {e}"
    
    def _create_session(self, user_id: str, session_type: str = 'camera', 
                       duration: int = None) -> str:
        """Create a new remote access session."""
        try:
            session_id = str(uuid.uuid4())
            
            with self.session_lock:
                self.active_sessions[session_id] = {
                    'user_id': user_id,
                    'session_type': session_type,
                    'start_time': now().isoformat(),
                    'duration': duration or self.session_timeout,
                    'status': 'active',
                    'created_by': 'remote_access_controller'
                }
                
                self._save_sessions()
                
                self.logger.info(f"Created session {session_id} for user {user_id}")
                return session_id
                
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise
    
    def _end_session(self, session_id: str):
        """End a remote access session."""
        try:
            with self.session_lock:
                if session_id in self.active_sessions:
                    session = self.active_sessions[session_id]
                    session['status'] = 'ended'
                    session['end_time'] = now().isoformat()
                    
                    # Stop camera session if it's a camera session
                    if session.get('session_type') == 'camera':
                        self.camera_manager.stop_camera_session(session_id)
                    
                    del self.active_sessions[session_id]
                    self._save_sessions()
                    
                    self.logger.info(f"Ended session {session_id}")
                    
        except Exception as e:
            self.logger.error(f"Failed to end session: {e}")
    
    def setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard."""
            return render_template('remote_gui.html', 
                                 rvm_id=self.rvm_id,
                                 active_sessions=len(self.active_sessions))
        
        @self.app.route('/api/remote_access', methods=['POST'])
        def request_remote_access():
            """Request remote access."""
            try:
                # Authenticate request
                auth_success, auth_message = self._authenticate_request(request)
                if not auth_success:
                    return jsonify({'success': False, 'error': auth_message}), 401
                
                data = request.get_json()
                user_id = data.get('user_id', 'unknown')
                session_type = data.get('session_type', 'camera')
                duration = data.get('duration', self.session_timeout)
                
                # Create session
                session_id = self._create_session(user_id, session_type, duration)
                
                # Start camera session if requested
                if session_type == 'camera':
                    success, message = self.camera_manager.start_camera_session(
                        session_id, user_id, duration
                    )
                    
                    if not success:
                        self._end_session(session_id)
                        return jsonify({'success': False, 'error': message}), 500
                
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'session_type': session_type,
                    'duration': duration,
                    'camera_url': self.camera_manager.get_camera_url() if session_type == 'camera' else None,
                    'message': 'Remote access granted'
                })
                
            except Exception as e:
                self.logger.error(f"Remote access request error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/remote_status', methods=['GET'])
        def get_remote_status():
            """Get remote access status."""
            try:
                session_id = request.args.get('session_id')
                
                if session_id:
                    # Get specific session status
                    if session_id in self.active_sessions:
                        session = self.active_sessions[session_id]
                        camera_status = self.camera_manager.get_session_status(session_id)
                        
                        return jsonify({
                            'success': True,
                            'session_id': session_id,
                            'status': 'active',
                            'session': session,
                            'camera_status': camera_status
                        })
                    else:
                        return jsonify({'success': False, 'error': 'Session not found'}), 404
                else:
                    # Get all sessions status
                    return jsonify({
                        'success': True,
                        'total_sessions': len(self.active_sessions),
                        'active_sessions': list(self.active_sessions.keys()),
                        'sessions': self.active_sessions,
                        'camera_manager_status': self.camera_manager.get_status()
                    })
                    
            except Exception as e:
                self.logger.error(f"Remote status error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/end_session', methods=['POST'])
        def end_session():
            """End remote access session."""
            try:
                # Authenticate request
                auth_success, auth_message = self._authenticate_request(request)
                if not auth_success:
                    return jsonify({'success': False, 'error': auth_message}), 401
                
                data = request.get_json()
                session_id = data.get('session_id')
                
                if not session_id:
                    return jsonify({'success': False, 'error': 'Session ID required'}), 400
                
                if session_id not in self.active_sessions:
                    return jsonify({'success': False, 'error': 'Session not found'}), 404
                
                self._end_session(session_id)
                
                return jsonify({
                    'success': True,
                    'message': f'Session {session_id} ended successfully'
                })
                
            except Exception as e:
                self.logger.error(f"End session error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/camera_available', methods=['GET'])
        def check_camera_available():
            """Check if camera is available."""
            try:
                available = self.camera_manager.is_camera_available()
                camera_url = self.camera_manager.get_camera_url()
                
                return jsonify({
                    'success': True,
                    'camera_available': available,
                    'camera_url': camera_url,
                    'active_sessions': len(self.active_sessions)
                })
                
            except Exception as e:
                self.logger.error(f"Camera availability check error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/extend_session', methods=['POST'])
        def extend_session():
            """Extend session duration."""
            try:
                # Authenticate request
                auth_success, auth_message = self._authenticate_request(request)
                if not auth_success:
                    return jsonify({'success': False, 'error': auth_message}), 401
                
                data = request.get_json()
                session_id = data.get('session_id')
                additional_duration = data.get('duration', 3600)  # Default 1 hour
                
                if not session_id:
                    return jsonify({'success': False, 'error': 'Session ID required'}), 400
                
                if session_id not in self.active_sessions:
                    return jsonify({'success': False, 'error': 'Session not found'}), 404
                
                # Extend camera session
                success, message = self.camera_manager.extend_session(session_id, additional_duration)
                
                if success:
                    # Update session duration
                    with self.session_lock:
                        if session_id in self.active_sessions:
                            current_duration = self.active_sessions[session_id].get('duration', self.session_timeout)
                            self.active_sessions[session_id]['duration'] = current_duration + additional_duration
                            self._save_sessions()
                
                return jsonify({
                    'success': success,
                    'message': message
                })
                
            except Exception as e:
                self.logger.error(f"Extend session error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            try:
                return jsonify({
                    'status': 'healthy',
                    'timestamp': now().isoformat(),
                    'active_sessions': len(self.active_sessions),
                    'camera_manager_status': self.camera_manager.get_status()
                })
                
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
    
    def start(self):
        """Start the remote access controller."""
        try:
            self.logger.info(f"Starting Remote Access Controller on {self.host}:{self.port}")
            
            # Run Flask app
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                threaded=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start Remote Access Controller: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        try:
            return {
                'controller_running': True,
                'port': self.port,
                'host': self.host,
                'authentication_required': self.authentication_required,
                'session_timeout': self.session_timeout,
                'active_sessions': len(self.active_sessions),
                'sessions': self.active_sessions,
                'camera_manager_status': self.camera_manager.get_status()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get status: {e}")
            return {'error': str(e)}

# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Remote Access Controller')
    parser.add_argument('--port', type=int, default=5001, help='Port to run on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--no-auth', action='store_true', help='Disable authentication')
    args = parser.parse_args()
    
    # Load configuration
    config_path = project_root / "config" / "development_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Override config with command line arguments
    config['remote_access']['controller_port'] = args.port
    config['remote_access']['host'] = args.host
    config['remote_access']['authentication_required'] = not args.no_auth
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start remote access controller
    controller = RemoteAccessController(config)
    controller.start()
