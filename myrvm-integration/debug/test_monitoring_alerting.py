#!/usr/bin/env python3
"""
Monitoring & Alerting Test Script
Test Stage 3 monitoring and alerting for MyRVM Platform Integration
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
sys.path.append(str(Path(__file__).parent.parent / "monitoring"))

from metrics_collector import MetricsCollector
from alerting_engine import AlertingEngine
from dashboard_server import MonitoringDashboard
from health_monitor import HealthMonitor

def test_metrics_collector():
    """Test metrics collector functionality"""
    print("\n📊 Testing Metrics Collector...")
    
    try:
        # Create test configuration
        config = {
            'monitoring_interval': 5.0,
            'metrics_history_size': 100,
            'enable_gpu_monitoring': True
        }
        
        # Initialize metrics collector
        metrics_collector = MetricsCollector(config)
        
        # Test metrics collection
        print("   Starting metrics collection...")
        metrics_collector.start_collection()
        
        # Wait for some metrics to be collected
        time.sleep(10)
        
        # Test current metrics
        current_metrics = metrics_collector.get_current_metrics()
        if current_metrics and 'system' in current_metrics:
            print("   ✅ Current metrics collection working")
            print(f"   ✅ CPU: {current_metrics['system'].get('cpu', {}).get('percent', 'N/A')}%")
            print(f"   ✅ Memory: {current_metrics['system'].get('memory', {}).get('percent', 'N/A')}%")
        else:
            print("   ❌ Current metrics collection failed")
            return False
        
        # Test metrics history
        cpu_history = metrics_collector.get_metrics_history('system.cpu.percent', 10)
        if cpu_history:
            print(f"   ✅ Metrics history working: {len(cpu_history)} entries")
        else:
            print("   ❌ Metrics history failed")
            return False
        
        # Test custom metrics
        metrics_collector.update_custom_metric('application', 'test_metric', 42)
        custom_metrics = metrics_collector.get_current_metrics()
        if custom_metrics.get('application', {}).get('test_metric') == 42:
            print("   ✅ Custom metrics working")
        else:
            print("   ❌ Custom metrics failed")
            return False
        
        # Test metrics export
        json_export = metrics_collector.export_metrics('json')
        if json_export and 'system' in json_export:
            print("   ✅ JSON export working")
        else:
            print("   ❌ JSON export failed")
            return False
        
        # Test metrics summary
        summary = metrics_collector.get_metrics_summary()
        if summary and 'collection_status' in summary:
            print("   ✅ Metrics summary working")
        else:
            print("   ❌ Metrics summary failed")
            return False
        
        # Test metrics report
        report = metrics_collector.get_metrics_report()
        if report and 'Metrics Collector Report' in report:
            print("   ✅ Metrics report working")
        else:
            print("   ❌ Metrics report failed")
            return False
        
        # Stop collection
        metrics_collector.stop_collection()
        
        print("   ✅ Metrics Collector test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Metrics Collector test failed: {e}")
        return False

def test_alerting_engine():
    """Test alerting engine functionality"""
    print("\n🚨 Testing Alerting Engine...")
    
    try:
        # Create test configuration
        config = {
            'environment': 'test',
            'email_alerts': {
                'enabled': False
            },
            'webhook_alerts': {
                'enabled': False
            }
        }
        
        # Initialize alerting engine
        alerting_engine = AlertingEngine(config)
        
        # Test alert rules loading
        if alerting_engine.alert_rules:
            print(f"   ✅ Alert rules loaded: {len(alerting_engine.alert_rules)} rules")
        else:
            print("   ❌ Alert rules loading failed")
            return False
        
        # Test alert processing with normal metrics
        normal_metrics = {
            'system': {
                'cpu': {'percent': 50},
                'memory': {'percent': 60},
                'disk': {'percent': 70}
            },
            'application': {
                'uptime_seconds': 3600,
                'error_count': 0
            },
            'gpu': {
                'load_percent': 30,
                'temperature_c': 45
            }
        }
        
        alerting_engine.process_metrics(normal_metrics)
        active_alerts = alerting_engine.get_active_alerts()
        if len(active_alerts) == 0:
            print("   ✅ Normal metrics processing working (no alerts)")
        else:
            print(f"   ⚠️ Normal metrics triggered {len(active_alerts)} alerts")
        
        # Test alert processing with critical metrics
        critical_metrics = {
            'system': {
                'cpu': {'percent': 98},
                'memory': {'percent': 96},
                'disk': {'percent': 99}
            },
            'application': {
                'uptime_seconds': 0,
                'error_count': 15
            },
            'gpu': {
                'load_percent': 95,
                'temperature_c': 85
            }
        }
        
        alerting_engine.process_metrics(critical_metrics)
        active_alerts = alerting_engine.get_active_alerts()
        if len(active_alerts) > 0:
            print(f"   ✅ Critical metrics processing working: {len(active_alerts)} alerts")
        else:
            print("   ❌ Critical metrics processing failed (no alerts triggered)")
            return False
        
        # Test alert history
        alert_history = alerting_engine.get_alert_history(10)
        if alert_history:
            print(f"   ✅ Alert history working: {len(alert_history)} entries")
        else:
            print("   ❌ Alert history failed")
            return False
        
        # Test alert suppression
        alerting_engine.suppress_alert('high_cpu_usage', 1)  # 1 minute
        suppressed_alerts = alerting_engine.suppressed_alerts
        if 'high_cpu_usage' in suppressed_alerts:
            print("   ✅ Alert suppression working")
        else:
            print("   ❌ Alert suppression failed")
            return False
        
        # Test alerting status
        status = alerting_engine.get_alerting_status()
        if status and 'active_alerts_count' in status:
            print("   ✅ Alerting status working")
        else:
            print("   ❌ Alerting status failed")
            return False
        
        # Test alerting report
        report = alerting_engine.get_alerting_report()
        if report and 'Alerting Engine Report' in report:
            print("   ✅ Alerting report working")
        else:
            print("   ❌ Alerting report failed")
            return False
        
        print("   ✅ Alerting Engine test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Alerting Engine test failed: {e}")
        return False

def test_health_monitor():
    """Test health monitor functionality"""
    print("\n🏥 Testing Health Monitor...")
    
    try:
        # Create test configuration
        config = {
            'health_check_interval': 10.0,
            'recovery_enabled': True,
            'max_recovery_attempts': 2
        }
        
        # Initialize health monitor
        health_monitor = HealthMonitor(config)
        
        # Test health checks initialization
        if health_monitor.health_checks:
            print(f"   ✅ Health checks initialized: {len(health_monitor.health_checks)} checks")
        else:
            print("   ❌ Health checks initialization failed")
            return False
        
        # Test individual health checks
        system_resources = health_monitor._check_system_resources()
        if 'cpu_percent' in system_resources:
            print("   ✅ System resources check working")
        else:
            print("   ❌ System resources check failed")
            return False
        
        process_health = health_monitor._check_process_health()
        if 'process_count' in process_health:
            print("   ✅ Process health check working")
        else:
            print("   ❌ Process health check failed")
            return False
        
        file_system = health_monitor._check_file_system()
        if 'health_percent' in file_system:
            print("   ✅ File system check working")
        else:
            print("   ❌ File system check failed")
            return False
        
        # Test health monitoring
        print("   Starting health monitoring...")
        health_monitor.start_monitoring()
        
        # Wait for health checks to run
        time.sleep(15)
        
        # Test health status
        health_status = health_monitor.get_health_status()
        if health_status and 'overall' in health_status:
            overall_status = health_status['overall']
            print(f"   ✅ Health monitoring working: {overall_status.get('status', 'unknown')}")
            print(f"   ✅ Healthy checks: {overall_status.get('healthy_checks', 0)}")
            print(f"   ✅ Warning checks: {overall_status.get('warning_checks', 0)}")
            print(f"   ✅ Critical checks: {overall_status.get('critical_checks', 0)}")
        else:
            print("   ❌ Health monitoring failed")
            return False
        
        # Test health history
        health_history = health_monitor.get_health_history(5)
        if health_history:
            print(f"   ✅ Health history working: {len(health_history)} entries")
        else:
            print("   ❌ Health history failed")
            return False
        
        # Test health report
        report = health_monitor.get_health_report()
        if report and 'Health Monitor Report' in report:
            print("   ✅ Health report working")
        else:
            print("   ❌ Health report failed")
            return False
        
        # Stop monitoring
        health_monitor.stop_monitoring()
        
        print("   ✅ Health Monitor test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Health Monitor test failed: {e}")
        return False

def test_dashboard_server():
    """Test dashboard server functionality"""
    print("\n📊 Testing Dashboard Server...")
    
    try:
        # Create test configuration
        config = {
            'dashboard_host': '127.0.0.1',
            'dashboard_port': 5002,  # Use different port for testing
            'dashboard_debug': False,
            'dashboard_refresh_interval': 5
        }
        
        # Initialize dashboard server
        dashboard = MonitoringDashboard(config)
        
        # Test dashboard initialization
        if dashboard.app:
            print("   ✅ Dashboard server initialized")
        else:
            print("   ❌ Dashboard server initialization failed")
            return False
        
        # Test dashboard info
        info = dashboard.get_dashboard_info()
        if info and 'url' in info:
            print(f"   ✅ Dashboard info working: {info['url']}")
        else:
            print("   ❌ Dashboard info failed")
            return False
        
        # Test system status
        system_status = dashboard._get_system_status()
        if system_status and 'status' in system_status:
            print(f"   ✅ System status working: {system_status['status']}")
        else:
            print("   ❌ System status failed")
            return False
        
        # Test fallback metrics
        fallback_metrics = dashboard._get_fallback_metrics()
        if fallback_metrics and 'system' in fallback_metrics:
            print("   ✅ Fallback metrics working")
        else:
            print("   ❌ Fallback metrics failed")
            return False
        
        # Test health status
        health_status = dashboard._get_health_status()
        if health_status and 'status' in health_status:
            print(f"   ✅ Health status working: {health_status['status']}")
        else:
            print("   ❌ Health status failed")
            return False
        
        # Test dashboard report
        report = dashboard.get_dashboard_report()
        if report and 'Monitoring Dashboard Report' in report:
            print("   ✅ Dashboard report working")
        else:
            print("   ❌ Dashboard report failed")
            return False
        
        print("   ✅ Dashboard Server test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Dashboard Server test failed: {e}")
        return False

def test_monitoring_integration():
    """Test integration of all monitoring components"""
    print("\n🔗 Testing Monitoring Integration...")
    
    try:
        # Create comprehensive configuration
        config = {
            'environment': 'test',
            'monitoring_interval': 5.0,
            'health_check_interval': 10.0,
            'dashboard_host': '127.0.0.1',
            'dashboard_port': 5003,
            'enable_gpu_monitoring': True,
            'recovery_enabled': True
        }
        
        # Initialize all components
        metrics_collector = MetricsCollector(config)
        alerting_engine = AlertingEngine(config)
        health_monitor = HealthMonitor(config)
        dashboard = MonitoringDashboard(config, metrics_collector, alerting_engine)
        
        print("   ✅ All components initialized successfully")
        
        # Test metrics callback integration
        def metrics_callback(metrics):
            alerting_engine.process_metrics(metrics)
        
        metrics_collector.add_metrics_callback(metrics_callback)
        print("   ✅ Metrics callback integration working")
        
        # Test health callback integration
        def health_callback(health_status):
            print(f"   Health status: {health_status.get('overall', {}).get('status', 'unknown')}")
        
        health_monitor.add_health_callback(health_callback)
        print("   ✅ Health callback integration working")
        
        # Start all components
        print("   Starting all monitoring components...")
        metrics_collector.start_collection()
        health_monitor.start_monitoring()
        
        # Wait for components to run
        time.sleep(15)
        
        # Test integration
        current_metrics = metrics_collector.get_current_metrics()
        active_alerts = alerting_engine.get_active_alerts()
        health_status = health_monitor.get_health_status()
        
        if current_metrics and health_status:
            print("   ✅ Monitoring integration working")
            print(f"   ✅ Metrics collection: Active")
            print(f"   ✅ Active alerts: {len(active_alerts)}")
            print(f"   ✅ Health status: {health_status.get('overall', {}).get('status', 'unknown')}")
        else:
            print("   ❌ Monitoring integration failed")
            return False
        
        # Stop all components
        metrics_collector.stop_collection()
        health_monitor.stop_monitoring()
        
        print("   ✅ Monitoring Integration test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Monitoring Integration test failed: {e}")
        return False

def test_monitoring_performance():
    """Test monitoring system performance"""
    print("\n⚡ Testing Monitoring Performance...")
    
    try:
        # Create test configuration
        config = {
            'monitoring_interval': 1.0,  # Fast interval for testing
            'metrics_history_size': 50,
            'enable_gpu_monitoring': True
        }
        
        # Initialize metrics collector
        metrics_collector = MetricsCollector(config)
        
        # Test collection performance
        start_time = time.time()
        metrics_collector.start_collection()
        
        # Collect metrics for 10 seconds
        time.sleep(10)
        
        end_time = time.time()
        collection_time = end_time - start_time
        
        # Get metrics summary
        summary = metrics_collector.get_metrics_summary()
        metrics_count = summary.get('metrics_count', 0)
        
        if metrics_count > 0:
            print(f"   ✅ Performance test completed")
            print(f"   ✅ Collection time: {collection_time:.2f}s")
            print(f"   ✅ Metrics collected: {metrics_count}")
            print(f"   ✅ Collection rate: {metrics_count/collection_time:.2f} metrics/sec")
        else:
            print("   ❌ Performance test failed")
            return False
        
        # Test export performance
        export_start = time.time()
        json_export = metrics_collector.export_metrics('json')
        export_time = time.time() - export_start
        
        if json_export:
            print(f"   ✅ Export performance: {export_time:.3f}s")
        else:
            print("   ❌ Export performance failed")
            return False
        
        # Stop collection
        metrics_collector.stop_collection()
        
        print("   ✅ Monitoring Performance test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Monitoring Performance test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Stage 3: Monitoring & Alerting Test")
    print("=" * 60)
    
    test_results = {
        'metrics_collector': False,
        'alerting_engine': False,
        'health_monitor': False,
        'dashboard_server': False,
        'monitoring_integration': False,
        'monitoring_performance': False
    }
    
    # Run individual component tests
    test_results['metrics_collector'] = test_metrics_collector()
    test_results['alerting_engine'] = test_alerting_engine()
    test_results['health_monitor'] = test_health_monitor()
    test_results['dashboard_server'] = test_dashboard_server()
    
    # Run integration tests
    test_results['monitoring_integration'] = test_monitoring_integration()
    test_results['monitoring_performance'] = test_monitoring_performance()
    
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
        print("🎉 All monitoring and alerting tests passed!")
        print("✅ Stage 3: Monitoring & Alerting - COMPLETED")
    else:
        print("⚠️  Some tests failed. Please check the logs for details.")
    
    # Save test results
    results_file = Path(__file__).parent.parent / 'logs' / f'monitoring_alerting_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
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
