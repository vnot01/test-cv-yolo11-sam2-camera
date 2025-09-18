#!/bin/bash
# Setup timezone using environment variables (no sudo required)

echo "Setting up timezone using environment variables..."

# Create timezone configuration file
mkdir -p ~/.config/myrvm-integration

# Set timezone in user profile
echo 'export TZ="Asia/Jakarta"' >> ~/.bashrc
echo 'export TZ="Asia/Jakarta"' >> ~/.profile

# Create timezone config file
cat > ~/.config/myrvm-integration/timezone.conf << 'EOF'
# MyRVM Platform Integration Timezone Configuration
TZ=Asia/Jakarta
TIMEZONE=Asia/Jakarta
COUNTRY=Indonesia
CITY=Jakarta
UTC_OFFSET=+0700
EOF

# Create systemd user service directory
mkdir -p ~/.config/systemd/user

# Create user systemd service
cat > ~/.config/systemd/user/timezone-sync.service << 'EOF'
[Unit]
Description=MyRVM Platform Timezone Sync Service (User)
After=graphical-session.target

[Service]
Type=oneshot
Environment=TZ=Asia/Jakarta
WorkingDirectory=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration
ExecStart=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration/venv/bin/python /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/services/timezone_sync_service_no_sudo.py --auto-sync
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

# Create user systemd timer
cat > ~/.config/systemd/user/timezone-sync.timer << 'EOF'
[Unit]
Description=MyRVM Platform Timezone Sync Timer (User)
Requires=timezone-sync.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=24h
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Reload systemd user daemon
systemctl --user daemon-reload

# Enable and start timer
systemctl --user enable timezone-sync.timer
systemctl --user start timezone-sync.timer

echo "Timezone environment setup completed successfully!"
echo "User timezone service installed and started"

# Test the setup
echo "Testing timezone setup..."
source ~/.bashrc
echo "Current TZ: $TZ"
echo "Current time: $(date)"

# Check service status
echo "Service status:"
systemctl --user status timezone-sync.timer
