#!/bin/bash
# Install Remote Camera and GUI Services for MyRVM Platform Integration

set -e

echo "🚀 Installing RVM Remote Services..."
echo "=================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please do not run this script as root"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "services/remote_camera_service.py" ]; then
    echo "❌ Please run this script from the myrvm-integration directory"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p storages/images/remote_captures
mkdir -p templates
mkdir -p static/css
mkdir -p static/js

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install flask opencv-python psutil pillow

# Copy systemd service files
echo "⚙️ Installing systemd service files..."
sudo cp systemd/rvm-remote-camera.service /etc/systemd/system/
sudo cp systemd/rvm-remote-gui.service /etc/systemd/system/

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable services
echo "✅ Enabling services..."
sudo systemctl enable rvm-remote-camera.service
sudo systemctl enable rvm-remote-gui.service

# Set permissions
echo "🔐 Setting permissions..."
chmod +x services/remote_camera_service.py
chmod +x services/remote_gui_service.py
chmod +x scripts/install_remote_services.sh

# Create log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/rvm-remote-services > /dev/null <<EOF
/home/my/test-cv-yolo11-sam2-camera/myrvm-integration/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 my my
}
EOF

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Start the services:"
echo "   sudo systemctl start rvm-remote-camera"
echo "   sudo systemctl start rvm-remote-gui"
echo ""
echo "2. Check service status:"
echo "   sudo systemctl status rvm-remote-camera"
echo "   sudo systemctl status rvm-remote-gui"
echo ""
echo "3. Access the services:"
echo "   Camera: http://$(hostname -I | awk '{print $1}'):5000"
echo "   GUI: http://$(hostname -I | awk '{print $1}'):5001"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u rvm-remote-camera -f"
echo "   sudo journalctl -u rvm-remote-gui -f"
echo ""
echo "🎉 Remote services are ready!"
