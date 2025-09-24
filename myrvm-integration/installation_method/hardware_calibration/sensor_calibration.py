#!/usr/bin/env python3
"""
Sensor Calibration Module
Handles sensor testing, calibration, and configuration
"""

import time
import logging
import json
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class SensorCalibration:
    """Sensor calibration and testing module"""
    
    def __init__(self):
        self.sensors = {
            'door_sensor': {'type': 'magnetic', 'pin': 5, 'active_low': True},
            'weight_sensor': {'type': 'load_cell', 'pin': 6, 'calibration_factor': 1.0},
            'proximity_sensor': {'type': 'ultrasonic', 'pin': 13, 'max_range': 200},
            'temperature_sensor': {'type': 'ds18b20', 'pin': 19, 'resolution': 12},
            'humidity_sensor': {'type': 'dht22', 'pin': 26, 'accuracy': 2.0}
        }
        
        self.sensor_settings = {
            'sampling_rate': 1.0,  # seconds
            'calibration_enabled': True,
            'threshold_sensitivity': 0.1
        }
        
        self.calibration_data = {}
    
    def test_sensors(self) -> Dict[str, Any]:
        """Test all sensors"""
        logger.info("Testing sensors...")
        
        try:
            test_results = {}
            
            # Test each sensor
            for sensor_name, sensor_info in self.sensors.items():
                logger.info(f"Testing {sensor_name}...")
                sensor_result = self._test_single_sensor(sensor_name, sensor_info)
                test_results[sensor_name] = sensor_result
            
            # Test sensor integration
            integration_result = self._test_sensor_integration()
            test_results['integration'] = integration_result
            
            # Calculate overall test result
            all_tests_passed = all(
                result.get('success', False) 
                for result in test_results.values()
                if isinstance(result, dict)
            )
            
            return {
                'success': all_tests_passed,
                'message': 'Sensor test completed',
                'data': test_results,
                'summary': {
                    'total_sensors': len(self.sensors),
                    'working_sensors': sum(1 for r in test_results.values() 
                                         if isinstance(r, dict) and r.get('success', False)),
                    'failed_sensors': sum(1 for r in test_results.values() 
                                        if isinstance(r, dict) and not r.get('success', False))
                }
            }
            
        except Exception as e:
            logger.error(f"Sensor test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Sensor test failed'
            }
    
    def _test_single_sensor(self, sensor_name: str, sensor_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test single sensor"""
        try:
            sensor_type = sensor_info['type']
            
            if sensor_type == 'magnetic':
                return self._test_magnetic_sensor(sensor_name, sensor_info)
            elif sensor_type == 'load_cell':
                return self._test_load_cell_sensor(sensor_name, sensor_info)
            elif sensor_type == 'ultrasonic':
                return self._test_ultrasonic_sensor(sensor_name, sensor_info)
            elif sensor_type == 'ds18b20':
                return self._test_temperature_sensor(sensor_name, sensor_info)
            elif sensor_type == 'dht22':
                return self._test_humidity_sensor(sensor_name, sensor_info)
            else:
                return {
                    'success': False,
                    'error': f'Unknown sensor type: {sensor_type}',
                    'message': f'{sensor_name} test failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'{sensor_name} test failed'
            }
    
    def _test_magnetic_sensor(self, sensor_name: str, sensor_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test magnetic door sensor"""
        try:
            # Mock magnetic sensor test
            # In real implementation, this would read from GPIO pin
            
            # Simulate door open/closed states
            door_states = ['open', 'closed', 'open', 'closed']
            readings = []
            
            for state in door_states:
                # Simulate reading
                reading = {
                    'state': state,
                    'value': 0 if state == 'closed' else 1,
                    'timestamp': time.time()
                }
                readings.append(reading)
                time.sleep(0.1)
            
            return {
                'success': True,
                'sensor_type': 'magnetic',
                'readings': readings,
                'pin': sensor_info['pin'],
                'active_low': sensor_info['active_low'],
                'message': f'{sensor_name} test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'{sensor_name} test failed'
            }
    
    def _test_load_cell_sensor(self, sensor_name: str, sensor_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test weight/load cell sensor"""
        try:
            # Mock load cell test
            # In real implementation, this would read from ADC
            
            # Simulate weight readings
            test_weights = [0, 100, 500, 1000, 0]  # grams
            readings = []
            
            for weight in test_weights:
                # Simulate reading with some noise
                raw_value = weight * sensor_info['calibration_factor']
                noise = (hash(str(time.time())) % 10) - 5  # ±5 noise
                reading = {
                    'weight_grams': weight,
                    'raw_value': raw_value + noise,
                    'calibrated_value': weight,
                    'timestamp': time.time()
                }
                readings.append(reading)
                time.sleep(0.2)
            
            return {
                'success': True,
                'sensor_type': 'load_cell',
                'readings': readings,
                'pin': sensor_info['pin'],
                'calibration_factor': sensor_info['calibration_factor'],
                'message': f'{sensor_name} test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'{sensor_name} test failed'
            }
    
    def _test_ultrasonic_sensor(self, sensor_name: str, sensor_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test ultrasonic proximity sensor"""
        try:
            # Mock ultrasonic sensor test
            # In real implementation, this would use ultrasonic library
            
            # Simulate distance readings
            test_distances = [10, 25, 50, 100, 150, 200]  # cm
            readings = []
            
            for distance in test_distances:
                # Simulate reading with some noise
                noise = (hash(str(time.time())) % 5) - 2  # ±2cm noise
                reading = {
                    'distance_cm': distance,
                    'raw_value': distance + noise,
                    'max_range': sensor_info['max_range'],
                    'in_range': distance <= sensor_info['max_range'],
                    'timestamp': time.time()
                }
                readings.append(reading)
                time.sleep(0.1)
            
            return {
                'success': True,
                'sensor_type': 'ultrasonic',
                'readings': readings,
                'pin': sensor_info['pin'],
                'max_range': sensor_info['max_range'],
                'message': f'{sensor_name} test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'{sensor_name} test failed'
            }
    
    def _test_temperature_sensor(self, sensor_name: str, sensor_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test temperature sensor"""
        try:
            # Mock temperature sensor test
            # In real implementation, this would read from DS18B20
            
            # Simulate temperature readings
            test_temperatures = [20.0, 25.5, 30.0, 35.2, 40.0]  # Celsius
            readings = []
            
            for temp in test_temperatures:
                # Simulate reading with some noise
                noise = (hash(str(time.time())) % 20) / 10 - 1  # ±1°C noise
                reading = {
                    'temperature_celsius': temp,
                    'raw_value': temp + noise,
                    'resolution': sensor_info['resolution'],
                    'timestamp': time.time()
                }
                readings.append(reading)
                time.sleep(0.1)
            
            return {
                'success': True,
                'sensor_type': 'ds18b20',
                'readings': readings,
                'pin': sensor_info['pin'],
                'resolution': sensor_info['resolution'],
                'message': f'{sensor_name} test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'{sensor_name} test failed'
            }
    
    def _test_humidity_sensor(self, sensor_name: str, sensor_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test humidity sensor"""
        try:
            # Mock humidity sensor test
            # In real implementation, this would read from DHT22
            
            # Simulate humidity readings
            test_humidities = [30.0, 45.5, 60.0, 75.2, 90.0]  # Percentage
            readings = []
            
            for humidity in test_humidities:
                # Simulate reading with some noise
                noise = (hash(str(time.time())) % 20) / 10 - 1  # ±1% noise
                reading = {
                    'humidity_percent': humidity,
                    'raw_value': humidity + noise,
                    'accuracy': sensor_info['accuracy'],
                    'timestamp': time.time()
                }
                readings.append(reading)
                time.sleep(0.1)
            
            return {
                'success': True,
                'sensor_type': 'dht22',
                'readings': readings,
                'pin': sensor_info['pin'],
                'accuracy': sensor_info['accuracy'],
                'message': f'{sensor_name} test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'{sensor_name} test failed'
            }
    
    def _test_sensor_integration(self) -> Dict[str, Any]:
        """Test sensor integration and communication"""
        try:
            # Mock integration test
            # Test sensor data collection and processing
            
            integration_tests = {
                'data_collection': True,
                'data_processing': True,
                'threshold_detection': True,
                'calibration_application': True,
                'error_handling': True
            }
            
            return {
                'success': all(integration_tests.values()),
                'tests': integration_tests,
                'message': 'Sensor integration test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Sensor integration test failed'
            }
    
    def calibrate_sensors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calibrate sensors"""
        logger.info("Calibrating sensors...")
        
        try:
            calibration_results = {}
            
            # Calibrate sampling rate
            if 'sampling_rate' in params:
                sampling_rate = max(0.1, min(10.0, params['sampling_rate']))
                self.sensor_settings['sampling_rate'] = sampling_rate
                calibration_results['sampling_rate'] = {
                    'value': sampling_rate,
                    'success': True
                }
            
            # Calibrate threshold sensitivity
            if 'threshold_sensitivity' in params:
                sensitivity = max(0.01, min(1.0, params['threshold_sensitivity']))
                self.sensor_settings['threshold_sensitivity'] = sensitivity
                calibration_results['threshold_sensitivity'] = {
                    'value': sensitivity,
                    'success': True
                }
            
            # Calibrate individual sensors
            for sensor_name, sensor_params in params.get('sensors', {}).items():
                if sensor_name in self.sensors:
                    sensor_result = self._calibrate_single_sensor(sensor_name, sensor_params)
                    calibration_results[sensor_name] = sensor_result
            
            # Test calibrated settings
            test_result = self._test_calibrated_settings()
            calibration_results['test'] = test_result
            
            # Store calibration data
            self.calibration_data = {
                'settings': self.sensor_settings.copy(),
                'calibration_params': params,
                'results': calibration_results,
                'timestamp': time.time()
            }
            
            return {
                'success': True,
                'message': 'Sensor calibration completed successfully',
                'data': calibration_results
            }
            
        except Exception as e:
            logger.error(f"Sensor calibration failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Sensor calibration failed'
            }
    
    def _calibrate_single_sensor(self, sensor_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calibrate single sensor"""
        try:
            sensor_info = self.sensors[sensor_name]
            calibration_result = {}
            
            # Update sensor parameters
            for param, value in params.items():
                if param in sensor_info:
                    sensor_info[param] = value
                    calibration_result[param] = {
                        'value': value,
                        'success': True
                    }
            
            return {
                'success': True,
                'sensor_name': sensor_name,
                'calibration': calibration_result,
                'message': f'{sensor_name} calibration completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'{sensor_name} calibration failed'
            }
    
    def _test_calibrated_settings(self) -> Dict[str, Any]:
        """Test calibrated sensor settings"""
        try:
            # Test with calibrated settings
            test_readings = {}
            
            for sensor_name in self.sensors.keys():
                # Simulate reading with calibrated settings
                test_readings[sensor_name] = {
                    'value': 50.0,  # Mock value
                    'calibrated': True,
                    'timestamp': time.time()
                }
            
            return {
                'success': True,
                'test_readings': test_readings,
                'settings': self.sensor_settings.copy(),
                'message': 'Calibrated settings test completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Calibrated settings test failed'
            }
    
    def get_sensor_data(self, sensor_name: Optional[str] = None) -> Dict[str, Any]:
        """Get sensor data"""
        try:
            if sensor_name:
                if sensor_name not in self.sensors:
                    return {
                        'success': False,
                        'error': f'Sensor {sensor_name} not found',
                        'message': 'Invalid sensor name'
                    }
                
                # Get data for specific sensor
                sensor_info = self.sensors[sensor_name]
                data = self._read_sensor_data(sensor_name, sensor_info)
                
                return {
                    'success': True,
                    'data': {
                        'sensor_name': sensor_name,
                        'sensor_info': sensor_info,
                        'reading': data
                    }
                }
            else:
                # Get data for all sensors
                all_data = {}
                for name, info in self.sensors.items():
                    all_data[name] = self._read_sensor_data(name, info)
                
                return {
                    'success': True,
                    'data': all_data
                }
                
        except Exception as e:
            logger.error(f"Get sensor data failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Get sensor data failed'
            }
    
    def _read_sensor_data(self, sensor_name: str, sensor_info: Dict[str, Any]) -> Dict[str, Any]:
        """Read data from specific sensor"""
        # Mock sensor reading
        # In real implementation, this would read actual sensor data
        
        sensor_type = sensor_info['type']
        timestamp = time.time()
        
        if sensor_type == 'magnetic':
            return {
                'state': 'closed',
                'value': 0,
                'timestamp': timestamp
            }
        elif sensor_type == 'load_cell':
            return {
                'weight_grams': 0,
                'raw_value': 0,
                'timestamp': timestamp
            }
        elif sensor_type == 'ultrasonic':
            return {
                'distance_cm': 100,
                'in_range': True,
                'timestamp': timestamp
            }
        elif sensor_type == 'ds18b20':
            return {
                'temperature_celsius': 25.0,
                'timestamp': timestamp
            }
        elif sensor_type == 'dht22':
            return {
                'humidity_percent': 50.0,
                'temperature_celsius': 25.0,
                'timestamp': timestamp
            }
        else:
            return {
                'value': 0,
                'timestamp': timestamp
            }
    
    def get_sensor_status(self) -> Dict[str, Any]:
        """Get sensor status"""
        try:
            return {
                'success': True,
                'data': {
                    'sensors': self.sensors.copy(),
                    'settings': self.sensor_settings.copy(),
                    'calibration_data': self.calibration_data
                }
            }
            
        except Exception as e:
            logger.error(f"Get sensor status failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Get sensor status failed'
            }
    
    def reset_sensors(self) -> Dict[str, Any]:
        """Reset sensors to default settings"""
        try:
            # Reset settings to defaults
            self.sensor_settings.update({
                'sampling_rate': 1.0,
                'calibration_enabled': True,
                'threshold_sensitivity': 0.1
            })
            
            # Clear calibration data
            self.calibration_data = {}
            
            return {
                'success': True,
                'message': 'Sensors reset to default settings',
                'data': self.sensor_settings.copy()
            }
            
        except Exception as e:
            logger.error(f"Reset sensors failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Reset sensors failed'
            }





