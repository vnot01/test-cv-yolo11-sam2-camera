#!/usr/bin/env python3
"""
Camera Calibration Module
Handles camera testing, calibration, and configuration
"""

import cv2
import numpy as np
import logging
import time
import json
import os
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class CameraCalibration:
    """Camera calibration and testing module"""
    
    def __init__(self):
        self.camera = None
        self.calibration_data = {}
        self.is_camera_open = False
        
        # Camera settings
        self.default_settings = {
            'width': 1920,
            'height': 1080,
            'fps': 30,
            'brightness': 50,
            'contrast': 50,
            'saturation': 50,
            'hue': 0,
            'exposure': -6,
            'gain': 0,
            'white_balance': 4000
        }
    
    def test_camera(self) -> Dict[str, Any]:
        """Test camera functionality"""
        logger.info("Testing camera...")
        
        try:
            # Try to open camera
            self.camera = cv2.VideoCapture(0)
            
            if not self.camera.isOpened():
                return {
                    'success': False,
                    'error': 'Failed to open camera',
                    'message': 'Camera not accessible'
                }
            
            self.is_camera_open = True
            
            # Get camera properties
            width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            # Test frame capture
            ret, frame = self.camera.read()
            if not ret:
                return {
                    'success': False,
                    'error': 'Failed to capture frame',
                    'message': 'Camera frame capture failed'
                }
            
            # Analyze frame quality
            frame_analysis = self._analyze_frame(frame)
            
            # Test different resolutions
            resolution_tests = self._test_resolutions()
            
            # Close camera
            self.camera.release()
            self.is_camera_open = False
            
            return {
                'success': True,
                'message': 'Camera test completed successfully',
                'data': {
                    'resolution': f"{width}x{height}",
                    'fps': fps,
                    'frame_analysis': frame_analysis,
                    'resolution_tests': resolution_tests,
                    'camera_info': {
                        'backend': self.camera.getBackendName(),
                        'format': self.camera.get(cv2.CAP_PROP_FORMAT),
                        'mode': self.camera.get(cv2.CAP_PROP_MODE)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Camera test failed: {e}")
            if self.is_camera_open:
                self.camera.release()
                self.is_camera_open = False
            
            return {
                'success': False,
                'error': str(e),
                'message': 'Camera test failed'
            }
    
    def _analyze_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyze frame quality"""
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate image statistics
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            
            # Calculate contrast
            contrast = std_brightness / mean_brightness if mean_brightness > 0 else 0
            
            # Detect blur using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (frame.shape[0] * frame.shape[1])
            
            return {
                'mean_brightness': float(mean_brightness),
                'std_brightness': float(std_brightness),
                'contrast': float(contrast),
                'sharpness': float(laplacian_var),
                'edge_density': float(edge_density),
                'quality_score': self._calculate_quality_score(mean_brightness, contrast, laplacian_var)
            }
            
        except Exception as e:
            logger.error(f"Frame analysis failed: {e}")
            return {'error': str(e)}
    
    def _calculate_quality_score(self, brightness: float, contrast: float, sharpness: float) -> float:
        """Calculate overall image quality score"""
        # Normalize values (0-100 scale)
        brightness_score = min(100, max(0, (brightness / 128) * 100))
        contrast_score = min(100, max(0, contrast * 100))
        sharpness_score = min(100, max(0, sharpness / 100))
        
        # Weighted average
        quality_score = (brightness_score * 0.3 + contrast_score * 0.3 + sharpness_score * 0.4)
        return round(quality_score, 2)
    
    def _test_resolutions(self) -> List[Dict[str, Any]]:
        """Test different camera resolutions"""
        resolutions = [
            (640, 480),
            (1280, 720),
            (1920, 1080),
            (2560, 1440)
        ]
        
        results = []
        
        for width, height in resolutions:
            try:
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # Wait for settings to take effect
                time.sleep(0.1)
                
                # Check actual resolution
                actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Test frame capture
                ret, frame = self.camera.read()
                
                results.append({
                    'requested': f"{width}x{height}",
                    'actual': f"{actual_width}x{actual_height}",
                    'supported': ret and actual_width == width and actual_height == height,
                    'fps': self.camera.get(cv2.CAP_PROP_FPS)
                })
                
            except Exception as e:
                results.append({
                    'requested': f"{width}x{height}",
                    'actual': "N/A",
                    'supported': False,
                    'error': str(e)
                })
        
        return results
    
    def calibrate_camera(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calibrate camera settings"""
        logger.info("Calibrating camera...")
        
        try:
            # Open camera
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                return {
                    'success': False,
                    'error': 'Failed to open camera',
                    'message': 'Camera not accessible for calibration'
                }
            
            self.is_camera_open = True
            
            # Apply calibration parameters
            calibration_results = {}
            
            # Set resolution
            if 'width' in params and 'height' in params:
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, params['width'])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, params['height'])
                time.sleep(0.1)
                
                actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                calibration_results['resolution'] = {
                    'requested': f"{params['width']}x{params['height']}",
                    'actual': f"{actual_width}x{actual_height}",
                    'success': actual_width == params['width'] and actual_height == params['height']
                }
            
            # Set brightness
            if 'brightness' in params:
                self.camera.set(cv2.CAP_PROP_BRIGHTNESS, params['brightness'] / 100.0)
                actual_brightness = self.camera.get(cv2.CAP_PROP_BRIGHTNESS) * 100
                calibration_results['brightness'] = {
                    'requested': params['brightness'],
                    'actual': round(actual_brightness, 2),
                    'success': abs(actual_brightness - params['brightness']) < 5
                }
            
            # Set contrast
            if 'contrast' in params:
                self.camera.set(cv2.CAP_PROP_CONTRAST, params['contrast'] / 100.0)
                actual_contrast = self.camera.get(cv2.CAP_PROP_CONTRAST) * 100
                calibration_results['contrast'] = {
                    'requested': params['contrast'],
                    'actual': round(actual_contrast, 2),
                    'success': abs(actual_contrast - params['contrast']) < 5
                }
            
            # Set saturation
            if 'saturation' in params:
                self.camera.set(cv2.CAP_PROP_SATURATION, params['saturation'] / 100.0)
                actual_saturation = self.camera.get(cv2.CAP_PROP_SATURATION) * 100
                calibration_results['saturation'] = {
                    'requested': params['saturation'],
                    'actual': round(actual_saturation, 2),
                    'success': abs(actual_saturation - params['saturation']) < 5
                }
            
            # Set exposure
            if 'exposure' in params:
                self.camera.set(cv2.CAP_PROP_EXPOSURE, params['exposure'])
                actual_exposure = self.camera.get(cv2.CAP_PROP_EXPOSURE)
                calibration_results['exposure'] = {
                    'requested': params['exposure'],
                    'actual': round(actual_exposure, 2),
                    'success': abs(actual_exposure - params['exposure']) < 1
                }
            
            # Set gain
            if 'gain' in params:
                self.camera.set(cv2.CAP_PROP_GAIN, params['gain'])
                actual_gain = self.camera.get(cv2.CAP_PROP_GAIN)
                calibration_results['gain'] = {
                    'requested': params['gain'],
                    'actual': round(actual_gain, 2),
                    'success': abs(actual_gain - params['gain']) < 1
                }
            
            # Set white balance
            if 'white_balance' in params:
                self.camera.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, params['white_balance'])
                actual_wb = self.camera.get(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U)
                calibration_results['white_balance'] = {
                    'requested': params['white_balance'],
                    'actual': round(actual_wb, 2),
                    'success': abs(actual_wb - params['white_balance']) < 100
                }
            
            # Test calibrated settings
            ret, frame = self.camera.read()
            if ret:
                frame_analysis = self._analyze_frame(frame)
                calibration_results['frame_analysis'] = frame_analysis
            
            # Close camera
            self.camera.release()
            self.is_camera_open = False
            
            # Store calibration data
            self.calibration_data = {
                'settings': params,
                'results': calibration_results,
                'timestamp': time.time()
            }
            
            return {
                'success': True,
                'message': 'Camera calibration completed successfully',
                'data': calibration_results
            }
            
        except Exception as e:
            logger.error(f"Camera calibration failed: {e}")
            if self.is_camera_open:
                self.camera.release()
                self.is_camera_open = False
            
            return {
                'success': False,
                'error': str(e),
                'message': 'Camera calibration failed'
            }
    
    def capture_test_image(self, save_path: str = "test_image.jpg") -> Dict[str, Any]:
        """Capture test image with current settings"""
        try:
            if not self.is_camera_open:
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    return {
                        'success': False,
                        'error': 'Failed to open camera',
                        'message': 'Camera not accessible'
                    }
                self.is_camera_open = True
            
            # Capture frame
            ret, frame = self.camera.read()
            if not ret:
                return {
                    'success': False,
                    'error': 'Failed to capture frame',
                    'message': 'Frame capture failed'
                }
            
            # Save image
            cv2.imwrite(save_path, frame)
            
            # Analyze captured image
            frame_analysis = self._analyze_frame(frame)
            
            return {
                'success': True,
                'message': 'Test image captured successfully',
                'data': {
                    'image_path': save_path,
                    'resolution': f"{frame.shape[1]}x{frame.shape[0]}",
                    'analysis': frame_analysis
                }
            }
            
        except Exception as e:
            logger.error(f"Test image capture failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Test image capture failed'
            }
    
    def get_camera_info(self) -> Dict[str, Any]:
        """Get detailed camera information"""
        try:
            if not self.is_camera_open:
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    return {
                        'success': False,
                        'error': 'Failed to open camera',
                        'message': 'Camera not accessible'
                    }
                self.is_camera_open = True
            
            info = {
                'backend': self.camera.getBackendName(),
                'width': int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': self.camera.get(cv2.CAP_PROP_FPS),
                'brightness': self.camera.get(cv2.CAP_PROP_BRIGHTNESS),
                'contrast': self.camera.get(cv2.CAP_PROP_CONTRAST),
                'saturation': self.camera.get(cv2.CAP_PROP_SATURATION),
                'hue': self.camera.get(cv2.CAP_PROP_HUE),
                'exposure': self.camera.get(cv2.CAP_PROP_EXPOSURE),
                'gain': self.camera.get(cv2.CAP_PROP_GAIN),
                'white_balance_blue': self.camera.get(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U),
                'white_balance_red': self.camera.get(cv2.CAP_PROP_WHITE_BALANCE_RED_V),
                'format': self.camera.get(cv2.CAP_PROP_FORMAT),
                'mode': self.camera.get(cv2.CAP_PROP_MODE),
                'buffer_size': self.camera.get(cv2.CAP_PROP_BUFFERSIZE)
            }
            
            return {
                'success': True,
                'message': 'Camera information retrieved successfully',
                'data': info
            }
            
        except Exception as e:
            logger.error(f"Failed to get camera info: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get camera information'
            }
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """Reset camera to default settings"""
        logger.info("Resetting camera to default settings...")
        
        try:
            if not self.is_camera_open:
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    return {
                        'success': False,
                        'error': 'Failed to open camera',
                        'message': 'Camera not accessible'
                    }
                self.is_camera_open = True
            
            # Apply default settings
            for setting, value in self.default_settings.items():
                if setting == 'width':
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, value)
                elif setting == 'height':
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, value)
                elif setting == 'fps':
                    self.camera.set(cv2.CAP_PROP_FPS, value)
                elif setting == 'brightness':
                    self.camera.set(cv2.CAP_PROP_BRIGHTNESS, value / 100.0)
                elif setting == 'contrast':
                    self.camera.set(cv2.CAP_PROP_CONTRAST, value / 100.0)
                elif setting == 'saturation':
                    self.camera.set(cv2.CAP_PROP_SATURATION, value / 100.0)
                elif setting == 'hue':
                    self.camera.set(cv2.CAP_PROP_HUE, value)
                elif setting == 'exposure':
                    self.camera.set(cv2.CAP_PROP_EXPOSURE, value)
                elif setting == 'gain':
                    self.camera.set(cv2.CAP_PROP_GAIN, value)
                elif setting == 'white_balance':
                    self.camera.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, value)
            
            # Wait for settings to take effect
            time.sleep(0.5)
            
            # Verify settings
            current_settings = self.get_camera_info()
            
            return {
                'success': True,
                'message': 'Camera reset to default settings',
                'data': {
                    'default_settings': self.default_settings,
                    'current_settings': current_settings.get('data', {})
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to reset camera: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to reset camera settings'
            }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.is_camera_open and self.camera is not None:
            self.camera.release()
            self.is_camera_open = False










