#!/bin/bash
# MyRVM Platform Integration Service Installation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="myrvm-integration"
SERVICE_USER="jetson"
SERVICE_GROUP="jetson"
PROJECT_DIR="/home/my/test-cv-yolo11-sam2-camera/myrvm-integration"
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_FILE="$SYSTEMD_DIR/$SERVICE_NAME.service"

echo -e "${BLUE}🚀 MyRVM Platform Integration Service Installation${NC}"
echo "=================================================="

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  Running as root. This is not recommended for service installation.${NC}"
    echo "Please run this script as a regular user with sudo privileges."
    exit 1
fi

# Check if user has sudo privileges
if ! sudo -n true 2>/dev/null; then
    echo -e "${RED}❌ This script requires sudo privileges.${NC}"
    echo "Please ensure you can run sudo commands."
    exit 1
fi

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
    exit 1
fi

# Check if virtual environment exists
VENV_DIR="/home/my/test-cv-yolo11-sam2-camera/myenv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Virtual environment not found: $VENV_DIR${NC}"
    echo "Please create the virtual environment first."
    exit 1
fi

# Check if main script exists
MAIN_SCRIPT="$PROJECT_DIR/main/enhanced_jetson_main.py"
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo -e "${RED}❌ Main script not found: $MAIN_SCRIPT${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Stop existing service if running
echo -e "${YELLOW}🛑 Stopping existing service...${NC}"
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    sudo systemctl stop "$SERVICE_NAME"
    echo -e "${GREEN}✅ Service stopped${NC}"
else
    echo -e "${BLUE}ℹ️  Service not running${NC}"
fi

# Disable existing service if enabled
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    sudo systemctl disable "$SERVICE_NAME"
    echo -e "${GREEN}✅ Service disabled${NC}"
fi

# Copy service file
echo -e "${YELLOW}📄 Installing service file...${NC}"
sudo cp "$PROJECT_DIR/systemd/$SERVICE_NAME.service" "$SERVICE_FILE"
sudo chmod 644 "$SERVICE_FILE"
echo -e "${GREEN}✅ Service file installed${NC}"

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
sudo mkdir -p /var/run
sudo mkdir -p "$PROJECT_DIR/logs"
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "$PROJECT_DIR/logs"
echo -e "${GREEN}✅ Directories created${NC}"

# Set proper permissions
echo -e "${YELLOW}🔐 Setting permissions...${NC}"
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "$PROJECT_DIR"
sudo chmod -R 755 "$PROJECT_DIR"
sudo chmod +x "$MAIN_SCRIPT"
echo -e "${GREEN}✅ Permissions set${NC}"

# Reload systemd
echo -e "${YELLOW}🔄 Reloading systemd...${NC}"
sudo systemctl daemon-reload
echo -e "${GREEN}✅ Systemd reloaded${NC}"

# Enable service
echo -e "${YELLOW}⚡ Enabling service...${NC}"
sudo systemctl enable "$SERVICE_NAME"
echo -e "${GREEN}✅ Service enabled${NC}"

# Start service
echo -e "${YELLOW}🚀 Starting service...${NC}"
sudo systemctl start "$SERVICE_NAME"
echo -e "${GREEN}✅ Service started${NC}"

# Wait a moment for service to start
sleep 3

# Check service status
echo -e "${YELLOW}📊 Checking service status...${NC}"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✅ Service is running${NC}"
else
    echo -e "${RED}❌ Service failed to start${NC}"
    echo "Service status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager
    exit 1
fi

# Show service information
echo ""
echo -e "${BLUE}📋 Service Information${NC}"
echo "====================="
echo "Service Name: $SERVICE_NAME"
echo "Service File: $SERVICE_FILE"
echo "Project Directory: $PROJECT_DIR"
echo "Main Script: $MAIN_SCRIPT"
echo "Log File: $PROJECT_DIR/logs/myrvm-integration.log"

echo ""
echo -e "${BLUE}🔧 Service Management Commands${NC}"
echo "================================="
echo "Start service:    sudo systemctl start $SERVICE_NAME"
echo "Stop service:     sudo systemctl stop $SERVICE_NAME"
echo "Restart service:  sudo systemctl restart $SERVICE_NAME"
echo "Service status:   sudo systemctl status $SERVICE_NAME"
echo "View logs:        sudo journalctl -u $SERVICE_NAME -f"
echo "View service logs: tail -f $PROJECT_DIR/logs/myrvm-integration.log"

echo ""
echo -e "${GREEN}🎉 Service installation completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Check service logs: sudo journalctl -u $SERVICE_NAME -f"
echo "2. Verify service is working: sudo systemctl status $SERVICE_NAME"
echo "3. Monitor application logs: tail -f $PROJECT_DIR/logs/myrvm-integration.log"
echo "4. Test the service functionality"
echo ""
echo -e "${BLUE}ℹ️  The service will automatically start on system boot.${NC}"
