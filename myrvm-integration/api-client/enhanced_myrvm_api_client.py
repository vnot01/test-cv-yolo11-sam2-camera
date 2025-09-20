#!/usr/bin/env python3
"""
Enhanced MyRVM Platform API Client
Handles communication between Jetson Orin and MyRVM Platform with advanced features
"""

import requests
import json
import time
import logging
import threading
import websocket
import queue
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, asdict
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.timezone_manager import get_timezone_manager, now, format_datetime

@dataclass
class RetryConfig:
    """Retry configuration for API calls"""
    max_attempts: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0
    max_delay: float = 60.0
    retry_on_status: List[int] = None
    
    def __post_init__(self):
        if self.retry_on_status is None:
            self.retry_on_status = [500, 502, 503, 504, 429]

@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration"""
    max_connections: int = 10
    max_keepalive: int = 5
    pool_block: bool = False
    pool_connections: int = 10

@dataclass
class WebSocketConfig:
    """WebSocket configuration"""
    url: str = None
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    ping_interval: int = 30
    ping_timeout: int = 10

class EnhancedMyRVMAPIClient:
    """Enhanced API client with real-time communication and advanced features"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_token: str = None, 
                 tunnel_url: str = None, use_tunnel: bool = False, rvm_id: str = None):
        """
        Initialize Enhanced API client
        
        Args:
            base_url: MyRVM Platform base URL (local)
            api_token: API authentication token
            tunnel_url: Tunnel URL (for external access)
            use_tunnel: Whether to use tunnel URL
            rvm_id: RVM identifier
        """
        self.base_url = base_url.rstrip('/')
        self.tunnel_url = tunnel_url.rstrip('/') if tunnel_url else None
        self.use_tunnel = use_tunnel
        self.api_token = api_token
        self.rvm_id = rvm_id
        
        # Configuration
        self.retry_config = RetryConfig()
        self.pool_config = ConnectionPoolConfig()
        self.websocket_config = WebSocketConfig()
        
        # Session and connection management
        self.session = self._create_session()
        self.current_url = self.tunnel_url if self.use_tunnel and self.tunnel_url else self.base_url
        
        # WebSocket management
        self.websocket = None
        self.websocket_thread = None
        self.websocket_connected = False
        self.message_queue = queue.Queue()
        self.websocket_callbacks = []
        
        # Request/response logging
        self.request_logger = self._setup_request_logger()
        self.request_count = 0
        self.response_times = []
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize WebSocket if configured
        if self.websocket_config.url:
            self._initialize_websocket()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry and connection pooling"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.retry_config.max_attempts,
            backoff_factor=self.retry_config.backoff_factor,
            status_forcelist=self.retry_config.retry_on_status,
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.pool_config.pool_connections,
            pool_maxsize=self.pool_config.max_connections,
            pool_block=self.pool_config.pool_block
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        if self.api_token:
            session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'MyRVM-Edge-Client/2.0'
            })
        else:
            session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'MyRVM-Edge-Client/2.0'
            })
        
        return session
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for API client"""
        logger = logging.getLogger('EnhancedMyRVMAPIClient')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'enhanced_api_client_{format_datetime(now(), "%Y%m%d")}.log'
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
    
    def _setup_request_logger(self) -> logging.Logger:
        """Setup request/response logger"""
        logger = logging.getLogger('APIRequestLogger')
        logger.setLevel(logging.DEBUG)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'api_requests_{format_datetime(now(), "%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        return logger
    
    def _log_request(self, method: str, url: str, data: Dict = None, 
                    response_time: float = None, status_code: int = None):
        """Log API request and response"""
        self.request_count += 1
        
        log_data = {
            'request_id': self.request_count,
            'method': method,
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'data_size': len(json.dumps(data)) if data else 0,
            'response_time': response_time,
            'status_code': status_code
        }
        
        if response_time:
            self.response_times.append(response_time)
            # Keep only last 100 response times
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-100:]
        
        self.request_logger.debug(f"API Request: {json.dumps(log_data)}")
    
    def _initialize_websocket(self):
        """Initialize WebSocket connection"""
        if not self.websocket_config.url:
            return
        
        self.websocket_config.url = self.websocket_config.url.replace('http', 'ws')
        if self.rvm_id:
            self.websocket_config.url += f"?rvm_id={self.rvm_id}"
        
        self._connect_websocket()
    
    def _connect_websocket(self):
        """Connect to WebSocket"""
        try:
            self.websocket = websocket.WebSocketApp(
                self.websocket_config.url,
                on_open=self._on_websocket_open,
                on_message=self._on_websocket_message,
                on_error=self._on_websocket_error,
                on_close=self._on_websocket_close
            )
            
            self.websocket_thread = threading.Thread(
                target=self.websocket.run_forever,
                daemon=True,
                name="WebSocketThread"
            )
            self.websocket_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebSocket: {e}")
    
    def _on_websocket_open(self, ws):
        """WebSocket connection opened"""
        self.websocket_connected = True
        self.logger.info("WebSocket connection established")
        
        # Send authentication if token available
        if self.api_token:
            auth_message = {
                'type': 'auth',
                'token': self.api_token,
                'rvm_id': self.rvm_id
            }
            ws.send(json.dumps(auth_message))
    
    def _on_websocket_message(self, ws, message):
        """WebSocket message received"""
        try:
            data = json.loads(message)
            self.message_queue.put(data)
            
            # Notify callbacks
            for callback in self.websocket_callbacks:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"WebSocket callback error: {e}")
                    
        except Exception as e:
            self.logger.error(f"WebSocket message error: {e}")
    
    def _on_websocket_error(self, ws, error):
        """WebSocket error occurred"""
        self.logger.error(f"WebSocket error: {error}")
        self.websocket_connected = False
    
    def _on_websocket_close(self, ws, close_status_code, close_msg):
        """WebSocket connection closed"""
        self.websocket_connected = False
        self.logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        
        # Attempt to reconnect
        if self.websocket_config.max_reconnect_attempts > 0:
            self._schedule_reconnect()
    
    def _schedule_reconnect(self):
        """Schedule WebSocket reconnection"""
        def reconnect():
            time.sleep(self.websocket_config.reconnect_interval)
            self._connect_websocket()
        
        reconnect_thread = threading.Thread(target=reconnect, daemon=True)
        reconnect_thread.start()
    
    def register_websocket_callback(self, callback: Callable[[Dict], None]):
        """Register WebSocket message callback"""
        self.websocket_callbacks.append(callback)
        self.logger.info("WebSocket callback registered")
    
    def send_websocket_message(self, message: Dict):
        """Send message via WebSocket"""
        if self.websocket_connected and self.websocket:
            try:
                self.websocket.send(json.dumps(message))
                return True
            except Exception as e:
                self.logger.error(f"Failed to send WebSocket message: {e}")
                return False
        return False
    
    def get_websocket_messages(self, timeout: float = 1.0) -> List[Dict]:
        """Get WebSocket messages from queue"""
        messages = []
        try:
            while True:
                message = self.message_queue.get(timeout=timeout)
                messages.append(message)
        except queue.Empty:
            pass
        return messages
    
    def switch_to_tunnel(self):
        """Switch to tunnel URL"""
        if self.tunnel_url:
            self.current_url = self.tunnel_url
            self.use_tunnel = True
            self.logger.info(f"Switched to tunnel URL: {self.current_url}")
        else:
            self.logger.warning("No tunnel URL configured")
    
    def switch_to_local(self):
        """Switch to local URL"""
        self.current_url = self.base_url
        self.use_tunnel = False
        self.logger.info(f"Switched to local URL: {self.current_url}")
    
    def test_connectivity(self) -> Tuple[bool, str]:
        """Test connectivity to current URL"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.current_url}/api/health", timeout=10)
            response_time = time.time() - start_time
            
            self._log_request('GET', f"{self.current_url}/api/health", 
                            response_time=response_time, status_code=response.status_code)
            
            if response.status_code in [200, 404]:  # 404 is OK for unimplemented endpoint
                return True, "Connected"
            else:
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            response_time = time.time() - start_time
            self._log_request('GET', f"{self.current_url}/api/health", 
                            response_time=response_time, status_code=None)
            return False, str(e)
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, 
                     params: Dict = None, files: Dict = None) -> Tuple[bool, Dict]:
        """
        Make HTTP request to MyRVM Platform with enhanced features
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            files: Files to upload
            
        Returns:
            Tuple of (success, response_data)
        """
        url = f"{self.current_url}{endpoint}"
        start_time = time.time()
        
        try:
            self.logger.info(f"Making {method} request to {url}")
            
            if files:
                # Remove Content-Type header for file uploads
                headers = {k: v for k, v in self.session.headers.items() 
                          if k.lower() != 'content-type'}
                response = self.session.request(
                    method, url, data=data, params=params, 
                    files=files, headers=headers, timeout=30
                )
            else:
                response = self.session.request(
                    method, url, json=data, params=params, timeout=30
                )
            
            response_time = time.time() - start_time
            self._log_request(method, url, data, response_time, response.status_code)
            
            self.logger.info(f"Response status: {response.status_code} (took {response_time:.2f}s)")
            
            if response.status_code in [200, 201, 202]:
                try:
                    response_data = response.json()
                    self.logger.info(f"Response data: {response_data}")
                    return True, response_data
                except json.JSONDecodeError:
                    self.logger.warning("Response is not JSON, returning text")
                    return True, {'message': response.text}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                return False, {'error': error_msg}
                
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            self._log_request(method, url, data, response_time, None)
            error_msg = f"Request failed: {str(e)}"
            self.logger.error(error_msg)
            return False, {'error': error_msg}
        except Exception as e:
            response_time = time.time() - start_time
            self._log_request(method, url, data, response_time, None)
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return False, {'error': error_msg}
    
    # Configuration Management Endpoints
    def get_rvm_config(self, rvm_id: str = None) -> Tuple[bool, Dict]:
        """Get RVM configuration from server"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('GET', f'/api/v2/rvms/{rvm_id}/config')
    
    def update_rvm_config(self, rvm_id: str, config_data: Dict) -> Tuple[bool, Dict]:
        """Update RVM configuration on server"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('PATCH', f'/api/v2/rvms/{rvm_id}/config', data=config_data)
    
    def get_confidence_threshold(self, rvm_id: str = None) -> Tuple[bool, Dict]:
        """Get confidence threshold for RVM"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('GET', f'/api/v2/rvms/{rvm_id}/config/confidence-threshold')
    
    def update_confidence_threshold(self, rvm_id: str, threshold: float) -> Tuple[bool, Dict]:
        """Update confidence threshold for RVM"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('PATCH', f'/api/v2/rvms/{rvm_id}/config/confidence-threshold', 
                                data={'confidence_threshold': threshold})
    
    # Remote Access Endpoints
    def start_remote_access(self, rvm_id: str, access_data: Dict) -> Tuple[bool, Dict]:
        """Start remote access session"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('POST', f'/api/v2/rvms/{rvm_id}/remote-access/start', 
                                data=access_data)
    
    def stop_remote_access(self, rvm_id: str) -> Tuple[bool, Dict]:
        """Stop remote access session"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('POST', f'/api/v2/rvms/{rvm_id}/remote-access/stop')
    
    def get_remote_access_status(self, rvm_id: str = None) -> Tuple[bool, Dict]:
        """Get remote access session status"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('GET', f'/api/v2/rvms/{rvm_id}/remote-access/status')
    
    def get_remote_access_history(self, rvm_id: str = None, limit: int = 10) -> Tuple[bool, Dict]:
        """Get remote access session history"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        params = {'limit': limit}
        return self._make_request('GET', f'/api/v2/rvms/{rvm_id}/remote-access/history', 
                                params=params)
    
    # System Monitoring Endpoints
    def send_system_metrics(self, rvm_id: str, metrics_data: Dict) -> Tuple[bool, Dict]:
        """Send system metrics to server"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('POST', f'/api/v2/rvms/{rvm_id}/metrics', data=metrics_data)
    
    def get_system_metrics(self, rvm_id: str = None, days: int = 7) -> Tuple[bool, Dict]:
        """Get system metrics from server"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        params = {'days': days}
        return self._make_request('GET', f'/api/v2/rvms/{rvm_id}/metrics', params=params)
    
    # Backup Operations Endpoints
    def start_backup(self, rvm_id: str, backup_data: Dict) -> Tuple[bool, Dict]:
        """Start backup operation"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('POST', f'/api/v2/rvms/{rvm_id}/backup/start', data=backup_data)
    
    def get_backup_status(self, rvm_id: str = None) -> Tuple[bool, Dict]:
        """Get backup operation status"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        return self._make_request('GET', f'/api/v2/rvms/{rvm_id}/backup/status')
    
    def upload_backup(self, rvm_id: str, backup_file_path: str, metadata: Dict = None) -> Tuple[bool, Dict]:
        """Upload backup file to server"""
        rvm_id = rvm_id or self.rvm_id
        if not rvm_id:
            return False, {'error': 'RVM ID not provided'}
        
        if not Path(backup_file_path).exists():
            return False, {'error': f'Backup file not found: {backup_file_path}'}
        
        files = {'backup_file': open(backup_file_path, 'rb')}
        data = metadata or {}
        
        try:
            success, response = self._make_request('POST', f'/api/v2/rvms/{rvm_id}/backup/upload', 
                                                 data=data, files=files)
            return success, response
        finally:
            files['backup_file'].close()
    
    # Timezone Sync Endpoints
    def sync_timezone(self, timezone_data: Dict) -> Tuple[bool, Dict]:
        """Sync timezone with server"""
        return self._make_request('POST', '/api/v2/timezone/sync', data=timezone_data)
    
    def get_timezone_status(self, device_id: str = None) -> Tuple[bool, Dict]:
        """Get timezone sync status"""
        device_id = device_id or self.rvm_id
        if not device_id:
            return False, {'error': 'Device ID not provided'}
        
        return self._make_request('GET', f'/api/v2/timezone/status/{device_id}')
    
    def manual_timezone_sync(self, timezone_data: Dict) -> Tuple[bool, Dict]:
        """Manual timezone sync"""
        return self._make_request('POST', '/api/v2/timezone/sync/manual', data=timezone_data)
    
    # Legacy endpoints (from original API client)
    def login(self, email: str, password: str) -> Tuple[bool, Dict]:
        """Login to MyRVM Platform and get API token"""
        login_data = {
            'email': email,
            'password': password
        }
        
        success, response = self._make_request('POST', '/api/v2/auth/login', data=login_data)
        
        if success and 'data' in response and 'token' in response['data']:
            self.api_token = response['data']['token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_token}'
            })
            self.logger.info("Login successful, token updated")
        
        return success, response
    
    def ping_platform(self) -> Tuple[bool, Dict]:
        """Ping MyRVM Platform to check connectivity"""
        return self._make_request('GET', '/api/health')
    
    def register_processing_engine(self, engine_data: Dict) -> Tuple[bool, Dict]:
        """Register Jetson Orin as processing engine"""
        return self._make_request('POST', '/api/v2/processing-engines', data=engine_data)
    
    def upload_detection_results(self, results_data: Dict) -> Tuple[bool, Dict]:
        """Upload detection results to Edge Vision"""
        return self._make_request('POST', '/api/v2/detection-results', data=results_data)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get API client performance statistics"""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            'total_requests': self.request_count,
            'average_response_time': avg_response_time,
            'websocket_connected': self.websocket_connected,
            'current_url': self.current_url,
            'use_tunnel': self.use_tunnel,
            'pool_config': asdict(self.pool_config),
            'retry_config': asdict(self.retry_config)
        }
    
    def shutdown(self):
        """Shutdown API client"""
        self.logger.info("Shutting down Enhanced API client...")
        
        # Close WebSocket
        if self.websocket:
            self.websocket.close()
        
        # Close session
        self.session.close()
        
        self.logger.info("Enhanced API client shutdown completed")

# Example usage and testing
if __name__ == "__main__":
    # Initialize Enhanced API client
    client = EnhancedMyRVMAPIClient(
        base_url="http://localhost:8000",
        api_token=None,
        rvm_id="jetson_orin_nano_001"
    )
    
    # Test connectivity
    print("Testing Enhanced MyRVM Platform connectivity...")
    success, response = client.test_connectivity()
    
    if success:
        print("✅ Connected to MyRVM Platform")
        print(f"Response: {response}")
    else:
        print("❌ Failed to connect to MyRVM Platform")
        print(f"Error: {response}")
    
    # Test configuration endpoints
    print("\nTesting configuration endpoints...")
    success, response = client.get_rvm_config()
    if success:
        print("✅ RVM configuration retrieved")
        print(f"Response: {response}")
    else:
        print("❌ Failed to get RVM configuration")
        print(f"Error: {response}")
    
    # Test performance stats
    print("\nPerformance Statistics:")
    stats = client.get_performance_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Average response time: {stats['average_response_time']:.2f}s")
    print(f"WebSocket connected: {stats['websocket_connected']}")
    
    # Shutdown
    client.shutdown()
    print("\n✅ Enhanced API client test completed!")
