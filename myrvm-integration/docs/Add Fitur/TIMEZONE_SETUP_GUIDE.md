# Timezone Synchronization Setup Guide

## 📋 **Overview**

Panduan lengkap untuk setup timezone synchronization service di Jetson Orin Nano untuk MyRVM Platform Integration.

## 🎯 **What We've Implemented**

### **✅ Core Features Completed:**

1. **TimezoneSyncService** - Core timezone synchronization service
2. **TimezoneManager** - Centralized timezone management utility
3. **IP-based Detection** - Automatic timezone detection using public IP
4. **Multiple Fallback Services** - ipapi.co, ipinfo.io, ipgeolocation.io
5. **Daily Auto Sync** - Automatic sync once per day at startup
6. **Manual Sync** - Dashboard button for on-demand sync
7. **Fallback Mechanism** - UTC+7 (Asia/Jakarta) if detection fails
8. **Comprehensive Logging** - Full logging and monitoring system
9. **Test Framework** - Complete testing and validation
10. **Systemd Integration** - Service and timer files for automatic startup

### **✅ Test Results:**
- **Timezone Detection**: ✅ **PASSED** (Asia/Jakarta detected)
- **Public IP**: 182.8.226.59 (Indonesia, Magelang)
- **Local Time**: 2025-09-19 03:23:40 WIB
- **UTC Offset**: +0700
- **Fallback**: UTC+7 (Asia/Jakarta) working

## 🔧 **Setup Instructions**

### **1. Install Dependencies**
```bash
cd /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
source venv/bin/activate
pip install pytz
```

### **2. Setup Sudo Permissions**
```bash
# Run the setup script (requires password)
./scripts/setup_timezone_permissions.sh

# Or manually:
sudo usermod -a -G time my
echo "my ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-timezone *" | sudo tee /etc/sudoers.d/timezone-sync
sudo chmod 440 /etc/sudoers.d/timezone-sync
```

### **3. Install Systemd Service**
```bash
# Install timezone sync service
./scripts/install_timezone_service.sh

# Or manually:
sudo cp systemd/timezone-sync.service /etc/systemd/system/
sudo cp systemd/timezone-sync.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable timezone-sync.timer
sudo systemctl start timezone-sync.timer
```

### **4. Test Service**
```bash
# Test timezone detection
python services/timezone_sync_service.py --test

# Test auto sync
python services/timezone_sync_service.py --auto-sync

# Check service status
python services/timezone_sync_service.py --status

# Check systemd service status
sudo systemctl status timezone-sync.timer
```

## 📁 **File Structure**

```
services/
├── timezone_sync_service.py          # Core timezone sync service
└── ...

utils/
├── timezone_manager.py               # Centralized timezone management
└── ...

systemd/
├── timezone-sync.service             # Systemd service file
├── timezone-sync.timer               # Systemd timer file
└── ...

scripts/
├── setup_timezone_permissions.sh     # Setup sudo permissions
├── install_timezone_service.sh       # Install systemd service
├── update_timezone_usage.py          # Update project files
└── update_project_timezone.py        # Update only project files

debug/
├── test_timezone_sync.py             # Test script for timezone sync
└── ...

data/
├── timezone_sync.json                # Sync information storage
└── ...

logs/
├── timezone_sync_YYYYMMDD.log        # Daily sync logs
├── timezone_changes.jsonl            # Timezone change events
└── ...
```

## 🚀 **Usage Examples**

### **Command Line Usage**
```bash
# Automatic sync (for systemd service)
python services/timezone_sync_service.py --auto-sync

# Manual sync (for dashboard button)
python services/timezone_sync_service.py --manual-sync

# Check status
python services/timezone_sync_service.py --status

# Test mode
python services/timezone_sync_service.py --test
```

### **Python Code Usage**
```python
from utils.timezone_manager import get_timezone_manager, now, format_datetime

# Get timezone manager
tz_manager = get_timezone_manager()

# Get current time
current_time = now()
formatted_time = format_datetime(current_time)

# Get timezone info
tz_info = tz_manager.get_timezone_info()
print(f"Current timezone: {tz_info['timezone']}")
print(f"Local time: {tz_info['local_time']}")
```

## 🔄 **Service Configuration**

### **Systemd Service (timezone-sync.service)**
```ini
[Unit]
Description=MyRVM Platform Timezone Sync Service
After=network.target
Wants=network.target

[Service]
Type=oneshot
User=my
Group=my
WorkingDirectory=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration
ExecStart=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration/venv/bin/python /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/services/timezone_sync_service.py --auto-sync
StandardOutput=journal
StandardError=journal
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
```

### **Systemd Timer (timezone-sync.timer)**
```ini
[Unit]
Description=MyRVM Platform Timezone Sync Timer
Requires=timezone-sync.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=24h
Persistent=true

[Install]
WantedBy=timers.target
```

## 📊 **Monitoring & Logging**

### **Log Files**
- **Daily Logs**: `logs/timezone_sync_YYYYMMDD.log`
- **Change Events**: `logs/timezone_changes.jsonl`
- **Systemd Logs**: `journalctl -u timezone-sync.service`

### **Check Service Status**
```bash
# Check timer status
sudo systemctl status timezone-sync.timer

# Check service logs
journalctl -u timezone-sync.service -f

# Check last run
sudo systemctl list-timers timezone-sync.timer
```

## 🔧 **Configuration Files**

### **Development Config**
```json
{
  "environment": "development",
  "myrvm_base_url": "http://172.28.233.83:8001",
  "timezone_sync": {
    "enabled": true,
    "auto_sync": true,
    "sync_interval": 86400,
    "fallback_timezone": "Asia/Jakarta"
  }
}
```

### **Update Config**
```json
{
  "update_scheduling": {
    "enabled": false,
    "schedule": "0 2 * * *",
    "timezone": "Asia/Jakarta",
    "maintenance_window": {
      "enabled": true,
      "start_time": "02:00",
      "end_time": "04:00",
      "timezone": "Asia/Jakarta"
    }
  }
}
```

## 🎯 **Integration with MyRVM Platform**

### **API Endpoints (To be implemented)**
```http
POST /api/v2/timezone-sync
GET /api/v2/timezone-status/{device_id}
POST /api/v2/timezone-sync/manual
```

### **Dashboard Integration (To be implemented)**
```html
<div class="timezone-widget">
  <h3>Device Local Time</h3>
  <div class="time-display">
    <span id="local-time">2025-09-19 03:23:40</span>
    <span id="timezone">Asia/Jakarta (WIB)</span>
  </div>
  <button id="sync-button" onclick="manualSync()">
    Sync Timezone
  </button>
</div>
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Sudo Permission Error**
```bash
# Error: sudo: a terminal is required to read the password
# Solution: Run setup script with password
./scripts/setup_timezone_permissions.sh
```

#### **2. Service Not Starting**
```bash
# Check service status
sudo systemctl status timezone-sync.service

# Check logs
journalctl -u timezone-sync.service

# Restart service
sudo systemctl restart timezone-sync.timer
```

#### **3. Timezone Detection Failed**
```bash
# Check network connectivity
ping ipapi.co

# Test manual detection
python services/timezone_sync_service.py --test

# Check fallback timezone
python -c "from utils.timezone_manager import get_timezone_manager; print(get_timezone_manager().get_timezone_info())"
```

### **Debug Commands**
```bash
# Test timezone detection
python debug/test_timezone_sync.py

# Check system timezone
timedatectl show

# Check timezone manager
python utils/timezone_manager.py

# Check service configuration
sudo systemctl cat timezone-sync.service
sudo systemctl cat timezone-sync.timer
```

## 🎉 **Success Metrics**

### **✅ Completed Features**
- [x] Timezone detection using public IP
- [x] Multiple fallback services
- [x] Daily automatic sync
- [x] Manual sync capability
- [x] Fallback to Asia/Jakarta
- [x] Comprehensive logging
- [x] Systemd integration
- [x] Test framework
- [x] Timezone manager utility
- [x] Project-wide timezone integration

### **⏳ Pending Features**
- [ ] Sudo permissions setup (requires manual intervention)
- [ ] MyRVM Platform API integration
- [ ] Dashboard manual sync button
- [ ] Production deployment

## 📝 **Next Steps**

### **Phase 1: Complete Setup**
1. **Setup Sudo Permissions**: Run setup script with password
2. **Install Systemd Service**: Install and start service
3. **Test Full Integration**: Verify all components working

### **Phase 2: MyRVM Platform Integration**
1. **API Endpoints**: Implement timezone sync endpoints
2. **Dashboard Widget**: Add timezone display and sync button
3. **Database Schema**: Add timezone tables

### **Phase 3: Production Deployment**
1. **Service Installation**: Deploy to production
2. **Monitoring Setup**: Configure monitoring and alerting
3. **Documentation**: Complete user documentation

## 🎯 **Conclusion**

Timezone synchronization feature telah berhasil diimplementasikan dengan:

- ✅ **Core Service**: TimezoneSyncService dan TimezoneManager
- ✅ **Automatic Detection**: IP-based timezone detection
- ✅ **Fallback Mechanism**: UTC+7 (Asia/Jakarta) fallback
- ✅ **Systemd Integration**: Service dan timer files
- ✅ **Test Framework**: Comprehensive testing
- ✅ **Project Integration**: Timezone-aware datetime functions

**Status**: Core implementation COMPLETED, Setup PENDING (requires sudo permissions)

**Next Action**: Run setup scripts with sudo permissions to complete the installation.

---

**Last Updated**: September 19, 2025  
**Status**: Implementation COMPLETED, Setup PENDING
