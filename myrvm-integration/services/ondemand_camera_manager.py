#!/usr/bin/env python3
"""
On-Demand Camera Manager for MyRVM Platform Integration
Manages camera activation only when needed for remote access
"""

import os
import sys
import json
import time
import logging
import threading
import subprocess
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import psutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "api-client"))

from myrvm_api_client import MyRVMAPIClient
from utils.timezone_manager import get_timezone_manager, now, format_datetime

class OnDemandCameraManager:
    """
    On-demand camera manager for remote access.
    Activates camera only when needed and manages sessions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.rvm_id = config.get('rvm_id', 1)
        self.session_timeout = config.get('remote_access', {}).get('session_timeout', 3600)  # 1 hour
        self.camera_script = config.get('remote_access', {}).get('camera_script', 
            '/home/my/test-cv-yolo11-sam2-camera/cv-camera/camera_sam2_integration.py')
        self.camera_port = config.get('remote_access', {}).get('camera_port', 5000)
        self.auto_status_change = config.get('remote_access', {}).get('auto_status_change', True)
        self.maintenance_status = config.get('remote_access', {}).get('maintenance_status', 'maintenance')
        self.restore_status = config.get('remote_access', {}).get('restore_status', 'active')
        
        # Initialize components
        self.api_client = MyRVMAPIClient(
            base_url=config.get('myrvm_base_url'),
            use_tunnel=config.get('use_tunnel', False)
        )
        
        # Session management
        self.active_sessions = {}
        self.camera_process = None
        self.session_lock = threading.Lock()
        self.original_status = None
        
        # Setup logging
        self._setup_logger()
        
        # Load session data
        self.session_file = project_root / "data" / "camera_sessions.json"
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_sessions()
        
    def _setup_logger(self):
        """Setup logger for on-demand camera manager."""
        log_dir = project_root / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'ondemand_camera_{now().strftime("%Y%m%d")}.log'
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
                    self.original_status = data.get('original_status')
                    self.logger.info(f"Loaded {len(self.active_sessions)} active sessions")
        except Exception as e:
            self.logger.warning(f"Could not load sessions: {e}")
            
    def _save_sessions(self):
        """Save active sessions to file."""
        try:
            data = {
                'sessions': self.active_sessions,
                'original_status': self.original_status,
                'last_updated': now().isoformat()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Could not save sessions: {e}")
    
    def start_camera_session(self, session_id: str, user_id: str = None, 
                           duration: int = None) -> Tuple[bool, str]:
        """
        Start a new camera session.
        
        Args:
            session_id: Unique session identifier
            user_id: User requesting access
            duration: Session duration in seconds (default: session_timeout)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with self.session_lock:
                # Check if camera is already running
                if self.camera_process and self.camera_process.poll() is None:
                    self.logger.info(f"Camera already running, adding session {session_id}")
                    self.active_sessions[session_id] = {
                        'user_id': user_id,
                        'start_time': now().isoformat(),
                        'duration': duration or self.session_timeout,
                        'status': 'active'
                    }
                    self._save_sessions()
                    return True, "Camera session added to existing session"
                
                # Start camera process
                self.logger.info(f"Starting camera session {session_id}")
                
                # Change RVM status to maintenance if enabled
                if self.auto_status_change:
                    self._change_rvm_status(self.maintenance_status)
                
                # Start camera script
                env = os.environ.copy()
                env['PYTHONPATH'] = str(project_root)
                env['DISPLAY'] = ':0'
                
                self.camera_process = subprocess.Popen(
                    [sys.executable, self.camera_script],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid
                )
                
                # Wait for camera to start
                time.sleep(3)
                
                # Check if camera started successfully
                if self.camera_process.poll() is None:
                    # Add session
                    self.active_sessions[session_id] = {
                        'user_id': user_id,
                        'start_time': now().isoformat(),
                        'duration': duration or self.session_timeout,
                        'status': 'active'
                    }
                    self._save_sessions()
                    
                    # Start session timeout thread
                    self._start_session_timeout(session_id)
                    
                    self.logger.info(f"Camera session {session_id} started successfully")
                    return True, f"Camera session started on port {self.camera_port}"
                else:
                    # Camera failed to start
                    stdout, stderr = self.camera_process.communicate()
                    error_msg = f"Camera failed to start: {stderr.decode()}"
                    self.logger.error(error_msg)
                    
                    # Restore RVM status
                    if self.auto_status_change:
                        self._change_rvm_status(self.restore_status)
                    
                    return False, error_msg
                    
        except Exception as e:
            self.logger.error(f"Failed to start camera session: {e}")
            return False, f"Failed to start camera session: {e}"
    
    def stop_camera_session(self, session_id: str) -> Tuple[bool, str]:
        """
        Stop a specific camera session.
        
        Args:
            session_id: Session identifier to stop
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with self.session_lock:
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                    self._save_sessions()
                    self.logger.info(f"Session {session_id} removed")
                
                # Check if there are any active sessions left
                if not self.active_sessions:
                    return self._stop_camera_process()
                else:
                    return True, f"Session {session_id} stopped, {len(self.active_sessions)} sessions remaining"
                    
        except Exception as e:
            self.logger.error(f"Failed to stop camera session: {e}")
            return False, f"Failed to stop camera session: {e}"
    
    def _stop_camera_process(self) -> Tuple[bool, str]:
        """Stop the camera process."""
        try:
            if self.camera_process and self.camera_process.poll() is None:
                self.logger.info("Stopping camera process")
                
                # Terminate the process group
                os.killpg(os.getpgid(self.camera_process.pid), signal.SIGTERM)
                
                # Wait for graceful shutdown
                try:
                    self.camera_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    os.killpg(os.getpgid(self.camera_process.pid), signal.SIGKILL)
                    self.camera_process.wait()
                
                self.camera_process = None
                
                # Restore RVM status
                if self.auto_status_change:
                    self._change_rvm_status(self.restore_status)
                
                self.logger.info("Camera process stopped successfully")
                return True, "Camera process stopped"
            else:
                return True, "Camera process was not running"
                
        except Exception as e:
            self.logger.error(f"Failed to stop camera process: {e}")
            return False, f"Failed to stop camera process: {e}"
    
    def _start_session_timeout(self, session_id: str):
        """Start timeout thread for a session."""
        def timeout_worker():
            try:
                session = self.active_sessions.get(session_id)
                if not session:
                    return
                
                duration = session.get('duration', self.session_timeout)
                time.sleep(duration)
                
                # Check if session still exists
                if session_id in self.active_sessions:
                    self.logger.info(f"Session {session_id} timed out after {duration} seconds")
                    self.stop_camera_session(session_id)
                    
            except Exception as e:
                self.logger.error(f"Session timeout error for {session_id}: {e}")
        
        thread = threading.Thread(target=timeout_worker, daemon=True)
        thread.start()
    
    def _change_rvm_status(self, status: str):
        """Change RVM status via API."""
        try:
            if self.original_status is None and status == self.maintenance_status:
                # Store original status before changing to maintenance
                current_status = self.api_client.get_rvm_status(self.rvm_id)
                if current_status:
                    self.original_status = current_status.get('status', 'active')
                    self.logger.info(f"Stored original status: {self.original_status}")
            
            # Change status
            result = self.api_client.update_rvm_status(self.rvm_id, status)
            if result:
                self.logger.info(f"RVM status changed to: {status}")
            else:
                self.logger.warning(f"Failed to change RVM status to: {status}")
                
        except Exception as e:
            self.logger.error(f"Failed to change RVM status: {e}")
    
    def get_session_status(self, session_id: str = None) -> Dict[str, Any]:
        """
        Get session status.
        
        Args:
            session_id: Specific session ID, or None for all sessions
            
        Returns:
            Session status information
        """
        try:
            if session_id:
                if session_id in self.active_sessions:
                    session = self.active_sessions[session_id]
                    return {
                        'session_id': session_id,
                        'status': 'active',
                        'user_id': session.get('user_id'),
                        'start_time': session.get('start_time'),
                        'duration': session.get('duration'),
                        'camera_running': self.camera_process and self.camera_process.poll() is None,
                        'camera_port': self.camera_port
                    }
                else:
                    return {'session_id': session_id, 'status': 'not_found'}
            else:
                return {
                    'total_sessions': len(self.active_sessions),
                    'active_sessions': list(self.active_sessions.keys()),
                    'camera_running': self.camera_process and self.camera_process.poll() is None,
                    'camera_port': self.camera_port,
                    'sessions': self.active_sessions
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get session status: {e}")
            return {'error': str(e)}
    
    def extend_session(self, session_id: str, additional_duration: int) -> Tuple[bool, str]:
        """
        Extend session duration.
        
        Args:
            session_id: Session identifier
            additional_duration: Additional duration in seconds
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with self.session_lock:
                if session_id in self.active_sessions:
                    current_duration = self.active_sessions[session_id].get('duration', self.session_timeout)
                    new_duration = current_duration + additional_duration
                    self.active_sessions[session_id]['duration'] = new_duration
                    self._save_sessions()
                    
                    self.logger.info(f"Session {session_id} extended by {additional_duration} seconds")
                    return True, f"Session extended to {new_duration} seconds"
                else:
                    return False, f"Session {session_id} not found"
                    
        except Exception as e:
            self.logger.error(f"Failed to extend session: {e}")
            return False, f"Failed to extend session: {e}"
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            current_time = now()
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                start_time = datetime.fromisoformat(session['start_time'])
                duration = session.get('duration', self.session_timeout)
                
                if (current_time - start_time).total_seconds() > duration:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self.logger.info(f"Cleaning up expired session: {session_id}")
                self.stop_camera_session(session_id)
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
    
    def get_camera_url(self) -> str:
        """Get camera access URL."""
        try:
            # Get local IP address
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            return f"http://{local_ip}:{self.camera_port}"
            
        except Exception as e:
            self.logger.error(f"Failed to get camera URL: {e}")
            return f"http://localhost:{self.camera_port}"
    
    def is_camera_available(self) -> bool:
        """Check if camera is available for new sessions."""
        try:
            # Check if camera process is running
            if self.camera_process and self.camera_process.poll() is None:
                return True
            
            # Check if camera script exists
            if not Path(self.camera_script).exists():
                return False
            
            # Check if port is available
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', self.camera_port))
            sock.close()
            
            return result != 0  # Port is available if connection fails
            
        except Exception as e:
            self.logger.error(f"Failed to check camera availability: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        try:
            return {
                'camera_running': self.camera_process and self.camera_process.poll() is None,
                'camera_port': self.camera_port,
                'active_sessions': len(self.active_sessions),
                'session_timeout': self.session_timeout,
                'auto_status_change': self.auto_status_change,
                'current_status': self.maintenance_status if self.active_sessions else self.restore_status,
                'original_status': self.original_status,
                'camera_available': self.is_camera_available(),
                'camera_url': self.get_camera_url(),
                'sessions': self.active_sessions
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get status: {e}")
            return {'error': str(e)}

# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='On-Demand Camera Manager')
    parser.add_argument('--start-session', help='Start camera session with given ID')
    parser.add_argument('--stop-session', help='Stop camera session with given ID')
    parser.add_argument('--status', action='store_true', help='Show camera manager status')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup expired sessions')
    args = parser.parse_args()
    
    # Load configuration
    config_path = project_root / "config" / "development_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create camera manager
    camera_manager = OnDemandCameraManager(config)
    
    if args.start_session:
        success, message = camera_manager.start_camera_session(args.start_session)
        print(f"Start session result: {success} - {message}")
    
    elif args.stop_session:
        success, message = camera_manager.stop_camera_session(args.stop_session)
        print(f"Stop session result: {success} - {message}")
    
    elif args.status:
        status = camera_manager.get_status()
        print("Camera Manager Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    elif args.cleanup:
        camera_manager.cleanup_expired_sessions()
        print("Expired sessions cleaned up")
    
    else:
        parser.print_help()
