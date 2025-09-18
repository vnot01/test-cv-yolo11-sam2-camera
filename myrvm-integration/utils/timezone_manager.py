#!/usr/bin/env python3
"""
MyRVM Platform Integration - Timezone Manager Utility
Provides timezone-aware datetime functions for all modules
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import pytz

class TimezoneManager:
    """
    Centralized timezone management utility.
    Provides timezone-aware datetime functions for all modules.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any] = None):
        if self._initialized:
            return
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        self.current_timezone = None
        self.fallback_timezone = "Asia/Jakarta"  # UTC+7 Indonesia
        
        # Load timezone info
        self._load_timezone_info()
        
        self._initialized = True
    
    def _load_timezone_info(self):
        """Load current timezone information."""
        try:
            # Try to load from timezone sync data
            sync_info_file = Path(__file__).parent.parent / "data" / "timezone_sync.json"
            if sync_info_file.exists():
                with open(sync_info_file, 'r') as f:
                    data = json.load(f)
                    self.current_timezone = data.get('timezone')
                    self.logger.info(f"Loaded timezone from sync data: {self.current_timezone}")
            else:
                # Try to get from system
                import subprocess
                try:
                    result = subprocess.run(
                        ['timedatectl', 'show', '--property=Timezone', '--value'],
                        capture_output=True, text=True, check=True
                    )
                    self.current_timezone = result.stdout.strip()
                    self.logger.info(f"Loaded timezone from system: {self.current_timezone}")
                except Exception as e:
                    self.logger.warning(f"Could not get system timezone: {e}")
                    self.current_timezone = self.fallback_timezone
                    
        except Exception as e:
            self.logger.warning(f"Could not load timezone info: {e}")
            self.current_timezone = self.fallback_timezone
    
    def get_current_timezone(self) -> str:
        """Get current timezone."""
        return self.current_timezone or self.fallback_timezone
    
    def get_timezone_object(self) -> pytz.timezone:
        """Get timezone object."""
        try:
            return pytz.timezone(self.get_current_timezone())
        except Exception as e:
            self.logger.warning(f"Invalid timezone {self.get_current_timezone()}, using fallback: {e}")
            return pytz.timezone(self.fallback_timezone)
    
    def now(self) -> datetime:
        """Get current datetime in local timezone."""
        try:
            tz = self.get_timezone_object()
            return datetime.now(tz)
        except Exception as e:
            self.logger.warning(f"Error getting local time: {e}")
            return datetime.now(pytz.timezone(self.fallback_timezone))
    
    def utc_now(self) -> datetime:
        """Get current datetime in UTC."""
        return datetime.now(pytz.UTC)
    
    def to_local(self, dt: datetime) -> datetime:
        """Convert datetime to local timezone."""
        try:
            if dt.tzinfo is None:
                # Assume UTC if no timezone info
                dt = pytz.UTC.localize(dt)
            
            tz = self.get_timezone_object()
            return dt.astimezone(tz)
        except Exception as e:
            self.logger.warning(f"Error converting to local time: {e}")
            return dt
    
    def to_utc(self, dt: datetime) -> datetime:
        """Convert datetime to UTC."""
        try:
            if dt.tzinfo is None:
                # Assume local timezone if no timezone info
                tz = self.get_timezone_object()
                dt = tz.localize(dt)
            
            return dt.astimezone(pytz.UTC)
        except Exception as e:
            self.logger.warning(f"Error converting to UTC: {e}")
            return dt
    
    def format_datetime(self, dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime in local timezone."""
        if dt is None:
            dt = self.now()
        else:
            dt = self.to_local(dt)
        
        return dt.strftime(format_str)
    
    def format_utc_datetime(self, dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime in UTC."""
        if dt is None:
            dt = self.utc_now()
        else:
            dt = self.to_utc(dt)
        
        return dt.strftime(format_str)
    
    def parse_datetime(self, date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
        """Parse datetime string in local timezone."""
        try:
            dt = datetime.strptime(date_str, format_str)
            tz = self.get_timezone_object()
            return tz.localize(dt)
        except Exception as e:
            self.logger.warning(f"Error parsing datetime: {e}")
            return datetime.now(self.get_timezone_object())
    
    def parse_utc_datetime(self, date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
        """Parse datetime string in UTC."""
        try:
            dt = datetime.strptime(date_str, format_str)
            return pytz.UTC.localize(dt)
        except Exception as e:
            self.logger.warning(f"Error parsing UTC datetime: {e}")
            return datetime.now(pytz.UTC)
    
    def get_timestamp(self, dt: datetime = None) -> float:
        """Get timestamp from datetime."""
        if dt is None:
            dt = self.now()
        
        return dt.timestamp()
    
    def from_timestamp(self, timestamp: float) -> datetime:
        """Create datetime from timestamp in local timezone."""
        dt = datetime.fromtimestamp(timestamp, tz=self.get_timezone_object())
        return dt
    
    def get_utc_offset(self) -> str:
        """Get UTC offset string."""
        try:
            now = self.now()
            return now.strftime('%z')
        except Exception as e:
            self.logger.warning(f"Error getting UTC offset: {e}")
            return "+0700"  # Default to Indonesia time
    
    def get_timezone_name(self) -> str:
        """Get timezone name."""
        try:
            now = self.now()
            return now.tzname()
        except Exception as e:
            self.logger.warning(f"Error getting timezone name: {e}")
            return "WIB"  # Default to Indonesia time
    
    def is_dst(self) -> bool:
        """Check if daylight saving time is active."""
        try:
            now = self.now()
            return now.dst() != timedelta(0)
        except Exception as e:
            self.logger.warning(f"Error checking DST: {e}")
            return False
    
    def get_timezone_info(self) -> Dict[str, Any]:
        """Get comprehensive timezone information."""
        try:
            now = self.now()
            utc_now = self.utc_now()
            
            return {
                'timezone': self.get_current_timezone(),
                'timezone_name': self.get_timezone_name(),
                'utc_offset': self.get_utc_offset(),
                'local_time': self.format_datetime(now),
                'utc_time': self.format_utc_datetime(utc_now),
                'timestamp': self.get_timestamp(now),
                'is_dst': self.is_dst(),
                'fallback_timezone': self.fallback_timezone
            }
        except Exception as e:
            self.logger.error(f"Error getting timezone info: {e}")
            return {
                'timezone': self.fallback_timezone,
                'timezone_name': 'WIB',
                'utc_offset': '+0700',
                'local_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'utc_time': datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': time.time(),
                'is_dst': False,
                'fallback_timezone': self.fallback_timezone
            }

# Global instance
_timezone_manager = None

def get_timezone_manager(config: Dict[str, Any] = None) -> TimezoneManager:
    """Get global timezone manager instance."""
    global _timezone_manager
    if _timezone_manager is None:
        _timezone_manager = TimezoneManager(config)
    return _timezone_manager

# Convenience functions
def now() -> datetime:
    """Get current datetime in local timezone."""
    return get_timezone_manager().now()

def utc_now() -> datetime:
    """Get current datetime in UTC."""
    return get_timezone_manager().utc_now()

def format_datetime(dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime in local timezone."""
    return get_timezone_manager().format_datetime(dt, format_str)

def format_utc_datetime(dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime in UTC."""
    return get_timezone_manager().format_utc_datetime(dt, format_str)

def get_timestamp(dt: datetime = None) -> float:
    """Get timestamp from datetime."""
    return get_timezone_manager().get_timestamp(dt)

def from_timestamp(timestamp: float) -> datetime:
    """Create datetime from timestamp in local timezone."""
    return get_timezone_manager().from_timestamp(timestamp)

def get_timezone_info() -> Dict[str, Any]:
    """Get comprehensive timezone information."""
    return get_timezone_manager().get_timezone_info()

# Example usage and testing
if __name__ == "__main__":
    import time
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test timezone manager
    print("Testing Timezone Manager...")
    
    tz_manager = TimezoneManager()
    
    print(f"Current timezone: {tz_manager.get_current_timezone()}")
    print(f"Local time: {tz_manager.format_datetime()}")
    print(f"UTC time: {tz_manager.format_utc_datetime()}")
    print(f"UTC offset: {tz_manager.get_utc_offset()}")
    print(f"Timezone name: {tz_manager.get_timezone_name()}")
    print(f"Is DST: {tz_manager.is_dst()}")
    
    print("\nTimezone Info:")
    info = tz_manager.get_timezone_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\nConvenience functions:")
    print(f"now(): {now()}")
    print(f"utc_now(): {utc_now()}")
    print(f"format_datetime(): {format_datetime()}")
    print(f"get_timestamp(): {get_timestamp()}")
