#!/bin/bash
# Setup timezone sync permissions

echo "Setting up timezone sync permissions..."

# Add user to time group
sudo usermod -a -G time my

# Configure sudoers for timezone sync
echo "my ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-timezone *" | sudo tee /etc/sudoers.d/timezone-sync

# Set proper permissions
sudo chmod 440 /etc/sudoers.d/timezone-sync

echo "Timezone sync permissions configured successfully!"
echo "User 'my' can now change timezone without password prompt"
