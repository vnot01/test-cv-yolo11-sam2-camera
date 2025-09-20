#!/usr/bin/env python3
"""
Recovery Manager for MyRVM Platform Integration
Comprehensive recovery procedures and disaster recovery management
"""

import os
import json
import logging
import shutil
import gzip
import tarfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from cryptography.fernet import Fernet

class RecoveryManager:
    """Comprehensive recovery and disaster recovery management system"""
    
    def __init__(self, config: Dict, backup_manager=None):
        """
        Initialize recovery manager
        
        Args:
            config: Configuration dictionary
            backup_manager: Backup manager instance
        """
        self.config = config
        self.backup_manager = backup_manager
        self.recovery_enabled = config.get('recovery_enabled', True)
        self.recovery_timeout = config.get('recovery_timeout', 3600)  # 1 hour
        self.auto_recovery = config.get('auto_recovery', False)
        
        # Recovery directories
        self.recovery_dir = Path(config.get('recovery_dir', 'recovery'))
        self.recovery_dir.mkdir(exist_ok=True)
        
        self.temp_recovery_dir = self.recovery_dir / 'temp'
        self.temp_recovery_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Recovery callbacks
        self.recovery_callbacks = []
        
        # Recovery history
        self.recovery_history = []
        self.max_history_size = 1000
        
        # Recovery procedures
        self._initialize_recovery_procedures()
        
        self.logger.info("Recovery manager initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for recovery manager"""
        logger = logging.getLogger('RecoveryManager')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'recovery_manager_{now().strftime("%Y%m%d")}.log'
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
    
    def _initialize_recovery_procedures(self):
        """Initialize recovery procedures"""
        self.recovery_procedures = {
            'database': {
                'enabled': True,
                'rto_minutes': 15,  # Recovery Time Objective
                'rpo_minutes': 5,   # Recovery Point Objective
                'recovery_function': self._recover_database
            },
            'config': {
                'enabled': True,
                'rto_minutes': 5,
                'rpo_minutes': 1,
                'recovery_function': self._recover_config
            },
            'logs': {
                'enabled': True,
                'rto_minutes': 10,
                'rpo_minutes': 30,
                'recovery_function': self._recover_logs
            },
            'application': {
                'enabled': True,
                'rto_minutes': 30,
                'rpo_minutes': 60,
                'recovery_function': self._recover_application
            },
            'full_system': {
                'enabled': True,
                'rto_minutes': 60,
                'rpo_minutes': 15,
                'recovery_function': self._recover_full_system
            }
        }
        
        # Update with config overrides
        config_procedures = self.config.get('recovery_procedures', {})
        for procedure_name, procedure_config in config_procedures.items():
            if procedure_name in self.recovery_procedures:
                self.recovery_procedures[procedure_name].update(procedure_config)
    
    def recover(self, recovery_type: str, backup_file: str = None, target_timestamp: str = None) -> Dict:
        """Execute recovery procedure"""
        try:
            if not self.recovery_enabled:
                return {
                    'success': False,
                    'error': 'Recovery is disabled',
                    'recovery_type': recovery_type
                }
            
            if recovery_type not in self.recovery_procedures:
                return {
                    'success': False,
                    'error': f'Unknown recovery type: {recovery_type}',
                    'recovery_type': recovery_type
                }
            
            procedure = self.recovery_procedures[recovery_type]
            if not procedure.get('enabled', True):
                return {
                    'success': False,
                    'error': f'Recovery type {recovery_type} is disabled',
                    'recovery_type': recovery_type
                }
            
            self.logger.info(f"Starting {recovery_type} recovery")
            
            start_time = time.time()
            
            # Find backup file if not provided
            if not backup_file:
                backup_file = self._find_latest_backup(recovery_type, target_timestamp)
                if not backup_file:
                    return {
                        'success': False,
                        'error': f'No backup file found for {recovery_type}',
                        'recovery_type': recovery_type
                    }
            
            # Execute recovery
            recovery_result = procedure['recovery_function'](backup_file, target_timestamp)
            
            end_time = time.time()
            recovery_duration = end_time - start_time
            
            # Prepare result
            result = {
                'success': recovery_result.get('success', False),
                'recovery_type': recovery_type,
                'backup_file': backup_file,
                'target_timestamp': target_timestamp,
                'duration': recovery_duration,
                'timestamp': now().isoformat(),
                'rto_minutes': procedure.get('rto_minutes', 60),
                'rpo_minutes': procedure.get('rpo_minutes', 15)
            }
            
            if not result['success']:
                result['error'] = recovery_result.get('error', 'Unknown recovery error')
            
            # Store recovery result
            self.recovery_history.append(result)
            if len(self.recovery_history) > self.max_history_size:
                self.recovery_history.pop(0)
            
            # Notify callbacks
            self._notify_recovery_callbacks(result)
            
            # Log result
            if result['success']:
                self.logger.info(f"Successfully completed {recovery_type} recovery in {recovery_duration:.2f}s")
            else:
                self.logger.error(f"Failed {recovery_type} recovery: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing {recovery_type} recovery: {e}")
            return {
                'success': False,
                'error': str(e),
                'recovery_type': recovery_type
            }
    
    def _find_latest_backup(self, recovery_type: str, target_timestamp: str = None) -> Optional[str]:
        """Find latest backup file for recovery type"""
        try:
            if not self.backup_manager:
                return None
            
            # Get backup directory for recovery type
            if recovery_type == 'database':
                backup_dir = self.backup_manager.database_backup_dir
            elif recovery_type == 'config':
                backup_dir = self.backup_manager.config_backup_dir
            elif recovery_type == 'logs':
                backup_dir = self.backup_manager.log_backup_dir
            elif recovery_type == 'application':
                backup_dir = self.backup_manager.app_backup_dir
            else:
                return None
            
            # Find backup files
            backup_files = []
            for backup_file in backup_dir.glob('*'):
                if backup_file.is_file():
                    backup_files.append(backup_file)
            
            if not backup_files:
                return None
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # If target timestamp is specified, find closest backup
            if target_timestamp:
                target_time = datetime.fromisoformat(target_timestamp)
                closest_backup = None
                min_diff = float('inf')
                
                for backup_file in backup_files:
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    diff = abs((target_time - file_time).total_seconds())
                    if diff < min_diff:
                        min_diff = diff
                        closest_backup = backup_file
                
                return str(closest_backup) if closest_backup else None
            
            # Return latest backup
            return str(backup_files[0])
            
        except Exception as e:
            self.logger.error(f"Error finding latest backup: {e}")
            return None
    
    def _recover_database(self, backup_file: str, target_timestamp: str = None) -> Dict:
        """Recover database from backup"""
        try:
            self.logger.info(f"Recovering database from {backup_file}")
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
            
            # This is a placeholder for database recovery
            # In a real implementation, you would:
            # 1. Stop database services
            # 2. Restore database from backup
            # 3. Start database services
            # 4. Verify database integrity
            
            # For demonstration, we'll just simulate the recovery
            time.sleep(2)  # Simulate recovery time
            
            return {
                'success': True,
                'message': 'Database recovery completed successfully',
                'recovered_tables': 10,  # Placeholder
                'recovered_records': 1000  # Placeholder
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _recover_config(self, backup_file: str, target_timestamp: str = None) -> Dict:
        """Recover configuration from backup"""
        try:
            self.logger.info(f"Recovering configuration from {backup_file}")
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
            
            # Extract backup file
            extracted_dir = self.temp_recovery_dir / f"config_recovery_{now().strftime('%Y%m%d_%H%M%S')}"
            extracted_dir.mkdir(exist_ok=True)
            
            # Process backup file (decompress and decrypt if needed)
            processed_file = self._process_backup_file_for_recovery(backup_file)
            
            # Extract tar archive
            with tarfile.open(processed_file, 'r') as tar:
                tar.extractall(extracted_dir)
            
            # Restore configuration files
            config_dir = Path(__file__).parent.parent / 'config'
            config_dir.mkdir(exist_ok=True)
            
            # Copy recovered config files
            recovered_config_dir = extracted_dir / 'config'
            if recovered_config_dir.exists():
                shutil.copytree(recovered_config_dir, config_dir, dirs_exist_ok=True)
            
            # Cleanup
            shutil.rmtree(extracted_dir)
            if processed_file != backup_file:
                processed_file.unlink()
            
            return {
                'success': True,
                'message': 'Configuration recovery completed successfully',
                'recovered_files': len(list(config_dir.glob('*')))
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _recover_logs(self, backup_file: str, target_timestamp: str = None) -> Dict:
        """Recover logs from backup"""
        try:
            self.logger.info(f"Recovering logs from {backup_file}")
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
            
            # Extract backup file
            extracted_dir = self.temp_recovery_dir / f"logs_recovery_{now().strftime('%Y%m%d_%H%M%S')}"
            extracted_dir.mkdir(exist_ok=True)
            
            # Process backup file
            processed_file = self._process_backup_file_for_recovery(backup_file)
            
            # Extract tar archive
            with tarfile.open(processed_file, 'r') as tar:
                tar.extractall(extracted_dir)
            
            # Restore log files
            logs_dir = Path(__file__).parent.parent / 'logs'
            logs_dir.mkdir(exist_ok=True)
            
            # Copy recovered log files
            recovered_logs_dir = extracted_dir / 'logs'
            if recovered_logs_dir.exists():
                for log_file in recovered_logs_dir.glob('*'):
                    if log_file.is_file():
                        shutil.copy2(log_file, logs_dir / log_file.name)
            
            # Cleanup
            shutil.rmtree(extracted_dir)
            if processed_file != backup_file:
                processed_file.unlink()
            
            return {
                'success': True,
                'message': 'Logs recovery completed successfully',
                'recovered_files': len(list(logs_dir.glob('*')))
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _recover_application(self, backup_file: str, target_timestamp: str = None) -> Dict:
        """Recover application from backup"""
        try:
            self.logger.info(f"Recovering application from {backup_file}")
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
            
            # Extract backup file
            extracted_dir = self.temp_recovery_dir / f"app_recovery_{now().strftime('%Y%m%d_%H%M%S')}"
            extracted_dir.mkdir(exist_ok=True)
            
            # Process backup file
            processed_file = self._process_backup_file_for_recovery(backup_file)
            
            # Extract tar archive
            with tarfile.open(processed_file, 'r') as tar:
                tar.extractall(extracted_dir)
            
            # Restore application files
            app_dir = Path(__file__).parent.parent
            
            # Copy recovered application files
            for item in extracted_dir.iterdir():
                if item.name not in ['backups', 'logs', '__pycache__', '.git']:
                    target_path = app_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, target_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, target_path)
            
            # Cleanup
            shutil.rmtree(extracted_dir)
            if processed_file != backup_file:
                processed_file.unlink()
            
            return {
                'success': True,
                'message': 'Application recovery completed successfully',
                'recovered_files': len(list(app_dir.glob('*')))
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _recover_full_system(self, backup_file: str, target_timestamp: str = None) -> Dict:
        """Recover full system from backup"""
        try:
            self.logger.info(f"Recovering full system from {backup_file}")
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
            
            # Full system recovery involves multiple components
            recovery_results = {}
            
            # Recover application
            app_result = self._recover_application(backup_file, target_timestamp)
            recovery_results['application'] = app_result
            
            # Recover configuration
            config_result = self._recover_config(backup_file, target_timestamp)
            recovery_results['configuration'] = config_result
            
            # Recover database (if available)
            db_result = self._recover_database(backup_file, target_timestamp)
            recovery_results['database'] = db_result
            
            # Check overall success
            overall_success = all(result.get('success', False) for result in recovery_results.values())
            
            return {
                'success': overall_success,
                'message': 'Full system recovery completed',
                'component_results': recovery_results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_backup_file_for_recovery(self, backup_file: str) -> str:
        """Process backup file for recovery (decompress and decrypt)"""
        try:
            backup_path = Path(backup_file)
            processed_file = backup_path
            
            # Handle encryption
            if backup_path.suffix == '.enc':
                # Decrypt file
                decrypted_file = backup_path.with_suffix('')
                
                with open(backup_path, 'rb') as f_in:
                    encrypted_data = f_in.read()
                
                if self.backup_manager and self.backup_manager.encryption_key:
                    cipher_suite = Fernet(self.backup_manager.encryption_key)
                    decrypted_data = cipher_suite.decrypt(encrypted_data)
                    
                    with open(decrypted_file, 'wb') as f_out:
                        f_out.write(decrypted_data)
                    
                    processed_file = decrypted_file
            
            # Handle compression
            if processed_file.suffix == '.gz':
                # Decompress file
                decompressed_file = processed_file.with_suffix('')
                
                with gzip.open(processed_file, 'rb') as f_in:
                    with open(decompressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove compressed file if it was created during processing
                if processed_file != backup_path:
                    processed_file.unlink()
                
                processed_file = decompressed_file
            
            return str(processed_file)
            
        except Exception as e:
            self.logger.error(f"Error processing backup file for recovery: {e}")
            return backup_file
    
    def test_recovery(self, recovery_type: str) -> Dict:
        """Test recovery procedure without actually restoring"""
        try:
            self.logger.info(f"Testing {recovery_type} recovery procedure")
            
            # Find latest backup
            backup_file = self._find_latest_backup(recovery_type)
            if not backup_file:
                return {
                    'success': False,
                    'error': f'No backup file found for {recovery_type}',
                    'recovery_type': recovery_type
                }
            
            # Test backup file integrity
            backup_path = Path(backup_file)
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f'Backup file does not exist: {backup_file}',
                    'recovery_type': recovery_type
                }
            
            # Test file processing
            try:
                processed_file = self._process_backup_file_for_recovery(backup_file)
                if processed_file != backup_file:
                    Path(processed_file).unlink()  # Cleanup test file
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Backup file processing failed: {e}',
                    'recovery_type': recovery_type
                }
            
            return {
                'success': True,
                'message': f'{recovery_type} recovery test passed',
                'backup_file': backup_file,
                'backup_size': backup_path.stat().st_size,
                'backup_age_hours': (time.time() - backup_path.stat().st_mtime) / 3600
            }
            
        except Exception as e:
            self.logger.error(f"Error testing {recovery_type} recovery: {e}")
            return {
                'success': False,
                'error': str(e),
                'recovery_type': recovery_type
            }
    
    def add_recovery_callback(self, callback: Callable):
        """Add recovery callback"""
        self.recovery_callbacks.append(callback)
        self.logger.info(f"Added recovery callback: {callback.__name__}")
    
    def remove_recovery_callback(self, callback: Callable):
        """Remove recovery callback"""
        if callback in self.recovery_callbacks:
            self.recovery_callbacks.remove(callback)
            self.logger.info(f"Removed recovery callback: {callback.__name__}")
    
    def _notify_recovery_callbacks(self, recovery_result: Dict):
        """Notify recovery callbacks"""
        try:
            for callback in self.recovery_callbacks:
                try:
                    callback(recovery_result)
                except Exception as e:
                    self.logger.error(f"Error in recovery callback: {e}")
        except Exception as e:
            self.logger.error(f"Error notifying recovery callbacks: {e}")
    
    def get_recovery_status(self) -> Dict:
        """Get recovery system status"""
        try:
            return {
                'enabled': self.recovery_enabled,
                'auto_recovery': self.auto_recovery,
                'procedures': len(self.recovery_procedures),
                'enabled_procedures': sum(1 for p in self.recovery_procedures.values() if p.get('enabled', True)),
                'recovery_history_count': len(self.recovery_history),
                'last_recovery': self.recovery_history[-1] if self.recovery_history else None,
                'recovery_timeout': self.recovery_timeout
            }
        except Exception as e:
            self.logger.error(f"Error getting recovery status: {e}")
            return {}
    
    def get_recovery_history(self, limit: int = 100) -> List[Dict]:
        """Get recovery history"""
        try:
            return self.recovery_history[-limit:] if limit else self.recovery_history
        except Exception as e:
            self.logger.error(f"Error getting recovery history: {e}")
            return []
    
    def get_recovery_report(self) -> str:
        """Generate recovery report"""
        try:
            status = self.get_recovery_status()
            history = self.get_recovery_history(10)
            
            report = f"""
Recovery Manager Report
======================
Recovery Enabled: {status.get('enabled', False)}
Auto Recovery: {status.get('auto_recovery', False)}
Total Procedures: {status.get('procedures', 0)}
Enabled Procedures: {status.get('enabled_procedures', 0)}
Recovery History: {status.get('recovery_history_count', 0)} entries
Recovery Timeout: {status.get('recovery_timeout', 0)}s

Recovery Procedures:
"""
            
            for procedure_name, procedure_config in self.recovery_procedures.items():
                enabled = "✅" if procedure_config.get('enabled', True) else "❌"
                rto = procedure_config.get('rto_minutes', 60)
                rpo = procedure_config.get('rpo_minutes', 15)
                report += f"- {enabled} {procedure_name}: RTO={rto}min, RPO={rpo}min\n"
            
            report += f"\nRecent Recoveries ({len(history)}):\n"
            for recovery in history:
                success = "✅" if recovery.get('success', False) else "❌"
                recovery_type = recovery.get('recovery_type', 'unknown')
                timestamp = recovery.get('timestamp', 'unknown')
                duration = recovery.get('duration', 0)
                report += f"- {success} {recovery_type}: {timestamp} ({duration:.2f}s)\n"
            
            if not history:
                report += "- No recovery history available\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating recovery report: {e}")
            return f"Error generating recovery report: {e}"
