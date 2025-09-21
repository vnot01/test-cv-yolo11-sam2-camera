#!/bin/bash

# HARDWARE CONFIGURATION SCRIPT FOR RVM LOCATION A
# This script configures hardware-specific settings for Location A

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
RVM_ID=5
LOCATION_NAME="Location A"
DISPLAY_RESOLUTION="1920x1080"
TOUCH_DEVICE="/dev/input/event0"
CAMERA_DEVICE="/dev/video0"

print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Function to configure display
configure_display() {
    print_status "Configuring display settings..."
    
    # Create X11 configuration
    sudo tee /etc/X11/xorg.conf.d/99-myrvm-display.conf > /dev/null << EOF
Section "Monitor"
    Identifier "MyRVM Monitor"
    Option "PreferredMode" "$DISPLAY_RESOLUTION"
    Option "Position" "0 0"
EndSection

Section "Device"
    Identifier "MyRVM Device"
    Driver "nvidia"
    Option "NoLogo" "true"
    Option "UseEDID" "false"
    Option "CustomEDID" "DFP:/etc/X11/edid.bin"
EndSection

Section "Screen"
    Identifier "MyRVM Screen"
    Device "MyRVM Device"
    Monitor "MyRVM Monitor"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "$DISPLAY_RESOLUTION"
    EndSubSection
EndSection
EOF
    
    print_status "Display configuration completed"
}

# Function to configure touch input
configure_touch() {
    print_status "Configuring touch input..."
    
    # Check if touch device exists
    if [ -e "$TOUCH_DEVICE" ]; then
        print_status "Touch device found: $TOUCH_DEVICE"
        
        # Create touch configuration
        sudo tee /etc/X11/xorg.conf.d/99-myrvm-touch.conf > /dev/null << EOF
Section "InputClass"
    Identifier "MyRVM Touch"
    MatchIsTouchscreen "on"
    MatchDevicePath "/dev/input/event*"
    Driver "libinput"
    Option "CalibrationMatrix" "1 0 0 0 1 0 0 0 1"
    Option "SwapAxes" "0"
    Option "InvertX" "false"
    Option "InvertY" "false"
EndSection
EOF
        
        # Set permissions
        sudo chmod 666 $TOUCH_DEVICE
        sudo usermod -a -G input $USER
        
        print_status "Touch configuration completed"
    else
        print_warning "Touch device not found: $TOUCH_DEVICE"
    fi
}

# Function to configure camera
configure_camera() {
    print_status "Configuring camera settings..."
    
    # Check if camera device exists
    if [ -e "$CAMERA_DEVICE" ]; then
        print_status "Camera device found: $CAMERA_DEVICE"
        
        # Set camera permissions
        sudo chmod 666 $CAMERA_DEVICE
        sudo usermod -a -G video $USER
        
        # Create camera configuration
        sudo tee /etc/modprobe.d/camera.conf > /dev/null << EOF
# Camera configuration for MyRVM
options uvcvideo nodrop=1
options uvcvideo quirks=0x80
EOF
        
        print_status "Camera configuration completed"
    else
        print_warning "Camera device not found: $CAMERA_DEVICE"
    fi
}

# Function to configure network
configure_network() {
    print_status "Configuring network settings..."
    
    # Create network configuration
    sudo tee /etc/netplan/99-myrvm.yaml > /dev/null << EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: false
  wifis:
    wlan0:
      dhcp4: true
      dhcp6: false
      access-points:
        "MyRVM-Network":
          password: "myrvm123"
EOF
    
    # Apply network configuration
    sudo netplan apply
    
    print_status "Network configuration completed"
}

# Function to configure GPIO (for motor control)
configure_gpio() {
    print_status "Configuring GPIO for motor control..."
    
    # Install GPIO tools
    sudo apt install -y gpiod libgpiod-dev
    
    # Create GPIO configuration
    sudo tee /etc/gpio-myrvm.conf > /dev/null << EOF
# GPIO configuration for MyRVM Location A
# Motor control pins
MOTOR_STEP_PIN=18
MOTOR_DIR_PIN=19
MOTOR_ENABLE_PIN=20

# Door sensor pins
DOOR_OPEN_SENSOR_PIN=21
DOOR_CLOSE_SENSOR_PIN=22

# LED control pins
LED_STATUS_PIN=23
LED_ERROR_PIN=24
EOF
    
    # Set GPIO permissions
    sudo chmod 666 /dev/gpiochip0
    sudo usermod -a -G gpio $USER
    
    print_status "GPIO configuration completed"
}

# Function to configure system services
configure_services() {
    print_status "Configuring system services..."
    
    # Disable unnecessary services
    sudo systemctl disable bluetooth
    sudo systemctl disable cups
    sudo systemctl disable cups-browsed
    
    # Enable required services
    sudo systemctl enable ssh
    sudo systemctl enable networking
    
    print_status "System services configured"
}

# Function to configure auto-login
configure_autologin() {
    print_status "Configuring auto-login..."
    
    # Configure auto-login for GUI
    sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
    sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER --noclear %I \$TERM
EOF
    
    # Configure auto-start X
    echo "if [[ -z \$DISPLAY ]] && [[ \$(tty) = /dev/tty1 ]]; then
    exec startx
fi" >> ~/.bashrc
    
    print_status "Auto-login configured"
}

# Function to configure kiosk mode
configure_kiosk() {
    print_status "Configuring kiosk mode..."
    
    # Create kiosk startup script
    sudo tee /usr/local/bin/myrvm-kiosk.sh > /dev/null << 'EOF'
#!/bin/bash

# Disable screen saver
xset s off
xset -dpms
xset s noblank

# Hide cursor
unclutter -idle 0.5 -root &

# Start MyRVM GUI
cd /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
source venv/bin/activate
python3 gui/gui_client.py &

# Start browser in kiosk mode
sleep 5
chromium-browser \
    --kiosk \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --user-data-dir=/tmp/chrome_myrvm \
    --disable-infobars \
    --disable-extensions \
    --disable-plugins \
    --disable-web-security \
    --disable-features=TranslateUI \
    --disable-ipc-flooding-protection \
    http://localhost:5001
EOF
    
    sudo chmod +x /usr/local/bin/myrvm-kiosk.sh
    
    # Configure X to start kiosk mode
    echo "exec /usr/local/bin/myrvm-kiosk.sh" > ~/.xinitrc
    
    print_status "Kiosk mode configured"
}

# Function to test hardware configuration
test_hardware_config() {
    print_status "Testing hardware configuration..."
    
    # Test display
    if xrandr --listmonitors >/dev/null 2>&1; then
        print_status "Display: OK"
    else
        print_warning "Display: Not working"
    fi
    
    # Test touch
    if [ -e "$TOUCH_DEVICE" ]; then
        print_status "Touch: Device found"
    else
        print_warning "Touch: Device not found"
    fi
    
    # Test camera
    if [ -e "$CAMERA_DEVICE" ]; then
        print_status "Camera: Device found"
    else
        print_warning "Camera: Device not found"
    fi
    
    # Test GPIO
    if [ -e "/dev/gpiochip0" ]; then
        print_status "GPIO: Available"
    else
        print_warning "GPIO: Not available"
    fi
    
    print_status "Hardware configuration test completed"
}

# Function to display configuration summary
display_summary() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  HARDWARE CONFIGURATION COMPLETED${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Configuration Details:${NC}"
    echo -e "  Location: $LOCATION_NAME"
    echo -e "  RVM ID: $RVM_ID"
    echo -e "  Display: $DISPLAY_RESOLUTION"
    echo -e "  Touch Device: $TOUCH_DEVICE"
    echo -e "  Camera Device: $CAMERA_DEVICE"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "  1. Reboot the system: sudo reboot"
    echo -e "  2. System will auto-login and start kiosk mode"
    echo -e "  3. MyRVM GUI will be displayed on the touchscreen"
    echo ""
    echo -e "${BLUE}Manual Commands:${NC}"
    echo -e "  Start kiosk mode: /usr/local/bin/myrvm-kiosk.sh"
    echo -e "  Test display: xrandr --listmonitors"
    echo -e "  Test touch: evtest $TOUCH_DEVICE"
    echo -e "  Test camera: v4l2-ctl --list-devices"
    echo ""
}

# Main configuration function
main() {
    print_status "Starting hardware configuration for $LOCATION_NAME"
    
    configure_display
    configure_touch
    configure_camera
    configure_network
    configure_gpio
    configure_services
    configure_autologin
    configure_kiosk
    test_hardware_config
    display_summary
    
    print_status "Hardware configuration completed successfully!"
}

# Run main function
main "$@"
