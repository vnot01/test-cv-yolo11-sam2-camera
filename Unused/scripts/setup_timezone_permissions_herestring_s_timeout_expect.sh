#!/bin/bash
# Setup timezone sync permissions using here string with -S flag and timeout and expect

echo "Setting up timezone sync permissions..."

# Create sudoers file directly
expect << 'EOF'
spawn sudo tee /etc/sudoers.d/timezone-sync
expect "password for my:"
send "my\r"
send "my ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-timezone *\r"
send "\x04"
expect eof
EOF

# Set proper permissions
expect << 'EOF'
spawn sudo chmod 440 /etc/sudoers.d/timezone-sync
expect "password for my:"
send "my\r"
expect eof
EOF

# Add user to time group
expect << 'EOF'
spawn sudo usermod -a -G time my
expect "password for my:"
send "my\r"
expect eof
EOF

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
