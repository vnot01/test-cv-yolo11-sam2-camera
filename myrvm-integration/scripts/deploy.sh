#!/bin/bash
# MyRVM Application Deployment Script
# Production deployment automation

set -e  # Exit on any error

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
SERVICE_NAME="myrvm-application"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
BACKUP_DIR="/backup/myrvm"
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
    
    # Check if running as root for systemd operations
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. Some operations may require sudo."
    fi
    
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
    
    log_success "System requirements check passed"
}

backup_current_deployment() {
    log_info "Creating backup of current deployment..."
    
    # Create backup directory
    sudo mkdir -p "$BACKUP_DIR"
    
    # Create timestamped backup
    BACKUP_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
    
    # Backup application files
    sudo cp -r "$APP_DIR" "$BACKUP_PATH"
    
    # Backup systemd service if exists
    if [ -f "$SERVICE_FILE" ]; then
        sudo cp "$SERVICE_FILE" "$BACKUP_PATH/systemd_service.backup"
    fi
    
    log_success "Backup created at $BACKUP_PATH"
}

install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Install/upgrade dependencies
    pip install --upgrade pip
    pip install -r "$APP_DIR/requirements.txt" 2>/dev/null || {
        log_warning "requirements.txt not found, installing basic dependencies"
        pip install flask qrcode[pil] websocket-client psutil
    }
    
    log_success "Dependencies installed successfully"
}

create_systemd_service() {
    log_info "Creating systemd service file..."
    
    # Create systemd service file
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=MyRVM Application - Computer Vision Hybrid Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=my
Group=my
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python3 $APP_DIR/main_application.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myrvm-application

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR $LOG_DIR $BACKUP_DIR

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

    log_success "Systemd service file created"
}

setup_logging() {
    log_info "Setting up logging directories..."
    
    # Create log directories
    sudo mkdir -p "$LOG_DIR"
    sudo chown -R my:my "$LOG_DIR"
    
    # Create backup directory
    sudo mkdir -p "$BACKUP_DIR"
    sudo chown -R my:my "$BACKUP_DIR"
    
    log_success "Logging directories created"
}

configure_firewall() {
    log_info "Configuring firewall rules..."
    
    # Allow GUI Client port
    sudo ufw allow 5001/tcp comment "MyRVM GUI Client" 2>/dev/null || {
        log_warning "UFW not available or already configured"
    }
    
    log_success "Firewall configured"
}

enable_service() {
    log_info "Enabling and starting MyRVM service..."
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable "$SERVICE_NAME"
    
    # Start service
    sudo systemctl start "$SERVICE_NAME"
    
    # Check status
    sleep 2
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "MyRVM service started successfully"
    else
        log_error "Failed to start MyRVM service"
        sudo systemctl status "$SERVICE_NAME"
        exit 1
    fi
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check service status
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Service is running"
    else
        log_error "Service is not running"
        return 1
    fi
    
    # Check GUI Client
    if curl -s http://localhost:5001 > /dev/null; then
        log_success "GUI Client is accessible"
    else
        log_warning "GUI Client is not accessible"
    fi
    
    # Check logs
    if [ -f "$LOG_DIR/myrvm_application_$(date +%Y%m%d).log" ]; then
        log_success "Application logs are being created"
    else
        log_warning "Application logs not found"
    fi
    
    log_success "Deployment verification completed"
}

show_status() {
    log_info "MyRVM Application Status:"
    echo "=================================="
    
    # Service status
    echo "Service Status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
    
    echo ""
    echo "Service Logs (last 10 lines):"
    sudo journalctl -u "$SERVICE_NAME" -n 10 --no-pager
    
    echo ""
    echo "Application Logs (last 10 lines):"
    if [ -f "$LOG_DIR/myrvm_application_$(date +%Y%m%d).log" ]; then
        tail -n 10 "$LOG_DIR/myrvm_application_$(date +%Y%m%d).log"
    else
        echo "No application logs found"
    fi
    
    echo ""
    echo "GUI Client: http://localhost:5001"
    echo "LED Touch Screen: Access via browser at http://localhost:5001"
}

# Main deployment function
deploy() {
    log_info "Starting MyRVM Application deployment..."
    
    check_requirements
    backup_current_deployment
    install_dependencies
    create_systemd_service
    setup_logging
    configure_firewall
    enable_service
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
        log_info "Restarting MyRVM service..."
        sudo systemctl restart "$SERVICE_NAME"
        log_success "Service restarted"
        show_status
        ;;
    "stop")
        log_info "Stopping MyRVM service..."
        sudo systemctl stop "$SERVICE_NAME"
        log_success "Service stopped"
        ;;
    "start")
        log_info "Starting MyRVM service..."
        sudo systemctl start "$SERVICE_NAME"
        log_success "Service started"
        show_status
        ;;
    "logs")
        log_info "Showing MyRVM service logs..."
        sudo journalctl -u "$SERVICE_NAME" -f
        ;;
    "uninstall")
        log_warning "Uninstalling MyRVM Application..."
        sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
        sudo rm -f "$SERVICE_FILE"
        sudo systemctl daemon-reload
        log_success "MyRVM Application uninstalled"
        ;;
    *)
        echo "Usage: $0 {deploy|status|restart|stop|start|logs|uninstall}"
        echo ""
        echo "Commands:"
        echo "  deploy     - Deploy MyRVM Application (default)"
        echo "  status     - Show application status"
        echo "  restart    - Restart the service"
        echo "  stop       - Stop the service"
        echo "  start      - Start the service"
        echo "  logs       - Show service logs"
        echo "  uninstall  - Uninstall the application"
        exit 1
        ;;
esac
