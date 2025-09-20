#!/usr/bin/env python3
"""
MyRVM Service Integration
Main service integration class for coordinating all services
"""

import logging
import threading
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import enhanced services
from config.enhanced_config_manager import EnhancedConfigurationManager
import importlib.util

# Import enhanced API client
spec = importlib.util.spec_from_file_location('enhanced_myrvm_api_client', 'api-client/enhanced_myrvm_api_client.py')
enhanced_api_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(enhanced_api_client)

@dataclass
class ServiceStatus:
    """Service status information"""
    name: str
    status: str  # running, stopped, error, starting, stopping
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    error_message: Optional[str] = None
    restart_count: int = 0
    last_health_check: Optional[datetime] = None

@dataclass
class ServiceMetrics:
    """Service performance metrics"""
    service_name: str
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    response_time: float = 0.0
    request_count: int = 0
    error_count: int = 0
    last_updated: Optional[datetime] = None

class MyRVMServiceIntegration:
    """Main service integration class for MyRVM Platform"""
    
    def __init__(self, rvm_id: str, config_dir: str = "config"):
        """
        Initialize MyRVM Service Integration
        
        Args:
            rvm_id: RVM identifier
            config_dir: Configuration directory path
        """
        self.rvm_id = rvm_id
        self.config_dir = config_dir
        
        # Core components
        self.config_manager = None
        self.api_client = None
        
        # Service management
        self.services = {}
        self.service_status = {}
        self.service_metrics = {}
        self.service_callbacks = {}
        
        # Integration state
        self.is_running = False
        self.is_initialized = False
        self.start_time = None
        
        # Threading
        self.monitor_thread = None
        self.metrics_thread = None
        self.shutdown_event = threading.Event()
        
        # Configuration
        self.health_check_interval = 30  # seconds
        self.metrics_interval = 60  # seconds
        self.max_restart_attempts = 3
        self.restart_delay = 5  # seconds
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Initialize integration
        self._initialize_integration()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for service integration"""
        logger = logging.getLogger('MyRVMServiceIntegration')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'service_integration_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _initialize_integration(self):
        """Initialize service integration components"""
        try:
            self.logger.info("Initializing MyRVM Service Integration...")
            
            # Initialize Enhanced API Client
            self._initialize_api_client()
            
            # Initialize Enhanced Configuration Manager
            self._initialize_config_manager()
            
            # Setup service callbacks
            self._setup_service_callbacks()
            
            # Initialize services
            self._initialize_services()
            
            self.is_initialized = True
            self.logger.info("Service integration initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Service integration initialization failed: {e}")
            raise
    
    def _initialize_api_client(self):
        """Initialize Enhanced API Client"""
        try:
            self.logger.info("Initializing Enhanced API Client...")
            
            # Get configuration for API client
            base_url = "http://172.28.233.83:8001"  # Default from config
            api_token = None  # Will be set from config
            
            self.api_client = enhanced_api_client.EnhancedMyRVMAPIClient(
                base_url=base_url,
                api_token=api_token,
                rvm_id=self.rvm_id
            )
            
            # Test connectivity
            success, response = self.api_client.test_connectivity()
            if success:
                self.logger.info("API client connectivity test passed")
            else:
                self.logger.warning(f"API client connectivity test failed: {response}")
            
            self.logger.info("Enhanced API Client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize API client: {e}")
            raise
    
    def _initialize_config_manager(self):
        """Initialize Enhanced Configuration Manager"""
        try:
            self.logger.info("Initializing Enhanced Configuration Manager...")
            
            self.config_manager = EnhancedConfigurationManager(
                api_client=self.api_client,
                rvm_id=self.rvm_id,
                config_dir=self.config_dir
            )
            
            # Register configuration update callback
            self.config_manager.register_update_callback(self._handle_config_update)
            
            self.logger.info("Enhanced Configuration Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration manager: {e}")
            raise
    
    def _setup_service_callbacks(self):
        """Setup service callbacks"""
        try:
            self.logger.info("Setting up service callbacks...")
            
            # Register WebSocket callback for real-time updates
            if self.api_client:
                self.api_client.register_websocket_callback(self._handle_websocket_message)
            
            self.logger.info("Service callbacks setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup service callbacks: {e}")
            raise
    
    def _initialize_services(self):
        """Initialize all services"""
        try:
            self.logger.info("Initializing services...")
            
            # Initialize detection service
            self._initialize_detection_service()
            
            # Initialize optimized detection service (skip for now due to missing dependencies)
            # self._initialize_optimized_detection_service()
            
            # Initialize other services as needed
            self._initialize_additional_services()
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _initialize_detection_service(self):
        """Initialize detection service"""
        try:
            from services.detection_service import DetectionService
            
            models_dir = self.config_manager.get_config('models_dir', '../models')
            
            detection_service = DetectionService(models_dir=models_dir)
            
            self.services['detection'] = detection_service
            self.service_status['detection'] = ServiceStatus(
                name='detection',
                status='stopped'
            )
            self.service_metrics['detection'] = ServiceMetrics(
                service_name='detection'
            )
            
            self.logger.info("Detection service initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize detection service: {e}")
            raise
    
    def _initialize_optimized_detection_service(self):
        """Initialize optimized detection service"""
        try:
            from services.optimized_detection_service import OptimizedDetectionService
            
            config = self.config_manager.get_config()
            
            optimized_detection_service = OptimizedDetectionService(config)
            
            self.services['optimized_detection'] = optimized_detection_service
            self.service_status['optimized_detection'] = ServiceStatus(
                name='optimized_detection',
                status='stopped'
            )
            self.service_metrics['optimized_detection'] = ServiceMetrics(
                service_name='optimized_detection'
            )
            
            self.logger.info("Optimized detection service initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize optimized detection service: {e}")
            raise
    
    def _initialize_additional_services(self):
        """Initialize additional services"""
        try:
            # Initialize timezone sync service
            self._initialize_timezone_service()
            
            # Initialize remote access service
            self._initialize_remote_access_service()
            
            self.logger.info("Additional services initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize additional services: {e}")
            # Don't raise - these are optional services
    
    def _initialize_timezone_service(self):
        """Initialize timezone sync service"""
        try:
            from services.timezone_sync_service import TimezoneSyncService
            
            timezone_service = TimezoneSyncService()
            
            self.services['timezone_sync'] = timezone_service
            self.service_status['timezone_sync'] = ServiceStatus(
                name='timezone_sync',
                status='stopped'
            )
            self.service_metrics['timezone_sync'] = ServiceMetrics(
                service_name='timezone_sync'
            )
            
            self.logger.info("Timezone sync service initialized")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize timezone sync service: {e}")
    
    def _initialize_remote_access_service(self):
        """Initialize remote access service"""
        try:
            from services.remote_access_controller import RemoteAccessController
            
            remote_access_service = RemoteAccessController()
            
            self.services['remote_access'] = remote_access_service
            self.service_status['remote_access'] = ServiceStatus(
                name='remote_access',
                status='stopped'
            )
            self.service_metrics['remote_access'] = ServiceMetrics(
                service_name='remote_access'
            )
            
            self.logger.info("Remote access service initialized")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize remote access service: {e}")
    
    def start_services(self):
        """Start all services"""
        try:
            self.logger.info("Starting all services...")
            
            if not self.is_initialized:
                raise RuntimeError("Service integration not initialized")
            
            # Start services in order
            service_start_order = [
                'timezone_sync',
                'detection',
                'optimized_detection',
                'remote_access'
            ]
            
            for service_name in service_start_order:
                if service_name in self.services:
                    self._start_service(service_name)
            
            # Start monitoring threads
            self._start_monitoring()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            self.logger.info("All services started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start services: {e}")
            raise
    
    def _start_service(self, service_name: str):
        """Start a specific service"""
        try:
            if service_name not in self.services:
                self.logger.warning(f"Service {service_name} not found")
                return
            
            service = self.services[service_name]
            status = self.service_status[service_name]
            
            self.logger.info(f"Starting service: {service_name}")
            
            # Update status
            status.status = 'starting'
            status.start_time = datetime.now()
            
            # Start service based on type
            if hasattr(service, 'start'):
                service.start()
            elif hasattr(service, 'initialize'):
                service.initialize()
            
            # Update status
            status.status = 'running'
            status.last_health_check = datetime.now()
            
            self.logger.info(f"Service {service_name} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start service {service_name}: {e}")
            status = self.service_status[service_name]
            status.status = 'error'
            status.error_message = str(e)
            raise
    
    def stop_services(self):
        """Stop all services"""
        try:
            self.logger.info("Stopping all services...")
            
            # Stop monitoring threads
            self._stop_monitoring()
            
            # Stop services in reverse order
            service_stop_order = [
                'remote_access',
                'optimized_detection',
                'detection',
                'timezone_sync'
            ]
            
            for service_name in service_stop_order:
                if service_name in self.services:
                    self._stop_service(service_name)
            
            self.is_running = False
            
            self.logger.info("All services stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop services: {e}")
            raise
    
    def _stop_service(self, service_name: str):
        """Stop a specific service"""
        try:
            if service_name not in self.services:
                return
            
            service = self.services[service_name]
            status = self.service_status[service_name]
            
            self.logger.info(f"Stopping service: {service_name}")
            
            # Update status
            status.status = 'stopping'
            
            # Stop service based on type
            if hasattr(service, 'stop'):
                service.stop()
            elif hasattr(service, 'shutdown'):
                service.shutdown()
            
            # Update status
            status.status = 'stopped'
            status.stop_time = datetime.now()
            
            self.logger.info(f"Service {service_name} stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop service {service_name}: {e}")
            status = self.service_status[service_name]
            status.status = 'error'
            status.error_message = str(e)
    
    def _start_monitoring(self):
        """Start monitoring threads"""
        try:
            # Start health check thread
            self.monitor_thread = threading.Thread(
                target=self._health_check_loop,
                daemon=True,
                name="HealthCheckThread"
            )
            self.monitor_thread.start()
            
            # Start metrics collection thread
            self.metrics_thread = threading.Thread(
                target=self._metrics_collection_loop,
                daemon=True,
                name="MetricsCollectionThread"
            )
            self.metrics_thread.start()
            
            self.logger.info("Monitoring threads started")
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring threads: {e}")
            raise
    
    def _stop_monitoring(self):
        """Stop monitoring threads"""
        try:
            self.shutdown_event.set()
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
            
            if self.metrics_thread and self.metrics_thread.is_alive():
                self.metrics_thread.join(timeout=5)
            
            self.logger.info("Monitoring threads stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring threads: {e}")
    
    def _health_check_loop(self):
        """Health check loop for all services"""
        while not self.shutdown_event.is_set():
            try:
                for service_name, service in self.services.items():
                    self._check_service_health(service_name, service)
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                time.sleep(5)
    
    def _check_service_health(self, service_name: str, service):
        """Check health of a specific service"""
        try:
            status = self.service_status[service_name]
            
            # Update last health check time
            status.last_health_check = datetime.now()
            
            # Check if service is responding
            if hasattr(service, 'health_check'):
                is_healthy = service.health_check()
                if not is_healthy and status.status == 'running':
                    self.logger.warning(f"Service {service_name} health check failed")
                    self._handle_service_failure(service_name)
            
        except Exception as e:
            self.logger.error(f"Health check failed for service {service_name}: {e}")
            self._handle_service_failure(service_name)
    
    def _handle_service_failure(self, service_name: str):
        """Handle service failure"""
        try:
            status = self.service_status[service_name]
            
            if status.restart_count < self.max_restart_attempts:
                self.logger.info(f"Attempting to restart service {service_name}")
                
                # Stop service
                self._stop_service(service_name)
                
                # Wait before restart
                time.sleep(self.restart_delay)
                
                # Restart service
                self._start_service(service_name)
                
                # Update restart count
                status.restart_count += 1
                
            else:
                self.logger.error(f"Service {service_name} failed after {self.max_restart_attempts} restart attempts")
                status.status = 'error'
                status.error_message = f"Failed after {self.max_restart_attempts} restart attempts"
                
        except Exception as e:
            self.logger.error(f"Failed to handle service failure for {service_name}: {e}")
    
    def _metrics_collection_loop(self):
        """Metrics collection loop"""
        while not self.shutdown_event.is_set():
            try:
                for service_name, service in self.services.items():
                    self._collect_service_metrics(service_name, service)
                
                # Send metrics to server
                self._send_metrics_to_server()
                
                time.sleep(self.metrics_interval)
                
            except Exception as e:
                self.logger.error(f"Metrics collection loop error: {e}")
                time.sleep(10)
    
    def _collect_service_metrics(self, service_name: str, service):
        """Collect metrics for a specific service"""
        try:
            metrics = self.service_metrics[service_name]
            
            # Collect basic metrics
            metrics.last_updated = datetime.now()
            
            # Collect service-specific metrics if available
            if hasattr(service, 'get_metrics'):
                service_metrics = service.get_metrics()
                metrics.cpu_usage = service_metrics.get('cpu_usage', 0.0)
                metrics.memory_usage = service_metrics.get('memory_usage', 0.0)
                metrics.response_time = service_metrics.get('response_time', 0.0)
                metrics.request_count = service_metrics.get('request_count', 0)
                metrics.error_count = service_metrics.get('error_count', 0)
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics for service {service_name}: {e}")
    
    def _send_metrics_to_server(self):
        """Send metrics to server"""
        try:
            if not self.api_client:
                return
            
            # Prepare metrics data
            metrics_data = {
                'rvm_id': self.rvm_id,
                'timestamp': datetime.now().isoformat(),
                'services': {}
            }
            
            for service_name, metrics in self.service_metrics.items():
                metrics_data['services'][service_name] = asdict(metrics)
            
            # Send to server
            success, response = self.api_client.send_system_metrics(self.rvm_id, metrics_data)
            
            if success:
                self.logger.debug("Metrics sent to server successfully")
            else:
                self.logger.warning(f"Failed to send metrics to server: {response}")
                
        except Exception as e:
            self.logger.error(f"Failed to send metrics to server: {e}")
    
    def _handle_config_update(self, config: Dict[str, Any]):
        """Handle configuration update"""
        try:
            self.logger.info("Configuration update received")
            
            # Update services with new configuration
            for service_name, service in self.services.items():
                if hasattr(service, 'update_config'):
                    service.update_config(config)
                    self.logger.info(f"Updated configuration for service {service_name}")
            
            # Log configuration changes
            self.logger.info(f"Configuration updated: {list(config.keys())}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle configuration update: {e}")
    
    def _handle_websocket_message(self, message: Dict):
        """Handle WebSocket message"""
        try:
            message_type = message.get('type', 'unknown')
            
            if message_type == 'config_update':
                # Handle real-time configuration update
                config_data = message.get('data', {})
                self._handle_config_update(config_data)
                
            elif message_type == 'service_command':
                # Handle service commands
                command = message.get('command', '')
                service_name = message.get('service', '')
                
                if command == 'restart' and service_name in self.services:
                    self.logger.info(f"Restarting service {service_name} via WebSocket command")
                    self._stop_service(service_name)
                    time.sleep(2)
                    self._start_service(service_name)
                
            elif message_type == 'status_request':
                # Send status update
                self._send_status_update()
            
            self.logger.debug(f"WebSocket message handled: {message_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle WebSocket message: {e}")
    
    def _send_status_update(self):
        """Send status update via WebSocket"""
        try:
            if not self.api_client:
                return
            
            status_data = {
                'type': 'status_update',
                'rvm_id': self.rvm_id,
                'timestamp': datetime.now().isoformat(),
                'is_running': self.is_running,
                'services': {}
            }
            
            for service_name, status in self.service_status.items():
                status_data['services'][service_name] = asdict(status)
            
            self.api_client.send_websocket_message(status_data)
            
        except Exception as e:
            self.logger.error(f"Failed to send status update: {e}")
    
    def get_service_status(self, service_name: str = None) -> Dict:
        """Get service status"""
        if service_name:
            return asdict(self.service_status.get(service_name, ServiceStatus(name=service_name, status='not_found')))
        else:
            return {name: asdict(status) for name, status in self.service_status.items()}
    
    def get_service_metrics(self, service_name: str = None) -> Dict:
        """Get service metrics"""
        if service_name:
            return asdict(self.service_metrics.get(service_name, ServiceMetrics(service_name=service_name)))
        else:
            return {name: asdict(metrics) for name, metrics in self.service_metrics.items()}
    
    def get_integration_status(self) -> Dict:
        """Get overall integration status"""
        return {
            'rvm_id': self.rvm_id,
            'is_running': self.is_running,
            'is_initialized': self.is_initialized,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime': str(datetime.now() - self.start_time) if self.start_time else None,
            'services_count': len(self.services),
            'running_services': len([s for s in self.service_status.values() if s.status == 'running']),
            'error_services': len([s for s in self.service_status.values() if s.status == 'error']),
            'api_client_connected': self.api_client is not None,
            'config_manager_active': self.config_manager is not None
        }
    
    def shutdown(self):
        """Shutdown service integration"""
        try:
            self.logger.info("Shutting down service integration...")
            
            # Stop all services
            if self.is_running:
                self.stop_services()
            
            # Shutdown configuration manager
            if self.config_manager:
                self.config_manager.shutdown()
            
            # Shutdown API client
            if self.api_client:
                self.api_client.shutdown()
            
            self.logger.info("Service integration shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Service integration shutdown error: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test service integration
    integration = MyRVMServiceIntegration("jetson_orin_nano_001")
    
    try:
        # Start services
        integration.start_services()
        
        # Get status
        status = integration.get_integration_status()
        print(f"Integration Status: {status}")
        
        # Wait for a bit
        time.sleep(10)
        
        # Get service status
        service_status = integration.get_service_status()
        print(f"Service Status: {service_status}")
        
        # Get service metrics
        service_metrics = integration.get_service_metrics()
        print(f"Service Metrics: {service_metrics}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Shutdown
        integration.shutdown()
        print("Service integration test completed!")
