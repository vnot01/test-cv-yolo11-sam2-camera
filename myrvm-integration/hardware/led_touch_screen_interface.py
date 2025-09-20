#!/usr/bin/env python3
"""
LED Touch Screen Interface
Main interface for LED Touch Screen hardware integration
"""

import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from hardware.hardware_detector import HardwareDetector
from hardware.touch_event_handler import TouchEventHandler, TouchEvent
from hardware.display_manager import DisplayManager, DisplayInfo, DisplaySettings

@dataclass
class LEDScreenConfig:
    """LED Screen configuration"""
    screen_id: str
    resolution: tuple
    brightness: int
    contrast: int
    orientation: str
    touch_enabled: bool
    multi_touch_enabled: bool
    gesture_enabled: bool
    auto_brightness: bool
    calibration_data: Dict

@dataclass
class LEDScreenStatus:
    """LED Screen status"""
    is_initialized: bool
    is_running: bool
    display_info: Optional[DisplayInfo]
    display_settings: Optional[DisplaySettings]
    touch_handler_status: Dict
    hardware_detection: Dict
    performance_metrics: Dict

class LEDTouchScreenInterface:
    """Main LED Touch Screen Interface"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize LED Touch Screen Interface
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.screen_config = None
        self.is_initialized = False
        self.is_running = False
        
        # Core components
        self.hardware_detector = None
        self.touch_handler = None
        self.display_manager = None
        
        # Status and metrics
        self.status = LEDScreenStatus(
            is_initialized=False,
            is_running=False,
            display_info=None,
            display_settings=None,
            touch_handler_status={},
            hardware_detection={},
            performance_metrics={}
        )
        
        # Callbacks
        self.touch_callbacks = []
        self.gesture_callbacks = []
        self.status_callbacks = []
        
        # Threading
        self.monitor_thread = None
        self.shutdown_event = threading.Event()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize interface
        self._initialize_interface()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for LED Touch Screen Interface"""
        logger = logging.getLogger('LEDTouchScreenInterface')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        from datetime import datetime
        log_file = log_dir / f'led_touch_screen_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _initialize_interface(self):
        """Initialize LED Touch Screen Interface"""
        try:
            self.logger.info("Initializing LED Touch Screen Interface...")
            
            # Initialize hardware detector
            self._initialize_hardware_detector()
            
            # Initialize display manager
            self._initialize_display_manager()
            
            # Initialize touch handler
            self._initialize_touch_handler()
            
            # Load configuration
            self._load_configuration()
            
            # Setup callbacks
            self._setup_callbacks()
            
            self.is_initialized = True
            self.status.is_initialized = True
            
            self.logger.info("LED Touch Screen Interface initialized successfully")
            
        except Exception as e:
            self.logger.error(f"LED Touch Screen Interface initialization failed: {e}")
            raise
    
    def _initialize_hardware_detector(self):
        """Initialize hardware detector"""
        try:
            self.logger.info("Initializing hardware detector...")
            self.hardware_detector = HardwareDetector()
            
            # Detect hardware
            detection_results = self.hardware_detector.detect_all_hardware()
            self.status.hardware_detection = detection_results
            
            self.logger.info("Hardware detector initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize hardware detector: {e}")
            raise
    
    def _initialize_display_manager(self):
        """Initialize display manager"""
        try:
            self.logger.info("Initializing display manager...")
            
            # Get screen config from hardware detection
            screen_config = self.status.hardware_detection.get('screen_hardware', {})
            
            self.display_manager = DisplayManager(screen_config)
            
            # Get display info and settings
            self.status.display_info = self.display_manager.get_display_info()
            self.status.display_settings = self.display_manager.get_display_settings()
            
            self.logger.info("Display manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize display manager: {e}")
            raise
    
    def _initialize_touch_handler(self):
        """Initialize touch handler"""
        try:
            self.logger.info("Initializing touch handler...")
            
            self.touch_handler = TouchEventHandler(self)
            
            # Get touch handler status
            self.status.touch_handler_status = self.touch_handler.get_touch_status()
            
            self.logger.info("Touch handler initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize touch handler: {e}")
            raise
    
    def _load_configuration(self):
        """Load configuration"""
        try:
            self.logger.info("Loading configuration...")
            
            # Create default configuration
            default_config = LEDScreenConfig(
                screen_id="led_touch_screen_001",
                resolution=(1920, 1080),
                brightness=80,
                contrast=50,
                orientation="landscape",
                touch_enabled=True,
                multi_touch_enabled=True,
                gesture_enabled=True,
                auto_brightness=False,
                calibration_data={}
            )
            
            # Update with detected hardware info
            if self.status.display_info:
                default_config.resolution = self.status.display_info.resolution
                default_config.brightness = self.status.display_info.brightness
                default_config.contrast = self.status.display_info.contrast
                default_config.orientation = self.status.display_info.orientation
            
            # Update with touch capabilities
            if self.status.touch_handler_status:
                default_config.touch_enabled = self.status.touch_handler_status.get('touch_devices_count', 0) > 0
                default_config.multi_touch_enabled = self.status.touch_handler_status.get('evdev_available', False)
            
            # Apply user configuration
            if self.config:
                for key, value in self.config.items():
                    if hasattr(default_config, key):
                        setattr(default_config, key, value)
            
            self.screen_config = default_config
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _setup_callbacks(self):
        """Setup callbacks"""
        try:
            self.logger.info("Setting up callbacks...")
            
            # Setup touch callbacks
            if self.touch_handler:
                self.touch_handler.register_touch_callback(self._handle_touch_event)
                self.touch_handler.register_gesture_callback(self._handle_gesture_event)
            
            self.logger.info("Callbacks setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup callbacks: {e}")
            raise
    
    def start(self):
        """Start LED Touch Screen Interface"""
        try:
            if not self.is_initialized:
                raise RuntimeError("Interface not initialized")
            
            if self.is_running:
                self.logger.warning("Interface already running")
                return
            
            self.logger.info("Starting LED Touch Screen Interface...")
            
            # Start touch handler
            if self.touch_handler and self.screen_config.touch_enabled:
                self.touch_handler.start_touch_handling()
                self.logger.info("Touch handler started")
            
            # Optimize display for LED
            if self.display_manager:
                self.display_manager.optimize_for_led()
                self.logger.info("Display optimized for LED")
            
            # Start monitoring thread
            self._start_monitoring()
            
            self.is_running = True
            self.status.is_running = True
            
            self.logger.info("LED Touch Screen Interface started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start LED Touch Screen Interface: {e}")
            raise
    
    def stop(self):
        """Stop LED Touch Screen Interface"""
        try:
            if not self.is_running:
                self.logger.warning("Interface not running")
                return
            
            self.logger.info("Stopping LED Touch Screen Interface...")
            
            # Stop monitoring thread
            self._stop_monitoring()
            
            # Stop touch handler
            if self.touch_handler:
                self.touch_handler.stop_touch_handling()
                self.logger.info("Touch handler stopped")
            
            self.is_running = False
            self.status.is_running = False
            
            self.logger.info("LED Touch Screen Interface stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop LED Touch Screen Interface: {e}")
    
    def _start_monitoring(self):
        """Start monitoring thread"""
        try:
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="LEDScreenMonitorThread"
            )
            self.monitor_thread.start()
            self.logger.info("Monitoring thread started")
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring thread: {e}")
    
    def _stop_monitoring(self):
        """Stop monitoring thread"""
        try:
            self.shutdown_event.set()
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
            
            self.logger.info("Monitoring thread stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring thread: {e}")
    
    def _monitoring_loop(self):
        """Monitoring loop"""
        while not self.shutdown_event.is_set():
            try:
                # Update status
                self._update_status()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Notify status callbacks
                self._notify_status_callbacks()
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)
    
    def _update_status(self):
        """Update status information"""
        try:
            # Update display info
            if self.display_manager:
                self.status.display_info = self.display_manager.get_display_info()
                self.status.display_settings = self.display_manager.get_display_settings()
            
            # Update touch handler status
            if self.touch_handler:
                self.status.touch_handler_status = self.touch_handler.get_touch_status()
            
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            import psutil
            
            metrics = {
                'timestamp': time.time(),
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'touch_events_per_second': 0,  # TODO: Calculate from touch handler
                'display_fps': 60,  # TODO: Get from display manager
                'response_time_ms': 0  # TODO: Calculate average response time
            }
            
            self.status.performance_metrics = metrics
            
        except Exception as e:
            self.logger.error(f"Failed to update performance metrics: {e}")
    
    def _handle_touch_event(self, touch_event: TouchEvent):
        """Handle touch event"""
        try:
            self.logger.debug(f"Touch event: {touch_event.event_type} - {len(touch_event.touch_points)} points")
            
            # Notify touch callbacks
            for callback in self.touch_callbacks:
                try:
                    callback(touch_event)
                except Exception as e:
                    self.logger.error(f"Touch callback error: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle touch event: {e}")
    
    def _handle_gesture_event(self, touch_event: TouchEvent):
        """Handle gesture event"""
        try:
            self.logger.debug(f"Gesture event: {touch_event.gesture_type} - {touch_event.gesture_data}")
            
            # Notify gesture callbacks
            for callback in self.gesture_callbacks:
                try:
                    callback(touch_event)
                except Exception as e:
                    self.logger.error(f"Gesture callback error: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle gesture event: {e}")
    
    def _notify_status_callbacks(self):
        """Notify status callbacks"""
        try:
            for callback in self.status_callbacks:
                try:
                    callback(self.status)
                except Exception as e:
                    self.logger.error(f"Status callback error: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to notify status callbacks: {e}")
    
    # Public methods for external use
    
    def set_brightness(self, brightness: int) -> bool:
        """Set display brightness"""
        try:
            if not self.display_manager:
                return False
            
            success = self.display_manager.set_brightness(brightness)
            if success:
                self.screen_config.brightness = brightness
                self.logger.info(f"Brightness set to {brightness}%")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to set brightness: {e}")
            return False
    
    def set_contrast(self, contrast: int) -> bool:
        """Set display contrast"""
        try:
            if not self.display_manager:
                return False
            
            success = self.display_manager.set_contrast(contrast)
            if success:
                self.screen_config.contrast = contrast
                self.logger.info(f"Contrast set to {contrast}%")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to set contrast: {e}")
            return False
    
    def set_orientation(self, orientation: str) -> bool:
        """Set display orientation"""
        try:
            if not self.display_manager:
                return False
            
            success = self.display_manager.set_orientation(orientation)
            if success:
                self.screen_config.orientation = orientation
                self.logger.info(f"Orientation set to {orientation}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to set orientation: {e}")
            return False
    
    def set_resolution(self, width: int, height: int) -> bool:
        """Set display resolution"""
        try:
            if not self.display_manager:
                return False
            
            success = self.display_manager.set_resolution(width, height)
            if success:
                self.screen_config.resolution = (width, height)
                self.logger.info(f"Resolution set to {width}x{height}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to set resolution: {e}")
            return False
    
    def calibrate_touch(self, calibration_data: Dict):
        """Calibrate touch screen"""
        try:
            if not self.touch_handler:
                return False
            
            self.touch_handler.calibrate_touch(calibration_data)
            self.screen_config.calibration_data = calibration_data
            self.logger.info("Touch calibration applied")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to calibrate touch: {e}")
            return False
    
    def register_touch_callback(self, callback: Callable[[TouchEvent], None]):
        """Register touch callback"""
        self.touch_callbacks.append(callback)
        self.logger.info("Touch callback registered")
    
    def register_gesture_callback(self, callback: Callable[[TouchEvent], None]):
        """Register gesture callback"""
        self.gesture_callbacks.append(callback)
        self.logger.info("Gesture callback registered")
    
    def register_status_callback(self, callback: Callable[[LEDScreenStatus], None]):
        """Register status callback"""
        self.status_callbacks.append(callback)
        self.logger.info("Status callback registered")
    
    def get_status(self) -> LEDScreenStatus:
        """Get current status"""
        return self.status
    
    def get_config(self) -> LEDScreenConfig:
        """Get current configuration"""
        return self.screen_config
    
    def get_hardware_info(self) -> Dict:
        """Get hardware information"""
        return self.status.hardware_detection
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        return self.status.performance_metrics
    
    def save_configuration(self, file_path: str):
        """Save configuration to file"""
        try:
            config_data = asdict(self.screen_config)
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            self.logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def load_configuration(self, file_path: str):
        """Load configuration from file"""
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            self.screen_config = LEDScreenConfig(**config_data)
            self.logger.info(f"Configuration loaded from {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test LED Touch Screen Interface
    interface = LEDTouchScreenInterface()
    
    print("LED Touch Screen Interface Test:")
    print("=" * 50)
    
    # Get status
    print("\n1. Interface Status:")
    status = interface.get_status()
    print(f"   Initialized: {status.is_initialized}")
    print(f"   Running: {status.is_running}")
    print(f"   Display: {status.display_info.name if status.display_info else 'None'}")
    print(f"   Touch Devices: {status.touch_handler_status.get('touch_devices_count', 0)}")
    
    # Get configuration
    print("\n2. Configuration:")
    config = interface.get_config()
    print(f"   Screen ID: {config.screen_id}")
    print(f"   Resolution: {config.resolution}")
    print(f"   Brightness: {config.brightness}%")
    print(f"   Contrast: {config.contrast}%")
    print(f"   Orientation: {config.orientation}")
    print(f"   Touch Enabled: {config.touch_enabled}")
    print(f"   Multi-touch Enabled: {config.multi_touch_enabled}")
    print(f"   Gesture Enabled: {config.gesture_enabled}")
    
    # Get hardware info
    print("\n3. Hardware Information:")
    hardware_info = interface.get_hardware_info()
    print(f"   Platform: {hardware_info.get('system_info', {}).get('platform', 'Unknown')}")
    print(f"   Architecture: {hardware_info.get('system_info', {}).get('architecture', 'Unknown')}")
    print(f"   Display Devices: {len(hardware_info.get('display_devices', []))}")
    print(f"   Touch Devices: {len(hardware_info.get('touch_devices', []))}")
    
    # Test callbacks
    print("\n4. Testing Callbacks:")
    
    def touch_callback(touch_event: TouchEvent):
        print(f"   Touch: {touch_event.event_type} - {len(touch_event.touch_points)} points")
    
    def gesture_callback(touch_event: TouchEvent):
        print(f"   Gesture: {touch_event.gesture_type}")
    
    def status_callback(status: LEDScreenStatus):
        print(f"   Status: Running={status.is_running}, Display={status.display_info.name if status.display_info else 'None'}")
    
    interface.register_touch_callback(touch_callback)
    interface.register_gesture_callback(gesture_callback)
    interface.register_status_callback(status_callback)
    
    # Start interface
    print("\n5. Starting Interface:")
    interface.start()
    
    # Test for a few seconds
    print("\n6. Testing for 10 seconds...")
    time.sleep(10)
    
    # Test display controls
    print("\n7. Testing Display Controls:")
    print("   Setting brightness to 70%...")
    interface.set_brightness(70)
    
    print("   Setting contrast to 55%...")
    interface.set_contrast(55)
    
    print("   Setting orientation to 'normal'...")
    interface.set_orientation('normal')
    
    # Get performance metrics
    print("\n8. Performance Metrics:")
    metrics = interface.get_performance_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    # Stop interface
    print("\n9. Stopping Interface:")
    interface.stop()
    
    print("\n✅ LED Touch Screen Interface test completed successfully!")
