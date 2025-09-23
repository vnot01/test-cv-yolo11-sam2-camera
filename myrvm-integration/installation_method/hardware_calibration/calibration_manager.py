#!/usr/bin/env python3
"""
Hardware Calibration Manager
Main coordinator for all hardware calibration operations
"""

import os
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from .camera_calibration import CameraCalibration
from .motor_calibration import MotorCalibration
from .led_calibration import LEDCalibration
from .touch_calibration import TouchCalibration
from .gpio_calibration import GPIOCalibration
from .sensor_calibration import SensorCalibration
from .audio_calibration import AudioCalibration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalibrationManager:
    """Main calibration manager for all hardware components"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.calibration_data = {}
        self.calibration_status = {}
        self.is_calibrating = False
        
        # Initialize calibration modules
        self.camera_cal = CameraCalibration()
        self.motor_cal = MotorCalibration()
        self.led_cal = LEDCalibration()
        self.touch_cal = TouchCalibration()
        self.gpio_cal = GPIOCalibration()
        self.sensor_cal = SensorCalibration()
        self.audio_cal = AudioCalibration()
        
        # Create config directory
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load existing calibration data
        self.load_calibration_data()
    
    def load_calibration_data(self):
        """Load existing calibration data from file"""
        calibration_file = os.path.join(self.config_dir, "calibration_data.json")
        
        if os.path.exists(calibration_file):
            try:
                with open(calibration_file, 'r') as f:
                    self.calibration_data = json.load(f)
                logger.info("Calibration data loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load calibration data: {e}")
                self.calibration_data = {}
        else:
            self.calibration_data = {}
            logger.info("No existing calibration data found")
    
    def save_calibration_data(self):
        """Save calibration data to file"""
        calibration_file = os.path.join(self.config_dir, "calibration_data.json")
        
        try:
            with open(calibration_file, 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
            logger.info("Calibration data saved successfully")
        except Exception as e:
            logger.error(f"Failed to save calibration data: {e}")
    
    def get_calibration_status(self) -> Dict[str, Any]:
        """Get current calibration status for all components"""
        return {
            'timestamp': datetime.now().isoformat(),
            'is_calibrating': self.is_calibrating,
            'components': self.calibration_status,
            'overall_status': self.get_overall_status()
        }
    
    def get_overall_status(self) -> str:
        """Get overall calibration status"""
        if not self.calibration_status:
            return 'not_started'
        
        statuses = [status.get('status', 'unknown') for status in self.calibration_status.values()]
        
        if all(status == 'completed' for status in statuses):
            return 'completed'
        elif any(status == 'error' for status in statuses):
            return 'error'
        elif any(status == 'in_progress' for status in statuses):
            return 'in_progress'
        else:
            return 'partial'
    
    def test_all_components(self) -> Dict[str, Any]:
        """Test all hardware components"""
        logger.info("Starting hardware component testing...")
        
        results = {}
        
        # Test camera
        try:
            logger.info("Testing camera...")
            camera_result = self.camera_cal.test_camera()
            results['camera'] = camera_result
            self.calibration_status['camera'] = {
                'status': 'completed' if camera_result.get('success') else 'error',
                'message': camera_result.get('message', 'Camera test completed'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Camera test failed: {e}")
            results['camera'] = {'success': False, 'error': str(e)}
            self.calibration_status['camera'] = {
                'status': 'error',
                'message': f'Camera test failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Test motor
        try:
            logger.info("Testing motor...")
            motor_result = self.motor_cal.test_motor()
            results['motor'] = motor_result
            self.calibration_status['motor'] = {
                'status': 'completed' if motor_result.get('success') else 'error',
                'message': motor_result.get('message', 'Motor test completed'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Motor test failed: {e}")
            results['motor'] = {'success': False, 'error': str(e)}
            self.calibration_status['motor'] = {
                'status': 'error',
                'message': f'Motor test failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Test LED
        try:
            logger.info("Testing LED...")
            led_result = self.led_cal.test_led()
            results['led'] = led_result
            self.calibration_status['led'] = {
                'status': 'completed' if led_result.get('success') else 'error',
                'message': led_result.get('message', 'LED test completed'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"LED test failed: {e}")
            results['led'] = {'success': False, 'error': str(e)}
            self.calibration_status['led'] = {
                'status': 'error',
                'message': f'LED test failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Test touch screen
        try:
            logger.info("Testing touch screen...")
            touch_result = self.touch_cal.test_touch_screen()
            results['touch_screen'] = touch_result
            self.calibration_status['touch_screen'] = {
                'status': 'completed' if touch_result.get('success') else 'error',
                'message': touch_result.get('message', 'Touch screen test completed'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Touch screen test failed: {e}")
            results['touch_screen'] = {'success': False, 'error': str(e)}
            self.calibration_status['touch_screen'] = {
                'status': 'error',
                'message': f'Touch screen test failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Test GPIO
        try:
            logger.info("Testing GPIO...")
            gpio_result = self.gpio_cal.test_gpio()
            results['gpio'] = gpio_result
            self.calibration_status['gpio'] = {
                'status': 'completed' if gpio_result.get('success') else 'error',
                'message': gpio_result.get('message', 'GPIO test completed'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"GPIO test failed: {e}")
            results['gpio'] = {'success': False, 'error': str(e)}
            self.calibration_status['gpio'] = {
                'status': 'error',
                'message': f'GPIO test failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Test sensors
        try:
            logger.info("Testing sensors...")
            sensor_result = self.sensor_cal.test_sensors()
            results['sensors'] = sensor_result
            self.calibration_status['sensors'] = {
                'status': 'completed' if sensor_result.get('success') else 'error',
                'message': sensor_result.get('message', 'Sensor test completed'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Sensor test failed: {e}")
            results['sensors'] = {'success': False, 'error': str(e)}
            self.calibration_status['sensors'] = {
                'status': 'error',
                'message': f'Sensor test failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        
        # Test audio
        try:
            logger.info("Testing audio...")
            audio_result = self.audio_cal.test_audio()
            results['audio'] = audio_result
            self.calibration_status['audio'] = {
                'status': 'completed' if audio_result.get('success') else 'error',
                'message': audio_result.get('message', 'Audio test completed'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Audio test failed: {e}")
            results['audio'] = {'success': False, 'error': str(e)}
            self.calibration_status['audio'] = {
                'status': 'error',
                'message': f'Audio test failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        
        logger.info("Hardware component testing completed")
        return results
    
    def calibrate_all_components(self, calibration_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calibrate all hardware components"""
        if self.is_calibrating:
            return {'success': False, 'error': 'Calibration already in progress'}
        
        self.is_calibrating = True
        logger.info("Starting hardware calibration...")
        
        try:
            results = {}
            
            # Camera calibration
            if calibration_params and 'camera' in calibration_params:
                logger.info("Calibrating camera...")
                camera_result = self.camera_cal.calibrate_camera(calibration_params['camera'])
                results['camera'] = camera_result
                self.calibration_status['camera'] = {
                    'status': 'completed' if camera_result.get('success') else 'error',
                    'message': camera_result.get('message', 'Camera calibration completed'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Motor calibration
            if calibration_params and 'motor' in calibration_params:
                logger.info("Calibrating motor...")
                motor_result = self.motor_cal.calibrate_motor(calibration_params['motor'])
                results['motor'] = motor_result
                self.calibration_status['motor'] = {
                    'status': 'completed' if motor_result.get('success') else 'error',
                    'message': motor_result.get('message', 'Motor calibration completed'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # LED calibration
            if calibration_params and 'led' in calibration_params:
                logger.info("Calibrating LED...")
                led_result = self.led_cal.calibrate_led(calibration_params['led'])
                results['led'] = led_result
                self.calibration_status['led'] = {
                    'status': 'completed' if led_result.get('success') else 'error',
                    'message': led_result.get('message', 'LED calibration completed'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Touch screen calibration
            if calibration_params and 'touch_screen' in calibration_params:
                logger.info("Calibrating touch screen...")
                touch_result = self.touch_cal.calibrate_touch_screen(calibration_params['touch_screen'])
                results['touch_screen'] = touch_result
                self.calibration_status['touch_screen'] = {
                    'status': 'completed' if touch_result.get('success') else 'error',
                    'message': touch_result.get('message', 'Touch screen calibration completed'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Save calibration data
            self.calibration_data.update(results)
            self.save_calibration_data()
            
            logger.info("Hardware calibration completed")
            return {
                'success': True,
                'message': 'Hardware calibration completed successfully',
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Hardware calibration failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Hardware calibration failed'
            }
        finally:
            self.is_calibrating = False
    
    def calibrate_component(self, component: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calibrate specific hardware component"""
        logger.info(f"Calibrating {component}...")
        
        try:
            if component == 'camera':
                result = self.camera_cal.calibrate_camera(params)
            elif component == 'motor':
                result = self.motor_cal.calibrate_motor(params)
            elif component == 'led':
                result = self.led_cal.calibrate_led(params)
            elif component == 'touch_screen':
                result = self.touch_cal.calibrate_touch_screen(params)
            elif component == 'gpio':
                result = self.gpio_cal.calibrate_gpio(params)
            elif component == 'sensors':
                result = self.sensor_cal.calibrate_sensors(params)
            elif component == 'audio':
                result = self.audio_cal.calibrate_audio(params)
            else:
                return {'success': False, 'error': f'Unknown component: {component}'}
            
            # Update calibration status
            self.calibration_status[component] = {
                'status': 'completed' if result.get('success') else 'error',
                'message': result.get('message', f'{component} calibration completed'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Save calibration data
            if result.get('success'):
                self.calibration_data[component] = result.get('data', {})
                self.save_calibration_data()
            
            return result
            
        except Exception as e:
            logger.error(f"{component} calibration failed: {e}")
            self.calibration_status[component] = {
                'status': 'error',
                'message': f'{component} calibration failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            return {'success': False, 'error': str(e)}
    
    def get_calibration_report(self) -> Dict[str, Any]:
        """Generate calibration report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': self.get_overall_status(),
            'components': self.calibration_status,
            'calibration_data': self.calibration_data,
            'summary': {
                'total_components': len(self.calibration_status),
                'completed': len([s for s in self.calibration_status.values() if s.get('status') == 'completed']),
                'errors': len([s for s in self.calibration_status.values() if s.get('status') == 'error']),
                'in_progress': len([s for s in self.calibration_status.values() if s.get('status') == 'in_progress'])
            }
        }
    
    def reset_calibration(self):
        """Reset all calibration data"""
        logger.info("Resetting calibration data...")
        
        self.calibration_data = {}
        self.calibration_status = {}
        self.is_calibrating = False
        
        # Remove calibration file
        calibration_file = os.path.join(self.config_dir, "calibration_data.json")
        if os.path.exists(calibration_file):
            os.remove(calibration_file)
        
        logger.info("Calibration data reset completed")
    
    def export_calibration(self, export_path: str) -> bool:
        """Export calibration data to file"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'calibration_data': self.calibration_data,
                'calibration_status': self.calibration_status,
                'version': '1.0.0'
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Calibration data exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export calibration data: {e}")
            return False
    
    def import_calibration(self, import_path: str) -> bool:
        """Import calibration data from file"""
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            self.calibration_data = import_data.get('calibration_data', {})
            self.calibration_status = import_data.get('calibration_status', {})
            
            # Save imported data
            self.save_calibration_data()
            
            logger.info(f"Calibration data imported from {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import calibration data: {e}")
            return False


