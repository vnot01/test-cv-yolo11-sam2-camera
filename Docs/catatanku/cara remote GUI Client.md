# Cara Remote GUI Client - MyRVM Application

## 1. Start MyRVM Application
```bash
# Option 1: Using deployment script (recommended)
cd /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
./scripts/deploy.sh

# Option 2: Using start script (development)
./scripts/start.sh

# Option 3: Manual start
cd /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
source venv/bin/activate
python main_application.py
```

## 2. Start GUI Client for LED Touch Screen
```bash
# Using the safe browser script
cd /home/my/test-cv-yolo11-sam2-camera
./scripts/start_gui_client.sh
```

## 3. Manual Browser Launch (Alternative)
```bash
# Safe Chromium launch (fixes SELinux error)
chromium-browser \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --kiosk \
    --disable-infobars \
    --user-data-dir=/tmp/chrome_myrvm \
    http://localhost:5001

# Or using Firefox
firefox --kiosk http://localhost:5001
```

## 4. Access URLs
- **Local**: http://localhost:5001
- **Network**: http://192.168.1.11:5001
- **LED Touch Screen**: Use kiosk mode for full screen

## 5. Troubleshooting
- **SELinux Error**: Use `--no-sandbox` flag
- **Capabilities Error**: Use `--disable-dev-shm-usage` flag
- **GUI Not Loading**: Check if MyRVM Application is running
- **Touch Not Working**: Ensure touch screen drivers are installed

## 6. Service Management
```bash
# Check status
sudo systemctl status myrvm-application

# Restart service
sudo systemctl restart myrvm-application

# View logs
sudo journalctl -u myrvm-application -f
```