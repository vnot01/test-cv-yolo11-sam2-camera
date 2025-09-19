# Remote Camera & GUI Implementation
## Technical Documentation for Jetson Orin Integration

---

## 📋 **STATUS ANALISIS**

### **✅ YANG SUDAH ADA:**

1. **Camera SAM2 Integration (Port 5000) - ON-DEMAND**
   - **Lokasi**: `/home/my/test-cv-yolo11-sam2-camera/cv-camera/camera_sam2_integration.py`
   - **Fungsi**: Live camera streaming + SAM2 detection dengan Flask
   - **Port**: 5000
   - **Akses**: `http://172.28.93.97:5000`
   - **Status**: ✅ **SUDAH ADA** - **ON-DEMAND ACTIVATION**
   - **Fitur**: Camera streaming, SAM2 detection, image capture, real-time statistics

2. **Monitoring Dashboard (Port 5001)**
   - **Lokasi**: `/home/my/test-cv-yolo11-sam2-camera/myrvm-integration/monitoring/dashboard_server.py`
   - **Fungsi**: Real-time monitoring dashboard
   - **Port**: 5001
   - **Akses**: `http://172.28.93.97:5001`
   - **Status**: ✅ **SUDAH ADA** tapi belum terintegrasi

3. **Camera Service (Internal)**
   - **Lokasi**: `/home/my/test-cv-yolo11-sam2-camera/myrvm-integration/services/camera_service.py`
   - **Fungsi**: Internal camera processing
   - **Status**: ✅ **SUDAH ADA** untuk internal processing

### **❌ YANG BELUM ADA:**

1. **On-Demand Camera Activation** - Service untuk mengaktifkan kamera saat dibutuhkan
2. **Remote Access Integration** - API endpoint untuk remote access dari MyRVM Platform
3. **Session Management** - Manajemen session remote access (1 jam timeout)
4. **RVM Status Management** - Auto-change status ke maintenance saat remote access
5. **GUI Integration** - Interface untuk remote control

---

## 🚀 **IMPLEMENTASI YANG DIPERLUKAN**

### **1. On-Demand Camera Service Integration**

#### **A. Buat On-Demand Camera Manager**
```bash
# Lokasi: /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/services/ondemand_camera_manager.py
```

**Fitur yang diperlukan:**
- ✅ **On-Demand Activation** - Aktifkan kamera hanya saat dibutuhkan
- ✅ **Session Management** - Session timeout 1 jam
- ✅ **RVM Status Management** - Auto-change status ke maintenance saat remote access
- ✅ **Camera SAM2 Integration** - Menggunakan `camera_sam2_integration.py` yang sudah ada
- ✅ **Remote Access API** - API endpoint untuk remote access dari MyRVM Platform
- ✅ **Authentication** - Token validation untuk remote access
- ✅ **Auto-cleanup** - Auto-stop kamera dan restore status setelah session habis

#### **B. Buat Remote Access Controller**
```bash
# Lokasi: /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/services/remote_access_controller.py
```

**Fitur yang diperlukan:**
- ✅ **Remote Access Management** - Manage remote access sessions
- ✅ **Camera/GUI Selection** - Pilih akses kamera atau GUI
- ✅ **Session Tracking** - Track active remote sessions
- ✅ **Status Management** - Auto-change RVM status saat remote access
- ✅ **Timeout Management** - Auto-cleanup setelah 1 jam
- ✅ **Integration API** - API untuk MyRVM Platform integration

### **2. Service Integration**

#### **A. Update Enhanced Jetson Main**
```python
# File: /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/main/enhanced_jetson_main.py

# Tambahkan service baru:
from services.ondemand_camera_manager import OnDemandCameraManager
from services.remote_access_controller import RemoteAccessController

class EnhancedJetsonMain:
    def __init__(self):
        # ... existing code ...
        self.ondemand_camera_manager = OnDemandCameraManager(self.config)
        self.remote_access_controller = RemoteAccessController(self.config)
    
    def start_all_services(self):
        # ... existing code ...
        # Hanya start remote access controller, camera manager on-demand
        self.remote_access_controller.start()
        # Camera akan diaktifkan saat ada remote access request
```

#### **B. Update Configuration**
```json
// File: /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/main/config.json
{
  "remote_access": {
    "enabled": true,
    "controller_port": 5001,
    "host": "0.0.0.0",
    "authentication_required": true,
    "session_timeout": 3600,
    "camera_script": "/home/my/test-cv-yolo11-sam2-camera/cv-camera/camera_sam2_integration.py",
    "camera_port": 5000,
    "auto_status_change": true,
    "maintenance_status": "maintenance",
    "restore_status": "active"
  }
}
```

### **3. Systemd Service Files**

#### **A. Remote Access Controller Service**
```ini
# File: /etc/systemd/system/rvm-remote-access.service
[Unit]
Description=RVM Remote Access Controller
After=network.target

[Service]
Type=simple
User=my
WorkingDirectory=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration
ExecStart=/usr/bin/python3 -m services.remote_access_controller
Restart=always
RestartSec=10
Environment=PYTHONPATH=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration

[Install]
WantedBy=multi-user.target
```

**Note**: Camera service tidak perlu systemd karena akan diaktifkan on-demand melalui remote access controller.

### **4. API Endpoints yang Diperlukan**

#### **A. Remote Access Controller API**
```python
# Endpoints yang diperlukan:
POST /remote/start_camera    # Start camera session (on-demand)
POST /remote/stop_camera     # Stop camera session
GET  /remote/status          # Remote access status
GET  /remote/sessions        # Active sessions
POST /remote/extend_session  # Extend session timeout
GET  /remote/camera_url      # Get camera access URL
```

#### **B. MyRVM Platform Integration API**
```python
# Endpoints untuk MyRVM Platform:
POST /api/remote_access      # Request remote access
GET  /api/remote_status      # Check remote access status
POST /api/end_session        # End remote session
GET  /api/camera_available   # Check if camera is available
```

### **5. Security Implementation**

#### **A. Authentication**
```python
# Token-based authentication
- Generate unique tokens for each RVM
- Validate tokens on each request
- Implement token expiration
- Secure communication over HTTPS
```

#### **B. Access Control**
```python
# Role-based access control
- Admin: Full access
- Operator: Camera control only
- Viewer: Read-only access
```

---

## 🛠️ **IMPLEMENTATION STEPS**

### **Phase 1: On-Demand Camera Manager**
1. ✅ Create `ondemand_camera_manager.py`
2. ✅ Create `remote_access_controller.py`
3. ✅ Update `enhanced_jetson_main.py`
4. ✅ Update configuration files
5. ✅ Test on-demand camera activation

### **Phase 2: Session Management**
1. ✅ Implement session tracking
2. ✅ Implement 1-hour timeout
3. ✅ Auto-status change to maintenance
4. ✅ Auto-restore status after session

### **Phase 3: MyRVM Platform Integration**
1. ✅ Create API endpoints for remote access
2. ✅ Integrate with MyRVM Platform ping logic
3. ✅ Test remote access workflow
4. ✅ Implement authentication

### **Phase 4: Service Integration**
1. ✅ Create systemd service for remote access controller
2. ✅ Test service management
3. ✅ Implement error handling
4. ✅ Test camera SAM2 integration

### **Phase 5: Testing & Deployment**
1. ✅ Test complete remote access workflow
2. ✅ Test session timeout and cleanup
3. ✅ Test status management
4. ✅ Production deployment

---

## 📊 **TECHNICAL SPECIFICATIONS**

### **Port Usage**
- **Port 5000**: Camera SAM2 Integration (On-demand activation)
- **Port 5001**: Remote Access Controller (Always running)
- **Port 8000**: MyRVM Platform Communication (API calls)

### **Communication Flow**
```
MyRVM Platform (172.28.233.83:8001)
    ↓ HTTP API Calls
Jetson Orin (172.28.93.97)
    ├── Port 5001: Remote Access Controller (Always running)
    ├── Port 5000: Camera SAM2 Integration (On-demand only)
    └── Internal: Camera Service, Detection Service
```

### **On-Demand Workflow**
```
1. Admin clicks "Remote Access" in MyRVM Platform
2. MyRVM Platform calls Jetson Orin API (Port 5001)
3. Remote Access Controller starts Camera SAM2 (Port 5000)
4. RVM status changes to "maintenance"
5. Admin accesses camera via Port 5000
6. After 1 hour or manual stop, camera stops
7. RVM status returns to "active"
```

### **Dependencies**
- Flask (Web framework)
- OpenCV (Camera handling)
- WebSocket (Real-time communication)
- psutil (System monitoring)
- requests (HTTP client)

---

## 🎯 **EXPECTED OUTCOMES**

### **After Implementation:**
1. ✅ **On-Demand Camera Access**: `http://172.28.93.97:5000` (Only when needed)
2. ✅ **Remote Access Controller**: `http://172.28.93.97:5001` (Always running)
3. ✅ **Session Management**: 1-hour timeout with auto-cleanup
4. ✅ **Status Management**: Auto-change to maintenance during remote access
5. ✅ **Camera SAM2 Integration**: Full camera + SAM2 detection features
6. ✅ **Secure Access**: Token-based authentication
7. ✅ **Integration**: Seamless MyRVM Platform integration

### **MyRVM Platform Integration:**
1. ✅ **Ping Test**: Test connection to port 5001 (Remote Access Controller)
2. ✅ **Remote Access Request**: API call to start camera session
3. ✅ **Status Monitoring**: Real-time status updates
4. ✅ **Session Management**: Track and manage remote sessions
5. ✅ **Auto-cleanup**: Automatic session termination and status restore

---

## 📝 **NEXT STEPS**

1. **Review this updated documentation**
2. **Implement On-Demand Camera Manager** (Phase 1)
3. **Implement Session Management** (Phase 2)
4. **Test on-demand camera activation**
5. **Implement MyRVM Platform Integration** (Phase 3)
6. **Test complete remote access workflow**
7. **Deploy and test in production**

---

## 🔗 **RELATED FILES**

- `cv-camera/camera_sam2_integration.py` - **Main camera script (ON-DEMAND)**
- `monitoring/dashboard_server.py` - Existing dashboard (reference)
- `services/camera_service.py` - Internal camera service
- `main/enhanced_jetson_main.py` - Main coordinator
- `config.json` - Configuration file

---

## 🎯 **KEY BENEFITS OF ON-DEMAND APPROACH**

1. **Resource Efficiency**: Camera hanya aktif saat dibutuhkan
2. **Better Performance**: Tidak ada overhead dari camera yang selalu running
3. **Status Management**: RVM status otomatis berubah saat remote access
4. **Session Control**: Timeout 1 jam dengan auto-cleanup
5. **Existing Integration**: Menggunakan `camera_sam2_integration.py` yang sudah ada
6. **User Experience**: Interface yang sudah familiar (seperti gambar yang diupload)

---

**Created**: 2025-01-19
**Updated**: 2025-01-19 (On-Demand Approach)
**Status**: Ready for Implementation
**Priority**: High
**Estimated Time**: 1-2 days implementation
