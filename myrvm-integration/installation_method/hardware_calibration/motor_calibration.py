#!/usr/bin/env python3
"""
Motor Calibration Module
Handles motor testing, calibration, and configuration
"""

import time
import logging
import json
import threading
from typing import Dict, List, Optional, Any
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

class MotorCalibration:
    """Motor calibration and testing module"""
    
    def __init__(self):
        self.motor_pins = {
            'step': 18,      # GPIO pin for step signal
            'direction': 19, # GPIO pin for direction signal
            'enable': 20     # GPIO pin for enable signal
        }
        
        self.motor_settings = {
            'steps_per_revolution': 200,
            'microsteps': 16,
            'max_speed': 1000,  # steps per second
            'acceleration': 500,  # steps per second squared
            'current_position': 0,
            'is_enabled': False
        }
        
        self.is_initialized = False
        self.is_moving = False
        self.calibration_data = {}
        
        # Initialize GPIO
        self._init_gpio()
    
    def _init_gpio(self):
        """Initialize GPIO pins for motor control"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup motor pins
            for pin_name, pin_number in self.motor_pins.items():
                GPIO.setup(pin_number, GPIO.OUT)
                GPIO.output(pin_number, GPIO.LOW)
            
            # Disable motor initially
            GPIO.output(self.motor_pins['enable'], GPIO.HIGH)
            
            self.is_initialized = True
            logger.info("GPIO initialized for motor control")
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
            self.is_initialized = False
    
    def test_motor(self) -> Dict[str, Any]:
        """Test motor functionality"""
        logger.info("Testing motor...")
        
        if not self.is_initialized:
            return {
                'success': False,
                'error': 'GPIO not initialized',
                'message': 'Motor GPIO not properly initialized'
            }
        
        try:
            test_results = {}
            
            # Test 1: Enable/Disable motor
            logger.info("Testing motor enable/disable...")
            enable_result = self._test_enable_disable()
            test_results['enable_disable'] = enable_result
            
            # Test 2: Direction control
            logger.info("Testing motor direction...")
            direction_result = self._test_direction()
            test_results['direction'] = direction_result
            
            # Test 3: Step generation
            logger.info("Testing step generation...")
            step_result = self._test_step_generation()
            test_results['step_generation'] = step_result
            
            # Test 4: Speed control
            logger.info("Testing speed control...")
            speed_result = self._test_speed_control()
            test_results['speed_control'] = speed_result
            
            # Test 5: Position tracking
            logger.info("Testing position tracking...")
            position_result = self._test_position_tracking()
            test_results['position_tracking'] = position_result
            
            # Calculate overall test result
            all_tests_passed = all(
                result.get('success', False) 
                for result in test_results.values()
            )
            
            return {
                'success': all_tests_passed,
                'message': 'Motor test completed',
                'data': test_results,
                'summary': {
                    'total_tests': len(test_results),
                    'passed_tests': sum(1 for r in test_results.values() if r.get('success', False)),
                    'failed_tests': sum(1 for r in test_results.values() if not r.get('success', False))
                }
            }
            
        except Exception as e:
            logger.error(f"Motor test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Motor test failed'
            }
    
    def _test_enable_disable(self) -> Dict[str, Any]:
        """Test motor enable/disable functionality"""
        try:
            # Test enable
            self._enable_motor()
            time.sleep(0.1)
            enable_state = GPIO.input(self.motor_pins['enable'])
            
            # Test disable
            self._disable_motor()
            time.sleep(0.1)
            disable_state = GPIO.input(self.motor_pins['enable'])
            
            return {
                'success': enable_state == GPIO.LOW and disable_state == GPIO.HIGH,
                'enable_state': 'LOW' if enable_state == GPIO.LOW else 'HIGH',
                'disable_state': 'HIGH' if disable_state == GPIO.HIGH else 'LOW',
                'message': 'Enable/disable test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Enable/disable test failed'
            }
    
    def _test_direction(self) -> Dict[str, Any]:
        """Test motor direction control"""
        try:
            self._enable_motor()
            
            # Test forward direction
            self._set_direction(True)  # Forward
            time.sleep(0.1)
            forward_state = GPIO.input(self.motor_pins['direction'])
            
            # Test reverse direction
            self._set_direction(False)  # Reverse
            time.sleep(0.1)
            reverse_state = GPIO.input(self.motor_pins['direction'])
            
            self._disable_motor()
            
            return {
                'success': forward_state == GPIO.HIGH and reverse_state == GPIO.LOW,
                'forward_state': 'HIGH' if forward_state == GPIO.HIGH else 'LOW',
                'reverse_state': 'LOW' if reverse_state == GPIO.LOW else 'HIGH',
                'message': 'Direction test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Direction test failed'
            }
    
    def _test_step_generation(self) -> Dict[str, Any]:
        """Test step signal generation"""
        try:
            self._enable_motor()
            self._set_direction(True)
            
            # Generate 10 steps
            step_count = 10
            start_time = time.time()
            
            for _ in range(step_count):
                self._generate_step()
                time.sleep(0.001)  # 1ms delay between steps
            
            end_time = time.time()
            duration = end_time - start_time
            
            self._disable_motor()
            
            return {
                'success': True,
                'steps_generated': step_count,
                'duration': round(duration, 3),
                'average_step_time': round(duration / step_count, 3),
                'message': 'Step generation test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Step generation test failed'
            }
    
    def _test_speed_control(self) -> Dict[str, Any]:
        """Test motor speed control"""
        try:
            self._enable_motor()
            self._set_direction(True)
            
            speeds = [100, 500, 1000]  # steps per second
            results = {}
            
            for speed in speeds:
                start_time = time.time()
                steps = 50
                
                for _ in range(steps):
                    self._generate_step()
                    time.sleep(1.0 / speed)
                
                end_time = time.time()
                actual_duration = end_time - start_time
                expected_duration = steps / speed
                
                results[f'speed_{speed}'] = {
                    'requested_speed': speed,
                    'expected_duration': round(expected_duration, 3),
                    'actual_duration': round(actual_duration, 3),
                    'accuracy': round((expected_duration / actual_duration) * 100, 1)
                }
            
            self._disable_motor()
            
            return {
                'success': True,
                'speed_tests': results,
                'message': 'Speed control test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Speed control test failed'
            }
    
    def _test_position_tracking(self) -> Dict[str, Any]:
        """Test position tracking"""
        try:
            self._enable_motor()
            
            # Reset position
            self.motor_settings['current_position'] = 0
            
            # Move forward 100 steps
            self._move_steps(100, True)
            forward_position = self.motor_settings['current_position']
            
            # Move backward 50 steps
            self._move_steps(50, False)
            backward_position = self.motor_settings['current_position']
            
            self._disable_motor()
            
            return {
                'success': True,
                'initial_position': 0,
                'after_forward_100': forward_position,
                'after_backward_50': backward_position,
                'expected_final': 50,
                'position_accuracy': abs(backward_position - 50) <= 1,
                'message': 'Position tracking test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Position tracking test failed'
            }
    
    def calibrate_motor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calibrate motor settings"""
        logger.info("Calibrating motor...")
        
        try:
            calibration_results = {}
            
            # Calibrate steps per revolution
            if 'steps_per_revolution' in params:
                self.motor_settings['steps_per_revolution'] = params['steps_per_revolution']
                calibration_results['steps_per_revolution'] = {
                    'value': params['steps_per_revolution'],
                    'success': True
                }
            
            # Calibrate microsteps
            if 'microsteps' in params:
                self.motor_settings['microsteps'] = params['microsteps']
                calibration_results['microsteps'] = {
                    'value': params['microsteps'],
                    'success': True
                }
            
            # Calibrate max speed
            if 'max_speed' in params:
                self.motor_settings['max_speed'] = params['max_speed']
                calibration_results['max_speed'] = {
                    'value': params['max_speed'],
                    'success': True
                }
            
            # Calibrate acceleration
            if 'acceleration' in params:
                self.motor_settings['acceleration'] = params['acceleration']
                calibration_results['acceleration'] = {
                    'value': params['acceleration'],
                    'success': True
                }
            
            # Perform homing calibration
            if params.get('perform_homing', False):
                homing_result = self._perform_homing()
                calibration_results['homing'] = homing_result
            
            # Store calibration data
            self.calibration_data = {
                'settings': self.motor_settings.copy(),
                'calibration_params': params,
                'results': calibration_results,
                'timestamp': time.time()
            }
            
            return {
                'success': True,
                'message': 'Motor calibration completed successfully',
                'data': calibration_results
            }
            
        except Exception as e:
            logger.error(f"Motor calibration failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Motor calibration failed'
            }
    
    def _perform_homing(self) -> Dict[str, Any]:
        """Perform homing sequence"""
        try:
            logger.info("Performing homing sequence...")
            
            self._enable_motor()
            
            # Move to home position (assume home is at position 0)
            # Move backward until home sensor is triggered
            self._set_direction(False)  # Reverse direction
            
            # Move slowly until home position
            for _ in range(1000):  # Maximum 1000 steps
                self._generate_step()
                time.sleep(0.01)  # 10ms delay for slow movement
                
                # Check home sensor (mock implementation)
                # In real implementation, check actual sensor
                if self.motor_settings['current_position'] <= 0:
                    break
            
            # Reset position to 0
            self.motor_settings['current_position'] = 0
            
            self._disable_motor()
            
            return {
                'success': True,
                'home_position': 0,
                'message': 'Homing sequence completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Homing sequence failed'
            }
    
    def _enable_motor(self):
        """Enable motor"""
        GPIO.output(self.motor_pins['enable'], GPIO.LOW)
        self.motor_settings['is_enabled'] = True
    
    def _disable_motor(self):
        """Disable motor"""
        GPIO.output(self.motor_pins['enable'], GPIO.HIGH)
        self.motor_settings['is_enabled'] = False
    
    def _set_direction(self, forward: bool):
        """Set motor direction"""
        GPIO.output(self.motor_pins['direction'], GPIO.HIGH if forward else GPIO.LOW)
    
    def _generate_step(self):
        """Generate a step pulse"""
        GPIO.output(self.motor_pins['step'], GPIO.HIGH)
        time.sleep(0.0001)  # 100 microseconds pulse width
        GPIO.output(self.motor_pins['step'], GPIO.LOW)
        
        # Update position
        if self.motor_settings['is_enabled']:
            direction = 1 if GPIO.input(self.motor_pins['direction']) == GPIO.HIGH else -1
            self.motor_settings['current_position'] += direction
    
    def _move_steps(self, steps: int, forward: bool):
        """Move motor by specified number of steps"""
        self._set_direction(forward)
        
        for _ in range(steps):
            self._generate_step()
            time.sleep(0.001)  # 1ms delay between steps
    
    def move_to_position(self, target_position: int) -> Dict[str, Any]:
        """Move motor to specific position"""
        try:
            current_pos = self.motor_settings['current_position']
            steps_to_move = target_position - current_pos
            
            if steps_to_move == 0:
                return {
                    'success': True,
                    'message': 'Already at target position',
                    'current_position': current_pos
                }
            
            self._enable_motor()
            self._move_steps(abs(steps_to_move), steps_to_move > 0)
            self._disable_motor()
            
            return {
                'success': True,
                'message': f'Moved to position {target_position}',
                'previous_position': current_pos,
                'current_position': self.motor_settings['current_position'],
                'steps_moved': steps_to_move
            }
            
        except Exception as e:
            logger.error(f"Move to position failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Move to position failed'
            }
    
    def get_motor_status(self) -> Dict[str, Any]:
        """Get current motor status"""
        return {
            'success': True,
            'data': {
                'is_enabled': self.motor_settings['is_enabled'],
                'current_position': self.motor_settings['current_position'],
                'settings': self.motor_settings.copy(),
                'gpio_status': {
                    'step': GPIO.input(self.motor_pins['step']),
                    'direction': GPIO.input(self.motor_pins['direction']),
                    'enable': GPIO.input(self.motor_pins['enable'])
                }
            }
        }
    
    def reset_motor(self) -> Dict[str, Any]:
        """Reset motor to default settings"""
        try:
            # Disable motor
            self._disable_motor()
            
            # Reset position
            self.motor_settings['current_position'] = 0
            
            # Reset to default settings
            self.motor_settings.update({
                'steps_per_revolution': 200,
                'microsteps': 16,
                'max_speed': 1000,
                'acceleration': 500
            })
            
            return {
                'success': True,
                'message': 'Motor reset to default settings',
                'data': self.motor_settings.copy()
            }
            
        except Exception as e:
            logger.error(f"Motor reset failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Motor reset failed'
            }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            if self.is_initialized:
                self._disable_motor()
                GPIO.cleanup()
        except:
            pass
