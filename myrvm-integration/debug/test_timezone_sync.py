#!/usr/bin/env python3
"""
Test script for timezone synchronization service
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.timezone_sync_service import TimezoneSyncService

def test_timezone_detection():
    """Test timezone detection without system changes."""
    print("=" * 60)
    print("TESTING TIMEZONE DETECTION SERVICE")
    print("=" * 60)
    
    # Load configuration
    config_path = project_root / "config" / "development_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Create service
    timezone_service = TimezoneSyncService(config)
    
    # Test timezone detection
    print("\n1. Testing timezone detection...")
    timezone_info = timezone_service.get_timezone_from_ip()
    
    if timezone_info:
        print("✅ Timezone detection successful!")
        print(f"   Public IP: {timezone_info['ip']}")
        print(f"   Country: {timezone_info['country']}")
        print(f"   City: {timezone_info['city']}")
        print(f"   Timezone: {timezone_info['timezone']}")
        print(f"   Service: {timezone_info['service']}")
    else:
        print("❌ Timezone detection failed!")
    
    # Test local time
    print("\n2. Testing local time...")
    local_time = timezone_service.get_local_time()
    print("✅ Local time information:")
    for key, value in local_time.items():
        print(f"   {key}: {value}")
    
    # Test status
    print("\n3. Testing service status...")
    status = timezone_service.get_status()
    print("✅ Service status:")
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Test should sync
    print("\n4. Testing sync logic...")
    should_sync = timezone_service.should_sync()
    print(f"   Should sync: {should_sync}")
    
    print("\n" + "=" * 60)
    print("TIMEZONE DETECTION TEST COMPLETED")
    print("=" * 60)
    
    return timezone_info is not None

def test_manual_sync():
    """Test manual sync (without sudo)."""
    print("\n" + "=" * 60)
    print("TESTING MANUAL SYNC (DETECTION ONLY)")
    print("=" * 60)
    
    # Load configuration
    config_path = project_root / "config" / "development_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Create service
    timezone_service = TimezoneSyncService(config)
    
    # Test manual sync
    print("\nTesting manual sync...")
    success, time_info = timezone_service.manual_sync()
    
    if success:
        print("✅ Manual sync successful!")
        print(f"   Timezone: {time_info['timezone']}")
        print(f"   Local time: {time_info['local_time']}")
        print(f"   UTC offset: {time_info['utc_offset']}")
    else:
        print("❌ Manual sync failed!")
    
    return success

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test timezone detection
    detection_success = test_timezone_detection()
    
    # Test manual sync
    sync_success = test_manual_sync()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Timezone Detection: {'✅ PASSED' if detection_success else '❌ FAILED'}")
    print(f"Manual Sync: {'✅ PASSED' if sync_success else '❌ FAILED'}")
    print("=" * 60)
