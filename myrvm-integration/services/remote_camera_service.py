#!/usr/bin/env python3
"""
Remote Camera Service for MyRVM Platform Integration
Provides web-based camera streaming and control for remote access
"""

import cv2
import time
import json
import logging
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from flask import Flask, render_template, Response, jsonify, request
import base64
import io
from PIL import Image

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "api-client"))

from myrvm_api_client import MyRVMAPIClient

class RemoteCameraService:
    """Remote camera service with web interface for MyRVM Platform"""
    
    def __init__(self, config: Dict):
        """
        Initialize remote camera service
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.camera_index = config.get('camera_index', 0)
        self.port = config.get('remote_camera', {}).get('port', 5000)
        self.host = config.get('remote_camera', {}).get('host', '0.0.0.0')
        self.rvm_id = config.get('rvm_id', 1)
        
        # Initialize components
        self.camera = None
        self.is_streaming = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.api_client = MyRVMAPIClient(
            base_url=config.get('myrvm_base_url'),
            use_tunnel=config.get('use_tunnel', False)
        )
        
        # Setup Flask app
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Statistics
        self.stats = {
            'start_time': None,
            'frame_count': 0,
            'last_frame_time': None,
            'fps': 0
        }
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for remote camera service"""
        logger = logging.getLogger('RemoteCameraService')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'remote_camera_{datetime.now().strftime("%Y%m%d")}.log'
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
            """Main camera interface"""
            return render_template('remote_camera.html', rvm_id=self.rvm_id)
        
        @self.app.route('/video_feed')
        def video_feed():
            """Video streaming route"""
            return Response(self.generate_frames(),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/camera_info')
        def camera_info():
            """Get camera information"""
            if self.camera is None:
                return jsonify({'error': 'Camera not initialized'})
            
            elapsed_time = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
            current_fps = self.stats['frame_count'] / elapsed_time if elapsed_time > 0 else 0
            
            width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            camera_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            return jsonify({
                'rvm_id': self.rvm_id,
                'resolution': f"{width}x{height}",
                'fps': camera_fps,
                'current_fps': round(current_fps, 2),
                'frame_count': self.stats['frame_count'],
                'uptime': round(elapsed_time, 2),
                'status': 'streaming' if self.is_streaming else 'stopped'
            })
        
        @self.app.route('/capture')
        def capture():
            """Capture current frame"""
            if self.camera is None:
                return jsonify({'error': 'Camera not initialized'})
            
            ret, frame = self.camera.read()
            
            if not ret:
                return jsonify({'error': 'Cannot capture frame'})
            
            # Save image
            output_dir = Path(__file__).parent.parent / 'storages' / 'images' / 'remote_captures'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"remote_capture_{timestamp}.jpg"
            filepath = output_dir / filename
            
            cv2.imwrite(str(filepath), frame)
            
            # Upload to MyRVM Platform if configured
            if self.api_client:
                try:
                    success, response = self.api_client.upload_image_file(
                        str(filepath), 
                        {'rvm_id': self.rvm_id, 'type': 'remote_capture'}
                    )
                    if success:
                        self.logger.info(f"Image uploaded to MyRVM Platform: {filename}")
                except Exception as e:
                    self.logger.warning(f"Failed to upload image: {e}")
            
            return jsonify({
                'success': True,
                'filename': filename,
                'path': str(filepath),
                'rvm_id': self.rvm_id
            })
        
        @self.app.route('/control', methods=['POST'])
        def control():
            """Camera control endpoint"""
            data = request.get_json()
            action = data.get('action')
            
            if action == 'start':
                if not self.is_streaming:
                    self.start_camera()
                    return jsonify({'success': True, 'message': 'Camera started'})
                else:
                    return jsonify({'success': False, 'message': 'Camera already running'})
            
            elif action == 'stop':
                if self.is_streaming:
                    self.stop_camera()
                    return jsonify({'success': True, 'message': 'Camera stopped'})
                else:
                    return jsonify({'success': False, 'message': 'Camera not running'})
            
            elif action == 'restart':
                self.restart_camera()
                return jsonify({'success': True, 'message': 'Camera restarted'})
            
            else:
                return jsonify({'success': False, 'message': 'Invalid action'})
        
        @self.app.route('/status')
        def status():
            """Get service status"""
            return jsonify({
                'service': 'Remote Camera Service',
                'rvm_id': self.rvm_id,
                'status': 'running' if self.is_streaming else 'stopped',
                'camera_initialized': self.camera is not None,
                'port': self.port,
                'host': self.host,
                'uptime': time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
            })
    
    def init_camera(self) -> bool:
        """Initialize camera"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                self.logger.error(f"Cannot open camera {self.camera_index}")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 25)
            
            # Get actual properties
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            self.logger.info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps} FPS")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def generate_frames(self):
        """Generate frames for streaming"""
        while self.is_streaming:
            if self.camera is None:
                break
                
            ret, frame = self.camera.read()
            
            if not ret:
                self.logger.error("Cannot read frame from camera")
                break
            
            self.stats['frame_count'] += 1
            self.stats['last_frame_time'] = time.time()
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Control frame rate
            time.sleep(1.0 / 25)  # 25 FPS
    
    def start_camera(self):
        """Start camera streaming"""
        if not self.init_camera():
            return False
        
        self.is_streaming = True
        self.stats['start_time'] = time.time()
        self.logger.info("Camera streaming started")
        return True
    
    def stop_camera(self):
        """Stop camera streaming"""
        self.is_streaming = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.logger.info("Camera streaming stopped")
    
    def restart_camera(self):
        """Restart camera"""
        self.stop_camera()
        time.sleep(1)
        self.start_camera()
    
    def start(self):
        """Start remote camera service"""
        try:
            self.logger.info(f"Starting Remote Camera Service on {self.host}:{self.port}")
            
            # Start camera
            if not self.start_camera():
                self.logger.error("Failed to start camera")
                return False
            
            # Start Flask app
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
            
        except Exception as e:
            self.logger.error(f"Error starting remote camera service: {e}")
            return False
    
    def stop(self):
        """Stop remote camera service"""
        self.stop_camera()
        self.logger.info("Remote Camera Service stopped")

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
    service = RemoteCameraService(config)
    
    try:
        service.start()
    except KeyboardInterrupt:
        print("\n⏹️  Service stopped by user")
    finally:
        service.stop()
