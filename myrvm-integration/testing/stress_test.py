#!/usr/bin/env python3
"""
MyRVM Platform Integration - Stress Testing Framework
Implements comprehensive stress testing scenarios for production validation.
"""

import os
import sys
import time
import json
import logging
import threading
import asyncio
import aiohttp
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import statistics
import psutil
import requests
from dataclasses import dataclass, asdict
import csv
import random

@dataclass
class StressTestResult:
    """Data class for stress test results."""
    timestamp: str
    test_name: str
    stress_type: str
    max_concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_usage: float
    test_duration: float
    breaking_point: Optional[int]
    recovery_time: Optional[float]

class StressTestFramework:
    """
    Comprehensive stress testing framework for MyRVM Platform Integration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.results: List[StressTestResult] = []
        self.stress_scenarios = self._load_stress_scenarios()
        self.monitoring_data: List[Dict] = []
        self.is_running = False
        self.breaking_point = None
        
        # Stress test configuration
        self.base_url = self.config.get('myrvm_base_url', 'http://localhost:8000')
        self.timeout = self.config.get('timeout', 30)
        self.max_workers = self.config.get('max_workers', 500)
        
    def _load_stress_scenarios(self) -> Dict[str, Dict]:
        """Load stress test scenarios configuration."""
        return {
            "cpu_stress": {
                "name": "CPU Stress Test",
                "description": "Stress test CPU resources with high computational load",
                "max_concurrent_users": 200,
                "ramp_up_rate": 10,  # users per second
                "duration": 600,  # 10 minutes
                "stress_type": "cpu"
            },
            "memory_stress": {
                "name": "Memory Stress Test",
                "description": "Stress test memory resources with large data processing",
                "max_concurrent_users": 150,
                "ramp_up_rate": 5,  # users per second
                "duration": 600,  # 10 minutes
                "stress_type": "memory"
            },
            "network_stress": {
                "name": "Network Stress Test",
                "description": "Stress test network resources with high bandwidth usage",
                "max_concurrent_users": 300,
                "ramp_up_rate": 15,  # users per second
                "duration": 600,  # 10 minutes
                "stress_type": "network"
            },
            "disk_stress": {
                "name": "Disk Stress Test",
                "description": "Stress test disk I/O with high file operations",
                "max_concurrent_users": 100,
                "ramp_up_rate": 5,  # users per second
                "duration": 600,  # 10 minutes
                "stress_type": "disk"
            },
            "mixed_stress": {
                "name": "Mixed Resource Stress Test",
                "description": "Stress test all system resources simultaneously",
                "max_concurrent_users": 250,
                "ramp_up_rate": 8,  # users per second
                "duration": 900,  # 15 minutes
                "stress_type": "mixed"
            },
            "gradual_stress": {
                "name": "Gradual Stress Test",
                "description": "Gradually increase load to find breaking point",
                "max_concurrent_users": 500,
                "ramp_up_rate": 2,  # users per second
                "duration": 1800,  # 30 minutes
                "stress_type": "gradual"
            }
        }
    
    async def _make_stress_request(self, session: aiohttp.ClientSession, endpoint: str, stress_type: str, user_id: int) -> Tuple[bool, float, int]:
        """Make a stress-inducing HTTP request based on stress type."""
        start_time = time.time()
        
        try:
            if stress_type == "cpu":
                # CPU-intensive request with complex processing
                data = {
                    "complex_calculation": True,
                    "iterations": 1000,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
                async with session.post(f"{self.base_url}{endpoint}", json=data, timeout=self.timeout) as response:
                    response_time = time.time() - start_time
                    return response.status in [200, 201], response_time, response.status
                    
            elif stress_type == "memory":
                # Memory-intensive request with large data
                large_data = {
                    "large_array": [random.randint(1, 1000) for _ in range(10000)],
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
                async with session.post(f"{self.base_url}{endpoint}", json=large_data, timeout=self.timeout) as response:
                    response_time = time.time() - start_time
                    return response.status in [200, 201], response_time, response.status
                    
            elif stress_type == "network":
                # Network-intensive request with large payload
                network_data = {
                    "large_payload": "x" * 10000,  # 10KB string
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
                async with session.post(f"{self.base_url}{endpoint}", json=network_data, timeout=self.timeout) as response:
                    response_time = time.time() - start_time
                    return response.status in [200, 201], response_time, response.status
                    
            elif stress_type == "disk":
                # Disk-intensive request with file operations
                disk_data = {
                    "file_operations": True,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
                async with session.post(f"{self.base_url}{endpoint}", json=disk_data, timeout=self.timeout) as response:
                    response_time = time.time() - start_time
                    return response.status in [200, 201], response_time, response.status
                    
            else:  # mixed or default
                # Mixed stress with random operations
                mixed_data = {
                    "stress_type": random.choice(["cpu", "memory", "network", "disk"]),
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
                async with session.post(f"{self.base_url}{endpoint}", json=mixed_data, timeout=self.timeout) as response:
                    response_time = time.time() - start_time
                    return response.status in [200, 201], response_time, response.status
                    
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return False, response_time, 408
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Stress request failed: {e}")
            return False, response_time, 500
    
    async def _stress_user_simulation(self, session: aiohttp.ClientSession, user_id: int, scenario: Dict, stress_type: str) -> Dict[str, Any]:
        """Simulate a single user's stress behavior during the test."""
        user_results = {
            "user_id": user_id,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": []
        }
        
        start_time = time.time()
        end_time = start_time + scenario["duration"]
        
        # Get stress endpoints
        stress_endpoints = self._get_stress_endpoints(stress_type)
        
        while time.time() < end_time and self.is_running:
            # Select random stress endpoint
            endpoint = random.choice(stress_endpoints)
            
            # Make stress request
            success, response_time, status_code = await self._make_stress_request(
                session, 
                endpoint, 
                stress_type, 
                user_id
            )
            
            user_results["total_requests"] += 1
            user_results["response_times"].append(response_time)
            
            if success:
                user_results["successful_requests"] += 1
            else:
                user_results["failed_requests"] += 1
                user_results["errors"].append({
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Shorter delay for stress testing (0.05 to 0.5 seconds)
            await asyncio.sleep(random.uniform(0.05, 0.5))
        
        return user_results
    
    def _get_stress_endpoints(self, stress_type: str) -> List[str]:
        """Get stress-specific endpoints."""
        base_endpoints = [
            "/api/v2/deposits",
            "/api/v2/processing-engines", 
            "/api/v2/detection-results",
            "/api/v2/rvm-status/1"
        ]
        
        if stress_type == "cpu":
            return base_endpoints + ["/api/v2/trigger-processing"]
        elif stress_type == "memory":
            return base_endpoints + ["/api/v2/upload"]
        elif stress_type == "network":
            return base_endpoints + ["/api/v2/upload", "/api/v2/processing-history"]
        elif stress_type == "disk":
            return base_endpoints + ["/api/v2/upload", "/api/v2/backup"]
        else:  # mixed
            return base_endpoints + ["/api/v2/trigger-processing", "/api/v2/upload", "/api/v2/processing-history"]
    
    async def _monitor_system_resources(self, duration: float):
        """Monitor system resources during stress test."""
        start_time = time.time()
        end_time = start_time + duration
        
        while time.time() < end_time and self.is_running:
            # CPU monitoring
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory monitoring
            memory = psutil.virtual_memory()
            
            # Disk monitoring
            disk = psutil.disk_usage('/')
            
            # Network monitoring (simplified)
            network_io = psutil.net_io_counters()
            
            self.monitoring_data.append({
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / 1024 / 1024,
                "memory_available_mb": memory.available / 1024 / 1024,
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / 1024 / 1024 / 1024,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                "network_bytes_sent": network_io.bytes_sent,
                "network_bytes_recv": network_io.bytes_recv
            })
            
            # Check for breaking point
            if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
                if not self.breaking_point:
                    self.breaking_point = len(self.monitoring_data)
                    self.logger.warning(f"Breaking point detected at monitoring point {self.breaking_point}")
            
            await asyncio.sleep(2)  # Monitor every 2 seconds for stress tests
    
    async def run_stress_test(self, scenario_name: str) -> StressTestResult:
        """Run a specific stress test scenario."""
        if scenario_name not in self.stress_scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.stress_scenarios[scenario_name]
        stress_type = scenario["stress_type"]
        
        self.logger.info(f"Starting {scenario['name']} with max {scenario['max_concurrent_users']} concurrent users")
        
        self.is_running = True
        self.monitoring_data = []
        self.breaking_point = None
        
        # Create HTTP session
        connector = aiohttp.TCPConnector(limit=self.max_workers)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Start system monitoring
            monitoring_task = asyncio.create_task(
                self._monitor_system_resources(scenario["duration"])
            )
            
            # Gradually ramp up users
            user_tasks = []
            start_time = time.time()
            ramp_up_rate = scenario["ramp_up_rate"]
            max_users = scenario["max_concurrent_users"]
            
            # Start users gradually
            for i in range(max_users):
                user_task = asyncio.create_task(
                    self._stress_user_simulation(session, i, scenario, stress_type)
                )
                user_tasks.append(user_task)
                
                # Wait before starting next user (ramp up)
                if i < max_users - 1:
                    await asyncio.sleep(1.0 / ramp_up_rate)
            
            # Wait for all users to complete
            user_results = await asyncio.gather(*user_tasks)
            
            # Stop monitoring
            self.is_running = False
            monitoring_task.cancel()
            
            end_time = time.time()
            test_duration = end_time - start_time
        
        # Calculate aggregated results
        total_requests = sum(result["total_requests"] for result in user_results)
        successful_requests = sum(result["successful_requests"] for result in user_results)
        failed_requests = sum(result["failed_requests"] for result in user_results)
        
        all_response_times = []
        for result in user_results:
            all_response_times.extend(result["response_times"])
        
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            max_response_time = max(all_response_times)
            p95_response_time = statistics.quantiles(all_response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(all_response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = max_response_time = p95_response_time = p99_response_time = 0.0
        
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate average system resources
        if self.monitoring_data:
            avg_cpu = statistics.mean([data["cpu_percent"] for data in self.monitoring_data])
            avg_memory = statistics.mean([data["memory_percent"] for data in self.monitoring_data])
            avg_disk = statistics.mean([data["disk_percent"] for data in self.monitoring_data])
            
            # Calculate network usage (simplified)
            if len(self.monitoring_data) > 1:
                network_usage = (self.monitoring_data[-1]["network_bytes_sent"] - self.monitoring_data[0]["network_bytes_sent"]) / test_duration
            else:
                network_usage = 0.0
        else:
            avg_cpu = avg_memory = avg_disk = network_usage = 0.0
        
        # Calculate recovery time (simplified)
        recovery_time = None
        if self.breaking_point and len(self.monitoring_data) > self.breaking_point:
            # Estimate recovery time as time after breaking point
            recovery_time = (len(self.monitoring_data) - self.breaking_point) * 2  # 2 seconds per monitoring point
        
        # Create result
        result = StressTestResult(
            timestamp=datetime.now().isoformat(),
            test_name=scenario["name"],
            stress_type=stress_type,
            max_concurrent_users=max_users,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            cpu_usage=avg_cpu,
            memory_usage=avg_memory,
            disk_usage=avg_disk,
            network_usage=network_usage,
            test_duration=test_duration,
            breaking_point=self.breaking_point,
            recovery_time=recovery_time
        )
        
        self.results.append(result)
        self.logger.info(f"Stress test completed: {result.requests_per_second:.2f} RPS, {result.error_rate:.2f}% error rate")
        
        return result
    
    def run_all_stress_tests(self) -> List[StressTestResult]:
        """Run all stress test scenarios."""
        self.logger.info("Starting comprehensive stress testing")
        
        all_results = []
        
        for scenario_name in self.stress_scenarios.keys():
            try:
                result = asyncio.run(self.run_stress_test(scenario_name))
                all_results.append(result)
                
                # Wait between tests for system recovery
                time.sleep(120)  # 2 minutes cooldown
                
            except Exception as e:
                self.logger.error(f"Stress test {scenario_name} failed: {e}")
        
        return all_results
    
    def save_results(self, filename: str = None):
        """Save test results to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_test_results_{timestamp}.json"
        
        results_file = Path(__file__).parent / "results" / filename
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert results to dictionaries
        results_data = [asdict(result) for result in self.results]
        
        with open(results_file, 'w') as f:
            json.dump({
                "test_results": results_data,
                "monitoring_data": self.monitoring_data,
                "test_summary": self.get_test_summary()
            }, f, indent=2)
        
        self.logger.info(f"Results saved to {results_file}")
    
    def save_results_csv(self, filename: str = None):
        """Save test results to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_test_results_{timestamp}.csv"
        
        results_file = Path(__file__).parent / "results" / filename
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.results:
            self.logger.warning("No results to save")
            return
        
        with open(results_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(self.results[0]).keys())
            writer.writeheader()
            for result in self.results:
                writer.writerow(asdict(result))
        
        self.logger.info(f"Results saved to {results_file}")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all stress test results."""
        if not self.results:
            return {"message": "No test results available"}
        
        total_tests = len(self.results)
        total_requests = sum(result.total_requests for result in self.results)
        total_successful = sum(result.successful_requests for result in self.results)
        total_failed = sum(result.failed_requests for result in self.results)
        
        avg_rps = statistics.mean([result.requests_per_second for result in self.results])
        avg_response_time = statistics.mean([result.average_response_time for result in self.results])
        avg_error_rate = statistics.mean([result.error_rate for result in self.results])
        avg_cpu = statistics.mean([result.cpu_usage for result in self.results])
        avg_memory = statistics.mean([result.memory_usage for result in self.results])
        avg_disk = statistics.mean([result.disk_usage for result in self.results])
        
        breaking_points = [result.breaking_point for result in self.results if result.breaking_point]
        recovery_times = [result.recovery_time for result in self.results if result.recovery_time]
        
        return {
            "total_tests": total_tests,
            "total_requests": total_requests,
            "total_successful_requests": total_successful,
            "total_failed_requests": total_failed,
            "overall_success_rate": (total_successful / total_requests * 100) if total_requests > 0 else 0,
            "average_requests_per_second": avg_rps,
            "average_response_time": avg_response_time,
            "average_error_rate": avg_error_rate,
            "average_cpu_usage": avg_cpu,
            "average_memory_usage": avg_memory,
            "average_disk_usage": avg_disk,
            "breaking_points_detected": len(breaking_points),
            "average_recovery_time": statistics.mean(recovery_times) if recovery_times else None,
            "test_scenarios": [result.test_name for result in self.results]
        }
    
    def print_results(self):
        """Print stress test results in a formatted way."""
        if not self.results:
            print("No test results available")
            return
        
        print("\n" + "="*80)
        print("STRESS TEST RESULTS SUMMARY")
        print("="*80)
        
        for result in self.results:
            print(f"\nTest: {result.test_name}")
            print(f"Stress Type: {result.stress_type}")
            print(f"Max Concurrent Users: {result.max_concurrent_users}")
            print(f"Duration: {result.test_duration:.2f} seconds")
            print(f"Total Requests: {result.total_requests}")
            print(f"Successful Requests: {result.successful_requests}")
            print(f"Failed Requests: {result.failed_requests}")
            print(f"Success Rate: {((result.successful_requests / result.total_requests) * 100):.2f}%")
            print(f"Requests/Second: {result.requests_per_second:.2f}")
            print(f"Average Response Time: {result.average_response_time:.3f}s")
            print(f"Max Response Time: {result.max_response_time:.3f}s")
            print(f"95th Percentile Response Time: {result.p95_response_time:.3f}s")
            print(f"99th Percentile Response Time: {result.p99_response_time:.3f}s")
            print(f"Error Rate: {result.error_rate:.2f}%")
            print(f"Average CPU Usage: {result.cpu_usage:.2f}%")
            print(f"Average Memory Usage: {result.memory_usage:.2f}%")
            print(f"Average Disk Usage: {result.disk_usage:.2f}%")
            print(f"Network Usage: {result.network_usage:.2f} bytes/s")
            if result.breaking_point:
                print(f"Breaking Point Detected: Yes (at monitoring point {result.breaking_point})")
            else:
                print(f"Breaking Point Detected: No")
            if result.recovery_time:
                print(f"Recovery Time: {result.recovery_time:.2f} seconds")
            print("-" * 40)
        
        # Print overall summary
        summary = self.get_test_summary()
        print(f"\nOVERALL SUMMARY:")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Overall Success Rate: {summary['overall_success_rate']:.2f}%")
        print(f"Average RPS: {summary['average_requests_per_second']:.2f}")
        print(f"Average Response Time: {summary['average_response_time']:.3f}s")
        print(f"Average Error Rate: {summary['average_error_rate']:.2f}%")
        print(f"Average CPU Usage: {summary['average_cpu_usage']:.2f}%")
        print(f"Average Memory Usage: {summary['average_memory_usage']:.2f}%")
        print(f"Average Disk Usage: {summary['average_disk_usage']:.2f}%")
        print(f"Breaking Points Detected: {summary['breaking_points_detected']}")
        if summary['average_recovery_time']:
            print(f"Average Recovery Time: {summary['average_recovery_time']:.2f} seconds")

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
    
    # Create stress test framework
    stress_test = StressTestFramework(config)
    
    # Run a single test scenario
    print("Running CPU stress test...")
    result = asyncio.run(stress_test.run_stress_test("cpu_stress"))
    
    # Print results
    stress_test.print_results()
    
    # Save results
    stress_test.save_results()
    stress_test.save_results_csv()

if __name__ == "__main__":
    main()
