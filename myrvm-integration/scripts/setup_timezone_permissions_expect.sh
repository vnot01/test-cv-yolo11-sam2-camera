#!/usr/bin/expect -f
# Setup timezone sync permissions with expect

set timeout 30

# Add user to time group
spawn sudo usermod -a -G time my
expect "password for my:"
send "my\r"
expect eof

# Configure sudoers for timezone sync
spawn sudo tee /etc/sudoers.d/timezone-sync
expect "password for my:"
send "my\r"
send "my ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-timezone *\r"
send "\x04"
expect eof

# Set proper permissions
spawn sudo chmod 440 /etc/sudoers.d/timezone-sync
expect "password for my:"
send "my\r"
expect eof

puts "Timezone sync permissions configured successfully!"
puts "User 'my' can now change timezone without password prompt"
