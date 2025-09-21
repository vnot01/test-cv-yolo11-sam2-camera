#!/bin/bash

# INSTALLATION SCRIPT FOR RVM LOCATION A
# This script automates the installation process for MyRVM Integration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RVM_ID=5
LOCATION_NAME="Location A"
SERVER_URL="http://172.28.233.83:8001"
API_KEY="your_api_key_here"
REPO_URL="https://github.com/vnot01/test-cv-yolo11-sam2-camera.git"

# Logging
LOG_FILE="/tmp/myrvm_installation_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a $LOG_FILE)
exec 2>&1

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MyRVM Integration Installation Script${NC}"
echo -e "${BLUE}  Location: $LOCATION_NAME${NC}"
echo -e "${BLUE}  RVM ID: $RVM_ID${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check if running on Jetson
    if [ ! -f /etc/nv_tegra_release ]; then
        print_warning "This script is designed for Jetson devices. Continue anyway? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_error "Installation cancelled"
            exit 1
        fi
    fi
    
    # Check Python version
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python version: $PYTHON_VERSION"
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Git
    if command_exists git; then
        print_status "Git is available"
    else
        print_error "Git is not installed"
        exit 1
    fi
    
    # Check network connectivity
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        print_status "Network connectivity: OK"
    else
        print_error "No network connectivity"
        exit 1
    fi
    
    print_status "System requirements check completed"
}

# Function to install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y \
        chromium-browser \
        xdotool \
        unclutter \
        curl \
        wget \
        nano \
        htop \
        tree
    
    print_status "System dependencies installed"
}

# Function to clone repository
clone_repository() {
    print_status "Cloning MyRVM Integration repository..."
    
    cd /home/my
    
    if [ -d "test-cv-yolo11-sam2-camera" ]; then
        print_warning "Repository already exists. Updating..."
        cd test-cv-yolo11-sam2-camera
        git pull origin main
    else
        git clone $REPO_URL
        cd test-cv-yolo11-sam2-camera
    fi
    
    cd myrvm-integration
    print_status "Repository cloned/updated successfully"
}

# Function to setup virtual environment
setup_virtual_environment() {
    print_status "Setting up virtual environment..."
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install basic dependencies
    pip install \
        requests \
        flask \
        opencv-python \
        numpy \
        psutil \
        websockets \
        aiohttp
    
    print_status "Virtual environment setup completed"
}

# Function to configure RVM
configure_rvm() {
    print_status "Configuring RVM for $LOCATION_NAME..."
    
    # Backup existing config
    if [ -f "config/production_config.json" ]; then
        cp config/production_config.json config/production_config.json.backup
        print_status "Backed up existing configuration"
    fi
    
    # Create new configuration
    cat > config/production_config.json << EOF
{
  "application": {
    "name": "MyRVM Application - $LOCATION_NAME",
    "version": "1.0.0",
    "environment": "production",
    "debug": false,
    "log_level": "INFO"
  },
  "services": {
    "config_manager": {"enabled": true, "priority": 1},
    "api_client": {"enabled": true, "priority": 2},
    "service_integration": {"enabled": true, "priority": 3},
    "gui_client": {"enabled": true, "priority": 4, "port": 5001},
    "led_screen_interface": {"enabled": true, "priority": 5},
    "user_profile_manager": {"enabled": true, "priority": 6},
    "detection_service": {"enabled": true, "priority": 7},
    "metrics_sender": {"enabled": true, "priority": 8},
    "command_receiver": {"enabled": true, "priority": 9}
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
    "enabled": true,
    "interval": "daily",
    "retention_days": 30,
    "backup_path": "/backup/myrvm"
  },
  "security": {
    "encrypt_credentials": true,
    "require_https": false,
    "access_control": true
  },
  "logging": {
    "structured_logging": true,
    "log_rotation": true,
    "max_log_size_mb": 10,
    "backup_count": 10
  },
  "remote_access": {
    "server_url": "$SERVER_URL",
    "api_key": "$API_KEY",
    "rvm_id": $RVM_ID,
    "metrics_interval": 30,
    "command_timeout": 30
  },
  "service": {
    "auto_start": true,
    "restart_policy": "always",
    "restart_sec": 3,
    "timeout_start_sec": 20,
    "timeout_stop_sec": 20
  },
  "monitoring_interval": 15.0,
  "health_check_interval": 30.0,
  "capture_interval": 3.0,
  "batch_size": 6,
  "max_processing_queue": 15,
  "max_memory_mb": 2048,
  "memory_threshold": 0.7
}
EOF
    
    print_status "RVM configuration completed"
}

# Function to test hardware
test_hardware() {
    print_status "Testing hardware components..."
    
    # Test camera
    if python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera FAIL'); cap.release()" 2>/dev/null; then
        print_status "Camera: OK"
    else
        print_warning "Camera: Not detected or not working"
    fi
    
    # Test display
    if command_exists xrandr; then
        DISPLAY_COUNT=$(xrandr --listmonitors | grep -c "Monitors:")
        print_status "Display: $DISPLAY_COUNT monitor(s) detected"
    else
        print_warning "Display: Cannot detect displays"
    fi
    
    # Test network
    if curl -s --connect-timeout 5 $SERVER_URL/api/health-check >/dev/null; then
        print_status "Network: Server connectivity OK"
    else
        print_warning "Network: Cannot connect to server"
    fi
    
    print_status "Hardware testing completed"
}

# Function to deploy application
deploy_application() {
    print_status "Deploying MyRVM Application..."
    
    # Make scripts executable
    chmod +x scripts/*.sh
    
    # Run deployment script
    if [ -f "scripts/deploy.sh" ]; then
        sudo ./scripts/deploy.sh
        print_status "Application deployed successfully"
    else
        print_error "Deployment script not found"
        exit 1
    fi
}

# Function to configure auto-start
configure_autostart() {
    print_status "Configuring auto-start..."
    
    # Enable systemd service
    sudo systemctl enable myrvm-application.service
    sudo systemctl daemon-reload
    
    print_status "Auto-start configured"
}

# Function to run final tests
run_final_tests() {
    print_status "Running final tests..."
    
    # Test systemd service
    if sudo systemctl is-enabled myrvm-application.service >/dev/null; then
        print_status "Systemd service: Enabled"
    else
        print_warning "Systemd service: Not enabled"
    fi
    
    # Test configuration
    if python3 -c "import json; json.load(open('config/production_config.json'))" 2>/dev/null; then
        print_status "Configuration: Valid"
    else
        print_error "Configuration: Invalid"
        exit 1
    fi
    
    # Test server connectivity
    if curl -s --connect-timeout 10 $SERVER_URL/api/health-check >/dev/null; then
        print_status "Server connectivity: OK"
    else
        print_warning "Server connectivity: Failed"
    fi
    
    print_status "Final tests completed"
}

# Function to display installation summary
display_summary() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  INSTALLATION COMPLETED SUCCESSFULLY${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Installation Details:${NC}"
    echo -e "  Location: $LOCATION_NAME"
    echo -e "  RVM ID: $RVM_ID"
    echo -e "  Server URL: $SERVER_URL"
    echo -e "  Installation Path: $(pwd)"
    echo -e "  Log File: $LOG_FILE"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "  1. Start the application: sudo systemctl start myrvm-application.service"
    echo -e "  2. Check status: sudo systemctl status myrvm-application.service"
    echo -e "  3. View logs: sudo journalctl -u myrvm-application.service -f"
    echo -e "  4. Test GUI: ./scripts/start_gui_client.sh"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo -e "  Stop service: sudo systemctl stop myrvm-application.service"
    echo -e "  Restart service: sudo systemctl restart myrvm-application.service"
    echo -e "  View logs: tail -f logs/myrvm_application.log"
    echo ""
}

# Main installation function
main() {
    print_status "Starting MyRVM Integration installation for $LOCATION_NAME"
    
    check_requirements
    install_system_dependencies
    clone_repository
    setup_virtual_environment
    configure_rvm
    test_hardware
    deploy_application
    configure_autostart
    run_final_tests
    display_summary
    
    print_status "Installation completed successfully!"
}

# Run main function
main "$@"
