#!/usr/bin/env python3
"""
Backup & Recovery Test Script
Test Stage 4 backup and recovery for MyRVM Platform Integration
"""

import os
import json
import time
import logging
import sys
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "backup"))

from backup_manager import BackupManager
from recovery_manager import RecoveryManager
from backup_monitor import BackupMonitor

def test_backup_manager():
    """Test backup manager functionality"""
    print("\n💾 Testing Backup Manager...")
    
    try:
        # Create test configuration
        config = {
            'backup_enabled': True,
            'backup_interval': 10,  # 10 seconds for testing
            'retention_days': 7,
            'compression_enabled': True,
            'encryption_enabled': True,
            'backup_dir': 'test_backups'
        }
        
        # Initialize backup manager
        backup_manager = BackupManager(config)
        
        # Test backup strategies initialization
        if backup_manager.backup_strategies:
            print(f"   ✅ Backup strategies initialized: {len(backup_manager.backup_strategies)} strategies")
        else:
            print("   ❌ Backup strategies initialization failed")
            return False
        
        # Test manual backup execution
        print("   Testing manual backup execution...")
        
        # Test database backup
        db_result = backup_manager.run_manual_backup('database')
        if db_result.get('success', False):
            print("   ✅ Database backup working")
            backup_file = db_result.get('backup_file', 'N/A')
            print(f"   ✅ Backup file: {backup_file}")
            # Check if backup file exists
            if os.path.exists(backup_file):
                print("   ✅ Backup file exists and is accessible")
            else:
                print(f"   ⚠️ Backup file not found at expected location: {backup_file}")
                # Check if there are any backup files in the directory
                backup_dir = backup_manager.database_backup_dir
                if backup_dir.exists():
                    backup_files = list(backup_dir.glob('*'))
                    if backup_files:
                        print(f"   ✅ Found {len(backup_files)} backup files in directory")
                        print(f"   ✅ Latest backup: {backup_files[-1].name}")
                    else:
                        print("   ❌ No backup files found in directory")
                        return False
                else:
                    print("   ❌ Backup directory does not exist")
                    return False
        else:
            print(f"   ❌ Database backup failed: {db_result.get('error', 'Unknown error')}")
            return False
        
        # Test config backup
        config_result = backup_manager.run_manual_backup('config')
        if config_result.get('success', False):
            print("   ✅ Config backup working")
        else:
            print(f"   ❌ Config backup failed: {config_result.get('error', 'Unknown error')}")
            return False
        
        # Test logs backup
        logs_result = backup_manager.run_manual_backup('logs')
        if logs_result.get('success', False):
            print("   ✅ Logs backup working")
        else:
            print(f"   ❌ Logs backup failed: {logs_result.get('error', 'Unknown error')}")
            return False
        
        # Test application backup
        app_result = backup_manager.run_manual_backup('application')
        if app_result.get('success', False):
            print("   ✅ Application backup working")
        else:
            print(f"   ❌ Application backup failed: {app_result.get('error', 'Unknown error')}")
            return False
        
        # Test backup status
        status = backup_manager.get_backup_status()
        if status and 'enabled' in status:
            print("   ✅ Backup status working")
        else:
            print("   ❌ Backup status failed")
            return False
        
        # Test backup history
        history = backup_manager.get_backup_history(10)
        if history:
            print(f"   ✅ Backup history working: {len(history)} entries")
        else:
            print("   ❌ Backup history failed")
            return False
        
        # Test backup report
        report = backup_manager.get_backup_report()
        if report and 'Backup Manager Report' in report:
            print("   ✅ Backup report working")
        else:
            print("   ❌ Backup report failed")
            return False
        
        print("   ✅ Backup Manager test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Backup Manager test failed: {e}")
        return False

def test_recovery_manager():
    """Test recovery manager functionality"""
    print("\n🔄 Testing Recovery Manager...")
    
    try:
        # Create test configuration
        config = {
            'recovery_enabled': True,
            'recovery_timeout': 300,
            'auto_recovery': False
        }
        
        # Initialize recovery manager
        recovery_manager = RecoveryManager(config)
        
        # Test recovery procedures initialization
        if recovery_manager.recovery_procedures:
            print(f"   ✅ Recovery procedures initialized: {len(recovery_manager.recovery_procedures)} procedures")
        else:
            print("   ❌ Recovery procedures initialization failed")
            return False
        
        # Test recovery testing (without actual recovery)
        print("   Testing recovery procedures...")
        
        # Test database recovery
        db_test = recovery_manager.test_recovery('database')
        if db_test.get('success', False):
            print("   ✅ Database recovery test working")
        else:
            print(f"   ❌ Database recovery test failed: {db_test.get('error', 'Unknown error')}")
            return False
        
        # Test config recovery
        config_test = recovery_manager.test_recovery('config')
        if config_test.get('success', False):
            print("   ✅ Config recovery test working")
        else:
            print(f"   ❌ Config recovery test failed: {config_test.get('error', 'Unknown error')}")
            return False
        
        # Test logs recovery
        logs_test = recovery_manager.test_recovery('logs')
        if logs_test.get('success', False):
            print("   ✅ Logs recovery test working")
        else:
            print(f"   ❌ Logs recovery test failed: {logs_test.get('error', 'Unknown error')}")
            return False
        
        # Test application recovery
        app_test = recovery_manager.test_recovery('application')
        if app_test.get('success', False):
            print("   ✅ Application recovery test working")
        else:
            print(f"   ❌ Application recovery test failed: {app_test.get('error', 'Unknown error')}")
            return False
        
        # Test recovery status
        status = recovery_manager.get_recovery_status()
        if status and 'enabled' in status:
            print("   ✅ Recovery status working")
        else:
            print("   ❌ Recovery status failed")
            return False
        
        # Test recovery history
        history = recovery_manager.get_recovery_history(10)
        if history is not None:
            print(f"   ✅ Recovery history working: {len(history)} entries")
        else:
            print("   ❌ Recovery history failed")
            return False
        
        # Test recovery report
        report = recovery_manager.get_recovery_report()
        if report and 'Recovery Manager Report' in report:
            print("   ✅ Recovery report working")
        else:
            print("   ❌ Recovery report failed")
            return False
        
        print("   ✅ Recovery Manager test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Recovery Manager test failed: {e}")
        return False

def test_backup_monitor():
    """Test backup monitor functionality"""
    print("\n📊 Testing Backup Monitor...")
    
    try:
        # Create test configuration
        config = {
            'backup_monitoring_enabled': True,
            'backup_monitoring_interval': 10,  # 10 seconds for testing
            'backup_monitoring_rules': {
                'backup_failure': {
                    'enabled': True,
                    'severity': 'critical',
                    'threshold': 1
                },
                'storage_usage_high': {
                    'enabled': True,
                    'severity': 'warning',
                    'threshold': 80
                }
            }
        }
        
        # Initialize backup monitor
        backup_monitor = BackupMonitor(config)
        
        # Test monitoring rules initialization
        if backup_monitor.monitoring_rules:
            print(f"   ✅ Monitoring rules initialized: {len(backup_monitor.monitoring_rules)} rules")
        else:
            print("   ❌ Monitoring rules initialization failed")
            return False
        
        # Test monitoring data collection
        print("   Testing monitoring data collection...")
        
        # Test backup status collection
        backup_monitor._collect_backup_status()
        backup_status = backup_monitor.monitoring_data.get('backup_status', {})
        if backup_status:
            print("   ✅ Backup status collection working")
        else:
            print("   ❌ Backup status collection failed")
            return False
        
        # Test storage usage collection
        backup_monitor._collect_storage_usage()
        storage_usage = backup_monitor.monitoring_data.get('storage_usage', {})
        if storage_usage:
            print("   ✅ Storage usage collection working")
        else:
            print("   ❌ Storage usage collection failed")
            return False
        
        # Test performance metrics collection
        backup_monitor._collect_performance_metrics()
        performance_metrics = backup_monitor.monitoring_data.get('performance_metrics', {})
        if performance_metrics:
            print("   ✅ Performance metrics collection working")
        else:
            print("   ❌ Performance metrics collection failed")
            return False
        
        # Test monitoring status
        status = backup_monitor.get_monitoring_status()
        if status and 'enabled' in status:
            print("   ✅ Monitoring status working")
        else:
            print("   ❌ Monitoring status failed")
            return False
        
        # Test monitoring data
        monitoring_data = backup_monitor.get_monitoring_data()
        if monitoring_data:
            print("   ✅ Monitoring data working")
        else:
            print("   ❌ Monitoring data failed")
            return False
        
        # Test monitoring report
        report = backup_monitor.get_monitoring_report()
        if report and 'Backup Monitor Report' in report:
            print("   ✅ Monitoring report working")
        else:
            print("   ❌ Monitoring report failed")
            return False
        
        print("   ✅ Backup Monitor test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Backup Monitor test failed: {e}")
        return False

def test_backup_recovery_integration():
    """Test integration of backup and recovery components"""
    print("\n🔗 Testing Backup & Recovery Integration...")
    
    try:
        # Create comprehensive configuration
        config = {
            'backup_enabled': True,
            'backup_interval': 10,
            'retention_days': 7,
            'compression_enabled': True,
            'encryption_enabled': True,
            'backup_dir': 'test_backups',
            'recovery_enabled': True,
            'recovery_timeout': 300,
            'backup_monitoring_enabled': True,
            'backup_monitoring_interval': 10
        }
        
        # Initialize all components
        backup_manager = BackupManager(config)
        recovery_manager = RecoveryManager(config, backup_manager)
        backup_monitor = BackupMonitor(config, backup_manager)
        
        print("   ✅ All components initialized successfully")
        
        # Test backup execution
        print("   Testing backup execution...")
        db_result = backup_manager.run_manual_backup('database')
        if db_result.get('success', False):
            print("   ✅ Backup execution working")
        else:
            print(f"   ❌ Backup execution failed: {db_result.get('error', 'Unknown error')}")
            return False
        
        # Test recovery testing
        print("   Testing recovery procedures...")
        recovery_test = recovery_manager.test_recovery('database')
        if recovery_test.get('success', False):
            print("   ✅ Recovery testing working")
        else:
            print(f"   ❌ Recovery testing failed: {recovery_test.get('error', 'Unknown error')}")
            return False
        
        # Test monitoring integration
        print("   Testing monitoring integration...")
        backup_monitor._collect_backup_status()
        monitoring_data = backup_monitor.get_monitoring_data()
        if monitoring_data:
            print("   ✅ Monitoring integration working")
        else:
            print("   ❌ Monitoring integration failed")
            return False
        
        # Test component communication
        print("   Testing component communication...")
        backup_status = backup_manager.get_backup_status()
        recovery_status = recovery_manager.get_recovery_status()
        monitoring_status = backup_monitor.get_monitoring_status()
        
        if backup_status and recovery_status and monitoring_status:
            print("   ✅ Component communication working")
        else:
            print("   ❌ Component communication failed")
            return False
        
        print("   ✅ Backup & Recovery Integration test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Backup & Recovery Integration test failed: {e}")
        return False

def test_backup_performance():
    """Test backup system performance"""
    print("\n⚡ Testing Backup Performance...")
    
    try:
        # Create test configuration
        config = {
            'backup_enabled': True,
            'backup_interval': 1,  # 1 second for testing
            'retention_days': 1,
            'compression_enabled': True,
            'encryption_enabled': True,
            'backup_dir': 'test_backups'
        }
        
        # Initialize backup manager
        backup_manager = BackupManager(config)
        
        # Test backup performance
        print("   Testing backup performance...")
        
        start_time = time.time()
        
        # Run multiple backups
        backup_results = []
        for i in range(3):
            result = backup_manager.run_manual_backup('config')
            backup_results.append(result)
            time.sleep(0.5)  # Small delay between backups
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Check results
        successful_backups = sum(1 for result in backup_results if result.get('success', False))
        total_backups = len(backup_results)
        
        if successful_backups == total_backups:
            print(f"   ✅ Backup performance test completed")
            print(f"   ✅ Total time: {total_time:.2f}s")
            print(f"   ✅ Successful backups: {successful_backups}/{total_backups}")
            print(f"   ✅ Average time per backup: {total_time/total_backups:.2f}s")
        else:
            print(f"   ❌ Backup performance test failed")
            print(f"   ❌ Successful backups: {successful_backups}/{total_backups}")
            return False
        
        # Test backup history performance
        history_start = time.time()
        history = backup_manager.get_backup_history(100)
        history_time = time.time() - history_start
        
        if history:
            print(f"   ✅ Backup history performance: {history_time:.3f}s for {len(history)} entries")
        else:
            print("   ❌ Backup history performance failed")
            return False
        
        print("   ✅ Backup Performance test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Backup Performance test failed: {e}")
        return False

def test_backup_recovery_scenarios():
    """Test various backup and recovery scenarios"""
    print("\n🎭 Testing Backup & Recovery Scenarios...")
    
    try:
        # Create test configuration
        config = {
            'backup_enabled': True,
            'backup_interval': 10,
            'retention_days': 7,
            'compression_enabled': True,
            'encryption_enabled': True,
            'backup_dir': 'test_backups',
            'recovery_enabled': True,
            'recovery_timeout': 300
        }
        
        # Initialize components
        backup_manager = BackupManager(config)
        recovery_manager = RecoveryManager(config, backup_manager)
        
        # Scenario 1: Full backup cycle
        print("   Testing full backup cycle...")
        backup_result = backup_manager.run_manual_backup('application')
        if backup_result.get('success', False):
            print("   ✅ Full backup cycle working")
        else:
            print(f"   ❌ Full backup cycle failed: {backup_result.get('error', 'Unknown error')}")
            return False
        
        # Scenario 2: Recovery testing
        print("   Testing recovery scenarios...")
        recovery_test = recovery_manager.test_recovery('application')
        if recovery_test.get('success', False):
            print("   ✅ Recovery scenarios working")
        else:
            print(f"   ❌ Recovery scenarios failed: {recovery_test.get('error', 'Unknown error')}")
            return False
        
        # Scenario 3: Multiple backup types
        print("   Testing multiple backup types...")
        backup_types = ['database', 'config', 'logs', 'application']
        successful_types = 0
        
        for backup_type in backup_types:
            result = backup_manager.run_manual_backup(backup_type)
            if result.get('success', False):
                successful_types += 1
        
        if successful_types == len(backup_types):
            print(f"   ✅ Multiple backup types working: {successful_types}/{len(backup_types)}")
        else:
            print(f"   ❌ Multiple backup types failed: {successful_types}/{len(backup_types)}")
            return False
        
        # Scenario 4: Backup status monitoring
        print("   Testing backup status monitoring...")
        status = backup_manager.get_backup_status()
        history = backup_manager.get_backup_history(10)
        
        if status and history:
            print("   ✅ Backup status monitoring working")
        else:
            print("   ❌ Backup status monitoring failed")
            return False
        
        print("   ✅ Backup & Recovery Scenarios test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Backup & Recovery Scenarios test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Stage 4: Backup & Recovery Test")
    print("=" * 60)
    
    test_results = {
        'backup_manager': False,
        'recovery_manager': False,
        'backup_monitor': False,
        'backup_recovery_integration': False,
        'backup_performance': False,
        'backup_recovery_scenarios': False
    }
    
    # Run individual component tests
    test_results['backup_manager'] = test_backup_manager()
    test_results['recovery_manager'] = test_recovery_manager()
    test_results['backup_monitor'] = test_backup_monitor()
    
    # Run integration tests
    test_results['backup_recovery_integration'] = test_backup_recovery_integration()
    test_results['backup_performance'] = test_backup_performance()
    test_results['backup_recovery_scenarios'] = test_backup_recovery_scenarios()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All backup and recovery tests passed!")
        print("✅ Stage 4: Backup & Recovery - COMPLETED")
    else:
        print("⚠️  Some tests failed. Please check the logs for details.")
    
    # Save test results
    results_file = Path(__file__).parent.parent / 'logs' / f'backup_recovery_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'test_results': test_results,
            'timestamp': datetime.now().isoformat(),
            'passed_tests': passed_tests,
            'total_tests': total_tests
        }, f, indent=2)
    
    print(f"📝 Test results saved to: {results_file}")

if __name__ == "__main__":
    main()
