# API Reference v3 - RVM Jetson Integration (RVM-Only Endpoints)

**Project:** MyRVM Platform Integration with Jetson Orin Nano  
**Date:** September 25, 2025  
**Version:** 3.0.0 (RVM-Focused)  
**Focus:** RVM-provided endpoints only (not server endpoints)

## 📋 Overview

This document provides comprehensive API reference for **RVM-provided endpoints only**. This focuses on what the RVM Jetson device exposes for external access, monitoring, and control.

**Previous Versions:**
- [API_REFERENCE.md](API_REFERENCE.md) - Complete server + RVM endpoints
- [API_REFERENCE-v2.md](API_REFERENCE-v2.md) - Updated metrics and timezone endpoints

## 🏗️ **RVM Architecture**

### **RVM IP Addresses:**
- **Primary:** `100.117.234.2` (Tailscale Network)
- **Backup:** `172.28.93.97` (ZeroTier Network)
- **Local:** `localhost` (SSH tunnel)

### **Port Configuration:**
- **Port 5000:** Camera Service (On-demand camera operations)
- **Port 5001:** GUI Client (User interaction interface)
- **Port 5002:** Remote Access Controller (Main monitoring & control)
- **Port 8080:** Installation GUI (Setup and configuration)

---

## 📷 **Camera Service APIs (Port 5000)**

**Base URL:** `http://100.117.234.2:5000`  
**Purpose:** Camera control, image capture, streaming  
**Access:** Local endpoints (no authentication required)

### **Camera Status**
```http
GET /api/camera/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "camera_available": false,
    "camera_running": null,
    "camera_port": 5000,
    "camera_url": "http://100.117.234.2:5000",
    "current_status": "active",
    "active_sessions": 0,
    "session_timeout": 3600,
    "auto_status_change": true,
    "sessions": {}
  }
}
```

### **Capture Image**
```http
POST /api/camera/capture
Content-Type: application/json

{
  "resolution": "1920x1080",
  "format": "jpeg",
  "quality": 95
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "image_path": "/storages/images/capture_20250925_234500.jpg",
    "resolution": "1920x1080",
    "format": "jpeg",
    "file_size": 245760,
    "timestamp": "2025-09-25T23:45:00.000000Z"
  }
}
```

### **Start Video Stream**
```http
POST /api/camera/stream/start
Content-Type: application/json

{
  "resolution": "1280x720",
  "fps": 30,
  "format": "mjpeg"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "stream_url": "http://100.117.234.2:5000/stream",
    "resolution": "1280x720",
    "fps": 30,
    "format": "mjpeg",
    "status": "streaming"
  }
}
```

### **Stop Video Stream**
```http
POST /api/camera/stream/stop
```

**Response:**
```json
{
  "success": true,
  "message": "Video stream stopped"
}
```

---

## 📱 **GUI Client APIs (Port 5001)**

**Base URL:** `http://100.117.234.2:5001`  
**Purpose:** Touch screen interface, user interaction  
**Access:** Local endpoints (no authentication required)

### **GUI Client Interface**
```http
GET /
```

**Description:** Main GUI interface for user interaction on LED/LCD touch screen

**Features:**
- QR Code login screen
- User authentication
- Main dashboard
- Profile management
- System settings

### **Screen Navigation (Development Only)**
```http
GET /?screen=main
GET /?screen=profile
GET /?screen=settings
GET /screen/main
GET /screen/profile
GET /screen/settings
```

**Description:** Direct screen access for testing (will be locked in production)

### **QR Code Generation**
```http
GET /api/qr-code
```

**Response:**
```json
{
  "success": true,
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "qr_data": {
    "rvm_id": "1",
    "timestamp": 1695678900,
    "action": "login",
    "session_token": "abc123def456_1695678900",
    "expires_at": 1695678960,
    "version": "1.0"
  }
}
```

### **User Authentication**
```http
POST /api/authenticate
Content-Type: application/json

{
  "qr_data": {
    "rvm_id": "1",
    "timestamp": 1695678900,
    "action": "login",
    "session_token": "abc123def456_1695678900",
    "expires_at": 1695678960,
    "version": "1.0"
  }
}
```

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "sess_abc123def456_1695678900",
    "user": {
      "name": "Test User",
      "email": "test@example.com",
      "balance": 15000.0
    }
  }
}
```

### **User Logout**
```http
POST /api/logout
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### **GUI Status**
```http
GET /api/status
```

**Response:**
```json
{
  "success": true,
  "status": {
    "rvm_id": "1",
    "current_screen": "login",
    "user_session": null,
    "system_info": {
      "cpu_usage": 0.0,
      "memory_usage": 0.0,
      "gpu_usage": 0.0,
      "temperature": 0.0,
      "rvm_id": "1",
      "services_status": {},
      "timestamp": "2025-09-25T23:45:00.000000Z",
      "uptime": "N/A"
    },
    "detection_results": [],
    "auth_status": {
      "rvm_id": "1",
      "active_sessions_count": 0,
      "max_sessions": 10,
      "session_timeout": 3600,
      "user_profiles_count": 0,
      "authentication_callbacks_count": 1
    }
  }
}
```

### **Detection Results**
```http
GET /api/detection-results
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "class": "plastic_bottle",
      "confidence": 0.95,
      "bbox": [100, 100, 200, 200],
      "timestamp": "2025-09-25T23:45:00.000000Z"
    }
  ]
}
```

### **System Information**
```http
GET /api/system-info
```

**Response:**
```json
{
  "success": true,
  "system_info": {
    "timestamp": "2025-09-25T23:45:00.000000Z",
    "rvm_id": "1",
    "uptime": "N/A",
    "cpu_usage": 0.0,
    "memory_usage": 0.0,
    "gpu_usage": 0.0,
    "temperature": 0.0,
    "services_status": {}
  }
}
```

### **Change Screen**
```http
POST /api/change-screen
Content-Type: application/json

{
  "screen": "main"
}
```

**Response:**
```json
{
  "success": true,
  "current_screen": "main"
}
```

---

## 🌐 **Remote Access Controller APIs (Port 5002)**

**Base URL:** `http://100.117.234.2:5002`  
**Purpose:** Remote control, monitoring, command execution  
**Access:** Remote endpoints (API key authentication for some endpoints)

### **Pulse Heartbeat (Simplified)**
```http
GET /pulse
```

**Description:** Lightweight heartbeat endpoint for server monitoring

**Response:**
```json
{
  "status": "ok",
  "services": {
    "camera_service_5000": true,
    "gui_client_5001": true,
    "remote_access_5002": true
  },
  "current_time_iso": "2025-09-25T23:45:00.000000+07:00",
  "uptime_service_seconds": 3600
}
```

### **RVM Health Check (Comprehensive)**
```http
GET /rvm-health
```

**Description:** Comprehensive health check with detailed status information

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-09-25T23:45:00.000000+07:00",
  "last_update": "2025-09-25T23:45:00.000000+07:00",
  "uptime_service_seconds": 3600,
  "active_sessions": 0,
  "camera_manager_status": {
    "active_sessions": 0,
    "auto_status_change": true,
    "camera_available": false,
    "camera_port": 5000,
    "camera_running": null,
    "camera_url": "http://100.117.234.2:5000",
    "current_status": "active",
    "original_status": null,
    "session_timeout": 3600,
    "sessions": {}
  },
  "gui_client_status": {
    "service_status": "active",
    "port_open": true,
    "gui_client_port": 5001,
    "gui_client_url": "http://100.117.234.2:5001",
    "current_status": "active",
    "api_accessible": true,
    "api_status": {
      "success": true,
      "status": {
        "rvm_id": "1",
        "current_screen": "login",
        "user_session": null,
        "auth_status": {
          "active_sessions_count": 0,
          "max_sessions": 10,
          "session_timeout": 3600
        }
      }
    },
    "timestamp": "2025-09-25T23:45:00.000000+07:00"
  },
  "services": {
    "remote_access_5002": true,
    "gui_client_5001": true,
    "camera_service_5000": true
  },
  "timezone_info": {
    "timezone": "Asia/Jakarta",
    "offset": "+0700",
    "offset_hours": 7.0,
    "current_time": "2025-09-25 23:45:00 WIB",
    "current_time_iso": "2025-09-25T23:45:00.000000+07:00"
  }
}
```

### **RVM Status (Detailed)**
```http
GET /rvm/status
```

**Description:** Comprehensive RVM status with system health, services, and hardware information

**Response:**
```json
{
  "rvm_id": 1,
  "overall_status": "active",
  "status_details": {
    "system_health": {
      "cpu_usage": 25.0,
      "memory_usage": 51.5,
      "disk_usage": 36.9,
      "gpu_temperature": 51.4,
      "uptime": 3600
    },
    "services": {
      "camera_service": "active",
      "gui_client": "active",
      "remote_access": "active",
      "metrics_sender": "active"
    },
    "api_connectivity": {
      "connected": true,
      "base_url": "http://100.123.143.87:8001",
      "response": "Connected"
    },
    "hardware": {
      "gpu_usage": 0.0,
      "gpu_temperature": 51.4,
      "gpu_memory_usage": 0.0
    },
    "power": {
      "gpu_power_display": "6.55 W",
      "cpu_power_display": "1.79 W",
      "total_power_display": "8.34 W"
    },
    "network": {
      "local_ip": "203.0.113.45",
      "signal_strength": 80,
      "connection_type": "wireless"
    }
  },
  "timestamp": "2025-09-25T23:45:00.000000+07:00",
  "timezone_info": {
    "timezone": "Asia/Jakarta",
    "offset": "+0700",
    "offset_hours": 7.0,
    "current_time": "2025-09-25 23:45:00 WIB",
    "current_time_iso": "2025-09-25T23:45:00.000000+07:00"
  }
}
```

### **Restart Services**
```http
POST /api/restart_services
X-API-Key: {api_key}
Content-Type: application/json
```

**Description:** Restart all RVM services (camera, GUI client, remote access, metrics sender)

**Response:**
```json
{
  "success": true,
  "message": "Services restart initiated",
  "states": {
    "rvm-remote-camera.service": "restarted",
    "rvm-remote-gui.service": "restarted",
    "rvm-remote-access.service": "restarted",
    "rvm-metrics-sender.service": "restarted"
  }
}
```

### **Timezone Information**
```http
GET /timezone/info
```

**Response:**
```json
{
  "timezone": "Asia/Jakarta",
  "offset": "+0700",
  "offset_hours": 7.0,
  "current_time": "2025-09-25 23:45:00 WIB",
  "current_time_iso": "2025-09-25T23:45:00.000000+07:00"
}
```

### **Timezone Conversion**
```http
POST /timezone/convert
Content-Type: application/json

{
  "server_time": "2025-09-25T16:45:00.000000Z"
}
```

**Response:**
```json
{
  "server_time": "2025-09-25T16:45:00.000000Z",
  "local_time": "2025-09-25 23:45:00 WIB",
  "local_time_iso": "2025-09-25T23:45:00.000000+07:00",
  "relative_time": "Just now",
  "timezone_info": {
    "timezone": "Asia/Jakarta",
    "offset": "+0700",
    "offset_hours": 7.0,
    "current_time": "2025-09-25 23:45:00 WIB",
    "current_time_iso": "2025-09-25T23:45:00.000000+07:00"
  }
}
```

---

## 🔧 **Installation GUI APIs (Port 8080)**

**Base URL:** `http://100.117.234.2:8080`  
**Purpose:** Installation process, hardware detection, network setup  
**Access:** Local endpoints (no authentication required)

### **Installation Status**
```http
GET /api/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "ready",
    "phase": "initialization",
    "progress": 0,
    "current_step": 1,
    "total_steps": 5,
    "timezone_info": {
      "timezone": "Asia/Jakarta",
      "offset": "+0700",
      "offset_hours": 7.0,
      "current_time": "2025-09-25 23:45:00 WIB",
      "current_time_iso": "2025-09-25T23:45:00.000000+07:00"
    }
  }
}
```

### **Hardware Detection**
```http
GET /api/hardware/detect
```

**Response:**
```json
{
  "success": true,
  "data": {
    "cpu": "Cortex-A78AE (Jetson Orin)",
    "memory": "7.4GB",
    "gpu": "Orin (nvgpu)",
    "camera": "Not detected",
    "network": {
      "interface": "wlP1p1s0",
      "status": "connected",
      "ip_address": "192.168.1.11"
    }
  }
}
```

### **Network Status**
```http
GET /api/network/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "wifi_connected": true,
    "current_network": "Kikimiu",
    "ip_address": "192.168.1.11",
    "internet_access": true,
    "myrvm_platform_access": true
  }
}
```

### **WiFi Network Scan**
```http
GET /api/network/scan
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "ssid": "Kikimiu",
      "signal": 89,
      "security": "WPA2",
      "frequency": 2412,
      "bssid": "CC:B1:71:52:B9:D0"
    }
  ]
}
```

### **WiFi Connection**
```http
POST /api/network/connect
Content-Type: application/json

{
  "ssid": "Kikimiu",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "WiFi connection initiated",
  "data": {
    "ssid": "Kikimiu",
    "status": "connecting"
  }
}
```

### **Server Connectivity Test**
```http
POST /api/server/test
Content-Type: application/json

{
  "server_url": "http://100.123.143.87:8001"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "server_url": "http://100.123.143.87:8001",
    "connectivity": true,
    "response_time": 150,
    "status_code": 200
  }
}
```

### **AI Models Testing**
```http
GET /api/ai/test
```

**Response:**
```json
{
  "success": true,
  "data": {
    "yolo": {
      "status": "available",
      "model_path": "models/yolo11n.pt",
      "test_result": "success"
    },
    "sam2": {
      "status": "available", 
      "model_path": "models/sam2.1_b.pt",
      "test_result": "success"
    }
  }
}
```

### **Configuration Save**
```http
POST /api/config/save
Content-Type: application/json

{
  "network": {
    "interface": "wlP1p1s0",
    "server_url": "http://100.123.143.87:8001"
  },
  "hardware": {
    "camera_enabled": true,
    "motor_enabled": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration saved successfully",
  "data": {
    "config_path": "/home/my/test-cv-yolo11-sam2-camera/myrvm-integration/config/production_config.json",
    "timestamp": "2025-09-25T23:45:00.000000Z"
  }
}
```

### **Deployment Start**
```http
POST /api/deploy/start
```

**Response:**
```json
{
  "success": true,
  "data": {
    "deployment_id": "deploy_20250925_234500",
    "status": "started",
    "estimated_time": "5 minutes"
  }
}
```

### **Services Start**
```http
POST /api/services/start
```

**Description:** Enable and start all RVM services (camera, GUI client, remote access, metrics sender)

**Response:**
```json
{
  "success": true,
  "message": "Services started successfully",
  "data": {
    "services": [
      "rvm-remote-camera.service",
      "rvm-remote-gui.service", 
      "rvm-remote-access.service",
      "rvm-metrics-sender.service"
    ],
    "status": "active",
    "timestamp": "2025-09-25T23:45:00.000000Z"
  }
}
```

### **Timezone Information (Installation)**
```http
GET /api/timezone/info
```

**Response:**
```json
{
  "timezone": "Asia/Jakarta",
  "offset": "+0700",
  "offset_hours": 7.0,
  "current_time": "2025-09-25 23:45:00 WIB",
  "current_time_iso": "2025-09-25T23:45:00.000000+07:00"
}
```

### **Timezone Conversion (Installation)**
```http
POST /api/timezone/convert
Content-Type: application/json

{
  "server_time": "2025-09-25T16:45:00.000000Z"
}
```

**Response:**
```json
{
  "server_time": "2025-09-25T16:45:00.000000Z",
  "local_time": "2025-09-25 23:45:00 WIB",
  "local_time_iso": "2025-09-25T23:45:00.000000+07:00",
  "relative_time": "Just now",
  "timezone_info": {
    "timezone": "Asia/Jakarta",
    "offset": "+0700",
    "offset_hours": 7.0,
    "current_time": "2025-09-25 23:45:00 WIB",
    "current_time_iso": "2025-09-25T23:45:00.000000+07:00"
  }
}
```

---

## 📊 **Metrics Sender (Push to Server)**

**Purpose:** RVM sends metrics to server  
**Direction:** RVM → Server  
**Endpoint:** `POST http://100.123.143.87:8001/api/v2/rvms/{rvm_id}/metrics`

### **Metrics Payload**
```json
{
  "rvm_id": 1,
  "timezone": "Asia/Jakarta",
  "timestamp": "2025-09-25T23:45:00.000000+07:00",
  "system_metrics": {
    "cpu_usage": 1.5,
    "memory_usage": 41.7,
    "disk_usage": 35.0,
    "gpu_usage": 0.0,
    "temperature": 51.6,
    "gpu_temperature": 51.4,
    "disk_read_speed": 0,
    "disk_write_speed": 0,
    "network_upload_speed": 0,
    "network_download_speed": 0,
    "memory_available": 4655190016,
    "disk_available": 149394894848,
    "process_count": 339,
    "load_average": 1.01,
    "uptime": 3600,
    "power_consumption": {
      "sensor_path": "/sys/devices/platform/bus@0/c240000.i2c/i2c-1/1-0040/hwmon/hwmon1",
      "gpu_power_mw": 6549.504,
      "cpu_power_mw": 1791.36,
      "measured_total_mw": 1757.184,
      "cpu_gpu_combined_mw": 8340.864,
      "total_power_mw": 8340.864,
      "soc_power_mw": 0.0,
      "gpu_power_display": "6.55 W",
      "cpu_power_display": "1.79 W",
      "measured_total_display": "1.76 W",
      "cpu_gpu_combined_display": "8.34 W",
      "total_power_display": "8.34 W",
      "soc_power_display": "0.0 mW"
    }
  },
  "application_metrics": {
    "software_version": "1.0.0",
    "ai_model_version": "v1.0.0",
    "ai_model_path": "/home/my/models/best.pt",
    "uptime_seconds": 11,
    "deposit_count_since_restart": 0,
    "last_deposit_time": null,
    "error_count": 0,
    "warning_count": 0
  },
  "network_info": {
    "local_ip": "203.0.113.45",
    "virtual_ip": "100.117.234.2",
    "gateway_ip": "192.168.1.1",
    "dns_servers": ["127.0.0.53"],
    "network_interface": "wlP1p1s0",
    "connection_type": "wireless",
    "signal_strength": 80,
    "last_network_check": "2025-09-25T23:45:00.000000+07:00"
  }
}
```

**Headers:**
```
Content-Type: application/json
X-API-Key: {api_key}
X-RVM-ID: 1
X-Requested-With: XMLHttpRequest
```

---

## 🔐 **Authentication**

### **API Key Authentication**
Some endpoints require API key authentication:

```http
X-API-Key: {api_key}
```

**Endpoints requiring API key:**
- `POST /api/restart_services` (Port 5002)

### **No Authentication Required**
Most RVM endpoints are accessible without authentication for local access:
- All Camera Service endpoints (Port 5000)
- All GUI Client endpoints (Port 5001)
- Most Remote Access Controller endpoints (Port 5002)
- All Installation GUI endpoints (Port 8080)

---

## 📊 **Service Status Monitoring**

### **Quick Health Check**
```bash
# Pulse heartbeat (lightweight)
curl http://100.117.234.2:5002/pulse

# Comprehensive health check
curl http://100.117.234.2:5002/rvm-health
```

### **Service Status Check**
```bash
# Check all services
systemctl status rvm-remote-camera.service
systemctl status rvm-remote-gui.service
systemctl status rvm-remote-access.service
systemctl status rvm-metrics-sender.service
systemctl status rvm-gui-client.service
```

### **Port Status Check**
```bash
# Check if ports are listening
ss -ltnp | grep ':5000\|:5001\|:5002\|:8080'
```

---

## 🚨 **Error Responses**

### **Service Unavailable (503)**
```json
{
  "status": "error",
  "error": "Service temporarily unavailable"
}
```

### **Bad Request (400)**
```json
{
  "success": false,
  "error": "Invalid request parameters"
}
```

### **Internal Server Error (500)**
```json
{
  "status": "error",
  "error": "Internal server error"
}
```

---

## 📋 **Endpoint Summary**

### **Total RVM Endpoints: 25+ APIs**

#### **📷 Camera Service (Port 5000) - 4 endpoints**
- Camera status, capture, stream start/stop

#### **📱 GUI Client (Port 5001) - 8 endpoints**
- QR code generation, authentication, status, system info

#### **🌐 Remote Access Controller (Port 5002) - 7 endpoints**
- Pulse heartbeat, health check, status, restart services, timezone

#### **🔧 Installation GUI (Port 8080) - 8+ endpoints**
- Hardware detection, network setup, AI testing, deployment

#### **📊 Metrics Sender - 1 endpoint (Push)**
- System metrics, application metrics, network info

---

## 🔄 **Multiple RVM Deployment**

### **No Conflicts Between RVMs**
Each RVM operates independently:
- **Unique IP addresses** per RVM
- **Same port numbers** (5000, 5001, 5002, 8080) on each RVM
- **Unique RVM IDs** for server identification
- **Independent services** and configurations

### **Example Multi-RVM Setup**
```
RVM-1: http://192.168.1.100:5002/pulse
RVM-2: http://192.168.1.101:5002/pulse  
RVM-3: http://192.168.1.102:5002/pulse
```

---

## 📚 **Related Documentation**

- [API_REFERENCE.md](API_REFERENCE.md) - Complete server + RVM endpoints
- [API_REFERENCE-v2.md](API_REFERENCE-v2.md) - Updated metrics and timezone endpoints
- [RVM_STATUS_API.md](RVM_STATUS_API.md) - Detailed status API documentation

---

**Last Updated:** September 25, 2025  
**Next Review:** October 2, 2025  
**Maintainer:** RVM System (Jetson Orin)  
**Status:** ✅ Production Ready (RVM-Focused API Documentation)
