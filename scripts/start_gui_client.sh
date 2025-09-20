#!/bin/bash
# MyRVM GUI Client Start Script
# Safe browser launch for LED Touch Screen

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GUI_URL="http://localhost:5001"
BACKUP_URL="http://192.168.1.11:5001"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if GUI Client is running
check_gui_client() {
    log_info "Checking if GUI Client is running..."
    
    if curl -s "$GUI_URL" > /dev/null 2>&1; then
        log_success "GUI Client is running at $GUI_URL"
        return 0
    elif curl -s "$BACKUP_URL" > /dev/null 2>&1; then
        log_success "GUI Client is running at $BACKUP_URL"
        GUI_URL="$BACKUP_URL"
        return 0
    else
        log_warning "GUI Client is not running"
        return 1
    fi
}

# Start GUI Client if not running
start_gui_client() {
    log_info "Starting GUI Client..."
    
    cd /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_warning "Virtual environment not found, using system Python"
        python3 gui/gui_client.py &
    else
        source venv/bin/activate
        python gui/gui_client.py &
    fi
    
    # Wait for GUI Client to start
    sleep 5
    
    if check_gui_client; then
        log_success "GUI Client started successfully"
    else
        log_warning "GUI Client may not have started properly"
    fi
}

# Launch browser safely
launch_browser() {
    log_info "Launching browser for LED Touch Screen..."
    
    # Try different browser options
    if command -v chromium-browser &> /dev/null; then
        log_info "Using Chromium browser..."
        # Launch with minimal security restrictions
        chromium-browser \
            --no-sandbox \
            --disable-dev-shm-usage \
            --disable-gpu \
            --disable-software-rasterizer \
            --disable-background-timer-throttling \
            --disable-backgrounding-occluded-windows \
            --disable-renderer-backgrounding \
            --disable-features=TranslateUI \
            --disable-ipc-flooding-protection \
            --kiosk \
            --disable-infobars \
            --disable-web-security \
            --user-data-dir=/tmp/chrome_myrvm \
            "$GUI_URL" &
    elif command -v firefox &> /dev/null; then
        log_info "Using Firefox browser..."
        firefox --kiosk "$GUI_URL" &
    elif command -v google-chrome &> /dev/null; then
        log_info "Using Google Chrome browser..."
        google-chrome \
            --no-sandbox \
            --disable-dev-shm-usage \
            --kiosk \
            --disable-infobars \
            --user-data-dir=/tmp/chrome_myrvm \
            "$GUI_URL" &
    else
        log_warning "No suitable browser found. Please install chromium-browser, firefox, or google-chrome"
        echo "You can manually open: $GUI_URL"
        return 1
    fi
    
    log_success "Browser launched successfully"
}

# Main function
main() {
    echo "=========================================="
    echo "MyRVM GUI Client - LED Touch Screen"
    echo "=========================================="
    
    # Check if GUI Client is running
    if ! check_gui_client; then
        start_gui_client
    fi
    
    # Launch browser
    launch_browser
    
    echo ""
    echo "GUI Client URL: $GUI_URL"
    echo "LED Touch Screen: Browser launched in kiosk mode"
    echo ""
    echo "Press Ctrl+C to stop"
    
    # Keep script running
    wait
}

# Handle Ctrl+C
trap 'echo -e "\n${GREEN}[INFO]${NC} Stopping GUI Client..."; exit 0' INT

# Run main function
main
