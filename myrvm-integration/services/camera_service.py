#!/usr/bin/env python3
"""
Camera Service for MyRVM Platform Integration
Real-time camera processing with automatic detection upload
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

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "api-client"))

from myrvm_api_client import MyRVMAPIClient
from detection_service import DetectionService

class CameraService:
    """Real-time camera service with MyRVM Platform integration"""
    
    def __init__(self, config: Dict):
        """
        Initialize camera service
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.camera_index = config.get('camera_index', 0)
        self.capture_interval = config.get('capture_interval', 5.0)
        self.confidence_threshold = config.get('confidence_threshold', 0.5)
        self.rvm_id = config.get('rvm_id', 1)
        self.auto_processing = config.get('auto_processing', True)
        
        # Initialize components
        self.camera = None
        self.detection_service = DetectionService()
        self.api_client = MyRVMAPIClient(
            base_url=config.get('myrvm_base_url'),
            use_tunnel=config.get('use_tunnel', False)
        )
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Processing queue and threads
        self.processing_queue = queue.Queue(maxsize=config.get('max_processing_queue', 10))
        self.is_running = False
        self.capture_thread = None
        self.processing_thread = None
        
        # Statistics
        self.stats = {
            'images_captured': 0,
            'images_processed': 0,
            'detections_uploaded': 0,
            'errors': 0,
            'start_time': None
        }
        
        # Create output directories
        self._create_output_directories()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for camera service"""
        logger = logging.getLogger('CameraService')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'camera_service_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _create_output_directories(self):
        """Create output directories for images and results"""
        base_dir = Path(__file__).parent.parent.parent / 'storages' / 'images'
        
        directories = [
            'camera_captures',
            'output/camera_yolo/results/images',
            'output/camera_yolo/results/inference',
            'output/myrvm-integration'
        ]
        
        for dir_path in directories:
            full_path = base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {full_path}")
    
    def initialize_camera(self) -> bool:
        """Initialize camera"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                self.logger.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            # Test camera
            ret, frame = self.camera.read()
            if not ret:
                self.logger.error("Failed to read from camera")
                return False
            
            self.logger.info(f"Camera {self.camera_index} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {e}")
            return False
    
    def authenticate_with_platform(self) -> bool:
        """Authenticate with MyRVM Platform"""
        try:
            success, response = self.api_client.login(
                email='admin@myrvm.com',
                password='password'
            )
            
            if success:
                self.logger.info("Successfully authenticated with MyRVM Platform")
                return True
            else:
                self.logger.error(f"Authentication failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    def capture_image(self) -> Optional[str]:
        """Capture image from camera"""
        try:
            if not self.camera or not self.camera.isOpened():
                self.logger.error("Camera not initialized")
                return None
            
            ret, frame = self.camera.read()
            if not ret:
                self.logger.error("Failed to capture frame")
                return None
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"camera_capture_{timestamp}.jpg"
            
            # Save image
            base_dir = Path(__file__).parent.parent.parent / 'storages' / 'images' / 'camera_captures'
            image_path = base_dir / filename
            
            cv2.imwrite(str(image_path), frame)
            
            self.stats['images_captured'] += 1
            self.logger.info(f"Image captured: {image_path}")
            
            return str(image_path)
            
        except Exception as e:
            self.logger.error(f"Image capture failed: {e}")
            self.stats['errors'] += 1
            return None
    
    def process_image(self, image_path: str) -> Optional[Dict]:
        """Process image with AI detection"""
        try:
            # Run detection
            results = self.detection_service.detect_objects(
                image_path, 
                confidence_threshold=self.confidence_threshold
            )
            
            if 'error' in results:
                self.logger.error(f"Detection failed: {results['error']}")
                return None
            
            self.stats['images_processed'] += 1
            self.logger.info(f"Image processed: {results['total_detections']} objects detected")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Image processing failed: {e}")
            self.stats['errors'] += 1
            return None
    
    def upload_detection_results(self, image_path: str, detection_results: Dict) -> bool:
        """Upload detection results to MyRVM Platform"""
        try:
            # Prepare detection data
            detection_data = {
                'rvm_id': self.rvm_id,
                'image_path': image_path,
                'detections': detection_results.get('detections', []),
                'status': 'processed',
                'timestamp': datetime.now().isoformat()
            }
            
            # Upload to platform
            success, response = self.api_client.upload_detection_results(detection_data)
            
            if success:
                self.stats['detections_uploaded'] += 1
                self.logger.info(f"Detection results uploaded successfully")
                return True
            else:
                self.logger.error(f"Upload failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Upload error: {e}")
            self.stats['errors'] += 1
            return False
    
    def capture_worker(self):
        """Camera capture worker thread"""
        self.logger.info("Camera capture worker started")
        
        while self.is_running:
            try:
                # Capture image
                image_path = self.capture_image()
                
                if image_path and self.auto_processing:
                    # Add to processing queue
                    try:
                        self.processing_queue.put(image_path, timeout=1)
                    except queue.Full:
                        self.logger.warning("Processing queue full, skipping image")
                
                # Wait for next capture
                time.sleep(self.capture_interval)
                
            except Exception as e:
                self.logger.error(f"Capture worker error: {e}")
                time.sleep(1)
        
        self.logger.info("Camera capture worker stopped")
    
    def processing_worker(self):
        """Image processing worker thread"""
        self.logger.info("Image processing worker started")
        
        while self.is_running:
            try:
                # Get image from queue
                image_path = self.processing_queue.get(timeout=1)
                
                # Process image
                detection_results = self.process_image(image_path)
                
                if detection_results:
                    # Upload results
                    self.upload_detection_results(image_path, detection_results)
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Processing worker error: {e}")
                time.sleep(1)
        
        self.logger.info("Image processing worker stopped")
    
    def start(self) -> bool:
        """Start camera service"""
        try:
            # Initialize camera
            if not self.initialize_camera():
                return False
            
            # Authenticate with platform
            if not self.authenticate_with_platform():
                return False
            
            # Start service
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            # Start worker threads
            self.capture_thread = threading.Thread(target=self.capture_worker)
            self.processing_thread = threading.Thread(target=self.processing_worker)
            
            self.capture_thread.start()
            self.processing_thread.start()
            
            self.logger.info("Camera service started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start camera service: {e}")
            return False
    
    def stop(self):
        """Stop camera service"""
        self.logger.info("Stopping camera service...")
        
        # Stop worker threads
        self.is_running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=5)
        
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        
        # Release camera
        if self.camera:
            self.camera.release()
        
        self.logger.info("Camera service stopped")
    
    def get_status(self) -> Dict:
        """Get service status"""
        uptime = 0
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'is_running': self.is_running,
            'camera_initialized': self.camera is not None and self.camera.isOpened(),
            'queue_size': self.processing_queue.qsize(),
            'uptime_seconds': uptime,
            'stats': self.stats.copy()
        }
    
    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        uptime = 0
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            'uptime_seconds': uptime,
            'images_captured': self.stats['images_captured'],
            'images_processed': self.stats['images_processed'],
            'detections_uploaded': self.stats['detections_uploaded'],
            'errors': self.stats['errors'],
            'capture_rate': self.stats['images_captured'] / (uptime / 60) if uptime > 0 else 0,
            'processing_rate': self.stats['images_processed'] / (uptime / 60) if uptime > 0 else 0,
            'upload_rate': self.stats['detections_uploaded'] / (uptime / 60) if uptime > 0 else 0
        }

# Example usage and testing
if __name__ == "__main__":
    # Load configuration
    config_path = Path(__file__).parent.parent / 'main' / 'config.json'
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {
            'camera_index': 0,
            'capture_interval': 5.0,
            'confidence_threshold': 0.5,
            'rvm_id': 1,
            'auto_processing': True,
            'myrvm_base_url': 'http://172.28.233.83:8001',
            'use_tunnel': False,
            'max_processing_queue': 10
        }
    
    # Create and start camera service
    camera_service = CameraService(config)
    
    try:
        if camera_service.start():
            print("🎥 Camera service started successfully!")
            print("Press Ctrl+C to stop...")
            
            # Monitor service
            while True:
                time.sleep(10)
                stats = camera_service.get_statistics()
                print(f"📊 Stats: Captured: {stats['images_captured']}, "
                      f"Processed: {stats['images_processed']}, "
                      f"Uploaded: {stats['detections_uploaded']}, "
                      f"Errors: {stats['errors']}")
        else:
            print("❌ Failed to start camera service")
    
    except KeyboardInterrupt:
        print("\n⏹️  Stopping camera service...")
        camera_service.stop()
        print("✅ Camera service stopped")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        camera_service.stop()
