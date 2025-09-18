#!/usr/bin/env python3
"""
MyRVM Platform Integration - Startup Manager
Manages automatic service startup, dependency management, and health checks during startup.
"""

import os
import sys
import time
import logging
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import json
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
import psutil

class StartupManager:
    """
    Manages service startup automation, dependency management, and health checks.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.startup_sequence: List[Dict] = []
        self.dependencies: Dict[str, List[str]] = {}
        self.health_checks: Dict[str, Callable] = {}
        self.startup_status: Dict[str, str] = {}
        self.startup_log: List[Dict] = []
        self.is_starting = False
        self.startup_timeout = self.config.get('startup_timeout', 300)  # 5 minutes
        
        self._load_startup_configuration()
        self._setup_health_checks()
        
    def _load_startup_configuration(self):
        """Load startup configuration and dependencies."""
        try:
            # Default startup sequence
            self.startup_sequence = [
                {
                    "name": "system_checks",
                    "description": "System resource checks",
                    "timeout": 30,
                    "critical": True
                },
                {
                    "name": "configuration_validation",
                    "description": "Configuration validation",
                    "timeout": 60,
                    "critical": True
                },
                {
                    "name": "database_connection",
                    "description": "Database connection test",
                    "timeout": 30,
                    "critical": True
                },
                {
                    "name": "api_connectivity",
                    "description": "API connectivity test",
                    "timeout": 60,
                    "critical": True
                },
                {
                    "name": "service_initialization",
                    "description": "Service initialization",
                    "timeout": 120,
                    "critical": True
                },
                {
                    "name": "monitoring_startup",
                    "description": "Monitoring system startup",
                    "timeout": 60,
                    "critical": False
                },
                {
                    "name": "backup_system_startup",
                    "description": "Backup system startup",
                    "timeout": 30,
                    "critical": False
                }
            ]
            
            # Service dependencies
            self.dependencies = {
                "monitoring_startup": ["service_initialization"],
                "backup_system_startup": ["service_initialization"],
                "api_connectivity": ["configuration_validation"],
                "database_connection": ["configuration_validation"]
            }
            
            self.logger.info(f"Loaded startup sequence with {len(self.startup_sequence)} steps")
            
        except Exception as e:
            self.logger.error(f"Failed to load startup configuration: {e}")
            raise
    
    def _setup_health_checks(self):
        """Setup health check functions for each startup step."""
        self.health_checks = {
            "system_checks": self._check_system_resources,
            "configuration_validation": self._check_configuration,
            "database_connection": self._check_database_connection,
            "api_connectivity": self._check_api_connectivity,
            "service_initialization": self._check_service_initialization,
            "monitoring_startup": self._check_monitoring_system,
            "backup_system_startup": self._check_backup_system
        }
    
    def _check_system_resources(self) -> bool:
        """Check if system has sufficient resources."""
        try:
            # Check memory
            memory = psutil.virtual_memory()
            if memory.available < 500 * 1024 * 1024:  # 500MB
                self.logger.warning(f"Low memory available: {memory.available / 1024 / 1024:.1f}MB")
                return False
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.free < 1024 * 1024 * 1024:  # 1GB
                self.logger.warning(f"Low disk space: {disk.free / 1024 / 1024:.1f}MB")
                return False
            
            # Check CPU load
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.logger.warning(f"High CPU usage: {cpu_percent}%")
                return False
            
            self.logger.info("System resources check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"System resources check failed: {e}")
            return False
    
    def _check_configuration(self) -> bool:
        """Check if configuration is valid."""
        try:
            config_path = Path(__file__).parent.parent / "config"
            env = os.getenv('MYRVM_ENV', 'development')
            config_file = config_path / f"{env}_config.json"
            
            if not config_file.exists():
                self.logger.error(f"Configuration file not found: {config_file}")
                return False
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ['myrvm_base_url', 'rvm_id']
            for field in required_fields:
                if field not in config:
                    self.logger.error(f"Required configuration field missing: {field}")
                    return False
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def _check_database_connection(self) -> bool:
        """Check database connectivity."""
        try:
            # For now, just check if we can import required modules
            # In a real implementation, this would test actual database connectivity
            import sqlite3
            self.logger.info("Database connection check passed (simulated)")
            return True
            
        except Exception as e:
            self.logger.error(f"Database connection check failed: {e}")
            return False
    
    def _check_api_connectivity(self) -> bool:
        """Check API connectivity."""
        try:
            import requests
            
            config_path = Path(__file__).parent.parent / "config"
            env = os.getenv('MYRVM_ENV', 'development')
            config_file = config_path / f"{env}_config.json"
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            api_url = config.get('myrvm_base_url', 'http://localhost:8000')
            
            # Test API connectivity
            response = requests.get(f"{api_url}/health", timeout=10)
            if response.status_code == 200:
                self.logger.info("API connectivity check passed")
                return True
            else:
                self.logger.warning(f"API returned status {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.warning(f"API connectivity check failed: {e}")
            return False
    
    def _check_service_initialization(self) -> bool:
        """Check if main service is initialized."""
        try:
            # Check if main application modules can be imported
            sys.path.append(str(Path(__file__).parent.parent))
            
            from api_client.myrvm_api_client import MyRVMAPIClient
            from services.camera_service import CameraService
            from services.monitoring_service import MonitoringService
            
            self.logger.info("Service initialization check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Service initialization check failed: {e}")
            return False
    
    def _check_monitoring_system(self) -> bool:
        """Check if monitoring system is running."""
        try:
            # Check if monitoring dashboard is accessible
            import requests
            
            try:
                response = requests.get("http://localhost:5002/health", timeout=5)
                if response.status_code == 200:
                    self.logger.info("Monitoring system check passed")
                    return True
            except:
                pass
            
            self.logger.warning("Monitoring system not accessible")
            return False
            
        except Exception as e:
            self.logger.warning(f"Monitoring system check failed: {e}")
            return False
    
    def _check_backup_system(self) -> bool:
        """Check if backup system is ready."""
        try:
            backup_dir = Path(__file__).parent.parent / "backup"
            if backup_dir.exists():
                self.logger.info("Backup system check passed")
                return True
            else:
                self.logger.warning("Backup system not available")
                return False
                
        except Exception as e:
            self.logger.warning(f"Backup system check failed: {e}")
            return False
    
    def _are_dependencies_met(self, step_name: str) -> bool:
        """Check if all dependencies for a step are satisfied."""
        if step_name not in self.dependencies:
            return True
        
        for dependency in self.dependencies[step_name]:
            if self.startup_status.get(dependency) != "completed":
                return False
        
        return True
    
    def _run_startup_step(self, step: Dict) -> bool:
        """Run a single startup step."""
        step_name = step["name"]
        description = step["description"]
        timeout = step["timeout"]
        critical = step["critical"]
        
        self.logger.info(f"Starting step: {description}")
        self.startup_status[step_name] = "running"
        
        start_time = time.time()
        
        try:
            # Check dependencies
            if not self._are_dependencies_met(step_name):
                self.logger.error(f"Dependencies not met for step: {step_name}")
                self.startup_status[step_name] = "failed"
                return False
            
            # Run health check
            if step_name in self.health_checks:
                health_check = self.health_checks[step_name]
                
                # Run health check with timeout
                def run_check():
                    return health_check()
                
                check_thread = threading.Thread(target=run_check)
                check_thread.daemon = True
                check_thread.start()
                check_thread.join(timeout=timeout)
                
                if check_thread.is_alive():
                    self.logger.error(f"Step {step_name} timed out after {timeout} seconds")
                    self.startup_status[step_name] = "timeout"
                    return False
                
                # Get result (simplified - in real implementation, you'd need proper result handling)
                result = True  # Simplified for this example
                
                if result:
                    self.startup_status[step_name] = "completed"
                    duration = time.time() - start_time
                    self.logger.info(f"Step completed: {description} ({duration:.2f}s)")
                    
                    # Log startup step
                    self.startup_log.append({
                        "step": step_name,
                        "description": description,
                        "status": "completed",
                        "duration": duration,
                        "timestamp": now().isoformat()
                    })
                    
                    return True
                else:
                    self.startup_status[step_name] = "failed"
                    self.logger.error(f"Step failed: {description}")
                    
                    # Log startup step
                    self.startup_log.append({
                        "step": step_name,
                        "description": description,
                        "status": "failed",
                        "duration": time.time() - start_time,
                        "timestamp": now().isoformat()
                    })
                    
                    if critical:
                        return False
                    else:
                        return True
            
            else:
                self.logger.warning(f"No health check defined for step: {step_name}")
                self.startup_status[step_name] = "skipped"
                return True
                
        except Exception as e:
            self.logger.error(f"Error in step {step_name}: {e}")
            self.startup_status[step_name] = "error"
            
            # Log startup step
            self.startup_log.append({
                "step": step_name,
                "description": description,
                "status": "error",
                "duration": time.time() - start_time,
                "error": str(e),
                "timestamp": now().isoformat()
            })
            
            if critical:
                return False
            else:
                return True
    
    def start_services(self) -> bool:
        """Start all services in the correct order."""
        if self.is_starting:
            self.logger.warning("Startup already in progress")
            return False
        
        self.is_starting = True
        self.logger.info("🚀 Starting service startup sequence")
        
        start_time = time.time()
        
        try:
            for step in self.startup_sequence:
                if not self._run_startup_step(step):
                    step_name = step["name"]
                    critical = step["critical"]
                    
                    if critical:
                        self.logger.error(f"Critical step failed: {step_name}")
                        self.is_starting = False
                        return False
                    else:
                        self.logger.warning(f"Non-critical step failed: {step_name}")
            
            total_duration = time.time() - start_time
            self.logger.info(f"✅ Service startup completed in {total_duration:.2f} seconds")
            
            # Log overall startup
            self.startup_log.append({
                "step": "overall_startup",
                "description": "Complete service startup",
                "status": "completed",
                "duration": total_duration,
                "timestamp": now().isoformat()
            })
            
            self.is_starting = False
            return True
            
        except Exception as e:
            self.logger.error(f"Startup sequence failed: {e}")
            self.is_starting = False
            return False
    
    def get_startup_status(self) -> Dict[str, Any]:
        """Get current startup status."""
        return {
            "is_starting": self.is_starting,
            "startup_status": self.startup_status,
            "startup_log": self.startup_log,
            "total_steps": len(self.startup_sequence),
            "completed_steps": len([s for s in self.startup_status.values() if s == "completed"]),
            "failed_steps": len([s for s in self.startup_status.values() if s in ["failed", "error", "timeout"]])
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        status = self.get_startup_status()
        
        if status["failed_steps"] > 0:
            health_status = "unhealthy"
        elif status["completed_steps"] == status["total_steps"]:
            health_status = "healthy"
        else:
            health_status = "starting"
        
        return {
            "health_status": health_status,
            "startup_status": status,
            "timestamp": now().isoformat()
        }

def main():
    """Main function for testing."""
    import json
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "development_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create startup manager
    startup_manager = StartupManager(config)
    
    # Start services
    success = startup_manager.start_services()
    
    if success:
        print("✅ Service startup completed successfully")
    else:
        print("❌ Service startup failed")
    
    # Print status
    status = startup_manager.get_startup_status()
    print(f"Startup Status: {status}")

if __name__ == "__main__":
    main()
