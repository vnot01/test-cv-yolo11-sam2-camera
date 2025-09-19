#!/bin/bash

# Install Remote Access Services for MyRVM Platform Integration
# This script installs and configures the remote access controller

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/home/my/test-cv-yolo11-sam2-camera/myrvm-integration"
SERVICE_NAME="rvm-remote-access"
SERVICE_FILE="rvm-remote-access.service"

echo -e "${BLUE}🚀 Installing Remote Access Services...${NC}"

# Check if running as correct user
if [ "$USER" != "my" ]; then
    echo -e "${RED}❌ This script must be run as user 'my'${NC}"
    exit 1
fi

# Check if project directory exists
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_ROOT${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"

echo -e "${YELLOW}📁 Setting up directories...${NC}"

# Create necessary directories
mkdir -p data
mkdir -p logs
mkdir -p templates
mkdir -p systemd

echo -e "${YELLOW}🐍 Checking Python virtual environment...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please create it first.${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"

# Install required packages
pip install flask opencv-python pillow psutil

echo -e "${YELLOW}🔧 Installing systemd service...${NC}"

# Copy service file to systemd directory
sudo cp systemd/$SERVICE_FILE /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable $SERVICE_NAME

echo -e "${YELLOW}🔐 Setting up permissions...${NC}"

# Set proper permissions
chmod +x services/remote_access_controller.py
chmod +x services/ondemand_camera_manager.py

# Make scripts executable
chmod +x scripts/*.sh

echo -e "${YELLOW}📝 Creating log rotation configuration...${NC}"

# Create logrotate configuration
sudo tee /etc/logrotate.d/rvm-remote-access > /dev/null <<EOF
/home/my/test-cv-yolo11-sam2-camera/myrvm-integration/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 my my
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

echo -e "${YELLOW}🧪 Testing installation...${NC}"

# Test Python imports
python -c "
import sys
sys.path.append('$PROJECT_ROOT')
try:
    from services.remote_access_controller import RemoteAccessController
    from services.ondemand_camera_manager import OnDemandCameraManager
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

echo -e "${GREEN}✅ Installation completed successfully!${NC}"

echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "1. Start the service: ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
echo -e "2. Check status: ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "3. View logs: ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo -e "4. Access dashboard: ${YELLOW}http://localhost:5001${NC}"

echo -e "${BLUE}🔧 Configuration files:${NC}"
echo -e "- Service config: ${YELLOW}/etc/systemd/system/$SERVICE_FILE${NC}"
echo -e "- Log rotation: ${YELLOW}/etc/logrotate.d/rvm-remote-access${NC}"
echo -e "- Project config: ${YELLOW}$PROJECT_ROOT/config/development_config.json${NC}"

echo -e "${GREEN}🎉 Remote Access Services installation complete!${NC}"
