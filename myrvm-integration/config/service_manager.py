#!/usr/bin/env python3
"""
Service Manager for MyRVM Platform Integration
Production-ready service management and systemd integration
"""

import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import psutil

class ServiceManager:
    """Production-ready service management system"""
    
    def __init__(self, config: Dict):
        """
        Initialize service manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.service_name = 'myrvm-integration'
        self.service_user = os.getenv('USER', 'jetson')
        self.service_group = os.getenv('USER', 'jetson')
        
        # Service directories
        self.service_dir = Path(__file__).parent.parent
        self.systemd_dir = Path('/etc/systemd/system')
        self.service_file = self.systemd_dir / f'{self.service_name}.service'
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Service configuration
        self.service_config = self._get_service_config()
        
        self.logger.info("Service manager initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for service manager"""
        logger = logging.getLogger('ServiceManager')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if not exists
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'service_manager_{now().strftime("%Y%m%d")}.log'
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
    
    def _get_service_config(self) -> Dict:
        """Get service configuration"""
        return {
            'service_name': self.service_name,
            'service_user': self.service_user,
            'service_group': self.service_group,
            'working_directory': str(self.service_dir),
            'python_executable': sys.executable,
            'main_script': str(self.service_dir / 'main' / 'enhanced_jetson_main.py'),
            'config_file': str(self.service_dir / 'main' / 'config.json'),
            'log_file': str(self.service_dir / 'logs' / f'{self.service_name}.log'),
            'pid_file': f'/var/run/{self.service_name}.pid',
            'restart_policy': 'always',
            'restart_sec': 5,
            'timeout_start_sec': 30,
            'timeout_stop_sec': 30
        }
    
    def create_systemd_service(self) -> bool:
        """Create systemd service file"""
        try:
            service_content = self._generate_systemd_service_content()
            
            # Write service file
            with open(self.service_file, 'w') as f:
                f.write(service_content)
            
            # Set proper permissions
            os.chmod(self.service_file, 0o644)
            
            self.logger.info(f"Systemd service file created: {self.service_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create systemd service: {e}")
            return False
    
    def _generate_systemd_service_content(self) -> str:
        """Generate systemd service file content"""
        config = self.service_config
        
        service_content = f"""[Unit]
Description=MyRVM Platform Integration Service
Documentation=https://github.com/vnot01/test-cv-yolo11-sam2-camera
After=network.target network-online.target
Wants=network-online.target
StartLimitInterval=60
StartLimitBurst=3

[Service]
Type=simple
User={config['service_user']}
Group={config['service_group']}
WorkingDirectory={config['working_directory']}
ExecStart={config['python_executable']} {config['main_script']} --config {config['config_file']}
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill -TERM $MAINPID
PIDFile={config['pid_file']}
Restart={config['restart_policy']}
RestartSec={config['restart_sec']}
TimeoutStartSec={config['timeout_start_sec']}
TimeoutStopSec={config['timeout_stop_sec']}
StandardOutput=append:{config['log_file']}
StandardError=append:{config['log_file']}
Environment=PYTHONPATH={config['working_directory']}
Environment=MYRVM_ENVIRONMENT=production

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={config['working_directory']} /tmp /var/run

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
"""
        return service_content
    
    def install_service(self) -> bool:
        """Install systemd service"""
        try:
            # Create service file
            if not self.create_systemd_service():
                return False
            
            # Reload systemd
            result = subprocess.run(['sudo', 'systemctl', 'daemon-reload'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to reload systemd: {result.stderr}")
                return False
            
            # Enable service
            result = subprocess.run(['sudo', 'systemctl', 'enable', self.service_name], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to enable service: {result.stderr}")
                return False
            
            self.logger.info(f"Service {self.service_name} installed and enabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install service: {e}")
            return False
    
    def uninstall_service(self) -> bool:
        """Uninstall systemd service"""
        try:
            # Stop service if running
            self.stop_service()
            
            # Disable service
            result = subprocess.run(['sudo', 'systemctl', 'disable', self.service_name], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.warning(f"Failed to disable service: {result.stderr}")
            
            # Remove service file
            if self.service_file.exists():
                self.service_file.unlink()
                self.logger.info(f"Service file removed: {self.service_file}")
            
            # Reload systemd
            result = subprocess.run(['sudo', 'systemctl', 'daemon-reload'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.warning(f"Failed to reload systemd: {result.stderr}")
            
            self.logger.info(f"Service {self.service_name} uninstalled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall service: {e}")
            return False
    
    def start_service(self) -> bool:
        """Start systemd service"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'start', self.service_name], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to start service: {result.stderr}")
                return False
            
            # Wait for service to start
            time.sleep(2)
            
            if self.is_service_running():
                self.logger.info(f"Service {self.service_name} started successfully")
                return True
            else:
                self.logger.error(f"Service {self.service_name} failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop systemd service"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'stop', self.service_name], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to stop service: {result.stderr}")
                return False
            
            # Wait for service to stop
            time.sleep(2)
            
            if not self.is_service_running():
                self.logger.info(f"Service {self.service_name} stopped successfully")
                return True
            else:
                self.logger.warning(f"Service {self.service_name} may still be running")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to stop service: {e}")
            return False
    
    def restart_service(self) -> bool:
        """Restart systemd service"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'restart', self.service_name], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to restart service: {result.stderr}")
                return False
            
            # Wait for service to restart
            time.sleep(3)
            
            if self.is_service_running():
                self.logger.info(f"Service {self.service_name} restarted successfully")
                return True
            else:
                self.logger.error(f"Service {self.service_name} failed to restart")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to restart service: {e}")
            return False
    
    def reload_service(self) -> bool:
        """Reload systemd service"""
        try:
            result = subprocess.run(['sudo', 'systemctl', 'reload', self.service_name], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Failed to reload service: {result.stderr}")
                return False
            
            self.logger.info(f"Service {self.service_name} reloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reload service: {e}")
            return False
    
    def is_service_running(self) -> bool:
        """Check if service is running"""
        try:
            result = subprocess.run(['systemctl', 'is-active', self.service_name], 
                                  capture_output=True, text=True)
            return result.stdout.strip() == 'active'
        except Exception as e:
            self.logger.error(f"Failed to check service status: {e}")
            return False
    
    def get_service_status(self) -> Dict:
        """Get detailed service status"""
        try:
            # Get systemd status
            result = subprocess.run(['systemctl', 'show', self.service_name, '--no-pager'], 
                                  capture_output=True, text=True)
            
            status = {}
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        status[key] = value
            
            # Get process information
            process_info = self._get_process_info()
            
            return {
                'service_name': self.service_name,
                'systemd_status': status,
                'process_info': process_info,
                'is_running': self.is_service_running(),
                'service_file_exists': self.service_file.exists(),
                'timestamp': now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get service status: {e}")
            return {}
    
    def _get_process_info(self) -> Dict:
        """Get process information"""
        try:
            # Find process by name
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
                try:
                    if proc.info['name'] == 'python3' and proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'enhanced_jetson_main.py' in cmdline:
                            return {
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': cmdline,
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_info': proc.info['memory_info']._asdict() if proc.info['memory_info'] else {}
                            }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get process info: {e}")
            return {}
    
    def get_service_logs(self, lines: int = 100) -> List[str]:
        """Get service logs"""
        try:
            result = subprocess.run(['journalctl', '-u', self.service_name, '-n', str(lines), '--no-pager'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout.split('\n')
            else:
                self.logger.error(f"Failed to get service logs: {result.stderr}")
                return []
                
        except Exception as e:
            self.logger.error(f"Failed to get service logs: {e}")
            return []
    
    def create_health_check_endpoint(self) -> bool:
        """Create health check endpoint"""
        try:
            health_check_script = self.service_dir / 'scripts' / 'health_check.py'
            health_check_script.parent.mkdir(exist_ok=True)
            
            health_check_content = '''#!/usr/bin/env python3
"""
Health Check Endpoint for MyRVM Platform Integration
"""

import sys
import json
from pathlib import Path

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "main"))

def health_check():
    """Perform health check"""
    try:
        # Import main service
        from enhanced_jetson_main import EnhancedJetsonMain
from utils.timezone_manager import get_timezone_manager, now, format_datetime, utc_now
        
        # Check if service is running
        # This is a simplified check - in production, you'd want more comprehensive checks
        
        return {
            'status': 'healthy',
            'timestamp': now().isoformat(),
            'service': 'myrvm-integration'
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': now().isoformat(),
            'service': 'myrvm-integration'
        }

if __name__ == "__main__":
    result = health_check()
    print(json.dumps(result))
    sys.exit(0 if result['status'] == 'healthy' else 1)
'''
            
            with open(health_check_script, 'w') as f:
                f.write(health_check_content)
            
            # Make executable
            health_check_script.chmod(0o755)
            
            self.logger.info(f"Health check endpoint created: {health_check_script}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create health check endpoint: {e}")
            return False
    
    def get_service_report(self) -> str:
        """Generate service report"""
        try:
            status = self.get_service_status()
            logs = self.get_service_logs(10)
            
            report = f"""
Service Manager Report
=====================
Service Name: {status.get('service_name', 'N/A')}
Service File: {self.service_file}
Service File Exists: {status.get('service_file_exists', False)}
Is Running: {status.get('is_running', False)}

Systemd Status:
- Active State: {status.get('systemd_status', {}).get('ActiveState', 'N/A')}
- Sub State: {status.get('systemd_status', {}).get('SubState', 'N/A')}
- Load State: {status.get('systemd_status', {}).get('LoadState', 'N/A')}

Process Information:
"""
            
            process_info = status.get('process_info', {})
            if process_info:
                report += f"- PID: {process_info.get('pid', 'N/A')}\n"
                report += f"- CPU Percent: {process_info.get('cpu_percent', 'N/A')}%\n"
                memory_info = process_info.get('memory_info', {})
                if memory_info:
                    report += f"- Memory RSS: {memory_info.get('rss', 0) / 1024 / 1024:.1f}MB\n"
            else:
                report += "- No process information available\n"
            
            report += f"\nRecent Logs ({len(logs)} lines):\n"
            for log_line in logs[-5:]:  # Show last 5 lines
                if log_line.strip():
                    report += f"- {log_line}\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate service report: {e}")
            return f"Error generating service report: {e}"
