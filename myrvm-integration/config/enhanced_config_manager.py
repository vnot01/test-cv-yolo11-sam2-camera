"""
Enhanced Configuration Manager for MyRVM Integration
Handles static and dynamic configuration with real-time updates
"""

import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass, asdict


@dataclass
class ConfigValidationResult:
    """Configuration validation result"""
    is_valid: bool
    errors: list
    warnings: list


class EnhancedConfigurationManager:
    """
    Enhanced configuration manager with dynamic updates from API server
    """
    
    def __init__(self, api_client, rvm_id: str, config_dir: str = "config"):
        """
        Initialize Enhanced Configuration Manager
        
        Args:
            api_client: MyRVM API client instance
            rvm_id: RVM identifier
            config_dir: Configuration directory path
        """
        self.api_client = api_client
        self.rvm_id = rvm_id
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Configuration storage
        self.static_config = {}
        self.dynamic_config = {}
        self.merged_config = {}
        self.config_cache = {}
        
        # Update management
        self.last_update = None
        self.update_interval = 300  # 5 minutes
        self.update_thread = None
        self.is_updating = False
        self.update_callbacks = []
        
        # Error handling
        self.max_retry_attempts = 3
        self.retry_delay = 5  # seconds
        self.fallback_config = self._get_fallback_config()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize configuration
        self._initialize_configuration()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for configuration manager"""
        logger = logging.getLogger('EnhancedConfigManager')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'config_manager_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get fallback configuration for error recovery"""
        return {
            "myrvm_base_url": "http://localhost:8000",
            "rvm_id": self.rvm_id,
            "api_key": None,
            "camera_index": 0,
            "models_dir": "../models",
            "jetson_ip": "127.0.0.1",
            "jetson_port": 5000,
            "capture_interval": 5.0,
            "auto_processing": True,
            "max_processing_queue": 10,
            "confidence_threshold": 0.5,
            "remote_access_enabled": False,
            "remote_access_port": 5001,
            "admin_ips": [],
            "default_timezone": "Asia/Jakarta",
            "auto_sync_enabled": True,
            "sync_interval": 3600,
            "backup_enabled": False,
            "backup_interval": 86400,
            "backup_retention": 30,
            "monitoring_enabled": True,
            "metrics_interval": 300,
            "upload_interval": 3600
        }
    
    def _initialize_configuration(self):
        """Initialize configuration by loading static and dynamic configs"""
        try:
            self.logger.info("Initializing configuration...")
            
            # Load static configuration
            self._load_static_config()
            
            # Load dynamic configuration
            self._load_dynamic_config()
            
            # Merge configurations
            self._merge_configurations()
            
            # Validate merged configuration
            validation_result = self._validate_configuration(self.merged_config)
            if not validation_result.is_valid:
                self.logger.warning(f"Configuration validation failed: {validation_result.errors}")
                self._handle_configuration_error(validation_result.errors)
            
            # Start background update thread
            self._start_background_updates()
            
            self.logger.info("Configuration initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Configuration initialization failed: {e}")
            self._handle_initialization_error(e)
    
    def _load_static_config(self):
        """Load static configuration from base_config.json"""
        try:
            static_config_file = self.config_dir / "base_config.json"
            
            if static_config_file.exists():
                with open(static_config_file, 'r') as f:
                    self.static_config = json.load(f)
                self.logger.info(f"Static configuration loaded from {static_config_file}")
            else:
                self.logger.warning(f"Static config file not found: {static_config_file}")
                self.static_config = {}
                
        except Exception as e:
            self.logger.error(f"Failed to load static configuration: {e}")
            self.static_config = {}
    
    def _load_dynamic_config(self):
        """Load dynamic configuration from API server"""
        try:
            if not self.api_client:
                self.logger.warning("API client not available, skipping dynamic config")
                self.dynamic_config = {}
                return
            
            # Fetch configuration from server
            response = self.api_client.get_rvm_config(self.rvm_id)
            
            if response and response.get('success'):
                self.dynamic_config = response.get('data', {})
                self.logger.info("Dynamic configuration loaded from API server")
            else:
                self.logger.warning("Failed to fetch dynamic configuration from API server")
                self.dynamic_config = {}
                
        except Exception as e:
            self.logger.error(f"Failed to load dynamic configuration: {e}")
            self.dynamic_config = {}
    
    def _merge_configurations(self):
        """Merge static and dynamic configurations with priority handling"""
        try:
            # Start with fallback configuration
            self.merged_config = self.fallback_config.copy()
            
            # Apply static configuration (medium priority)
            self.merged_config.update(self.static_config)
            
            # Apply dynamic configuration (highest priority)
            self.merged_config.update(self.dynamic_config)
            
            # Update timestamp
            self.merged_config['_last_updated'] = datetime.now().isoformat()
            self.merged_config['_config_source'] = 'merged'
            
            self.logger.info("Configurations merged successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to merge configurations: {e}")
            self.merged_config = self.fallback_config.copy()
    
    def _validate_configuration(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """Validate configuration values"""
        errors = []
        warnings = []
        
        try:
            # Required fields validation
            required_fields = ['rvm_id', 'myrvm_base_url', 'api_key']
            for field in required_fields:
                if field not in config or config[field] is None:
                    errors.append(f"Required field '{field}' is missing or None")
            
            # Data type validation
            if 'camera_index' in config and not isinstance(config['camera_index'], int):
                errors.append("'camera_index' must be an integer")
            
            if 'capture_interval' in config and not isinstance(config['capture_interval'], (int, float)):
                errors.append("'capture_interval' must be a number")
            
            if 'confidence_threshold' in config:
                threshold = config['confidence_threshold']
                if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
                    errors.append("'confidence_threshold' must be a number between 0 and 1")
            
            # URL validation
            if 'myrvm_base_url' in config:
                url = config['myrvm_base_url']
                if not url.startswith(('http://', 'https://')):
                    errors.append("'myrvm_base_url' must be a valid URL")
            
            # Port validation
            port_fields = ['jetson_port', 'remote_access_port']
            for field in port_fields:
                if field in config:
                    port = config[field]
                    if not isinstance(port, int) or not (1 <= port <= 65535):
                        errors.append(f"'{field}' must be an integer between 1 and 65535")
            
            # Warning checks
            if config.get('confidence_threshold', 0.5) < 0.3:
                warnings.append("Low confidence threshold may result in false positives")
            
            if config.get('capture_interval', 5.0) < 1.0:
                warnings.append("Very short capture interval may impact performance")
            
            is_valid = len(errors) == 0
            
            return ConfigValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ConfigValidationResult(
                is_valid=False,
                errors=[f"Validation error: {e}"],
                warnings=[]
            )
    
    def _handle_configuration_error(self, errors: list):
        """Handle configuration validation errors"""
        self.logger.error(f"Configuration errors: {errors}")
        
        # Use fallback configuration
        self.merged_config = self.fallback_config.copy()
        self.merged_config['_config_source'] = 'fallback'
        self.merged_config['_errors'] = errors
    
    def _handle_initialization_error(self, error: Exception):
        """Handle initialization errors"""
        self.logger.error(f"Initialization error: {error}")
        
        # Use fallback configuration
        self.merged_config = self.fallback_config.copy()
        self.merged_config['_config_source'] = 'fallback'
        self.merged_config['_init_error'] = str(error)
    
    def _start_background_updates(self):
        """Start background thread for periodic configuration updates"""
        if self.update_thread and self.update_thread.is_alive():
            return
        
        self.update_thread = threading.Thread(
            target=self._background_update_loop,
            daemon=True,
            name="ConfigUpdateThread"
        )
        self.update_thread.start()
        self.logger.info("Background configuration update thread started")
    
    def _background_update_loop(self):
        """Background loop for periodic configuration updates"""
        while True:
            try:
                time.sleep(self.update_interval)
                
                if not self.is_updating:
                    self._update_dynamic_config()
                    
            except Exception as e:
                self.logger.error(f"Background update error: {e}")
                time.sleep(self.retry_delay)
    
    def _update_dynamic_config(self):
        """Update dynamic configuration from API server"""
        if self.is_updating:
            return
        
        self.is_updating = True
        
        try:
            self.logger.info("Updating dynamic configuration...")
            
            # Fetch latest configuration
            old_config = self.dynamic_config.copy()
            self._load_dynamic_config()
            
            # Check if configuration changed
            if old_config != self.dynamic_config:
                self.logger.info("Configuration changes detected, merging...")
                self._merge_configurations()
                
                # Validate new configuration
                validation_result = self._validate_configuration(self.merged_config)
                if validation_result.is_valid:
                    self.last_update = datetime.now()
                    self._notify_configuration_changed()
                    self.logger.info("Configuration updated successfully")
                else:
                    self.logger.warning(f"Updated configuration validation failed: {validation_result.errors}")
                    # Revert to previous configuration
                    self.dynamic_config = old_config
                    self._merge_configurations()
            else:
                self.logger.debug("No configuration changes detected")
                
        except Exception as e:
            self.logger.error(f"Failed to update dynamic configuration: {e}")
        finally:
            self.is_updating = False
    
    def _notify_configuration_changed(self):
        """Notify registered callbacks about configuration changes"""
        for callback in self.update_callbacks:
            try:
                callback(self.merged_config)
            except Exception as e:
                self.logger.error(f"Configuration change callback error: {e}")
    
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            if key is None:
                return self.merged_config.copy()
            
            # Support dot notation for nested keys
            keys = key.split('.')
            value = self.merged_config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"Error getting config '{key}': {e}")
            return default
    
    def set_config(self, key: str, value: Any, persist: bool = False):
        """
        Set configuration value
        
        Args:
            key: Configuration key (dot notation supported)
            value: Configuration value
            persist: Whether to persist to static config file
        """
        try:
            # Support dot notation for nested keys
            keys = key.split('.')
            config = self.merged_config
            
            # Navigate to parent of target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            # Update timestamp
            self.merged_config['_last_updated'] = datetime.now().isoformat()
            
            if persist:
                self._persist_static_config()
            
            self.logger.info(f"Configuration '{key}' set to '{value}'")
            
        except Exception as e:
            self.logger.error(f"Error setting config '{key}': {e}")
    
    def _persist_static_config(self):
        """Persist static configuration to file"""
        try:
            static_config_file = self.config_dir / "base_config.json"
            
            # Remove dynamic fields before persisting
            static_config = {k: v for k, v in self.merged_config.items() 
                           if not k.startswith('_') and k not in self.dynamic_config}
            
            with open(static_config_file, 'w') as f:
                json.dump(static_config, f, indent=2)
            
            self.logger.info(f"Static configuration persisted to {static_config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to persist static configuration: {e}")
    
    def register_update_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Register callback for configuration updates
        
        Args:
            callback: Function to call when configuration changes
        """
        self.update_callbacks.append(callback)
        self.logger.info("Configuration update callback registered")
    
    def force_update(self):
        """Force immediate configuration update"""
        self.logger.info("Forcing configuration update...")
        self._update_dynamic_config()
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get configuration status information"""
        return {
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'update_interval': self.update_interval,
            'is_updating': self.is_updating,
            'config_source': self.merged_config.get('_config_source', 'unknown'),
            'static_config_keys': list(self.static_config.keys()),
            'dynamic_config_keys': list(self.dynamic_config.keys()),
            'merged_config_keys': list(self.merged_config.keys()),
            'validation_errors': self.merged_config.get('_errors', []),
            'initialization_error': self.merged_config.get('_init_error')
        }
    
    def shutdown(self):
        """Shutdown configuration manager"""
        self.logger.info("Shutting down configuration manager...")
        
        # Stop background thread
        if self.update_thread and self.update_thread.is_alive():
            # Note: Thread will stop when daemon=True and main thread exits
            pass
        
        self.logger.info("Configuration manager shutdown completed")


# Example usage and testing
if __name__ == "__main__":
    # Mock API client for testing
    class MockAPIClient:
        def get_rvm_config(self, rvm_id):
            return {
                'success': True,
                'data': {
                    'confidence_threshold': 0.6,
                    'remote_access_enabled': True,
                    'backup_enabled': True
                }
            }
    
    # Test configuration manager
    api_client = MockAPIClient()
    config_manager = EnhancedConfigurationManager(api_client, "test_rvm_001")
    
    # Test configuration access
    print("Configuration Manager Test:")
    print(f"RVM ID: {config_manager.get_config('rvm_id')}")
    print(f"Confidence Threshold: {config_manager.get_config('confidence_threshold')}")
    print(f"Remote Access Enabled: {config_manager.get_config('remote_access_enabled')}")
    
    # Test configuration status
    status = config_manager.get_config_status()
    print(f"Config Status: {status}")
    
    # Test configuration update callback
    def config_changed_callback(config):
        print(f"Configuration changed: {config.get('_last_updated')}")
    
    config_manager.register_update_callback(config_changed_callback)
    
    print("Configuration manager test completed successfully!")
