#!/bin/bash

# RVM-Jetson Installation Script
# This script sets up SSH port forwarding, starts web GUI service, and auto-opens browser

# Script configuration
SCRIPT_VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WEB_GUI_PORT=8080
SSH_PORT=22
LOG_FILE="$PROJECT_DIR/logs/installation.log"
PID_FILE="$PROJECT_DIR/installation.pid"

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
    
    # Write to log file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Error handling
handle_error() {
    local exit_code=$?
    log "ERROR" "Script failed with exit code $exit_code"
    cleanup
    exit $exit_code
}

# Cleanup function
cleanup() {
    log "INFO" "Cleaning up..."
    
    # Kill background processes
    if [ -f "$PID_FILE" ]; then
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                log "INFO" "Stopping process $pid"
                kill "$pid"
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    
    # Stop web GUI if running
    pkill -f "web_config_gui/app.py" 2>/dev/null
    
    log "INFO" "Cleanup completed"
}

# Setup signal handlers
trap handle_error ERR
trap cleanup EXIT INT TERM

# Create necessary directories
setup_directories() {
    log "INFO" "Setting up directories..."
    
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/config"
    mkdir -p "$PROJECT_DIR/installation_method/web_config_gui/templates"
    mkdir -p "$PROJECT_DIR/installation_method/web_config_gui/static"
    
    log "INFO" "Directories created successfully"
}

# Check system requirements
check_requirements() {
    log "INFO" "Checking system requirements..."
    
    # Check if running on Jetson
    if ! grep -q "Jetson" /proc/device-tree/model 2>/dev/null; then
        log "WARN" "This script is designed for NVIDIA Jetson devices"
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log "ERROR" "Python3 is not installed"
        exit 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2)
    log "INFO" "Python version: $python_version"
    
    # Check if virtual environment exists
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        log "ERROR" "Virtual environment not found at $PROJECT_DIR/venv"
        log "INFO" "Please run setup.sh first to create virtual environment"
        exit 1
    fi
    
    # Check if web GUI files exist
    if [ ! -f "$PROJECT_DIR/installation_method/web_config_gui/app.py" ]; then
        log "ERROR" "Web GUI application not found"
        exit 1
    fi
    
    log "INFO" "System requirements check passed"
}

# Setup SSH port forwarding
setup_port_forwarding() {
    log "INFO" "Setting up SSH port forwarding..."
    
    # Check if SSH is running
    if ! systemctl is-active --quiet ssh; then
        log "INFO" "Starting SSH service..."
        sudo systemctl start ssh
    fi
    
    # Get current IP address
    local jetson_ip=$(hostname -I | awk '{print $1}')
    log "INFO" "Jetson IP address: $jetson_ip"
    
    # Display SSH connection instructions
    log "INFO" "SSH Port Forwarding Setup:"
    log "INFO" "Run this command on your laptop:"
    log "INFO" "ssh -L $WEB_GUI_PORT:localhost:$WEB_GUI_PORT my@$jetson_ip"
    log "INFO" "Then open browser to: http://localhost:$WEB_GUI_PORT/install"
    
    # Wait for user confirmation
    echo -e "${YELLOW}Press Enter when SSH port forwarding is set up...${NC}"
    read -r
    
    log "INFO" "SSH port forwarding setup completed"
}

# Start web GUI service
start_web_gui() {
    log "INFO" "Starting Web Configuration Interface..."
    
    # Kill any existing Web GUI processes
    log "INFO" "Checking for existing Web GUI processes..."
    pkill -f "web_config_gui/app.py" 2>/dev/null || true
    pkill -f "python3.*app.py" 2>/dev/null || true
    
    # Wait for processes to terminate
    sleep 2
    
    # Check if port is still in use
    if lsof -i :$WEB_GUI_PORT >/dev/null 2>&1; then
        log "WARN" "Port $WEB_GUI_PORT is still in use, trying to free it..."
        # Force kill processes using the port
        fuser -k $WEB_GUI_PORT/tcp 2>/dev/null || true
        sleep 2
    fi
    
    # Activate virtual environment
    source "$PROJECT_DIR/venv/bin/activate"
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Start web GUI in background
    nohup python3 installation_method/web_config_gui/app.py > "$LOG_FILE" 2>&1 &
    local web_gui_pid=$!
    
    # Save PID
    echo "$web_gui_pid" > "$PID_FILE"
    
    # Wait for service to start
    sleep 5
    
    # Check if service is running
    if kill -0 "$web_gui_pid" 2>/dev/null; then
        log "INFO" "Web GUI started successfully (PID: $web_gui_pid)"
        log "INFO" "Web GUI accessible at: http://localhost:$WEB_GUI_PORT/install"
    else
        log "ERROR" "Failed to start Web GUI"
        log "ERROR" "Check log file: $LOG_FILE"
        exit 1
    fi
}

# Auto-open browser (if possible)
auto_open_browser() {
    log "INFO" "Attempting to auto-open browser..."
    
    # Try to detect browser and open
    local browser_opened=false
    
    # Try different browsers
    for browser in "xdg-open" "firefox" "chromium-browser" "google-chrome"; do
        if command -v "$browser" &> /dev/null; then
            log "INFO" "Opening browser: $browser"
            "$browser" "http://localhost:$WEB_GUI_PORT/install" &
            browser_opened=true
            break
        fi
    done
    
    if [ "$browser_opened" = false ]; then
        log "WARN" "No browser found to auto-open"
        log "INFO" "Please manually open: http://localhost:$WEB_GUI_PORT/install"
    fi
}

# Monitor installation
monitor_installation() {
    log "INFO" "Starting installation monitoring..."
    
    # Create monitoring script
    cat > "$PROJECT_DIR/installation_method/monitor_installation.py" << 'EOF'
#!/usr/bin/env python3
import time
import requests
import json
import os
from datetime import datetime

def monitor_installation():
    """Monitor installation progress"""
    log_file = "logs/installation_monitor.log"
    web_gui_url = "http://localhost:8080/api/status"
    
    while True:
        try:
            # Check web GUI status
            response = requests.get(web_gui_url, timeout=5)
            if response.status_code == 200:
                status = response.json()
                
                # Log status
                with open(log_file, "a") as f:
                    f.write(f"[{datetime.now()}] Status: {status.get('status', 'unknown')} - {status.get('message', 'no message')}\n")
                
                # Check if installation is complete
                if status.get('status') == 'completed':
                    print("Installation completed successfully!")
                    break
                elif status.get('status') == 'error':
                    print(f"Installation failed: {status.get('message', 'unknown error')}")
                    break
                    
        except requests.exceptions.RequestException:
            print("Web GUI not responding, waiting...")
            
        time.sleep(5)

if __name__ == "__main__":
    monitor_installation()
EOF
    
    # Start monitoring in background
    python3 "$PROJECT_DIR/installation_method/monitor_installation.py" &
    local monitor_pid=$!
    echo "$monitor_pid" >> "$PID_FILE"
    
    log "INFO" "Installation monitoring started (PID: $monitor_pid)"
}

# Show installation status
show_status() {
    log "INFO" "Installation Status:"
    log "INFO" "==================="
    log "INFO" "Web GUI URL: http://localhost:$WEB_GUI_PORT/install"
    log "INFO" "Dashboard URL: http://localhost:$WEB_GUI_PORT/"
    log "INFO" "Log file: $LOG_FILE"
    log "INFO" "PID file: $PID_FILE"
    
    # Show running processes
    if [ -f "$PID_FILE" ]; then
        log "INFO" "Running processes:"
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                local cmd=$(ps -p "$pid" -o cmd= 2>/dev/null || echo "Unknown")
                log "INFO" "  PID $pid: $cmd"
            fi
        done < "$PID_FILE"
    fi
}

# Main installation function
main() {
    log "INFO" "Starting RVM-Jetson Installation Script v$SCRIPT_VERSION"
    log "INFO" "Project directory: $PROJECT_DIR"
    
    # Setup
    setup_directories
    check_requirements
    
    # Installation steps
    setup_port_forwarding
    start_web_gui
    auto_open_browser
    monitor_installation
    
    # Show final status
    show_status
    
    log "INFO" "Installation script completed successfully!"
    log "INFO" "Web Configuration Interface is now running"
    log "INFO" "Access it at: http://localhost:$WEB_GUI_PORT/install"
    
    # Keep script running to maintain services
    log "INFO" "Press Ctrl+C to stop all services"
    
    # Wait for user interrupt
    while true; do
        sleep 10
        
        # Check if web GUI is still running
        if [ -f "$PID_FILE" ]; then
            local web_gui_pid=$(head -n1 "$PID_FILE")
            if ! kill -0 "$web_gui_pid" 2>/dev/null; then
                log "ERROR" "Web GUI process died, restarting..."
                start_web_gui
            fi
        fi
    done
}

# Help function
show_help() {
    echo "RVM-Jetson Installation Script v$SCRIPT_VERSION"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --version  Show version information"
    echo "  --setup-only   Only setup directories and check requirements"
    echo "  --gui-only     Only start web GUI (skip port forwarding setup)"
    echo ""
    echo "This script will:"
    echo "  1. Setup SSH port forwarding"
    echo "  2. Start Web Configuration Interface"
    echo "  3. Auto-open browser (if possible)"
    echo "  4. Monitor installation progress"
    echo ""
    echo "Prerequisites:"
    echo "  - Virtual environment must be created (run setup.sh first)"
    echo "  - Web GUI files must be present"
    echo "  - SSH service must be available"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -v|--version)
        echo "RVM-Jetson Installation Script v$SCRIPT_VERSION"
        exit 0
        ;;
    --setup-only)
        setup_directories
        check_requirements
        log "INFO" "Setup completed successfully"
        exit 0
        ;;
    --gui-only)
        setup_directories
        check_requirements
        start_web_gui
        auto_open_browser
        show_status
        log "INFO" "Web GUI started successfully"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log "ERROR" "Unknown option: $1"
        show_help
        exit 1
        ;;
esac


