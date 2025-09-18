#!/usr/bin/env python3
"""
Monitoring Service for MyRVM Platform Integration
Real-time status monitoring and health checks
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "api-client"))

from myrvm_api_client import MyRVMAPIClient

class MonitoringService:
    """Real-time monitoring service for MyRVM Platform integration"""
    
    def __init__(self, config: Dict):
        """
        Initialize monitoring service
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.rvm_id = config.get('rvm_id', 1)
        self.monitoring_interval = config.get('monitoring_interval', 30.0)
        self.health_check_interval = config.get('health_check_interval', 60.0)
        
        # Initialize API client
        self.api_client = MyRVMAPIClient(
            base_url=config.get('myrvm_base_url'),
            use_tunnel=config.get('use_tunnel', False)
        )
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Monitoring state
        self.is_running = False
        self.monitoring_thread = None
        self.health_check_thread = None
        
        # Status data
        self.current_status = {
            'rvm_status': 'unknown',
            'processing_engines': [],
            'latest_detection': None,
            'detection_stats': {},
            'last_update': None,
            'connection_status': 'disconnected'
        }
        
        # Health metrics
        self.health_metrics = {
            'api_response_time': [],
            'connection_errors': 0,
            'last_successful_check': None,
            'uptime_start': None
        }
        
        # Alerts
        self.alerts = []
        self.alert_thresholds = {
            'max_response_time': 5.0,  # seconds
            'max_connection_errors': 5,
            'min_uptime': 300  # seconds
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for monitoring service"""
        logger = logging.getLogger('MonitoringService')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'monitoring_service_{now().strftime("%Y%m%d")}.log'
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
    
    def authenticate_with_platform(self) -> bool:
        """Authenticate with MyRVM Platform"""
        try:
            success, response = self.api_client.login(
                email='admin@myrvm.com',
                password='password'
            )
            
            if success:
                self.logger.info("Successfully authenticated with MyRVM Platform")
                return True
            else:
                self.logger.error(f"Authentication failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    def check_rvm_status(self) -> bool:
        """Check RVM status from platform"""
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
        try:
            start_time = time.time()
            
            success, response = self.api_client.get_rvm_status(self.rvm_id)
            
            response_time = time.time() - start_time
            self.health_metrics['api_response_time'].append(response_time)
            
            # Keep only last 10 response times
            if len(self.health_metrics['api_response_time']) > 10:
                self.health_metrics['api_response_time'] = self.health_metrics['api_response_time'][-10:]
            
            if success:
                self.current_status.update({
                    'rvm_status': response.get('data', {}).get('rvm', {}).get('status', 'unknown'),
                    'latest_detection': response.get('data', {}).get('latest_detection'),
                    'detection_stats': response.get('data', {}).get('detection_stats', {}),
                    'last_update': now().isoformat(),
                    'connection_status': 'connected'
                })
                
                self.health_metrics['last_successful_check'] = now()
                self.health_metrics['connection_errors'] = 0
                
                self.logger.info(f"RVM status updated: {self.current_status['rvm_status']}")
                return True
            else:
                self.logger.error(f"Failed to get RVM status: {response}")
                self.health_metrics['connection_errors'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"RVM status check error: {e}")
            self.health_metrics['connection_errors'] += 1
            return False
    
    def check_processing_engines(self) -> bool:
        """Check processing engines status"""
        try:
            success, response = self.api_client.get_processing_engines()
            
            if success:
                engines = response.get('data', {}).get('data', [])
                self.current_status['processing_engines'] = engines
                
                # Check for our Jetson Orin engine
                jetson_engines = [e for e in engines if 'jetson' in e.get('name', '').lower()]
                if jetson_engines:
                    self.logger.info(f"Found {len(jetson_engines)} Jetson processing engines")
                else:
                    self.logger.warning("No Jetson processing engines found")
                
                return True
            else:
                self.logger.error(f"Failed to get processing engines: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Processing engines check error: {e}")
            return False
    
    def check_health(self) -> Dict:
        """Perform health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': now().isoformat(),
            'metrics': {},
            'alerts': []
        }
        
        try:
            # Check API response time
            avg_response_time = sum(self.health_metrics['api_response_time']) / len(self.health_metrics['api_response_time']) if self.health_metrics['api_response_time'] else 0
            health_status['metrics']['avg_response_time'] = avg_response_time
            
            if avg_response_time > self.alert_thresholds['max_response_time']:
                health_status['alerts'].append({
                    'type': 'high_response_time',
                    'message': f"API response time is high: {avg_response_time:.2f}s",
                    'severity': 'warning'
                })
                health_status['status'] = 'degraded'
            
            # Check connection errors
            connection_errors = self.health_metrics['connection_errors']
            health_status['metrics']['connection_errors'] = connection_errors
            
            if connection_errors > self.alert_thresholds['max_connection_errors']:
                health_status['alerts'].append({
                    'type': 'connection_errors',
                    'message': f"Too many connection errors: {connection_errors}",
                    'severity': 'critical'
                })
                health_status['status'] = 'unhealthy'
            
            # Check uptime
            if self.health_metrics['uptime_start']:
                uptime = (now() - self.health_metrics['uptime_start']).total_seconds()
                health_status['metrics']['uptime_seconds'] = uptime
                
                if uptime < self.alert_thresholds['min_uptime']:
                    health_status['alerts'].append({
                        'type': 'low_uptime',
                        'message': f"Service uptime is low: {uptime:.0f}s",
                        'severity': 'info'
                    })
            
            # Check last successful check
            if self.health_metrics['last_successful_check']:
                time_since_success = (now() - self.health_metrics['last_successful_check']).total_seconds()
                health_status['metrics']['time_since_last_success'] = time_since_success
                
                if time_since_success > 300:  # 5 minutes
                    health_status['alerts'].append({
                        'type': 'stale_data',
                        'message': f"No successful checks for {time_since_success:.0f}s",
                        'severity': 'warning'
                    })
                    health_status['status'] = 'degraded'
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            return {
                'status': 'error',
                'timestamp': now().isoformat(),
                'error': str(e)
            }
    
    def monitoring_worker(self):
        """Main monitoring worker thread"""
        self.logger.info("Monitoring worker started")
        
        while self.is_running:
            try:
                # Check RVM status
                self.check_rvm_status()
                
                # Check processing engines
                self.check_processing_engines()
                
                # Wait for next check
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring worker error: {e}")
                time.sleep(5)
        
        self.logger.info("Monitoring worker stopped")
    
    def health_check_worker(self):
        """Health check worker thread"""
        self.logger.info("Health check worker started")
        
        while self.is_running:
            try:
                # Perform health check
                health_status = self.check_health()
                
                # Log health status
                if health_status['status'] != 'healthy':
                    self.logger.warning(f"Health status: {health_status['status']}")
                    for alert in health_status.get('alerts', []):
                        self.logger.warning(f"Alert: {alert['message']}")
                
                # Save health status
                self._save_health_status(health_status)
                
                # Wait for next health check
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Health check worker error: {e}")
                time.sleep(10)
        
        self.logger.info("Health check worker stopped")
    
    def _save_health_status(self, health_status: Dict):
        """Save health status to file"""
        try:
            log_dir = Path(__file__).parent.parent / 'logs'
            health_file = log_dir / f'health_status_{now().strftime("%Y%m%d")}.json'
            
            # Load existing data
            health_data = []
            if health_file.exists():
                with open(health_file, 'r') as f:
                    health_data = json.load(f)
            
            # Add new status
            health_data.append(health_status)
            
            # Keep only last 100 entries
            if len(health_data) > 100:
                health_data = health_data[-100:]
            
            # Save updated data
            with open(health_file, 'w') as f:
                json.dump(health_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save health status: {e}")
    
    def start(self) -> bool:
        """Start monitoring service"""
        try:
            # Authenticate with platform
            if not self.authenticate_with_platform():
                return False
            
            # Start service
            self.is_running = True
            self.health_metrics['uptime_start'] = now()
            
            # Start worker threads
            self.monitoring_thread = threading.Thread(target=self.monitoring_worker)
            self.health_check_thread = threading.Thread(target=self.health_check_worker)
            
            self.monitoring_thread.start()
            self.health_check_thread.start()
            
            self.logger.info("Monitoring service started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring service: {e}")
            return False
    
    def stop(self):
        """Stop monitoring service"""
        self.logger.info("Stopping monitoring service...")
        
        # Stop worker threads
        self.is_running = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        
        self.logger.info("Monitoring service stopped")
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'is_running': self.is_running,
            'current_status': self.current_status.copy(),
            'health_metrics': self.health_metrics.copy()
        }
    
    def get_health_status(self) -> Dict:
        """Get current health status"""
        return self.check_health()
    
    def trigger_processing(self) -> bool:
        """Trigger processing on RVM"""
        try:
            success, response = self.api_client.trigger_processing(self.rvm_id)
            
            if success:
                self.logger.info("Processing triggered successfully")
                return True
            else:
                self.logger.error(f"Failed to trigger processing: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Trigger processing error: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    # Load configuration
    config_path = Path(__file__).parent.parent / 'main' / 'config.json'
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {
            'rvm_id': 1,
            'monitoring_interval': 30.0,
            'health_check_interval': 60.0,
            'myrvm_base_url': 'http://172.28.233.83:8001',
            'use_tunnel': False
        }
    
    # Create and start monitoring service
    monitoring_service = MonitoringService(config)
    
    try:
        if monitoring_service.start():
            print("📊 Monitoring service started successfully!")
            print("Press Ctrl+C to stop...")
            
            # Monitor service
            while True:
                time.sleep(30)
                status = monitoring_service.get_status()
                health = monitoring_service.get_health_status()
                
                print(f"📊 Status: {status['current_status']['rvm_status']}, "
                      f"Health: {health['status']}, "
                      f"Connection: {status['current_status']['connection_status']}")
        else:
            print("❌ Failed to start monitoring service")
    
    except KeyboardInterrupt:
        print("\n⏹️  Stopping monitoring service...")
        monitoring_service.stop()
        print("✅ Monitoring service stopped")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        monitoring_service.stop()
