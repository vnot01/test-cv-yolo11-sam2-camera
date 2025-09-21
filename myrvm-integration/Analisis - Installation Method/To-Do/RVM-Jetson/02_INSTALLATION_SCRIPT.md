# TASK 02: INSTALLATION SCRIPT

**Tanggal**: 2025-09-21  
**Versi**: 1.0.0  
**Status**: 📋 PLANNING  
**Priority**: HIGH  

---

## **🎯 OBJECTIVE**

Membuat Installation Script yang dapat dijalankan oleh teknisi untuk setup port forwarding, start web GUI service, dan auto-open browser di laptop teknisi.

---

## **📋 REQUIREMENTS**

### **Functional Requirements:**
- **SSH Port Forwarding** setup
- **Web GUI Service** startup
- **Auto-open Browser** di laptop teknisi
- **Installation Status** monitoring
- **Error Handling** dan recovery
- **Logging** dan debugging
- **Configuration Backup** sebelum changes

### **Technical Requirements:**
- **Bash script** untuk Linux compatibility
- **Python virtual environment** setup
- **Service management** (systemd)
- **Port management** dan conflict detection
- **Browser detection** dan auto-open
- **Network connectivity** testing

---

## **🔧 IMPLEMENTATION PLAN**

### **1. Script Structure**
```
install.sh                 # Main installation script
├── setup_port_forwarding()    # SSH port forwarding setup
├── start_web_gui()            # Web GUI service startup
├── auto_open_browser()        # Browser auto-open
├── monitor_installation()     # Installation monitoring
├── handle_errors()            # Error handling
└── cleanup()                  # Cleanup on exit
```

### **2. Core Functions Implementation**

#### **A. Port Forwarding Setup**
```bash
setup_port_forwarding() {
    # Check if port 8080 is available
    # Setup SSH port forwarding
    # Test port forwarding
    # Display connection instructions
}
```

#### **B. Web GUI Service Startup**
```bash
start_web_gui() {
    # Activate virtual environment
    # Install dependencies
    # Start Flask application
    # Monitor service status
}
```

#### **C. Browser Auto-Open**
```bash
auto_open_browser() {
    # Detect default browser
    # Open localhost:8080/install
    # Handle browser detection errors
    # Provide manual instructions
}
```

#### **D. Installation Monitoring**
```bash
monitor_installation() {
    # Monitor web GUI status
    # Monitor port forwarding
    # Monitor installation progress
    # Display status updates
}
```

---

## **📝 SCRIPT IMPLEMENTATION**

### **1. Main Installation Script (`install.sh`)**
```bash
#!/bin/bash

# INSTALLATION SCRIPT FOR MYRVM CONFIGURATION GUI
# This script sets up port forwarding and starts web GUI

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
WEB_GUI_PORT=8080
WEB_GUI_HOST="0.0.0.0"
INSTALLATION_LOG="/tmp/myrvm_installation_$(date +%Y%m%d_%H%M%S).log"

# Logging
exec > >(tee -a $INSTALLATION_LOG)
exec 2>&1

print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

print_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if running on Jetson
    if [ ! -f /etc/nv_tegra_release ]; then
        print_warning "This script is designed for Jetson devices"
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "main_application.py" ]; then
        print_error "Please run this script from the myrvm-integration directory"
        exit 1
    fi
    
    print_status "Prerequisites check completed"
}

# Function to setup virtual environment
setup_virtual_environment() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    
    # Install required packages
    pip install flask flask-socketio requests psutil
    
    print_status "Virtual environment setup completed"
}

# Function to check port availability
check_port_availability() {
    print_status "Checking port availability..."
    
    if netstat -tuln | grep -q ":$WEB_GUI_PORT "; then
        print_warning "Port $WEB_GUI_PORT is already in use"
        print_info "Attempting to find alternative port..."
        
        for port in 8081 8082 8083 8084 8085; do
            if ! netstat -tuln | grep -q ":$port "; then
                WEB_GUI_PORT=$port
                print_status "Using alternative port: $WEB_GUI_PORT"
                break
            fi
        done
        
        if [ $WEB_GUI_PORT -eq 8080 ]; then
            print_error "No available ports found"
            exit 1
        fi
    else
        print_status "Port $WEB_GUI_PORT is available"
    fi
}

# Function to start web GUI service
start_web_gui() {
    print_status "Starting web GUI service..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Create web GUI startup script
    cat > start_web_gui.py << EOF
#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_config_gui.app import app, socketio
import threading
import time

def run_web_gui():
    try:
        print(f"Starting MyRVM Configuration GUI on port $WEB_GUI_PORT...")
        socketio.run(app, host='$WEB_GUI_HOST', port=$WEB_GUI_PORT, debug=False)
    except Exception as e:
        print(f"Error starting web GUI: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_web_gui()
EOF
    
    chmod +x start_web_gui.py
    
    # Start web GUI in background
    nohup python3 start_web_gui.py > /tmp/web_gui.log 2>&1 &
    WEB_GUI_PID=$!
    
    # Wait for service to start
    sleep 5
    
    # Check if service is running
    if ps -p $WEB_GUI_PID > /dev/null; then
        print_status "Web GUI service started successfully (PID: $WEB_GUI_PID)"
        echo $WEB_GUI_PID > /tmp/web_gui.pid
    else
        print_error "Failed to start web GUI service"
        exit 1
    fi
}

# Function to setup port forwarding instructions
setup_port_forwarding_instructions() {
    print_status "Setting up port forwarding instructions..."
    
    # Get current IP
    CURRENT_IP=$(hostname -I | awk '{print $1}')
    
    cat > /tmp/port_forwarding_instructions.txt << EOF
========================================
  MyRVM Configuration GUI Setup
========================================

Web GUI is running on: http://localhost:$WEB_GUI_PORT/install

To access from your laptop:

1. Open terminal on your laptop
2. Run SSH port forwarding:
   ssh -L $WEB_GUI_PORT:localhost:$WEB_GUI_PORT my@$CURRENT_IP

3. Open browser and go to:
   http://localhost:$WEB_GUI_PORT/install

Alternative access methods:
- Direct access: http://$CURRENT_IP:$WEB_GUI_PORT/install
- SSH tunnel: ssh -L $WEB_GUI_PORT:localhost:$WEB_GUI_PORT my@$CURRENT_IP

Service Status:
- Web GUI PID: $WEB_GUI_PID
- Port: $WEB_GUI_PORT
- Log: /tmp/web_gui.log

========================================
EOF
    
    print_info "Port forwarding instructions saved to: /tmp/port_forwarding_instructions.txt"
    cat /tmp/port_forwarding_instructions.txt
}

# Function to auto-open browser (if possible)
auto_open_browser() {
    print_status "Attempting to auto-open browser..."
    
    # Check if we're in a desktop environment
    if [ -n "$DISPLAY" ] && command -v xdg-open &> /dev/null; then
        print_info "Opening browser automatically..."
        xdg-open "http://localhost:$WEB_GUI_PORT/install" &
        print_status "Browser opened successfully"
    else
        print_warning "Cannot auto-open browser (no desktop environment)"
        print_info "Please manually open browser and go to: http://localhost:$WEB_GUI_PORT/install"
    fi
}

# Function to monitor installation
monitor_installation() {
    print_status "Monitoring installation..."
    
    # Monitor web GUI service
    while true; do
        if [ -f /tmp/web_gui.pid ]; then
            PID=$(cat /tmp/web_gui.pid)
            if ! ps -p $PID > /dev/null; then
                print_error "Web GUI service stopped unexpectedly"
                break
            fi
        else
            print_error "Web GUI PID file not found"
            break
        fi
        
        # Check port status
        if netstat -tuln | grep -q ":$WEB_GUI_PORT "; then
            print_status "Web GUI is running on port $WEB_GUI_PORT"
        else
            print_error "Port $WEB_GUI_PORT is not listening"
            break
        fi
        
        sleep 10
    done
}

# Function to handle cleanup
cleanup() {
    print_status "Cleaning up..."
    
    if [ -f /tmp/web_gui.pid ]; then
        PID=$(cat /tmp/web_gui.pid)
        if ps -p $PID > /dev/null; then
            kill $PID
            print_status "Web GUI service stopped"
        fi
        rm -f /tmp/web_gui.pid
    fi
    
    print_status "Cleanup completed"
}

# Function to display help
display_help() {
    cat << EOF
MyRVM Configuration GUI Installation Script

Usage: $0 [OPTIONS]

Options:
    -h, --help          Show this help message
    -p, --port PORT     Specify port for web GUI (default: 8080)
    -H, --host HOST     Specify host for web GUI (default: 0.0.0.0)
    -v, --verbose       Enable verbose output
    --no-browser        Don't attempt to auto-open browser
    --monitor           Monitor installation after setup

Examples:
    $0                  # Default installation
    $0 -p 8081          # Use port 8081
    $0 --no-browser     # Don't auto-open browser
    $0 --monitor        # Monitor after setup

EOF
}

# Main installation function
main() {
    print_status "Starting MyRVM Configuration GUI installation"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                display_help
                exit 0
                ;;
            -p|--port)
                WEB_GUI_PORT="$2"
                shift 2
                ;;
            -H|--host)
                WEB_GUI_HOST="$2"
                shift 2
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            --no-browser)
                NO_BROWSER=true
                shift
                ;;
            --monitor)
                MONITOR=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                display_help
                exit 1
                ;;
        esac
    done
    
    # Set up signal handlers
    trap cleanup EXIT INT TERM
    
    # Run installation steps
    check_prerequisites
    setup_virtual_environment
    check_port_availability
    start_web_gui
    setup_port_forwarding_instructions
    
    if [ "$NO_BROWSER" != "true" ]; then
        auto_open_browser
    fi
    
    print_status "Installation completed successfully!"
    print_info "Web GUI is accessible at: http://localhost:$WEB_GUI_PORT/install"
    
    if [ "$MONITOR" = "true" ]; then
        monitor_installation
    else
        print_info "Press Ctrl+C to stop the web GUI service"
        wait
    fi
}

# Run main function
main "$@"
```

---

## **🔧 SUPPORTING SCRIPTS**

### **1. Web GUI Startup Script (`start_web_gui.py`)**
```python
#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_config_gui.app import app, socketio
import threading
import time

def run_web_gui():
    try:
        print("Starting MyRVM Configuration GUI...")
        socketio.run(app, host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        print(f"Error starting web GUI: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_web_gui()
```

### **2. Service Management Script (`manage_service.sh`)**
```bash
#!/bin/bash

# Service management script for MyRVM Configuration GUI

case "$1" in
    start)
        ./install.sh --no-browser
        ;;
    stop)
        if [ -f /tmp/web_gui.pid ]; then
            PID=$(cat /tmp/web_gui.pid)
            kill $PID
            rm -f /tmp/web_gui.pid
            echo "Web GUI service stopped"
        else
            echo "Web GUI service is not running"
        fi
        ;;
    status)
        if [ -f /tmp/web_gui.pid ]; then
            PID=$(cat /tmp/web_gui.pid)
            if ps -p $PID > /dev/null; then
                echo "Web GUI service is running (PID: $PID)"
            else
                echo "Web GUI service is not running"
            fi
        else
            echo "Web GUI service is not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
```

---

## **🧪 TESTING STRATEGY**

### **Unit Testing:**
- **Port availability** checking
- **Service startup** testing
- **Browser detection** testing
- **Error handling** testing

### **Integration Testing:**
- **End-to-end** installation testing
- **Port forwarding** testing
- **Web GUI** accessibility testing
- **Service monitoring** testing

### **User Acceptance Testing:**
- **Technician workflow** testing
- **Error recovery** testing
- **Performance** testing
- **Usability** testing

---

## **📊 SUCCESS CRITERIA**

### **Functional Success:**
- ✅ SSH port forwarding setup
- ✅ Web GUI service startup
- ✅ Browser auto-open functionality
- ✅ Installation status monitoring
- ✅ Error handling and recovery
- ✅ Service management

### **Technical Success:**
- ✅ Port conflict detection
- ✅ Service monitoring
- ✅ Logging and debugging
- ✅ Cleanup on exit
- ✅ Signal handling

### **User Experience Success:**
- ✅ Clear status messages
- ✅ Helpful error messages
- ✅ Easy service management
- ✅ Comprehensive logging

---

## **⏱️ ESTIMATED TIMELINE**

### **Week 1: Core Script Development**
- **Day 1-2**: Main installation script
- **Day 3-4**: Port forwarding setup
- **Day 5**: Service management

### **Week 2: Integration & Testing**
- **Day 1-2**: Web GUI integration
- **Day 3-4**: Browser auto-open
- **Day 5**: Testing dan debugging

### **Week 3: Monitoring & Error Handling**
- **Day 1-2**: Installation monitoring
- **Day 3-4**: Error handling
- **Day 5**: Integration testing

### **Week 4: Documentation & Deployment**
- **Day 1-2**: Documentation
- **Day 3-4**: User guide
- **Day 5**: Final testing

---

## **📁 DELIVERABLES**

### **Script Files:**
- `install.sh`
- `start_web_gui.py`
- `manage_service.sh`

### **Documentation:**
- Installation guide
- User manual
- Troubleshooting guide
- API documentation

### **Testing:**
- Unit tests
- Integration tests
- User acceptance tests
- Performance tests

---

**Status**: 📋 **READY FOR IMPLEMENTATION**  
**Estimated Time**: 4 weeks  
**Difficulty**: Intermediate  
**Dependencies**: Web Configuration Interface, Hardware Detection, Network Management
