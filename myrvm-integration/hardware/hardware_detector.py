#!/usr/bin/env python3
"""
Hardware Detector for LED Touch Screen
Detect and configure LED Touch Screen hardware
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    import pyudev
    import psutil
    HARDWARE_LIBS_AVAILABLE = True
except ImportError:
    HARDWARE_LIBS_AVAILABLE = False

class HardwareDetector:
    """Detect and configure LED Touch Screen hardware"""
    
    def __init__(self):
        """Initialize Hardware Detector"""
        self.detected_hardware = {}
        self.screen_devices = []
        self.touch_devices = []
        self.display_devices = []
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Hardware detection results
        self.detection_results = {
            'screen_hardware': {},
            'touch_devices': [],
            'display_devices': [],
            'system_info': {},
            'capabilities': {}
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for hardware detector"""
        logger = logging.getLogger('HardwareDetector')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        from datetime import datetime
        log_file = log_dir / f'hardware_detector_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def detect_all_hardware(self) -> Dict:
        """
        Detect all LED Touch Screen hardware
        
        Returns:
            Dictionary containing all detected hardware information
        """
        try:
            self.logger.info("Starting hardware detection...")
            
            # Detect system information
            self._detect_system_info()
            
            # Detect display devices
            self._detect_display_devices()
            
            # Detect touch devices
            self._detect_touch_devices()
            
            # Detect screen hardware
            self._detect_screen_hardware()
            
            # Get hardware capabilities
            self._get_hardware_capabilities()
            
            self.logger.info("Hardware detection completed successfully")
            return self.detection_results
            
        except Exception as e:
            self.logger.error(f"Hardware detection failed: {e}")
            raise
    
    def _detect_system_info(self):
        """Detect system information"""
        try:
            self.logger.info("Detecting system information...")
            
            system_info = {
                'platform': sys.platform,
                'architecture': os.uname().machine if hasattr(os, 'uname') else 'unknown',
                'kernel_version': self._get_kernel_version(),
                'cpu_info': self._get_cpu_info(),
                'memory_info': self._get_memory_info(),
                'gpu_info': self._get_gpu_info()
            }
            
            self.detection_results['system_info'] = system_info
            self.logger.info(f"System info detected: {system_info['platform']} {system_info['architecture']}")
            
        except Exception as e:
            self.logger.error(f"Failed to detect system info: {e}")
            self.detection_results['system_info'] = {'error': str(e)}
    
    def _detect_display_devices(self):
        """Detect display devices"""
        try:
            self.logger.info("Detecting display devices...")
            
            display_devices = []
            
            # Check for framebuffer devices
            fb_devices = self._get_framebuffer_devices()
            display_devices.extend(fb_devices)
            
            # Check for DRM devices
            drm_devices = self._get_drm_devices()
            display_devices.extend(drm_devices)
            
            # Check for X11 displays
            x11_displays = self._get_x11_displays()
            display_devices.extend(x11_displays)
            
            # Check for Wayland displays
            wayland_displays = self._get_wayland_displays()
            display_devices.extend(wayland_displays)
            
            self.detection_results['display_devices'] = display_devices
            self.logger.info(f"Found {len(display_devices)} display devices")
            
        except Exception as e:
            self.logger.error(f"Failed to detect display devices: {e}")
            self.detection_results['display_devices'] = []
    
    def _detect_touch_devices(self):
        """Detect touch devices"""
        try:
            self.logger.info("Detecting touch devices...")
            
            touch_devices = []
            
            # Check for input devices
            input_devices = self._get_input_devices()
            for device in input_devices:
                if self._is_touch_device(device):
                    touch_devices.append(device)
            
            # Check for USB touch devices
            usb_touch_devices = self._get_usb_touch_devices()
            touch_devices.extend(usb_touch_devices)
            
            self.detection_results['touch_devices'] = touch_devices
            self.logger.info(f"Found {len(touch_devices)} touch devices")
            
        except Exception as e:
            self.logger.error(f"Failed to detect touch devices: {e}")
            self.detection_results['touch_devices'] = []
    
    def _detect_screen_hardware(self):
        """Detect screen hardware"""
        try:
            self.logger.info("Detecting screen hardware...")
            
            screen_hardware = {
                'primary_display': self._get_primary_display(),
                'available_resolutions': self._get_available_resolutions(),
                'color_depth': self._get_color_depth(),
                'refresh_rates': self._get_refresh_rates(),
                'brightness_control': self._check_brightness_control(),
                'orientation_support': self._check_orientation_support()
            }
            
            self.detection_results['screen_hardware'] = screen_hardware
            self.logger.info("Screen hardware detection completed")
            
        except Exception as e:
            self.logger.error(f"Failed to detect screen hardware: {e}")
            self.detection_results['screen_hardware'] = {'error': str(e)}
    
    def _get_hardware_capabilities(self):
        """Get hardware capabilities"""
        try:
            self.logger.info("Getting hardware capabilities...")
            
            capabilities = {
                'multi_touch': self._check_multi_touch_support(),
                'gesture_recognition': self._check_gesture_support(),
                'pressure_sensitivity': self._check_pressure_support(),
                'hardware_acceleration': self._check_hardware_acceleration(),
                'gpu_memory': self._get_gpu_memory(),
                'display_rotation': self._check_display_rotation()
            }
            
            self.detection_results['capabilities'] = capabilities
            self.logger.info("Hardware capabilities detection completed")
            
        except Exception as e:
            self.logger.error(f"Failed to get hardware capabilities: {e}")
            self.detection_results['capabilities'] = {'error': str(e)}
    
    def _get_kernel_version(self) -> str:
        """Get kernel version"""
        try:
            with open('/proc/version', 'r') as f:
                version = f.read().strip()
            return version
        except:
            return 'unknown'
    
    def _get_cpu_info(self) -> Dict:
        """Get CPU information"""
        try:
            if HARDWARE_LIBS_AVAILABLE:
                return {
                    'count': psutil.cpu_count(),
                    'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                    'usage': psutil.cpu_percent(interval=1)
                }
            else:
                return {'count': 1, 'frequency': {}, 'usage': 0}
        except:
            return {'count': 1, 'frequency': {}, 'usage': 0}
    
    def _get_memory_info(self) -> Dict:
        """Get memory information"""
        try:
            if HARDWARE_LIBS_AVAILABLE:
                memory = psutil.virtual_memory()
                return {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percentage': memory.percent
                }
            else:
                return {'total': 0, 'available': 0, 'used': 0, 'percentage': 0}
        except:
            return {'total': 0, 'available': 0, 'used': 0, 'percentage': 0}
    
    def _get_gpu_info(self) -> Dict:
        """Get GPU information"""
        try:
            # Try to get NVIDIA GPU info
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used', '--format=csv,noheader,nounits'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    gpus = []
                    for line in lines:
                        parts = line.split(', ')
                        if len(parts) >= 3:
                            gpus.append({
                                'name': parts[0],
                                'memory_total': int(parts[1]),
                                'memory_used': int(parts[2])
                            })
                    return {'nvidia_gpus': gpus}
            except:
                pass
            
            # Try to get general GPU info
            try:
                result = subprocess.run(['lspci', '-nn'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    gpu_lines = [line for line in result.stdout.split('\n') if 'VGA' in line or 'Display' in line]
                    return {'pci_gpus': gpu_lines}
            except:
                pass
            
            return {'error': 'No GPU information available'}
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_framebuffer_devices(self) -> List[Dict]:
        """Get framebuffer devices"""
        try:
            fb_devices = []
            fb_path = Path('/dev')
            for fb_file in fb_path.glob('fb*'):
                if fb_file.is_char_device():
                    fb_devices.append({
                        'device': str(fb_file),
                        'type': 'framebuffer',
                        'name': fb_file.name
                    })
            return fb_devices
        except:
            return []
    
    def _get_drm_devices(self) -> List[Dict]:
        """Get DRM devices"""
        try:
            drm_devices = []
            drm_path = Path('/dev/dri')
            if drm_path.exists():
                for drm_file in drm_path.glob('card*'):
                    if drm_file.is_char_device():
                        drm_devices.append({
                            'device': str(drm_file),
                            'type': 'drm',
                            'name': drm_file.name
                        })
            return drm_devices
        except:
            return []
    
    def _get_x11_displays(self) -> List[Dict]:
        """Get X11 displays"""
        try:
            displays = []
            if 'DISPLAY' in os.environ:
                displays.append({
                    'display': os.environ['DISPLAY'],
                    'type': 'x11',
                    'name': 'X11 Display'
                })
            return displays
        except:
            return []
    
    def _get_wayland_displays(self) -> List[Dict]:
        """Get Wayland displays"""
        try:
            displays = []
            if 'WAYLAND_DISPLAY' in os.environ:
                displays.append({
                    'display': os.environ['WAYLAND_DISPLAY'],
                    'type': 'wayland',
                    'name': 'Wayland Display'
                })
            return displays
        except:
            return []
    
    def _get_input_devices(self) -> List[Dict]:
        """Get input devices"""
        try:
            input_devices = []
            input_path = Path('/dev/input')
            if input_path.exists():
                for input_file in input_path.glob('event*'):
                    if input_file.is_char_device():
                        input_devices.append({
                            'device': str(input_file),
                            'type': 'input',
                            'name': input_file.name
                        })
            return input_devices
        except:
            return []
    
    def _is_touch_device(self, device: Dict) -> bool:
        """Check if device is a touch device"""
        try:
            # Check device capabilities
            device_path = device['device']
            try:
                result = subprocess.run(['evtest', '--query', device_path], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    output = result.stdout.lower()
                    return 'touch' in output or 'abs' in output
            except:
                pass
            
            # Check device name
            device_name = device.get('name', '').lower()
            return 'touch' in device_name or 'touchscreen' in device_name
            
        except:
            return False
    
    def _get_usb_touch_devices(self) -> List[Dict]:
        """Get USB touch devices"""
        try:
            usb_devices = []
            if HARDWARE_LIBS_AVAILABLE:
                context = pyudev.Context()
                for device in context.list_devices(subsystem='usb'):
                    if device.get('ID_INPUT_TOUCHSCREEN') == '1':
                        usb_devices.append({
                            'device': device.device_path,
                            'type': 'usb_touch',
                            'name': device.get('ID_MODEL', 'Unknown USB Touch Device'),
                            'vendor': device.get('ID_VENDOR', 'Unknown'),
                            'product': device.get('ID_PRODUCT', 'Unknown')
                        })
            return usb_devices
        except:
            return []
    
    def _get_primary_display(self) -> Dict:
        """Get primary display information"""
        try:
            # Try to get display info from xrandr
            try:
                result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if ' connected' in line and 'primary' in line:
                            parts = line.split()
                            if len(parts) >= 4:
                                return {
                                    'name': parts[0],
                                    'resolution': parts[3],
                                    'type': 'xrandr',
                                    'primary': True
                                }
            except:
                pass
            
            # Fallback to default
            return {
                'name': 'Default Display',
                'resolution': '1920x1080',
                'type': 'default',
                'primary': True
            }
            
        except:
            return {'error': 'Unable to detect primary display'}
    
    def _get_available_resolutions(self) -> List[str]:
        """Get available resolutions"""
        try:
            resolutions = []
            
            # Try to get resolutions from xrandr
            try:
                result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if ' connected' in line:
                            # Extract resolution from line
                            parts = line.split()
                            for part in parts:
                                if 'x' in part and '+' in part:
                                    resolution = part.split('+')[0]
                                    if resolution not in resolutions:
                                        resolutions.append(resolution)
            except:
                pass
            
            # Add common resolutions if none found
            if not resolutions:
                resolutions = ['1920x1080', '1366x768', '1280x720', '1024x768', '800x600']
            
            return resolutions
            
        except:
            return ['1920x1080']
    
    def _get_color_depth(self) -> int:
        """Get color depth"""
        try:
            # Try to get color depth from xdpyinfo
            try:
                result = subprocess.run(['xdpyinfo'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'depth of root window:' in line:
                            depth = int(line.split(':')[1].strip())
                            return depth
            except:
                pass
            
            return 24  # Default color depth
            
        except:
            return 24
    
    def _get_refresh_rates(self) -> List[int]:
        """Get available refresh rates"""
        try:
            refresh_rates = []
            
            # Try to get refresh rates from xrandr
            try:
                result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if ' connected' in line:
                            # Extract refresh rates from line
                            parts = line.split()
                            for part in parts:
                                if 'Hz' in part:
                                    rate = int(part.replace('Hz', '').replace('*', ''))
                                    if rate not in refresh_rates:
                                        refresh_rates.append(rate)
            except:
                pass
            
            # Add common refresh rates if none found
            if not refresh_rates:
                refresh_rates = [60, 75, 120, 144]
            
            return refresh_rates
            
        except:
            return [60]
    
    def _check_brightness_control(self) -> bool:
        """Check if brightness control is available"""
        try:
            # Check for brightness control files
            brightness_paths = [
                '/sys/class/backlight',
                '/sys/class/leds',
                '/proc/acpi/video'
            ]
            
            for path in brightness_paths:
                if Path(path).exists():
                    return True
            
            return False
            
        except:
            return False
    
    def _check_orientation_support(self) -> bool:
        """Check if orientation support is available"""
        try:
            # Check for orientation control
            orientation_paths = [
                '/sys/class/backlight',
                '/sys/devices/platform'
            ]
            
            for path in orientation_paths:
                if Path(path).exists():
                    return True
            
            return False
            
        except:
            return False
    
    def _check_multi_touch_support(self) -> bool:
        """Check if multi-touch is supported"""
        try:
            # Check touch devices for multi-touch capability
            touch_devices = self.detection_results.get('touch_devices', [])
            for device in touch_devices:
                if 'multi' in device.get('name', '').lower():
                    return True
            
            return len(touch_devices) > 0
            
        except:
            return False
    
    def _check_gesture_support(self) -> bool:
        """Check if gesture recognition is supported"""
        try:
            # Check for gesture support in touch devices
            touch_devices = self.detection_results.get('touch_devices', [])
            return len(touch_devices) > 0
            
        except:
            return False
    
    def _check_pressure_support(self) -> bool:
        """Check if pressure sensitivity is supported"""
        try:
            # Check for pressure support in touch devices
            touch_devices = self.detection_results.get('touch_devices', [])
            for device in touch_devices:
                if 'pressure' in device.get('name', '').lower():
                    return True
            
            return False
            
        except:
            return False
    
    def _check_hardware_acceleration(self) -> bool:
        """Check if hardware acceleration is available"""
        try:
            # Check for GPU and hardware acceleration
            gpu_info = self.detection_results.get('system_info', {}).get('gpu_info', {})
            return 'nvidia_gpus' in gpu_info or 'pci_gpus' in gpu_info
            
        except:
            return False
    
    def _get_gpu_memory(self) -> int:
        """Get GPU memory in MB"""
        try:
            gpu_info = self.detection_results.get('system_info', {}).get('gpu_info', {})
            if 'nvidia_gpus' in gpu_info:
                gpus = gpu_info['nvidia_gpus']
                if gpus:
                    return gpus[0].get('memory_total', 0)
            
            return 0
            
        except:
            return 0
    
    def _check_display_rotation(self) -> bool:
        """Check if display rotation is supported"""
        try:
            # Check for rotation support
            return self._check_orientation_support()
            
        except:
            return False
    
    def save_detection_results(self, file_path: str):
        """Save detection results to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.detection_results, f, indent=2)
            self.logger.info(f"Detection results saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save detection results: {e}")
    
    def load_detection_results(self, file_path: str):
        """Load detection results from file"""
        try:
            with open(file_path, 'r') as f:
                self.detection_results = json.load(f)
            self.logger.info(f"Detection results loaded from {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to load detection results: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test hardware detector
    detector = HardwareDetector()
    
    print("Hardware Detector Test:")
    print("=" * 50)
    
    # Detect all hardware
    print("\n1. Detecting all hardware...")
    results = detector.detect_all_hardware()
    
    # Print results
    print("\n2. Detection Results:")
    print(f"   System Info: {results.get('system_info', {}).get('platform', 'Unknown')}")
    print(f"   Display Devices: {len(results.get('display_devices', []))}")
    print(f"   Touch Devices: {len(results.get('touch_devices', []))}")
    print(f"   Screen Hardware: {len(results.get('screen_hardware', {}))}")
    print(f"   Capabilities: {len(results.get('capabilities', {}))}")
    
    # Print detailed results
    print("\n3. Detailed Results:")
    print(f"   System: {results.get('system_info', {})}")
    print(f"   Displays: {results.get('display_devices', [])}")
    print(f"   Touch: {results.get('touch_devices', [])}")
    print(f"   Screen: {results.get('screen_hardware', {})}")
    print(f"   Capabilities: {results.get('capabilities', {})}")
    
    # Save results
    print("\n4. Saving results...")
    detector.save_detection_results('hardware_detection_results.json')
    
    print("\n✅ Hardware detector test completed successfully!")
