#!/usr/bin/env python3
"""
Backup Monitor for MyRVM Platform Integration
Backup monitoring, alerting, and performance tracking
"""

import os
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import psutil
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now

class BackupMonitor:
    """Backup monitoring and alerting system"""
    
    def __init__(self, config: Dict, backup_manager=None, alerting_engine=None):
        """
        Initialize backup monitor
        
        Args:
            config: Configuration dictionary
            backup_manager: Backup manager instance
            alerting_engine: Alerting engine instance
        """
        self.config = config
        self.backup_manager = backup_manager
        self.alerting_engine = alerting_engine
        self.monitoring_enabled = config.get('backup_monitoring_enabled', True)
        self.monitoring_interval = config.get('backup_monitoring_interval', 300)  # 5 minutes
        
        # Monitoring control
        self.is_monitoring = False
        self.monitoring_thread = None
        self.monitoring_lock = threading.Lock()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Monitoring callbacks
        self.monitoring_callbacks = []
        
        # Monitoring data
        self.monitoring_data = {
            'backup_status': {},
            'storage_usage': {},
            'performance_metrics': {},
            'alert_status': {}
        }
        
        # Initialize monitoring rules
        self._initialize_monitoring_rules()
        
        self.logger.info("Backup monitor initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for backup monitor"""
        logger = logging.getLogger('BackupMonitor')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'backup_monitor_{now().strftime("%Y%m%d")}.log'
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
    
    def _initialize_monitoring_rules(self):
        """Initialize backup monitoring rules"""
        self.monitoring_rules = {
            'backup_failure': {
                'enabled': True,
                'severity': 'critical',
                'message': 'Backup operation failed',
                'threshold': 1,  # Any failure
                'cooldown': 300  # 5 minutes
            },
            'backup_delay': {
                'enabled': True,
                'severity': 'warning',
                'message': 'Backup operation delayed',
                'threshold': 3600,  # 1 hour delay
                'cooldown': 1800  # 30 minutes
            },
            'storage_usage_high': {
                'enabled': True,
                'severity': 'warning',
                'message': 'Backup storage usage is high',
                'threshold': 80,  # 80% usage
                'cooldown': 3600  # 1 hour
            },
            'storage_usage_critical': {
                'enabled': True,
                'severity': 'critical',
                'message': 'Backup storage usage is critical',
                'threshold': 95,  # 95% usage
                'cooldown': 1800  # 30 minutes
            },
            'backup_size_anomaly': {
                'enabled': True,
                'severity': 'warning',
                'message': 'Backup size anomaly detected',
                'threshold': 2.0,  # 2x normal size
                'cooldown': 3600  # 1 hour
            },
            'recovery_time_exceeded': {
                'enabled': True,
                'severity': 'critical',
                'message': 'Recovery time exceeded RTO',
                'threshold': 1,  # Any RTO exceed
                'cooldown': 1800  # 30 minutes
            }
        }
        
        # Update with config overrides
        config_rules = self.config.get('backup_monitoring_rules', {})
        for rule_name, rule_config in config_rules.items():
            if rule_name in self.monitoring_rules:
                self.monitoring_rules[rule_name].update(rule_config)
    
    def start_monitoring(self):
        """Start backup monitoring"""
        if not self.monitoring_enabled:
            self.logger.info("Backup monitoring is disabled")
            return
        
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            self.logger.info("Backup monitoring started")
    
    def stop_monitoring(self):
        """Stop backup monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            self.logger.info("Backup monitoring stopped")
    
    def _monitoring_loop(self):
        """Main backup monitoring loop"""
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                # Collect monitoring data
                with self.monitoring_lock:
                    self._collect_backup_status()
                    self._collect_storage_usage()
                    self._collect_performance_metrics()
                    self._check_monitoring_rules()
                
                # Calculate sleep time
                monitoring_time = time.time() - start_time
                sleep_time = max(0, self.monitoring_interval - monitoring_time)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Backup monitoring took {monitoring_time:.2f}s, longer than interval {self.monitoring_interval}s")
                
            except Exception as e:
                self.logger.error(f"Error in backup monitoring loop: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _collect_backup_status(self):
        """Collect backup status information"""
        try:
            if not self.backup_manager:
                self.monitoring_data['backup_status'] = {
                    'error': 'Backup manager not available'
                }
                return
            
            # Get backup status
            backup_status = self.backup_manager.get_backup_status()
            backup_history = self.backup_manager.get_backup_history(10)
            
            # Analyze backup status
            recent_backups = []
            failed_backups = []
            successful_backups = []
            
            for backup in backup_history:
                if backup.get('success', False):
                    successful_backups.append(backup)
                else:
                    failed_backups.append(backup)
                recent_backups.append(backup)
            
            # Calculate metrics
            total_backups = len(recent_backups)
            success_rate = (len(successful_backups) / total_backups * 100) if total_backups > 0 else 0
            
            # Check for recent failures
            recent_failures = 0
            for backup in failed_backups:
                backup_time = datetime.fromisoformat(backup.get('timestamp', ''))
                if now() - backup_time < timedelta(hours=24):
                    recent_failures += 1
            
            self.monitoring_data['backup_status'] = {
                'enabled': backup_status.get('enabled', False),
                'running': backup_status.get('running', False),
                'total_backups': total_backups,
                'successful_backups': len(successful_backups),
                'failed_backups': len(failed_backups),
                'success_rate': success_rate,
                'recent_failures': recent_failures,
                'last_backup': recent_backups[0] if recent_backups else None,
                'strategies_enabled': backup_status.get('enabled_strategies', 0),
                'total_strategies': backup_status.get('strategies', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting backup status: {e}")
            self.monitoring_data['backup_status'] = {
                'error': str(e)
            }
    
    def _collect_storage_usage(self):
        """Collect backup storage usage information"""
        try:
            if not self.backup_manager:
                self.monitoring_data['storage_usage'] = {
                    'error': 'Backup manager not available'
                }
                return
            
            # Get backup directories
            backup_status = self.backup_manager.get_backup_status()
            backup_dirs = backup_status.get('backup_directories', {})
            storage_info = {}
            total_size = 0
            total_available = 0
            
            for dir_name, dir_path in backup_dirs.items():
                try:
                    dir_path_obj = Path(dir_path)
                    if dir_path_obj.exists():
                        # Calculate directory size
                        dir_size = sum(f.stat().st_size for f in dir_path_obj.rglob('*') if f.is_file())
                        
                        # Get disk usage
                        disk_usage = psutil.disk_usage(str(dir_path_obj))
                        
                        storage_info[dir_name] = {
                            'size_bytes': dir_size,
                            'size_mb': dir_size / (1024 * 1024),
                            'size_gb': dir_size / (1024 * 1024 * 1024),
                            'disk_total': disk_usage.total,
                            'disk_used': disk_usage.used,
                            'disk_free': disk_usage.free,
                            'disk_percent': (disk_usage.used / disk_usage.total) * 100
                        }
                        
                        total_size += dir_size
                        total_available += disk_usage.free
                    else:
                        storage_info[dir_name] = {
                            'error': 'Directory does not exist'
                        }
                except Exception as e:
                    storage_info[dir_name] = {
                        'error': str(e)
                    }
            
            # Calculate overall storage usage
            overall_disk_usage = psutil.disk_usage('/')
            
            self.monitoring_data['storage_usage'] = {
                'directories': storage_info,
                'total_backup_size': total_size,
                'total_backup_size_gb': total_size / (1024 * 1024 * 1024),
                'total_available_space': total_available,
                'total_available_space_gb': total_available / (1024 * 1024 * 1024),
                'overall_disk_usage_percent': (overall_disk_usage.used / overall_disk_usage.total) * 100,
                'overall_disk_free_gb': overall_disk_usage.free / (1024 * 1024 * 1024)
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting storage usage: {e}")
            self.monitoring_data['storage_usage'] = {
                'error': str(e)
            }
    
    def _collect_performance_metrics(self):
        """Collect backup performance metrics"""
        try:
            if not self.backup_manager:
                self.monitoring_data['performance_metrics'] = {
                    'error': 'Backup manager not available'
                }
                return
            
            # Get recent backup history
            backup_history = self.backup_manager.get_backup_history(50)
            
            # Calculate performance metrics
            durations = []
            sizes = []
            success_count = 0
            failure_count = 0
            
            for backup in backup_history:
                if backup.get('success', False):
                    success_count += 1
                    duration = backup.get('duration', 0)
                    if duration > 0:
                        durations.append(duration)
                    
                    original_size = backup.get('original_size', 0)
                    compressed_size = backup.get('compressed_size', 0)
                    if original_size > 0:
                        sizes.append(original_size)
                else:
                    failure_count += 1
            
            # Calculate statistics
            avg_duration = sum(durations) / len(durations) if durations else 0
            max_duration = max(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            
            avg_size = sum(sizes) / len(sizes) if sizes else 0
            max_size = max(sizes) if sizes else 0
            min_size = min(sizes) if sizes else 0
            
            # Calculate compression ratio
            compression_ratios = []
            for backup in backup_history:
                if backup.get('success', False):
                    original_size = backup.get('original_size', 0)
                    compressed_size = backup.get('compressed_size', 0)
                    if original_size > 0 and compressed_size > 0:
                        ratio = compressed_size / original_size
                        compression_ratios.append(ratio)
            
            avg_compression_ratio = sum(compression_ratios) / len(compression_ratios) if compression_ratios else 0
            
            self.monitoring_data['performance_metrics'] = {
                'total_backups_analyzed': len(backup_history),
                'success_count': success_count,
                'failure_count': failure_count,
                'success_rate': (success_count / len(backup_history) * 100) if backup_history else 0,
                'duration_stats': {
                    'average': avg_duration,
                    'maximum': max_duration,
                    'minimum': min_duration,
                    'count': len(durations)
                },
                'size_stats': {
                    'average_mb': avg_size / (1024 * 1024),
                    'maximum_mb': max_size / (1024 * 1024),
                    'minimum_mb': min_size / (1024 * 1024),
                    'count': len(sizes)
                },
                'compression_ratio': avg_compression_ratio,
                'compression_efficiency': (1 - avg_compression_ratio) * 100 if avg_compression_ratio > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting performance metrics: {e}")
            self.monitoring_data['performance_metrics'] = {
                'error': str(e)
            }
    
    def _check_monitoring_rules(self):
        """Check backup monitoring rules and trigger alerts"""
        try:
            if not self.alerting_engine:
                return
            
            # Check backup failure rule
            if self.monitoring_rules['backup_failure']['enabled']:
                recent_failures = self.monitoring_data['backup_status'].get('recent_failures', 0)
                if recent_failures > 0:
                    self._trigger_backup_alert('backup_failure', {
                        'recent_failures': recent_failures,
                        'threshold': self.monitoring_rules['backup_failure']['threshold']
                    })
            
            # Check storage usage rules
            if self.monitoring_rules['storage_usage_high']['enabled']:
                disk_usage = self.monitoring_data['storage_usage'].get('overall_disk_usage_percent', 0)
                if disk_usage > self.monitoring_rules['storage_usage_high']['threshold']:
                    self._trigger_backup_alert('storage_usage_high', {
                        'disk_usage_percent': disk_usage,
                        'threshold': self.monitoring_rules['storage_usage_high']['threshold']
                    })
            
            if self.monitoring_rules['storage_usage_critical']['enabled']:
                disk_usage = self.monitoring_data['storage_usage'].get('overall_disk_usage_percent', 0)
                if disk_usage > self.monitoring_rules['storage_usage_critical']['threshold']:
                    self._trigger_backup_alert('storage_usage_critical', {
                        'disk_usage_percent': disk_usage,
                        'threshold': self.monitoring_rules['storage_usage_critical']['threshold']
                    })
            
            # Check backup size anomaly rule
            if self.monitoring_rules['backup_size_anomaly']['enabled']:
                avg_size = self.monitoring_data['performance_metrics'].get('size_stats', {}).get('average_mb', 0)
                max_size = self.monitoring_data['performance_metrics'].get('size_stats', {}).get('maximum_mb', 0)
                if avg_size > 0 and max_size > avg_size * self.monitoring_rules['backup_size_anomaly']['threshold']:
                    self._trigger_backup_alert('backup_size_anomaly', {
                        'max_size_mb': max_size,
                        'avg_size_mb': avg_size,
                        'ratio': max_size / avg_size,
                        'threshold': self.monitoring_rules['backup_size_anomaly']['threshold']
                    })
            
        except Exception as e:
            self.logger.error(f"Error checking monitoring rules: {e}")
    
    def _trigger_backup_alert(self, rule_name: str, alert_data: Dict):
        """Trigger backup alert"""
        try:
            if not self.alerting_engine:
                return
            
            rule = self.monitoring_rules[rule_name]
            
            # Create alert data
            alert_metrics = {
                'backup_status': self.monitoring_data['backup_status'],
                'storage_usage': self.monitoring_data['storage_usage'],
                'performance_metrics': self.monitoring_data['performance_metrics'],
                'alert_data': alert_data
            }
            
            # Process alert through alerting engine
            self.alerting_engine.process_metrics(alert_metrics)
            
            self.logger.warning(f"Backup alert triggered: {rule_name} - {rule['message']}")
            
        except Exception as e:
            self.logger.error(f"Error triggering backup alert: {e}")
    
    def add_monitoring_callback(self, callback: Callable):
        """Add monitoring callback"""
        self.monitoring_callbacks.append(callback)
        self.logger.info(f"Added monitoring callback: {callback.__name__}")
    
    def remove_monitoring_callback(self, callback: Callable):
        """Remove monitoring callback"""
        if callback in self.monitoring_callbacks:
            self.monitoring_callbacks.remove(callback)
            self.logger.info(f"Removed monitoring callback: {callback.__name__}")
    
    def get_monitoring_data(self) -> Dict:
        """Get current monitoring data"""
        with self.monitoring_lock:
            return self.monitoring_data.copy()
    
    def get_monitoring_status(self) -> Dict:
        """Get backup monitoring status"""
        try:
            return {
                'enabled': self.monitoring_enabled,
                'monitoring': self.is_monitoring,
                'interval': self.monitoring_interval,
                'rules_count': len(self.monitoring_rules),
                'enabled_rules': sum(1 for r in self.monitoring_rules.values() if r.get('enabled', True)),
                'callbacks_count': len(self.monitoring_callbacks),
                'last_update': now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting monitoring status: {e}")
            return {}
    
    def get_monitoring_report(self) -> str:
        """Generate backup monitoring report"""
        try:
            status = self.get_monitoring_status()
            monitoring_data = self.get_monitoring_data()
            
            report = f"""
Backup Monitor Report
====================
Monitoring Enabled: {status.get('enabled', False)}
Monitoring Active: {status.get('monitoring', False)}
Monitoring Interval: {status.get('interval', 0)}s
Total Rules: {status.get('rules_count', 0)}
Enabled Rules: {status.get('enabled_rules', 0)}
Callbacks: {status.get('callbacks_count', 0)}

Backup Status:
- Enabled: {monitoring_data.get('backup_status', {}).get('enabled', 'N/A')}
- Running: {monitoring_data.get('backup_status', {}).get('running', 'N/A')}
- Success Rate: {monitoring_data.get('backup_status', {}).get('success_rate', 'N/A')}%
- Recent Failures: {monitoring_data.get('backup_status', {}).get('recent_failures', 'N/A')}

Storage Usage:
- Total Backup Size: {monitoring_data.get('storage_usage', {}).get('total_backup_size_gb', 'N/A')}GB
- Overall Disk Usage: {monitoring_data.get('storage_usage', {}).get('overall_disk_usage_percent', 'N/A')}%
- Available Space: {monitoring_data.get('storage_usage', {}).get('overall_disk_free_gb', 'N/A')}GB

Performance Metrics:
- Success Rate: {monitoring_data.get('performance_metrics', {}).get('success_rate', 'N/A')}%
- Average Duration: {monitoring_data.get('performance_metrics', {}).get('duration_stats', {}).get('average', 'N/A')}s
- Compression Efficiency: {monitoring_data.get('performance_metrics', {}).get('compression_efficiency', 'N/A')}%

Monitoring Rules:
"""
            
            for rule_name, rule_config in self.monitoring_rules.items():
                enabled = "✅" if rule_config.get('enabled', True) else "❌"
                severity = rule_config.get('severity', 'unknown')
                threshold = rule_config.get('threshold', 'N/A')
                report += f"- {enabled} {rule_name}: {severity} (threshold: {threshold})\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating monitoring report: {e}")
            return f"Error generating monitoring report: {e}"
