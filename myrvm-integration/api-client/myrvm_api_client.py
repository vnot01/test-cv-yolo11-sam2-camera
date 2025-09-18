#!/usr/bin/env python3
"""
MyRVM Platform API Client
Handles communication between Jetson Orin and MyRVM Platform
"""

import requests
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class MyRVMAPIClient:
    """API Client for MyRVM Platform communication"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_token: str = None, 
                 tunnel_url: str = None, use_tunnel: bool = False):
        """
        Initialize API client
        
        Args:
            base_url: MyRVM Platform base URL (local)
            api_token: API authentication token
            tunnel_url: Tunnel URL (for external access)
            use_tunnel: Whether to use tunnel URL
        """
        self.base_url = base_url.rstrip('/')
        self.tunnel_url = tunnel_url.rstrip('/') if tunnel_url else None
        self.use_tunnel = use_tunnel
        self.api_token = api_token
        self.session = requests.Session()
        
        # Determine which URL to use
        self.current_url = self.tunnel_url if self.use_tunnel and self.tunnel_url else self.base_url
        
        # Set headers
        if self.api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
        else:
            self.session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
        
        # Setup logging
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for API client"""
        logger = logging.getLogger('MyRVMAPIClient')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'api_client_{datetime.now().strftime("%Y%m%d")}.log'
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
        try:
            response = self.session.get(f"{self.current_url}/api/health", timeout=10)
            if response.status_code == 200:
                return True, "Connected"
            else:
                return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, 
                     params: Dict = None, files: Dict = None) -> Tuple[bool, Dict]:
        """
        Make HTTP request to MyRVM Platform
        
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
            
            self.logger.info(f"Response status: {response.status_code}")
            
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
            error_msg = f"Request failed: {str(e)}"
            self.logger.error(error_msg)
            return False, {'error': error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return False, {'error': error_msg}
    
    def login(self, email: str, password: str) -> Tuple[bool, Dict]:
        """Login to MyRVM Platform and get authentication token"""
        login_data = {
            'email': email,
            'password': password
        }
        
        success, response = self._make_request('POST', '/api/v2/auth/login', data=login_data)
        
        if success and 'data' in response and 'token' in response['data']:
            # Store token for future requests
            self.api_token = response['data']['token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_token}'
            })
            self.logger.info("Successfully logged in and obtained token")
        
        return success, response
    
    def ping_platform(self) -> Tuple[bool, Dict]:
        """Ping MyRVM Platform to check connectivity"""
        return self._make_request('GET', '/api/health')
    
    def register_processing_engine(self, engine_data: Dict) -> Tuple[bool, Dict]:
        """
        Register Jetson Orin as processing engine
        
        Args:
            engine_data: Engine information
                {
                    'name': 'Jetson Orin Edge',
                    'type': 'jetson_edge',
                    'status': 'active',
                    'capabilities': ['object_detection', 'segmentation'],
                    'location': 'Edge Device',
                    'ip_address': '192.168.1.11',
                    'port': 5000
                }
        """
        return self._make_request('POST', '/admin/processing-engines', data=engine_data)
    
    def update_engine_status(self, engine_id: int, status: str) -> Tuple[bool, Dict]:
        """Update processing engine status"""
        return self._make_request('PUT', f'/admin/processing-engines/{engine_id}', 
                                data={'status': status})
    
    def ping_engine(self, engine_id: int) -> Tuple[bool, Dict]:
        """Ping processing engine"""
        return self._make_request('POST', f'/admin/processing-engines/{engine_id}/ping')
    
    def assign_engine_to_rvm(self, engine_id: int, rvm_id: int) -> Tuple[bool, Dict]:
        """Assign processing engine to RVM"""
        return self._make_request('POST', f'/admin/processing-engines/{engine_id}/assign', 
                                data={'rvm_id': rvm_id})
    
    def create_rvm_session(self, rvm_id: int, session_data: Dict) -> Tuple[bool, Dict]:
        """
        Create new RVM session
        
        Args:
            rvm_id: RVM ID
            session_data: Session information
                {
                    'user_id': 1,  # Optional
                    'session_type': 'guest'  # or 'user'
                }
        """
        return self._make_request('POST', f'/api/v2/rvm-sessions', data=session_data)
    
    def create_deposit(self, deposit_data: Dict) -> Tuple[bool, Dict]:
        """
        Create new deposit record
        
        Args:
            deposit_data: Deposit information
                {
                    'rvm_id': 1,
                    'session_id': 1,
                    'waste_type': 'plastic',
                    'weight': 0.5,
                    'quantity': 1,
                    'image_path': '/path/to/image.jpg'
                }
        """
        return self._make_request('POST', '/api/v2/deposits/create', data=deposit_data)
    
    def process_deposit(self, deposit_id: int, analysis_data: Dict) -> Tuple[bool, Dict]:
        """
        Process deposit with AI analysis results
        
        Args:
            deposit_id: Deposit ID
            analysis_data: AI analysis results
                {
                    'cv_confidence': 0.95,
                    'cv_analysis': 'plastic bottle detected',
                    'cv_waste_type': 'plastic',
                    'ai_confidence': 0.90,
                    'ai_analysis': 'High quality plastic bottle',
                    'status': 'processed'
                }
        """
        return self._make_request('POST', f'/api/v2/deposits/{deposit_id}/process', 
                                data=analysis_data)
    
    def upload_detection_results(self, results_data: Dict) -> Tuple[bool, Dict]:
        """
        Upload detection results to Edge Vision
        
        Args:
            results_data: Detection results
                {
                    'rvm_id': 1,
                    'image_path': '/path/to/image.jpg',
                    'detections': [
                        {
                            'class': 'plastic_bottle',
                            'confidence': 0.95,
                            'bbox': [100, 100, 200, 200],
                            'segmentation_mask': 'base64_encoded_mask'
                        }
                    ],
                    'timestamp': '2024-09-18T10:30:00Z'
                }
        """
        return self._make_request('POST', '/admin/edge-vision/upload-results', 
                                data=results_data)
    
    def trigger_processing(self, rvm_id: int) -> Tuple[bool, Dict]:
        """Trigger processing for specific RVM"""
        return self._make_request('POST', '/admin/edge-vision/trigger-processing', 
                                data={'rvm_id': rvm_id})
    
    def get_rvm_status(self, rvm_id: int) -> Tuple[bool, Dict]:
        """Get RVM status"""
        return self._make_request('GET', f'/admin/edge-vision/rvm-status/{rvm_id}')
    
    def upload_image_file(self, image_path: str, metadata: Dict = None) -> Tuple[bool, Dict]:
        """
        Upload image file to MyRVM Platform
        
        Args:
            image_path: Path to image file
            metadata: Additional metadata
        """
        if not Path(image_path).exists():
            return False, {'error': f'Image file not found: {image_path}'}
        
        files = {'image': open(image_path, 'rb')}
        data = metadata or {}
        
        try:
            success, response = self._make_request('POST', '/admin/edge-vision/upload-image', 
                                                 data=data, files=files)
            return success, response
        finally:
            files['image'].close()
    
    def get_processing_history(self, rvm_id: int = None, limit: int = 10) -> Tuple[bool, Dict]:
        """Get processing history"""
        params = {'limit': limit}
        if rvm_id:
            params['rvm_id'] = rvm_id
        
        return self._make_request('GET', '/admin/edge-vision/processing-history', 
                                params=params)

# Example usage and testing
if __name__ == "__main__":
    # Initialize API client
    client = MyRVMAPIClient(
        base_url="http://localhost:8000",
        api_token=None  # Add token if needed
    )
    
    # Test connectivity
    print("Testing MyRVM Platform connectivity...")
    success, response = client.ping_platform()
    
    if success:
        print("✅ Connected to MyRVM Platform")
        print(f"Response: {response}")
    else:
        print("❌ Failed to connect to MyRVM Platform")
        print(f"Error: {response}")
    
    # Test engine registration
    print("\nTesting engine registration...")
    engine_data = {
        'name': 'Jetson Orin Edge',
        'type': 'jetson_edge',
        'status': 'active',
        'capabilities': ['object_detection', 'segmentation'],
        'location': 'Edge Device',
        'ip_address': '192.168.1.11',
        'port': 5000
    }
    
    success, response = client.register_processing_engine(engine_data)
    if success:
        print("✅ Engine registered successfully")
        print(f"Response: {response}")
    else:
        print("❌ Failed to register engine")
        print(f"Error: {response}")
