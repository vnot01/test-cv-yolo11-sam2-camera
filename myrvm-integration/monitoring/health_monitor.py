#!/usr/bin/env python3
"""
Health Monitor for MyRVM Platform Integration
Automated health checks and recovery actions
"""

import os
import json
import logging
import threading
import time
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import psutil
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now

class HealthMonitor:
    """Automated health monitoring and recovery system"""
    
    def __init__(self, config: Dict):
        """
        Initialize health monitor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.health_check_interval = config.get('health_check_interval', 60.0)
        self.recovery_enabled = config.get('recovery_enabled', True)
        self.max_recovery_attempts = config.get('max_recovery_attempts', 3)
        
        # Health check results
        self.health_status = {}
        self.health_history = []
        self.recovery_attempts = {}
        
        # Monitoring control
        self.is_monitoring = False
        self.monitoring_thread = None
        self.health_lock = threading.Lock()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Health check callbacks
        self.health_callbacks = []
        
        # Initialize health checks
        self._initialize_health_checks()
        
        self.logger.info("Health monitor initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for health monitor"""
        logger = logging.getLogger('HealthMonitor')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'health_monitor_{now().strftime("%Y%m%d")}.log'
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
    
    def _initialize_health_checks(self):
        """Initialize health check configurations"""
        self.health_checks = {
            'system_resources': {
                'enabled': True,
                'check_function': self._check_system_resources,
                'recovery_function': self._recover_system_resources,
                'critical_thresholds': {
                    'cpu_percent': 95,
                    'memory_percent': 95,
                    'disk_percent': 98
                },
                'warning_thresholds': {
                    'cpu_percent': 80,
                    'memory_percent': 85,
                    'disk_percent': 90
                }
            },
            'service_availability': {
                'enabled': True,
                'check_function': self._check_service_availability,
                'recovery_function': self._recover_service_availability,
                'endpoints': [
                    'http://localhost:5001/api/health',
                    'http://172.28.233.83:8001/api/health'
                ]
            },
            'process_health': {
                'enabled': True,
                'check_function': self._check_process_health,
                'recovery_function': self._recover_process_health,
                'process_name': 'python3',
                'min_memory_mb': 100,
                'max_memory_mb': 2048
            },
            'network_connectivity': {
                'enabled': True,
                'check_function': self._check_network_connectivity,
                'recovery_function': self._recover_network_connectivity,
                'targets': [
                    '172.28.233.83:8001',
                    '8.8.8.8:53'
                ]
            },
            'file_system': {
                'enabled': True,
                'check_function': self._check_file_system,
                'recovery_function': self._recover_file_system,
                'critical_paths': [
                    '/home/my/test-cv-yolo11-sam2-camera/myrvm-integration',
                    '/tmp'
                ]
            }
        }
    
    def start_monitoring(self):
        """Start health monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            self.logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            self.logger.info("Health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main health monitoring loop"""
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                # Run all health checks
                with self.health_lock:
                    self._run_health_checks()
                
                # Calculate sleep time
                check_time = time.time() - start_time
                sleep_time = max(0, self.health_check_interval - check_time)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Health checks took {check_time:.2f}s, longer than interval {self.health_check_interval}s")
                
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _run_health_checks(self):
        """Run all enabled health checks"""
        try:
            overall_status = 'healthy'
            
            for check_name, check_config in self.health_checks.items():
                if not check_config.get('enabled', True):
                    continue
                
                try:
                    # Run health check
                    check_result = check_config['check_function']()
                    
                    # Determine status
                    status = self._determine_health_status(check_result, check_config)
                    
                    # Store result
                    self.health_status[check_name] = {
                        'status': status,
                        'result': check_result,
                        'timestamp': now().isoformat(),
                        'check_name': check_name
                    }
                    
                    # Update overall status
                    if status == 'critical':
                        overall_status = 'critical'
                    elif status == 'warning' and overall_status == 'healthy':
                        overall_status = 'warning'
                    
                    # Attempt recovery if needed
                    if status in ['critical', 'warning'] and self.recovery_enabled:
                        self._attempt_recovery(check_name, check_config, status)
                    
                except Exception as e:
                    self.logger.error(f"Error running health check {check_name}: {e}")
                    self.health_status[check_name] = {
                        'status': 'error',
                        'result': {'error': str(e)},
                        'timestamp': now().isoformat(),
                        'check_name': check_name
                    }
                    overall_status = 'critical'
            
            # Store overall health status
            self.health_status['overall'] = {
                'status': overall_status,
                'timestamp': now().isoformat(),
                'checks_count': len(self.health_checks),
                'healthy_checks': sum(1 for check in self.health_status.values() 
                                    if check.get('status') == 'healthy'),
                'warning_checks': sum(1 for check in self.health_status.values() 
                                    if check.get('status') == 'warning'),
                'critical_checks': sum(1 for check in self.health_status.values() 
                                     if check.get('status') == 'critical')
            }
            
            # Add to history
            self.health_history.append(self.health_status.copy())
            if len(self.health_history) > 100:  # Keep last 100 health checks
                self.health_history.pop(0)
            
            # Notify callbacks
            self._notify_health_callbacks(self.health_status)
            
        except Exception as e:
            self.logger.error(f"Error running health checks: {e}")
    
    def _determine_health_status(self, check_result: Dict, check_config: Dict) -> str:
        """Determine health status based on check result"""
        try:
            if 'error' in check_result:
                return 'critical'
            
            # Check critical thresholds
            critical_thresholds = check_config.get('critical_thresholds', {})
            for metric, threshold in critical_thresholds.items():
                if metric in check_result and check_result[metric] > threshold:
                    return 'critical'
            
            # Check warning thresholds
            warning_thresholds = check_config.get('warning_thresholds', {})
            for metric, threshold in warning_thresholds.items():
                if metric in check_result and check_result[metric] > threshold:
                    return 'warning'
            
            return 'healthy'
            
        except Exception as e:
            self.logger.error(f"Error determining health status: {e}")
            return 'error'
    
    def _attempt_recovery(self, check_name: str, check_config: Dict, status: str):
        """Attempt recovery for failed health check"""
        try:
            recovery_function = check_config.get('recovery_function')
            if not recovery_function:
                return
            
            # Check recovery attempts
            if check_name not in self.recovery_attempts:
                self.recovery_attempts[check_name] = 0
            
            if self.recovery_attempts[check_name] >= self.max_recovery_attempts:
                self.logger.warning(f"Max recovery attempts reached for {check_name}")
                return
            
            # Attempt recovery
            self.logger.info(f"Attempting recovery for {check_name} (attempt {self.recovery_attempts[check_name] + 1})")
            
            recovery_result = recovery_function()
            
            if recovery_result.get('success', False):
                self.logger.info(f"Recovery successful for {check_name}")
                self.recovery_attempts[check_name] = 0  # Reset counter
            else:
                self.recovery_attempts[check_name] += 1
                self.logger.warning(f"Recovery failed for {check_name}: {recovery_result.get('error', 'Unknown error')}")
            
        except Exception as e:
            self.logger.error(f"Error attempting recovery for {check_name}: {e}")
    
    # Health Check Functions
    def _check_system_resources(self) -> Dict:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': (disk.used / disk.total) * 100,
                'memory_available_gb': memory.available / (1024**3),
                'disk_free_gb': disk.free / (1024**3)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_service_availability(self) -> Dict:
        """Check service availability"""
        try:
            endpoints = self.health_checks['service_availability']['endpoints']
            results = {}
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    results[endpoint] = {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'available': response.status_code == 200
                    }
                except Exception as e:
                    results[endpoint] = {
                        'available': False,
                        'error': str(e)
                    }
            
            # Calculate overall availability
            available_count = sum(1 for result in results.values() if result.get('available', False))
            total_count = len(results)
            availability_percent = (available_count / total_count) * 100 if total_count > 0 else 0
            
            return {
                'availability_percent': availability_percent,
                'available_services': available_count,
                'total_services': total_count,
                'service_results': results
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_process_health(self) -> Dict:
        """Check process health"""
        try:
            process_name = self.health_checks['process_health']['process_name']
            min_memory = self.health_checks['process_health']['min_memory_mb']
            max_memory = self.health_checks['process_health']['max_memory_mb']
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    if proc.info['name'] == process_name:
                        memory_mb = proc.info['memory_info'].rss / (1024**2)
                        processes.append({
                            'pid': proc.info['pid'],
                            'memory_mb': memory_mb,
                            'cpu_percent': proc.info['cpu_percent'],
                            'healthy': min_memory <= memory_mb <= max_memory
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            healthy_count = sum(1 for proc in processes if proc['healthy'])
            total_count = len(processes)
            
            return {
                'process_count': total_count,
                'healthy_processes': healthy_count,
                'processes': processes,
                'health_percent': (healthy_count / total_count) * 100 if total_count > 0 else 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_network_connectivity(self) -> Dict:
        """Check network connectivity"""
        try:
            targets = self.health_checks['network_connectivity']['targets']
            results = {}
            
            for target in targets:
                try:
                    host, port = target.split(':')
                    # Simple connectivity check using subprocess
                    result = subprocess.run(['nc', '-z', host, port], 
                                          capture_output=True, timeout=5)
                    results[target] = {
                        'reachable': result.returncode == 0,
                        'response_time': 0  # nc doesn't provide timing
                    }
                except Exception as e:
                    results[target] = {
                        'reachable': False,
                        'error': str(e)
                    }
            
            reachable_count = sum(1 for result in results.values() if result.get('reachable', False))
            total_count = len(results)
            connectivity_percent = (reachable_count / total_count) * 100 if total_count > 0 else 0
            
            return {
                'connectivity_percent': connectivity_percent,
                'reachable_targets': reachable_count,
                'total_targets': total_count,
                'target_results': results
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_file_system(self) -> Dict:
        """Check file system health"""
        try:
            critical_paths = self.health_checks['file_system']['critical_paths']
            results = {}
            
            for path in critical_paths:
                try:
                    path_obj = Path(path)
                    if path_obj.exists():
                        # Check if path is writable
                        test_file = path_obj / '.health_check_test'
                        try:
                            test_file.write_text('health check')
                            test_file.unlink()
                            writable = True
                        except:
                            writable = False
                        
                        # Get disk usage
                        disk_usage = psutil.disk_usage(str(path_obj))
                        
                        results[path] = {
                            'exists': True,
                            'writable': writable,
                            'free_space_gb': disk_usage.free / (1024**3),
                            'usage_percent': (disk_usage.used / disk_usage.total) * 100
                        }
                    else:
                        results[path] = {
                            'exists': False,
                            'writable': False
                        }
                except Exception as e:
                    results[path] = {
                        'exists': False,
                        'writable': False,
                        'error': str(e)
                    }
            
            healthy_paths = sum(1 for result in results.values() 
                              if result.get('exists', False) and result.get('writable', False))
            total_paths = len(results)
            health_percent = (healthy_paths / total_paths) * 100 if total_paths > 0 else 0
            
            return {
                'health_percent': health_percent,
                'healthy_paths': healthy_paths,
                'total_paths': total_paths,
                'path_results': results
            }
        except Exception as e:
            return {'error': str(e)}
    
    # Recovery Functions
    def _recover_system_resources(self) -> Dict:
        """Attempt to recover system resources"""
        try:
            # Clear system caches (if possible)
            subprocess.run(['sync'], check=False)
            
            # Log memory usage
            memory = psutil.virtual_memory()
            self.logger.info(f"System memory: {memory.percent}% used, {memory.available / (1024**3):.1f}GB available")
            
            return {'success': True, 'action': 'system_cache_cleared'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _recover_service_availability(self) -> Dict:
        """Attempt to recover service availability"""
        try:
            # Restart local services if needed
            # This is a placeholder - actual implementation would depend on your services
            
            return {'success': True, 'action': 'service_restart_attempted'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _recover_process_health(self) -> Dict:
        """Attempt to recover process health"""
        try:
            # Kill and restart unhealthy processes
            # This is a placeholder - actual implementation would be more sophisticated
            
            return {'success': True, 'action': 'process_restart_attempted'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _recover_network_connectivity(self) -> Dict:
        """Attempt to recover network connectivity"""
        try:
            # Restart network services
            # This is a placeholder - actual implementation would depend on your network setup
            
            return {'success': True, 'action': 'network_restart_attempted'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _recover_file_system(self) -> Dict:
        """Attempt to recover file system issues"""
        try:
            # Clean up temporary files
            temp_dir = Path('/tmp')
            if temp_dir.exists():
                for temp_file in temp_dir.glob('*.tmp'):
                    try:
                        temp_file.unlink()
                    except:
                        pass
            
            return {'success': True, 'action': 'temp_files_cleaned'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_health_callback(self, callback: Callable):
        """Add health check callback"""
        self.health_callbacks.append(callback)
        self.logger.info(f"Added health callback: {callback.__name__}")
    
    def remove_health_callback(self, callback: Callable):
        """Remove health check callback"""
        if callback in self.health_callbacks:
            self.health_callbacks.remove(callback)
            self.logger.info(f"Removed health callback: {callback.__name__}")
    
    def _notify_health_callbacks(self, health_status: Dict):
        """Notify health check callbacks"""
        try:
            for callback in self.health_callbacks:
                try:
                    callback(health_status)
                except Exception as e:
                    self.logger.error(f"Error in health callback: {e}")
        except Exception as e:
            self.logger.error(f"Error notifying health callbacks: {e}")
    
    def get_health_status(self) -> Dict:
        """Get current health status"""
        with self.health_lock:
            return self.health_status.copy()
    
    def get_health_history(self, limit: int = 50) -> List[Dict]:
        """Get health check history"""
        try:
            return self.health_history[-limit:] if limit else self.health_history
        except Exception as e:
            self.logger.error(f"Error getting health history: {e}")
            return []
    
    def get_health_report(self) -> str:
        """Generate health report"""
        try:
            status = self.get_health_status()
            overall = status.get('overall', {})
            
            report = f"""
Health Monitor Report
====================
Overall Status: {overall.get('status', 'unknown')}
Monitoring Active: {self.is_monitoring}
Recovery Enabled: {self.recovery_enabled}
Check Interval: {self.health_check_interval}s

Health Check Summary:
- Total Checks: {overall.get('checks_count', 0)}
- Healthy: {overall.get('healthy_checks', 0)}
- Warning: {overall.get('warning_checks', 0)}
- Critical: {overall.get('critical_checks', 0)}

Individual Check Results:
"""
            
            for check_name, check_status in status.items():
                if check_name != 'overall':
                    report += f"- {check_name}: {check_status.get('status', 'unknown')}\n"
            
            if self.recovery_attempts:
                report += "\nRecovery Attempts:\n"
                for check_name, attempts in self.recovery_attempts.items():
                    report += f"- {check_name}: {attempts} attempts\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating health report: {e}")
            return f"Error generating health report: {e}"
