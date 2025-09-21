#!/bin/bash
# MyRVM Application Start Script
# Quick start script for development and testing

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/home/my/test-cv-yolo11-sam2-camera/myrvm-integration"
VENV_DIR="$APP_DIR/venv"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run the deployment script first: ./scripts/deploy.sh"
    exit 1
fi

# Check if main application exists
if [ ! -f "$APP_DIR/main_application.py" ]; then
    echo "Error: Main application not found at $APP_DIR/main_application.py"
    exit 1
fi

log_info "Starting MyRVM Application..."

# Change to application directory
cd "$APP_DIR"

# Activate virtual environment
log_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Start the application
log_info "Starting main application..."
python main_application.py

log_success "MyRVM Application started successfully!"
echo ""
echo "GUI Client: http://localhost:5001"
echo "LED Touch Screen: Access via browser at http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the application"

