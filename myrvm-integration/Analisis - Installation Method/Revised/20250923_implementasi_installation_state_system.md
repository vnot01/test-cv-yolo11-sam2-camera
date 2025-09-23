# Implementasi Installation State System - Technical Specification

**Tanggal:** 2025-09-23  
**Versi:** 1.0.0  
**Status:** Technical Implementation Guide  
**Priority:** HIGH

## 📋 Overview

Dokumen ini berisi spesifikasi teknis lengkap untuk mengimplementasikan Installation State Detection System yang akan mengatasi gap kritis dalam lifecycle management RVM.

## 🏗️ System Architecture

### **1. Core Components**

```
┌─────────────────────────────────────────────────────────────┐
│                    Installation State System                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ State Manager   │  │ Service Manager │  │ Port Manager │ │
│  │                 │  │                 │  │              │ │
│  │ - State File    │  │ - Lifecycle     │  │ - Port Config│ │
│  │ - Validation    │  │ - Transitions   │  │ - Enable/    │ │
│  │ - Transitions   │  │ - Monitoring    │  │   Disable    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ API Integration │  │ Startup Script  │  │ Monitoring   │ │
│  │                 │  │                 │  │              │ │
│  │ - State Checks  │  │ - Auto Mode     │  │ - Logging    │ │
│  │ - Redirects     │  │ - Service Start │  │ - Alerts     │ │
│  │ - Validation    │  │ - Health Check  │  │ - Metrics    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### **2. File Structure**

```
/opt/myrvm/
├── installation/
│   ├── state.json                    # Installation state file
│   ├── state_manager.py              # State management class
│   ├── installation_log.json         # Installation log
│   └── backup/                       # State backups
├── config/
│   ├── ports.json                    # Port configuration
│   ├── services.json                 # Service configuration
│   └── lifecycle.json                # Lifecycle configuration
├── scripts/
│   ├── service_manager.py            # Service lifecycle management
│   ├── port_manager.py               # Port management
│   ├── startup.sh                    # System startup script
│   ├── check_installation_state.py   # State checker
│   └── transition_manager.py         # Transition management
└── logs/
    ├── installation.log              # Installation logs
    ├── service_transitions.log       # Service transition logs
    └── state_changes.log             # State change logs
```

## 🔧 Implementation Details

### **1. Installation State Manager**

#### **A. State File Structure**
```json
{
  "installation_status": "not_installed",
  "installation_date": null,
  "installation_version": "1.0.0",
  "hardware_detected": false,
  "network_configured": false,
  "ai_models_ready": false,
  "services_deployed": false,
  "last_check": "2025-09-23T10:30:00Z",
  "installation_steps": {
    "hardware_detection": false,
    "network_setup": false,
    "ai_models_setup": false,
    "service_deployment": false,
    "configuration_save": false
  },
  "error_log": [],
  "backup_enabled": true,
  "auto_cleanup": true
}
```

#### **B. State Manager Implementation**
```python
#!/usr/bin/env python3
"""
Installation State Manager
Manages RVM installation state and transitions
"""

import json
import os
import shutil
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
import logging

class InstallationState(Enum):
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    MAINTENANCE = "maintenance"

class InstallationStateManager:
    def __init__(self, state_file: str = "/opt/myrvm/installation/state.json"):
        self.state_file = state_file
        self.backup_dir = os.path.join(os.path.dirname(state_file), "backup")
        self.logger = self._setup_logger()
        self.ensure_state_file()
    
    def _setup_logger(self):
        """Setup logging for state manager"""
        logger = logging.getLogger('InstallationStateManager')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('/opt/myrvm/logs/state_changes.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def get_installation_state(self) -> InstallationState:
        """Get current installation state"""
        try:
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
            return InstallationState(state_data['installation_status'])
        except Exception as e:
            self.logger.error(f"Error reading state file: {e}")
            return InstallationState.NOT_INSTALLED
    
    def set_installation_state(self, state: InstallationState, **kwargs):
        """Set installation state with additional data"""
        try:
            # Backup current state
            self._backup_state()
            
            # Load current state
            current_state = self._load_state()
            
            # Update state
            current_state['installation_status'] = state.value
            current_state['last_check'] = datetime.now().isoformat()
            
            # Add additional data
            for key, value in kwargs.items():
                current_state[key] = value
            
            # Save state
            self._save_state(current_state)
            
            self.logger.info(f"Installation state changed to: {state.value}")
            
        except Exception as e:
            self.logger.error(f"Error setting installation state: {e}")
            raise
    
    def is_installation_complete(self) -> bool:
        """Check if installation is complete"""
        return self.get_installation_state() == InstallationState.INSTALLED
    
    def is_installation_required(self) -> bool:
        """Check if installation is required"""
        state = self.get_installation_state()
        return state in [InstallationState.NOT_INSTALLED, InstallationState.FAILED]
    
    def get_installation_progress(self) -> Dict[str, Any]:
        """Get installation progress details"""
        try:
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
            
            steps = state_data.get('installation_steps', {})
            completed_steps = sum(1 for step in steps.values() if step)
            total_steps = len(steps)
            
            return {
                'progress_percentage': (completed_steps / total_steps * 100) if total_steps > 0 else 0,
                'completed_steps': completed_steps,
                'total_steps': total_steps,
                'steps': steps,
                'current_state': state_data['installation_status']
            }
        except Exception as e:
            self.logger.error(f"Error getting installation progress: {e}")
            return {'progress_percentage': 0, 'completed_steps': 0, 'total_steps': 0}
    
    def update_installation_step(self, step: str, completed: bool):
        """Update specific installation step"""
        try:
            state_data = self._load_state()
            if 'installation_steps' not in state_data:
                state_data['installation_steps'] = {}
            
            state_data['installation_steps'][step] = completed
            state_data['last_check'] = datetime.now().isoformat()
            
            self._save_state(state_data)
            self.logger.info(f"Installation step '{step}' updated to: {completed}")
            
        except Exception as e:
            self.logger.error(f"Error updating installation step: {e}")
            raise
    
    def add_error_log(self, error: str, step: str = None):
        """Add error to installation log"""
        try:
            state_data = self._load_state()
            if 'error_log' not in state_data:
                state_data['error_log'] = []
            
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'error': error,
                'step': step,
                'state': state_data['installation_status']
            }
            
            state_data['error_log'].append(error_entry)
            state_data['last_check'] = datetime.now().isoformat()
            
            self._save_state(state_data)
            self.logger.error(f"Error logged: {error}")
            
        except Exception as e:
            self.logger.error(f"Error adding error log: {e}")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from file"""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_state()
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
            return self._create_default_state()
    
    def _save_state(self, state_data: Dict[str, Any]):
        """Save state to file"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")
            raise
    
    def _create_default_state(self) -> Dict[str, Any]:
        """Create default state"""
        return {
            "installation_status": "not_installed",
            "installation_date": None,
            "installation_version": "1.0.0",
            "hardware_detected": False,
            "network_configured": False,
            "ai_models_ready": False,
            "services_deployed": False,
            "last_check": datetime.now().isoformat(),
            "installation_steps": {
                "hardware_detection": False,
                "network_setup": False,
                "ai_models_setup": False,
                "service_deployment": False,
                "configuration_save": False
            },
            "error_log": [],
            "backup_enabled": True,
            "auto_cleanup": True
        }
    
    def _backup_state(self):
        """Backup current state"""
        try:
            if os.path.exists(self.state_file):
                os.makedirs(self.backup_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(self.backup_dir, f"state_backup_{timestamp}.json")
                shutil.copy2(self.state_file, backup_file)
                
                # Keep only last 10 backups
                self._cleanup_backups()
                
        except Exception as e:
            self.logger.error(f"Error backing up state: {e}")
    
    def _cleanup_backups(self):
        """Cleanup old backups"""
        try:
            if os.path.exists(self.backup_dir):
                backups = [f for f in os.listdir(self.backup_dir) if f.startswith('state_backup_')]
                backups.sort(reverse=True)
                
                # Keep only last 10 backups
                for backup in backups[10:]:
                    os.remove(os.path.join(self.backup_dir, backup))
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {e}")
    
    def ensure_state_file(self):
        """Ensure state file exists with default values"""
        if not os.path.exists(self.state_file):
            default_state = self._create_default_state()
            self._save_state(default_state)
            self.logger.info("Created default state file")
    
    def reset_installation_state(self):
        """Reset installation state (for re-installation)"""
        try:
            self._backup_state()
            default_state = self._create_default_state()
            self._save_state(default_state)
            self.logger.info("Installation state reset")
        except Exception as e:
            self.logger.error(f"Error resetting installation state: {e}")
            raise
```

### **2. Service Manager**

#### **A. Service Manager Implementation**
```python
#!/usr/bin/env python3
"""
Service Manager
Manages service lifecycle and port configuration
"""

import json
import subprocess
import psutil
import time
from typing import Dict, List, Optional
from installation.state_manager import InstallationStateManager, InstallationState
import logging

class ServiceManager:
    def __init__(self):
        self.state_manager = InstallationStateManager()
        self.ports_config = "/opt/myrvm/config/ports.json"
        self.services_config = "/opt/myrvm/config/services.json"
        self.logger = self._setup_logger()
        self.ensure_config_files()
    
    def _setup_logger(self):
        """Setup logging for service manager"""
        logger = logging.getLogger('ServiceManager')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('/opt/myrvm/logs/service_transitions.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def check_installation_state(self) -> bool:
        """Check if RVM is in installation mode"""
        return self.state_manager.is_installation_required()
    
    def start_installation_mode(self) -> bool:
        """Start installation mode (Port 8080)"""
        try:
            if self.check_installation_state():
                self.logger.info("Starting installation mode")
                
                # Enable installation port
                self.enable_port(8080, "installation_method")
                
                # Disable production ports
                self.disable_production_ports()
                
                # Start installation service
                self.start_service("installation_method")
                
                self.logger.info("Installation mode started successfully")
                return True
            else:
                self.logger.warning("Installation not required, already installed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting installation mode: {e}")
            return False
    
    def start_production_mode(self) -> bool:
        """Start production mode (Port 5000+)"""
        try:
            if self.state_manager.is_installation_complete():
                self.logger.info("Starting production mode")
                
                # Disable installation port
                self.disable_port(8080, "installation_method")
                
                # Enable production ports
                self.enable_production_ports()
                
                # Start production services
                self.start_production_services()
                
                self.logger.info("Production mode started successfully")
                return True
            else:
                self.logger.warning("Installation not complete, cannot start production mode")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting production mode: {e}")
            return False
    
    def enable_port(self, port: int, service: str) -> bool:
        """Enable specific port and service"""
        try:
            self.logger.info(f"Enabling port {port} for service {service}")
            
            # Update port configuration
            self._update_port_config(port, True, service)
            
            # Start service if not running
            if not self.is_service_running(service):
                self.start_service(service)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling port {port}: {e}")
            return False
    
    def disable_port(self, port: int, service: str) -> bool:
        """Disable specific port and service"""
        try:
            self.logger.info(f"Disabling port {port} for service {service}")
            
            # Stop service
            self.stop_service(service)
            
            # Update port configuration
            self._update_port_config(port, False, service)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling port {port}: {e}")
            return False
    
    def enable_production_ports(self) -> bool:
        """Enable all production ports"""
        try:
            production_ports = [5000, 5001, 5002]
            production_services = ["remote_access", "gui_client", "camera_service"]
            
            for port, service in zip(production_ports, production_services):
                self.enable_port(port, service)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling production ports: {e}")
            return False
    
    def disable_production_ports(self) -> bool:
        """Disable all production ports"""
        try:
            production_ports = [5000, 5001, 5002]
            production_services = ["remote_access", "gui_client", "camera_service"]
            
            for port, service in zip(production_ports, production_services):
                self.disable_port(port, service)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling production ports: {e}")
            return False
    
    def start_service(self, service: str) -> bool:
        """Start specific service"""
        try:
            service_config = self._get_service_config(service)
            if not service_config:
                self.logger.error(f"Service configuration not found: {service}")
                return False
            
            # Check if service is already running
            if self.is_service_running(service):
                self.logger.info(f"Service {service} is already running")
                return True
            
            # Start service
            cmd = service_config.get('start_command')
            if cmd:
                subprocess.Popen(cmd, shell=True)
                time.sleep(2)  # Wait for service to start
                
                if self.is_service_running(service):
                    self.logger.info(f"Service {service} started successfully")
                    return True
                else:
                    self.logger.error(f"Service {service} failed to start")
                    return False
            else:
                self.logger.error(f"No start command configured for service: {service}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting service {service}: {e}")
            return False
    
    def stop_service(self, service: str) -> bool:
        """Stop specific service"""
        try:
            service_config = self._get_service_config(service)
            if not service_config:
                self.logger.error(f"Service configuration not found: {service}")
                return False
            
            # Check if service is running
            if not self.is_service_running(service):
                self.logger.info(f"Service {service} is not running")
                return True
            
            # Stop service
            cmd = service_config.get('stop_command')
            if cmd:
                subprocess.run(cmd, shell=True)
                time.sleep(2)  # Wait for service to stop
                
                if not self.is_service_running(service):
                    self.logger.info(f"Service {service} stopped successfully")
                    return True
                else:
                    self.logger.error(f"Service {service} failed to stop")
                    return False
            else:
                self.logger.error(f"No stop command configured for service: {service}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error stopping service {service}: {e}")
            return False
    
    def is_service_running(self, service: str) -> bool:
        """Check if service is running"""
        try:
            service_config = self._get_service_config(service)
            if not service_config:
                return False
            
            # Check by port
            port = service_config.get('port')
            if port:
                return self.is_port_in_use(port)
            
            # Check by process name
            process_name = service_config.get('process_name')
            if process_name:
                for proc in psutil.process_iter(['pid', 'name']):
                    if process_name in proc.info['name']:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking service status {service}: {e}")
            return False
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if port is in use"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking port {port}: {e}")
            return False
    
    def start_production_services(self) -> bool:
        """Start all production services"""
        try:
            production_services = ["remote_access", "gui_client", "camera_service"]
            
            for service in production_services:
                self.start_service(service)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting production services: {e}")
            return False
    
    def _update_port_config(self, port: int, enabled: bool, service: str):
        """Update port configuration"""
        try:
            config = self._load_ports_config()
            
            if 'ports' not in config:
                config['ports'] = {}
            
            config['ports'][str(port)] = {
                'enabled': enabled,
                'service': service,
                'last_updated': time.time()
            }
            
            self._save_ports_config(config)
            
        except Exception as e:
            self.logger.error(f"Error updating port config: {e}")
    
    def _load_ports_config(self) -> Dict:
        """Load ports configuration"""
        try:
            with open(self.ports_config, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_ports_config()
        except Exception as e:
            self.logger.error(f"Error loading ports config: {e}")
            return self._create_default_ports_config()
    
    def _save_ports_config(self, config: Dict):
        """Save ports configuration"""
        try:
            os.makedirs(os.path.dirname(self.ports_config), exist_ok=True)
            with open(self.ports_config, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving ports config: {e}")
    
    def _create_default_ports_config(self) -> Dict:
        """Create default ports configuration"""
        return {
            "ports": {
                "8080": {
                    "enabled": True,
                    "service": "installation_method",
                    "auto_disable": True
                },
                "5000": {
                    "enabled": False,
                    "service": "remote_access",
                    "auto_disable": False
                },
                "5001": {
                    "enabled": False,
                    "service": "gui_client",
                    "auto_disable": False
                },
                "5002": {
                    "enabled": False,
                    "service": "camera_service",
                    "auto_disable": False
                }
            }
        }
    
    def _get_service_config(self, service: str) -> Optional[Dict]:
        """Get service configuration"""
        try:
            with open(self.services_config, 'r') as f:
                config = json.load(f)
            return config.get('services', {}).get(service)
        except Exception as e:
            self.logger.error(f"Error getting service config: {e}")
            return None
    
    def ensure_config_files(self):
        """Ensure configuration files exist"""
        try:
            # Ensure ports config
            if not os.path.exists(self.ports_config):
                default_config = self._create_default_ports_config()
                self._save_ports_config(default_config)
            
            # Ensure services config
            if not os.path.exists(self.services_config):
                self._create_default_services_config()
                
        except Exception as e:
            self.logger.error(f"Error ensuring config files: {e}")
    
    def _create_default_services_config(self):
        """Create default services configuration"""
        default_config = {
            "services": {
                "installation_method": {
                    "port": 8080,
                    "process_name": "python3",
                    "start_command": "cd /opt/myrvm/installation_method && python3 app.py",
                    "stop_command": "pkill -f 'python3.*app.py'",
                    "auto_start": True
                },
                "remote_access": {
                    "port": 5000,
                    "process_name": "python3",
                    "start_command": "cd /opt/myrvm/services && python3 remote_access.py",
                    "stop_command": "pkill -f 'python3.*remote_access.py'",
                    "auto_start": False
                },
                "gui_client": {
                    "port": 5001,
                    "process_name": "python3",
                    "start_command": "cd /opt/myrvm/services && python3 gui_client.py",
                    "stop_command": "pkill -f 'python3.*gui_client.py'",
                    "auto_start": False
                },
                "camera_service": {
                    "port": 5002,
                    "process_name": "python3",
                    "start_command": "cd /opt/myrvm/services && python3 camera_service.py",
                    "stop_command": "pkill -f 'python3.*camera_service.py'",
                    "auto_start": False
                }
            }
        }
        
        try:
            os.makedirs(os.path.dirname(self.services_config), exist_ok=True)
            with open(self.services_config, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error creating services config: {e}")
```

### **3. Startup Script**

#### **A. System Startup Script**
```bash
#!/bin/bash
# File: /opt/myrvm/scripts/startup.sh

# RVM System Startup Script
# Automatically determines installation state and starts appropriate services

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/opt/myrvm/logs/startup.log"
PID_FILE="/opt/myrvm/startup.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} $message"
            ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Check if already running
check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "WARN" "Startup script already running (PID: $pid)"
            exit 1
        else
            rm -f "$PID_FILE"
        fi
    fi
}

# Create PID file
create_pid_file() {
    echo $$ > "$PID_FILE"
}

# Cleanup function
cleanup() {
    log "INFO" "Cleaning up..."
    rm -f "$PID_FILE"
    exit 0
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Check installation state
check_installation_state() {
    log "INFO" "Checking installation state..."
    
    # Run Python script to check state
    local state_output=$(python3 "$SCRIPT_DIR/check_installation_state.py" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log "INFO" "Installation state: INSTALLED"
        echo "INSTALLATION_STATE=installed"
        return 0
    elif [ $exit_code -eq 1 ]; then
        log "INFO" "Installation state: NOT_INSTALLED"
        echo "INSTALLATION_STATE=not_installed"
        return 1
    else
        log "ERROR" "Error checking installation state: $state_output"
        return 2
    fi
}

# Start installation mode
start_installation_mode() {
    log "INFO" "Starting installation mode..."
    
    # Start installation service
    python3 "$SCRIPT_DIR/service_manager.py" --mode=installation
    
    if [ $? -eq 0 ]; then
        log "INFO" "Installation mode started successfully"
        log "INFO" "Installation GUI available at: http://localhost:8080"
        return 0
    else
        log "ERROR" "Failed to start installation mode"
        return 1
    fi
}

# Start production mode
start_production_mode() {
    log "INFO" "Starting production mode..."
    
    # Start production services
    python3 "$SCRIPT_DIR/service_manager.py" --mode=production
    
    if [ $? -eq 0 ]; then
        log "INFO" "Production mode started successfully"
        log "INFO" "Remote Access available at: http://localhost:5000"
        log "INFO" "GUI Client available at: http://localhost:5001"
        log "INFO" "Camera Service available at: http://localhost:5002"
        return 0
    else
        log "ERROR" "Failed to start production mode"
        return 1
    fi
}

# Main startup logic
main() {
    log "INFO" "Starting RVM System..."
    log "INFO" "Script version: 1.0.0"
    log "INFO" "Project directory: $PROJECT_DIR"
    
    # Check if already running
    check_running
    
    # Create PID file
    create_pid_file
    
    # Check installation state
    local installation_state=$(check_installation_state)
    local state_result=$?
    
    if [ $state_result -eq 0 ]; then
        # Installation complete, start production mode
        start_production_mode
    elif [ $state_result -eq 1 ]; then
        # Installation required, start installation mode
        start_installation_mode
    else
        # Error checking state
        log "ERROR" "Cannot determine installation state, exiting"
        exit 1
    fi
    
    log "INFO" "RVM System startup completed"
}

# Run main function
main "$@"
```

#### **B. Installation State Checker**
```python
#!/usr/bin/env python3
"""
Installation State Checker
Checks RVM installation state and returns appropriate exit code
"""

import sys
import os
sys.path.append('/opt/myrvm')

from installation.state_manager import InstallationStateManager, InstallationState

def main():
    try:
        state_manager = InstallationStateManager()
        state = state_manager.get_installation_state()
        
        print(f"INSTALLATION_STATE={state.value}")
        
        if state == InstallationState.INSTALLED:
            print("RVM is installed, starting production mode")
            sys.exit(0)  # Production mode
        else:
            print(f"RVM installation state: {state.value}")
            sys.exit(1)  # Installation mode required
    
    except Exception as e:
        print(f"Error checking installation state: {e}")
        sys.exit(2)  # Error

if __name__ == "__main__":
    main()
```

## 📊 Testing Strategy

### **1. Unit Tests**

#### **A. State Manager Tests**
```python
#!/usr/bin/env python3
"""
Unit tests for Installation State Manager
"""

import unittest
import tempfile
import os
import json
from installation.state_manager import InstallationStateManager, InstallationState

class TestInstallationStateManager(unittest.TestCase):
    def setUp(self):
        # Create temporary state file
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "state.json")
        self.state_manager = InstallationStateManager(self.state_file)
    
    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initial_state(self):
        """Test initial state is NOT_INSTALLED"""
        state = self.state_manager.get_installation_state()
        self.assertEqual(state, InstallationState.NOT_INSTALLED)
    
    def test_set_installation_state(self):
        """Test setting installation state"""
        self.state_manager.set_installation_state(InstallationState.INSTALLING)
        state = self.state_manager.get_installation_state()
        self.assertEqual(state, InstallationState.INSTALLING)
    
    def test_installation_complete(self):
        """Test installation complete check"""
        self.state_manager.set_installation_state(InstallationState.INSTALLED)
        self.assertTrue(self.state_manager.is_installation_complete())
    
    def test_installation_required(self):
        """Test installation required check"""
        self.state_manager.set_installation_state(InstallationState.NOT_INSTALLED)
        self.assertTrue(self.state_manager.is_installation_required())
    
    def test_installation_progress(self):
        """Test installation progress tracking"""
        progress = self.state_manager.get_installation_progress()
        self.assertIn('progress_percentage', progress)
        self.assertIn('completed_steps', progress)
        self.assertIn('total_steps', progress)
    
    def test_update_installation_step(self):
        """Test updating installation step"""
        self.state_manager.update_installation_step('hardware_detection', True)
        progress = self.state_manager.get_installation_progress()
        self.assertTrue(progress['steps']['hardware_detection'])
    
    def test_error_logging(self):
        """Test error logging"""
        self.state_manager.add_error_log("Test error", "test_step")
        
        # Load state and check error log
        with open(self.state_file, 'r') as f:
            state_data = json.load(f)
        
        self.assertEqual(len(state_data['error_log']), 1)
        self.assertEqual(state_data['error_log'][0]['error'], "Test error")

if __name__ == '__main__':
    unittest.main()
```

### **2. Integration Tests**

#### **A. Service Manager Tests**
```python
#!/usr/bin/env python3
"""
Integration tests for Service Manager
"""

import unittest
import tempfile
import os
from scripts.service_manager import ServiceManager
from installation.state_manager import InstallationStateManager, InstallationState

class TestServiceManager(unittest.TestCase):
    def setUp(self):
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "state.json")
        self.ports_config = os.path.join(self.temp_dir, "ports.json")
        self.services_config = os.path.join(self.temp_dir, "services.json")
        
        # Create service manager with temporary configs
        self.service_manager = ServiceManager()
        self.service_manager.state_manager = InstallationStateManager(self.state_file)
        self.service_manager.ports_config = self.ports_config
        self.service_manager.services_config = self.services_config
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_installation_state_check(self):
        """Test installation state checking"""
        # Set state to not installed
        self.service_manager.state_manager.set_installation_state(InstallationState.NOT_INSTALLED)
        self.assertTrue(self.service_manager.check_installation_state())
        
        # Set state to installed
        self.service_manager.state_manager.set_installation_state(InstallationState.INSTALLED)
        self.assertFalse(self.service_manager.check_installation_state())
    
    def test_port_config_creation(self):
        """Test port configuration creation"""
        self.service_manager.ensure_config_files()
        self.assertTrue(os.path.exists(self.ports_config))
        self.assertTrue(os.path.exists(self.services_config))
    
    def test_port_enable_disable(self):
        """Test port enable/disable functionality"""
        self.service_manager.ensure_config_files()
        
        # Test enabling port
        result = self.service_manager.enable_port(8080, "test_service")
        self.assertTrue(result)
        
        # Test disabling port
        result = self.service_manager.disable_port(8080, "test_service")
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
```

## 🚀 Deployment Guide

### **1. Installation Steps**

#### **A. File Deployment**
```bash
#!/bin/bash
# File: deploy_installation_state_system.sh

# Create directories
sudo mkdir -p /opt/myrvm/installation
sudo mkdir -p /opt/myrvm/config
sudo mkdir -p /opt/myrvm/scripts
sudo mkdir -p /opt/myrvm/logs

# Copy files
sudo cp installation/state_manager.py /opt/myrvm/installation/
sudo cp scripts/service_manager.py /opt/myrvm/scripts/
sudo cp scripts/startup.sh /opt/myrvm/scripts/
sudo cp scripts/check_installation_state.py /opt/myrvm/scripts/

# Set permissions
sudo chmod +x /opt/myrvm/scripts/*.sh
sudo chmod +x /opt/myrvm/scripts/*.py

# Create systemd service
sudo cp systemd/myrvm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable myrvm.service
```

#### **B. Systemd Service**
```ini
# File: /etc/systemd/system/myrvm.service
[Unit]
Description=RVM System Service
After=network.target

[Service]
Type=forking
ExecStart=/opt/myrvm/scripts/startup.sh
ExecStop=/opt/myrvm/scripts/stop.sh
Restart=always
RestartSec=10
User=root
Group=root

[Install]
WantedBy=multi-user.target
```

### **2. Configuration**

#### **A. Environment Variables**
```bash
# File: /opt/myrvm/config/environment.conf
export MYRVM_STATE_FILE="/opt/myrvm/installation/state.json"
export MYRVM_PORTS_CONFIG="/opt/myrvm/config/ports.json"
export MYRVM_SERVICES_CONFIG="/opt/myrvm/config/services.json"
export MYRVM_LOG_DIR="/opt/myrvm/logs"
export MYRVM_BACKUP_DIR="/opt/myrvm/installation/backup"
```

#### **B. Log Rotation**
```bash
# File: /etc/logrotate.d/myrvm
/opt/myrvm/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
```

## 📋 Conclusion

Implementasi Installation State Detection System akan mengatasi gap kritis dalam lifecycle management RVM dengan:

1. **Proper State Management** - Deteksi otomatis status instalasi
2. **Service Lifecycle** - Transisi otomatis dari installation ke production
3. **Port Management** - Pengelolaan port yang proper
4. **Security** - Disable installation APIs setelah setup
5. **Resource Optimization** - Penggunaan resource yang efisien

**Rekomendasi: Implementasi segera dimulai untuk mengatasi gap kritis ini.**

---

**Last Updated:** 2025-09-23  
**Next Review:** 2025-09-30  
**Priority:** HIGH  
**Status:** Ready for Implementation
