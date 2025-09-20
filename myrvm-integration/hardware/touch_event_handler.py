#!/usr/bin/env python3
"""
Touch Event Handler for LED Touch Screen
Handle touch events from LED Touch Screen hardware
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from evdev import InputDevice, categorize, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False

@dataclass
class TouchPoint:
    """Touch point data"""
    id: int
    x: float
    y: float
    pressure: float = 0.0
    timestamp: float = 0.0
    status: str = "down"  # down, move, up

@dataclass
class TouchEvent:
    """Touch event data"""
    event_type: str  # touch_down, touch_move, touch_up, gesture
    touch_points: List[TouchPoint]
    timestamp: float
    gesture_type: Optional[str] = None
    gesture_data: Optional[Dict] = None

class TouchEventHandler:
    """Handle touch events from LED Touch Screen"""
    
    def __init__(self, screen_interface=None):
        """
        Initialize Touch Event Handler
        
        Args:
            screen_interface: LED Touch Screen interface instance
        """
        self.screen_interface = screen_interface
        self.touch_callbacks = []
        self.gesture_callbacks = []
        self.touch_devices = []
        self.active_touch_points = {}
        self.touch_threads = []
        self.is_running = False
        self.calibration_data = {}
        
        # Touch configuration
        self.touch_config = {
            'min_pressure': 10,
            'max_pressure': 1000,
            'touch_timeout': 5.0,  # seconds
            'gesture_threshold': 50,  # pixels
            'multi_touch_enabled': True,
            'gesture_enabled': True
        }
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize touch devices
        self._initialize_touch_devices()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for touch event handler"""
        logger = logging.getLogger('TouchEventHandler')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        from datetime import datetime
        log_file = log_dir / f'touch_event_handler_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _initialize_touch_devices(self):
        """Initialize touch devices"""
        try:
            if not EVDEV_AVAILABLE:
                self.logger.warning("evdev library not available, using mock touch device")
                self._create_mock_touch_device()
                return
            
            # Find touch devices
            input_path = Path('/dev/input')
            if input_path.exists():
                for event_file in input_path.glob('event*'):
                    try:
                        device = InputDevice(str(event_file))
                        if self._is_touch_device(device):
                            self.touch_devices.append(device)
                            self.logger.info(f"Found touch device: {device.name} at {event_file}")
                    except Exception as e:
                        self.logger.debug(f"Failed to open device {event_file}: {e}")
            
            # If no touch devices found, create mock device
            if not self.touch_devices:
                self.logger.warning("No touch devices found, creating mock touch device")
                self._create_mock_touch_device()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize touch devices: {e}")
            self._create_mock_touch_device()
    
    def _is_touch_device(self, device: InputDevice) -> bool:
        """Check if device is a touch device"""
        try:
            # Check device capabilities
            capabilities = device.capabilities()
            
            # Check for touch-related capabilities
            if ecodes.EV_ABS in capabilities:
                abs_caps = capabilities[ecodes.EV_ABS]
                # Check for X and Y axes (typical for touch screens)
                if ecodes.ABS_X in abs_caps and ecodes.ABS_Y in abs_caps:
                    return True
            
            # Check device name
            device_name = device.name.lower()
            touch_keywords = ['touch', 'touchscreen', 'touchpad', 'digitizer']
            return any(keyword in device_name for keyword in touch_keywords)
            
        except Exception as e:
            self.logger.debug(f"Error checking device capabilities: {e}")
            return False
    
    def _create_mock_touch_device(self):
        """Create mock touch device for testing"""
        try:
            # Create mock device data
            mock_device = {
                'name': 'Mock Touch Device',
                'path': '/dev/input/mock_touch',
                'capabilities': {
                    'abs': [ecodes.ABS_X, ecodes.ABS_Y, ecodes.ABS_PRESSURE],
                    'key': [ecodes.BTN_TOUCH]
                }
            }
            
            self.touch_devices.append(mock_device)
            self.logger.info("Created mock touch device for testing")
            
        except Exception as e:
            self.logger.error(f"Failed to create mock touch device: {e}")
    
    def start_touch_handling(self):
        """Start touch event handling"""
        try:
            if self.is_running:
                self.logger.warning("Touch handling already running")
                return
            
            self.is_running = True
            self.logger.info("Starting touch event handling...")
            
            # Start touch handling threads for each device
            for device in self.touch_devices:
                if EVDEV_AVAILABLE and hasattr(device, 'read_loop'):
                    # Real device
                    thread = threading.Thread(
                        target=self._handle_device_events,
                        args=(device,),
                        daemon=True,
                        name=f"TouchThread-{device.name}"
                    )
                    thread.start()
                    self.touch_threads.append(thread)
                else:
                    # Mock device
                    thread = threading.Thread(
                        target=self._handle_mock_events,
                        args=(device,),
                        daemon=True,
                        name=f"MockTouchThread-{device.get('name', 'Mock')}"
                    )
                    thread.start()
                    self.touch_threads.append(thread)
            
            self.logger.info(f"Started touch handling for {len(self.touch_devices)} devices")
            
        except Exception as e:
            self.logger.error(f"Failed to start touch handling: {e}")
            self.is_running = False
    
    def stop_touch_handling(self):
        """Stop touch event handling"""
        try:
            self.logger.info("Stopping touch event handling...")
            self.is_running = False
            
            # Wait for threads to finish
            for thread in self.touch_threads:
                if thread.is_alive():
                    thread.join(timeout=1.0)
            
            self.touch_threads.clear()
            self.active_touch_points.clear()
            
            self.logger.info("Touch event handling stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping touch handling: {e}")
    
    def _handle_device_events(self, device: InputDevice):
        """Handle events from real touch device"""
        try:
            self.logger.info(f"Handling events from device: {device.name}")
            
            for event in device.read_loop():
                if not self.is_running:
                    break
                
                self._process_event(event, device)
                
        except Exception as e:
            self.logger.error(f"Error handling device events: {e}")
    
    def _handle_mock_events(self, device: Dict):
        """Handle mock touch events for testing"""
        try:
            self.logger.info(f"Handling mock events from device: {device.get('name', 'Mock')}")
            
            # Simulate touch events for testing
            import random
            
            while self.is_running:
                # Simulate random touch events
                if random.random() < 0.1:  # 10% chance per second
                    self._simulate_touch_event()
                
                time.sleep(0.1)  # 100ms interval
                
        except Exception as e:
            self.logger.error(f"Error handling mock events: {e}")
    
    def _simulate_touch_event(self):
        """Simulate touch event for testing"""
        try:
            import random
            
            # Simulate touch down
            touch_point = TouchPoint(
                id=random.randint(0, 9),
                x=random.uniform(0, 1920),
                y=random.uniform(0, 1080),
                pressure=random.uniform(100, 1000),
                timestamp=time.time(),
                status="down"
            )
            
            # Create touch event
            touch_event = TouchEvent(
                event_type="touch_down",
                touch_points=[touch_point],
                timestamp=time.time()
            )
            
            # Process the event
            self._process_touch_event(touch_event)
            
            # Simulate touch up after short delay
            time.sleep(0.1)
            touch_point.status = "up"
            touch_event.event_type = "touch_up"
            self._process_touch_event(touch_event)
            
        except Exception as e:
            self.logger.error(f"Error simulating touch event: {e}")
    
    def _process_event(self, event, device: InputDevice):
        """Process input event"""
        try:
            if event.type == ecodes.EV_ABS:
                # Absolute position event
                if event.code == ecodes.ABS_X:
                    self._update_touch_point(event.value, 'x')
                elif event.code == ecodes.ABS_Y:
                    self._update_touch_point(event.value, 'y')
                elif event.code == ecodes.ABS_PRESSURE:
                    self._update_touch_point(event.value, 'pressure')
                elif event.code == ecodes.ABS_MT_TRACKING_ID:
                    if event.value >= 0:
                        self._start_touch_point(event.value)
                    else:
                        self._end_touch_point(event.value)
            
            elif event.type == ecodes.EV_KEY:
                # Key event
                if event.code == ecodes.BTN_TOUCH:
                    if event.value == 1:
                        self._handle_touch_down()
                    else:
                        self._handle_touch_up()
                        
        except Exception as e:
            self.logger.error(f"Error processing event: {e}")
    
    def _update_touch_point(self, value: int, axis: str):
        """Update touch point data"""
        try:
            # Apply calibration if available
            if axis in self.calibration_data:
                value = self._apply_calibration(value, axis)
            
            # Update active touch points
            for touch_id, touch_point in self.active_touch_points.items():
                if axis == 'x':
                    touch_point.x = value
                elif axis == 'y':
                    touch_point.y = value
                elif axis == 'pressure':
                    touch_point.pressure = value
                
                touch_point.timestamp = time.time()
                
        except Exception as e:
            self.logger.error(f"Error updating touch point: {e}")
    
    def _start_touch_point(self, touch_id: int):
        """Start new touch point"""
        try:
            touch_point = TouchPoint(
                id=touch_id,
                x=0.0,
                y=0.0,
                pressure=0.0,
                timestamp=time.time(),
                status="down"
            )
            
            self.active_touch_points[touch_id] = touch_point
            
            # Create touch event
            touch_event = TouchEvent(
                event_type="touch_down",
                touch_points=[touch_point],
                timestamp=time.time()
            )
            
            self._process_touch_event(touch_event)
            
        except Exception as e:
            self.logger.error(f"Error starting touch point: {e}")
    
    def _end_touch_point(self, touch_id: int):
        """End touch point"""
        try:
            if touch_id in self.active_touch_points:
                touch_point = self.active_touch_points[touch_id]
                touch_point.status = "up"
                touch_point.timestamp = time.time()
                
                # Create touch event
                touch_event = TouchEvent(
                    event_type="touch_up",
                    touch_points=[touch_point],
                    timestamp=time.time()
                )
                
                self._process_touch_event(touch_event)
                
                # Remove from active points
                del self.active_touch_points[touch_id]
                
        except Exception as e:
            self.logger.error(f"Error ending touch point: {e}")
    
    def _handle_touch_down(self):
        """Handle touch down event"""
        try:
            # Create touch event for all active points
            if self.active_touch_points:
                touch_points = list(self.active_touch_points.values())
                touch_event = TouchEvent(
                    event_type="touch_down",
                    touch_points=touch_points,
                    timestamp=time.time()
                )
                
                self._process_touch_event(touch_event)
                
        except Exception as e:
            self.logger.error(f"Error handling touch down: {e}")
    
    def _handle_touch_up(self):
        """Handle touch up event"""
        try:
            # Create touch event for all active points
            if self.active_touch_points:
                touch_points = list(self.active_touch_points.values())
                for touch_point in touch_points:
                    touch_point.status = "up"
                
                touch_event = TouchEvent(
                    event_type="touch_up",
                    touch_points=touch_points,
                    timestamp=time.time()
                )
                
                self._process_touch_event(touch_event)
                
                # Clear active points
                self.active_touch_points.clear()
                
        except Exception as e:
            self.logger.error(f"Error handling touch up: {e}")
    
    def _process_touch_event(self, touch_event: TouchEvent):
        """Process touch event and notify callbacks"""
        try:
            # Detect gestures
            if self.touch_config['gesture_enabled']:
                gesture = self._detect_gesture(touch_event)
                if gesture:
                    touch_event.gesture_type = gesture['type']
                    touch_event.gesture_data = gesture['data']
                    self._notify_gesture_callbacks(touch_event)
            
            # Notify touch callbacks
            self._notify_touch_callbacks(touch_event)
            
        except Exception as e:
            self.logger.error(f"Error processing touch event: {e}")
    
    def _detect_gesture(self, touch_event: TouchEvent) -> Optional[Dict]:
        """Detect gestures from touch event"""
        try:
            if len(touch_event.touch_points) == 1:
                # Single touch gestures
                touch_point = touch_event.touch_points[0]
                
                if touch_event.event_type == "touch_down":
                    # Store initial position for gesture detection
                    if not hasattr(self, '_gesture_start'):
                        self._gesture_start = {'x': touch_point.x, 'y': touch_point.y, 'time': touch_point.timestamp}
                
                elif touch_event.event_type == "touch_up":
                    # Detect tap, swipe, etc.
                    if hasattr(self, '_gesture_start'):
                        dx = touch_point.x - self._gesture_start['x']
                        dy = touch_point.y - self._gesture_start['y']
                        dt = touch_point.timestamp - self._gesture_start['time']
                        
                        distance = (dx**2 + dy**2)**0.5
                        
                        if distance < self.touch_config['gesture_threshold']:
                            return {'type': 'tap', 'data': {'x': touch_point.x, 'y': touch_point.y}}
                        elif distance > self.touch_config['gesture_threshold'] and dt < 0.5:
                            # Determine swipe direction
                            if abs(dx) > abs(dy):
                                direction = 'right' if dx > 0 else 'left'
                            else:
                                direction = 'down' if dy > 0 else 'up'
                            
                            return {
                                'type': 'swipe',
                                'data': {
                                    'direction': direction,
                                    'distance': distance,
                                    'duration': dt
                                }
                            }
                        
                        delattr(self, '_gesture_start')
            
            elif len(touch_event.touch_points) == 2:
                # Multi-touch gestures
                return {'type': 'pinch', 'data': {'points': len(touch_event.touch_points)}}
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting gesture: {e}")
            return None
    
    def _apply_calibration(self, value: int, axis: str) -> int:
        """Apply calibration to touch value"""
        try:
            if axis in self.calibration_data:
                calib = self.calibration_data[axis]
                # Apply linear calibration: new_value = (value - offset) * scale
                return int((value - calib.get('offset', 0)) * calib.get('scale', 1.0))
            return value
        except Exception as e:
            self.logger.error(f"Error applying calibration: {e}")
            return value
    
    def register_touch_callback(self, callback: Callable[[TouchEvent], None]):
        """Register callback for touch events"""
        self.touch_callbacks.append(callback)
        self.logger.info("Touch callback registered")
    
    def register_gesture_callback(self, callback: Callable[[TouchEvent], None]):
        """Register callback for gesture events"""
        self.gesture_callbacks.append(callback)
        self.logger.info("Gesture callback registered")
    
    def _notify_touch_callbacks(self, touch_event: TouchEvent):
        """Notify touch callbacks"""
        for callback in self.touch_callbacks:
            try:
                callback(touch_event)
            except Exception as e:
                self.logger.error(f"Touch callback error: {e}")
    
    def _notify_gesture_callbacks(self, touch_event: TouchEvent):
        """Notify gesture callbacks"""
        for callback in self.gesture_callbacks:
            try:
                callback(touch_event)
            except Exception as e:
                self.logger.error(f"Gesture callback error: {e}")
    
    def calibrate_touch(self, calibration_data: Dict):
        """Calibrate touch screen"""
        try:
            self.calibration_data = calibration_data
            self.logger.info("Touch calibration applied")
        except Exception as e:
            self.logger.error(f"Error applying touch calibration: {e}")
    
    def get_touch_status(self) -> Dict:
        """Get touch handler status"""
        return {
            'is_running': self.is_running,
            'touch_devices_count': len(self.touch_devices),
            'active_touch_points': len(self.active_touch_points),
            'touch_callbacks_count': len(self.touch_callbacks),
            'gesture_callbacks_count': len(self.gesture_callbacks),
            'calibration_applied': bool(self.calibration_data),
            'evdev_available': EVDEV_AVAILABLE
        }

# Example usage and testing
if __name__ == "__main__":
    # Test touch event handler
    touch_handler = TouchEventHandler()
    
    print("Touch Event Handler Test:")
    print("=" * 50)
    
    # Register callbacks
    def touch_callback(touch_event: TouchEvent):
        print(f"Touch Event: {touch_event.event_type} - Points: {len(touch_event.touch_points)}")
        for point in touch_event.touch_points:
            print(f"  Point {point.id}: ({point.x:.1f}, {point.y:.1f}) - {point.status}")
    
    def gesture_callback(touch_event: TouchEvent):
        print(f"Gesture: {touch_event.gesture_type} - {touch_event.gesture_data}")
    
    touch_handler.register_touch_callback(touch_callback)
    touch_handler.register_gesture_callback(gesture_callback)
    
    # Start touch handling
    print("\n1. Starting touch handling...")
    touch_handler.start_touch_handling()
    
    # Get status
    print("\n2. Touch handler status:")
    status = touch_handler.get_touch_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Test for a few seconds
    print("\n3. Testing touch events for 10 seconds...")
    time.sleep(10)
    
    # Stop touch handling
    print("\n4. Stopping touch handling...")
    touch_handler.stop_touch_handling()
    
    print("\n✅ Touch event handler test completed successfully!")
