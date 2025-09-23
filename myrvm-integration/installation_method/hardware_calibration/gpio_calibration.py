#!/usr/bin/env python3
"""
GPIO Calibration Module
Handles GPIO testing, calibration, and configuration
"""

import time
import logging
import json
from typing import Dict, List, Optional, Any
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO for non-Raspberry Pi systems
    class MockGPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        IN = 'IN'
        HIGH = 1
        LOW = 0
        PUD_UP = 'PUD_UP'
        PUD_DOWN = 'PUD_DOWN'
        RISING = 'RISING'
        FALLING = 'FALLING'
        BOTH = 'BOTH'
        
        @staticmethod
        def setmode(mode):
            pass
        
        @staticmethod
        def setwarnings(flag):
            pass
        
        @staticmethod
        def setup(pin, mode, pull_up_down=None):
            pass
        
        @staticmethod
        def output(pin, value):
            pass
        
        @staticmethod
        def input(pin):
            return MockGPIO.LOW
        
        @staticmethod
        def add_event_detect(pin, edge, bouncetime=None):
            pass
        
        @staticmethod
        def remove_event_detect(pin):
            pass
        
        @staticmethod
        def event_detected(pin):
            return False
        
        @staticmethod
        def cleanup():
            pass
    
    GPIO = MockGPIO()

logger = logging.getLogger(__name__)

class GPIOCalibration:
    """GPIO calibration and testing module"""
    
    def __init__(self):
        self.gpio_pins = {
            'input_pins': [5, 6, 13, 19, 26],   # GPIO pins for input
            'output_pins': [12, 16, 20, 21, 25]  # GPIO pins for output
        }
        
        self.gpio_settings = {
            'pull_up_down': GPIO.PUD_UP,
            'edge_detection': GPIO.RISING,
            'bounce_time': 300  # milliseconds
        }
        
        self.is_initialized = False
        self.calibration_data = {}
        
        # Initialize GPIO
        self._init_gpio()
    
    def _init_gpio(self):
        """Initialize GPIO pins"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup input pins
            for pin in self.gpio_pins['input_pins']:
                GPIO.setup(pin, GPIO.IN, pull_up_down=self.gpio_settings['pull_up_down'])
            
            # Setup output pins
            for pin in self.gpio_pins['output_pins']:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            
            self.is_initialized = True
            logger.info("GPIO initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
            self.is_initialized = False
    
    def test_gpio(self) -> Dict[str, Any]:
        """Test GPIO functionality"""
        logger.info("Testing GPIO...")
        
        if not self.is_initialized:
            return {
                'success': False,
                'error': 'GPIO not initialized',
                'message': 'GPIO not properly initialized'
            }
        
        try:
            test_results = {}
            
            # Test 1: Input pins
            logger.info("Testing input pins...")
            input_result = self._test_input_pins()
            test_results['input_pins'] = input_result
            
            # Test 2: Output pins
            logger.info("Testing output pins...")
            output_result = self._test_output_pins()
            test_results['output_pins'] = output_result
            
            # Test 3: Edge detection
            logger.info("Testing edge detection...")
            edge_result = self._test_edge_detection()
            test_results['edge_detection'] = edge_result
            
            # Test 4: Pull-up/down resistors
            logger.info("Testing pull-up/down resistors...")
            pull_result = self._test_pull_resistors()
            test_results['pull_resistors'] = pull_result
            
            # Calculate overall test result
            all_tests_passed = all(
                result.get('success', False) 
                for result in test_results.values()
            )
            
            return {
                'success': all_tests_passed,
                'message': 'GPIO test completed',
                'data': test_results,
                'summary': {
                    'total_tests': len(test_results),
                    'passed_tests': sum(1 for r in test_results.values() if r.get('success', False)),
                    'failed_tests': sum(1 for r in test_results.values() if not r.get('success', False))
                }
            }
            
        except Exception as e:
            logger.error(f"GPIO test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'GPIO test failed'
            }
    
    def _test_input_pins(self) -> Dict[str, Any]:
        """Test input pins"""
        try:
            input_results = {}
            
            for pin in self.gpio_pins['input_pins']:
                try:
                    # Read pin state
                    state = GPIO.input(pin)
                    input_results[f'pin_{pin}'] = {
                        'state': state,
                        'state_text': 'HIGH' if state == GPIO.HIGH else 'LOW',
                        'success': True
                    }
                except Exception as e:
                    input_results[f'pin_{pin}'] = {
                        'error': str(e),
                        'success': False
                    }
            
            all_success = all(result.get('success', False) for result in input_results.values())
            
            return {
                'success': all_success,
                'pins': input_results,
                'message': 'Input pins test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Input pins test failed'
            }
    
    def _test_output_pins(self) -> Dict[str, Any]:
        """Test output pins"""
        try:
            output_results = {}
            
            for pin in self.gpio_pins['output_pins']:
                try:
                    # Test HIGH output
                    GPIO.output(pin, GPIO.HIGH)
                    time.sleep(0.1)
                    high_state = GPIO.input(pin) if pin in self.gpio_pins['input_pins'] else None
                    
                    # Test LOW output
                    GPIO.output(pin, GPIO.LOW)
                    time.sleep(0.1)
                    low_state = GPIO.input(pin) if pin in self.gpio_pins['input_pins'] else None
                    
                    output_results[f'pin_{pin}'] = {
                        'high_output': 'HIGH' if high_state == GPIO.HIGH else 'LOW',
                        'low_output': 'LOW' if low_state == GPIO.LOW else 'HIGH',
                        'success': True
                    }
                    
                except Exception as e:
                    output_results[f'pin_{pin}'] = {
                        'error': str(e),
                        'success': False
                    }
            
            all_success = all(result.get('success', False) for result in output_results.values())
            
            return {
                'success': all_success,
                'pins': output_results,
                'message': 'Output pins test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Output pins test failed'
            }
    
    def _test_edge_detection(self) -> Dict[str, Any]:
        """Test edge detection"""
        try:
            # Test on first input pin
            test_pin = self.gpio_pins['input_pins'][0]
            
            # Setup edge detection
            GPIO.add_event_detect(test_pin, GPIO.RISING, bouncetime=self.gpio_settings['bounce_time'])
            
            # Wait for edge detection
            time.sleep(1)
            
            # Check if edge was detected
            edge_detected = GPIO.event_detected(test_pin)
            
            # Clean up
            GPIO.remove_event_detect(test_pin)
            
            return {
                'success': True,
                'test_pin': test_pin,
                'edge_detected': edge_detected,
                'bounce_time': self.gpio_settings['bounce_time'],
                'message': 'Edge detection test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Edge detection test failed'
            }
    
    def _test_pull_resistors(self) -> Dict[str, Any]:
        """Test pull-up/down resistors"""
        try:
            # Test pull-up resistor
            test_pin = self.gpio_pins['input_pins'][0]
            
            # Set pull-up
            GPIO.setup(test_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            time.sleep(0.1)
            pull_up_state = GPIO.input(test_pin)
            
            # Set pull-down
            GPIO.setup(test_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            time.sleep(0.1)
            pull_down_state = GPIO.input(test_pin)
            
            # Restore original setting
            GPIO.setup(test_pin, GPIO.IN, pull_up_down=self.gpio_settings['pull_up_down'])
            
            return {
                'success': True,
                'test_pin': test_pin,
                'pull_up_state': 'HIGH' if pull_up_state == GPIO.HIGH else 'LOW',
                'pull_down_state': 'LOW' if pull_down_state == GPIO.LOW else 'HIGH',
                'message': 'Pull resistors test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Pull resistors test failed'
            }
    
    def calibrate_gpio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calibrate GPIO settings"""
        logger.info("Calibrating GPIO...")
        
        try:
            calibration_results = {}
            
            # Calibrate pull-up/down setting
            if 'pull_up_down' in params:
                pull_setting = params['pull_up_down']
                if pull_setting in ['PUD_UP', 'PUD_DOWN', 'PUD_OFF']:
                    self.gpio_settings['pull_up_down'] = getattr(GPIO, pull_setting)
                    calibration_results['pull_up_down'] = {
                        'value': pull_setting,
                        'success': True
                    }
                else:
                    calibration_results['pull_up_down'] = {
                        'value': pull_setting,
                        'success': False,
                        'error': 'Invalid pull setting'
                    }
            
            # Calibrate edge detection
            if 'edge_detection' in params:
                edge_setting = params['edge_detection']
                if edge_setting in ['RISING', 'FALLING', 'BOTH']:
                    self.gpio_settings['edge_detection'] = getattr(GPIO, edge_setting)
                    calibration_results['edge_detection'] = {
                        'value': edge_setting,
                        'success': True
                    }
                else:
                    calibration_results['edge_detection'] = {
                        'value': edge_setting,
                        'success': False,
                        'error': 'Invalid edge detection setting'
                    }
            
            # Calibrate bounce time
            if 'bounce_time' in params:
                bounce_time = max(0, min(1000, params['bounce_time']))
                self.gpio_settings['bounce_time'] = bounce_time
                calibration_results['bounce_time'] = {
                    'value': bounce_time,
                    'success': True
                }
            
            # Test calibrated settings
            test_result = self._test_calibrated_settings()
            calibration_results['test'] = test_result
            
            # Store calibration data
            self.calibration_data = {
                'settings': self.gpio_settings.copy(),
                'calibration_params': params,
                'results': calibration_results,
                'timestamp': time.time()
            }
            
            return {
                'success': True,
                'message': 'GPIO calibration completed successfully',
                'data': calibration_results
            }
            
        except Exception as e:
            logger.error(f"GPIO calibration failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'GPIO calibration failed'
            }
    
    def _test_calibrated_settings(self) -> Dict[str, Any]:
        """Test calibrated GPIO settings"""
        try:
            # Test with calibrated settings
            test_pin = self.gpio_pins['input_pins'][0]
            
            # Apply calibrated settings
            GPIO.setup(test_pin, GPIO.IN, pull_up_down=self.gpio_settings['pull_up_down'])
            
            # Test edge detection with calibrated settings
            GPIO.add_event_detect(test_pin, self.gpio_settings['edge_detection'], 
                                bouncetime=self.gpio_settings['bounce_time'])
            
            time.sleep(0.5)
            edge_detected = GPIO.event_detected(test_pin)
            
            GPIO.remove_event_detect(test_pin)
            
            return {
                'success': True,
                'settings_applied': True,
                'edge_detected': edge_detected,
                'message': 'Calibrated settings test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Calibrated settings test failed'
            }
    
    def read_pin(self, pin: int) -> Dict[str, Any]:
        """Read GPIO pin state"""
        try:
            if pin not in self.gpio_pins['input_pins']:
                return {
                    'success': False,
                    'error': f'Pin {pin} is not configured as input',
                    'message': 'Invalid input pin'
                }
            
            state = GPIO.input(pin)
            
            return {
                'success': True,
                'data': {
                    'pin': pin,
                    'state': state,
                    'state_text': 'HIGH' if state == GPIO.HIGH else 'LOW'
                }
            }
            
        except Exception as e:
            logger.error(f"Read pin failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Read pin failed'
            }
    
    def write_pin(self, pin: int, state: bool) -> Dict[str, Any]:
        """Write GPIO pin state"""
        try:
            if pin not in self.gpio_pins['output_pins']:
                return {
                    'success': False,
                    'error': f'Pin {pin} is not configured as output',
                    'message': 'Invalid output pin'
                }
            
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            
            return {
                'success': True,
                'data': {
                    'pin': pin,
                    'state': state,
                    'state_text': 'HIGH' if state else 'LOW'
                }
            }
            
        except Exception as e:
            logger.error(f"Write pin failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Write pin failed'
            }
    
    def get_gpio_status(self) -> Dict[str, Any]:
        """Get GPIO status"""
        try:
            input_status = {}
            for pin in self.gpio_pins['input_pins']:
                try:
                    state = GPIO.input(pin)
                    input_status[f'pin_{pin}'] = {
                        'state': state,
                        'state_text': 'HIGH' if state == GPIO.HIGH else 'LOW'
                    }
                except:
                    input_status[f'pin_{pin}'] = {'error': 'Failed to read'}
            
            output_status = {}
            for pin in self.gpio_pins['output_pins']:
                try:
                    state = GPIO.input(pin)  # Read current output state
                    output_status[f'pin_{pin}'] = {
                        'state': state,
                        'state_text': 'HIGH' if state == GPIO.HIGH else 'LOW'
                    }
                except:
                    output_status[f'pin_{pin}'] = {'error': 'Failed to read'}
            
            return {
                'success': True,
                'data': {
                    'input_pins': input_status,
                    'output_pins': output_status,
                    'settings': self.gpio_settings.copy()
                }
            }
            
        except Exception as e:
            logger.error(f"Get GPIO status failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Get GPIO status failed'
            }
    
    def reset_gpio(self) -> Dict[str, Any]:
        """Reset GPIO to default settings"""
        try:
            # Reset all output pins to LOW
            for pin in self.gpio_pins['output_pins']:
                GPIO.output(pin, GPIO.LOW)
            
            # Reset settings to defaults
            self.gpio_settings.update({
                'pull_up_down': GPIO.PUD_UP,
                'edge_detection': GPIO.RISING,
                'bounce_time': 300
            })
            
            # Clear calibration data
            self.calibration_data = {}
            
            return {
                'success': True,
                'message': 'GPIO reset to default settings',
                'data': self.gpio_settings.copy()
            }
            
        except Exception as e:
            logger.error(f"Reset GPIO failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Reset GPIO failed'
            }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            if self.is_initialized:
                # Reset all output pins to LOW
                for pin in self.gpio_pins['output_pins']:
                    GPIO.output(pin, GPIO.LOW)
                GPIO.cleanup()
        except:
            pass
