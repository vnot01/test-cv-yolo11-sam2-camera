#!/usr/bin/env python3
"""
Simple Backup & Recovery Test Script
Test Stage 4 backup and recovery for MyRVM Platform Integration
"""

import os
import json
import time
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "backup"))

from backup_manager import BackupManager
from recovery_manager import RecoveryManager
from backup_monitor import BackupMonitor

def test_backup_manager_simple():
    """Test backup manager functionality - simple version"""
    print("\n💾 Testing Backup Manager (Simple)...")
    
    try:
        # Create test configuration
        config = {
            'backup_enabled': True,
            'backup_interval': 10,
            'retention_days': 7,
            'compression_enabled': True,
            'encryption_enabled': True,
            'backup_dir': 'test_backups_simple'
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
        print(f"   Database backup result: {db_result}")
        
        # Check if backup was created by looking at the directory
        backup_dir = backup_manager.database_backup_dir
        if backup_dir.exists():
            backup_files = list(backup_dir.glob('*'))
            if backup_files:
                print(f"   ✅ Found {len(backup_files)} backup files in directory")
                print(f"   ✅ Latest backup: {backup_files[-1].name}")
                print("   ✅ Database backup created successfully")
            else:
                print("   ❌ No backup files found in directory")
                return False
        else:
            print("   ❌ Backup directory does not exist")
            return False
        
        # Test config backup
        config_result = backup_manager.run_manual_backup('config')
        print(f"   Config backup result: {config_result}")
        
        # Check if config backup was created
        config_backup_dir = backup_manager.config_backup_dir
        if config_backup_dir.exists():
            config_backup_files = list(config_backup_dir.glob('*'))
            if config_backup_files:
                print(f"   ✅ Found {len(config_backup_files)} config backup files")
                print("   ✅ Config backup created successfully")
            else:
                print("   ❌ No config backup files found")
                return False
        else:
            print("   ❌ Config backup directory does not exist")
            return False
        
        # Test logs backup
        logs_result = backup_manager.run_manual_backup('logs')
        print(f"   Logs backup result: {logs_result}")
        
        # Check if logs backup was created
        if hasattr(backup_manager, 'logs_backup_dir'):
            logs_backup_dir = backup_manager.logs_backup_dir
            if logs_backup_dir.exists():
                logs_backup_files = list(logs_backup_dir.glob('*'))
                if logs_backup_files:
                    print(f"   ✅ Found {len(logs_backup_files)} logs backup files")
                    print("   ✅ Logs backup created successfully")
                else:
                    print("   ❌ No logs backup files found")
                    return False
            else:
                print("   ❌ Logs backup directory does not exist")
                return False
        else:
            print("   ⚠️ Logs backup directory attribute not found, checking backup directory structure")
            # Check if logs backup was created in the main backup directory
            backup_dir = backup_manager.backup_dir
            if backup_dir.exists():
                logs_backup_files = list(backup_dir.glob('logs/*'))
                if logs_backup_files:
                    print(f"   ✅ Found {len(logs_backup_files)} logs backup files")
                    print("   ✅ Logs backup created successfully")
                else:
                    print("   ❌ No logs backup files found")
                    return False
            else:
                print("   ❌ Main backup directory does not exist")
                return False
        
        # Test application backup
        app_result = backup_manager.run_manual_backup('application')
        print(f"   Application backup result: {app_result}")
        
        # Check if application backup was created
        if hasattr(backup_manager, 'application_backup_dir'):
            app_backup_dir = backup_manager.application_backup_dir
            if app_backup_dir.exists():
                app_backup_files = list(app_backup_dir.glob('*'))
                if app_backup_files:
                    print(f"   ✅ Found {len(app_backup_files)} application backup files")
                    print("   ✅ Application backup created successfully")
                else:
                    print("   ❌ No application backup files found")
                    return False
            else:
                print("   ❌ Application backup directory does not exist")
                return False
        else:
            print("   ⚠️ Application backup directory attribute not found, checking backup directory structure")
            # Check if application backup was created in the main backup directory
            backup_dir = backup_manager.backup_dir
            if backup_dir.exists():
                app_backup_files = list(backup_dir.glob('application/*'))
                if app_backup_files:
                    print(f"   ✅ Found {len(app_backup_files)} application backup files")
                    print("   ✅ Application backup created successfully")
                else:
                    print("   ❌ No application backup files found")
                    return False
            else:
                print("   ❌ Main backup directory does not exist")
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

def test_recovery_manager_simple():
    """Test recovery manager functionality - simple version"""
    print("\n🔄 Testing Recovery Manager (Simple)...")
    
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

def test_backup_monitor_simple():
    """Test backup monitor functionality - simple version"""
    print("\n📊 Testing Backup Monitor (Simple)...")
    
    try:
        # Create test configuration
        config = {
            'backup_monitoring_enabled': True,
            'backup_monitoring_interval': 10,
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

def test_backup_recovery_integration_simple():
    """Test integration of backup and recovery components - simple version"""
    print("\n🔗 Testing Backup & Recovery Integration (Simple)...")
    
    try:
        # Create comprehensive configuration
        config = {
            'backup_enabled': True,
            'backup_interval': 10,
            'retention_days': 7,
            'compression_enabled': True,
            'encryption_enabled': True,
            'backup_dir': 'test_backups_integration_simple',
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
        print(f"   Database backup result: {db_result}")
        
        # Check if backup was created
        backup_dir = backup_manager.database_backup_dir
        if backup_dir.exists():
            backup_files = list(backup_dir.glob('*'))
            if backup_files:
                print(f"   ✅ Found {len(backup_files)} backup files")
                print("   ✅ Backup execution working")
            else:
                print("   ❌ No backup files found")
                return False
        else:
            print("   ❌ Backup directory does not exist")
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
        
        # Test monitoring integration
        print("   Testing monitoring integration...")
        backup_monitor._collect_backup_status()
        monitoring_data = backup_monitor.get_monitoring_data()
        if monitoring_data:
            print("   ✅ Monitoring integration working")
        else:
            print("   ❌ Monitoring integration failed")
            return False
        
        print("   ✅ Backup & Recovery Integration test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Backup & Recovery Integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Stage 4: Backup & Recovery Test (Simple)")
    print("=" * 60)
    
    test_results = {
        'backup_manager': False,
        'recovery_manager': False,
        'backup_monitor': False,
        'backup_recovery_integration': False
    }
    
    # Run individual component tests
    test_results['backup_manager'] = test_backup_manager_simple()
    test_results['recovery_manager'] = test_recovery_manager_simple()
    test_results['backup_monitor'] = test_backup_monitor_simple()
    
    # Run integration tests
    test_results['backup_recovery_integration'] = test_backup_recovery_integration_simple()
    
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
    results_file = Path(__file__).parent.parent / 'logs' / f'backup_recovery_simple_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
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