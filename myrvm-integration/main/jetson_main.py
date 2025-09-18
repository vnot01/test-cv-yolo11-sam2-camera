#!/usr/bin/env python3
"""
Jetson Orin Main Coordinator
Main application for Jetson Orin integration with MyRVM Platform
"""

import cv2
import time
import json
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import sys
import os
import signal

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from api_client.myrvm_api_client import MyRVMAPIClient
from services.detection_service import DetectionService

class JetsonMain:
    """Main coordinator for Jetson Orin integration"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize Jetson Main coordinator
        
        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.running = False
        self.camera = None
        self.camera_index = self.config.get('camera_index', 0)
        
        # Initialize services
        self.api_client = MyRVMAPIClient(
            base_url=self.config.get('myrvm_base_url', 'http://localhost:8000'),
            api_token=self.config.get('api_token'),
            tunnel_url=self.config.get('myrvm_tunnel_url'),
            use_tunnel=self.config.get('use_tunnel', False)
        )
        self.detection_service = DetectionService(
            models_dir=self.config.get('models_dir', '../models')
        )
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Processing state
        self.current_session = None
        self.current_rvm_id = self.config.get('rvm_id', 1)
        self.processing_queue = []
        self.processing_thread = None
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from file"""
        config_path = Path(__file__).parent / config_file
        
        default_config = {
            'myrvm_base_url': 'http://localhost:8000',
            'api_token': None,
            'camera_index': 0,
            'rvm_id': 1,
            'models_dir': '../models',
            'capture_interval': 5.0,  # seconds
            'confidence_threshold': 0.5,
            'auto_processing': True,
            'debug_mode': True
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                print(f"✅ Configuration loaded from: {config_path}")
            except Exception as e:
                print(f"⚠️  Failed to load config file: {e}")
                print("Using default configuration")
        else:
            # Create default config file
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"📝 Created default config file: {config_path}")
        
        return default_config
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for main coordinator"""
        logger = logging.getLogger('JetsonMain')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'jetson_main_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def initialize_camera(self) -> bool:
        """Initialize camera"""
        try:
            self.logger.info(f"Initializing camera {self.camera_index}")
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                self.logger.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            # Get actual properties
            width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            self.logger.info(f"✅ Camera initialized: {width}x{height} @ {fps} FPS")
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {e}")
            return False
    
    def register_with_platform(self) -> bool:
        """Register Jetson Orin with MyRVM Platform"""
        try:
            self.logger.info("Registering with MyRVM Platform...")
            
            # Test connectivity first
            success, response = self.api_client.ping_platform()
            if not success:
                self.logger.error(f"Failed to connect to MyRVM Platform: {response}")
                return False
            
            # Register as processing engine
            engine_data = {
                'name': f'Jetson Orin Edge - RVM {self.current_rvm_id}',
                'type': 'jetson_edge',
                'status': 'active',
                'capabilities': ['object_detection', 'segmentation'],
                'location': f'RVM {self.current_rvm_id}',
                'ip_address': self.config.get('jetson_ip', '192.168.1.11'),
                'port': self.config.get('jetson_port', 5000)
            }
            
            success, response = self.api_client.register_processing_engine(engine_data)
            if success:
                self.logger.info("✅ Successfully registered with MyRVM Platform")
                return True
            else:
                self.logger.error(f"Failed to register: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Registration failed: {e}")
            return False
    
    def capture_image(self) -> Optional[str]:
        """Capture image from camera"""
        if not self.camera or not self.camera.isOpened():
            return None
        
        try:
            ret, frame = self.camera.read()
            if not ret:
                return None
            
            # Save captured image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jetson_capture_{timestamp}.jpg"
            filepath = Path("../storages/images/camera_captures") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            cv2.imwrite(str(filepath), frame)
            self.logger.info(f"📸 Image captured: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Image capture failed: {e}")
            return None
    
    def process_image(self, image_path: str) -> Dict:
        """Process image with AI models"""
        try:
            self.logger.info(f"Processing image: {image_path}")
            
            # Run detection and segmentation
            results = self.detection_service.detect_and_segment(
                image_path, 
                self.config.get('confidence_threshold', 0.5)
            )
            
            if 'error' in results:
                self.logger.error(f"Processing failed: {results['error']}")
                return results
            
            # Save results
            results_file = self.detection_service.save_results(results)
            self.logger.info(f"✅ Processing completed, results saved: {results_file}")
            
            return results
            
        except Exception as e:
            error_msg = f"Image processing failed: {e}"
            self.logger.error(error_msg)
            return {'error': error_msg}
    
    def send_results_to_platform(self, image_path: str, results: Dict) -> bool:
        """Send processing results to MyRVM Platform"""
        try:
            self.logger.info("Sending results to MyRVM Platform...")
            
            # Prepare results data
            results_data = {
                'rvm_id': self.current_rvm_id,
                'image_path': image_path,
                'timestamp': datetime.now().isoformat(),
                'detections': results.get('detection', {}).get('detections', []),
                'segments': results.get('segmentation', {}).get('segments', []),
                'processing_time': results.get('total_time', 0)
            }
            
            # Upload results
            success, response = self.api_client.upload_detection_results(results_data)
            if success:
                self.logger.info("✅ Results sent to MyRVM Platform")
                return True
            else:
                self.logger.error(f"Failed to send results: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send results: {e}")
            return False
    
    def processing_worker(self):
        """Background processing worker"""
        while self.running:
            if self.processing_queue:
                image_path = self.processing_queue.pop(0)
                
                try:
                    # Process image
                    results = self.process_image(image_path)
                    
                    if 'error' not in results:
                        # Send results to platform
                        self.send_results_to_platform(image_path, results)
                    
                except Exception as e:
                    self.logger.error(f"Processing worker error: {e}")
            
            time.sleep(0.1)  # Small delay to prevent busy waiting
    
    def start_processing_worker(self):
        """Start background processing worker"""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.processing_thread = threading.Thread(target=self.processing_worker)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            self.logger.info("✅ Processing worker started")
    
    def run(self):
        """Main run loop"""
        try:
            self.logger.info("🚀 Starting Jetson Orin Main Coordinator")
            
            # Initialize camera
            if not self.initialize_camera():
                self.logger.error("Failed to initialize camera")
                return
            
            # Register with platform
            if not self.register_with_platform():
                self.logger.error("Failed to register with MyRVM Platform")
                return
            
            # Start processing worker
            if self.config.get('auto_processing', True):
                self.start_processing_worker()
            
            self.running = True
            self.logger.info("✅ Jetson Orin Main Coordinator started successfully")
            
            # Main loop
            last_capture = time.time()
            capture_interval = self.config.get('capture_interval', 5.0)
            
            while self.running:
                current_time = time.time()
                
                # Capture image at intervals
                if current_time - last_capture >= capture_interval:
                    image_path = self.capture_image()
                    if image_path:
                        if self.config.get('auto_processing', True):
                            # Add to processing queue
                            self.processing_queue.append(image_path)
                        else:
                            # Process immediately
                            results = self.process_image(image_path)
                            if 'error' not in results:
                                self.send_results_to_platform(image_path, results)
                    
                    last_capture = current_time
                
                time.sleep(0.1)  # Small delay
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the coordinator"""
        self.logger.info("🛑 Stopping Jetson Orin Main Coordinator")
        self.running = False
        
        # Release camera
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
        
        self.logger.info("✅ Jetson Orin Main Coordinator stopped")

# Example usage and testing
if __name__ == "__main__":
    # Initialize and run
    coordinator = JetsonMain()
    
    try:
        coordinator.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        coordinator.stop()
