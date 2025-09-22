#!/usr/bin/env python3
"""
MyRVM Main Application
Production-ready application with full integration
"""

import os
import sys
import json
import time
import logging
import signal
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import traceback

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import all components
from config.enhanced_config_manager import EnhancedConfigurationManager
from api_client.enhanced_myrvm_api_client import EnhancedMyRVMAPIClient
from services.service_integration import MyRVMServiceIntegration
from gui.gui_client import GUIClient
from hardware.led_touch_screen_interface import LEDTouchScreenInterface
from user.user_profile_manager import UserProfileManager
from user.user_session_manager import UserSessionManager
from services.detection_service import DetectionService
# Import new Analisis 3 components
from monitoring.metrics_sender import MetricsSender
from monitoring.application_metrics_collector import ApplicationMetricsCollector
from remote.command_receiver import RemoteCommandReceiver

class MyRVMApplication:
    """Main MyRVM Application with full integration"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize MyRVM Application
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or 'config/production_config.json'
        self.is_running = False
        self.is_initialized = False
        
        # Application components
        self.config_manager = None
        self.api_client = None
        self.service_integration = None
        self.gui_client = None
        self.led_screen_interface = None
        self.user_profile_manager = None
        self.user_session_manager = None
        self.detection_service = None
        # New Analisis 3 components
        self.metrics_sender = None
        self.app_metrics_collector = None
        self.command_receiver = None
        
        # Application state
        self.startup_time = None
        self.services_status = {}
        self.health_status = {}
        
        # Threading
        self.monitor_thread = None
        self.shutdown_event = threading.Event()
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Initialize application
        self._initialize_application()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for main application"""
        logger = logging.getLogger('MyRVMApplication')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'myrvm_application_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.stop_application()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _initialize_application(self):
        """Initialize MyRVM Application"""
        try:
            self.logger.info("Initializing MyRVM Application...")
            
            # Load production configuration
            self._load_production_config()
            
            # Initialize components
            self._initialize_components()
            
            self.is_initialized = True
            self.logger.info("MyRVM Application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MyRVM Application: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _load_production_config(self):
        """Load production configuration"""
        try:
            self.logger.info("Loading production configuration...")
            
            # Create production config if not exists
            if not Path(self.config_path).exists():
                self._create_production_config()
            
            # Load configuration
            with open(self.config_path, 'r') as f:
                self.production_config = json.load(f)
            
            self.logger.info("Production configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load production configuration: {e}")
            raise
    
    def _create_production_config(self):
        """Create default production configuration"""
        try:
            config = {
                "application": {
                    "name": "MyRVM Application",
                    "version": "1.0.0",
                    "environment": "production",
                    "debug": False,
                    "log_level": "INFO"
                },
                "services": {
                    "config_manager": {"enabled": True, "priority": 1},
                    "api_client": {"enabled": True, "priority": 2},
                    "service_integration": {"enabled": True, "priority": 3},
                    "gui_client": {"enabled": True, "priority": 4, "port": 5001},
                    "led_screen_interface": {"enabled": True, "priority": 5},
                    "user_profile_manager": {"enabled": True, "priority": 6},
                    "detection_service": {"enabled": True, "priority": 7},
                    "metrics_sender": {"enabled": True, "priority": 8},
                    "command_receiver": {"enabled": True, "priority": 9}
                },
                "performance": {
                    "max_memory_usage": "80%",
                    "max_cpu_usage": "70%",
                    "monitoring_interval": 30,
                    "alert_thresholds": {
                        "memory": 85,
                        "cpu": 75,
                        "disk": 90
                    }
                },
                "backup": {
                    "enabled": True,
                    "interval": "daily",
                    "retention_days": 30,
                    "backup_path": "/backup/myrvm"
                },
                "remote_access": {
                    "server_url": "localhost:8000",
                    "api_key": "your_api_key_here",
                    "rvm_id": 1,
                    "metrics_interval": 60,
                    "command_timeout": 30
                }
            }
            
            # Create config directory
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info("Default production configuration created")
            
        except Exception as e:
            self.logger.error(f"Failed to create production configuration: {e}")
            raise
    
    def _initialize_components(self):
        """Initialize all application components"""
        try:
            self.logger.info("Initializing application components...")
            
            # Initialize Configuration Manager
            if self.production_config['services']['config_manager']['enabled']:
                self._initialize_config_manager()
            
            # Initialize API Client
            if self.production_config['services']['api_client']['enabled']:
                self._initialize_api_client()
            
            # Initialize Service Integration
            if self.production_config['services']['service_integration']['enabled']:
                self._initialize_service_integration()
            
            # Initialize User Profile Manager
            if self.production_config['services']['user_profile_manager']['enabled']:
                self._initialize_user_profile_manager()
            
            # Initialize User Session Manager
            if self.production_config['services']['user_profile_manager']['enabled']:
                self._initialize_user_session_manager()
            
            # Initialize LED Touch Screen Interface
            if self.production_config['services']['led_screen_interface']['enabled']:
                self._initialize_led_screen_interface()
            
            # Initialize GUI Client
            if self.production_config['services']['gui_client']['enabled']:
                self._initialize_gui_client()
            
            # Initialize Detection Service
            if self.production_config['services']['detection_service']['enabled']:
                self._initialize_detection_service()
            
            # Initialize Application Metrics Collector
            self._initialize_app_metrics_collector()
            
            # Initialize Metrics Sender
            if self.production_config['services']['metrics_sender']['enabled']:
                self._initialize_metrics_sender()
            
            # Initialize Remote Command Receiver
            if self.production_config['services']['command_receiver']['enabled']:
                self._initialize_command_receiver()
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _initialize_config_manager(self):
        """Initialize Configuration Manager"""
        try:
            self.logger.info("Initializing Configuration Manager...")
            # Get RVM ID from configuration
            rvm_id = self.production_config.get('remote_access', {}).get('rvm_id', 1)
            # Initialize with None API client first, will be updated later
            self.config_manager = EnhancedConfigurationManager(api_client=None, rvm_id=str(rvm_id))
            self.services_status['config_manager'] = 'initialized'
            self.logger.info("Configuration Manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Configuration Manager: {e}")
            raise
    
    def _initialize_api_client(self):
        """Initialize API Client"""
        try:
            self.logger.info("Initializing API Client...")
            self.api_client = EnhancedMyRVMAPIClient()
            self.services_status['api_client'] = 'initialized'
            self.logger.info("API Client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize API Client: {e}")
            raise
    
    def _initialize_service_integration(self):
        """Initialize Service Integration"""
        try:
            self.logger.info("Initializing Service Integration...")
            # Get RVM ID from configuration
            rvm_id = self.production_config.get('remote_access', {}).get('rvm_id', 1)
            self.service_integration = MyRVMServiceIntegration(
                rvm_id=str(rvm_id),
                config_dir="config"
            )
            self.services_status['service_integration'] = 'initialized'
            self.logger.info("Service Integration initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Service Integration: {e}")
            raise
    
    def _initialize_user_profile_manager(self):
        """Initialize User Profile Manager"""
        try:
            self.logger.info("Initializing User Profile Manager...")
            self.user_profile_manager = UserProfileManager(
                api_client=self.api_client
            )
            self.services_status['user_profile_manager'] = 'initialized'
            self.logger.info("User Profile Manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize User Profile Manager: {e}")
            raise
    
    def _initialize_user_session_manager(self):
        """Initialize User Session Manager"""
        try:
            self.logger.info("Initializing User Session Manager...")
            self.user_session_manager = UserSessionManager(
                user_profile_manager=self.user_profile_manager
            )
            self.services_status['user_session_manager'] = 'initialized'
            self.logger.info("User Session Manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize User Session Manager: {e}")
            raise
    
    def _initialize_led_screen_interface(self):
        """Initialize LED Touch Screen Interface"""
        try:
            self.logger.info("Initializing LED Touch Screen Interface...")
            self.led_screen_interface = LEDTouchScreenInterface()
            self.services_status['led_screen_interface'] = 'initialized'
            self.logger.info("LED Touch Screen Interface initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize LED Touch Screen Interface: {e}")
            raise
    
    def _initialize_gui_client(self):
        """Initialize GUI Client"""
        try:
            self.logger.info("Initializing GUI Client...")
            
            # Get GUI configuration
            gui_config = self.production_config['services']['gui_client']
            port = gui_config.get('port', 5001)
            
            # Get RVM ID from configuration
            rvm_id = self.production_config.get('remote_access', {}).get('rvm_id', 1)
            self.gui_client = GUIClient(
                rvm_id=str(rvm_id),
                host="0.0.0.0",
                port=port,
                api_client=self.api_client,
                service_integration=self.service_integration
            )
            self.services_status['gui_client'] = 'initialized'
            self.logger.info(f"GUI Client initialized on port {port}")
        except Exception as e:
            self.logger.error(f"Failed to initialize GUI Client: {e}")
            raise
    
    def _initialize_detection_service(self):
        """Initialize Detection Service"""
        try:
            self.logger.info("Initializing Detection Service...")
            self.detection_service = DetectionService()
            self.services_status['detection_service'] = 'initialized'
            self.logger.info("Detection Service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Detection Service: {e}")
            raise
    
    def _initialize_app_metrics_collector(self):
        """Initialize Application Metrics Collector"""
        try:
            self.logger.info("Initializing Application Metrics Collector...")
            self.app_metrics_collector = ApplicationMetricsCollector()
            self.services_status['app_metrics_collector'] = 'initialized'
            self.logger.info("Application Metrics Collector initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Application Metrics Collector: {e}")
            raise
    
    def _initialize_metrics_sender(self):
        """Initialize Metrics Sender"""
        try:
            self.logger.info("Initializing Metrics Sender...")
            
            # Get remote access configuration
            remote_config = self.production_config.get('remote_access', {})
            server_url = remote_config.get('server_url', 'localhost:8000')
            api_key = remote_config.get('api_key', 'your_api_key_here')
            rvm_id = remote_config.get('rvm_id', 1)
            
            self.metrics_sender = MetricsSender(server_url, rvm_id, api_key)
            self.services_status['metrics_sender'] = 'initialized'
            self.logger.info("Metrics Sender initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Metrics Sender: {e}")
            raise
    
    def _initialize_command_receiver(self):
        """Initialize Remote Command Receiver"""
        try:
            self.logger.info("Initializing Remote Command Receiver...")
            
            # Get remote access configuration
            remote_config = self.production_config.get('remote_access', {})
            server_url = remote_config.get('server_url', 'localhost:8000')
            api_key = remote_config.get('api_key', 'your_api_key_here')
            rvm_id = remote_config.get('rvm_id', 1)
            
            self.command_receiver = RemoteCommandReceiver(server_url, rvm_id, api_key)
            self.services_status['command_receiver'] = 'initialized'
            self.logger.info("Remote Command Receiver initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Remote Command Receiver: {e}")
            raise
    
    def start_application(self):
        """Start MyRVM Application"""
        try:
            if not self.is_initialized:
                raise RuntimeError("Application not initialized")
            
            if self.is_running:
                self.logger.warning("Application already running")
                return
            
            self.logger.info("Starting MyRVM Application...")
            self.startup_time = datetime.now()
            
            # Start components in priority order
            self._start_components()
            
            # Start monitoring thread
            self._start_monitoring()
            
            self.is_running = True
            self.logger.info("MyRVM Application started successfully")
            
            # Log startup information
            self._log_startup_info()
            
        except Exception as e:
            self.logger.error(f"Failed to start MyRVM Application: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _start_components(self):
        """Start all components in priority order"""
        try:
            # Sort services by priority
            services = sorted(
                self.production_config['services'].items(),
                key=lambda x: x[1].get('priority', 999)
            )
            
            for service_name, service_config in services:
                if not service_config.get('enabled', True):
                    continue
                
                self._start_component(service_name)
                
        except Exception as e:
            self.logger.error(f"Failed to start components: {e}")
            raise
    
    def _start_component(self, service_name: str):
        """Start individual component"""
        try:
            self.logger.info(f"Starting {service_name}...")
            
            if service_name == 'config_manager' and self.config_manager:
                # Configuration Manager is already initialized
                self.services_status[service_name] = 'running'
                
            elif service_name == 'api_client' and self.api_client:
                # API Client is already initialized
                self.services_status[service_name] = 'running'
                
            elif service_name == 'service_integration' and self.service_integration:
                self.service_integration.start_services()
                self.services_status[service_name] = 'running'
                
            elif service_name == 'user_profile_manager' and self.user_profile_manager:
                # User Profile Manager is already initialized
                self.services_status[service_name] = 'running'
                
            elif service_name == 'user_session_manager' and self.user_session_manager:
                # User Session Manager is already initialized
                self.services_status[service_name] = 'running'
                
            elif service_name == 'led_screen_interface' and self.led_screen_interface:
                self.led_screen_interface.start()
                self.services_status[service_name] = 'running'
                
            elif service_name == 'gui_client' and self.gui_client:
                # Start GUI client in separate thread
                gui_thread = threading.Thread(
                    target=self.gui_client.start,
                    daemon=True,
                    name="GUIClientThread"
                )
                gui_thread.start()
                self.services_status[service_name] = 'running'
                
            elif service_name == 'detection_service' and self.detection_service:
                # Detection Service is already initialized
                self.services_status[service_name] = 'running'
                
            elif service_name == 'metrics_sender' and self.metrics_sender:
                self.metrics_sender.start()
                self.services_status[service_name] = 'running'
                
            elif service_name == 'command_receiver' and self.command_receiver:
                self.command_receiver.start()
                self.services_status[service_name] = 'running'
            
            self.logger.info(f"{service_name} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start {service_name}: {e}")
            self.services_status[service_name] = 'error'
            raise
    
    def _start_monitoring(self):
        """Start monitoring thread"""
        try:
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="ApplicationMonitorThread"
            )
            self.monitor_thread.start()
            self.logger.info("Monitoring thread started")
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring thread: {e}")
    
    def _monitoring_loop(self):
        """Application monitoring loop"""
        while not self.shutdown_event.is_set():
            try:
                # Monitor application health
                self._monitor_health()
                
                # Update service status
                self._update_service_status()
                
                # Check performance
                self._check_performance()
                
                # Sleep for monitoring interval
                interval = self.production_config['performance'].get('monitoring_interval', 30)
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)
    
    def _monitor_health(self):
        """Monitor application health"""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update health status
            self.health_status = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': memory.available,
                'disk_usage': disk.percent,
                'disk_free': disk.free,
                'uptime': (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0
            }
            
            # Check alert thresholds
            self._check_alert_thresholds()
            
        except Exception as e:
            self.logger.error(f"Failed to monitor health: {e}")
    
    def _check_alert_thresholds(self):
        """Check performance alert thresholds"""
        try:
            thresholds = self.production_config['performance']['alert_thresholds']
            
            if self.health_status['cpu_usage'] > thresholds['cpu']:
                self.logger.warning(f"High CPU usage: {self.health_status['cpu_usage']}%")
            
            if self.health_status['memory_usage'] > thresholds['memory']:
                self.logger.warning(f"High memory usage: {self.health_status['memory_usage']}%")
            
            if self.health_status['disk_usage'] > thresholds['disk']:
                self.logger.warning(f"High disk usage: {self.health_status['disk_usage']}%")
                
        except Exception as e:
            self.logger.error(f"Failed to check alert thresholds: {e}")
    
    def _update_service_status(self):
        """Update service status"""
        try:
            # Check service status
            for service_name in self.services_status:
                if service_name == 'gui_client':
                    # GUI client runs in separate thread, check if thread is alive
                    for thread in threading.enumerate():
                        if thread.name == "GUIClientThread":
                            if not thread.is_alive():
                                self.services_status[service_name] = 'error'
                            break
                elif service_name == 'led_screen_interface' and self.led_screen_interface:
                    # Check LED screen interface status
                    status = self.led_screen_interface.get_status()
                    if status.is_running:
                        self.services_status[service_name] = 'running'
                    else:
                        self.services_status[service_name] = 'stopped'
                        
        except Exception as e:
            self.logger.error(f"Failed to update service status: {e}")
    
    def _check_performance(self):
        """Check application performance"""
        try:
            # Log performance metrics
            self.logger.debug(f"Performance: CPU {self.health_status.get('cpu_usage', 0)}%, "
                            f"Memory {self.health_status.get('memory_usage', 0)}%, "
                            f"Disk {self.health_status.get('disk_usage', 0)}%")
            
        except Exception as e:
            self.logger.error(f"Failed to check performance: {e}")
    
    def _log_startup_info(self):
        """Log startup information"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("MyRVM Application Startup Information")
            self.logger.info("=" * 60)
            self.logger.info(f"Application: {self.production_config['application']['name']}")
            self.logger.info(f"Version: {self.production_config['application']['version']}")
            self.logger.info(f"Environment: {self.production_config['application']['environment']}")
            self.logger.info(f"Startup Time: {self.startup_time}")
            self.logger.info(f"Services Status: {self.services_status}")
            
            # Log GUI access information
            gui_config = self.production_config['services']['gui_client']
            if gui_config.get('enabled', True):
                port = gui_config.get('port', 5001)
                self.logger.info(f"GUI Client: http://localhost:{port}")
                self.logger.info(f"LED Touch Screen: Access via browser at http://localhost:{port}")
            
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Failed to log startup info: {e}")
    
    def stop_application(self):
        """Stop MyRVM Application"""
        try:
            if not self.is_running:
                self.logger.warning("Application not running")
                return
            
            self.logger.info("Stopping MyRVM Application...")
            
            # Stop monitoring thread
            self._stop_monitoring()
            
            # Stop components in reverse priority order
            self._stop_components()
            
            self.is_running = False
            self.logger.info("MyRVM Application stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop MyRVM Application: {e}")
            self.logger.error(traceback.format_exc())
    
    def _stop_monitoring(self):
        """Stop monitoring thread"""
        try:
            self.shutdown_event.set()
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
            
            self.logger.info("Monitoring thread stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring thread: {e}")
    
    def _stop_components(self):
        """Stop all components"""
        try:
            # Stop components in reverse priority order
            services = sorted(
                self.production_config['services'].items(),
                key=lambda x: x[1].get('priority', 999),
                reverse=True
            )
            
            for service_name, service_config in services:
                if not service_config.get('enabled', True):
                    continue
                
                self._stop_component(service_name)
                
        except Exception as e:
            self.logger.error(f"Failed to stop components: {e}")
    
    def _stop_component(self, service_name: str):
        """Stop individual component"""
        try:
            self.logger.info(f"Stopping {service_name}...")
            
            if service_name == 'led_screen_interface' and self.led_screen_interface:
                self.led_screen_interface.stop()
                self.services_status[service_name] = 'stopped'
                
            elif service_name == 'service_integration' and self.service_integration:
                self.service_integration.stop_services()
                self.services_status[service_name] = 'stopped'
                
            elif service_name == 'user_profile_manager' and self.user_profile_manager:
                self.user_profile_manager.shutdown()
                self.services_status[service_name] = 'stopped'
                
            elif service_name == 'user_session_manager' and self.user_session_manager:
                self.user_session_manager.shutdown()
                self.services_status[service_name] = 'stopped'
                
            elif service_name == 'metrics_sender' and self.metrics_sender:
                self.metrics_sender.stop()
                self.services_status[service_name] = 'stopped'
                
            elif service_name == 'command_receiver' and self.command_receiver:
                self.command_receiver.stop()
                self.services_status[service_name] = 'stopped'
            
            self.logger.info(f"{service_name} stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop {service_name}: {e}")
            self.services_status[service_name] = 'error'
    
    def get_application_status(self) -> Dict:
        """Get application status"""
        return {
            'is_running': self.is_running,
            'is_initialized': self.is_initialized,
            'startup_time': self.startup_time.isoformat() if self.startup_time else None,
            'uptime': (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0,
            'services_status': self.services_status,
            'health_status': self.health_status,
            'production_config': self.production_config
        }
    
    def restart_application(self):
        """Restart MyRVM Application"""
        try:
            self.logger.info("Restarting MyRVM Application...")
            self.stop_application()
            time.sleep(2)
            self.start_application()
            self.logger.info("MyRVM Application restarted successfully")
        except Exception as e:
            self.logger.error(f"Failed to restart MyRVM Application: {e}")
            raise
    
    def increment_deposit_count(self):
        """Increment deposit count in metrics"""
        if self.app_metrics_collector:
            self.app_metrics_collector.increment_deposit_count()
    
    def increment_error_count(self):
        """Increment error count in metrics"""
        if self.app_metrics_collector:
            self.app_metrics_collector.increment_error_count()
    
    def increment_warning_count(self):
        """Increment warning count in metrics"""
        if self.app_metrics_collector:
            self.app_metrics_collector.increment_warning_count()
    
    def is_maintenance_mode(self) -> bool:
        """Check if system is in maintenance mode"""
        if self.command_receiver and self.command_receiver.command_executor:
            return self.command_receiver.command_executor.maintenance_mode
        return False

# Main application entry point
def main():
    """Main application entry point"""
    try:
        # Create and start application
        app = MyRVMApplication()
        app.start_application()
        
        # Keep application running
        try:
            while app.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            app.logger.info("Received keyboard interrupt, shutting down...")
        finally:
            app.stop_application()
            
    except Exception as e:
        print(f"Failed to start MyRVM Application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
