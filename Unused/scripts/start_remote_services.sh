#!/bin/bash
# Start Remote Camera and GUI Services

set -e

echo "🚀 Starting RVM Remote Services..."
echo "================================="

# Check if services are installed
if [ ! -f "/etc/systemd/system/rvm-remote-camera.service" ]; then
    echo "❌ Services not installed. Please run install_remote_services.sh first"
    exit 1
fi

# Start camera service
echo "📹 Starting Remote Camera Service..."
sudo systemctl start rvm-remote-camera.service

# Start GUI service
echo "🎛️ Starting Remote GUI Service..."
sudo systemctl start rvm-remote-gui.service

# Wait a moment for services to start
sleep 3

# Check service status
echo ""
echo "📊 Service Status:"
echo "=================="

echo "Camera Service:"
sudo systemctl status rvm-remote-camera.service --no-pager -l

echo ""
echo "GUI Service:"
sudo systemctl status rvm-remote-gui.service --no-pager -l

# Check if ports are listening
echo ""
echo "🌐 Port Status:"
echo "==============="

if netstat -tlnp | grep -q ":5000 "; then
    echo "✅ Port 5000 (Camera) is listening"
else
    echo "❌ Port 5000 (Camera) is not listening"
fi

if netstat -tlnp | grep -q ":5001 "; then
    echo "✅ Port 5001 (GUI) is listening"
else
    echo "❌ Port 5001 (GUI) is not listening"
fi

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "🎉 Services started successfully!"
echo ""
echo "📱 Access URLs:"
echo "Camera: http://$LOCAL_IP:5000"
echo "GUI: http://$LOCAL_IP:5001"
echo ""
echo "📋 Useful commands:"
echo "Stop services: sudo systemctl stop rvm-remote-camera rvm-remote-gui"
echo "Restart services: sudo systemctl restart rvm-remote-camera rvm-remote-gui"
echo "View logs: sudo journalctl -u rvm-remote-camera -f"
echo "View logs: sudo journalctl -u rvm-remote-gui -f"
