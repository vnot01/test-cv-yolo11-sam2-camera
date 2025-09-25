#!/usr/bin/env python3
"""
Timezone Converter Utility
Converts server timestamps to local RVM timezone for display
"""

import re
from datetime import datetime, timezone
from typing import Optional, Union
import pytz


class TimezoneConverter:
    """Convert server timestamps to local RVM timezone"""
    
    def __init__(self, local_timezone: str = None):
        """
        Initialize timezone converter
        
        Args:
            local_timezone: Local timezone (e.g., 'Asia/Jakarta')
                          If None, will auto-detect
        """
        self.local_timezone = local_timezone or self._get_local_timezone()
        self.local_tz = pytz.timezone(self.local_timezone)
    
    def _get_local_timezone(self) -> str:
        """Get local timezone automatically"""
        try:
            # First try to get from system
            timezone = datetime.now().astimezone().tzinfo.zone
            if timezone:
                return timezone
        except Exception:
            pass
        
        # Fallback: Try to detect from IP location
        try:
            import requests
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    country = data.get('country', '')
                    if country == 'Indonesia':
                        return 'Asia/Jakarta'
                    elif country == 'Malaysia':
                        return 'Asia/Kuala_Lumpur'
                    elif country == 'Singapore':
                        return 'Asia/Singapore'
                    elif country == 'Thailand':
                        return 'Asia/Bangkok'
                    elif country == 'Philippines':
                        return 'Asia/Manila'
        except Exception:
            pass
        
        # Final fallback
        return "Asia/Jakarta"
    
    def convert_server_time(self, server_time: Union[str, datetime]) -> str:
        """
        Convert server timestamp to local timezone
        
        Args:
            server_time: Server timestamp (UTC or with timezone)
                       Can be string or datetime object
        
        Returns:
            Formatted local time string
        """
        try:
            # Parse server time
            if isinstance(server_time, str):
                dt = self._parse_timestamp(server_time)
            else:
                dt = server_time
            
            # Convert to local timezone
            if dt.tzinfo is None:
                # Assume UTC if no timezone info
                dt = dt.replace(tzinfo=timezone.utc)
            
            local_dt = dt.astimezone(self.local_tz)
            
            # Format for display
            return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
            
        except Exception as e:
            print(f"Error converting time: {e}")
            return str(server_time)  # Return original if conversion fails
    
    def convert_server_time_iso(self, server_time: Union[str, datetime]) -> str:
        """
        Convert server timestamp to local timezone in ISO format
        
        Args:
            server_time: Server timestamp (UTC or with timezone)
        
        Returns:
            ISO formatted local time string
        """
        try:
            # Parse server time
            if isinstance(server_time, str):
                dt = self._parse_timestamp(server_time)
            else:
                dt = server_time
            
            # Convert to local timezone
            if dt.tzinfo is None:
                # Assume UTC if no timezone info
                dt = dt.replace(tzinfo=timezone.utc)
            
            local_dt = dt.astimezone(self.local_tz)
            
            # Return ISO format with timezone
            return local_dt.isoformat()
            
        except Exception as e:
            print(f"Error converting time: {e}")
            return str(server_time)
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse various timestamp formats
        
        Args:
            timestamp_str: Timestamp string in various formats
        
        Returns:
            datetime object
        """
        # Remove microseconds if present
        timestamp_str = re.sub(r'\.\d+', '', timestamp_str)
        
        # Common formats to try
        formats = [
            '%Y-%m-%dT%H:%M:%SZ',           # 2025-09-25T03:16:50Z
            '%Y-%m-%dT%H:%M:%S%z',          # 2025-09-25T03:16:50+00:00
            '%Y-%m-%dT%H:%M:%S',            # 2025-09-25T03:16:50
            '%Y-%m-%d %H:%M:%S',            # 2025-09-25 03:16:50
            '%Y-%m-%d %H:%M:%S.%f',         # 2025-09-25 03:16:50.123456
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # If all formats fail, try ISO format
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Unable to parse timestamp: {timestamp_str}")
    
    def get_local_timezone_info(self) -> dict:
        """
        Get local timezone information
        
        Returns:
            Dictionary with timezone info
        """
        now = datetime.now(self.local_tz)
        return {
            'timezone': self.local_timezone,
            'offset': now.strftime('%z'),
            'offset_hours': now.utcoffset().total_seconds() / 3600,
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'current_time_iso': now.isoformat()
        }
    
    def format_relative_time(self, server_time: Union[str, datetime]) -> str:
        """
        Format server time as relative time (e.g., "2 minutes ago")
        
        Args:
            server_time: Server timestamp
        
        Returns:
            Relative time string
        """
        try:
            # Parse server time
            if isinstance(server_time, str):
                dt = self._parse_timestamp(server_time)
            else:
                dt = server_time
            
            # Convert to local timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            
            local_dt = dt.astimezone(self.local_tz)
            now = datetime.now(self.local_tz)
            
            # Calculate difference
            diff = now - local_dt
            
            if diff.total_seconds() < 60:
                return "Just now"
            elif diff.total_seconds() < 3600:
                minutes = int(diff.total_seconds() / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif diff.total_seconds() < 86400:
                hours = int(diff.total_seconds() / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(diff.total_seconds() / 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
                
        except Exception as e:
            print(f"Error formatting relative time: {e}")
            return "Unknown"


# Global instance for easy access
timezone_converter = TimezoneConverter()


def convert_server_time(server_time: Union[str, datetime]) -> str:
    """
    Quick function to convert server time to local timezone
    
    Args:
        server_time: Server timestamp
    
    Returns:
        Formatted local time string
    """
    return timezone_converter.convert_server_time(server_time)


def convert_server_time_iso(server_time: Union[str, datetime]) -> str:
    """
    Quick function to convert server time to local timezone in ISO format
    
    Args:
        server_time: Server timestamp
    
    Returns:
        ISO formatted local time string
    """
    return timezone_converter.convert_server_time_iso(server_time)


def format_relative_time(server_time: Union[str, datetime]) -> str:
    """
    Quick function to format server time as relative time
    
    Args:
        server_time: Server timestamp
    
    Returns:
        Relative time string
    """
    return timezone_converter.format_relative_time(server_time)


if __name__ == "__main__":
    # Test the timezone converter
    converter = TimezoneConverter()
    
    print("=== Timezone Converter Test ===")
    print(f"Local timezone: {converter.local_timezone}")
    print(f"Timezone info: {converter.get_local_timezone_info()}")
    
    # Test with various server timestamps
    test_times = [
        "2025-09-25T03:16:50.000000Z",
        "2025-09-25T03:16:50Z",
        "2025-09-25T03:16:50+00:00",
        "2025-09-25T03:16:50",
    ]
    
    print("\n=== Server Time Conversion Test ===")
    for server_time in test_times:
        local_time = converter.convert_server_time(server_time)
        relative_time = converter.format_relative_time(server_time)
        print(f"Server: {server_time}")
        print(f"Local:  {local_time}")
        print(f"Relative: {relative_time}")
        print()
