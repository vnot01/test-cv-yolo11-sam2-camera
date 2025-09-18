#!/usr/bin/env python3
"""
Backup Manager for MyRVM Platform Integration
Central backup management system with automated scheduling and monitoring
"""

import os
import json
import logging
import threading
import time
import shutil
import gzip
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import hashlib
import schedule
from cryptography.fernet import Fernet
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now

class BackupManager:
    """Central backup management system"""
    
    def __init__(self, config: Dict):
        """
        Initialize backup manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.backup_enabled = config.get('backup_enabled', True)
        self.backup_interval = config.get('backup_interval', 3600)  # 1 hour
        self.retention_days = config.get('retention_days', 30)
        self.compression_enabled = config.get('compression_enabled', True)
        self.encryption_enabled = config.get('encryption_enabled', True)
        
        # Backup directories
        backup_dir_name = config.get('backup_dir', 'backups')
        if not os.path.isabs(backup_dir_name):
            # Make it relative to the project root
            project_root = Path(__file__).parent.parent
            self.backup_dir = project_root / backup_dir_name
        else:
            self.backup_dir = Path(backup_dir_name)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.database_backup_dir = self.backup_dir / 'database'
        self.database_backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_backup_dir = self.backup_dir / 'config'
        self.config_backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_backup_dir = self.backup_dir / 'logs'
        self.log_backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.app_backup_dir = self.backup_dir / 'application'
        self.app_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup control
        self.is_running = False
        self.backup_thread = None
        self.backup_lock = threading.Lock()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Backup callbacks
        self.backup_callbacks = []
        
        # Initialize encryption
        self.encryption_key = self._get_or_create_encryption_key()
        
        # Backup history
        self.backup_history = []
        self.max_history_size = 1000
        
        # Initialize backup strategies
        self._initialize_backup_strategies()
        
        self.logger.info("Backup manager initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for backup manager"""
        logger = logging.getLogger('BackupManager')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'backup_manager_{now().strftime("%Y%m%d")}.log'
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
    
    def _get_or_create_encryption_key(self) -> Optional[bytes]:
        """Get or create encryption key for backup encryption"""
        if not self.encryption_enabled:
            return None
        
        try:
            key_file = self.backup_dir / 'backup_encryption.key'
            
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key = f.read()
                self.logger.info("Loaded existing backup encryption key")
                return key
            
            # Create new encryption key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set secure permissions
            key_file.chmod(0o600)
            
            self.logger.info("Created new backup encryption key")
            return key
            
        except Exception as e:
            self.logger.error(f"Failed to get/create encryption key: {e}")
            return None
    
    def _initialize_backup_strategies(self):
        """Initialize backup strategies"""
        self.backup_strategies = {
            'database': {
                'enabled': True,
                'interval': 3600,  # 1 hour
                'retention_days': 7,
                'compression': True,
                'encryption': True
            },
            'config': {
                'enabled': True,
                'interval': 1800,  # 30 minutes
                'retention_days': 30,
                'compression': True,
                'encryption': True
            },
            'logs': {
                'enabled': True,
                'interval': 86400,  # 24 hours
                'retention_days': 14,
                'compression': True,
                'encryption': False
            },
            'application': {
                'enabled': True,
                'interval': 86400,  # 24 hours
                'retention_days': 30,
                'compression': True,
                'encryption': True
            }
        }
        
        # Update with config overrides
        config_strategies = self.config.get('backup_strategies', {})
        for strategy_name, strategy_config in config_strategies.items():
            if strategy_name in self.backup_strategies:
                self.backup_strategies[strategy_name].update(strategy_config)
    
    def start_backup_scheduler(self):
        """Start backup scheduler"""
        if not self.backup_enabled:
            self.logger.info("Backup is disabled")
            return
        
        if not self.is_running:
            self.is_running = True
            self.backup_thread = threading.Thread(target=self._backup_scheduler_loop)
            self.backup_thread.daemon = True
            self.backup_thread.start()
            
            # Schedule backup jobs
            self._schedule_backup_jobs()
            
            self.logger.info("Backup scheduler started")
    
    def stop_backup_scheduler(self):
        """Stop backup scheduler"""
        if self.is_running:
            self.is_running = False
            if self.backup_thread:
                self.backup_thread.join(timeout=5)
            
            # Clear scheduled jobs
            schedule.clear()
            
            self.logger.info("Backup scheduler stopped")
    
    def _schedule_backup_jobs(self):
        """Schedule backup jobs"""
        try:
            for strategy_name, strategy_config in self.backup_strategies.items():
                if not strategy_config.get('enabled', True):
                    continue
                
                interval = strategy_config.get('interval', 3600)
                
                if interval >= 86400:  # Daily or longer
                    schedule.every().day.at("02:00").do(self._run_backup, strategy_name)
                elif interval >= 3600:  # Hourly
                    schedule.every().hour.do(self._run_backup, strategy_name)
                elif interval >= 1800:  # 30 minutes
                    schedule.every(30).minutes.do(self._run_backup, strategy_name)
                else:  # Custom interval
                    schedule.every(interval).seconds.do(self._run_backup, strategy_name)
                
                self.logger.info(f"Scheduled {strategy_name} backup (interval: {interval}s)")
            
        except Exception as e:
            self.logger.error(f"Error scheduling backup jobs: {e}")
    
    def _backup_scheduler_loop(self):
        """Main backup scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in backup scheduler loop: {e}")
                time.sleep(60)
    
    def _run_backup(self, strategy_name: str):
        """Run backup for specific strategy"""
        try:
            with self.backup_lock:
                self.logger.info(f"Starting {strategy_name} backup")
                
                start_time = time.time()
                backup_result = self._execute_backup(strategy_name)
                end_time = time.time()
                
                backup_result['duration'] = end_time - start_time
                backup_result['timestamp'] = now().isoformat()
                backup_result['strategy'] = strategy_name
                
                # Store backup result
                self.backup_history.append(backup_result)
                if len(self.backup_history) > self.max_history_size:
                    self.backup_history.pop(0)
                
                # Notify callbacks
                self._notify_backup_callbacks(backup_result)
                
                # Cleanup old backups
                self._cleanup_old_backups(strategy_name)
                
                self.logger.info(f"Completed {strategy_name} backup in {backup_result['duration']:.2f}s")
                
        except Exception as e:
            self.logger.error(f"Error running {strategy_name} backup: {e}")
    
    def _execute_backup(self, strategy_name: str) -> Dict:
        """Execute backup for specific strategy"""
        try:
            strategy_config = self.backup_strategies[strategy_name]
            
            if strategy_name == 'database':
                return self._backup_database(strategy_config)
            elif strategy_name == 'config':
                return self._backup_config(strategy_config)
            elif strategy_name == 'logs':
                return self._backup_logs(strategy_config)
            elif strategy_name == 'application':
                return self._backup_application(strategy_config)
            else:
                raise ValueError(f"Unknown backup strategy: {strategy_name}")
                
        except Exception as e:
            self.logger.error(f"Error executing {strategy_name} backup: {e}")
            return {
                'success': False,
                'error': str(e),
                'strategy': strategy_name
            }
    
    def _backup_database(self, strategy_config: Dict) -> Dict:
        """Backup database"""
        try:
            # This is a placeholder for database backup
            # In a real implementation, you would connect to your database
            # and create a backup dump
            
            backup_file = self.database_backup_dir / f"database_backup_{now().strftime('%Y%m%d_%H%M%S')}.sql"
            
            # Create a dummy database backup file for demonstration
            with open(backup_file, 'w') as f:
                f.write(f"-- Database backup created at {now().isoformat()}\n")
                f.write("-- This is a placeholder for actual database backup\n")
            
            # Apply compression and encryption
            processed_file = self._process_backup_file(backup_file, strategy_config)
            
            return {
                'success': True,
                'backup_file': str(processed_file),
                'original_size': backup_file.stat().st_size,
                'compressed_size': processed_file.stat().st_size if processed_file.exists() else 0,
                'strategy': 'database'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'strategy': 'database'
            }
    
    def _backup_config(self, strategy_config: Dict) -> Dict:
        """Backup configuration files"""
        try:
            config_dir = Path(__file__).parent.parent / 'config'
            backup_file = self.config_backup_dir / f"config_backup_{now().strftime('%Y%m%d_%H%M%S')}.tar"
            
            # Create tar archive of config directory
            with tarfile.open(backup_file, 'w') as tar:
                if config_dir.exists():
                    tar.add(config_dir, arcname='config')
            
            # Apply compression and encryption
            processed_file = self._process_backup_file(backup_file, strategy_config)
            
            return {
                'success': True,
                'backup_file': str(processed_file),
                'original_size': backup_file.stat().st_size,
                'compressed_size': processed_file.stat().st_size if processed_file.exists() else 0,
                'strategy': 'config'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'strategy': 'config'
            }
    
    def _backup_logs(self, strategy_config: Dict) -> Dict:
        """Backup log files"""
        try:
            logs_dir = Path(__file__).parent.parent / 'logs'
            backup_file = self.log_backup_dir / f"logs_backup_{now().strftime('%Y%m%d_%H%M%S')}.tar"
            
            # Create tar archive of logs directory
            with tarfile.open(backup_file, 'w') as tar:
                if logs_dir.exists():
                    tar.add(logs_dir, arcname='logs')
            
            # Apply compression and encryption
            processed_file = self._process_backup_file(backup_file, strategy_config)
            
            return {
                'success': True,
                'backup_file': str(processed_file),
                'original_size': backup_file.stat().st_size,
                'compressed_size': processed_file.stat().st_size if processed_file.exists() else 0,
                'strategy': 'logs'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'strategy': 'logs'
            }
    
    def _backup_application(self, strategy_config: Dict) -> Dict:
        """Backup application files"""
        try:
            app_dir = Path(__file__).parent.parent
            backup_file = self.app_backup_dir / f"app_backup_{now().strftime('%Y%m%d_%H%M%S')}.tar"
            
            # Create tar archive of application directory (excluding backups and logs)
            with tarfile.open(backup_file, 'w') as tar:
                for item in app_dir.iterdir():
                    if item.name not in ['backups', 'logs', '__pycache__', '.git']:
                        tar.add(item, arcname=item.name)
            
            # Apply compression and encryption
            processed_file = self._process_backup_file(backup_file, strategy_config)
            
            return {
                'success': True,
                'backup_file': str(processed_file),
                'original_size': backup_file.stat().st_size,
                'compressed_size': processed_file.stat().st_size if processed_file.exists() else 0,
                'strategy': 'application'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'strategy': 'application'
            }
    
    def _process_backup_file(self, backup_file: Path, strategy_config: Dict) -> Path:
        """Process backup file with compression and encryption"""
        try:
            processed_file = backup_file
            
            # Apply compression
            if strategy_config.get('compression', True):
                compressed_file = backup_file.with_suffix(backup_file.suffix + '.gz')
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove original file
                backup_file.unlink()
                processed_file = compressed_file
            
            # Apply encryption
            if strategy_config.get('encryption', True) and self.encryption_key:
                encrypted_file = processed_file.with_suffix(processed_file.suffix + '.enc')
                
                with open(processed_file, 'rb') as f_in:
                    data = f_in.read()
                
                cipher_suite = Fernet(self.encryption_key)
                encrypted_data = cipher_suite.encrypt(data)
                
                with open(encrypted_file, 'wb') as f_out:
                    f_out.write(encrypted_data)
                
                # Remove unencrypted file
                processed_file.unlink()
                processed_file = encrypted_file
            
            return processed_file
            
        except Exception as e:
            self.logger.error(f"Error processing backup file: {e}")
            return backup_file
    
    def _cleanup_old_backups(self, strategy_name: str):
        """Cleanup old backups based on retention policy"""
        try:
            strategy_config = self.backup_strategies[strategy_name]
            retention_days = strategy_config.get('retention_days', 30)
            
            cutoff_date = now() - timedelta(days=retention_days)
            
            # Get backup directory for strategy
            if strategy_name == 'database':
                backup_dir = self.database_backup_dir
            elif strategy_name == 'config':
                backup_dir = self.config_backup_dir
            elif strategy_name == 'logs':
                backup_dir = self.log_backup_dir
            elif strategy_name == 'application':
                backup_dir = self.app_backup_dir
            else:
                return
            
            # Remove old backup files
            removed_count = 0
            for backup_file in backup_dir.glob('*'):
                if backup_file.is_file():
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        backup_file.unlink()
                        removed_count += 1
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old {strategy_name} backups")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")
    
    def add_backup_callback(self, callback: Callable):
        """Add backup callback"""
        self.backup_callbacks.append(callback)
        self.logger.info(f"Added backup callback: {callback.__name__}")
    
    def remove_backup_callback(self, callback: Callable):
        """Remove backup callback"""
        if callback in self.backup_callbacks:
            self.backup_callbacks.remove(callback)
            self.logger.info(f"Removed backup callback: {callback.__name__}")
    
    def _notify_backup_callbacks(self, backup_result: Dict):
        """Notify backup callbacks"""
        try:
            for callback in self.backup_callbacks:
                try:
                    callback(backup_result)
                except Exception as e:
                    self.logger.error(f"Error in backup callback: {e}")
        except Exception as e:
            self.logger.error(f"Error notifying backup callbacks: {e}")
    
    def run_manual_backup(self, strategy_name: str) -> Dict:
        """Run manual backup for specific strategy"""
        try:
            if strategy_name not in self.backup_strategies:
                raise ValueError(f"Unknown backup strategy: {strategy_name}")
            
            self.logger.info(f"Running manual {strategy_name} backup")
            self._run_backup(strategy_name)
            
            # Get latest backup result
            latest_backup = None
            for backup in reversed(self.backup_history):
                if backup.get('strategy') == strategy_name:
                    latest_backup = backup
                    break
            
            return latest_backup or {'success': False, 'error': 'Backup result not found'}
            
        except Exception as e:
            self.logger.error(f"Error running manual backup: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_backup_status(self) -> Dict:
        """Get backup system status"""
        try:
            return {
                'enabled': self.backup_enabled,
                'running': self.is_running,
                'strategies': len(self.backup_strategies),
                'enabled_strategies': sum(1 for s in self.backup_strategies.values() if s.get('enabled', True)),
                'backup_history_count': len(self.backup_history),
                'last_backup': self.backup_history[-1] if self.backup_history else None,
                'backup_directories': {
                    'database': str(self.database_backup_dir),
                    'config': str(self.config_backup_dir),
                    'logs': str(self.log_backup_dir),
                    'application': str(self.app_backup_dir)
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting backup status: {e}")
            return {}
    
    def get_backup_history(self, limit: int = 100) -> List[Dict]:
        """Get backup history"""
        try:
            return self.backup_history[-limit:] if limit else self.backup_history
        except Exception as e:
            self.logger.error(f"Error getting backup history: {e}")
            return []
    
    def get_backup_report(self) -> str:
        """Generate backup report"""
        try:
            status = self.get_backup_status()
            history = self.get_backup_history(10)
            
            report = f"""
Backup Manager Report
====================
Backup Enabled: {status.get('enabled', False)}
Backup Running: {status.get('running', False)}
Total Strategies: {status.get('strategies', 0)}
Enabled Strategies: {status.get('enabled_strategies', 0)}
Backup History: {status.get('backup_history_count', 0)} entries

Backup Directories:
- Database: {status.get('backup_directories', {}).get('database', 'N/A')}
- Config: {status.get('backup_directories', {}).get('config', 'N/A')}
- Logs: {status.get('backup_directories', {}).get('logs', 'N/A')}
- Application: {status.get('backup_directories', {}).get('application', 'N/A')}

Recent Backups ({len(history)}):
"""
            
            for backup in history:
                success = "✅" if backup.get('success', False) else "❌"
                strategy = backup.get('strategy', 'unknown')
                timestamp = backup.get('timestamp', 'unknown')
                duration = backup.get('duration', 0)
                report += f"- {success} {strategy}: {timestamp} ({duration:.2f}s)\n"
            
            if not history:
                report += "- No backup history available\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating backup report: {e}")
            return f"Error generating backup report: {e}"
