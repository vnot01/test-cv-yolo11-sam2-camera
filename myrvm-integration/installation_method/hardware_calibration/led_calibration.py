#!/usr/bin/env python3
"""
LED Calibration Module
Handles LED testing, calibration, and configuration
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

class LEDCalibration:
    """LED calibration and testing module"""
    
    def __init__(self):
        self.led_pins = {
            'status_led': 21,    # GPIO pin for status LED
            'warning_led': 22,   # GPIO pin for warning LED
            'error_led': 23,     # GPIO pin for error LED
            'backlight': 24      # GPIO pin for backlight
        }
        
        self.led_settings = {
            'brightness': 100,   # 0-100%
            'blink_rate': 1.0,   # seconds
            'color_mode': 'white'  # white, red, green, blue
        }
        
        self.is_initialized = False
        self.calibration_data = {}
        
        # Initialize GPIO
        self._init_gpio()
    
    def _init_gpio(self):
        """Initialize GPIO pins for LED control"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup LED pins
            for led_name, pin_number in self.led_pins.items():
                GPIO.setup(pin_number, GPIO.OUT)
                GPIO.output(pin_number, GPIO.LOW)
            
            self.is_initialized = True
            logger.info("GPIO initialized for LED control")
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
            self.is_initialized = False
    
    def test_led(self) -> Dict[str, Any]:
        """Test LED functionality"""
        logger.info("Testing LEDs...")
        
        if not self.is_initialized:
            return {
                'success': False,
                'error': 'GPIO not initialized',
                'message': 'LED GPIO not properly initialized'
            }
        
        try:
            test_results = {}
            
            # Test each LED
            for led_name, pin_number in self.led_pins.items():
                logger.info(f"Testing {led_name}...")
                led_result = self._test_single_led(led_name, pin_number)
                test_results[led_name] = led_result
            
            # Test LED patterns
            pattern_result = self._test_led_patterns()
            test_results['patterns'] = pattern_result
            
            # Calculate overall test result
            all_tests_passed = all(
                result.get('success', False) 
                for result in test_results.values()
                if isinstance(result, dict)
            )
            
            return {
                'success': all_tests_passed,
                'message': 'LED test completed',
                'data': test_results,
                'summary': {
                    'total_leds': len(self.led_pins),
                    'working_leds': sum(1 for r in test_results.values() 
                                      if isinstance(r, dict) and r.get('success', False)),
                    'failed_leds': sum(1 for r in test_results.values() 
                                     if isinstance(r, dict) and not r.get('success', False))
                }
            }
            
        except Exception as e:
            logger.error(f"LED test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'LED test failed'
            }
    
    def _test_single_led(self, led_name: str, pin_number: int) -> Dict[str, Any]:
        """Test single LED"""
        try:
            # Turn LED on
            GPIO.output(pin_number, GPIO.HIGH)
            time.sleep(0.5)
            
            # Check if LED is on
            led_state = GPIO.input(pin_number)
            
            # Turn LED off
            GPIO.output(pin_number, GPIO.LOW)
            time.sleep(0.1)
            
            return {
                'success': led_state == GPIO.HIGH,
                'pin_number': pin_number,
                'state_when_on': 'HIGH' if led_state == GPIO.HIGH else 'LOW',
                'message': f'{led_name} test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'{led_name} test failed'
            }
    
    def _test_led_patterns(self) -> Dict[str, Any]:
        """Test LED patterns"""
        try:
            patterns = {
                'all_on': self._pattern_all_on(),
                'all_off': self._pattern_all_off(),
                'blink': self._pattern_blink(),
                'chase': self._pattern_chase()
            }
            
            return {
                'success': all(pattern.get('success', False) for pattern in patterns.values()),
                'patterns': patterns,
                'message': 'LED pattern tests completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'LED pattern tests failed'
            }
    
    def _pattern_all_on(self) -> Dict[str, Any]:
        """Test pattern: all LEDs on"""
        try:
            # Turn all LEDs on
            for pin_number in self.led_pins.values():
                GPIO.output(pin_number, GPIO.HIGH)
            
            time.sleep(1)
            
            # Turn all LEDs off
            for pin_number in self.led_pins.values():
                GPIO.output(pin_number, GPIO.LOW)
            
            return {
                'success': True,
                'message': 'All LEDs on pattern completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'All LEDs on pattern failed'
            }
    
    def _pattern_all_off(self) -> Dict[str, Any]:
        """Test pattern: all LEDs off"""
        try:
            # Ensure all LEDs are off
            for pin_number in self.led_pins.values():
                GPIO.output(pin_number, GPIO.LOW)
            
            time.sleep(0.5)
            
            return {
                'success': True,
                'message': 'All LEDs off pattern completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'All LEDs off pattern failed'
            }
    
    def _pattern_blink(self) -> Dict[str, Any]:
        """Test pattern: blinking LEDs"""
        try:
            # Blink all LEDs 3 times
            for _ in range(3):
                # Turn on
                for pin_number in self.led_pins.values():
                    GPIO.output(pin_number, GPIO.HIGH)
                time.sleep(0.3)
                
                # Turn off
                for pin_number in self.led_pins.values():
                    GPIO.output(pin_number, GPIO.LOW)
                time.sleep(0.3)
            
            return {
                'success': True,
                'message': 'Blink pattern completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Blink pattern failed'
            }
    
    def _pattern_chase(self) -> Dict[str, Any]:
        """Test pattern: chasing LEDs"""
        try:
            # Chase pattern - LEDs turn on one by one
            for led_name, pin_number in self.led_pins.items():
                GPIO.output(pin_number, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(pin_number, GPIO.LOW)
            
            return {
                'success': True,
                'message': 'Chase pattern completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Chase pattern failed'
            }
    
    def calibrate_led(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calibrate LED settings"""
        logger.info("Calibrating LEDs...")
        
        try:
            calibration_results = {}
            
            # Calibrate brightness
            if 'brightness' in params:
                brightness = max(0, min(100, params['brightness']))
                self.led_settings['brightness'] = brightness
                calibration_results['brightness'] = {
                    'value': brightness,
                    'success': True
                }
            
            # Calibrate blink rate
            if 'blink_rate' in params:
                blink_rate = max(0.1, min(5.0, params['blink_rate']))
                self.led_settings['blink_rate'] = blink_rate
                calibration_results['blink_rate'] = {
                    'value': blink_rate,
                    'success': True
                }
            
            # Calibrate color mode
            if 'color_mode' in params:
                color_mode = params['color_mode']
                if color_mode in ['white', 'red', 'green', 'blue']:
                    self.led_settings['color_mode'] = color_mode
                    calibration_results['color_mode'] = {
                        'value': color_mode,
                        'success': True
                    }
                else:
                    calibration_results['color_mode'] = {
                        'value': color_mode,
                        'success': False,
                        'error': 'Invalid color mode'
                    }
            
            # Test calibrated settings
            test_result = self._test_calibrated_settings()
            calibration_results['test'] = test_result
            
            # Store calibration data
            self.calibration_data = {
                'settings': self.led_settings.copy(),
                'calibration_params': params,
                'results': calibration_results,
                'timestamp': time.time()
            }
            
            return {
                'success': True,
                'message': 'LED calibration completed successfully',
                'data': calibration_results
            }
            
        except Exception as e:
            logger.error(f"LED calibration failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'LED calibration failed'
            }
    
    def _test_calibrated_settings(self) -> Dict[str, Any]:
        """Test calibrated LED settings"""
        try:
            # Test brightness by turning on status LED
            GPIO.output(self.led_pins['status_led'], GPIO.HIGH)
            time.sleep(1)
            GPIO.output(self.led_pins['status_led'], GPIO.LOW)
            
            # Test blink rate
            blink_count = 3
            for _ in range(blink_count):
                GPIO.output(self.led_pins['warning_led'], GPIO.HIGH)
                time.sleep(self.led_settings['blink_rate'] / 2)
                GPIO.output(self.led_pins['warning_led'], GPIO.LOW)
                time.sleep(self.led_settings['blink_rate'] / 2)
            
            return {
                'success': True,
                'message': 'Calibrated settings test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Calibrated settings test failed'
            }
    
    def set_led_state(self, led_name: str, state: bool) -> Dict[str, Any]:
        """Set LED state"""
        try:
            if led_name not in self.led_pins:
                return {
                    'success': False,
                    'error': f'Unknown LED: {led_name}',
                    'message': 'LED not found'
                }
            
            pin_number = self.led_pins[led_name]
            GPIO.output(pin_number, GPIO.HIGH if state else GPIO.LOW)
            
            return {
                'success': True,
                'message': f'{led_name} set to {"ON" if state else "OFF"}',
                'data': {
                    'led_name': led_name,
                    'state': state,
                    'pin_number': pin_number
                }
            }
            
        except Exception as e:
            logger.error(f"Set LED state failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Set LED state failed'
            }
    
    def blink_led(self, led_name: str, duration: float = 1.0) -> Dict[str, Any]:
        """Blink LED for specified duration"""
        try:
            if led_name not in self.led_pins:
                return {
                    'success': False,
                    'error': f'Unknown LED: {led_name}',
                    'message': 'LED not found'
                }
            
            pin_number = self.led_pins[led_name]
            blink_rate = self.led_settings['blink_rate']
            end_time = time.time() + duration
            
            while time.time() < end_time:
                GPIO.output(pin_number, GPIO.HIGH)
                time.sleep(blink_rate / 2)
                GPIO.output(pin_number, GPIO.LOW)
                time.sleep(blink_rate / 2)
            
            return {
                'success': True,
                'message': f'{led_name} blinked for {duration} seconds',
                'data': {
                    'led_name': led_name,
                    'duration': duration,
                    'blink_rate': blink_rate
                }
            }
            
        except Exception as e:
            logger.error(f"Blink LED failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Blink LED failed'
            }
    
    def get_led_status(self) -> Dict[str, Any]:
        """Get current LED status"""
        try:
            led_status = {}
            for led_name, pin_number in self.led_pins.items():
                led_status[led_name] = {
                    'pin_number': pin_number,
                    'state': GPIO.input(pin_number) == GPIO.HIGH,
                    'state_text': 'ON' if GPIO.input(pin_number) == GPIO.HIGH else 'OFF'
                }
            
            return {
                'success': True,
                'data': {
                    'leds': led_status,
                    'settings': self.led_settings.copy()
                }
            }
            
        except Exception as e:
            logger.error(f"Get LED status failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Get LED status failed'
            }
    
    def reset_leds(self) -> Dict[str, Any]:
        """Reset all LEDs to default state"""
        try:
            # Turn off all LEDs
            for pin_number in self.led_pins.values():
                GPIO.output(pin_number, GPIO.LOW)
            
            # Reset settings to defaults
            self.led_settings.update({
                'brightness': 100,
                'blink_rate': 1.0,
                'color_mode': 'white'
            })
            
            return {
                'success': True,
                'message': 'LEDs reset to default state',
                'data': self.led_settings.copy()
            }
            
        except Exception as e:
            logger.error(f"Reset LEDs failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Reset LEDs failed'
            }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            if self.is_initialized:
                # Turn off all LEDs
                for pin_number in self.led_pins.values():
                    GPIO.output(pin_number, GPIO.LOW)
                GPIO.cleanup()
        except:
            pass
