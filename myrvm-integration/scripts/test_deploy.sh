#!/bin/bash
# MyRVM Application Test Deployment Script
# Test deployment without sudo requirements

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="MyRVM Application"
APP_DIR="/home/my/test-cv-yolo11-sam2-camera/myrvm-integration"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="$APP_DIR/logs"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not installed"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found at $VENV_DIR"
        exit 1
    fi
    
    # Check if main application exists
    if [ ! -f "$APP_DIR/main_application.py" ]; then
        log_error "Main application not found at $APP_DIR/main_application.py"
        exit 1
    fi
    
    log_success "System requirements check passed"
}

install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Install/upgrade dependencies
    pip install --upgrade pip
    pip install flask qrcode[pil] websocket-client psutil numpy
    
    log_success "Dependencies installed successfully"
}

setup_logging() {
    log_info "Setting up logging directories..."
    
    # Create log directories
    mkdir -p "$LOG_DIR"
    
    log_success "Logging directories created"
}

test_application() {
    log_info "Testing MyRVM Application..."
    
    # Change to application directory
    cd "$APP_DIR"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Test import
    python3 -c "
import sys
sys.path.append('.')
try:
    from main_application import MyRVMApplication
    print('✅ Main application import successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    
    log_success "Application test passed"
}

start_application() {
    log_info "Starting MyRVM Application..."
    
    # Change to application directory
    cd "$APP_DIR"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Start the application
    log_info "Starting main application..."
    python3 main_application.py &
    
    APP_PID=$!
    echo $APP_PID > /tmp/myrvm_app.pid
    
    # Wait for application to start
    sleep 5
    
    # Check if application is running
    if ps -p $APP_PID > /dev/null; then
        log_success "MyRVM Application started successfully (PID: $APP_PID)"
    else
        log_error "Failed to start MyRVM Application"
        return 1
    fi
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if application is running
    if [ -f "/tmp/myrvm_app.pid" ]; then
        APP_PID=$(cat /tmp/myrvm_app.pid)
        if ps -p $APP_PID > /dev/null; then
            log_success "Application is running (PID: $APP_PID)"
        else
            log_error "Application is not running"
            return 1
        fi
    else
        log_error "Application PID file not found"
        return 1
    fi
    
    # Check GUI Client
    if curl -s http://localhost:5001 > /dev/null; then
        log_success "GUI Client is accessible"
    else
        log_warning "GUI Client is not accessible"
    fi
    
    log_success "Deployment verification completed"
}

show_status() {
    log_info "MyRVM Application Status:"
    echo "=================================="
    
    # Check if application is running
    if [ -f "/tmp/myrvm_app.pid" ]; then
        APP_PID=$(cat /tmp/myrvm_app.pid)
        if ps -p $APP_PID > /dev/null; then
            echo "Application Status: Running (PID: $APP_PID)"
        else
            echo "Application Status: Not running"
        fi
    else
        echo "Application Status: Not started"
    fi
    
    # Check GUI Client
    if curl -s http://localhost:5001 > /dev/null; then
        echo "GUI Client: Accessible at http://localhost:5001"
    else
        echo "GUI Client: Not accessible"
    fi
    
    echo ""
    echo "GUI Client: http://localhost:5001"
    echo "LED Touch Screen: Access via browser at http://localhost:5001"
}

stop_application() {
    log_info "Stopping MyRVM Application..."
    
    if [ -f "/tmp/myrvm_app.pid" ]; then
        APP_PID=$(cat /tmp/myrvm_app.pid)
        if ps -p $APP_PID > /dev/null; then
            kill $APP_PID
            log_success "Application stopped (PID: $APP_PID)"
        else
            log_warning "Application was not running"
        fi
        rm -f /tmp/myrvm_app.pid
    else
        log_warning "Application PID file not found"
    fi
}

# Main deployment function
deploy() {
    log_info "Starting MyRVM Application test deployment..."
    
    check_requirements
    install_dependencies
    setup_logging
    test_application
    start_application
    verify_deployment
    
    log_success "MyRVM Application deployed successfully!"
    show_status
}

# Command line interface
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "status")
        show_status
        ;;
    "restart")
        log_info "Restarting MyRVM Application..."
        stop_application
        sleep 2
        start_application
        log_success "Application restarted"
        show_status
        ;;
    "stop")
        stop_application
        ;;
    "start")
        start_application
        show_status
        ;;
    *)
        echo "Usage: $0 {deploy|status|restart|stop|start}"
        echo ""
        echo "Commands:"
        echo "  deploy     - Deploy MyRVM Application (default)"
        echo "  status     - Show application status"
        echo "  restart    - Restart the application"
        echo "  stop       - Stop the application"
        echo "  start      - Start the application"
        exit 1
        ;;
esac


