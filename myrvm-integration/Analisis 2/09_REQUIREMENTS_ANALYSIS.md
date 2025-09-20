# REQUIREMENTS ANALYSIS - JETSON ORIN ↔ SERVER

**Tanggal**: 2025-01-20  
**Lokasi**: `/home/my/test-cv-yolo11-sam2-camera/myrvm-integration/Analisis 2/`  
**Tujuan**: Analisis requirements dari Jetson Orin ke Server dan sebaliknya

---

## **📁 OVERVIEW REQUIREMENTS ANALYSIS**

### **✅ BIDIRECTIONAL REQUIREMENTS:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    REQUIREMENTS ANALYSIS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   JETSON    │    │   SERVER    │    │   SERVER    │         │
│  │   ORIN      │    │ REQUIREMENTS│    │   TO        │         │
│  │             │    │   FROM      │    │   JETSON    │         │
│  │ • RVM       │    │   JETSON    │    │   ORIN      │         │
│  │   Status    │    │   ORIN      │    │             │         │
│  │ • Timezone  │    │             │    │ • API       │         │
│  │   Sync      │    │ • API       │    │   Endpoints │         │
│  │ • Remote    │    │   Endpoints │    │ • Database  │         │
│  │   Access    │    │ • Database  │    │   Schema    │         │
│  │ • Backup    │    │   Schema    │    │ • Services  │         │
│  │   Ops       │    │ • Services  │    │ • Config    │         │
│  │ • System    │    │ • Config    │    │             │         │
│  │   Monitor   │    │             │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## **🔍 DARI JETSON ORIN KE SERVER (REQUIREMENTS)**

### **1. 🎯 API ENDPOINTS YANG DIBUTUHKAN**

#### **A. RVM Status Management:**
```http
# Get RVM Status
GET /api/v2/rvms/{id}/status
Authorization: Bearer {token}

# Update RVM Status
PATCH /api/v2/rvms/{id}/status
Authorization: Bearer {token}
Content-Type: application/json
{
  "status": "active|inactive|maintenance|full|error|unknown"
}

# Get RVM Details
GET /api/v2/rvms/{id}
Authorization: Bearer {token}
```

#### **B. Timezone Sync:**
```http
# Sync Timezone
POST /api/v2/timezone/sync
Authorization: Bearer {token}
Content-Type: application/json
{
  "device_id": "jetson_orin_nano",
  "timezone": "Asia/Jakarta",
  "country": "Indonesia",
  "city": "Magelang",
  "ip": "182.8.226.59",
  "timestamp": "2025-01-20T10:30:00",
  "sync_method": "automatic|manual"
}

# Get Timezone Status
GET /api/v2/timezone/status/{device_id}
Authorization: Bearer {token}

# Manual Sync Trigger
POST /api/v2/timezone/sync/manual
Authorization: Bearer {token}
Content-Type: application/json
{
  "device_id": "jetson_orin_nano",
  "trigger": "dashboard_button"
}
```

#### **C. Remote Access:**
```http
# Start Remote Access
POST /api/v2/rvms/{id}/remote-access/start
Authorization: Bearer {token}
Content-Type: application/json
{
  "admin_id": 1,
  "ip_address": "192.168.1.100",
  "port": 5001
}

# Stop Remote Access
POST /api/v2/rvms/{id}/remote-access/stop
Authorization: Bearer {token}
Content-Type: application/json
{
  "admin_id": 1,
  "reason": "session_completed"
}

# Get Remote Access Status
GET /api/v2/rvms/{id}/remote-access/status
Authorization: Bearer {token}
```

#### **D. Backup Operations:**
```http
# Start Backup
POST /api/v2/rvms/{id}/backup/start
Authorization: Bearer {token}
Content-Type: application/json
{
  "backup_type": "full|incremental",
  "include_images": true,
  "include_logs": true
}

# Get Backup Status
GET /api/v2/rvms/{id}/backup/status
Authorization: Bearer {token}

# Upload Backup
POST /api/v2/rvms/{id}/backup/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data
{
  "file": "backup_file.tar.gz",
  "backup_type": "full|incremental"
}
```

#### **E. System Monitoring:**
```http
# Upload System Metrics
POST /api/v2/rvms/{id}/metrics
Authorization: Bearer {token}
Content-Type: application/json
{
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "disk_usage": 23.1,
  "gpu_usage": 12.5,
  "temperature": 65.0,
  "timestamp": "2025-01-20T10:30:00"
}

# Get System Metrics
GET /api/v2/rvms/{id}/metrics?days=7
Authorization: Bearer {token}
```

### **2. 🗄️ DATABASE SCHEMA YANG DIBUTUHKAN**

#### **A. RVM Status Table:**
```sql
CREATE TABLE reverse_vending_machines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    location_description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    special_status VARCHAR(20) NULL,
    capacity INTEGER DEFAULT 0,
    api_key VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Status values: active, inactive, maintenance, full, error, unknown
-- Special status: maintenance, inactive, error, unknown
```

#### **B. Timezone Sync Table:**
```sql
CREATE TABLE timezone_sync_logs (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    country VARCHAR(100),
    city VARCHAR(100),
    ip_address VARCHAR(45),
    sync_method VARCHAR(20) NOT NULL,
    sync_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE device_timezones (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    current_timezone VARCHAR(50) NOT NULL,
    country VARCHAR(100),
    city VARCHAR(100),
    last_sync TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **C. Remote Access Table:**
```sql
CREATE TABLE remote_access_sessions (
    id SERIAL PRIMARY KEY,
    rvm_id INTEGER NOT NULL,
    admin_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NULL,
    status VARCHAR(20) DEFAULT 'active',
    ip_address VARCHAR(45),
    port INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id),
    FOREIGN KEY (admin_id) REFERENCES users(id)
);
```

#### **D. Backup Logs Table:**
```sql
CREATE TABLE backup_logs (
    id SERIAL PRIMARY KEY,
    rvm_id INTEGER NOT NULL,
    backup_type VARCHAR(20) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    upload_status VARCHAR(20) DEFAULT 'pending',
    minio_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id)
);
```

#### **E. System Metrics Table:**
```sql
CREATE TABLE system_metrics (
    id SERIAL PRIMARY KEY,
    rvm_id INTEGER NOT NULL,
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    disk_usage DECIMAL(5,2),
    gpu_usage DECIMAL(5,2),
    temperature DECIMAL(5,2),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rvm_id) REFERENCES reverse_vending_machines(id)
);
```

### **3. 🔧 SERVICES YANG DIBUTUHKAN**

#### **A. RVM Status Service:**
- **Function**: Manage RVM status updates
- **Features**: Status checking, updating, validation
- **Integration**: Real-time status updates

#### **B. Timezone Sync Service:**
- **Function**: Handle timezone synchronization
- **Features**: Automatic sync, manual sync, status tracking
- **Integration**: IP-based timezone detection

#### **C. Remote Access Service:**
- **Function**: Manage remote access sessions
- **Features**: Session management, access control, monitoring
- **Integration**: Admin dashboard integration

#### **D. Backup Service:**
- **Function**: Handle backup operations
- **Features**: Backup scheduling, upload, status tracking
- **Integration**: MINIO storage integration

#### **E. System Monitoring Service:**
- **Function**: Collect and store system metrics
- **Features**: Metrics collection, storage, analysis
- **Integration**: Dashboard visualization

---

## **🔍 DARI SERVER KE JETSON ORIN (REQUIREMENTS)**

### **1. 🎯 SERVICES YANG DIBUTUHKAN**

#### **A. RVM Status Checker:**
```python
class RVMStatusChecker:
    """Check RVM status from server"""
    
    def __init__(self, api_client, rvm_id):
        self.api_client = api_client
        self.rvm_id = rvm_id
    
    def check_status(self):
        """Check current RVM status from server"""
        response = self.api_client.get(f"/api/v2/rvms/{self.rvm_id}/status")
        return response.get('data', {}).get('status')
    
    def update_status(self, status):
        """Update RVM status on server"""
        data = {"status": status}
        response = self.api_client.patch(f"/api/v2/rvms/{self.rvm_id}/status", data)
        return response
```

#### **B. Timezone Sync Client:**
```python
class TimezoneSyncClient:
    """Sync timezone with server"""
    
    def __init__(self, api_client, device_id):
        self.api_client = api_client
        self.device_id = device_id
    
    def sync_timezone(self, timezone_data):
        """Sync timezone with server"""
        response = self.api_client.post("/api/v2/timezone/sync", timezone_data)
        return response
    
    def get_timezone_status(self):
        """Get timezone status from server"""
        response = self.api_client.get(f"/api/v2/timezone/status/{self.device_id}")
        return response
```

#### **C. Remote Access Server:**
```python
class RemoteAccessServer:
    """Handle remote access requests"""
    
    def __init__(self, api_client, rvm_id):
        self.api_client = api_client
        self.rvm_id = rvm_id
    
    def start_remote_access(self, admin_data):
        """Start remote access session"""
        response = self.api_client.post(f"/api/v2/rvms/{self.rvm_id}/remote-access/start", admin_data)
        return response
    
    def stop_remote_access(self, admin_data):
        """Stop remote access session"""
        response = self.api_client.post(f"/api/v2/rvms/{self.rvm_id}/remote-access/stop", admin_data)
        return response
```

#### **D. Backup Client:**
```python
class BackupClient:
    """Handle backup operations"""
    
    def __init__(self, api_client, rvm_id):
        self.api_client = api_client
        self.rvm_id = rvm_id
    
    def start_backup(self, backup_config):
        """Start backup operation"""
        response = self.api_client.post(f"/api/v2/rvms/{self.rvm_id}/backup/start", backup_config)
        return response
    
    def upload_backup(self, backup_file):
        """Upload backup file"""
        response = self.api_client.post(f"/api/v2/rvms/{self.rvm_id}/backup/upload", backup_file)
        return response
```

#### **E. System Monitor:**
```python
class SystemMonitor:
    """Monitor system metrics"""
    
    def __init__(self, api_client, rvm_id):
        self.api_client = api_client
        self.rvm_id = rvm_id
    
    def collect_metrics(self):
        """Collect system metrics"""
        metrics = {
            "cpu_usage": self.get_cpu_usage(),
            "memory_usage": self.get_memory_usage(),
            "disk_usage": self.get_disk_usage(),
            "gpu_usage": self.get_gpu_usage(),
            "temperature": self.get_temperature(),
            "timestamp": datetime.now().isoformat()
        }
        return metrics
    
    def upload_metrics(self, metrics):
        """Upload metrics to server"""
        response = self.api_client.post(f"/api/v2/rvms/{self.rvm_id}/metrics", metrics)
        return response
```

### **2. ⚙️ CONFIGURATION YANG DIBUTUHKAN**

#### **A. Server Connection Config:**
```json
{
  "myrvm_base_url": "http://172.28.233.83:8001",
  "api_token": "your_api_token_here",
  "rvm_id": 1,
  "connection_timeout": 30,
  "retry_attempts": 3,
  "retry_delay": 2.0
}
```

#### **B. Remote Access Config:**
```json
{
  "remote_access_enabled": true,
  "remote_access_port": 5001,
  "admin_ips": ["192.168.1.0/24", "10.0.0.0/8"],
  "session_timeout": 3600,
  "max_concurrent_sessions": 1
}
```

#### **C. Timezone Config:**
```json
{
  "default_timezone": "Asia/Jakarta",
  "auto_sync_enabled": true,
  "sync_interval": 3600,
  "manual_sync_enabled": true,
  "timezone_api_url": "http://ip-api.com/json"
}
```

#### **D. Backup Config:**
```json
{
  "backup_enabled": true,
  "backup_interval": 86400,
  "backup_retention": 30,
  "include_images": true,
  "include_logs": true,
  "compression_enabled": true
}
```

#### **E. System Monitoring Config:**
```json
{
  "monitoring_enabled": true,
  "metrics_interval": 300,
  "upload_interval": 3600,
  "temperature_threshold": 80.0,
  "cpu_threshold": 90.0,
  "memory_threshold": 90.0
}
```

---

## **🔐 SUDO ACCESS SOLUTION**

### **✅ SOLUSI UNTUK SUDO ACCESS:**

#### **A. Service User Approach:**
```bash
# Create service user
sudo useradd -r -s /bin/false myrvm-service
sudo usermod -aG sudo myrvm-service

# Configure sudoers for specific commands
echo "myrvm-service ALL=(ALL) NOPASSWD: /bin/systemctl, /bin/reboot, /bin/shutdown, /bin/mount, /bin/umount" | sudo tee /etc/sudoers.d/myrvm-service

# Set proper permissions
sudo chown -R myrvm-service:myrvm-service /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
sudo chmod -R 755 /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
```

#### **B. Capability-based Approach:**
```bash
# Set capabilities for specific operations
sudo setcap 'cap_sys_admin,cap_net_admin+ep' /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/main/enhanced_jetson_main.py

# Set ownership
sudo chown myrvm-service:myrvm-service /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/main/enhanced_jetson_main.py
```

#### **C. Systemd Service Approach:**
```ini
[Unit]
Description=MyRVM Integration Service
Documentation=https://github.com/vnot01/test-cv-yolo11-sam2-camera
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=myrvm-service
Group=myrvm-service
WorkingDirectory=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration
ExecStart=/home/my/test-cv-yolo11-sam2-camera/myenv/bin/python /home/my/test-cv-yolo11-sam2-camera/myrvm-integration/main/enhanced_jetson_main.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration
Environment=MYRVM_ENVIRONMENT=production

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/my/test-cv-yolo11-sam2-camera/myrvm-integration /tmp /var/run

[Install]
WantedBy=multi-user.target
```

---

## **📋 KESIMPULAN REQUIREMENTS**

### **✅ DARI JETSON ORIN KE SERVER:**
1. **API Endpoints** - RVM status, timezone sync, remote access, backup, monitoring
2. **Database Schema** - RVM status, timezone sync, remote access, backup, metrics
3. **Services** - Status management, timezone sync, remote access, backup, monitoring

### **✅ DARI SERVER KE JETSON ORIN:**
1. **Services** - Status checker, timezone sync client, remote access server, backup client, system monitor
2. **Configuration** - Server connection, remote access, timezone, backup, monitoring
3. **Sudo Access** - Service user dengan limited sudo permissions

### **🔧 IMPLEMENTASI:**
1. **Server Side** - Implement API endpoints dan database schema
2. **Jetson Side** - Implement services dan configuration
3. **Security** - Setup service user dengan sudo access
4. **Integration** - Test bidirectional communication

---

**Status**: ✅ **REQUIREMENTS ANALYSIS COMPLETED**  
**Next**: **Final Recommendations**  
**Created**: 2025-01-20


