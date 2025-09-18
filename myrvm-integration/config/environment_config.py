#!/usr/bin/env python3
"""
Environment Configuration Manager for MyRVM Platform Integration
Production-ready environment-based configuration management
"""

import os
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from cryptography.fernet import Fernet
import hashlib

class EnvironmentConfig:
    """Environment-based configuration management system"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize environment configuration manager
        
        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.environment = self._detect_environment()
        self.config_cache = {}
        self.config_watchers = {}
        self.is_watching = False
        self.watch_thread = None
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Configuration schema
        self.config_schema = self._get_config_schema()
        
        # Load base configuration
        self.base_config = self._load_base_config()
        
        # Load environment-specific configuration
        self.env_config = self._load_environment_config()
        
        # Merge configurations
        self.config = self._merge_configurations()
        
        # Validate configuration
        self._validate_configuration()
        
        self.logger.info(f"Environment configuration initialized for: {self.environment}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for environment configuration"""
        logger = logging.getLogger('EnvironmentConfig')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'environment_config_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _detect_environment(self) -> str:
        """Detect current environment"""
        # Check environment variable first
        env = os.getenv('MYRVM_ENVIRONMENT', '').lower()
        if env in ['development', 'dev', 'staging', 'production', 'prod']:
            return env if env not in ['dev', 'prod'] else ('development' if env == 'dev' else 'production')
        
        # Check for environment files
        env_files = {
            'development': '.env.development',
            'staging': '.env.staging', 
            'production': '.env.production'
        }
        
        for env_name, env_file in env_files.items():
            if (self.config_dir / env_file).exists():
                return env_name
        
        # Check hostname for production indicators
        hostname = os.uname().nodename.lower()
        if any(indicator in hostname for indicator in ['prod', 'production', 'live']):
            return 'production'
        elif any(indicator in hostname for indicator in ['staging', 'stage', 'test']):
            return 'staging'
        
        # Default to development
        return 'development'
    
    def _get_config_schema(self) -> Dict:
        """Get configuration schema for validation"""
        return {
            'type': 'object',
            'required': ['environment', 'myrvm_base_url', 'rvm_id'],
            'properties': {
                'environment': {
                    'type': 'string',
                    'enum': ['development', 'staging', 'production']
                },
                'myrvm_base_url': {
                    'type': 'string',
                    'format': 'uri'
                },
                'rvm_id': {
                    'type': 'integer',
                    'minimum': 1
                },
                'camera_index': {
                    'type': 'integer',
                    'minimum': 0,
                    'default': 0
                },
                'capture_interval': {
                    'type': 'number',
                    'minimum': 0.1,
                    'default': 5.0
                },
                'confidence_threshold': {
                    'type': 'number',
                    'minimum': 0.0,
                    'maximum': 1.0,
                    'default': 0.5
                },
                'auto_processing': {
                    'type': 'boolean',
                    'default': True
                },
                'use_tunnel': {
                    'type': 'boolean',
                    'default': False
                },
                'monitoring_interval': {
                    'type': 'number',
                    'minimum': 1.0,
                    'default': 30.0
                },
                'health_check_interval': {
                    'type': 'number',
                    'minimum': 1.0,
                    'default': 60.0
                },
                'max_processing_queue': {
                    'type': 'integer',
                    'minimum': 1,
                    'default': 10
                },
                'batch_size': {
                    'type': 'integer',
                    'minimum': 1,
                    'default': 4
                },
                'batch_timeout': {
                    'type': 'number',
                    'minimum': 0.1,
                    'default': 2.0
                },
                'max_memory_mb': {
                    'type': 'integer',
                    'minimum': 256,
                    'default': 1024
                },
                'memory_threshold': {
                    'type': 'number',
                    'minimum': 0.1,
                    'maximum': 1.0,
                    'default': 0.8
                },
                'log_level': {
                    'type': 'string',
                    'enum': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    'default': 'INFO'
                },
                'security': {
                    'type': 'object',
                    'properties': {
                        'encrypt_credentials': {
                            'type': 'boolean',
                            'default': True
                        },
                        'require_https': {
                            'type': 'boolean',
                            'default': False
                        },
                        'access_control': {
                            'type': 'boolean',
                            'default': False
                        }
                    }
                }
            }
        }
    
    def _load_base_config(self) -> Dict:
        """Load base configuration"""
        base_config_file = self.config_dir / 'base_config.json'
        
        if base_config_file.exists():
            try:
                with open(base_config_file, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded base configuration from {base_config_file}")
                return config
            except Exception as e:
                self.logger.error(f"Failed to load base configuration: {e}")
        
        # Return default base configuration
        return {
            'environment': self.environment,
            'camera_index': 0,
            'capture_interval': 5.0,
            'confidence_threshold': 0.5,
            'auto_processing': True,
            'use_tunnel': False,
            'monitoring_interval': 30.0,
            'health_check_interval': 60.0,
            'max_processing_queue': 10,
            'batch_size': 4,
            'batch_timeout': 2.0,
            'max_memory_mb': 1024,
            'memory_threshold': 0.8,
            'log_level': 'INFO',
            'security': {
                'encrypt_credentials': True,
                'require_https': False,
                'access_control': False
            }
        }
    
    def _load_environment_config(self) -> Dict:
        """Load environment-specific configuration"""
        env_config_file = self.config_dir / f'{self.environment}_config.json'
        
        if env_config_file.exists():
            try:
                with open(env_config_file, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded {self.environment} configuration from {env_config_file}")
                return config
            except Exception as e:
                self.logger.error(f"Failed to load {self.environment} configuration: {e}")
        
        # Return environment-specific defaults
        if self.environment == 'production':
            return {
                'log_level': 'WARNING',
                'security': {
                    'encrypt_credentials': True,
                    'require_https': True,
                    'access_control': True
                },
                'monitoring_interval': 15.0,
                'health_check_interval': 30.0
            }
        elif self.environment == 'staging':
            return {
                'log_level': 'INFO',
                'security': {
                    'encrypt_credentials': True,
                    'require_https': False,
                    'access_control': True
                },
                'monitoring_interval': 20.0,
                'health_check_interval': 45.0
            }
        else:  # development
            return {
                'log_level': 'DEBUG',
                'security': {
                    'encrypt_credentials': False,
                    'require_https': False,
                    'access_control': False
                },
                'monitoring_interval': 60.0,
                'health_check_interval': 120.0
            }
    
    def _merge_configurations(self) -> Dict:
        """Merge base and environment configurations"""
        merged_config = self.base_config.copy()
        
        # Deep merge environment configuration
        def deep_merge(base: Dict, override: Dict) -> Dict:
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    base[key] = deep_merge(base[key], value)
                else:
                    base[key] = value
            return base
        
        merged_config = deep_merge(merged_config, self.env_config)
        
        # Set environment
        merged_config['environment'] = self.environment
        
        # Load from environment variables (highest priority)
        self._load_from_environment_variables(merged_config)
        
        return merged_config
    
    def _load_from_environment_variables(self, config: Dict):
        """Load configuration from environment variables"""
        env_mappings = {
            'MYRVM_BASE_URL': 'myrvm_base_url',
            'RVM_ID': 'rvm_id',
            'CAMERA_INDEX': 'camera_index',
            'CAPTURE_INTERVAL': 'capture_interval',
            'CONFIDENCE_THRESHOLD': 'confidence_threshold',
            'AUTO_PROCESSING': 'auto_processing',
            'USE_TUNNEL': 'use_tunnel',
            'LOG_LEVEL': 'log_level',
            'BATCH_SIZE': 'batch_size',
            'MAX_MEMORY_MB': 'max_memory_mb'
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert value to appropriate type
                if config_key in ['rvm_id', 'camera_index', 'batch_size', 'max_memory_mb']:
                    config[config_key] = int(value)
                elif config_key in ['capture_interval', 'confidence_threshold', 'max_memory_mb']:
                    config[config_key] = float(value)
                elif config_key in ['auto_processing', 'use_tunnel']:
                    config[config_key] = value.lower() in ['true', '1', 'yes', 'on']
                else:
                    config[config_key] = value
                
                self.logger.debug(f"Loaded {config_key} from environment variable {env_var}")
    
    def _validate_configuration(self):
        """Validate configuration against schema"""
        try:
            # Basic validation
            required_fields = self.config_schema.get('required', [])
            for field in required_fields:
                if field not in self.config:
                    raise ValueError(f"Required configuration field missing: {field}")
            
            # Type validation
            properties = self.config_schema.get('properties', {})
            for key, value in self.config.items():
                if key in properties:
                    prop_schema = properties[key]
                    expected_type = prop_schema.get('type')
                    
                    if expected_type == 'string' and not isinstance(value, str):
                        raise ValueError(f"Configuration field {key} must be string")
                    elif expected_type == 'integer' and not isinstance(value, int):
                        raise ValueError(f"Configuration field {key} must be integer")
                    elif expected_type == 'number' and not isinstance(value, (int, float)):
                        raise ValueError(f"Configuration field {key} must be number")
                    elif expected_type == 'boolean' and not isinstance(value, bool):
                        raise ValueError(f"Configuration field {key} must be boolean")
            
            self.logger.info("Configuration validation passed")
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.logger.debug(f"Configuration updated: {key} = {value}")
    
    def reload(self):
        """Reload configuration from files"""
        try:
            self.logger.info("Reloading configuration...")
            
            # Reload configurations
            self.base_config = self._load_base_config()
            self.env_config = self._load_environment_config()
            self.config = self._merge_configurations()
            
            # Validate new configuration
            self._validate_configuration()
            
            self.logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            raise
    
    def save_config(self, filename: str = None):
        """Save current configuration to file"""
        try:
            if filename is None:
                filename = f'current_config_{self.environment}.json'
            
            config_file = self.config_dir / filename
            
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def get_environment_info(self) -> Dict:
        """Get environment information"""
        return {
            'environment': self.environment,
            'config_dir': str(self.config_dir),
            'base_config_file': str(self.config_dir / 'base_config.json'),
            'env_config_file': str(self.config_dir / f'{self.environment}_config.json'),
            'config_keys': list(self.config.keys()),
            'last_updated': datetime.now().isoformat()
        }
    
    def start_watching(self):
        """Start watching configuration files for changes"""
        if not self.is_watching:
            self.is_watching = True
            self.watch_thread = threading.Thread(target=self._watch_config_files)
            self.watch_thread.start()
            self.logger.info("Configuration file watching started")
    
    def stop_watching(self):
        """Stop watching configuration files"""
        if self.is_watching:
            self.is_watching = False
            if self.watch_thread:
                self.watch_thread.join(timeout=5)
            self.logger.info("Configuration file watching stopped")
    
    def _watch_config_files(self):
        """Watch configuration files for changes"""
        import time
        
        config_files = [
            self.config_dir / 'base_config.json',
            self.config_dir / f'{self.environment}_config.json'
        ]
        
        file_times = {}
        for config_file in config_files:
            if config_file.exists():
                file_times[str(config_file)] = config_file.stat().st_mtime
        
        while self.is_watching:
            try:
                for config_file in config_files:
                    if config_file.exists():
                        current_time = config_file.stat().st_mtime
                        file_key = str(config_file)
                        
                        if file_key in file_times and current_time > file_times[file_key]:
                            self.logger.info(f"Configuration file changed: {config_file}")
                            self.reload()
                            file_times[file_key] = current_time
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Configuration file watching error: {e}")
                time.sleep(5)
    
    def get_configuration_report(self) -> str:
        """Generate configuration report"""
        env_info = self.get_environment_info()
        
        report = f"""
Environment Configuration Report
===============================
Environment: {env_info['environment']}
Configuration Directory: {env_info['config_dir']}
Base Config File: {env_info['base_config_file']}
Environment Config File: {env_info['env_config_file']}
Last Updated: {env_info['last_updated']}

Configuration Keys ({len(env_info['config_keys'])}):
{', '.join(env_info['config_keys'])}

Key Configuration Values:
- MyRVM Base URL: {self.get('myrvm_base_url', 'Not set')}
- RVM ID: {self.get('rvm_id', 'Not set')}
- Camera Index: {self.get('camera_index', 0)}
- Capture Interval: {self.get('capture_interval', 5.0)}s
- Confidence Threshold: {self.get('confidence_threshold', 0.5)}
- Auto Processing: {self.get('auto_processing', True)}
- Log Level: {self.get('log_level', 'INFO')}
- Batch Size: {self.get('batch_size', 4)}
- Max Memory: {self.get('max_memory_mb', 1024)}MB

Security Settings:
- Encrypt Credentials: {self.get('security.encrypt_credentials', False)}
- Require HTTPS: {self.get('security.require_https', False)}
- Access Control: {self.get('security.access_control', False)}

File Watching: {'Active' if self.is_watching else 'Inactive'}
"""
        return report
