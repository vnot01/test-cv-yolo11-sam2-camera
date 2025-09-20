#!/bin/bash
# Setup timezone sync permissions using printf

echo "Setting up timezone sync permissions..."

# Create sudoers file directly
printf "my\n" | sudo -S tee /etc/sudoers.d/timezone-sync > /dev/null << 'EOF'
my ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-timezone *
EOF

# Set proper permissions
printf "my\n" | sudo -S chmod 440 /etc/sudoers.d/timezone-sync

# Add user to time group
printf "my\n" | sudo -S usermod -a -G time my

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
