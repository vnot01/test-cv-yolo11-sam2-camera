#!/usr/bin/env python3
"""
MyRVM Platform Integration - Dependency Manager
Manages service dependencies, startup order, and dependency resolution.
"""

import os
import sys
import time
import logging
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import json
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
import networkx as nx
from collections import defaultdict, deque

class DependencyManager:
    """
    Manages service dependencies and ensures proper startup order.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.dependency_graph = nx.DiGraph()
        self.service_status: Dict[str, str] = {}
        self.service_health: Dict[str, bool] = {}
        self.dependency_checks: Dict[str, callable] = {}
        self.startup_order: List[str] = []
        self.shutdown_order: List[str] = []
        
        self._load_dependency_configuration()
        self._setup_dependency_checks()
        self._calculate_startup_order()
        
    def _load_dependency_configuration(self):
        """Load dependency configuration from config files."""
        try:
            # Define service dependencies
            dependencies = {
                # Core services
                "configuration_manager": [],
                "logging_system": [],
                "security_manager": ["configuration_manager"],
                
                # API and connectivity
                "api_client": ["configuration_manager", "security_manager"],
                "network_manager": ["configuration_manager"],
                
                # Core application services
                "camera_service": ["configuration_manager", "logging_system"],
                "detection_service": ["camera_service", "api_client"],
                "monitoring_service": ["configuration_manager", "logging_system"],
                
                # Advanced services
                "backup_manager": ["configuration_manager", "logging_system"],
                "recovery_manager": ["backup_manager"],
                "metrics_collector": ["monitoring_service"],
                "alerting_engine": ["metrics_collector"],
                "dashboard_server": ["metrics_collector", "alerting_engine"],
                
                # System services
                "service_manager": ["configuration_manager"],
                "health_monitor": ["monitoring_service"],
                "performance_monitor": ["metrics_collector"],
                
                # Main application
                "main_application": [
                    "configuration_manager",
                    "logging_system",
                    "security_manager",
                    "api_client",
                    "camera_service",
                    "detection_service",
                    "monitoring_service"
                ]
            }
            
            # Add services to dependency graph
            for service, deps in dependencies.items():
                self.dependency_graph.add_node(service)
                for dep in deps:
                    self.dependency_graph.add_edge(dep, service)
            
            self.logger.info(f"Loaded dependency graph with {len(self.dependency_graph.nodes)} services")
            
        except Exception as e:
            self.logger.error(f"Failed to load dependency configuration: {e}")
            raise
    
    def _setup_dependency_checks(self):
        """Setup dependency check functions for each service."""
        self.dependency_checks = {
            "configuration_manager": self._check_configuration_manager,
            "logging_system": self._check_logging_system,
            "security_manager": self._check_security_manager,
            "api_client": self._check_api_client,
            "network_manager": self._check_network_manager,
            "camera_service": self._check_camera_service,
            "detection_service": self._check_detection_service,
            "monitoring_service": self._check_monitoring_service,
            "backup_manager": self._check_backup_manager,
            "recovery_manager": self._check_recovery_manager,
            "metrics_collector": self._check_metrics_collector,
            "alerting_engine": self._check_alerting_engine,
            "dashboard_server": self._check_dashboard_server,
            "service_manager": self._check_service_manager,
            "health_monitor": self._check_health_monitor,
            "performance_monitor": self._check_performance_monitor,
            "main_application": self._check_main_application
        }
    
    def _check_configuration_manager(self) -> bool:
        """Check if configuration manager is ready."""
        try:
            config_path = Path(__file__).parent.parent / "config"
            return config_path.exists() and len(list(config_path.glob("*.json"))) > 0
        except:
            return False
    
    def _check_logging_system(self) -> bool:
        """Check if logging system is ready."""
        try:
            logs_path = Path(__file__).parent.parent / "logs"
            return logs_path.exists()
        except:
            return False
    
    def _check_security_manager(self) -> bool:
        """Check if security manager is ready."""
        try:
            security_file = Path(__file__).parent.parent / "config" / "security_manager.py"
            return security_file.exists()
        except:
            return False
    
    def _check_api_client(self) -> bool:
        """Check if API client is ready."""
        try:
            api_client_file = Path(__file__).parent.parent / "api-client" / "myrvm_api_client.py"
            return api_client_file.exists()
        except:
            return False
    
    def _check_network_manager(self) -> bool:
        """Check if network manager is ready."""
        try:
            import requests
            return True
        except:
            return False
    
    def _check_camera_service(self) -> bool:
        """Check if camera service is ready."""
        try:
            camera_service_file = Path(__file__).parent / "camera_service.py"
            return camera_service_file.exists()
        except:
            return False
    
    def _check_detection_service(self) -> bool:
        """Check if detection service is ready."""
        try:
            detection_service_file = Path(__file__).parent / "optimized_detection_service.py"
            return detection_service_file.exists()
        except:
            return False
    
    def _check_monitoring_service(self) -> bool:
        """Check if monitoring service is ready."""
        try:
            monitoring_service_file = Path(__file__).parent / "monitoring_service.py"
            return monitoring_service_file.exists()
        except:
            return False
    
    def _check_backup_manager(self) -> bool:
        """Check if backup manager is ready."""
        try:
            backup_manager_file = Path(__file__).parent.parent / "backup" / "backup_manager.py"
            return backup_manager_file.exists()
        except:
            return False
    
    def _check_recovery_manager(self) -> bool:
        """Check if recovery manager is ready."""
        try:
            recovery_manager_file = Path(__file__).parent.parent / "backup" / "recovery_manager.py"
            return recovery_manager_file.exists()
        except:
            return False
    
    def _check_metrics_collector(self) -> bool:
        """Check if metrics collector is ready."""
        try:
            metrics_collector_file = Path(__file__).parent.parent / "monitoring" / "metrics_collector.py"
            return metrics_collector_file.exists()
        except:
            return False
    
    def _check_alerting_engine(self) -> bool:
        """Check if alerting engine is ready."""
        try:
            alerting_engine_file = Path(__file__).parent.parent / "monitoring" / "alerting_engine.py"
            return alerting_engine_file.exists()
        except:
            return False
    
    def _check_dashboard_server(self) -> bool:
        """Check if dashboard server is ready."""
        try:
            dashboard_server_file = Path(__file__).parent.parent / "monitoring" / "dashboard_server.py"
            return dashboard_server_file.exists()
        except:
            return False
    
    def _check_service_manager(self) -> bool:
        """Check if service manager is ready."""
        try:
            service_manager_file = Path(__file__).parent.parent / "config" / "service_manager.py"
            return service_manager_file.exists()
        except:
            return False
    
    def _check_health_monitor(self) -> bool:
        """Check if health monitor is ready."""
        try:
            health_monitor_file = Path(__file__).parent.parent / "monitoring" / "health_monitor.py"
            return health_monitor_file.exists()
        except:
            return False
    
    def _check_performance_monitor(self) -> bool:
        """Check if performance monitor is ready."""
        try:
            performance_monitor_file = Path(__file__).parent.parent / "utils" / "performance_monitor.py"
            return performance_monitor_file.exists()
        except:
            return False
    
    def _check_main_application(self) -> bool:
        """Check if main application is ready."""
        try:
            main_app_file = Path(__file__).parent.parent / "main" / "enhanced_jetson_main.py"
            return main_app_file.exists()
        except:
            return False
    
    def _calculate_startup_order(self):
        """Calculate the correct startup order based on dependencies."""
        try:
            # Use topological sort to determine startup order
            self.startup_order = list(nx.topological_sort(self.dependency_graph))
            
            # Calculate shutdown order (reverse of startup order)
            self.shutdown_order = list(reversed(self.startup_order))
            
            self.logger.info(f"Calculated startup order: {self.startup_order}")
            self.logger.info(f"Calculated shutdown order: {self.shutdown_order}")
            
        except nx.NetworkXError as e:
            self.logger.error(f"Circular dependency detected: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to calculate startup order: {e}")
            raise
    
    def check_dependencies(self, service: str) -> Tuple[bool, List[str]]:
        """Check if all dependencies for a service are satisfied."""
        if service not in self.dependency_graph:
            return False, [f"Service {service} not found in dependency graph"]
        
        missing_deps = []
        for dep in self.dependency_graph.predecessors(service):
            if not self.is_service_ready(dep):
                missing_deps.append(dep)
        
        return len(missing_deps) == 0, missing_deps
    
    def is_service_ready(self, service: str) -> bool:
        """Check if a service is ready."""
        if service not in self.service_health:
            # Check if service is available
            if service in self.dependency_checks:
                self.service_health[service] = self.dependency_checks[service]()
            else:
                self.service_health[service] = False
        
        return self.service_health[service]
    
    def get_ready_services(self) -> List[str]:
        """Get list of services that are ready to start."""
        ready_services = []
        
        for service in self.startup_order:
            if self.service_status.get(service) == "running":
                continue
            
            deps_satisfied, missing_deps = self.check_dependencies(service)
            if deps_satisfied and self.is_service_ready(service):
                ready_services.append(service)
        
        return ready_services
    
    def get_blocked_services(self) -> Dict[str, List[str]]:
        """Get services that are blocked by missing dependencies."""
        blocked_services = {}
        
        for service in self.startup_order:
            if self.service_status.get(service) == "running":
                continue
            
            deps_satisfied, missing_deps = self.check_dependencies(service)
            if not deps_satisfied:
                blocked_services[service] = missing_deps
        
        return blocked_services
    
    def start_service(self, service: str) -> bool:
        """Start a specific service."""
        if service not in self.dependency_graph:
            self.logger.error(f"Service {service} not found in dependency graph")
            return False
        
        if self.service_status.get(service) == "running":
            self.logger.warning(f"Service {service} is already running")
            return True
        
        # Check dependencies
        deps_satisfied, missing_deps = self.check_dependencies(service)
        if not deps_satisfied:
            self.logger.error(f"Cannot start {service}: missing dependencies {missing_deps}")
            return False
        
        # Check if service is ready
        if not self.is_service_ready(service):
            self.logger.error(f"Service {service} is not ready")
            return False
        
        try:
            self.logger.info(f"Starting service: {service}")
            self.service_status[service] = "starting"
            
            # Simulate service startup (in real implementation, this would start actual services)
            time.sleep(0.1)  # Simulate startup time
            
            self.service_status[service] = "running"
            self.logger.info(f"Service {service} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start service {service}: {e}")
            self.service_status[service] = "failed"
            return False
    
    def stop_service(self, service: str) -> bool:
        """Stop a specific service."""
        if service not in self.dependency_graph:
            self.logger.error(f"Service {service} not found in dependency graph")
            return False
        
        if self.service_status.get(service) != "running":
            self.logger.warning(f"Service {service} is not running")
            return True
        
        try:
            self.logger.info(f"Stopping service: {service}")
            self.service_status[service] = "stopping"
            
            # Simulate service shutdown (in real implementation, this would stop actual services)
            time.sleep(0.1)  # Simulate shutdown time
            
            self.service_status[service] = "stopped"
            self.logger.info(f"Service {service} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop service {service}: {e}")
            self.service_status[service] = "error"
            return False
    
    def start_all_services(self) -> Dict[str, bool]:
        """Start all services in the correct order."""
        results = {}
        
        self.logger.info("🚀 Starting all services in dependency order")
        
        for service in self.startup_order:
            success = self.start_service(service)
            results[service] = success
            
            if not success:
                self.logger.error(f"Failed to start {service}, stopping startup sequence")
                break
        
        return results
    
    def stop_all_services(self) -> Dict[str, bool]:
        """Stop all services in the correct order."""
        results = {}
        
        self.logger.info("🛑 Stopping all services in reverse dependency order")
        
        for service in self.shutdown_order:
            success = self.stop_service(service)
            results[service] = success
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        return {
            "service_status": self.service_status,
            "service_health": self.service_health,
            "startup_order": self.startup_order,
            "shutdown_order": self.shutdown_order,
            "ready_services": self.get_ready_services(),
            "blocked_services": self.get_blocked_services(),
            "total_services": len(self.dependency_graph.nodes),
            "running_services": len([s for s in self.service_status.values() if s == "running"]),
            "failed_services": len([s for s in self.service_status.values() if s == "failed"])
        }
    
    def get_dependency_graph(self) -> Dict[str, Any]:
        """Get dependency graph information."""
        return {
            "nodes": list(self.dependency_graph.nodes),
            "edges": list(self.dependency_graph.edges),
            "is_dag": nx.is_directed_acyclic_graph(self.dependency_graph),
            "cycles": list(nx.simple_cycles(self.dependency_graph)) if not nx.is_directed_acyclic_graph(self.dependency_graph) else []
        }
    
    def validate_dependencies(self) -> bool:
        """Validate that the dependency graph is valid."""
        try:
            # Check for cycles
            if not nx.is_directed_acyclic_graph(self.dependency_graph):
                cycles = list(nx.simple_cycles(self.dependency_graph))
                self.logger.error(f"Circular dependencies detected: {cycles}")
                return False
            
            # Check that all services have dependency checks
            missing_checks = []
            for service in self.dependency_graph.nodes:
                if service not in self.dependency_checks:
                    missing_checks.append(service)
            
            if missing_checks:
                self.logger.warning(f"Missing dependency checks for services: {missing_checks}")
            
            self.logger.info("Dependency validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Dependency validation failed: {e}")
            return False

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
    
    # Create dependency manager
    dep_manager = DependencyManager(config)
    
    # Validate dependencies
    if not dep_manager.validate_dependencies():
        print("❌ Dependency validation failed")
        return
    
    print("✅ Dependency validation passed")
    
    # Get service status
    status = dep_manager.get_service_status()
    print(f"Service Status: {status}")
    
    # Start all services
    results = dep_manager.start_all_services()
    print(f"Startup Results: {results}")

if __name__ == "__main__":
    main()
