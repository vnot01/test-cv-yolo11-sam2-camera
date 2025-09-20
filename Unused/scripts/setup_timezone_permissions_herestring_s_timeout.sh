#!/bin/bash
# Setup timezone sync permissions using here string with -S flag and timeout

echo "Setting up timezone sync permissions..."

# Create sudoers file directly
timeout 10 bash -c 'echo "my" | sudo -S tee /etc/sudoers.d/timezone-sync > /dev/null <<< "my ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-timezone *"'

# Set proper permissions
timeout 10 bash -c 'echo "my" | sudo -S chmod 440 /etc/sudoers.d/timezone-sync'

# Add user to time group
timeout 10 bash -c 'echo "my" | sudo -S usermod -a -G time my'

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
