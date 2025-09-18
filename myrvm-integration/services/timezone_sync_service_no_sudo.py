#!/usr/bin/env python3
"""
MyRVM Platform Integration - Timezone Synchronization Service (No Sudo)
User-level timezone management without system-level changes
"""

import os
import sys
import json
import logging
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pytz

class TimezoneSyncServiceNoSudo:
    """
    Timezone synchronization service for Jetson Orin Nano.
    User-level timezone management without system-level changes.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.current_timezone = None
        self.last_sync = None
        self.fallback_timezone = "Asia/Jakarta"  # UTC+7 Indonesia
        
        # Setup logging
        self._setup_logger()
        
        # Load last sync info
        self.sync_info_file = Path(__file__).parent.parent / "data" / "timezone_sync.json"
        self.sync_info_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_sync_info()
        
    def _setup_logger(self):
        """Setup logger for timezone sync service."""
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'timezone_sync_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def _load_sync_info(self):
        """Load last sync information."""
        try:
            if self.sync_info_file.exists():
                with open(self.sync_info_file, 'r') as f:
                    data = json.load(f)
                    self.current_timezone = data.get('timezone')
                    last_sync_str = data.get('last_sync')
                    if last_sync_str:
                        try:
                            self.last_sync = datetime.fromisoformat(last_sync_str)
                        except ValueError:
                            self.last_sync = None
                    else:
                        self.last_sync = None
                    self.logger.info(f"Loaded sync info: {self.current_timezone} at {self.last_sync}")
        except Exception as e:
            self.logger.warning(f"Could not load sync info: {e}")
            
    def _save_sync_info(self, timezone_info: Dict[str, Any]):
        """Save sync information."""
        try:
            data = {
                'timezone': timezone_info['timezone'],
                'country': timezone_info['country'],
                'city': timezone_info['city'],
                'ip': timezone_info['ip'],
                'last_sync': datetime.now().isoformat(),
                'sync_method': 'automatic_no_sudo'
            }
            
            with open(self.sync_info_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.current_timezone = timezone_info['timezone']
            self.last_sync = datetime.now()
            
            self.logger.info(f"Saved sync info: {timezone_info['timezone']}")
            
        except Exception as e:
            self.logger.error(f"Could not save sync info: {e}")
    
    def get_timezone_from_ip(self) -> Optional[Dict[str, Any]]:
        """Detect timezone based on public IP address."""
        try:
            self.logger.info("Detecting timezone from public IP...")
            
            # Try multiple IP geolocation services
            services = [
                'https://ipapi.co/json/',
                'https://ipinfo.io/json',
                'https://api.ipgeolocation.io/ipgeo?apiKey=free'
            ]
            
            for service_url in services:
                try:
                    response = requests.get(service_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract timezone info based on service
                        if 'ipapi.co' in service_url:
                            timezone = data.get('timezone')
                            country = data.get('country_name')
                            city = data.get('city')
                            ip = data.get('ip')
                        elif 'ipinfo.io' in service_url:
                            timezone = data.get('timezone')
                            country = data.get('country')
                            city = data.get('city')
                            ip = data.get('ip')
                        else:  # ipgeolocation.io
                            timezone = data.get('time_zone', {}).get('name')
                            country = data.get('country_name')
                            city = data.get('city')
                            ip = data.get('ip')
                        
                        if timezone:
                            result = {
                                'timezone': timezone,
                                'country': country,
                                'city': city,
                                'ip': ip,
                                'service': service_url
                            }
                            
                            self.logger.info(f"Timezone detected: {timezone} ({country}, {city})")
                            return result
                            
                except Exception as e:
                    self.logger.warning(f"Service {service_url} failed: {e}")
                    continue
            
            self.logger.error("All timezone detection services failed")
            return None
            
        except Exception as e:
            self.logger.error(f"Timezone detection failed: {e}")
            return None
    
    def set_user_timezone(self, timezone_str: str) -> bool:
        """Set user-level timezone (no sudo required)."""
        try:
            self.logger.info(f"Setting user timezone to: {timezone_str}")
            
            # Set TZ environment variable
            os.environ['TZ'] = timezone_str
            
            # Update time.tzset() if available
            try:
                import time
                time.tzset()
            except AttributeError:
                # time.tzset() not available on all systems
                pass
            
            # Verify timezone change
            current_tz = os.environ.get('TZ', 'UTC')
            if current_tz == timezone_str:
                self.logger.info(f"User timezone successfully set to: {current_tz}")
                return True
            else:
                self.logger.error(f"Timezone verification failed. Expected: {timezone_str}, Got: {current_tz}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set user timezone: {e}")
            return False
    
    def get_local_time(self) -> Dict[str, Any]:
        """Get local time information."""
        try:
            if self.current_timezone:
                current_tz = pytz.timezone(self.current_timezone)
            else:
                current_tz = pytz.timezone(self.fallback_timezone)
            
            local_time = datetime.now(current_tz)
            utc_time = datetime.now(pytz.UTC)
            
            return {
                'local_time': local_time.strftime('%Y-%m-%d %H:%M:%S'),
                'utc_time': utc_time.strftime('%Y-%m-%d %H:%M:%S'),
                'timezone': self.current_timezone or self.fallback_timezone,
                'utc_offset': local_time.strftime('%z'),
                'timezone_name': local_time.tzname()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get local time: {e}")
            return {
                'local_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'utc_time': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
                'timezone': self.fallback_timezone,
                'utc_offset': '+0700',
                'timezone_name': 'WIB'
            }
    
    def should_sync(self) -> bool:
        """Check if timezone should be synced."""
        if not self.last_sync:
            return True
        
        # Sync once per day
        time_since_sync = datetime.now() - self.last_sync
        return time_since_sync.days >= 1
    
    def auto_detect_and_sync(self) -> Tuple[bool, Dict[str, Any]]:
        """Automatically detect and sync timezone (user-level)."""
        try:
            self.logger.info("Starting automatic timezone detection and sync (no sudo)...")
            
            # Check if sync is needed
            if not self.should_sync():
                self.logger.info("Timezone sync not needed (synced within 24 hours)")
                return True, self.get_local_time()
            
            # Detect timezone
            timezone_info = self.get_timezone_from_ip()
            
            if timezone_info and timezone_info['timezone']:
                # Set user timezone
                if self.set_user_timezone(timezone_info['timezone']):
                    # Save sync info
                    self._save_sync_info(timezone_info)
                    
                    # Log to MyRVM Platform
                    self._log_timezone_change(timezone_info)
                    
                    self.logger.info(f"User timezone successfully synced to: {timezone_info['timezone']}")
                    return True, self.get_local_time()
                else:
                    self.logger.error("Failed to set user timezone")
                    return False, self.get_local_time()
            else:
                # Use fallback timezone
                self.logger.warning(f"Timezone detection failed, using fallback: {self.fallback_timezone}")
                
                if self.set_user_timezone(self.fallback_timezone):
                    fallback_info = {
                        'timezone': self.fallback_timezone,
                        'country': 'Indonesia',
                        'city': 'Jakarta',
                        'ip': 'fallback',
                        'service': 'fallback'
                    }
                    self._save_sync_info(fallback_info)
                    return True, self.get_local_time()
                else:
                    return False, self.get_local_time()
                    
        except Exception as e:
            self.logger.error(f"Auto sync failed: {e}")
            return False, self.get_local_time()
    
    def manual_sync(self) -> Tuple[bool, Dict[str, Any]]:
        """Manual timezone sync (triggered by dashboard button)."""
        try:
            self.logger.info("Starting manual timezone sync (no sudo)...")
            
            # Force sync regardless of last sync time
            self.last_sync = None
            
            return self.auto_detect_and_sync()
            
        except Exception as e:
            self.logger.error(f"Manual sync failed: {e}")
            return False, self.get_local_time()
    
    def _log_timezone_change(self, timezone_info: Dict[str, Any]):
        """Log timezone change to MyRVM Platform."""
        try:
            # This would integrate with MyRVM Platform API
            # For now, just log locally
            
            log_data = {
                'device_id': 'jetson_orin_nano',
                'event': 'timezone_sync',
                'timezone': timezone_info['timezone'],
                'country': timezone_info['country'],
                'city': timezone_info['city'],
                'ip': timezone_info['ip'],
                'timestamp': datetime.now().isoformat(),
                'sync_method': 'automatic_no_sudo'
            }
            
            # Save to local log file
            log_file = Path(__file__).parent.parent / "logs" / "timezone_changes.jsonl"
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_data) + '\n')
            
            self.logger.info(f"Timezone change logged: {timezone_info['timezone']}")
            
            # TODO: Send to MyRVM Platform API
            # api_client.send_timezone_info(log_data)
            
        except Exception as e:
            self.logger.error(f"Failed to log timezone change: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get timezone sync service status."""
        return {
            'current_timezone': self.current_timezone,
            'fallback_timezone': self.fallback_timezone,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'should_sync': self.should_sync(),
            'local_time': self.get_local_time(),
            'service_status': 'active_no_sudo',
            'user_tz': os.environ.get('TZ', 'UTC')
        }

# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Timezone Sync Service (No Sudo)')
    parser.add_argument('--auto-sync', action='store_true', help='Run automatic timezone sync')
    parser.add_argument('--manual-sync', action='store_true', help='Run manual timezone sync')
    parser.add_argument('--status', action='store_true', help='Show timezone service status')
    parser.add_argument('--test', action='store_true', help='Run test mode')
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "development_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create timezone sync service
    timezone_service = TimezoneSyncServiceNoSudo(config)
    
    if args.auto_sync:
        print("Running automatic timezone sync (no sudo)...")
        success, time_info = timezone_service.auto_detect_and_sync()
        
        if success:
            print("✅ Timezone sync successful!")
            print(f"Current timezone: {time_info['timezone']}")
            print(f"Local time: {time_info['local_time']}")
            print(f"UTC offset: {time_info['utc_offset']}")
        else:
            print("❌ Timezone sync failed!")
            sys.exit(1)
    
    elif args.manual_sync:
        print("Running manual timezone sync (no sudo)...")
        success, time_info = timezone_service.manual_sync()
        
        if success:
            print("✅ Manual timezone sync successful!")
            print(f"Current timezone: {time_info['timezone']}")
            print(f"Local time: {time_info['local_time']}")
            print(f"UTC offset: {time_info['utc_offset']}")
        else:
            print("❌ Manual timezone sync failed!")
            sys.exit(1)
    
    elif args.status:
        print("Timezone Service Status (No Sudo):")
        status = timezone_service.get_status()
        for key, value in status.items():
            print(f"{key}: {value}")
    
    elif args.test:
        print("Testing automatic timezone sync (no sudo)...")
        success, time_info = timezone_service.auto_detect_and_sync()
        
        if success:
            print("✅ Timezone sync successful!")
            print(f"Current timezone: {time_info['timezone']}")
            print(f"Local time: {time_info['local_time']}")
            print(f"UTC offset: {time_info['utc_offset']}")
        else:
            print("❌ Timezone sync failed!")
        
        # Show status
        print("\nTimezone Service Status:")
        status = timezone_service.get_status()
        for key, value in status.items():
            print(f"{key}: {value}")
    
    else:
        # Default: show help
        parser.print_help()
