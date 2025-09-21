# TASK 03: HARDWARE CALIBRATION MODULE

**Tanggal**: 2025-09-21  
**Versi**: 1.0.0  
**Status**: 📋 PLANNING  
**Priority**: HIGH  

---

## **🎯 OBJECTIVE**

Membuat Hardware Calibration Module untuk testing dan kalibrasi semua komponen hardware RVM-Jetson melalui Web Configuration Interface.

---

## **📋 REQUIREMENTS**

### **Functional Requirements:**
- **Camera Testing & Calibration** (resolution, focus, color, exposure)
- **Motor Stepper Testing** (forward/backward, speed, steps, torque)
- **LED/Lamp Testing** (brightness, color, patterns, blinking)
- **Touch Screen Calibration** (touch response, multi-touch, gestures)
- **GPIO Testing** (input/output, voltage, current)
- **Sensor Testing** (door sensors, weight sensors, proximity)
- **Audio Testing** (speaker, microphone, volume)

### **Technical Requirements:**
- **Real-time Testing** dengan live feedback
- **Calibration Data Storage** dan retrieval
- **Hardware Status Monitoring** dan reporting
- **Error Detection** dan troubleshooting
- **Performance Metrics** collection
- **Calibration Profiles** management

---

## **🔧 IMPLEMENTATION PLAN**

### **1. Hardware Calibration Module Structure**
```
hardware_calibration/
├── __init__.py
├── camera_calibration.py      # Camera testing & calibration
├── motor_calibration.py       # Motor stepper testing
├── led_calibration.py         # LED/Lamp testing
├── touch_calibration.py       # Touch screen calibration
├── gpio_calibration.py        # GPIO testing
├── sensor_calibration.py      # Sensor testing
├── audio_calibration.py       # Audio testing
├── calibration_manager.py     # Main calibration manager
├── calibration_storage.py     # Calibration data storage
└── utils/
    ├── hardware_detector.py
    ├── performance_monitor.py
    └── error_handler.py
```

### **2. Core Features Implementation**

#### **A. Camera Calibration**
```python
class CameraCalibration:
    def test_camera_detection(self):
        # Test camera device detection
        
    def test_resolution(self):
        # Test different resolutions
        
    def test_focus(self):
        # Test focus adjustment
        
    def test_color_balance(self):
        # Test color balance
        
    def test_exposure(self):
        # Test exposure settings
        
    def calibrate_camera(self):
        # Full camera calibration
```

#### **B. Motor Stepper Calibration**
```python
class MotorCalibration:
    def test_motor_detection(self):
        # Test motor GPIO detection
        
    def test_forward_movement(self):
        # Test forward movement
        
    def test_backward_movement(self):
        # Test backward movement
        
    def test_speed_control(self):
        # Test speed control
        
    def test_step_accuracy(self):
        # Test step accuracy
        
    def calibrate_motor(self):
        # Full motor calibration
```

#### **C. LED/Lamp Calibration**
```python
class LEDCalibration:
    def test_led_detection(self):
        # Test LED GPIO detection
        
    def test_brightness(self):
        # Test brightness levels
        
    def test_color_control(self):
        # Test color control (RGB)
        
    def test_patterns(self):
        # Test LED patterns
        
    def test_blinking(self):
        # Test blinking frequency
        
    def calibrate_led(self):
        # Full LED calibration
```

#### **D. Touch Screen Calibration**
```python
class TouchCalibration:
    def test_touch_detection(self):
        # Test touch device detection
        
    def test_touch_response(self):
        # Test touch response time
        
    def test_multi_touch(self):
        # Test multi-touch capability
        
    def test_gestures(self):
        # Test gesture recognition
        
    def calibrate_touch(self):
        # Full touch calibration
```

---

## **📝 DETAILED IMPLEMENTATION**

### **1. Camera Calibration Module**

#### **Camera Testing & Calibration:**
```python
import cv2
import numpy as np
import time
import json
from typing import Dict, List, Tuple, Optional

class CameraCalibration:
    def __init__(self):
        self.camera = None
        self.calibration_data = {}
        self.test_results = {}
        
    def initialize_camera(self, device_id: int = 0) -> bool:
        """Initialize camera device"""
        try:
            self.camera = cv2.VideoCapture(device_id)
            if not self.camera.isOpened():
                return False
            
            # Set default properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            return True
        except Exception as e:
            print(f"Error initializing camera: {e}")
            return False
    
    def test_camera_detection(self) -> Dict:
        """Test camera device detection"""
        results = {
            'detected': False,
            'device_id': None,
            'device_name': None,
            'capabilities': {},
            'error': None
        }
        
        try:
            # Test multiple camera devices
            for device_id in range(5):  # Test first 5 devices
                cap = cv2.VideoCapture(device_id)
                if cap.isOpened():
                    results['detected'] = True
                    results['device_id'] = device_id
                    results['device_name'] = f"Camera {device_id}"
                    
                    # Get camera capabilities
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    results['capabilities'] = {
                        'max_width': width,
                        'max_height': height,
                        'fps': fps
                    }
                    
                    cap.release()
                    break
                cap.release()
                
        except Exception as e:
            results['error'] = str(e)
            
        return results
    
    def test_resolution(self, resolutions: List[Tuple[int, int]] = None) -> Dict:
        """Test different resolutions"""
        if resolutions is None:
            resolutions = [
                (640, 480),   # VGA
                (1280, 720),  # HD
                (1920, 1080), # Full HD
                (2560, 1440), # 2K
                (3840, 2160)  # 4K
            ]
        
        results = {
            'supported_resolutions': [],
            'failed_resolutions': [],
            'recommended_resolution': None
        }
        
        if not self.camera:
            if not self.initialize_camera():
                results['error'] = 'Camera not available'
                return results
        
        for width, height in resolutions:
            try:
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # Test if resolution is actually set
                actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                if actual_width == width and actual_height == height:
                    # Test if we can capture a frame
                    ret, frame = self.camera.read()
                    if ret and frame is not None:
                        results['supported_resolutions'].append({
                            'width': width,
                            'height': height,
                            'aspect_ratio': width / height
                        })
                    else:
                        results['failed_resolutions'].append({
                            'width': width,
                            'height': height,
                            'reason': 'Cannot capture frame'
                        })
                else:
                    results['failed_resolutions'].append({
                        'width': width,
                        'height': height,
                        'reason': f'Resolution not supported (got {actual_width}x{actual_height})'
                    })
                    
            except Exception as e:
                results['failed_resolutions'].append({
                    'width': width,
                    'height': height,
                    'reason': str(e)
                })
        
        # Recommend best resolution
        if results['supported_resolutions']:
            # Prefer Full HD if available
            for res in results['supported_resolutions']:
                if res['width'] == 1920 and res['height'] == 1080:
                    results['recommended_resolution'] = res
                    break
            
            # If Full HD not available, use the highest resolution
            if not results['recommended_resolution']:
                results['recommended_resolution'] = max(
                    results['supported_resolutions'],
                    key=lambda x: x['width'] * x['height']
                )
        
        return results
    
    def test_focus(self) -> Dict:
        """Test focus adjustment"""
        results = {
            'auto_focus_available': False,
            'manual_focus_available': False,
            'focus_range': None,
            'current_focus': None,
            'test_images': []
        }
        
        if not self.camera:
            if not self.initialize_camera():
                results['error'] = 'Camera not available'
                return results
        
        try:
            # Test auto focus
            self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            auto_focus = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)
            results['auto_focus_available'] = auto_focus > 0
            
            # Test manual focus
            self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            manual_focus = self.camera.get(cv2.CAP_PROP_AUTOFOCUS)
            results['manual_focus_available'] = manual_focus == 0
            
            # Get focus range
            focus_min = self.camera.get(cv2.CAP_PROP_FOCUS)
            results['current_focus'] = focus_min
            
            # Test focus at different levels
            focus_levels = [0, 25, 50, 75, 100]
            for level in focus_levels:
                self.camera.set(cv2.CAP_PROP_FOCUS, level)
                ret, frame = self.camera.read()
                if ret:
                    # Calculate focus quality (using Laplacian variance)
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    focus_quality = cv2.Laplacian(gray, cv2.CV_64F).var()
                    
                    results['test_images'].append({
                        'focus_level': level,
                        'focus_quality': focus_quality,
                        'image_size': frame.shape
                    })
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def test_color_balance(self) -> Dict:
        """Test color balance and white balance"""
        results = {
            'white_balance_available': False,
            'color_temperature_range': None,
            'color_accuracy': {},
            'test_results': []
        }
        
        if not self.camera:
            if not self.initialize_camera():
                results['error'] = 'Camera not available'
                return results
        
        try:
            # Test white balance
            self.camera.set(cv2.CAP_PROP_AUTO_WB, 0)
            wb_available = self.camera.get(cv2.CAP_PROP_AUTO_WB)
            results['white_balance_available'] = wb_available >= 0
            
            # Test different color temperatures
            color_temps = [2800, 3200, 4000, 5000, 6500, 8000]  # Kelvin
            for temp in color_temps:
                self.camera.set(cv2.CAP_PROP_WB_TEMPERATURE, temp)
                ret, frame = self.camera.read()
                if ret:
                    # Analyze color distribution
                    b, g, r = cv2.split(frame)
                    color_stats = {
                        'temperature': temp,
                        'mean_b': float(np.mean(b)),
                        'mean_g': float(np.mean(g)),
                        'mean_r': float(np.mean(r)),
                        'std_b': float(np.std(b)),
                        'std_g': float(np.std(g)),
                        'std_r': float(np.std(r))
                    }
                    results['test_results'].append(color_stats)
            
            # Test color accuracy with known colors
            color_targets = [
                {'name': 'red', 'bgr': (0, 0, 255)},
                {'name': 'green', 'bgr': (0, 255, 0)},
                {'name': 'blue', 'bgr': (255, 0, 0)},
                {'name': 'white', 'bgr': (255, 255, 255)},
                {'name': 'black', 'bgr': (0, 0, 0)}
            ]
            
            for target in color_targets:
                ret, frame = self.camera.read()
                if ret:
                    # Find the target color in the image
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    target_hsv = cv2.cvtColor(np.uint8([[target['bgr']]]), cv2.COLOR_BGR2HSV)[0][0]
                    
                    # Create mask for the color
                    lower = np.array([target_hsv[0] - 10, 50, 50])
                    upper = np.array([target_hsv[0] + 10, 255, 255])
                    mask = cv2.inRange(hsv, lower, upper)
                    
                    # Calculate color accuracy
                    accuracy = np.sum(mask > 0) / (frame.shape[0] * frame.shape[1])
                    results['color_accuracy'][target['name']] = float(accuracy)
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def test_exposure(self) -> Dict:
        """Test exposure settings"""
        results = {
            'auto_exposure_available': False,
            'manual_exposure_available': False,
            'exposure_range': None,
            'test_results': []
        }
        
        if not self.camera:
            if not self.initialize_camera():
                results['error'] = 'Camera not available'
                return results
        
        try:
            # Test auto exposure
            self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
            auto_exposure = self.camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            results['auto_exposure_available'] = auto_exposure > 0
            
            # Test manual exposure
            self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
            manual_exposure = self.camera.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            results['manual_exposure_available'] = manual_exposure == 0
            
            # Test different exposure values
            exposure_values = [-10, -5, 0, 5, 10]  # EV values
            for ev in exposure_values:
                self.camera.set(cv2.CAP_PROP_EXPOSURE, ev)
                ret, frame = self.camera.read()
                if ret:
                    # Calculate brightness
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    brightness = np.mean(gray)
                    
                    results['test_results'].append({
                        'exposure_value': ev,
                        'brightness': float(brightness),
                        'image_size': frame.shape
                    })
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def calibrate_camera(self) -> Dict:
        """Perform full camera calibration"""
        calibration_results = {
            'detection': {},
            'resolution': {},
            'focus': {},
            'color_balance': {},
            'exposure': {},
            'overall_score': 0,
            'recommendations': [],
            'calibration_data': {}
        }
        
        try:
            # Run all tests
            calibration_results['detection'] = self.test_camera_detection()
            calibration_results['resolution'] = self.test_resolution()
            calibration_results['focus'] = self.test_focus()
            calibration_results['color_balance'] = self.test_color_balance()
            calibration_results['exposure'] = self.test_exposure()
            
            # Calculate overall score
            scores = []
            if calibration_results['detection']['detected']:
                scores.append(100)
            if calibration_results['resolution']['supported_resolutions']:
                scores.append(len(calibration_results['resolution']['supported_resolutions']) * 20)
            if calibration_results['focus']['auto_focus_available'] or calibration_results['focus']['manual_focus_available']:
                scores.append(80)
            if calibration_results['color_balance']['white_balance_available']:
                scores.append(70)
            if calibration_results['exposure']['auto_exposure_available'] or calibration_results['exposure']['manual_exposure_available']:
                scores.append(70)
            
            calibration_results['overall_score'] = sum(scores) / len(scores) if scores else 0
            
            # Generate recommendations
            if calibration_results['overall_score'] < 70:
                calibration_results['recommendations'].append('Camera calibration failed. Check hardware connections.')
            if not calibration_results['detection']['detected']:
                calibration_results['recommendations'].append('Camera not detected. Check USB connection.')
            if not calibration_results['resolution']['supported_resolutions']:
                calibration_results['recommendations'].append('No supported resolutions found.')
            if calibration_results['overall_score'] >= 90:
                calibration_results['recommendations'].append('Camera calibration successful. Ready for production.')
            
            # Store calibration data
            self.calibration_data = calibration_results
            self.save_calibration_data()
            
        except Exception as e:
            calibration_results['error'] = str(e)
            calibration_results['recommendations'].append(f'Calibration error: {str(e)}')
        
        return calibration_results
    
    def save_calibration_data(self):
        """Save calibration data to file"""
        try:
            with open('/tmp/camera_calibration.json', 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
        except Exception as e:
            print(f"Error saving calibration data: {e}")
    
    def load_calibration_data(self) -> Dict:
        """Load calibration data from file"""
        try:
            with open('/tmp/camera_calibration.json', 'r') as f:
                self.calibration_data = json.load(f)
                return self.calibration_data
        except Exception as e:
            print(f"Error loading calibration data: {e}")
            return {}
    
    def cleanup(self):
        """Cleanup camera resources"""
        if self.camera:
            self.camera.release()
            self.camera = None
```

### **2. Motor Stepper Calibration Module**

#### **Motor Testing & Calibration:**
```python
import RPi.GPIO as GPIO
import time
import json
from typing import Dict, List, Optional

class MotorCalibration:
    def __init__(self):
        self.gpio_pins = {
            'step': 18,
            'dir': 19,
            'enable': 20
        }
        self.motor_config = {
            'steps_per_revolution': 200,
            'microsteps': 16,
            'max_speed': 1000,  # steps per second
            'acceleration': 500  # steps per second squared
        }
        self.calibration_data = {}
        self.test_results = {}
        
    def initialize_gpio(self) -> bool:
        """Initialize GPIO pins for motor control"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pins['step'], GPIO.OUT)
            GPIO.setup(self.gpio_pins['dir'], GPIO.OUT)
            GPIO.setup(self.gpio_pins['enable'], GPIO.OUT)
            
            # Set initial states
            GPIO.output(self.gpio_pins['enable'], GPIO.LOW)  # Enable motor
            GPIO.output(self.gpio_pins['dir'], GPIO.LOW)     # Set direction
            GPIO.output(self.gpio_pins['step'], GPIO.LOW)    # Set step pin low
            
            return True
        except Exception as e:
            print(f"Error initializing GPIO: {e}")
            return False
    
    def test_motor_detection(self) -> Dict:
        """Test motor GPIO detection"""
        results = {
            'gpio_available': False,
            'pins_configured': False,
            'motor_responsive': False,
            'error': None
        }
        
        try:
            # Test GPIO availability
            results['gpio_available'] = True
            
            # Test pin configuration
            if self.initialize_gpio():
                results['pins_configured'] = True
                
                # Test motor responsiveness
                self.test_single_step()
                results['motor_responsive'] = True
                
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def test_single_step(self) -> bool:
        """Test single step movement"""
        try:
            # Send single step pulse
            GPIO.output(self.gpio_pins['step'], GPIO.HIGH)
            time.sleep(0.001)  # 1ms pulse
            GPIO.output(self.gpio_pins['step'], GPIO.LOW)
            time.sleep(0.001)  # 1ms delay
            
            return True
        except Exception as e:
            print(f"Error in single step: {e}")
            return False
    
    def test_forward_movement(self, steps: int = 100) -> Dict:
        """Test forward movement"""
        results = {
            'success': False,
            'steps_completed': 0,
            'time_taken': 0,
            'average_speed': 0,
            'error': None
        }
        
        try:
            if not self.initialize_gpio():
                results['error'] = 'GPIO initialization failed'
                return results
            
            # Set direction to forward
            GPIO.output(self.gpio_pins['dir'], GPIO.LOW)
            time.sleep(0.001)
            
            start_time = time.time()
            
            for i in range(steps):
                GPIO.output(self.gpio_pins['step'], GPIO.HIGH)
                time.sleep(0.001)
                GPIO.output(self.gpio_pins['step'], GPIO.LOW)
                time.sleep(0.001)
            
            end_time = time.time()
            
            results['success'] = True
            results['steps_completed'] = steps
            results['time_taken'] = end_time - start_time
            results['average_speed'] = steps / (end_time - start_time)
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def test_backward_movement(self, steps: int = 100) -> Dict:
        """Test backward movement"""
        results = {
            'success': False,
            'steps_completed': 0,
            'time_taken': 0,
            'average_speed': 0,
            'error': None
        }
        
        try:
            if not self.initialize_gpio():
                results['error'] = 'GPIO initialization failed'
                return results
            
            # Set direction to backward
            GPIO.output(self.gpio_pins['dir'], GPIO.HIGH)
            time.sleep(0.001)
            
            start_time = time.time()
            
            for i in range(steps):
                GPIO.output(self.gpio_pins['step'], GPIO.HIGH)
                time.sleep(0.001)
                GPIO.output(self.gpio_pins['step'], GPIO.LOW)
                time.sleep(0.001)
            
            end_time = time.time()
            
            results['success'] = True
            results['steps_completed'] = steps
            results['time_taken'] = end_time - start_time
            results['average_speed'] = steps / (end_time - start_time)
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def test_speed_control(self, speeds: List[int] = None) -> Dict:
        """Test speed control at different speeds"""
        if speeds is None:
            speeds = [100, 200, 500, 1000, 2000]  # steps per second
        
        results = {
            'tested_speeds': [],
            'max_speed': 0,
            'min_speed': 0,
            'speed_accuracy': {}
        }
        
        try:
            if not self.initialize_gpio():
                results['error'] = 'GPIO initialization failed'
                return results
            
            for target_speed in speeds:
                step_delay = 1.0 / target_speed  # seconds per step
                
                start_time = time.time()
                steps_completed = 0
                
                # Run for 1 second
                while time.time() - start_time < 1.0:
                    GPIO.output(self.gpio_pins['step'], GPIO.HIGH)
                    time.sleep(step_delay / 2)
                    GPIO.output(self.gpio_pins['step'], GPIO.LOW)
                    time.sleep(step_delay / 2)
                    steps_completed += 1
                
                actual_speed = steps_completed / (time.time() - start_time)
                speed_accuracy = (actual_speed / target_speed) * 100
                
                results['tested_speeds'].append({
                    'target_speed': target_speed,
                    'actual_speed': actual_speed,
                    'accuracy': speed_accuracy
                })
                
                results['speed_accuracy'][target_speed] = speed_accuracy
            
            # Calculate max and min speeds
            if results['tested_speeds']:
                results['max_speed'] = max(results['tested_speeds'], key=lambda x: x['actual_speed'])['actual_speed']
                results['min_speed'] = min(results['tested_speeds'], key=lambda x: x['actual_speed'])['actual_speed']
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def test_step_accuracy(self, test_cycles: int = 10) -> Dict:
        """Test step accuracy over multiple cycles"""
        results = {
            'cycles_completed': 0,
            'accuracy_scores': [],
            'average_accuracy': 0,
            'consistency': 0,
            'error': None
        }
        
        try:
            if not self.initialize_gpio():
                results['error'] = 'GPIO initialization failed'
                return results
            
            steps_per_cycle = 200  # One full revolution
            accuracy_scores = []
            
            for cycle in range(test_cycles):
                # Move forward
                GPIO.output(self.gpio_pins['dir'], GPIO.LOW)
                start_time = time.time()
                
                for step in range(steps_per_cycle):
                    GPIO.output(self.gpio_pins['step'], GPIO.HIGH)
                    time.sleep(0.001)
                    GPIO.output(self.gpio_pins['step'], GPIO.LOW)
                    time.sleep(0.001)
                
                forward_time = time.time() - start_time
                
                # Move backward
                GPIO.output(self.gpio_pins['dir'], GPIO.HIGH)
                start_time = time.time()
                
                for step in range(steps_per_cycle):
                    GPIO.output(self.gpio_pins['step'], GPIO.HIGH)
                    time.sleep(0.001)
                    GPIO.output(self.gpio_pins['step'], GPIO.LOW)
                    time.sleep(0.001)
                
                backward_time = time.time() - start_time
                
                # Calculate accuracy (time consistency)
                time_accuracy = 100 - abs(forward_time - backward_time) / max(forward_time, backward_time) * 100
                accuracy_scores.append(time_accuracy)
            
            results['cycles_completed'] = test_cycles
            results['accuracy_scores'] = accuracy_scores
            results['average_accuracy'] = sum(accuracy_scores) / len(accuracy_scores)
            results['consistency'] = 100 - (max(accuracy_scores) - min(accuracy_scores))
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def calibrate_motor(self) -> Dict:
        """Perform full motor calibration"""
        calibration_results = {
            'detection': {},
            'forward_movement': {},
            'backward_movement': {},
            'speed_control': {},
            'step_accuracy': {},
            'overall_score': 0,
            'recommendations': [],
            'calibration_data': {}
        }
        
        try:
            # Run all tests
            calibration_results['detection'] = self.test_motor_detection()
            calibration_results['forward_movement'] = self.test_forward_movement()
            calibration_results['backward_movement'] = self.test_backward_movement()
            calibration_results['speed_control'] = self.test_speed_control()
            calibration_results['step_accuracy'] = self.test_step_accuracy()
            
            # Calculate overall score
            scores = []
            if calibration_results['detection']['motor_responsive']:
                scores.append(100)
            if calibration_results['forward_movement']['success']:
                scores.append(90)
            if calibration_results['backward_movement']['success']:
                scores.append(90)
            if calibration_results['speed_control']['tested_speeds']:
                scores.append(80)
            if calibration_results['step_accuracy']['average_accuracy'] > 95:
                scores.append(85)
            
            calibration_results['overall_score'] = sum(scores) / len(scores) if scores else 0
            
            # Generate recommendations
            if calibration_results['overall_score'] < 70:
                calibration_results['recommendations'].append('Motor calibration failed. Check hardware connections.')
            if not calibration_results['detection']['motor_responsive']:
                calibration_results['recommendations'].append('Motor not responsive. Check power and connections.')
            if calibration_results['step_accuracy']['average_accuracy'] < 90:
                calibration_results['recommendations'].append('Step accuracy low. Check motor driver settings.')
            if calibration_results['overall_score'] >= 90:
                calibration_results['recommendations'].append('Motor calibration successful. Ready for production.')
            
            # Store calibration data
            self.calibration_data = calibration_results
            self.save_calibration_data()
            
        except Exception as e:
            calibration_results['error'] = str(e)
            calibration_results['recommendations'].append(f'Calibration error: {str(e)}')
        
        return calibration_results
    
    def save_calibration_data(self):
        """Save calibration data to file"""
        try:
            with open('/tmp/motor_calibration.json', 'w') as f:
                json.dump(self.calibration_data, f, indent=2)
        except Exception as e:
            print(f"Error saving calibration data: {e}")
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"Error cleaning up GPIO: {e}")
```

---

## **🧪 TESTING STRATEGY**

### **Unit Testing:**
- **Hardware detection** testing
- **Calibration functions** testing
- **Error handling** testing
- **Performance metrics** testing

### **Integration Testing:**
- **Hardware integration** testing
- **Web interface** integration
- **Data storage** testing
- **Real-time feedback** testing

### **Hardware Testing:**
- **Camera functionality** testing
- **Motor movement** testing
- **LED control** testing
- **Touch response** testing

---

## **📊 SUCCESS CRITERIA**

### **Functional Success:**
- ✅ Camera testing & calibration
- ✅ Motor stepper testing
- ✅ LED/Lamp testing
- ✅ Touch screen calibration
- ✅ GPIO testing
- ✅ Sensor testing
- ✅ Audio testing

### **Technical Success:**
- ✅ Real-time testing
- ✅ Calibration data storage
- ✅ Hardware status monitoring
- ✅ Error detection
- ✅ Performance metrics
- ✅ Calibration profiles

### **Integration Success:**
- ✅ Web interface integration
- ✅ Hardware detection integration
- ✅ Data persistence
- ✅ Real-time feedback

---

## **⏱️ ESTIMATED TIMELINE**

### **Week 1: Core Modules**
- **Day 1-2**: Camera calibration module
- **Day 3-4**: Motor calibration module
- **Day 5**: LED calibration module

### **Week 2: Advanced Modules**
- **Day 1-2**: Touch screen calibration
- **Day 3-4**: GPIO testing
- **Day 5**: Sensor testing

### **Week 3: Integration & Testing**
- **Day 1-2**: Audio testing
- **Day 3-4**: Calibration manager
- **Day 5**: Integration testing

### **Week 4: Documentation & Deployment**
- **Day 1-2**: Documentation
- **Day 3-4**: Testing
- **Day 5**: Deployment

---

## **📁 DELIVERABLES**

### **Code Files:**
- `camera_calibration.py`
- `motor_calibration.py`
- `led_calibration.py`
- `touch_calibration.py`
- `gpio_calibration.py`
- `sensor_calibration.py`
- `audio_calibration.py`
- `calibration_manager.py`

### **Documentation:**
- API documentation
- Hardware compatibility guide
- Calibration procedures
- Troubleshooting guide

### **Testing:**
- Unit tests
- Integration tests
- Hardware tests
- Performance tests

---

**Status**: 📋 **READY FOR IMPLEMENTATION**  
**Estimated Time**: 4 weeks  
**Difficulty**: Advanced  
**Dependencies**: Hardware detection, GPIO libraries, OpenCV, Web interface
