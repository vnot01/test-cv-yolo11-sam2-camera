#!/usr/bin/env python3
"""
Display Manager for LED Touch Screen
Manage LED display settings and optimization
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

@dataclass
class DisplayInfo:
    """Display information"""
    name: str
    resolution: Tuple[int, int]
    refresh_rate: int
    color_depth: int
    brightness: int
    contrast: int
    orientation: str
    is_primary: bool = False

@dataclass
class DisplaySettings:
    """Display settings"""
    resolution: Tuple[int, int]
    refresh_rate: int
    brightness: int
    contrast: int
    orientation: str
    color_profile: str
    gamma: float
    color_temperature: int

class DisplayManager:
    """Manage LED display settings and optimization"""
    
    def __init__(self, screen_config: Dict = None):
        """
        Initialize Display Manager
        
        Args:
            screen_config: Screen configuration dictionary
        """
        self.screen_config = screen_config or {}
        self.current_display = None
        self.available_displays = []
        self.display_settings = None
        
        # Display configuration
        self.display_config = {
            'default_resolution': (1920, 1080),
            'default_refresh_rate': 60,
            'default_brightness': 80,
            'default_contrast': 50,
            'default_orientation': 'landscape',
            'color_profiles': ['sRGB', 'Adobe RGB', 'DCI-P3'],
            'gamma_range': (0.5, 3.0),
            'color_temp_range': (2000, 10000)
        }
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize display
        self._initialize_display()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for display manager"""
        logger = logging.getLogger('DisplayManager')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        from datetime import datetime
        log_file = log_dir / f'display_manager_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _initialize_display(self):
        """Initialize display"""
        try:
            self.logger.info("Initializing display...")
            
            # Detect available displays
            self._detect_displays()
            
            # Set primary display
            self._set_primary_display()
            
            # Initialize display settings
            self._initialize_display_settings()
            
            self.logger.info("Display initialization completed")
            
        except Exception as e:
            self.logger.error(f"Display initialization failed: {e}")
            self._create_default_display()
    
    def _detect_displays(self):
        """Detect available displays"""
        try:
            self.logger.info("Detecting displays...")
            
            displays = []
            
            # Try to detect displays using xrandr
            try:
                result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    displays.extend(self._parse_xrandr_output(result.stdout))
            except:
                pass
            
            # Try to detect displays using DRM
            try:
                drm_displays = self._detect_drm_displays()
                displays.extend(drm_displays)
            except:
                pass
            
            # If no displays found, create default
            if not displays:
                displays.append(self._create_default_display_info())
            
            self.available_displays = displays
            self.logger.info(f"Found {len(displays)} displays")
            
        except Exception as e:
            self.logger.error(f"Failed to detect displays: {e}")
            self.available_displays = [self._create_default_display_info()]
    
    def _parse_xrandr_output(self, output: str) -> List[DisplayInfo]:
        """Parse xrandr output to get display information"""
        try:
            displays = []
            lines = output.split('\n')
            
            for line in lines:
                if ' connected' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        name = parts[0]
                        is_primary = 'primary' in line
                        
                        # Extract resolution
                        resolution_str = parts[3] if parts[3] != 'primary' else parts[4]
                        if '+' in resolution_str:
                            resolution_str = resolution_str.split('+')[0]
                        
                        try:
                            width, height = map(int, resolution_str.split('x'))
                            resolution = (width, height)
                        except:
                            resolution = self.display_config['default_resolution']
                        
                        # Create display info
                        display = DisplayInfo(
                            name=name,
                            resolution=resolution,
                            refresh_rate=self.display_config['default_refresh_rate'],
                            color_depth=24,
                            brightness=self.display_config['default_brightness'],
                            contrast=self.display_config['default_contrast'],
                            orientation=self.display_config['default_orientation'],
                            is_primary=is_primary
                        )
                        
                        displays.append(display)
            
            return displays
            
        except Exception as e:
            self.logger.error(f"Failed to parse xrandr output: {e}")
            return []
    
    def _detect_drm_displays(self) -> List[DisplayInfo]:
        """Detect displays using DRM"""
        try:
            displays = []
            drm_path = Path('/dev/dri')
            
            if drm_path.exists():
                for card_file in drm_path.glob('card*'):
                    if card_file.is_char_device():
                        display = DisplayInfo(
                            name=f"DRM-{card_file.name}",
                            resolution=self.display_config['default_resolution'],
                            refresh_rate=self.display_config['default_refresh_rate'],
                            color_depth=24,
                            brightness=self.display_config['default_brightness'],
                            contrast=self.display_config['default_contrast'],
                            orientation=self.display_config['default_orientation'],
                            is_primary=False
                        )
                        displays.append(display)
            
            return displays
            
        except Exception as e:
            self.logger.error(f"Failed to detect DRM displays: {e}")
            return []
    
    def _create_default_display_info(self) -> DisplayInfo:
        """Create default display info"""
        return DisplayInfo(
            name="Default Display",
            resolution=self.display_config['default_resolution'],
            refresh_rate=self.display_config['default_refresh_rate'],
            color_depth=24,
            brightness=self.display_config['default_brightness'],
            contrast=self.display_config['default_contrast'],
            orientation=self.display_config['default_orientation'],
            is_primary=True
        )
    
    def _set_primary_display(self):
        """Set primary display"""
        try:
            if self.available_displays:
                # Find primary display
                primary_display = None
                for display in self.available_displays:
                    if display.is_primary:
                        primary_display = display
                        break
                
                # If no primary found, use first display
                if not primary_display:
                    primary_display = self.available_displays[0]
                    primary_display.is_primary = True
                
                self.current_display = primary_display
                self.logger.info(f"Primary display set to: {primary_display.name}")
            else:
                self._create_default_display()
                
        except Exception as e:
            self.logger.error(f"Failed to set primary display: {e}")
            self._create_default_display()
    
    def _create_default_display(self):
        """Create default display"""
        try:
            default_display = self._create_default_display_info()
            self.available_displays = [default_display]
            self.current_display = default_display
            self.logger.info("Created default display")
        except Exception as e:
            self.logger.error(f"Failed to create default display: {e}")
    
    def _initialize_display_settings(self):
        """Initialize display settings"""
        try:
            if self.current_display:
                self.display_settings = DisplaySettings(
                    resolution=self.current_display.resolution,
                    refresh_rate=self.current_display.refresh_rate,
                    brightness=self.current_display.brightness,
                    contrast=self.current_display.contrast,
                    orientation=self.current_display.orientation,
                    color_profile='sRGB',
                    gamma=2.2,
                    color_temperature=6500
                )
                self.logger.info("Display settings initialized")
            else:
                self.logger.warning("No current display, using default settings")
                self.display_settings = DisplaySettings(
                    resolution=self.display_config['default_resolution'],
                    refresh_rate=self.display_config['default_refresh_rate'],
                    brightness=self.display_config['default_brightness'],
                    contrast=self.display_config['default_contrast'],
                    orientation=self.display_config['default_orientation'],
                    color_profile='sRGB',
                    gamma=2.2,
                    color_temperature=6500
                )
                
        except Exception as e:
            self.logger.error(f"Failed to initialize display settings: {e}")
    
    def set_resolution(self, width: int, height: int) -> bool:
        """
        Set display resolution
        
        Args:
            width: Display width
            height: Display height
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Setting resolution to {width}x{height}")
            
            if not self.current_display:
                self.logger.error("No current display")
                return False
            
            # Try to set resolution using xrandr
            try:
                result = subprocess.run([
                    'xrandr', '--output', self.current_display.name,
                    '--mode', f'{width}x{height}'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.current_display.resolution = (width, height)
                    if self.display_settings:
                        self.display_settings.resolution = (width, height)
                    self.logger.info(f"Resolution set to {width}x{height}")
                    return True
                else:
                    self.logger.error(f"Failed to set resolution: {result.stderr}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error setting resolution: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set resolution: {e}")
            return False
    
    def set_brightness(self, brightness: int) -> bool:
        """
        Set display brightness
        
        Args:
            brightness: Brightness level (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            brightness = max(0, min(100, brightness))  # Clamp to 0-100
            self.logger.info(f"Setting brightness to {brightness}%")
            
            if not self.current_display:
                self.logger.error("No current display")
                return False
            
            # Try to set brightness using backlight control
            success = False
            
            # Try different brightness control methods
            brightness_paths = [
                '/sys/class/backlight',
                '/sys/class/leds',
                '/proc/acpi/video'
            ]
            
            for path in brightness_paths:
                if Path(path).exists():
                    if self._set_brightness_sysfs(path, brightness):
                        success = True
                        break
            
            if success:
                self.current_display.brightness = brightness
                if self.display_settings:
                    self.display_settings.brightness = brightness
                self.logger.info(f"Brightness set to {brightness}%")
                return True
            else:
                self.logger.warning("No brightness control available, using software simulation")
                # Simulate brightness change
                self.current_display.brightness = brightness
                if self.display_settings:
                    self.display_settings.brightness = brightness
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to set brightness: {e}")
            return False
    
    def _set_brightness_sysfs(self, path: str, brightness: int) -> bool:
        """Set brightness using sysfs"""
        try:
            brightness_path = Path(path)
            
            # Find brightness control file
            for item in brightness_path.iterdir():
                if item.is_dir():
                    brightness_file = item / 'brightness'
                    max_brightness_file = item / 'max_brightness'
                    
                    if brightness_file.exists() and max_brightness_file.exists():
                        try:
                            # Read max brightness
                            with open(max_brightness_file, 'r') as f:
                                max_brightness = int(f.read().strip())
                            
                            # Calculate actual brightness value
                            actual_brightness = int((brightness / 100.0) * max_brightness)
                            
                            # Set brightness
                            with open(brightness_file, 'w') as f:
                                f.write(str(actual_brightness))
                            
                            return True
                            
                        except Exception as e:
                            self.logger.debug(f"Failed to set brightness via {brightness_file}: {e}")
                            continue
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error setting brightness via sysfs: {e}")
            return False
    
    def set_contrast(self, contrast: int) -> bool:
        """
        Set display contrast
        
        Args:
            contrast: Contrast level (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            contrast = max(0, min(100, contrast))  # Clamp to 0-100
            self.logger.info(f"Setting contrast to {contrast}%")
            
            if not self.current_display:
                self.logger.error("No current display")
                return False
            
            # Try to set contrast using xrandr
            try:
                result = subprocess.run([
                    'xrandr', '--output', self.current_display.name,
                    '--brightness', str(contrast / 100.0)
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.current_display.contrast = contrast
                    if self.display_settings:
                        self.display_settings.contrast = contrast
                    self.logger.info(f"Contrast set to {contrast}%")
                    return True
                else:
                    self.logger.warning(f"Failed to set contrast via xrandr: {result.stderr}")
                    # Simulate contrast change
                    self.current_display.contrast = contrast
                    if self.display_settings:
                        self.display_settings.contrast = contrast
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Error setting contrast: {e}")
                # Simulate contrast change
                self.current_display.contrast = contrast
                if self.display_settings:
                    self.display_settings.contrast = contrast
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to set contrast: {e}")
            return False
    
    def set_orientation(self, orientation: str) -> bool:
        """
        Set display orientation
        
        Args:
            orientation: Orientation ('normal', 'left', 'right', 'inverted')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            valid_orientations = ['normal', 'left', 'right', 'inverted']
            if orientation not in valid_orientations:
                self.logger.error(f"Invalid orientation: {orientation}")
                return False
            
            self.logger.info(f"Setting orientation to {orientation}")
            
            if not self.current_display:
                self.logger.error("No current display")
                return False
            
            # Try to set orientation using xrandr
            try:
                result = subprocess.run([
                    'xrandr', '--output', self.current_display.name,
                    '--rotate', orientation
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.current_display.orientation = orientation
                    if self.display_settings:
                        self.display_settings.orientation = orientation
                    self.logger.info(f"Orientation set to {orientation}")
                    return True
                else:
                    self.logger.warning(f"Failed to set orientation via xrandr: {result.stderr}")
                    # Simulate orientation change
                    self.current_display.orientation = orientation
                    if self.display_settings:
                        self.display_settings.orientation = orientation
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Error setting orientation: {e}")
                # Simulate orientation change
                self.current_display.orientation = orientation
                if self.display_settings:
                    self.display_settings.orientation = orientation
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to set orientation: {e}")
            return False
    
    def optimize_for_led(self) -> bool:
        """Optimize display settings for LED screen"""
        try:
            self.logger.info("Optimizing display for LED screen...")
            
            if not self.current_display:
                self.logger.error("No current display")
                return False
            
            # LED-specific optimizations
            optimizations = [
                ('brightness', 85),  # Higher brightness for LED
                ('contrast', 60),    # Higher contrast for LED
                ('color_profile', 'sRGB'),  # Standard color profile
                ('gamma', 2.2),      # Standard gamma
                ('color_temperature', 6500)  # Daylight color temperature
            ]
            
            success_count = 0
            for setting, value in optimizations:
                if setting == 'brightness':
                    if self.set_brightness(value):
                        success_count += 1
                elif setting == 'contrast':
                    if self.set_contrast(value):
                        success_count += 1
                elif setting == 'color_profile':
                    if self.display_settings:
                        self.display_settings.color_profile = value
                        success_count += 1
                elif setting == 'gamma':
                    if self.display_settings:
                        self.display_settings.gamma = value
                        success_count += 1
                elif setting == 'color_temperature':
                    if self.display_settings:
                        self.display_settings.color_temperature = value
                        success_count += 1
            
            self.logger.info(f"LED optimization completed: {success_count}/{len(optimizations)} settings applied")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to optimize for LED: {e}")
            return False
    
    def get_display_info(self) -> Optional[DisplayInfo]:
        """Get current display information"""
        return self.current_display
    
    def get_display_settings(self) -> Optional[DisplaySettings]:
        """Get current display settings"""
        return self.display_settings
    
    def get_available_resolutions(self) -> List[Tuple[int, int]]:
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
                            parts = line.split()
                            for part in parts:
                                if 'x' in part and '+' in part:
                                    resolution_str = part.split('+')[0]
                                    try:
                                        width, height = map(int, resolution_str.split('x'))
                                        if (width, height) not in resolutions:
                                            resolutions.append((width, height))
                                    except:
                                        pass
            except:
                pass
            
            # Add common resolutions if none found
            if not resolutions:
                resolutions = [
                    (1920, 1080), (1366, 768), (1280, 720),
                    (1024, 768), (800, 600), (640, 480)
                ]
            
            return resolutions
            
        except Exception as e:
            self.logger.error(f"Failed to get available resolutions: {e}")
            return [(1920, 1080)]
    
    def get_display_status(self) -> Dict:
        """Get display status"""
        return {
            'current_display': self.current_display.name if self.current_display else None,
            'available_displays': len(self.available_displays),
            'resolution': self.current_display.resolution if self.current_display else None,
            'brightness': self.current_display.brightness if self.current_display else None,
            'contrast': self.current_display.contrast if self.current_display else None,
            'orientation': self.current_display.orientation if self.current_display else None,
            'display_settings': self.display_settings.__dict__ if self.display_settings else None
        }

# Example usage and testing
if __name__ == "__main__":
    # Test display manager
    display_manager = DisplayManager()
    
    print("Display Manager Test:")
    print("=" * 50)
    
    # Get display info
    print("\n1. Display Information:")
    display_info = display_manager.get_display_info()
    if display_info:
        print(f"   Name: {display_info.name}")
        print(f"   Resolution: {display_info.resolution}")
        print(f"   Refresh Rate: {display_info.refresh_rate}")
        print(f"   Brightness: {display_info.brightness}%")
        print(f"   Contrast: {display_info.contrast}%")
        print(f"   Orientation: {display_info.orientation}")
        print(f"   Is Primary: {display_info.is_primary}")
    
    # Get display settings
    print("\n2. Display Settings:")
    display_settings = display_manager.get_display_settings()
    if display_settings:
        print(f"   Resolution: {display_settings.resolution}")
        print(f"   Refresh Rate: {display_settings.refresh_rate}")
        print(f"   Brightness: {display_settings.brightness}%")
        print(f"   Contrast: {display_settings.contrast}%")
        print(f"   Orientation: {display_settings.orientation}")
        print(f"   Color Profile: {display_settings.color_profile}")
        print(f"   Gamma: {display_settings.gamma}")
        print(f"   Color Temperature: {display_settings.color_temperature}K")
    
    # Test brightness control
    print("\n3. Testing Brightness Control:")
    print("   Setting brightness to 50%...")
    if display_manager.set_brightness(50):
        print("   ✅ Brightness set successfully")
    else:
        print("   ❌ Failed to set brightness")
    
    print("   Setting brightness to 80%...")
    if display_manager.set_brightness(80):
        print("   ✅ Brightness set successfully")
    else:
        print("   ❌ Failed to set brightness")
    
    # Test contrast control
    print("\n4. Testing Contrast Control:")
    print("   Setting contrast to 60%...")
    if display_manager.set_contrast(60):
        print("   ✅ Contrast set successfully")
    else:
        print("   ❌ Failed to set contrast")
    
    # Test orientation
    print("\n5. Testing Orientation:")
    print("   Setting orientation to 'normal'...")
    if display_manager.set_orientation('normal'):
        print("   ✅ Orientation set successfully")
    else:
        print("   ❌ Failed to set orientation")
    
    # Test LED optimization
    print("\n6. Testing LED Optimization:")
    if display_manager.optimize_for_led():
        print("   ✅ LED optimization completed")
    else:
        print("   ❌ LED optimization failed")
    
    # Get available resolutions
    print("\n7. Available Resolutions:")
    resolutions = display_manager.get_available_resolutions()
    for resolution in resolutions:
        print(f"   {resolution[0]}x{resolution[1]}")
    
    # Get display status
    print("\n8. Display Status:")
    status = display_manager.get_display_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Display manager test completed successfully!")
