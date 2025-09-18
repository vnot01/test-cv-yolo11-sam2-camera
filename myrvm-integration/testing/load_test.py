#!/usr/bin/env python3
"""
MyRVM Platform Integration - Load Testing Framework
Implements comprehensive load testing scenarios for production validation.
"""

import os
import sys
import time
import json
import logging
import threading
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import statistics
import psutil
import requests
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class LoadTestResult:
    """Data class for load test results."""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    response_times: List[float] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    system_metrics: Dict[str, List[float]] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

class LoadTestFramework:
    """Comprehensive load testing framework for MyRVM Platform Integration."""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.results_dir = self.project_root / "testing" / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Load test configuration
        self.load_test_config = self.config.get("load_testing", {})
        self.base_url = self.config.get("myrvm_base_url", "http://localhost:8000")
        self.api_endpoints = self.load_test_config.get("endpoints", ["/health"])
        self.concurrent_users = self.load_test_config.get("concurrent_users", [10, 50, 100])
        self.test_duration = self.load_test_config.get("test_duration", 60)  # 1 minute
        
        # System monitoring
        self.system_metrics = defaultdict(list)
        self.monitoring_enabled = True
        self.monitoring_thread = None
        
        # Test results
        self.test_results: List[LoadTestResult] = []
        
    def _start_system_monitoring(self):
        """Start system monitoring in background thread."""
        if not self.monitoring_enabled:
            return
            
        def monitor_system():
            while self.monitoring_enabled:
                try:
                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.system_metrics["cpu_percent"].append(cpu_percent)
                    
                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.system_metrics["memory_percent"].append(memory.percent)
                    
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"System monitoring error: {e}")
                    time.sleep(1)
        
        self.monitoring_thread = threading.Thread(target=monitor_system, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("System monitoring started")
    
    def _stop_system_monitoring(self):
        """Stop system monitoring."""
        self.monitoring_enabled = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("System monitoring stopped")
    
    def _make_request(self, endpoint: str) -> Tuple[float, bool, str]:
        """Make a single HTTP request and return response time, success, and error message."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=30)
            response_time = time.time() - start_time
            success = 200 <= response.status_code < 300
            
            if not success:
                error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
            else:
                error_msg = ""
            
            return response_time, success, error_msg
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return response_time, False, "Request timeout"
        except requests.exceptions.ConnectionError:
            response_time = time.time() - start_time
            return response_time, False, "Connection error"
        except Exception as e:
            response_time = time.time() - start_time
            return response_time, False, f"Request error: {str(e)}"
    
    def run_load_test(self, scenario_name: str, concurrent_users: int, duration: int) -> LoadTestResult:
        """Run a single load test scenario."""
        self.logger.info(f"Starting load test: {scenario_name}")
        self.logger.info(f"Concurrent users: {concurrent_users}, Duration: {duration}s")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration)
        
        # Initialize result
        result = LoadTestResult(
            test_name=scenario_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            total_requests=0,
            successful_requests=0,
            failed_requests=0
        )
        
        # Start system monitoring
        self._start_system_monitoring()
        
        # Create thread pool for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            # Submit initial batch of requests
            for _ in range(concurrent_users):
                endpoint = self.api_endpoints[0]
                future = executor.submit(self._make_request, endpoint)
                futures.append(future)
            
            # Continue submitting requests until duration is reached
            while datetime.now() < end_time:
                # Collect completed requests
                completed_futures = []
                for future in futures:
                    if future.done():
                        try:
                            response_time, success, error_msg = future.result()
                            result.total_requests += 1
                            result.response_times.append(response_time)
                            
                            if success:
                                result.successful_requests += 1
                            else:
                                result.failed_requests += 1
                                if error_msg:
                                    result.error_messages.append(error_msg)
                            
                            completed_futures.append(future)
                        except Exception as e:
                            result.total_requests += 1
                            result.failed_requests += 1
                            result.error_messages.append(f"Future error: {str(e)}")
                            completed_futures.append(future)
                
                # Remove completed futures
                for future in completed_futures:
                    futures.remove(future)
                
                # Submit new requests to maintain concurrency
                while len(futures) < concurrent_users and datetime.now() < end_time:
                    endpoint = self.api_endpoints[0]
                    future = executor.submit(self._make_request, endpoint)
                    futures.append(future)
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
            
            # Wait for remaining requests to complete
            for future in futures:
                try:
                    response_time, success, error_msg = future.result(timeout=5)
                    result.total_requests += 1
                    result.response_times.append(response_time)
                    
                    if success:
                        result.successful_requests += 1
                    else:
                        result.failed_requests += 1
                        if error_msg:
                            result.error_messages.append(error_msg)
                except Exception as e:
                    result.total_requests += 1
                    result.failed_requests += 1
                    result.error_messages.append(f"Future timeout: {str(e)}")
        
        # Stop system monitoring and collect metrics
        self._stop_system_monitoring()
        result.system_metrics = dict(self.system_metrics)
        
        # Clear metrics for next test
        self.system_metrics.clear()
        
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds()
        
        self.logger.info(f"Load test completed: {scenario_name}")
        self.logger.info(f"Total requests: {result.total_requests}")
        self.logger.info(f"Success rate: {result.success_rate:.2f}%")
        self.logger.info(f"Average response time: {result.average_response_time:.3f}s")
        
        return result
    
    def run_all_load_tests(self) -> List[LoadTestResult]:
        """Run all load test scenarios."""
        self.logger.info("Starting comprehensive load testing")
        
        all_results = []
        
        # Run tests with different concurrent user levels
        for concurrent_users in self.concurrent_users:
            try:
                result = self.run_load_test(
                    f"Load Test ({concurrent_users} users)",
                    concurrent_users,
                    self.test_duration
                )
                all_results.append(result)
                time.sleep(10)  # Cooldown period
            except Exception as e:
                self.logger.error(f"Load test with {concurrent_users} users failed: {e}")
        
        self.test_results = all_results
        return all_results
    
    def generate_load_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive load test report."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "test_date": datetime.now().isoformat(),
                "total_requests": sum(result.total_requests for result in self.test_results),
                "total_successful_requests": sum(result.successful_requests for result in self.test_results),
                "total_failed_requests": sum(result.failed_requests for result in self.test_results)
            },
            "test_results": []
        }
        
        for result in self.test_results:
            test_result = {
                "test_name": result.test_name,
                "duration": result.duration,
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "success_rate": result.success_rate,
                "average_response_time": result.average_response_time,
                "error_count": len(result.error_messages)
            }
            report["test_results"].append(test_result)
        
        return report
    
    def save_load_test_report(self, report: Dict[str, Any], filename: str = None):
        """Save load test report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_report_{timestamp}.json"
        
        report_path = self.results_dir / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Load test report saved to: {report_path}")
        return report_path
    
    def test_single_user_load(self):
        """Test single user load for basic validation."""
        self.logger.info("Testing single user load")
        
        start_time = datetime.now()
        result = {
            "test_name": "Single User Load Test",
            "start_time": start_time,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "error_messages": []
        }
        
        try:
            # Make 10 simple requests
            for i in range(10):
                response_time, success, error_msg = self._make_request("/health")
                result["total_requests"] += 1
                result["response_times"].append(response_time)
                
                if success:
                    result["successful_requests"] += 1
                else:
                    result["failed_requests"] += 1
                    if error_msg:
                        result["error_messages"].append(error_msg)
                
                time.sleep(0.1)  # Small delay between requests
            
        except Exception as e:
            self.logger.error(f"Single user load test failed: {e}")
            result["error_messages"].append(str(e))
        
        result["end_time"] = datetime.now()
        result["duration"] = (result["end_time"] - result["start_time"]).total_seconds()
        
        success_rate = (result["successful_requests"] / result["total_requests"] * 100) if result["total_requests"] > 0 else 0
        self.logger.info(f"Single user load test completed: {success_rate:.2f}% success rate")
        return result

def main():
    """Main function for testing."""
    import json
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "development_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create load test framework
    load_test = LoadTestFramework(config)
    
    # Run load tests
    results = load_test.run_all_load_tests()
    
    # Generate and save report
    report = load_test.generate_load_test_report()
    report_path = load_test.save_load_test_report(report)
    
    print(f"Load testing completed. Report saved to: {report_path}")

if __name__ == "__main__":
    main()