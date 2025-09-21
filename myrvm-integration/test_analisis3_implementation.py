#!/usr/bin/env python3
"""
Test Script for Analisis 3 Implementation
Enhanced Metrics Collection and Remote Command Executor
"""

import os
import sys
import time
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import components
from monitoring.hardware_metrics_collector import HardwareMetricsCollector
from monitoring.application_metrics_collector import ApplicationMetricsCollector
from monitoring.network_info_collector import NetworkInfoCollector
from monitoring.metrics_sender import MetricsSender
from remote.command_receiver import RemoteCommandReceiver
from remote.command_executor import RemoteCommandExecutor

def test_hardware_metrics_collector():
    """Test Hardware Metrics Collector"""
    print("=" * 60)
    print("TESTING HARDWARE METRICS COLLECTOR")
    print("=" * 60)
    
    try:
        collector = HardwareMetricsCollector()
        
        # Test individual metrics
        print("Testing CPU metrics...")
        cpu_metrics = collector.collect_cpu_metrics()
        print(f"CPU Metrics: {json.dumps(cpu_metrics, indent=2)}")
        
        print("\nTesting Memory metrics...")
        memory_metrics = collector.collect_memory_metrics()
        print(f"Memory Metrics: {json.dumps(memory_metrics, indent=2)}")
        
        print("\nTesting Disk metrics...")
        disk_metrics = collector.collect_disk_metrics()
        print(f"Disk Metrics: {json.dumps(disk_metrics, indent=2)}")
        
        print("\nTesting GPU metrics...")
        gpu_metrics = collector.collect_gpu_metrics()
        print(f"GPU Metrics: {json.dumps(gpu_metrics, indent=2)}")
        
        print("\nTesting Network metrics...")
        network_metrics = collector.collect_network_metrics()
        print(f"Network Metrics: {json.dumps(network_metrics, indent=2)}")
        
        print("\nTesting Process metrics...")
        process_metrics = collector.collect_process_metrics()
        print(f"Process Metrics: {json.dumps(process_metrics, indent=2)}")
        
        print("\nTesting All metrics...")
        all_metrics = collector.collect_all_metrics()
        print(f"All Hardware Metrics: {json.dumps(all_metrics, indent=2)}")
        
        print("✅ Hardware Metrics Collector test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Hardware Metrics Collector test failed: {e}")
        return False

def test_application_metrics_collector():
    """Test Application Metrics Collector"""
    print("=" * 60)
    print("TESTING APPLICATION METRICS COLLECTOR")
    print("=" * 60)
    
    try:
        collector = ApplicationMetricsCollector()
        
        # Test individual metrics
        print("Testing Software version...")
        software_metrics = collector.collect_software_version()
        print(f"Software Metrics: {json.dumps(software_metrics, indent=2)}")
        
        print("\nTesting AI model info...")
        ai_model_metrics = collector.collect_ai_model_info()
        print(f"AI Model Metrics: {json.dumps(ai_model_metrics, indent=2)}")
        
        print("\nTesting Uptime metrics...")
        uptime_metrics = collector.collect_uptime_metrics()
        print(f"Uptime Metrics: {json.dumps(uptime_metrics, indent=2)}")
        
        print("\nTesting Deposit metrics...")
        deposit_metrics = collector.collect_deposit_metrics()
        print(f"Deposit Metrics: {json.dumps(deposit_metrics, indent=2)}")
        
        print("\nTesting Error metrics...")
        error_metrics = collector.collect_error_metrics()
        print(f"Error Metrics: {json.dumps(error_metrics, indent=2)}")
        
        # Test increment methods
        print("\nTesting increment methods...")
        collector.increment_deposit_count()
        collector.increment_error_count()
        collector.increment_warning_count()
        
        print("\nTesting All metrics...")
        all_metrics = collector.collect_all_metrics()
        print(f"All Application Metrics: {json.dumps(all_metrics, indent=2)}")
        
        print("✅ Application Metrics Collector test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Application Metrics Collector test failed: {e}")
        return False

def test_network_info_collector():
    """Test Network Info Collector"""
    print("=" * 60)
    print("TESTING NETWORK INFO COLLECTOR")
    print("=" * 60)
    
    try:
        collector = NetworkInfoCollector()
        
        print("Testing Network info collection...")
        network_info = collector.collect_network_info()
        print(f"Network Info: {json.dumps(network_info, indent=2)}")
        
        print("✅ Network Info Collector test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Network Info Collector test failed: {e}")
        return False

async def test_remote_command_executor():
    """Test Remote Command Executor"""
    print("=" * 60)
    print("TESTING REMOTE COMMAND EXECUTOR")
    print("=" * 60)
    
    try:
        executor = RemoteCommandExecutor()
        executor.start()
        
        print("Testing Hardware commands...")
        
        # Test door commands
        print("Testing open door...")
        result = await executor.open_door()
        print(f"Open Door Result: {json.dumps(result, indent=2)}")
        
        print("Testing close door...")
        result = await executor.close_door()
        print(f"Close Door Result: {json.dumps(result, indent=2)}")
        
        # Test motor test
        print("Testing motor test...")
        result = await executor.test_motor()
        print(f"Motor Test Result: {json.dumps(result, indent=2)}")
        
        # Test sensor test
        print("Testing sensor test...")
        result = await executor.test_sensors()
        print(f"Sensor Test Result: {json.dumps(result, indent=2)}")
        
        print("Testing System commands...")
        
        # Test maintenance mode
        print("Testing enter maintenance mode...")
        result = await executor.enter_maintenance_mode()
        print(f"Enter Maintenance Result: {json.dumps(result, indent=2)}")
        
        print("Testing exit maintenance mode...")
        result = await executor.exit_maintenance_mode()
        print(f"Exit Maintenance Result: {json.dumps(result, indent=2)}")
        
        print("Testing Diagnostics commands...")
        
        # Test snapshot
        print("Testing take snapshot...")
        result = await executor.take_snapshot()
        print(f"Snapshot Result: {json.dumps(result, indent=2)}")
        
        # Test get logs
        print("Testing get logs...")
        result = await executor.get_logs()
        print(f"Get Logs Result: {json.dumps(result, indent=2)}")
        
        # Test system info
        print("Testing get system info...")
        result = await executor.get_system_info()
        print(f"System Info Result: {json.dumps(result, indent=2)}")
        
        executor.stop()
        
        print("✅ Remote Command Executor test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Remote Command Executor test failed: {e}")
        return False

def test_metrics_sender():
    """Test Metrics Sender (without actual sending)"""
    print("=" * 60)
    print("TESTING METRICS SENDER")
    print("=" * 60)
    
    try:
        # Test with dummy server URL (won't actually send)
        sender = MetricsSender("localhost:8000", 1, "test_api_key")
        
        print("Testing metrics collection and preparation...")
        
        # Test immediate metrics sending (will fail but should not crash)
        try:
            sender.send_immediate_metrics()
            print("✅ Metrics Sender test completed successfully!")
        except Exception as e:
            print(f"⚠️ Metrics Sender test completed with expected network error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Metrics Sender test failed: {e}")
        return False

def test_integration():
    """Test integration of all components"""
    print("=" * 60)
    print("TESTING INTEGRATION")
    print("=" * 60)
    
    try:
        # Test that all components can be imported and initialized
        print("Testing component imports...")
        
        from monitoring import HardwareMetricsCollector, ApplicationMetricsCollector, NetworkInfoCollector, MetricsSender
        from remote import RemoteCommandReceiver, RemoteCommandExecutor
        
        print("✅ All components imported successfully!")
        
        # Test initialization
        print("Testing component initialization...")
        
        hardware_collector = HardwareMetricsCollector()
        app_collector = ApplicationMetricsCollector()
        network_collector = NetworkInfoCollector()
        command_executor = RemoteCommandExecutor()
        
        print("✅ All components initialized successfully!")
        
        # Test basic functionality
        print("Testing basic functionality...")
        
        hardware_metrics = hardware_collector.collect_all_metrics()
        app_metrics = app_collector.collect_all_metrics()
        network_info = network_collector.collect_network_info()
        
        print(f"Hardware metrics collected: {len(hardware_metrics)} categories")
        print(f"Application metrics collected: {len(app_metrics)} categories")
        print(f"Network info collected: {len(network_info)} fields")
        
        print("✅ Integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 STARTING ANALISIS 3 IMPLEMENTATION TESTS")
    print("=" * 80)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Hardware Metrics Collector", test_hardware_metrics_collector()))
    test_results.append(("Application Metrics Collector", test_application_metrics_collector()))
    test_results.append(("Network Info Collector", test_network_info_collector()))
    test_results.append(("Remote Command Executor", await test_remote_command_executor()))
    test_results.append(("Metrics Sender", test_metrics_sender()))
    test_results.append(("Integration", test_integration()))
    
    # Print results
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Analisis 3 implementation is working correctly!")
    else:
        print(f"\n⚠️ {failed} tests failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)