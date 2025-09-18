#!/bin/bash
# Setup timezone sync permissions using password file

echo "Setting up timezone sync permissions..."

# Create password file
echo "my" > /tmp/sudo_password

# Create sudoers file directly
sudo -S tee /etc/sudoers.d/timezone-sync < /tmp/sudo_password > /dev/null << 'EOF'
my ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-timezone *
EOF

# Set proper permissions
sudo -S chmod 440 /etc/sudoers.d/timezone-sync < /tmp/sudo_password

# Add user to time group
sudo -S usermod -a -G time my < /tmp/sudo_password

# Clean up password file
rm /tmp/sudo_password

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
