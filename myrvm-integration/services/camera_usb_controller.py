#!/usr/bin/env python3
"""
Camera USB Controller API for MyRVM Platform Integration
Provides comprehensive API endpoints for remote camera USB control on Jetson Orin
"""

import cv2
import time
import json
import logging
import threading
import queue
import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from flask import Flask, Response, jsonify, request, send_file
import base64
import io
from PIL import Image

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "api_client"))

from api_client.myrvm_api_client import MyRVMAPIClient

class CameraUSBController:
    """Camera USB Controller with comprehensive API endpoints for Jetson Orin"""
    
    def __init__(self, config: Dict):
        """
        Initialize camera USB controller
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.port = config.get('camera_usb', {}).get('port', 5004)
        self.host = config.get('camera_usb', {}).get('host', '0.0.0.0')
        self.rvm_id = config.get('rvm_id', 1)
        
        # Camera management
        self.cameras = {}  # {camera_id: camera_object}
        self.active_camera = None
        self.camera_index = 0
        self.is_streaming = False
        self.frame_queue = queue.Queue(maxsize=10)
        
        # API client for MyRVM Platform integration
        self.api_client = MyRVMAPIClient(
            base_url=config.get('server_url'),
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
            'fps': 0,
            'total_captures': 0,
            'total_streaming_time': 0
        }
        
        # Camera settings
        self.camera_settings = {
            'resolution': {'width': 640, 'height': 480},
            'fps': 25,
            'quality': 85,
            'brightness': 0,
            'contrast': 0,
            'saturation': 0
        }
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for camera USB controller"""
        logger = logging.getLogger('CameraUSBController')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'camera_usb_{datetime.now().strftime("%Y%m%d")}.log'
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
        """Setup Flask API routes"""
        
        # ===== CAMERA DETECTION & MANAGEMENT =====
        
        @self.app.route('/api/cameras', methods=['GET'])
        def list_cameras():
            """List all available USB cameras"""
            try:
                cameras = self.detect_cameras()
                return jsonify({
                    'success': True,
                    'rvm_id': self.rvm_id,
                    'cameras': cameras,
                    'total_cameras': len(cameras)
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/cameras/<int:camera_id>/info', methods=['GET'])
        def get_camera_info(camera_id):
            """Get detailed information about specific camera"""
            try:
                info = self.get_camera_info(camera_id)
                if info:
                    return jsonify({
                        'success': True,
                        'rvm_id': self.rvm_id,
                        'camera_id': camera_id,
                        'info': info
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Camera {camera_id} not found'
                    }), 404
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ===== CAMERA CONTROL =====
        
        @self.app.route('/api/cameras/<int:camera_id>/start', methods=['POST'])
        def start_camera(camera_id):
            """Start specific camera"""
            try:
                data = request.get_json() or {}
                settings = data.get('settings', {})
                
                success = self.start_camera(camera_id, settings)
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Camera {camera_id} started successfully',
                        'rvm_id': self.rvm_id,
                        'camera_id': camera_id
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to start camera {camera_id}'
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/cameras/<int:camera_id>/stop', methods=['POST'])
        def stop_camera(camera_id):
            """Stop specific camera"""
            try:
                success = self.stop_camera(camera_id)
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Camera {camera_id} stopped successfully',
                        'rvm_id': self.rvm_id,
                        'camera_id': camera_id
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Camera {camera_id} not running'
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/cameras/<int:camera_id>/restart', methods=['POST'])
        def restart_camera(camera_id):
            """Restart specific camera"""
            try:
                success = self.restart_camera(camera_id)
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Camera {camera_id} restarted successfully',
                        'rvm_id': self.rvm_id,
                        'camera_id': camera_id
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to restart camera {camera_id}'
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ===== STREAMING =====
        
        @self.app.route('/api/cameras/<int:camera_id>/stream')
        def stream_camera(camera_id):
            """Stream video from specific camera"""
            if camera_id not in self.cameras or not self.cameras[camera_id].isOpened():
                return jsonify({'error': f'Camera {camera_id} not available'}), 404
            
            return Response(self.generate_stream(camera_id),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/api/cameras/<int:camera_id>/stream/start', methods=['POST'])
        def start_streaming(camera_id):
            """Start streaming from specific camera"""
            try:
                if camera_id not in self.cameras:
                    return jsonify({
                        'success': False,
                        'error': f'Camera {camera_id} not initialized'
                    }), 404
                
                self.is_streaming = True
                self.active_camera = camera_id
                self.stats['start_time'] = time.time()
                
                return jsonify({
                    'success': True,
                    'message': f'Streaming started for camera {camera_id}',
                    'rvm_id': self.rvm_id,
                    'camera_id': camera_id,
                    'stream_url': f'/api/cameras/{camera_id}/stream'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/cameras/<int:camera_id>/stream/stop', methods=['POST'])
        def stop_streaming(camera_id):
            """Stop streaming from specific camera"""
            try:
                self.is_streaming = False
                self.active_camera = None
                
                return jsonify({
                    'success': True,
                    'message': f'Streaming stopped for camera {camera_id}',
                    'rvm_id': self.rvm_id,
                    'camera_id': camera_id
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ===== CAPTURE & SAVE =====
        
        @self.app.route('/api/cameras/<int:camera_id>/capture', methods=['POST'])
        def capture_image(camera_id):
            """Capture image from specific camera"""
            try:
                data = request.get_json() or {}
                save_to_server = data.get('save_to_server', True)
                quality = data.get('quality', self.camera_settings['quality'])
                
                result = self.capture_image(camera_id, quality, save_to_server)
                if result['success']:
                    return jsonify({
                        'success': True,
                        'rvm_id': self.rvm_id,
                        'camera_id': camera_id,
                        'filename': result['filename'],
                        'path': result['path'],
                        'size': result['size'],
                        'timestamp': result['timestamp']
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': result['error']
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/cameras/<int:camera_id>/capture/base64', methods=['POST'])
        def capture_image_base64(camera_id):
            """Capture image and return as base64"""
            try:
                data = request.get_json() or {}
                quality = data.get('quality', self.camera_settings['quality'])
                
                result = self.capture_image_base64(camera_id, quality)
                if result['success']:
                    return jsonify({
                        'success': True,
                        'rvm_id': self.rvm_id,
                        'camera_id': camera_id,
                        'image_base64': result['image_base64'],
                        'size': result['size'],
                        'timestamp': result['timestamp']
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': result['error']
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ===== CAMERA SETTINGS =====
        
        @self.app.route('/api/cameras/<int:camera_id>/settings', methods=['GET'])
        def get_camera_settings(camera_id):
            """Get camera settings"""
            try:
                if camera_id not in self.cameras:
                    return jsonify({
                        'success': False,
                        'error': f'Camera {camera_id} not initialized'
                    }), 404
                
                camera = self.cameras[camera_id]
                settings = {
                    'resolution': {
                        'width': int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        'height': int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    },
                    'fps': camera.get(cv2.CAP_PROP_FPS),
                    'brightness': camera.get(cv2.CAP_PROP_BRIGHTNESS),
                    'contrast': camera.get(cv2.CAP_PROP_CONTRAST),
                    'saturation': camera.get(cv2.CAP_PROP_SATURATION),
                    'hue': camera.get(cv2.CAP_PROP_HUE),
                    'gain': camera.get(cv2.CAP_PROP_GAIN),
                    'exposure': camera.get(cv2.CAP_PROP_EXPOSURE)
                }
                
                return jsonify({
                    'success': True,
                    'rvm_id': self.rvm_id,
                    'camera_id': camera_id,
                    'settings': settings
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/cameras/<int:camera_id>/settings', methods=['POST'])
        def set_camera_settings(camera_id):
            """Set camera settings"""
            try:
                if camera_id not in self.cameras:
                    return jsonify({
                        'success': False,
                        'error': f'Camera {camera_id} not initialized'
                    }), 404
                
                data = request.get_json()
                if not data:
                    return jsonify({
                        'success': False,
                        'error': 'No settings provided'
                    }), 400
                
                success = self.set_camera_settings(camera_id, data)
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Camera {camera_id} settings updated',
                        'rvm_id': self.rvm_id,
                        'camera_id': camera_id
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Failed to update camera {camera_id} settings'
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ===== STATUS & MONITORING =====
        
        @self.app.route('/api/cameras/status', methods=['GET'])
        def get_all_cameras_status():
            """Get status of all cameras"""
            try:
                status = {
                    'rvm_id': self.rvm_id,
                    'total_cameras': len(self.cameras),
                    'active_camera': self.active_camera,
                    'is_streaming': self.is_streaming,
                    'cameras': {}
                }
                
                for camera_id, camera in self.cameras.items():
                    status['cameras'][camera_id] = {
                        'is_opened': camera.isOpened() if camera else False,
                        'is_active': camera_id == self.active_camera,
                        'frame_count': self.stats['frame_count'] if camera_id == self.active_camera else 0
                    }
                
                return jsonify({
                    'success': True,
                    'status': status
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/cameras/<int:camera_id>/status', methods=['GET'])
        def get_camera_status(camera_id):
            """Get status of specific camera"""
            try:
                if camera_id not in self.cameras:
                    return jsonify({
                        'success': False,
                        'error': f'Camera {camera_id} not found'
                    }), 404
                
                camera = self.cameras[camera_id]
                elapsed_time = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
                current_fps = self.stats['frame_count'] / elapsed_time if elapsed_time > 0 else 0
                
                status = {
                    'rvm_id': self.rvm_id,
                    'camera_id': camera_id,
                    'is_opened': camera.isOpened(),
                    'is_active': camera_id == self.active_camera,
                    'is_streaming': self.is_streaming and camera_id == self.active_camera,
                    'frame_count': self.stats['frame_count'] if camera_id == self.active_camera else 0,
                    'current_fps': round(current_fps, 2) if camera_id == self.active_camera else 0,
                    'uptime': round(elapsed_time, 2) if camera_id == self.active_camera else 0,
                    'resolution': {
                        'width': int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        'height': int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    } if camera.isOpened() else None
                }
                
                return jsonify({
                    'success': True,
                    'status': status
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # ===== HEALTH CHECK =====
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            try:
                return jsonify({
                    'success': True,
                    'service': 'Camera USB Controller',
                    'rvm_id': self.rvm_id,
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0.0',
                    'cameras_available': len(self.cameras),
                    'active_cameras': len([c for c in self.cameras.values() if c and c.isOpened()])
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    # ===== CAMERA DETECTION METHODS =====
    
    def detect_cameras(self) -> List[Dict]:
        """Detect all available USB cameras"""
        cameras = []
        
        # Check for cameras using v4l2-ctl if available
        try:
            result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                devices = result.stdout.split('\n\n')
                for device in devices:
                    if 'video' in device.lower():
                        lines = device.strip().split('\n')
                        name = lines[0].strip()
                        for line in lines[1:]:
                            if '/dev/video' in line:
                                device_path = line.strip()
                                camera_id = int(device_path.split('/dev/video')[1])
                                cameras.append({
                                    'camera_id': camera_id,
                                    'device_path': device_path,
                                    'name': name,
                                    'type': 'usb'
                                })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback: check cameras 0-9
        if not cameras:
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        cameras.append({
                            'camera_id': i,
                            'device_path': f'/dev/video{i}',
                            'name': f'Camera {i}',
                            'type': 'usb'
                        })
                    cap.release()
        
        return cameras
    
    def get_camera_info(self, camera_id: int) -> Optional[Dict]:
        """Get detailed information about specific camera"""
        try:
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                return None
            
            info = {
                'camera_id': camera_id,
                'device_path': f'/dev/video{camera_id}',
                'resolution': {
                    'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                },
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'brightness': cap.get(cv2.CAP_PROP_BRIGHTNESS),
                'contrast': cap.get(cv2.CAP_PROP_CONTRAST),
                'saturation': cap.get(cv2.CAP_PROP_SATURATION),
                'hue': cap.get(cv2.CAP_PROP_HUE),
                'gain': cap.get(cv2.CAP_PROP_GAIN),
                'exposure': cap.get(cv2.CAP_PROP_EXPOSURE),
                'backend': cap.getBackendName()
            }
            
            cap.release()
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting camera info: {e}")
            return None
    
    # ===== CAMERA CONTROL METHODS =====
    
    def start_camera(self, camera_id: int, settings: Dict = None) -> bool:
        """Start specific camera with optional settings"""
        try:
            # Initialize camera
            camera = cv2.VideoCapture(camera_id)
            if not camera.isOpened():
                self.logger.error(f"Cannot open camera {camera_id}")
                return False
            
            # Apply settings if provided
            if settings:
                if 'resolution' in settings:
                    width = settings['resolution'].get('width', 640)
                    height = settings['resolution'].get('height', 480)
                    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                if 'fps' in settings:
                    camera.set(cv2.CAP_PROP_FPS, settings['fps'])
                
                if 'brightness' in settings:
                    camera.set(cv2.CAP_PROP_BRIGHTNESS, settings['brightness'])
                
                if 'contrast' in settings:
                    camera.set(cv2.CAP_PROP_CONTRAST, settings['contrast'])
                
                if 'saturation' in settings:
                    camera.set(cv2.CAP_PROP_SATURATION, settings['saturation'])
            
            # Store camera
            self.cameras[camera_id] = camera
            self.logger.info(f"Camera {camera_id} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting camera {camera_id}: {e}")
            return False
    
    def stop_camera(self, camera_id: int) -> bool:
        """Stop specific camera"""
        try:
            if camera_id in self.cameras:
                camera = self.cameras[camera_id]
                if camera and camera.isOpened():
                    camera.release()
                del self.cameras[camera_id]
                
                if self.active_camera == camera_id:
                    self.active_camera = None
                    self.is_streaming = False
                
                self.logger.info(f"Camera {camera_id} stopped successfully")
                return True
            else:
                self.logger.warning(f"Camera {camera_id} not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error stopping camera {camera_id}: {e}")
            return False
    
    def restart_camera(self, camera_id: int) -> bool:
        """Restart specific camera"""
        try:
            self.stop_camera(camera_id)
            time.sleep(1)
            return self.start_camera(camera_id)
        except Exception as e:
            self.logger.error(f"Error restarting camera {camera_id}: {e}")
            return False
    
    # ===== STREAMING METHODS =====
    
    def generate_stream(self, camera_id: int):
        """Generate video stream from specific camera"""
        while self.is_streaming and camera_id == self.active_camera:
            if camera_id not in self.cameras:
                break
                
            camera = self.cameras[camera_id]
            if not camera or not camera.isOpened():
                break
                
            ret, frame = camera.read()
            if not ret:
                self.logger.error(f"Cannot read frame from camera {camera_id}")
                break
            
            self.stats['frame_count'] += 1
            self.stats['last_frame_time'] = time.time()
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.camera_settings['quality']])
            
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Control frame rate
            time.sleep(1.0 / self.camera_settings['fps'])
    
    # ===== CAPTURE METHODS =====
    
    def capture_image(self, camera_id: int, quality: int = 85, save_to_server: bool = True) -> Dict:
        """Capture image from specific camera"""
        try:
            if camera_id not in self.cameras:
                return {'success': False, 'error': f'Camera {camera_id} not initialized'}
            
            camera = self.cameras[camera_id]
            if not camera or not camera.isOpened():
                return {'success': False, 'error': f'Camera {camera_id} not available'}
            
            ret, frame = camera.read()
            if not ret:
                return {'success': False, 'error': f'Cannot capture frame from camera {camera_id}'}
            
            # Save image
            output_dir = Path(__file__).parent.parent / 'storages' / 'images' / 'camera_captures'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"camera_{camera_id}_capture_{timestamp}.jpg"
            filepath = output_dir / filename
            
            cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            
            # Get file size
            file_size = filepath.stat().st_size
            
            # Upload to MyRVM Platform if requested
            if save_to_server and self.api_client:
                try:
                    success, response = self.api_client.upload_image_file(
                        str(filepath), 
                        {'rvm_id': self.rvm_id, 'camera_id': camera_id, 'type': 'camera_capture'}
                    )
                    if success:
                        self.logger.info(f"Image uploaded to MyRVM Platform: {filename}")
                except Exception as e:
                    self.logger.warning(f"Failed to upload image: {e}")
            
            self.stats['total_captures'] += 1
            
            return {
                'success': True,
                'filename': filename,
                'path': str(filepath),
                'size': file_size,
                'timestamp': timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Error capturing image from camera {camera_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def capture_image_base64(self, camera_id: int, quality: int = 85) -> Dict:
        """Capture image and return as base64"""
        try:
            if camera_id not in self.cameras:
                return {'success': False, 'error': f'Camera {camera_id} not initialized'}
            
            camera = self.cameras[camera_id]
            if not camera or not camera.isOpened():
                return {'success': False, 'error': f'Camera {camera_id} not available'}
            
            ret, frame = camera.read()
            if not ret:
                return {'success': False, 'error': f'Cannot capture frame from camera {camera_id}'}
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if not ret:
                return {'success': False, 'error': 'Failed to encode image'}
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'success': True,
                'image_base64': image_base64,
                'size': len(buffer),
                'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
            }
            
        except Exception as e:
            self.logger.error(f"Error capturing base64 image from camera {camera_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    # ===== SETTINGS METHODS =====
    
    def set_camera_settings(self, camera_id: int, settings: Dict) -> bool:
        """Set camera settings"""
        try:
            if camera_id not in self.cameras:
                return False
            
            camera = self.cameras[camera_id]
            if not camera or not camera.isOpened():
                return False
            
            # Apply settings
            if 'resolution' in settings:
                width = settings['resolution'].get('width', 640)
                height = settings['resolution'].get('height', 480)
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            if 'fps' in settings:
                camera.set(cv2.CAP_PROP_FPS, settings['fps'])
            
            if 'brightness' in settings:
                camera.set(cv2.CAP_PROP_BRIGHTNESS, settings['brightness'])
            
            if 'contrast' in settings:
                camera.set(cv2.CAP_PROP_CONTRAST, settings['contrast'])
            
            if 'saturation' in settings:
                camera.set(cv2.CAP_PROP_SATURATION, settings['saturation'])
            
            if 'hue' in settings:
                camera.set(cv2.CAP_PROP_HUE, settings['hue'])
            
            if 'gain' in settings:
                camera.set(cv2.CAP_PROP_GAIN, settings['gain'])
            
            if 'exposure' in settings:
                camera.set(cv2.CAP_PROP_EXPOSURE, settings['exposure'])
            
            self.logger.info(f"Camera {camera_id} settings updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting camera {camera_id} settings: {e}")
            return False
    
    # ===== SERVICE MANAGEMENT =====
    
    def start(self):
        """Start camera USB controller service"""
        try:
            self.logger.info(f"Starting Camera USB Controller on {self.host}:{self.port}")
            
            # Start Flask app
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
            
        except Exception as e:
            self.logger.error(f"Error starting camera USB controller: {e}")
            return False
    
    def stop(self):
        """Stop camera USB controller service"""
        try:
            # Stop all cameras
            for camera_id in list(self.cameras.keys()):
                self.stop_camera(camera_id)
            
            self.is_streaming = False
            self.active_camera = None
            
            self.logger.info("Camera USB Controller stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping camera USB controller: {e}")

# Main execution
if __name__ == "__main__":
    # Load configuration
    config_path = Path(__file__).parent.parent / 'config' / 'production_config.json'
    
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Create and start service
    controller = CameraUSBController(config)
    
    try:
        controller.start()
    except KeyboardInterrupt:
        print("\n⏹️  Camera USB Controller stopped by user")
    finally:
        controller.stop()







