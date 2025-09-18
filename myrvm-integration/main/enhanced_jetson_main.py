#!/usr/bin/env python3
"""
Enhanced Jetson Main Coordinator
Real-time integration with MyRVM Platform
"""

import json
import time
import logging
import signal
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "services"))
sys.path.append(str(Path(__file__).parent.parent / "api-client"))

from camera_service import CameraService
from monitoring_service import MonitoringService
from detection_service import DetectionService
from myrvm_api_client import MyRVMAPIClient

class EnhancedJetsonMain:
    """Enhanced main coordinator with real-time MyRVM Platform integration"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize enhanced Jetson main coordinator
        
        Args:
            config_file: Configuration file path
        """
        self.config_file = config_file
        self.config = self._load_config()
        
        # Initialize services
        self.camera_service = None
        self.monitoring_service = None
        self.detection_service = None
        self.api_client = None
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Service management
        self.services = {}
        self.is_running = False
        
        # Statistics
        self.stats = {
            'start_time': None,
            'services_started': 0,
            'services_failed': 0,
            'total_errors': 0
        }
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
        config_path = Path(__file__).parent / self.config_file
        
        if not config_path.exists():
            self.logger.error(f"Configuration file not found: {config_path}")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Add default values
            config.setdefault('monitoring_interval', 30.0)
            config.setdefault('health_check_interval', 60.0)
            config.setdefault('max_processing_queue', 10)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for enhanced main coordinator"""
        logger = logging.getLogger('EnhancedJetsonMain')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'enhanced_jetson_main_{now().strftime("%Y%m%d")}.log'
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
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def initialize_services(self) -> bool:
        """Initialize all services"""
        try:
            self.logger.info("Initializing services...")
            
            # Initialize API client
            self.api_client = MyRVMAPIClient(
                base_url=self.config.get('myrvm_base_url'),
                use_tunnel=self.config.get('use_tunnel', False)
            )
            self.services['api_client'] = self.api_client
            
            # Initialize detection service
            self.detection_service = DetectionService(
                models_dir=self.config.get('models_dir', '../models')
            )
            self.services['detection_service'] = self.detection_service
            
            # Initialize camera service
            self.camera_service = CameraService(self.config)
            self.services['camera_service'] = self.camera_service
            
            # Initialize monitoring service
            self.monitoring_service = MonitoringService(self.config)
            self.services['monitoring_service'] = self.monitoring_service
            
            self.logger.info("All services initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            return False
    
    def start_services(self) -> bool:
        """Start all services"""
        try:
            self.logger.info("Starting services...")
            
            # Start monitoring service first
            if self.monitoring_service.start():
                self.logger.info("✅ Monitoring service started")
                self.stats['services_started'] += 1
            else:
                self.logger.error("❌ Failed to start monitoring service")
                self.stats['services_failed'] += 1
            
            # Start camera service
            if self.camera_service.start():
                self.logger.info("✅ Camera service started")
                self.stats['services_started'] += 1
            else:
                self.logger.error("❌ Failed to start camera service")
                self.stats['services_failed'] += 1
            
            # Check if all critical services started
            if self.stats['services_started'] >= 2:
                self.logger.info("✅ All critical services started successfully")
                return True
            else:
                self.logger.error("❌ Failed to start critical services")
                return False
                
        except Exception as e:
            self.logger.error(f"Service startup failed: {e}")
            return False
    
    def stop_services(self):
        """Stop all services"""
        self.logger.info("Stopping services...")
        
        # Stop camera service
        if self.camera_service:
            self.camera_service.stop()
            self.logger.info("✅ Camera service stopped")
        
        # Stop monitoring service
        if self.monitoring_service:
            self.monitoring_service.stop()
            self.logger.info("✅ Monitoring service stopped")
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        status = {
            'timestamp': now().isoformat(),
            'is_running': self.is_running,
            'uptime_seconds': 0,
            'services': {},
            'stats': self.stats.copy()
        }
        
        # Calculate uptime
        if self.stats['start_time']:
            status['uptime_seconds'] = (now() - self.stats['start_time']).total_seconds()
        
        # Get service statuses
        if self.camera_service:
            status['services']['camera'] = self.camera_service.get_status()
        
        if self.monitoring_service:
            status['services']['monitoring'] = self.monitoring_service.get_status()
        
        return status
    
    def get_health_status(self) -> Dict:
        """Get system health status"""
        health = {
            'timestamp': now().isoformat(),
            'overall_status': 'healthy',
            'services': {},
            'alerts': []
        }
        
        try:
            # Get monitoring service health
            if self.monitoring_service:
                monitoring_health = self.monitoring_service.get_health_status()
                health['services']['monitoring'] = monitoring_health
                
                if monitoring_health['status'] != 'healthy':
                    health['alerts'].extend(monitoring_health.get('alerts', []))
                    if monitoring_health['status'] == 'unhealthy':
                        health['overall_status'] = 'unhealthy'
                    elif health['overall_status'] == 'healthy':
                        health['overall_status'] = 'degraded'
            
            # Get camera service statistics
            if self.camera_service:
                camera_stats = self.camera_service.get_statistics()
                health['services']['camera'] = {
                    'status': 'healthy' if camera_stats['errors'] == 0 else 'degraded',
                    'stats': camera_stats
                }
                
                if camera_stats['errors'] > 10:
                    health['alerts'].append({
                        'type': 'camera_errors',
                        'message': f"Camera service has {camera_stats['errors']} errors",
                        'severity': 'warning'
                    })
                    if health['overall_status'] == 'healthy':
                        health['overall_status'] = 'degraded'
            
            return health
            
        except Exception as e:
            self.logger.error(f"Health status check failed: {e}")
            return {
                'timestamp': now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def save_status_report(self):
        """Save status report to file"""
        try:
            log_dir = Path(__file__).parent.parent / 'logs'
            status_file = log_dir / f'system_status_{now().strftime("%Y%m%d_%H%M%S")}.json'
            
            report = {
                'system_status': self.get_system_status(),
                'health_status': self.get_health_status(),
                'timestamp': now().isoformat()
            }
            
            with open(status_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Status report saved to: {status_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save status report: {e}")
    
    def run(self):
        """Main run loop"""
        try:
            self.logger.info("🚀 Starting Enhanced Jetson Main Coordinator")
            self.stats['start_time'] = now()
            
            # Initialize services
            if not self.initialize_services():
                self.logger.error("❌ Service initialization failed")
                return False
            
            # Start services
            if not self.start_services():
                self.logger.error("❌ Service startup failed")
                return False
            
            # Main service is running
            self.is_running = True
            self.logger.info("✅ Enhanced Jetson Main Coordinator started successfully")
            
            # Main monitoring loop
            last_status_report = time.time()
            status_report_interval = 300  # 5 minutes
            
            while self.is_running:
                try:
                    # Save status report periodically
                    current_time = time.time()
                    if current_time - last_status_report >= status_report_interval:
                        self.save_status_report()
                        last_status_report = current_time
                    
                    # Log system status every minute
                    time.sleep(60)
                    
                    # Get and log current status
                    system_status = self.get_system_status()
                    health_status = self.get_health_status()
                    
                    self.logger.info(f"📊 System Status: {health_status['overall_status']}, "
                                   f"Uptime: {system_status['uptime_seconds']:.0f}s, "
                                   f"Services: {self.stats['services_started']}/{self.stats['services_started'] + self.stats['services_failed']}")
                    
                    # Log any alerts
                    for alert in health_status.get('alerts', []):
                        self.logger.warning(f"⚠️  Alert: {alert['message']}")
                    
                except KeyboardInterrupt:
                    self.logger.info("Received keyboard interrupt")
                    break
                except Exception as e:
                    self.logger.error(f"Main loop error: {e}")
                    self.stats['total_errors'] += 1
                    time.sleep(5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Main run loop failed: {e}")
            return False
        finally:
            self.stop()
    
    def stop(self):
        """Stop the enhanced main coordinator"""
        self.logger.info("🛑 Stopping Enhanced Jetson Main Coordinator...")
        
        self.is_running = False
        
        # Stop all services
        self.stop_services()
        
        # Save final status report
        self.save_status_report()
        
        # Log final statistics
        uptime = 0
        if self.stats['start_time']:
            uptime = (now() - self.stats['start_time']).total_seconds()
        
        self.logger.info(f"📊 Final Statistics:")
        self.logger.info(f"   Uptime: {uptime:.0f} seconds")
        self.logger.info(f"   Services Started: {self.stats['services_started']}")
        self.logger.info(f"   Services Failed: {self.stats['services_failed']}")
        self.logger.info(f"   Total Errors: {self.stats['total_errors']}")
        
        self.logger.info("✅ Enhanced Jetson Main Coordinator stopped")

# Example usage and testing
if __name__ == "__main__":
    # Create enhanced main coordinator
    enhanced_main = EnhancedJetsonMain()
    
    try:
        # Run the coordinator
        success = enhanced_main.run()
        
        if success:
            print("🎉 Enhanced Jetson Main Coordinator completed successfully")
        else:
            print("❌ Enhanced Jetson Main Coordinator failed")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⏹️  Enhanced Jetson Main Coordinator interrupted by user")
        enhanced_main.stop()
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        enhanced_main.stop()
        sys.exit(1)
