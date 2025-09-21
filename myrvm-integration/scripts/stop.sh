#!/bin/bash
# MyRVM Application Stop Script
# Stop the application gracefully

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="myrvm-application"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if service is running
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    log_info "Stopping MyRVM service..."
    sudo systemctl stop "$SERVICE_NAME"
    log_success "MyRVM service stopped"
else
    log_info "MyRVM service is not running"
fi

# Check for running Python processes
PYTHON_PIDS=$(pgrep -f "main_application.py" || true)
if [ ! -z "$PYTHON_PIDS" ]; then
    log_info "Stopping Python processes..."
    echo "$PYTHON_PIDS" | xargs kill -TERM
    sleep 2
    
    # Force kill if still running
    PYTHON_PIDS=$(pgrep -f "main_application.py" || true)
    if [ ! -z "$PYTHON_PIDS" ]; then
        log_info "Force stopping Python processes..."
        echo "$PYTHON_PIDS" | xargs kill -KILL
    fi
    
    log_success "Python processes stopped"
else
    log_info "No Python processes found"
fi

# Check for Flask processes
FLASK_PIDS=$(pgrep -f "gui_client.py" || true)
if [ ! -z "$FLASK_PIDS" ]; then
    log_info "Stopping Flask processes..."
    echo "$FLASK_PIDS" | xargs kill -TERM
    sleep 2
    
    # Force kill if still running
    FLASK_PIDS=$(pgrep -f "gui_client.py" || true)
    if [ ! -z "$FLASK_PIDS" ]; then
        log_info "Force stopping Flask processes..."
        echo "$FLASK_PIDS" | xargs kill -KILL
    fi
    
    log_success "Flask processes stopped"
else
    log_info "No Flask processes found"
fi

log_success "MyRVM Application stopped successfully!"



