#!/usr/bin/env python3
"""
Production Logging Configuration for MyRVM Platform Integration
Enterprise-grade logging system with rotation and monitoring
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import traceback
import sys

class ProductionLoggingConfig:
    """Production-ready logging configuration system"""
    
    def __init__(self, config: Dict):
        """
        Initialize production logging configuration
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.log_level = config.get('log_level', 'INFO')
        self.environment = config.get('environment', 'development')
        
        # Logging directories
        self.logs_dir = Path(__file__).parent.parent / 'logs'
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.app_logs_dir = self.logs_dir / 'application'
        self.app_logs_dir.mkdir(exist_ok=True)
        
        self.error_logs_dir = self.logs_dir / 'errors'
        self.error_logs_dir.mkdir(exist_ok=True)
        
        self.audit_logs_dir = self.logs_dir / 'audit'
        self.audit_logs_dir.mkdir(exist_ok=True)
        
        self.performance_logs_dir = self.logs_dir / 'performance'
        self.performance_logs_dir.mkdir(exist_ok=True)
        
        # Logging configuration
        self.log_rotation_config = {
            'max_bytes': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'when': 'midnight',
            'interval': 1
        }
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Configure all loggers
        self._configure_loggers()
        
        self.logger.info("Production logging configuration initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup main logger for logging configuration"""
        logger = logging.getLogger('LoggingConfig')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        return logger
    
    def _configure_loggers(self):
        """Configure all application loggers"""
        try:
            # Configure root logger
            self._configure_root_logger()
            
            # Configure application loggers
            self._configure_application_loggers()
            
            # Configure error logger
            self._configure_error_logger()
            
            # Configure audit logger
            self._configure_audit_logger()
            
            # Configure performance logger
            self._configure_performance_logger()
            
            # Configure third-party loggers
            self._configure_third_party_loggers()
            
            self.logger.info("All loggers configured successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to configure loggers: {e}")
            raise
    
    def _configure_root_logger(self):
        """Configure root logger"""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add console handler for development
        if self.environment == 'development':
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
    
    def _configure_application_loggers(self):
        """Configure application-specific loggers"""
        app_loggers = [
            'MyRVMAPIClient',
            'CameraService',
            'MonitoringService',
            'DetectionService',
            'OptimizedDetectionService',
            'MemoryManager',
            'BatchProcessor',
            'PerformanceMonitor',
            'EnvironmentConfig',
            'SecurityManager',
            'EnhancedJetsonMain'
        ]
        
        for logger_name in app_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, self.log_level))
            
            # Add file handler
            log_file = self.app_logs_dir / f'{logger_name.lower()}.log'
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.log_rotation_config['max_bytes'],
                backupCount=self.log_rotation_config['backup_count']
            )
            file_handler.setLevel(getattr(logging, self.log_level))
            
            # Structured formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            
            # Prevent duplicate logs
            logger.propagate = False
    
    def _configure_error_logger(self):
        """Configure error logger"""
        error_logger = logging.getLogger('ErrorLogger')
        error_logger.setLevel(logging.ERROR)
        
        # Error log file
        error_log_file = self.error_logs_dir / 'errors.log'
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.log_rotation_config['max_bytes'],
            backupCount=self.log_rotation_config['backup_count']
        )
        error_handler.setLevel(logging.ERROR)
        
        # Detailed error formatter
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n%(pathname)s:%(lineno)d\n%(exc_info)s'
        )
        error_handler.setFormatter(error_formatter)
        
        error_logger.addHandler(error_handler)
        error_logger.propagate = False
    
    def _configure_audit_logger(self):
        """Configure audit logger"""
        audit_logger = logging.getLogger('AuditLogger')
        audit_logger.setLevel(logging.INFO)
        
        # Audit log file
        audit_log_file = self.audit_logs_dir / 'audit.log'
        audit_handler = logging.handlers.TimedRotatingFileHandler(
            audit_log_file,
            when=self.log_rotation_config['when'],
            interval=self.log_rotation_config['interval'],
            backupCount=self.log_rotation_config['backup_count']
        )
        audit_handler.setLevel(logging.INFO)
        
        # JSON formatter for audit logs
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False
    
    def _configure_performance_logger(self):
        """Configure performance logger"""
        perf_logger = logging.getLogger('PerformanceLogger')
        perf_logger.setLevel(logging.INFO)
        
        # Performance log file
        perf_log_file = self.performance_logs_dir / 'performance.log'
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_file,
            maxBytes=self.log_rotation_config['max_bytes'],
            backupCount=self.log_rotation_config['backup_count']
        )
        perf_handler.setLevel(logging.INFO)
        
        # Performance formatter
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERFORMANCE - %(message)s'
        )
        perf_handler.setFormatter(perf_formatter)
        
        perf_logger.addHandler(perf_handler)
        perf_logger.propagate = False
    
    def _configure_third_party_loggers(self):
        """Configure third-party library loggers"""
        third_party_loggers = {
            'urllib3': 'WARNING',
            'requests': 'WARNING',
            'PIL': 'WARNING',
            'matplotlib': 'WARNING',
            'tensorflow': 'WARNING',
            'torch': 'WARNING',
            'cv2': 'WARNING'
        }
        
        for logger_name, level in third_party_loggers.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, level))
    
    def log_structured(self, logger_name: str, level: str, message: str, **kwargs):
        """Log structured message"""
        try:
            logger = logging.getLogger(logger_name)
            log_level = getattr(logging, level.upper())
            
            # Create structured message
            structured_data = {
                'timestamp': datetime.now().isoformat(),
                'level': level.upper(),
                'message': message,
                'environment': self.environment,
                **kwargs
            }
            
            # Log the message
            logger.log(log_level, json.dumps(structured_data))
            
        except Exception as e:
            self.logger.error(f"Failed to log structured message: {e}")
    
    def log_error(self, error: Exception, context: Dict = None):
        """Log error with context"""
        try:
            error_logger = logging.getLogger('ErrorLogger')
            
            error_data = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'context': context or {},
                'timestamp': datetime.now().isoformat()
            }
            
            error_logger.error(json.dumps(error_data, indent=2))
            
        except Exception as e:
            self.logger.error(f"Failed to log error: {e}")
    
    def log_audit(self, action: str, user_id: str = None, details: Dict = None):
        """Log audit event"""
        try:
            audit_logger = logging.getLogger('AuditLogger')
            
            audit_data = {
                'action': action,
                'user_id': user_id,
                'details': details or {},
                'timestamp': datetime.now().isoformat(),
                'environment': self.environment
            }
            
            audit_logger.info(json.dumps(audit_data))
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
    
    def log_performance(self, operation: str, duration: float, metrics: Dict = None):
        """Log performance metrics"""
        try:
            perf_logger = logging.getLogger('PerformanceLogger')
            
            perf_data = {
                'operation': operation,
                'duration_seconds': duration,
                'metrics': metrics or {},
                'timestamp': datetime.now().isoformat(),
                'environment': self.environment
            }
            
            perf_logger.info(json.dumps(perf_data))
            
        except Exception as e:
            self.logger.error(f"Failed to log performance metrics: {e}")
    
    def get_log_files(self) -> Dict[str, List[str]]:
        """Get list of log files"""
        try:
            log_files = {
                'application': [],
                'errors': [],
                'audit': [],
                'performance': []
            }
            
            for category, log_dir in [
                ('application', self.app_logs_dir),
                ('errors', self.error_logs_dir),
                ('audit', self.audit_logs_dir),
                ('performance', self.performance_logs_dir)
            ]:
                for log_file in log_dir.glob('*.log*'):
                    log_files[category].append(str(log_file))
            
            return log_files
            
        except Exception as e:
            self.logger.error(f"Failed to get log files: {e}")
            return {}
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Cleanup old log files"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            cleaned_files = 0
            
            for log_dir in [self.app_logs_dir, self.error_logs_dir, 
                          self.audit_logs_dir, self.performance_logs_dir]:
                for log_file in log_dir.glob('*.log.*'):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
                        cleaned_files += 1
            
            self.logger.info(f"Cleaned up {cleaned_files} old log files")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
    
    def get_logging_status(self) -> Dict:
        """Get logging status"""
        try:
            log_files = self.get_log_files()
            
            return {
                'environment': self.environment,
                'log_level': self.log_level,
                'logs_directory': str(self.logs_dir),
                'log_files': log_files,
                'rotation_config': self.log_rotation_config,
                'total_log_files': sum(len(files) for files in log_files.values())
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get logging status: {e}")
            return {}
    
    def get_logging_report(self) -> str:
        """Generate logging report"""
        try:
            status = self.get_logging_status()
            
            report = f"""
Production Logging Report
========================
Environment: {status.get('environment', 'N/A')}
Log Level: {status.get('log_level', 'N/A')}
Logs Directory: {status.get('logs_directory', 'N/A')}
Total Log Files: {status.get('total_log_files', 0)}

Log Rotation Configuration:
- Max Bytes: {status.get('rotation_config', {}).get('max_bytes', 0):,} bytes
- Backup Count: {status.get('rotation_config', {}).get('backup_count', 0)}
- Rotation When: {status.get('rotation_config', {}).get('when', 'N/A')}
- Rotation Interval: {status.get('rotation_config', {}).get('interval', 0)}

Log Files by Category:
"""
            
            log_files = status.get('log_files', {})
            for category, files in log_files.items():
                report += f"- {category.title()}: {len(files)} files\n"
                for log_file in files[:3]:  # Show first 3 files
                    report += f"  * {Path(log_file).name}\n"
                if len(files) > 3:
                    report += f"  * ... and {len(files) - 3} more\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate logging report: {e}")
            return f"Error generating logging report: {e}"
