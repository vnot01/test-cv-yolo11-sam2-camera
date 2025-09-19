#!/bin/bash
# Setup timezone sync permissions using environment variable

echo "Setting up timezone sync permissions..."

# Check if password is provided
if [ -z "$SUDO_PASSWORD" ]; then
    echo "Please set SUDO_PASSWORD environment variable:"
    echo "export SUDO_PASSWORD=your_password"
    echo "Then run: ./scripts/setup_timezone_permissions_env.sh"
    exit 1
fi

# Create sudoers file directly
echo "$SUDO_PASSWORD" | sudo -S tee /etc/sudoers.d/timezone-sync > /dev/null << 'EOF'
my ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-timezone *
EOF

# Set proper permissions
echo "$SUDO_PASSWORD" | sudo -S chmod 440 /etc/sudoers.d/timezone-sync

# Add user to time group
echo "$SUDO_PASSWORD" | sudo -S usermod -a -G time my

echo "Timezone sync permissions configured successfully!"
echo "User 'my' can now change timezone without password prompt"

# Test the permission
echo "Testing timezone change permission..."
sudo -n timedatectl set-timezone Asia/Jakarta
if [ $? -eq 0 ]; then
    echo "✅ Permission test successful!"
else
    echo "❌ Permission test failed!"
fi
