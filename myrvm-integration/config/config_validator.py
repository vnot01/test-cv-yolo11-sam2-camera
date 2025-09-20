"""
Configuration Validator for MyRVM Integration
Validates configuration values and provides error handling
"""

import re
import ipaddress
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationRule:
    """Configuration validation rule"""
    field: str
    required: bool = False
    data_type: type = None
    min_value: Any = None
    max_value: Any = None
    allowed_values: List[Any] = None
    pattern: str = None
    custom_validator: callable = None


@dataclass
class ValidationResult:
    """Configuration validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    field_results: Dict[str, Dict[str, Any]]


class ConfigurationValidator:
    """
    Configuration validator with comprehensive validation rules
    """
    
    def __init__(self):
        """Initialize configuration validator"""
        self.validation_rules = self._get_validation_rules()
        self.custom_validators = self._get_custom_validators()
    
    def _get_validation_rules(self) -> Dict[str, ValidationRule]:
        """Get validation rules for all configuration fields"""
        return {
            # Core Configuration
            'rvm_id': ValidationRule(
                field='rvm_id',
                required=True,
                data_type=str,
                pattern=r'^[a-zA-Z0-9_-]+$'
            ),
            'myrvm_base_url': ValidationRule(
                field='myrvm_base_url',
                required=True,
                data_type=str,
                custom_validator=self._validate_url
            ),
            'api_key': ValidationRule(
                field='api_key',
                required=True,
                data_type=str,
                min_value=10  # Minimum length
            ),
            
            # Camera Configuration
            'camera_index': ValidationRule(
                field='camera_index',
                required=True,
                data_type=int,
                min_value=0,
                max_value=10
            ),
            'capture_interval': ValidationRule(
                field='capture_interval',
                required=True,
                data_type=(int, float),
                min_value=0.1,
                max_value=60.0
            ),
            
            # Network Configuration
            'jetson_ip': ValidationRule(
                field='jetson_ip',
                required=True,
                data_type=str,
                custom_validator=self._validate_ip_address
            ),
            'jetson_port': ValidationRule(
                field='jetson_port',
                required=True,
                data_type=int,
                min_value=1,
                max_value=65535
            ),
            
            # Detection Configuration
            'confidence_threshold': ValidationRule(
                field='confidence_threshold',
                required=True,
                data_type=(int, float),
                min_value=0.0,
                max_value=1.0
            ),
            'max_processing_queue': ValidationRule(
                field='max_processing_queue',
                required=True,
                data_type=int,
                min_value=1,
                max_value=100
            ),
            
            # Remote Access Configuration
            'remote_access_enabled': ValidationRule(
                field='remote_access_enabled',
                required=False,
                data_type=bool
            ),
            'remote_access_port': ValidationRule(
                field='remote_access_port',
                required=False,
                data_type=int,
                min_value=1,
                max_value=65535
            ),
            'admin_ips': ValidationRule(
                field='admin_ips',
                required=False,
                data_type=list,
                custom_validator=self._validate_ip_list
            ),
            
            # Timezone Configuration
            'default_timezone': ValidationRule(
                field='default_timezone',
                required=False,
                data_type=str,
                pattern=r'^[A-Za-z_/]+$'
            ),
            'auto_sync_enabled': ValidationRule(
                field='auto_sync_enabled',
                required=False,
                data_type=bool
            ),
            'sync_interval': ValidationRule(
                field='sync_interval',
                required=False,
                data_type=int,
                min_value=60,
                max_value=86400
            ),
            
            # Backup Configuration
            'backup_enabled': ValidationRule(
                field='backup_enabled',
                required=False,
                data_type=bool
            ),
            'backup_interval': ValidationRule(
                field='backup_interval',
                required=False,
                data_type=int,
                min_value=3600,
                max_value=604800
            ),
            'backup_retention': ValidationRule(
                field='backup_retention',
                required=False,
                data_type=int,
                min_value=1,
                max_value=365
            ),
            
            # Monitoring Configuration
            'monitoring_enabled': ValidationRule(
                field='monitoring_enabled',
                required=False,
                data_type=bool
            ),
            'metrics_interval': ValidationRule(
                field='metrics_interval',
                required=False,
                data_type=int,
                min_value=60,
                max_value=3600
            ),
            'upload_interval': ValidationRule(
                field='upload_interval',
                required=False,
                data_type=int,
                min_value=300,
                max_value=86400
            ),
            
            # Hardware Configuration
            'hardware.camera_resolution': ValidationRule(
                field='hardware.camera_resolution',
                required=False,
                data_type=str,
                pattern=r'^\d+x\d+$'
            ),
            'hardware.camera_fps': ValidationRule(
                field='hardware.camera_fps',
                required=False,
                data_type=int,
                min_value=1,
                max_value=60
            ),
            'hardware.gpu_memory_limit': ValidationRule(
                field='hardware.gpu_memory_limit',
                required=False,
                data_type=int,
                min_value=512,
                max_value=8192
            ),
            'hardware.cpu_cores': ValidationRule(
                field='hardware.cpu_cores',
                required=False,
                data_type=int,
                min_value=1,
                max_value=16
            ),
            
            # Detection Model Configuration
            'detection.yolo_model_path': ValidationRule(
                field='detection.yolo_model_path',
                required=False,
                data_type=str,
                custom_validator=self._validate_file_path
            ),
            'detection.yolo11n_path': ValidationRule(
                field='detection.yolo11n_path',
                required=False,
                data_type=str,
                custom_validator=self._validate_file_path
            ),
            'detection.sam2_model_path': ValidationRule(
                field='detection.sam2_model_path',
                required=False,
                data_type=str,
                custom_validator=self._validate_file_path
            ),
            'detection.batch_size': ValidationRule(
                field='detection.batch_size',
                required=False,
                data_type=int,
                min_value=1,
                max_value=32
            ),
            'detection.device': ValidationRule(
                field='detection.device',
                required=False,
                data_type=str,
                allowed_values=['cpu', 'cuda', 'auto']
            ),
            
            # Storage Configuration
            'storage.images_dir': ValidationRule(
                field='storage.images_dir',
                required=False,
                data_type=str,
                custom_validator=self._validate_directory_path
            ),
            'storage.logs_dir': ValidationRule(
                field='storage.logs_dir',
                required=False,
                data_type=str,
                custom_validator=self._validate_directory_path
            ),
            'storage.cache_dir': ValidationRule(
                field='storage.cache_dir',
                required=False,
                data_type=str,
                custom_validator=self._validate_directory_path
            ),
            'storage.backup_dir': ValidationRule(
                field='storage.backup_dir',
                required=False,
                data_type=str,
                custom_validator=self._validate_directory_path
            ),
            
            # GUI Configuration
            'gui.port': ValidationRule(
                field='gui.port',
                required=False,
                data_type=int,
                min_value=1,
                max_value=65535
            ),
            'gui.host': ValidationRule(
                field='gui.host',
                required=False,
                data_type=str,
                allowed_values=['0.0.0.0', '127.0.0.1', 'localhost']
            ),
            'gui.debug': ValidationRule(
                field='gui.debug',
                required=False,
                data_type=bool
            ),
            'gui.auto_reload': ValidationRule(
                field='gui.auto_reload',
                required=False,
                data_type=bool
            )
        }
    
    def _get_custom_validators(self) -> Dict[str, callable]:
        """Get custom validation functions"""
        return {
            'url': self._validate_url,
            'ip_address': self._validate_ip_address,
            'ip_list': self._validate_ip_list,
            'file_path': self._validate_file_path,
            'directory_path': self._validate_directory_path
        }
    
    def _validate_url(self, value: str) -> Tuple[bool, str]:
        """Validate URL format"""
        if not isinstance(value, str):
            return False, "URL must be a string"
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(value):
            return False, "Invalid URL format"
        
        return True, ""
    
    def _validate_ip_address(self, value: str) -> Tuple[bool, str]:
        """Validate IP address format"""
        if not isinstance(value, str):
            return False, "IP address must be a string"
        
        try:
            ipaddress.ip_address(value)
            return True, ""
        except ValueError:
            return False, "Invalid IP address format"
    
    def _validate_ip_list(self, value: list) -> Tuple[bool, str]:
        """Validate list of IP addresses or CIDR blocks"""
        if not isinstance(value, list):
            return False, "IP list must be a list"
        
        for ip_item in value:
            if not isinstance(ip_item, str):
                return False, "All IP list items must be strings"
            
            try:
                # Try to parse as IP address or network
                if '/' in ip_item:
                    ipaddress.ip_network(ip_item, strict=False)
                else:
                    ipaddress.ip_address(ip_item)
            except ValueError:
                return False, f"Invalid IP address or CIDR block: {ip_item}"
        
        return True, ""
    
    def _validate_file_path(self, value: str) -> Tuple[bool, str]:
        """Validate file path"""
        if not isinstance(value, str):
            return False, "File path must be a string"
        
        if not value.strip():
            return False, "File path cannot be empty"
        
        # Check if path contains valid characters
        if not re.match(r'^[a-zA-Z0-9_./-]+$', value):
            return False, "File path contains invalid characters"
        
        return True, ""
    
    def _validate_directory_path(self, value: str) -> Tuple[bool, str]:
        """Validate directory path"""
        if not isinstance(value, str):
            return False, "Directory path must be a string"
        
        if not value.strip():
            return False, "Directory path cannot be empty"
        
        # Check if path contains valid characters
        if not re.match(r'^[a-zA-Z0-9_./-]+$', value):
            return False, "Directory path contains invalid characters"
        
        return True, ""
    
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete configuration
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        field_results = {}
        
        # Validate each field
        for field_name, rule in self.validation_rules.items():
            field_result = self._validate_field(config, field_name, rule)
            field_results[field_name] = field_result
            
            if field_result['errors']:
                errors.extend(field_result['errors'])
            
            if field_result['warnings']:
                warnings.extend(field_result['warnings'])
        
        # Cross-field validation
        cross_validation_errors = self._cross_field_validation(config)
        errors.extend(cross_validation_errors)
        
        # Performance warnings
        performance_warnings = self._performance_validation(config)
        warnings.extend(performance_warnings)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_results=field_results
        )
    
    def _validate_field(self, config: Dict[str, Any], field_name: str, rule: ValidationRule) -> Dict[str, Any]:
        """Validate individual field"""
        errors = []
        warnings = []
        
        # Get field value (support dot notation)
        field_value = self._get_nested_value(config, field_name)
        
        # Check if required field is present
        if rule.required and field_value is None:
            errors.append(f"Required field '{field_name}' is missing")
            return {'errors': errors, 'warnings': warnings, 'value': field_value}
        
        # Skip validation if field is not present and not required
        if field_value is None:
            return {'errors': errors, 'warnings': warnings, 'value': field_value}
        
        # Data type validation
        if rule.data_type and not isinstance(field_value, rule.data_type):
            if isinstance(rule.data_type, tuple):
                type_names = [t.__name__ for t in rule.data_type]
                errors.append(f"Field '{field_name}' must be one of: {', '.join(type_names)}")
            else:
                errors.append(f"Field '{field_name}' must be of type {rule.data_type.__name__}")
            return {'errors': errors, 'warnings': warnings, 'value': field_value}
        
        # Range validation for numeric values
        if rule.min_value is not None and field_value < rule.min_value:
            errors.append(f"Field '{field_name}' must be >= {rule.min_value}")
        
        if rule.max_value is not None and field_value > rule.max_value:
            errors.append(f"Field '{field_name}' must be <= {rule.max_value}")
        
        # Allowed values validation
        if rule.allowed_values and field_value not in rule.allowed_values:
            errors.append(f"Field '{field_name}' must be one of: {', '.join(map(str, rule.allowed_values))}")
        
        # Pattern validation
        if rule.pattern and isinstance(field_value, str):
            if not re.match(rule.pattern, field_value):
                errors.append(f"Field '{field_name}' does not match required pattern")
        
        # Custom validation
        if rule.custom_validator:
            is_valid, error_msg = rule.custom_validator(field_value)
            if not is_valid:
                errors.append(f"Field '{field_name}': {error_msg}")
        
        return {'errors': errors, 'warnings': warnings, 'value': field_value}
    
    def _get_nested_value(self, config: Dict[str, Any], field_name: str) -> Any:
        """Get nested value from configuration using dot notation"""
        keys = field_name.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _cross_field_validation(self, config: Dict[str, Any]) -> List[str]:
        """Cross-field validation rules"""
        errors = []
        
        # Check if remote access port conflicts with jetson port
        jetson_port = config.get('jetson_port')
        remote_access_port = config.get('remote_access_port')
        
        if jetson_port and remote_access_port and jetson_port == remote_access_port:
            errors.append("jetson_port and remote_access_port cannot be the same")
        
        # Check if GUI port conflicts with other ports
        gui_port = config.get('gui', {}).get('port')
        if gui_port:
            if jetson_port and gui_port == jetson_port:
                errors.append("gui.port and jetson_port cannot be the same")
            if remote_access_port and gui_port == remote_access_port:
                errors.append("gui.port and remote_access_port cannot be the same")
        
        # Check if backup interval is reasonable compared to retention
        backup_interval = config.get('backup_interval')
        backup_retention = config.get('backup_retention')
        
        if backup_interval and backup_retention:
            # Convert backup_interval from seconds to days
            backup_interval_days = backup_interval / 86400
            if backup_interval_days > backup_retention:
                errors.append("backup_interval should not be longer than backup_retention")
        
        return errors
    
    def _performance_validation(self, config: Dict[str, Any]) -> List[str]:
        """Performance-related validation warnings"""
        warnings = []
        
        # Check confidence threshold
        confidence_threshold = config.get('confidence_threshold')
        if confidence_threshold is not None:
            if confidence_threshold < 0.3:
                warnings.append("Low confidence threshold (< 0.3) may result in many false positives")
            elif confidence_threshold > 0.8:
                warnings.append("High confidence threshold (> 0.8) may result in missed detections")
        
        # Check capture interval
        capture_interval = config.get('capture_interval')
        if capture_interval is not None:
            if capture_interval < 1.0:
                warnings.append("Very short capture interval (< 1s) may impact system performance")
            elif capture_interval > 30.0:
                warnings.append("Long capture interval (> 30s) may result in delayed detection")
        
        # Check processing queue size
        max_processing_queue = config.get('max_processing_queue')
        if max_processing_queue is not None:
            if max_processing_queue > 50:
                warnings.append("Large processing queue (> 50) may consume significant memory")
        
        # Check GPU memory limit
        gpu_memory_limit = config.get('hardware', {}).get('gpu_memory_limit')
        if gpu_memory_limit is not None:
            if gpu_memory_limit < 1024:
                warnings.append("Low GPU memory limit (< 1GB) may impact model performance")
        
        return warnings
    
    def validate_field(self, config: Dict[str, Any], field_name: str) -> Dict[str, Any]:
        """
        Validate specific field
        
        Args:
            config: Configuration dictionary
            field_name: Field name to validate
            
        Returns:
            Validation result for the field
        """
        if field_name not in self.validation_rules:
            return {
                'errors': [f"No validation rule found for field '{field_name}'"],
                'warnings': [],
                'value': self._get_nested_value(config, field_name)
            }
        
        rule = self.validation_rules[field_name]
        return self._validate_field(config, field_name, rule)


# Example usage and testing
if __name__ == "__main__":
    # Test configuration
    test_config = {
        "rvm_id": "jetson_orin_nano_001",
        "myrvm_base_url": "http://172.28.233.83:8001",
        "api_key": "test_api_key_12345",
        "camera_index": 0,
        "capture_interval": 5.0,
        "jetson_ip": "172.28.93.97",
        "jetson_port": 5000,
        "confidence_threshold": 0.5,
        "max_processing_queue": 10,
        "remote_access_enabled": True,
        "remote_access_port": 5001,
        "admin_ips": ["192.168.1.0/24", "10.0.0.0/8"],
        "default_timezone": "Asia/Jakarta",
        "auto_sync_enabled": True,
        "sync_interval": 3600,
        "backup_enabled": True,
        "backup_interval": 86400,
        "backup_retention": 30,
        "monitoring_enabled": True,
        "metrics_interval": 300,
        "upload_interval": 3600,
        "hardware": {
            "camera_resolution": "1920x1080",
            "camera_fps": 30,
            "gpu_memory_limit": 2048,
            "cpu_cores": 6
        },
        "detection": {
            "yolo_model_path": "../models/best.pt",
            "yolo11n_path": "../models/yolo11n.pt",
            "sam2_model_path": "../models/sam2.1_b.pt",
            "batch_size": 1,
            "device": "cuda"
        },
        "storage": {
            "images_dir": "../storages/images",
            "logs_dir": "../logs",
            "cache_dir": "../cache",
            "backup_dir": "../backups"
        },
        "gui": {
            "port": 5002,
            "host": "0.0.0.0",
            "debug": False,
            "auto_reload": False
        }
    }
    
    # Test validator
    validator = ConfigurationValidator()
    result = validator.validate_configuration(test_config)
    
    print("Configuration Validation Test:")
    print(f"Valid: {result.is_valid}")
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    
    # Test individual field validation
    field_result = validator.validate_field(test_config, "confidence_threshold")
    print(f"Confidence threshold validation: {field_result}")
    
    print("Configuration validator test completed successfully!")
