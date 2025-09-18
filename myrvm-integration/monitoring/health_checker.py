#!/usr/bin/env python3
"""
Health Checker for MyRVM Platform Integration
Automated health checks and recovery actions
"""

import json
import time
import logging
import threading
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import psutil

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "services"))

from monitoring_service import MonitoringService

class HealthChecker:
    """Automated health checking and recovery system"""
    
    def __init__(self, config: Dict):
        """
        Initialize health checker
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Health check configuration
        self.check_interval = config.get('health_check_interval', 60)
        self.timeout = config.get('health_check_timeout', 30)
        self.retry_count = config.get('health_check_retry_count', 3)
        self.recovery_enabled = config.get('health_recovery_enabled', True)
        
        # Health check definitions
        self.health_checks = {
            'system_resources': {
                'enabled': True,
                'critical_thresholds': {
                    'cpu_percent': 90,
                    'memory_percent': 90,
                    'disk_percent': 95,
                    'temperature': 85
                },
                'warning_thresholds': {
                    'cpu_percent': 80,
                    'memory_percent': 80,
                    'disk_percent': 85,
                    'temperature': 75
                }
            },
            'service_availability': {
                'enabled': True,
                'services': [
                    'myrvm-integration',
                    'camera-service',
                    'monitoring-service'
                ]
            },
            'api_connectivity': {
                'enabled': True,
                'endpoints': [
                    'http://172.28.233.83:8001/api/v2/deposits',
                    'http://172.28.233.83:8001/api/v2/processing-engines'
                ]
            },
            'database_connectivity': {
                'enabled': True,
                'databases': [
                    'metrics.db',
                    'logs.db'
                ]
            },
            'network_connectivity': {
                'enabled': True,
                'targets': [
                    '172.28.233.83',
                    '8.8.8.8'
                ]
            }
        }
        
        # Recovery actions
        self.recovery_actions = {
            'restart_service': {
                'enabled': True,
                'services': ['myrvm-integration']
            },
            'clear_temp_files': {
                'enabled': True,
                'paths': ['/tmp', '/var/tmp']
            },
            'restart_network': {
                'enabled': False,
                'interfaces': ['eth0', 'wlan0']
            }
        }
        
        # Health status
        self.health_status = {
            'overall': 'unknown',
            'score': 0,
            'checks': {},
            'last_check': None,
            'recovery_actions_taken': []
        }
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize monitoring service
        self.monitoring_service = MonitoringService(config)
        
        # Health check thread
        self.health_thread = None
        self.is_running = False
        
        # Load health configuration
        self._load_health_config()
        
        self.logger.info("Health checker initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for health checker"""
        logger = logging.getLogger('HealthChecker')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'health_checker_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_health_config(self):
        """Load health configuration from file"""
        config_file = Path(__file__).parent / 'config' / 'health.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                self.health_checks.update(config_data.get('health_checks', {}))
                self.recovery_actions.update(config_data.get('recovery_actions', {}))
                
                self.logger.info("Health configuration loaded from file")
            except Exception as e:
                self.logger.error(f"Failed to load health configuration: {e}")
        else:
            # Create default configuration
            self._save_health_config()
    
    def _save_health_config(self):
        """Save health configuration to file"""
        try:
            config_file = Path(__file__).parent / 'config' / 'health.json'
            config_file.parent.mkdir(exist_ok=True)
            
            config_data = {
                'health_checks': self.health_checks,
                'recovery_actions': self.recovery_actions,
                'check_interval': self.check_interval,
                'timeout': self.timeout,
                'retry_count': self.retry_count,
                'recovery_enabled': self.recovery_enabled
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info("Health configuration saved to file")
            
        except Exception as e:
            self.logger.error(f"Failed to save health configuration: {e}")
    
    def check_system_resources(self) -> Dict:
        """Check system resource health"""
        try:
            check_result = {
                'status': 'healthy',
                'score': 100,
                'details': {},
                'issues': []
            }
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check CPU
            if cpu_percent > self.health_checks['system_resources']['critical_thresholds']['cpu_percent']:
                check_result['status'] = 'critical'
                check_result['score'] -= 30
                check_result['issues'].append(f'Critical CPU usage: {cpu_percent:.1f}%')
            elif cpu_percent > self.health_checks['system_resources']['warning_thresholds']['cpu_percent']:
                if check_result['status'] == 'healthy':
                    check_result['status'] = 'warning'
                check_result['score'] -= 15
                check_result['issues'].append(f'High CPU usage: {cpu_percent:.1f}%')
            
            check_result['details']['cpu_percent'] = cpu_percent
            
            # Check Memory
            if memory.percent > self.health_checks['system_resources']['critical_thresholds']['memory_percent']:
                check_result['status'] = 'critical'
                check_result['score'] -= 30
                check_result['issues'].append(f'Critical memory usage: {memory.percent:.1f}%')
            elif memory.percent > self.health_checks['system_resources']['warning_thresholds']['memory_percent']:
                if check_result['status'] == 'healthy':
                    check_result['status'] = 'warning'
                check_result['score'] -= 15
                check_result['issues'].append(f'High memory usage: {memory.percent:.1f}%')
            
            check_result['details']['memory_percent'] = memory.percent
            
            # Check Disk
            if disk.percent > self.health_checks['system_resources']['critical_thresholds']['disk_percent']:
                check_result['status'] = 'critical'
                check_result['score'] -= 25
                check_result['issues'].append(f'Critical disk usage: {disk.percent:.1f}%')
            elif disk.percent > self.health_checks['system_resources']['warning_thresholds']['disk_percent']:
                if check_result['status'] == 'healthy':
                    check_result['status'] = 'warning'
                check_result['score'] -= 10
                check_result['issues'].append(f'High disk usage: {disk.percent:.1f}%')
            
            check_result['details']['disk_percent'] = disk.percent
            
            # Check Temperature (if available)
            try:
                import psutil
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            if 'cpu' in name.lower() or 'core' in name.lower():
                                temp = entry.current
                                if temp > self.health_checks['system_resources']['critical_thresholds']['temperature']:
                                    check_result['status'] = 'critical'
                                    check_result['score'] -= 20
                                    check_result['issues'].append(f'Critical temperature: {temp:.1f}°C')
                                elif temp > self.health_checks['system_resources']['warning_thresholds']['temperature']:
                                    if check_result['status'] == 'healthy':
                                        check_result['status'] = 'warning'
                                    check_result['score'] -= 10
                                    check_result['issues'].append(f'High temperature: {temp:.1f}°C')
                                
                                check_result['details']['temperature'] = temp
                                break
            except Exception:
                pass  # Temperature checking not available
            
            return check_result
            
        except Exception as e:
            self.logger.error(f"Failed to check system resources: {e}")
            return {
                'status': 'error',
                'score': 0,
                'details': {},
                'issues': [f'System resource check failed: {str(e)}']
            }
    
    def check_service_availability(self) -> Dict:
        """Check service availability"""
        try:
            check_result = {
                'status': 'healthy',
                'score': 100,
                'details': {},
                'issues': []
            }
            
            services = self.health_checks['service_availability']['services']
            
            for service in services:
                try:
                    # Check if service is running using systemctl
                    result = subprocess.run(
                        ['systemctl', 'is-active', service],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0 and result.stdout and result.stdout.strip() == 'active':
                        check_result['details'][service] = 'active'
                    else:
                        check_result['status'] = 'critical'
                        check_result['score'] -= 25
                        check_result['issues'].append(f'Service {service} is not active')
                        check_result['details'][service] = 'inactive'
                        
                except Exception as e:
                    check_result['status'] = 'critical'
                    check_result['score'] -= 25
                    check_result['issues'].append(f'Failed to check service {service}: {str(e)}')
                    check_result['details'][service] = 'error'
            
            return check_result
            
        except Exception as e:
            self.logger.error(f"Failed to check service availability: {e}")
            return {
                'status': 'error',
                'score': 0,
                'details': {},
                'issues': [f'Service availability check failed: {str(e)}']
            }
    
    def check_api_connectivity(self) -> Dict:
        """Check API connectivity"""
        try:
            check_result = {
                'status': 'healthy',
                'score': 100,
                'details': {},
                'issues': []
            }
            
            endpoints = self.health_checks['api_connectivity']['endpoints']
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=self.timeout)
                    if response.status_code == 200:
                        check_result['details'][endpoint] = 'accessible'
                    else:
                        check_result['status'] = 'warning'
                        check_result['score'] -= 15
                        check_result['issues'].append(f'API endpoint {endpoint} returned status {response.status_code}')
                        check_result['details'][endpoint] = f'status_{response.status_code}'
                        
                except requests.exceptions.RequestException as e:
                    check_result['status'] = 'critical'
                    check_result['score'] -= 25
                    check_result['issues'].append(f'API endpoint {endpoint} is not accessible: {str(e)}')
                    check_result['details'][endpoint] = 'inaccessible'
            
            return check_result
            
        except Exception as e:
            self.logger.error(f"Failed to check API connectivity: {e}")
            return {
                'status': 'error',
                'score': 0,
                'details': {},
                'issues': [f'API connectivity check failed: {str(e)}']
            }
    
    def check_database_connectivity(self) -> Dict:
        """Check database connectivity"""
        try:
            check_result = {
                'status': 'healthy',
                'score': 100,
                'details': {},
                'issues': []
            }
            
            databases = self.health_checks['database_connectivity']['databases']
            
            for db_name in databases:
                try:
                    db_path = Path(__file__).parent.parent / 'data' / db_name
                    if db_path.exists():
                        check_result['details'][db_name] = 'accessible'
                    else:
                        check_result['status'] = 'warning'
                        check_result['score'] -= 20
                        check_result['issues'].append(f'Database {db_name} not found')
                        check_result['details'][db_name] = 'not_found'
                        
                except Exception as e:
                    check_result['status'] = 'critical'
                    check_result['score'] -= 30
                    check_result['issues'].append(f'Database {db_name} check failed: {str(e)}')
                    check_result['details'][db_name] = 'error'
            
            return check_result
            
        except Exception as e:
            self.logger.error(f"Failed to check database connectivity: {e}")
            return {
                'status': 'error',
                'score': 0,
                'details': {},
                'issues': [f'Database connectivity check failed: {str(e)}']
            }
    
    def check_network_connectivity(self) -> Dict:
        """Check network connectivity"""
        try:
            check_result = {
                'status': 'healthy',
                'score': 100,
                'details': {},
                'issues': []
            }
            
            targets = self.health_checks['network_connectivity']['targets']
            
            for target in targets:
                try:
                    result = subprocess.run(
                        ['ping', '-c', '1', '-W', '5', target],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        check_result['details'][target] = 'reachable'
                    else:
                        check_result['status'] = 'warning'
                        check_result['score'] -= 20
                        check_result['issues'].append(f'Network target {target} is not reachable')
                        check_result['details'][target] = 'unreachable'
                        
                except Exception as e:
                    check_result['status'] = 'critical'
                    check_result['score'] -= 25
                    check_result['issues'].append(f'Network check failed for {target}: {str(e)}')
                    check_result['details'][target] = 'error'
            
            return check_result
            
        except Exception as e:
            self.logger.error(f"Failed to check network connectivity: {e}")
            return {
                'status': 'error',
                'score': 0,
                'details': {},
                'issues': [f'Network connectivity check failed: {str(e)}']
            }
    
    def perform_health_checks(self) -> Dict:
        """Perform all health checks"""
        try:
            health_results = {
                'overall': 'healthy',
                'score': 100,
                'checks': {},
                'last_check': datetime.now().isoformat(),
                'issues': []
            }
            
            # Perform individual health checks
            if self.health_checks['system_resources']['enabled']:
                health_results['checks']['system_resources'] = self.check_system_resources()
            
            if self.health_checks['service_availability']['enabled']:
                health_results['checks']['service_availability'] = self.check_service_availability()
            
            if self.health_checks['api_connectivity']['enabled']:
                health_results['checks']['api_connectivity'] = self.check_api_connectivity()
            
            if self.health_checks['database_connectivity']['enabled']:
                health_results['checks']['database_connectivity'] = self.check_database_connectivity()
            
            if self.health_checks['network_connectivity']['enabled']:
                health_results['checks']['network_connectivity'] = self.check_network_connectivity()
            
            # Calculate overall health
            total_score = 0
            check_count = 0
            critical_issues = 0
            warning_issues = 0
            
            for check_name, check_result in health_results['checks'].items():
                if check_result['status'] == 'critical':
                    critical_issues += 1
                elif check_result['status'] == 'warning':
                    warning_issues += 1
                
                total_score += check_result['score']
                check_count += 1
                
                health_results['issues'].extend(check_result.get('issues', []))
            
            if check_count > 0:
                health_results['score'] = total_score / check_count
            
            # Determine overall status
            if critical_issues > 0:
                health_results['overall'] = 'critical'
            elif warning_issues > 0:
                health_results['overall'] = 'warning'
            else:
                health_results['overall'] = 'healthy'
            
            # Update health status
            self.health_status = health_results
            
            return health_results
            
        except Exception as e:
            self.logger.error(f"Failed to perform health checks: {e}")
            return {
                'overall': 'error',
                'score': 0,
                'checks': {},
                'last_check': datetime.now().isoformat(),
                'issues': [f'Health check failed: {str(e)}']
            }
    
    def execute_recovery_actions(self, health_results: Dict):
        """Execute recovery actions based on health results"""
        if not self.recovery_enabled:
            return
        
        try:
            recovery_actions_taken = []
            
            # Check if recovery actions are needed
            if health_results['overall'] == 'critical':
                # Restart services if they're down
                if self.recovery_actions['restart_service']['enabled']:
                    for service in self.recovery_actions['restart_service']['services']:
                        try:
                            result = subprocess.run(
                                ['sudo', 'systemctl', 'restart', service],
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            
                            if result.returncode == 0:
                                recovery_actions_taken.append(f'Restarted service: {service}')
                                self.logger.info(f'Recovery action: Restarted service {service}')
                            else:
                                self.logger.error(f'Failed to restart service {service}: {result.stderr}')
                                
                        except Exception as e:
                            self.logger.error(f'Failed to restart service {service}: {e}')
                
                # Clear temporary files
                if self.recovery_actions['clear_temp_files']['enabled']:
                    for temp_path in self.recovery_actions['clear_temp_files']['paths']:
                        try:
                            result = subprocess.run(
                                ['find', temp_path, '-type', 'f', '-mtime', '+7', '-delete'],
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            
                            recovery_actions_taken.append(f'Cleared temp files: {temp_path}')
                            self.logger.info(f'Recovery action: Cleared temp files in {temp_path}')
                            
                        except Exception as e:
                            self.logger.error(f'Failed to clear temp files in {temp_path}: {e}')
            
            # Update recovery actions taken
            self.health_status['recovery_actions_taken'] = recovery_actions_taken
            
        except Exception as e:
            self.logger.error(f"Failed to execute recovery actions: {e}")
    
    def _health_check_worker(self):
        """Health check worker thread"""
        self.logger.info("Health check worker started")
        
        while self.is_running:
            try:
                # Perform health checks
                health_results = self.perform_health_checks()
                
                # Execute recovery actions if needed
                self.execute_recovery_actions(health_results)
                
                # Log health status
                self.logger.info(f"Health check completed: {health_results['overall']} (score: {health_results['score']:.1f})")
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Health check worker error: {e}")
                time.sleep(10)
        
        self.logger.info("Health check worker stopped")
    
    def start(self):
        """Start health checking"""
        if not self.is_running:
            self.is_running = True
            self.health_thread = threading.Thread(target=self._health_check_worker)
            self.health_thread.start()
            self.logger.info("Health checking started")
    
    def stop(self):
        """Stop health checking"""
        if self.is_running:
            self.is_running = False
            if self.health_thread:
                self.health_thread.join(timeout=5)
            self.logger.info("Health checking stopped")
    
    def get_health_status(self) -> Dict:
        """Get current health status"""
        return self.health_status
    
    def get_health_summary(self) -> Dict:
        """Get health check summary"""
        return {
            'is_running': self.is_running,
            'check_interval': self.check_interval,
            'recovery_enabled': self.recovery_enabled,
            'health_checks_enabled': {
                check_name: check_config['enabled'] 
                for check_name, check_config in self.health_checks.items()
            },
            'recovery_actions_enabled': {
                action_name: action_config['enabled'] 
                for action_name, action_config in self.recovery_actions.items()
            },
            'current_status': self.health_status
        }
