# Timezone Synchronization - No Sudo Setup

## 📋 **Overview**

Panduan lengkap untuk setup timezone synchronization service di Jetson Orin Nano **TANPA menggunakan sudo permissions**. Menggunakan pendekatan user-level timezone management.

## 🎯 **Pendekatan No-Sudo**

### **✅ Keuntungan:**
1. **Tidak memerlukan sudo permissions**
2. **User-level configuration**
3. **Environment variable based**
4. **Systemd user services**
5. **Aman dan tidak mengubah system settings**

### **✅ Fitur yang Tersedia:**
1. **Automatic timezone detection** - Berdasarkan IP public
2. **Manual sync** - Dashboard button support
3. **Daily auto sync** - Systemd user timer
4. **Fallback mechanism** - UTC+7 (Asia/Jakarta)
5. **Comprehensive logging** - Full logging system
6. **MyRVM Platform integration** - API ready

## 🔧 **Setup Instructions**

### **1. Install Dependencies**
```bash
cd /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
source venv/bin/activate
pip install pytz
```

### **2. Setup Environment-based Configuration**
```bash
# Run the no-sudo setup script
./scripts/setup_timezone_env.sh
```

### **3. Test No-Sudo Service**
```bash
# Test timezone detection
python services/timezone_sync_service_no_sudo.py --test

# Test manual sync
python services/timezone_sync_service_no_sudo.py --manual-sync

# Check service status
python services/timezone_sync_service_no_sudo.py --status
```

### **4. Check Systemd User Service**
```bash
# Check timer status
systemctl --user status timezone-sync.timer

# Check service logs
journalctl --user -u timezone-sync.service -f

# Check last run
systemctl --user list-timers timezone-sync.timer
```

## 📁 **File Structure**

```
services/
├── timezone_sync_service_no_sudo.py    # No-sudo timezone sync service
└── ...

scripts/
├── setup_timezone_env.sh               # Environment-based setup
└── ...

~/.config/
├── myrvm-integration/
│   └── timezone.conf                   # User timezone configuration
└── systemd/user/
    ├── timezone-sync.service           # User systemd service
    └── timezone-sync.timer             # User systemd timer

~/.bashrc                               # TZ environment variable
~/.profile                              # TZ environment variable
```

## 🚀 **Usage Examples**

### **Command Line Usage**
```bash
# Automatic sync (for systemd user service)
python services/timezone_sync_service_no_sudo.py --auto-sync

# Manual sync (for dashboard button)
python services/timezone_sync_service_no_sudo.py --manual-sync

# Check status
python services/timezone_sync_service_no_sudo.py --status

# Test mode
python services/timezone_sync_service_no_sudo.py --test
```

### **Python Code Usage**
```python
from services.timezone_sync_service_no_sudo import TimezoneSyncServiceNoSudo

# Create no-sudo service
config = {"environment": "development"}
tz_service = TimezoneSyncServiceNoSudo(config)

# Get current timezone info
status = tz_service.get_status()
print(f"Current timezone: {status['current_timezone']}")
print(f"Local time: {status['local_time']['local_time']}")

# Manual sync
success, time_info = tz_service.manual_sync()
if success:
    print("✅ Timezone sync successful!")
```

## 🔄 **Service Configuration**

### **User Systemd Service**
```ini
[Unit]
Description=MyRVM Platform Timezone Sync Service (User)
After=graphical-session.target

[Service]
Type=oneshot
Environment=TZ=Asia/Jakarta
WorkingDirectory=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration
ExecStart=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration/venv/bin/python /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/services/timezone_sync_service_no_sudo.py --auto-sync
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

### **User Systemd Timer**
```ini
[Unit]
Description=MyRVM Platform Timezone Sync Timer (User)
Requires=timezone-sync.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=24h
Persistent=true

[Install]
WantedBy=timers.target
```

### **Environment Configuration**
```bash
# ~/.bashrc
export TZ="Asia/Jakarta"

# ~/.profile
export TZ="Asia/Jakarta"

# ~/.config/myrvm-integration/timezone.conf
TZ=Asia/Jakarta
TIMEZONE=Asia/Jakarta
COUNTRY=Indonesia
CITY=Jakarta
UTC_OFFSET=+0700
```

## 📊 **Test Results**

### **✅ Successful Tests:**
- **Timezone Detection**: ✅ **PASSED** (Asia/Jakarta detected)
- **Public IP**: 182.8.226.59 (Indonesia, Magelang)
- **Local Time**: 2025-09-19 03:36:36 WIB
- **UTC Offset**: +0700
- **Manual Sync**: ✅ **PASSED**
- **Auto Sync**: ✅ **PASSED**
- **Systemd User Service**: ✅ **PASSED**

### **✅ Service Status:**
```
Timezone Service Status (No Sudo):
current_timezone: Asia/Jakarta
fallback_timezone: Asia/Jakarta
last_sync: 2025-09-19T03:36:36.956000
should_sync: False
local_time: {'local_time': '2025-09-19 03:36:36', 'utc_time': '2025-09-18 20:36:36', 'timezone': 'Asia/Jakarta', 'utc_offset': '+0700', 'timezone_name': 'WIB'}
service_status: active_no_sudo
user_tz: Asia/Jakarta
```

## 🔧 **Technical Implementation**

### **User-level Timezone Management**
```python
def set_user_timezone(self, timezone_str: str) -> bool:
    """Set user-level timezone (no sudo required)."""
    try:
        # Set TZ environment variable
        os.environ['TZ'] = timezone_str
        
        # Update time.tzset() if available
        try:
            import time
            time.tzset()
        except AttributeError:
            # time.tzset() not available on all systems
            pass
        
        return True
    except Exception as e:
        self.logger.error(f"Failed to set user timezone: {e}")
        return False
```

### **Environment Variable Integration**
```python
def get_status(self) -> Dict[str, Any]:
    """Get timezone sync service status."""
    return {
        'current_timezone': self.current_timezone,
        'fallback_timezone': self.fallback_timezone,
        'last_sync': self.last_sync.isoformat() if self.last_sync else None,
        'should_sync': self.should_sync(),
        'local_time': self.get_local_time(),
        'service_status': 'active_no_sudo',
        'user_tz': os.environ.get('TZ', 'UTC')
    }
```

## 📈 **Monitoring & Logging**

### **Log Files**
- **Daily Logs**: `logs/timezone_sync_YYYYMMDD.log`
- **Change Events**: `logs/timezone_changes.jsonl`
- **Systemd User Logs**: `journalctl --user -u timezone-sync.service`

### **Check Service Status**
```bash
# Check timer status
systemctl --user status timezone-sync.timer

# Check service logs
journalctl --user -u timezone-sync.service -f

# Check last run
systemctl --user list-timers timezone-sync.timer

# Check environment
echo $TZ
date
```

## 🎯 **Integration with MyRVM Platform**

### **API Endpoints (Ready for implementation)**
```http
POST /api/v2/timezone-sync
Content-Type: application/json

{
  "device_id": "jetson_orin_nano",
  "event": "timezone_sync",
  "timezone": "Asia/Jakarta",
  "country": "Indonesia",
  "city": "Magelang",
  "ip": "182.8.226.59",
  "timestamp": "2025-09-19T03:36:36",
  "sync_method": "automatic_no_sudo"
}
```

### **Dashboard Integration (Ready for implementation)**
```html
<div class="timezone-widget">
  <h3>Device Local Time (No Sudo)</h3>
  <div class="time-display">
    <span id="local-time">2025-09-19 03:36:36</span>
    <span id="timezone">Asia/Jakarta (WIB)</span>
  </div>
  <div class="timezone-info">
    <p>Country: Indonesia</p>
    <p>City: Magelang</p>
    <p>Last Sync: 2025-09-19 03:36:36</p>
    <p>Method: No Sudo</p>
  </div>
  <button id="sync-button" onclick="manualSync()">
    Sync Timezone
  </button>
</div>
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Service Not Starting**
```bash
# Check user systemd service
systemctl --user status timezone-sync.service

# Check logs
journalctl --user -u timezone-sync.service

# Restart service
systemctl --user restart timezone-sync.timer
```

#### **2. Environment Variable Not Set**
```bash
# Check TZ variable
echo $TZ

# Reload environment
source ~/.bashrc

# Check timezone
date
```

#### **3. Timezone Detection Failed**
```bash
# Test manual detection
python services/timezone_sync_service_no_sudo.py --test

# Check network connectivity
ping ipapi.co

# Check fallback timezone
python -c "from services.timezone_sync_service_no_sudo import TimezoneSyncServiceNoSudo; print(TimezoneSyncServiceNoSudo({}).get_timezone_info())"
```

### **Debug Commands**
```bash
# Test timezone detection
python services/timezone_sync_service_no_sudo.py --test

# Check service status
python services/timezone_sync_service_no_sudo.py --status

# Manual sync
python services/timezone_sync_service_no_sudo.py --manual-sync

# Check systemd user service
systemctl --user cat timezone-sync.service
systemctl --user cat timezone-sync.timer
```

## 🎉 **Success Metrics**

### **✅ Completed Features**
- [x] No-sudo timezone detection
- [x] User-level timezone management
- [x] Environment variable configuration
- [x] Systemd user service integration
- [x] Daily automatic sync
- [x] Manual sync capability
- [x] Fallback to Asia/Jakarta
- [x] Comprehensive logging
- [x] Test framework
- [x] MyRVM Platform API ready

### **✅ Test Results**
- **Timezone Detection**: ✅ PASSED
- **Manual Sync**: ✅ PASSED
- **Auto Sync**: ✅ PASSED
- **Systemd User Service**: ✅ PASSED
- **Environment Integration**: ✅ PASSED

## 📝 **Next Steps**

### **Phase 1: MyRVM Platform Integration**
1. **API Endpoints**: Implement timezone sync endpoints
2. **Dashboard Widget**: Add timezone display and sync button
3. **Database Schema**: Add timezone tables

### **Phase 2: Production Deployment**
1. **Service Installation**: Deploy to production
2. **Monitoring Setup**: Configure monitoring and alerting
3. **Documentation**: Complete user documentation

## 🎯 **Conclusion**

Timezone synchronization feature telah berhasil diimplementasikan **TANPA menggunakan sudo permissions** dengan:

- ✅ **No-Sudo Service**: TimezoneSyncServiceNoSudo
- ✅ **User-level Management**: Environment variable based
- ✅ **Systemd User Integration**: User services and timers
- ✅ **Automatic Detection**: IP-based timezone detection
- ✅ **Manual Sync**: Dashboard button support
- ✅ **Fallback Mechanism**: UTC+7 (Asia/Jakarta)
- ✅ **Comprehensive Logging**: Full logging system
- ✅ **MyRVM Platform Ready**: API integration ready

**Status**: No-sudo implementation COMPLETED, MyRVM Platform integration PENDING

**Keuntungan**: Tidak memerlukan sudo permissions, aman, dan mudah di-deploy.

---

**Last Updated**: September 19, 2025  
**Status**: No-Sudo Implementation COMPLETED
