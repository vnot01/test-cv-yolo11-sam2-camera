# Remote Camera & GUI Services
## MyRVM Platform Integration

---

## 📋 **OVERVIEW**

This document describes the Remote Camera and GUI Services implementation for MyRVM Platform integration on Jetson Orin.

### **Services Included:**

1. **Remote Camera Service** (Port 5000)
   - Live camera streaming
   - Camera control (start/stop/restart)
   - Image capture
   - Integration with MyRVM Platform

2. **Remote GUI Service** (Port 5001)
   - System monitoring dashboard
   - Service management
   - Camera control panel
   - API connectivity status

---

## 🚀 **QUICK START**

### **1. Installation**
```bash
cd /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
./scripts/install_remote_services.sh
```

### **2. Start Services**
```bash
./scripts/start_remote_services.sh
```

### **3. Test Services**
```bash
./scripts/test_remote_services.sh
```

### **4. Access Services**
- **Camera**: http://172.28.93.97:5000
- **GUI**: http://172.28.93.97:5001

---

## 📁 **FILE STRUCTURE**

```
myrvm-integration/
├── services/
│   ├── remote_camera_service.py      # Camera service
│   └── remote_gui_service.py         # GUI service
├── templates/
│   ├── remote_camera.html            # Camera interface
│   └── remote_gui.html               # GUI interface
├── systemd/
│   ├── rvm-remote-camera.service     # Camera systemd service
│   └── rvm-remote-gui.service        # GUI systemd service
├── scripts/
│   ├── install_remote_services.sh    # Installation script
│   ├── start_remote_services.sh      # Start services
│   ├── test_remote_services.sh       # Test services
│   └── run_all_services.sh           # Run all services
└── docs/
    └── Add Fitur/
        └── 2/
            └── REMOTE_CAMERA_AND_GUI_IMPLEMENTATION.md
```

---

## 🔧 **SERVICE DETAILS**

### **Remote Camera Service (Port 5000)**

**Features:**
- ✅ Live camera streaming
- ✅ Camera control (start/stop/restart)
- ✅ Image capture
- ✅ Integration with MyRVM Platform
- ✅ Real-time statistics

**Endpoints:**
- `GET /` - Main camera interface
- `GET /video_feed` - Live camera stream
- `GET /camera_info` - Camera information
- `GET /capture` - Capture current frame
- `POST /control` - Camera control
- `GET /status` - Service status

**Usage:**
```bash
# Start service
sudo systemctl start rvm-remote-camera

# Check status
sudo systemctl status rvm-remote-camera

# View logs
sudo journalctl -u rvm-remote-camera -f
```

### **Remote GUI Service (Port 5001)**

**Features:**
- ✅ System monitoring dashboard
- ✅ Service management
- ✅ Camera control panel
- ✅ API connectivity status
- ✅ Real-time metrics

**Endpoints:**
- `GET /` - Main dashboard
- `GET /dashboard` - Dashboard data
- `GET /system/status` - System status
- `GET /system/metrics` - System metrics
- `POST /system/control` - System control
- `GET /camera/control` - Camera control panel
- `GET /api/status` - API status
- `GET /logs` - System logs

**Usage:**
```bash
# Start service
sudo systemctl start rvm-remote-gui

# Check status
sudo systemctl status rvm-remote-gui

# View logs
sudo journalctl -u rvm-remote-gui -f
```

---

## 🌐 **MYRVM PLATFORM INTEGRATION**

### **Ping Test Implementation**

Update your MyRVM Platform ping logic to test both ports:

```php
private function performPing($ip, $port = 8000)
{
    $startTime = microtime(true);
    
    // Handle dummy data (0.0.0.0)
    if ($ip === '0.0.0.0' || $ip === 'localhost' || $ip === '127.0.0.1') {
        $responseTime = round((microtime(true) - $startTime) * 1000, 2);
        return [
            'success' => true,
            'message' => 'Dummy data - No actual connection test',
            'response_time' => $responseTime,
            'is_dummy' => true
        ];
    }
    
    // Test multiple ports for RVM services
    $ports = [5000, 5001]; // Camera and GUI services
    $results = [];
    
    foreach ($ports as $testPort) {
        try {
            $connection = @fsockopen($ip, $testPort, $errno, $errstr, 5);
            
            if ($connection) {
                $responseTime = round((microtime(true) - $startTime) * 1000, 2);
                fclose($connection);
                
                $results[$testPort] = [
                    'success' => true,
                    'message' => 'Connection successful',
                    'response_time' => $responseTime
                ];
            } else {
                $results[$testPort] = [
                    'success' => false,
                    'message' => "Connection failed: $errstr ($errno)"
                ];
            }
        } catch (\Exception $e) {
            $results[$testPort] = [
                'success' => false,
                'message' => 'Connection error: ' . $e->getMessage()
            ];
        }
    }
    
    // Return combined results
    return [
        'success' => !empty(array_filter($results, fn($r) => $r['success'])),
        'message' => 'Multi-port test completed',
        'ports' => $results,
        'is_dummy' => false
    ];
}
```

### **Remote Access URLs**

For each RVM, you can now provide:
- **Camera Access**: `http://{RVM_IP}:5000`
- **GUI Access**: `http://{RVM_IP}:5001`

---

## 🛠️ **TROUBLESHOOTING**

### **Common Issues:**

1. **Port 5000/5001 not accessible**
   ```bash
   # Check if services are running
   sudo systemctl status rvm-remote-camera rvm-remote-gui
   
   # Check if ports are listening
   netstat -tlnp | grep -E '(5000|5001)'
   
   # Check firewall
   sudo ufw status
   ```

2. **Camera not working**
   ```bash
   # Check camera permissions
   ls -la /dev/video*
   
   # Test camera manually
   python3 services/remote_camera_service.py
   ```

3. **Services not starting**
   ```bash
   # Check service logs
   sudo journalctl -u rvm-remote-camera -f
   sudo journalctl -u rvm-remote-gui -f
   
   # Check Python dependencies
   pip3 list | grep -E "(flask|opencv|psutil)"
   ```

### **Manual Service Start:**

If systemd services fail, you can start services manually:

```bash
# Start camera service
cd /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
python3 services/remote_camera_service.py &

# Start GUI service
python3 services/remote_gui_service.py &
```

---

## 📊 **MONITORING**

### **Service Status:**
```bash
# Check all services
sudo systemctl status rvm-remote-camera rvm-remote-gui

# Check ports
netstat -tlnp | grep -E '(5000|5001)'

# Check processes
ps aux | grep -E "(remote_camera|remote_gui)"
```

### **Logs:**
```bash
# Service logs
sudo journalctl -u rvm-remote-camera -f
sudo journalctl -u rvm-remote-gui -f

# Application logs
tail -f logs/remote_camera_*.log
tail -f logs/remote_gui_*.log
```

### **Performance:**
```bash
# System resources
htop

# Network connections
ss -tlnp | grep -E '(5000|5001)'

# Disk usage
df -h
```

---

## 🔒 **SECURITY**

### **Current Security Measures:**
- ✅ Service isolation with systemd
- ✅ Limited file system access
- ✅ No root privileges
- ✅ Log rotation

### **Recommended Additional Security:**
- 🔒 HTTPS/TLS encryption
- 🔒 Authentication tokens
- 🔒 Firewall rules
- 🔒 VPN access only

---

## 📈 **PERFORMANCE**

### **Resource Usage:**
- **Camera Service**: ~50-100MB RAM, 10-20% CPU
- **GUI Service**: ~30-50MB RAM, 5-10% CPU
- **Network**: ~1-5 Mbps for camera stream

### **Optimization:**
- Adjust camera resolution in `remote_camera_service.py`
- Modify frame rate for bandwidth optimization
- Use hardware acceleration if available

---

## 🎯 **NEXT STEPS**

1. **Test the services** with the provided scripts
2. **Update MyRVM Platform** ping logic
3. **Configure firewall** rules if needed
4. **Set up monitoring** and alerting
5. **Implement security** measures
6. **Performance optimization** based on usage

---

**Created**: 2025-01-19
**Status**: Ready for Implementation
**Priority**: High
