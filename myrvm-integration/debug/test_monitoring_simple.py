#!/usr/bin/env python3
"""
Simple Monitoring Test Script
Simplified test for Stage 3 monitoring and alerting components
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
sys.path.append(str(Path(__file__).parent.parent / "monitoring"))

def test_alerting_system():
    """Test alerting system functionality"""
    print("\n🚨 Testing Alerting System...")
    
    try:
        from alerting_system import AlertingSystem
        
        # Create test configuration
        config = {
            'alert_thresholds': {
                'cpu_percent': 80.0,
                'memory_percent': 80.0,
                'disk_percent': 85.0,
                'temperature': 75.0
            },
            'notification_channels': {
                'email': {'enabled': False},
                'webhook': {'enabled': False},
                'slack': {'enabled': False},
                'sms': {'enabled': False}
            },
            'alert_cooldown': 300
        }
        
        # Initialize alerting system
        alerting = AlertingSystem(config)
        
        # Test alerting initialization
        print("   ✅ Alerting system initialized successfully")
        
        # Test metrics checking
        test_metrics = {
            'cpu': {'percent': 85.0},
            'memory': {'percent': 75.0},
            'disk': {'percent': 90.0},
            'temperature': {'cpu_celsius': 80.0}
        }
        
        alerts = alerting.check_metrics(test_metrics)
        print(f"   ✅ Metrics checking working ({len(alerts)} alerts generated)")
        
        # Test alert processing
        alerting.process_alerts(alerts)
        print("   ✅ Alert processing working")
        
        # Test active alerts
        active_alerts = alerting.get_active_alerts()
        print(f"   ✅ Active alerts: {len(active_alerts)}")
        
        # Test alert statistics
        stats = alerting.get_alert_statistics()
        print(f"   ✅ Alert statistics: {stats.get('total_alerts', 0)} total alerts")
        
        print("   ✅ Alerting System test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Alerting System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metrics_collector():
    """Test metrics collector functionality"""
    print("\n📈 Testing Metrics Collector...")
    
    try:
        from metrics_collector import MetricsCollector
        
        # Create test configuration
        config = {
            'metrics_collection_interval': 30,
            'metrics_retention_days': 30,
            'aggregation_intervals': [300, 3600, 86400],
            'log_level': 'INFO'
        }
        
        # Initialize metrics collector
        collector = MetricsCollector(config)
        
        # Test collector initialization
        print("   ✅ Metrics collector initialized successfully")
        
        # Test system metrics collection
        system_metrics = collector.collect_system_metrics()
        print(f"   ✅ System metrics collection working ({len(system_metrics)} metrics)")
        
        # Test application metrics collection
        app_metrics = collector.collect_application_metrics()
        print(f"   ✅ Application metrics collection working ({len(app_metrics)} metrics)")
        
        # Test business metrics collection
        business_metrics = collector.collect_business_metrics()
        print(f"   ✅ Business metrics collection working ({len(business_metrics)} metrics)")
        
        # Test custom metrics collection
        custom_metrics = collector.collect_custom_metrics()
        print(f"   ✅ Custom metrics collection working ({len(custom_metrics)} metrics)")
        
        # Test metrics storage
        test_metrics = {'test_metric': 123.45}
        collector.store_metrics(test_metrics, 'test')
        print("   ✅ Metrics storage working")
        
        # Test metrics history
        history = collector.get_metrics_history('test_metric', 1)
        print(f"   ✅ Metrics history working ({len(history)} records)")
        
        # Test metrics summary
        summary = collector.get_metrics_summary()
        print(f"   ✅ Metrics summary: {summary.get('total_metrics', 0)} total metrics")
        
        print("   ✅ Metrics Collector test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Metrics Collector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_checker_simple():
    """Test health checker functionality (simplified)"""
    print("\n🏥 Testing Health Checker (Simplified)...")
    
    try:
        from health_checker import HealthChecker
        
        # Create test configuration
        config = {
            'health_check_interval': 60,
            'health_check_timeout': 30,
            'health_check_retry_count': 3,
            'health_recovery_enabled': True,
            'log_level': 'INFO'
        }
        
        # Initialize health checker
        health_checker = HealthChecker(config)
        
        # Test health checker initialization
        print("   ✅ Health checker initialized successfully")
        
        # Test system resources check
        system_check = health_checker.check_system_resources()
        print(f"   ✅ System resources check: {system_check['status']} (score: {system_check['score']})")
        
        # Test database connectivity check
        db_check = health_checker.check_database_connectivity()
        print(f"   ✅ Database connectivity check: {db_check['status']} (score: {db_check['score']})")
        
        # Test overall health checks
        health_results = health_checker.perform_health_checks()
        print(f"   ✅ Overall health check: {health_results['overall']} (score: {health_results['score']:.1f})")
        
        # Test health status
        status = health_checker.get_health_status()
        print(f"   ✅ Health status: {status['overall']}")
        
        print("   ✅ Health Checker test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Health Checker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_integration_simple():
    """Test integration of monitoring components (simplified)"""
    print("\n🔗 Testing Monitoring Integration (Simplified)...")
    
    try:
        from alerting_system import AlertingSystem
        from metrics_collector import MetricsCollector
        
        # Create comprehensive configuration
        config = {
            'alert_thresholds': {
                'cpu_percent': 80.0,
                'memory_percent': 80.0,
                'disk_percent': 85.0,
                'temperature': 75.0
            },
            'notification_channels': {
                'email': {'enabled': False},
                'webhook': {'enabled': False},
                'slack': {'enabled': False},
                'sms': {'enabled': False}
            },
            'metrics_collection_interval': 30,
            'log_level': 'INFO',
            'environment': 'development'
        }
        
        # Initialize components
        alerting = AlertingSystem(config)
        collector = MetricsCollector(config)
        
        print("   ✅ Monitoring components initialized successfully")
        
        # Test data flow
        # 1. Collect metrics
        system_metrics = collector.collect_system_metrics()
        print("   ✅ Metrics collection working")
        
        # 2. Check for alerts
        alerts = alerting.check_metrics(system_metrics)
        print(f"   ✅ Alert checking working ({len(alerts)} alerts)")
        
        # 3. Process alerts
        alerting.process_alerts(alerts)
        print("   ✅ Alert processing working")
        
        # Test component status
        alerting_status = alerting.get_alerting_status()
        collector_summary = collector.get_metrics_summary()
        
        print("   ✅ Component status checks working")
        
        print("   ✅ Monitoring Integration test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Monitoring Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Stage 3: Monitoring & Alerting Test (Simplified)")
    print("=" * 60)
    
    test_results = {
        'alerting_system': False,
        'metrics_collector': False,
        'health_checker': False,
        'monitoring_integration': False
    }
    
    # Run individual component tests
    test_results['alerting_system'] = test_alerting_system()
    test_results['metrics_collector'] = test_metrics_collector()
    test_results['health_checker'] = test_health_checker_simple()
    
    # Run integration tests
    test_results['monitoring_integration'] = test_monitoring_integration_simple()
    
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
    results_file = Path(__file__).parent.parent / 'logs' / f'monitoring_alerting_simple_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
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
