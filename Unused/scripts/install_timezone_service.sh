#!/bin/bash
# Install timezone sync service

echo "Installing timezone sync service..."

# Copy service files
sudo cp systemd/timezone-sync.service /etc/systemd/system/
sudo cp systemd/timezone-sync.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start timer
sudo systemctl enable timezone-sync.timer
sudo systemctl start timezone-sync.timer

# Check status
echo "Timezone sync service status:"
sudo systemctl status timezone-sync.timer

echo "Timezone sync service installed successfully!"
echo "Service will run daily at 2:00 AM and on boot"
