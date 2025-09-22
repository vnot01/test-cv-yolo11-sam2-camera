"""
Hardware Calibration Module for RVM-Jetson
Provides testing and calibration for all hardware components
"""

__version__ = "1.0.0"
__author__ = "RVM-Jetson Team"

try:
    from .calibration_manager import CalibrationManager
    from .camera_calibration import CameraCalibration
    from .motor_calibration import MotorCalibration
    from .led_calibration import LEDCalibration
    from .touch_calibration import TouchCalibration
    from .gpio_calibration import GPIOCalibration
    from .sensor_calibration import SensorCalibration
    from .audio_calibration import AudioCalibration
except ImportError as e:
    print(f"Warning: Hardware calibration modules not available: {e}")
    # Create mock classes for non-Raspberry Pi systems
    class CalibrationManager:
        def __init__(self):
            pass
        def test_all_components(self):
            return {"success": True, "message": "Mock calibration manager"}
    
    class CameraCalibration:
        def test_camera(self):
            return {"success": True, "message": "Mock camera test"}
        def calibrate_camera(self, params):
            return {"success": True, "message": "Mock camera calibration"}
    
    class MotorCalibration:
        def test_motor(self):
            return {"success": True, "message": "Mock motor test"}
        def calibrate_motor(self, params):
            return {"success": True, "message": "Mock motor calibration"}
    
    class LEDCalibration:
        def test_led(self):
            return {"success": True, "message": "Mock LED test"}
        def calibrate_led(self, params):
            return {"success": True, "message": "Mock LED calibration"}
    
    class TouchCalibration:
        def test_touch_screen(self):
            return {"success": True, "message": "Mock touch test"}
        def calibrate_touch_screen(self, params):
            return {"success": True, "message": "Mock touch calibration"}
    
    class GPIOCalibration:
        def test_gpio(self):
            return {"success": True, "message": "Mock GPIO test"}
        def calibrate_gpio(self, params):
            return {"success": True, "message": "Mock GPIO calibration"}
    
    class SensorCalibration:
        def test_sensors(self):
            return {"success": True, "message": "Mock sensor test"}
        def calibrate_sensors(self, params):
            return {"success": True, "message": "Mock sensor calibration"}
    
    class AudioCalibration:
        def test_audio(self):
            return {"success": True, "message": "Mock audio test"}
        def calibrate_audio(self, params):
            return {"success": True, "message": "Mock audio calibration"}

__all__ = [
    'CalibrationManager',
    'CameraCalibration',
    'MotorCalibration',
    'LEDCalibration',
    'TouchCalibration',
    'GPIOCalibration',
    'SensorCalibration',
    'AudioCalibration'
]
