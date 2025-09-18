#!/usr/bin/env python3
"""
MyRVM Platform Integration - End-to-End Testing Framework
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import sys
sys.path.append(str(project_root / "api-client"))
from myrvm_api_client import MyRVMAPIClient

class E2ETestFramework:
    """End-to-end testing framework for MyRVM Platform Integration."""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.results_dir = self.project_root / "testing" / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize API client
        base_url = config.get('myrvm_base_url', 'http://localhost:8000')
        self.api_client = MyRVMAPIClient(base_url)
        
        # Test results
        self.test_results = []
        
    def test_api_connectivity(self):
        """Test API connectivity and authentication."""
        self.logger.info("Testing API connectivity")
        
        start_time = time.time()
        try:
            # Test authentication
            auth_result = self.api_client.login(
                self.config['myrvm_username'],
                self.config['myrvm_password']
            )
            
            if auth_result:
                self.logger.info("API connectivity test PASSED")
                return {"status": "PASS", "duration": time.time() - start_time}
            else:
                self.logger.error("API connectivity test FAILED")
                return {"status": "FAIL", "duration": time.time() - start_time}
                
        except Exception as e:
            self.logger.error(f"API connectivity test failed: {e}")
            return {"status": "FAIL", "duration": time.time() - start_time, "error": str(e)}
    
    def test_engine_registration(self):
        """Test processing engine registration."""
        self.logger.info("Testing engine registration")
        
        start_time = time.time()
        try:
            engine_data = {
                "name": "Jetson Orin Nano E2E Test",
                "type": "jetson_orin_nano",
                "status": "active",
                "capabilities": ["object_detection", "image_processing"],
                "gpu_memory_limit": 8192,
                "max_concurrent_requests": 10,
                "location": "Test Environment",
                "ip_address": "192.168.1.100",
                "port": 8080
            }
            
            result = self.api_client.register_processing_engine(engine_data)
            
            if result:
                self.logger.info("Engine registration test PASSED")
                return {"status": "PASS", "duration": time.time() - start_time}
            else:
                self.logger.error("Engine registration test FAILED")
                return {"status": "FAIL", "duration": time.time() - start_time}
            
        except Exception as e:
            self.logger.error(f"Engine registration test failed: {e}")
            return {"status": "FAIL", "duration": time.time() - start_time, "error": str(e)}
    
    def test_deposit_creation(self):
        """Test deposit creation."""
        self.logger.info("Testing deposit creation")
        
        start_time = time.time()
        try:
            deposit_data = {
                "location": "Test Location",
                "type": "plastic_bottle",
                "weight": 0.5,
                "status": "detected"
            }
            
            result = self.api_client.create_deposit(deposit_data)
            
            if result:
                self.logger.info("Deposit creation test PASSED")
                return {"status": "PASS", "duration": time.time() - start_time, "deposit_id": result.get('id')}
            else:
                self.logger.error("Deposit creation test FAILED")
                return {"status": "FAIL", "duration": time.time() - start_time}
                
        except Exception as e:
            self.logger.error(f"Deposit creation test failed: {e}")
            return {"status": "FAIL", "duration": time.time() - start_time, "error": str(e)}
    
    def run_all_tests(self):
        """Run all end-to-end tests."""
        self.logger.info("Starting end-to-end testing")
        
        tests = [
            ("API Connectivity", self.test_api_connectivity),
            ("Engine Registration", self.test_engine_registration),
            ("Deposit Creation", self.test_deposit_creation)
        ]
        
        results = []
        for test_name, test_func in tests:
            self.logger.info(f"Running {test_name} test...")
            result = test_func()
            result["test_name"] = test_name
            results.append(result)
            time.sleep(1)  # Cooldown between tests
        
        self.test_results = results
        return results
    
    def generate_report(self):
        """Generate test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                    "timestamp": datetime.now().isoformat()
            },
            "results": self.test_results
        }
        
        return report
    
    def save_report(self, report):
        """Save test report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"e2e_test_report_{timestamp}.json"
        report_path = self.results_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"E2E test report saved to: {report_path}")
        return report_path

def main():
    """Main function."""
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
    
    # Run tests
    e2e_test = E2ETestFramework(config)
    results = e2e_test.run_all_tests()
    report = e2e_test.generate_report()
    report_path = e2e_test.save_report(report)
    
    print(f"E2E testing completed. Report saved to: {report_path}")
    
    # Print summary
    summary = report["summary"]
    print(f"\nTest Summary:")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.2f}%")

if __name__ == "__main__":
    main()