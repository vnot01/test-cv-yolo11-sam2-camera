#!/bin/bash
# Setup timezone sync permissions using cat

echo "Setting up timezone sync permissions..."

# Create sudoers file directly
cat << 'EOF' | sudo tee /etc/sudoers.d/timezone-sync > /dev/null
my ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-timezone *
EOF

# Set proper permissions
sudo chmod 440 /etc/sudoers.d/timezone-sync

# Add user to time group
sudo usermod -a -G time my

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
