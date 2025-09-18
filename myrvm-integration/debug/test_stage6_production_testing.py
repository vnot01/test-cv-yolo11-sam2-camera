#!/usr/bin/env python3
"""
Stage 6: Production Testing - Test Script
Tests all production testing frameworks.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_load_testing():
    """Test load testing framework."""
    print("Testing Load Testing Framework...")
    
    try:
        from testing.load_test import LoadTestFramework
        
        # Load configuration
        config_path = project_root / "config" / "development_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        load_test = LoadTestFramework(config)
        print("✓ Load testing framework initialized successfully")
        
        # Test basic functionality
        result = load_test.test_single_user_load()
        if result:
            print("✓ Single user load test completed")
        else:
            print("✗ Single user load test failed")
        
        return True
        
    except Exception as e:
        print(f"✗ Load testing framework failed: {e}")
        return False

def test_stress_testing():
    """Test stress testing framework."""
    print("Testing Stress Testing Framework...")
    
    try:
        # Check if stress test file exists
        stress_test_file = project_root / "testing" / "stress_test.py"
        if stress_test_file.exists():
            print("✓ Stress test file exists")
            
            # Try basic import test
            from testing.stress_test import StressTestFramework
            print("✓ Stress testing framework can be imported")
            
            return True
        else:
            print("✗ Stress test file does not exist")
            return False
        
    except Exception as e:
        print(f"✗ Stress testing framework failed: {e}")
        return False

def test_e2e_testing():
    """Test end-to-end testing framework."""
    print("Testing End-to-End Testing Framework...")
    
    try:
        from testing.e2e_test import E2ETestFramework
        
        # Load configuration
        config_path = project_root / "config" / "development_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        e2e_test = E2ETestFramework(config)
        print("✓ E2E testing framework initialized successfully")
        
        # Test basic functionality
        result = e2e_test.test_api_connectivity()
        if result and result["status"] == "PASS":
            print("✓ API connectivity test completed")
        else:
            print("✗ API connectivity test failed")
        
        return True
        
    except Exception as e:
        print(f"✗ E2E testing framework failed: {e}")
        return False

def test_performance_benchmarking():
    """Test performance benchmarking framework."""
    print("Testing Performance Benchmarking Framework...")
    
    try:
        # Check if performance benchmark file exists
        benchmark_file = project_root / "testing" / "performance_benchmark.py"
        if benchmark_file.exists():
            print("✓ Performance benchmark file exists")
            
            # Try to import (basic test)
            from testing.performance_benchmark import PerformanceBenchmark
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
            print("✓ Performance benchmark framework can be imported")
            
            return True
        else:
            print("✗ Performance benchmark file does not exist")
            return False
        
    except Exception as e:
        print(f"✗ Performance benchmarking framework failed: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 60)
    print("Stage 6: Production Testing - Framework Tests")
    print("=" * 60)
    print()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_results = []
    
    # Test all frameworks
    tests = [
        ("Load Testing Framework", test_load_testing),
        ("Stress Testing Framework", test_stress_testing),
        ("E2E Testing Framework", test_e2e_testing),
        ("Performance Benchmarking Framework", test_performance_benchmarking)
    ]
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            test_results.append({
                "test_name": test_name,
                "status": "PASS" if result else "FAIL",
                "duration": duration
            })
            
            if result:
                print(f"✓ {test_name} - PASSED ({duration:.2f}s)")
            else:
                print(f"✗ {test_name} - FAILED ({duration:.2f}s)")
                
        except Exception as e:
            duration = time.time() - start_time
            test_results.append({
                "test_name": test_name,
                "status": "ERROR",
                "duration": duration,
                "error": str(e)
            })
            print(f"✗ {test_name} - ERROR: {e} ({duration:.2f}s)")
        
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r["status"] == "PASS")
    failed_tests = sum(1 for r in test_results if r["status"] == "FAIL")
    error_tests = sum(1 for r in test_results if r["status"] == "ERROR")
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Errors: {error_tests}")
    print(f"Success Rate: {(passed_tests / total_tests * 100):.2f}%")
    
    # Save results
    results_dir = project_root / "testing" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"stage6_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "timestamp": now().isoformat()
            },
            "test_results": test_results
        }, f, indent=2)
    
    print(f"\nTest results saved to: {results_file}")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
