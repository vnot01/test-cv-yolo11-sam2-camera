#!/usr/bin/env python3
"""
Integration Test Script
Tests the integration between Jetson Orin and MyRVM Platform
"""

import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
import subprocess

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "api-client"))
sys.path.append(str(Path(__file__).parent.parent / "services"))
sys.path.append(str(Path(__file__).parent.parent / "debug"))

from myrvm_api_client import MyRVMAPIClient
from detection_service import DetectionService
from system_monitor import SystemMonitor

class IntegrationTester:
    """Integration testing tool"""
    
    def __init__(self):
        """Initialize integration tester"""
        self.logger = self._setup_logger()
        self.test_results = []
        
        # Initialize services
        self.api_client = MyRVMAPIClient()
        self.detection_service = DetectionService()
        self.system_monitor = SystemMonitor()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for integration tester"""
        logger = logging.getLogger('IntegrationTester')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        return logger
    
    def _record_test(self, test_name: str, success: bool, message: str, details: dict = None):
        """Record test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        self.logger.info(f"{status} {test_name}: {message}")
    
    def test_system_requirements(self):
        """Test system requirements"""
        self.logger.info("=== Testing System Requirements ===")
        
        # Test Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            self._record_test("Python Version", True, f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self._record_test("Python Version", False, f"Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.8+)")
        
        # Test required packages
        required_packages = ['cv2', 'numpy', 'requests', 'ultralytics', 'psutil']
        for package in required_packages:
            try:
                __import__(package)
                self._record_test(f"Package {package}", True, f"{package} is available")
            except ImportError:
                self._record_test(f"Package {package}", False, f"{package} is not installed")
        
        # Test system resources
        health = self.system_monitor.get_system_health()
        if health['status'] in ['good', 'warning']:
            self._record_test("System Health", True, f"System status: {health['status']}", health)
        else:
            self._record_test("System Health", False, f"System status: {health['status']}", health)
    
    def test_model_availability(self):
        """Test AI model availability"""
        self.logger.info("=== Testing Model Availability ===")
        
        model_info = self.detection_service.get_model_info()
        
        # Test YOLO model
        yolo_info = model_info['yolo_model']
        if yolo_info['loaded']:
            self._record_test("YOLO Model", True, f"YOLO model loaded: {yolo_info['path']}")
        else:
            self._record_test("YOLO Model", False, f"YOLO model not loaded: {yolo_info['path']}")
        
        # Test SAM2 model
        sam2_info = model_info['sam2_model']
        if sam2_info['loaded']:
            self._record_test("SAM2 Model", True, f"SAM2 model loaded: {sam2_info['path']}")
        else:
            self._record_test("SAM2 Model", False, f"SAM2 model not loaded: {sam2_info['path']}")
    
    def test_camera_availability(self):
        """Test camera availability"""
        self.logger.info("=== Testing Camera Availability ===")
        
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self._record_test("Camera", True, "Camera is available and working")
                else:
                    self._record_test("Camera", False, "Camera opened but cannot read frames")
                cap.release()
            else:
                self._record_test("Camera", False, "Cannot open camera")
                
        except Exception as e:
            self._record_test("Camera", False, f"Camera test failed: {e}")
    
    def test_myrvm_platform_connection(self):
        """Test connection to MyRVM Platform"""
        self.logger.info("=== Testing MyRVM Platform Connection ===")
        
        # Test ping
        success, response = self.api_client.ping_platform()
        if success:
            self._record_test("MyRVM Platform Ping", True, "Successfully connected to MyRVM Platform", response)
        else:
            self._record_test("MyRVM Platform Ping", False, f"Failed to connect: {response}")
            return  # Skip other tests if platform is not reachable
        
        # Test engine registration
        engine_data = {
            'name': 'Jetson Orin Test',
            'type': 'jetson_edge',
            'status': 'active',
            'capabilities': ['object_detection', 'segmentation'],
            'location': 'Test Device',
            'ip_address': '192.168.1.11',
            'port': 5000
        }
        
        success, response = self.api_client.register_processing_engine(engine_data)
        if success:
            self._record_test("Engine Registration", True, "Successfully registered processing engine", response)
        else:
            self._record_test("Engine Registration", False, f"Failed to register: {response}")
    
    def test_detection_service(self):
        """Test detection service"""
        self.logger.info("=== Testing Detection Service ===")
        
        # Test with sample image if available
        sample_images = [
            "../storages/images/input/55_mineral_filled.jpg",
            "../storages/images/camera_captures/camera_capture_20240918_070000.jpg",
            "test_image.jpg"
        ]
        
        test_image = None
        for img_path in sample_images:
            if Path(img_path).exists():
                test_image = img_path
                break
        
        if test_image:
            # Test detection
            result = self.detection_service.detect_objects(test_image)
            if 'error' not in result:
                self._record_test("Object Detection", True, f"Detection successful: {result['total_detections']} objects found", result)
            else:
                self._record_test("Object Detection", False, f"Detection failed: {result['error']}")
            
            # Test segmentation if SAM2 is available
            if self.detection_service.sam2_model:
                result = self.detection_service.segment_objects(test_image)
                if 'error' not in result:
                    self._record_test("Object Segmentation", True, f"Segmentation successful: {result['total_segments']} segments", result)
                else:
                    self._record_test("Object Segmentation", False, f"Segmentation failed: {result['error']}")
            else:
                self._record_test("Object Segmentation", False, "SAM2 model not available")
        else:
            self._record_test("Detection Service", False, "No test image available")
    
    def test_file_system(self):
        """Test file system and directories"""
        self.logger.info("=== Testing File System ===")
        
        # Test required directories
        required_dirs = [
            "../models",
            "../storages/images/input",
            "../storages/images/output",
            "../logs"
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists():
                self._record_test(f"Directory {dir_path}", True, "Directory exists")
            else:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self._record_test(f"Directory {dir_path}", True, "Directory created")
                except Exception as e:
                    self._record_test(f"Directory {dir_path}", False, f"Failed to create: {e}")
        
        # Test write permissions
        test_file = Path("../logs/test_write.txt")
        try:
            test_file.write_text("test")
            test_file.unlink()
            self._record_test("Write Permissions", True, "Write permissions OK")
        except Exception as e:
            self._record_test("Write Permissions", False, f"Write failed: {e}")
    
    def test_network_connectivity(self):
        """Test network connectivity"""
        self.logger.info("=== Testing Network Connectivity ===")
        
        # Test internet connectivity
        try:
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self._record_test("Internet Connectivity", True, "Internet connection OK")
            else:
                self._record_test("Internet Connectivity", False, "No internet connection")
        except Exception as e:
            self._record_test("Internet Connectivity", False, f"Connectivity test failed: {e}")
        
        # Test MyRVM Platform connectivity
        try:
            import requests
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                self._record_test("MyRVM Platform Connectivity", True, "MyRVM Platform reachable")
            else:
                self._record_test("MyRVM Platform Connectivity", False, f"HTTP {response.status_code}")
        except Exception as e:
            self._record_test("MyRVM Platform Connectivity", False, f"Connection failed: {e}")
    
    def run_all_tests(self):
        """Run all integration tests"""
        self.logger.info("🚀 Starting Integration Tests")
        start_time = time.time()
        
        # Run all test suites
        self.test_system_requirements()
        self.test_model_availability()
        self.test_camera_availability()
        self.test_file_system()
        self.test_network_connectivity()
        self.test_myrvm_platform_connection()
        self.test_detection_service()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        duration = time.time() - start_time
        
        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("📊 INTEGRATION TEST SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"Passed: {passed_tests}")
        self.logger.info(f"Failed: {failed_tests}")
        self.logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        
        # Save results
        results_file = Path("../logs") / f"integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                },
                'results': self.test_results
            }, f, indent=2)
        
        self.logger.info(f"✅ Test results saved to: {results_file}")
        
        # Return success status
        return failed_tests == 0

# Example usage
if __name__ == "__main__":
    tester = IntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some integration tests failed!")
        sys.exit(1)
