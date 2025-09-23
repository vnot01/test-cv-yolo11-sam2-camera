# API Reference

**Project:** MyRVM Platform Integration with Jetson Orin Nano  
**Date:** September 22, 2025  
**Version:** 2.0.0 (Updated)

## 📋 Overview

This document provides comprehensive API reference for the MyRVM Platform integration with the Jetson Orin Nano CV system. **Updated to reflect actual endpoint structure.**

### ✅ Updated RVM Registration Flow
- Admin/Technician pre-registers RVM in Dashboard → API key is auto-generated and displayed immediately after creation (copy and store it)
- On the RVM UI, Technician presses “Confirm/Activate” → RVM sends its final details (IP, port, timezone, etc.) using the API key to the server
- Server updates the RVM profile and the device appears on the Admin dashboard

Notes:
- API key source: Dashboard Admin (shown right after “Add New RVM”)
- Confirmation is done on the RVM device UI, not in Admin API
- RVM uses API key authentication for its self-claim/self-update endpoints

## 🏗️ **API Endpoints Architecture**

### **📊 Endpoint Categories:**

#### **1. 🔐 Authentication APIs**
- **Provider:** MyRVM-Platform (Server)
- **Purpose:** User authentication, token management
- **Access:** Public endpoints

#### **2. 🤖 Processing Engine APIs**
- **Provider:** MyRVM-Platform (Server)
- **Purpose:** AI processing engine management, registration
- **Access:** Protected (Bearer token required)

#### **3. 📸 Detection Results APIs**
- **Provider:** MyRVM-Platform (Server)
- **Purpose:** Computer vision results, AI inference data
- **Access:** Protected (Bearer token required)

#### **4. 💰 Deposit Management APIs**
- **Provider:** MyRVM-Platform (Server)
- **Purpose:** Waste deposit processing, reward system
- **Access:** Protected (Bearer token required)

#### **5. 🏪 RVM Management APIs**
- **Provider:** MyRVM-Platform (Server)
- **Purpose:** RVM device management, remote control
- **Access:** Protected (Bearer token required)

#### **5.a 🔑 RVM Self APIs (API Key Auth) – NEW**
- **Provider:** MyRVM-Platform (Server)
- **Purpose:** Allow RVM to claim/update its own details after Admin pre-registration
- **Access:** API key (X-API-Key)

#### **6. 📁 File Upload APIs**
- **Provider:** MyRVM-Platform (Server)
- **Purpose:** Image and file upload handling
- **Access:** Protected (Bearer token required)

#### **7. 🏥 Health Check APIs**
- **Provider:** MyRVM-Platform (Server)
- **Purpose:** System health monitoring
- **Access:** Public endpoints

#### **8. 🔧 Installation Method APIs**
- **Provider:** RVM-Jetson (Edge Device)
- **Purpose:** Installation process, hardware detection, network setup
- **Access:** Local endpoints (port 8080)

#### **9. 🌐 Remote Access APIs**
- **Provider:** RVM-Jetson (Edge Device)
- **Purpose:** Remote control, monitoring, command execution
- **Access:** Remote endpoints (port 5000)

#### **10. 📱 GUI Client APIs**
- **Provider:** RVM-Jetson (Edge Device)
- **Purpose:** Touch screen interface, user interaction
- **Access:** Local endpoints (port 5001)

#### **11. 📷 Camera Service APIs**
- **Provider:** RVM-Jetson (Edge Device)
- **Purpose:** Camera control, image capture, streaming
- **Access:** Local endpoints (port 5002)

## 📚 Istilah-istilah Umum

### **🏗️ Arsitektur Sistem:**

**`server_ip`** - IP Address dari MyRVM-Platform Server
- **Deskripsi:** Server utama yang menjalankan MyRVM-Platform (Laravel application)
- **Port:** 8001 (API), 8000 (Web)
- **Fungsi:** Menyediakan API endpoints, database, dashboard admin, dan manajemen sistem
- **Primary IP:** `100.123.143.87` (Tailscale)
- **Backup IP:** `172.28.233.83` (ZeroTier)
- **Local Access:** `localhost` (jika terforward via SSH)
- **Contoh:** `server_ip:8001` atau `100.123.143.87:8001` (Tailscale) atau `172.28.233.83:8001` (ZeroTier) ata

**`rvm_ip`** - IP Address dari RVM-Jetson Edge Device
- **Deskripsi:** Mesin RVM (Reverse Vending Machine) yang menjalankan Jetson Orin Nano
- **Port:** 5000 (Remote Access), 5001 (GUI), 5002 (Camera)
- **Fungsi:** Computer Vision, AI processing, sensor control, dan komunikasi dengan server
- **Primary IP:** `100.117.234.2` (Tailscale)
- **Backup IP:** `172.28.93.97` (ZeroTier)
- **Local Access:** `localhost` (jika terforward via SSH)
- **Contoh:** `rvm_ip:5000` atau `100.117.234.2:5000` (Tailscale) atau `172.28.93.97:5000` (ZeroTier)

### ** Komponen Sistem:**

**MyRVM-Platform** - Server Application
- **Teknologi:** Laravel (PHP), PostgreSQL, Redis
- **Fungsi:** Backend API, database, admin dashboard, user management
- **Lokasi:** Server VM (Cloud/Data Center)

**RVM-Jetson** - Edge Device
- **Teknologi:** Python, YOLO11, SAM2, OpenCV, Flask
- **Fungsi:** Computer Vision, AI inference, sensor control, real-time processing
- **Lokasi:** Edge VM (Lokasi fisik RVM)

### ** Komunikasi:**

**VPN Connection** - Virtual Private Network
- **Fungsi:** Koneksi aman antara Server VM dan Edge VM
- **Protokol:** IPsec, OpenVPN, atau WireGuard
- **Keamanan:** Enkripsi end-to-end

**API Communication** - Application Programming Interface
- **Direction:** RVM-Jetson → MyRVM-Platform (metrics, status)
- **Direction:** MyRVM-Platform → RVM-Jetson (commands, updates)
- **Format:** JSON over HTTP/HTTPS

### ** Port Configuration:**

**Server Ports (MyRVM-Platform):**
- **8000:** Web Dashboard (Admin Panel)
- **8001:** API Endpoints (REST API)

**Edge Ports (RVM-Jetson):**
- **5000:** Remote Access Controller (Main service)
- **5001:** GUI Client (Touch screen interface)
- **5002:** Camera Manager (On-demand camera service)

### ** Data Flow:**

**Metrics Flow:** RVM-Jetson → MyRVM-Platform
- **Data:** System metrics, application metrics, network info
- **Frequency:** Real-time (every 30 seconds)
- **Endpoint:** `POST /api/v2/rvms/{id}/metrics`

**Command Flow:** MyRVM-Platform → RVM-Jetson
- **Data:** Remote commands, system updates, configuration
- **Trigger:** Admin actions, scheduled tasks
- **Endpoint:** `POST /api/v2/detection-results/trigger-processing`

### ** Authentication:**

**Bearer Token** - API Authentication
- **Format:** `Authorization: Bearer {token}`
- **Expiry:** 24 hours
- **Scope:** API access, user permissions

**API Key** - RVM Authentication
- **Format:** `X-API-Key: {api_key}`
- **Purpose:** RVM-specific authentication
- **Scope:** RVM operations, metrics submission

### ** Status Codes:**

**200** - Success
**201** - Created
**400** - Bad Request
**401** - Unauthorized
**404** - Not Found
**422** - Validation Error
**500** - Internal Server Error

### ** Network Configuration:**

**Server IP Addresses (MyRVM-Platform):**
- **Primary:** `100.123.143.87` (Tailscale Network)
- **Backup:** `172.28.233.83` (ZeroTier Network)
- **Local:** `localhost` (jika terforward via SSH tunnel)

**RVM IP Addresses (Jetson Orin Nano):**
- **Primary:** `100.117.234.2` (Tailscale Network)
- **Backup:** `172.28.93.97` (ZeroTier Network)
- **Local:** `localhost` (jika terforward via SSH tunnel)

**Network Access Methods:**
1. **Tailscale (Recommended):** Primary network untuk production
2. **ZeroTier (Backup):** Secondary network untuk failover
3. **SSH Tunnel:** Local development dan debugging

### ** Environment Variables:**

**Development:** `localhost`, `127.0.0.1`
**Production:** 
- **Tailscale:** `100.123.143.87` (server), `100.117.234.2` (rvm)
- **ZeroTier:** `172.28.233.83` (server), `172.28.93.97` (rvm)
**Testing:** `test_ip`, `mock_ip` (for testing purposes)

### ** Network Access Examples:**

**Tailscale Network (Primary):**
```bash
# Server API Access
curl http://100.123.143.87:8001/api/health-check

# RVM Remote Access
curl http://100.117.234.2:5000/health

# Web Dashboard
http://100.123.143.87:8000
```

**ZeroTier Network (Backup):**
```bash
# Server API Access
curl http://172.28.233.83:8001/api/health-check

# RVM Remote Access
curl http://172.28.93.97:5000/health

# Web Dashboard
http://172.28.233.83:8000
```

**SSH Tunnel (Local Development):**
```bash
# Forward Server API
ssh -L 8001:100.123.143.87:8001 user@server
curl http://localhost:8001/api/health-check

# Forward RVM Access
ssh -L 5000:100.117.234.2:5000 user@rvm
curl http://localhost:5000/health
```

### **📝 IP Address Placeholders:**

**`rvm_ip`** - Placeholder untuk IP address RVM-Jetson
- **Ganti dengan:** IP address RVM yang sesungguhnya
- **Contoh:** `100.117.234.2` (Tailscale) atau `172.28.93.97` (ZeroTier)
- **Penggunaan:** Semua endpoint RVM-Jetson

**`server_ip`** - Placeholder untuk IP address MyRVM-Platform Server
- **Ganti dengan:** IP address server yang sesungguhnya
- **Contoh:** `100.123.143.87` (Tailscale) atau `172.28.233.83` (ZeroTier)
- **Penggunaan:** Semua endpoint MyRVM-Platform

**`localhost`** - Hanya untuk SSH port forwarding
- **Penggunaan:** Hanya jika menggunakan SSH tunnel
- **Contoh:** `ssh -L 8080:rvm_ip:8080 user@rvm`
- **Akses:** `http://localhost:8080` (setelah port forwarding)

**Note:** 
- `rvm_ip` = IP address RVM yang sesungguhnya (contoh: `100.117.234.2` untuk Tailscale atau `172.28.93.97` untuk ZeroTier)
- `server_ip` = IP address MyRVM-Platform Server yang sesungguhnya (contoh: `100.123.143.87` untuk Tailscale atau `172.28.233.83` untuk ZeroTier)
- `localhost` = Hanya digunakan jika menggunakan SSH port forwarding

## 🔐 Authentication

### **Login**
```http
POST /api/v2/auth/login
Content-Type: application/json

{
  "email": "admin@myrvm.com",
  "password": "password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "21|epxqGDMSdKgZ357EmWxlQBOuh4XtqRJD0WBzhs934cd94f41",
    "user": {
      "id": 1,
      "name": "Admin",
      "email": "admin@myrvm.com"
    }
  },
  "message": "Login successful"
}
```

**Usage:**
```python
# Python example
import requests

login_data = {
    'email': 'admin@myrvm.com',
    'password': 'password'
}

response = requests.post('http://100.123.143.87:8001/api/v2/auth/login', 
                        json=login_data)
token = response.json()['data']['token']
```

## 🤖 Processing Engines

### **List Processing Engines**
```http
GET /api/v2/processing-engines
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 25,
      "name": "Jetson Orin Nano - CV System",
      "type": "nvidia_cuda",
      "server_address": "100.117.234.2",
      "port": 5000,
      "gpu_memory_limit": 8,
      "docker_gpu_passthrough": true,
      "model_path": "/models/yolo11n.pt",
      "processing_timeout": 30,
      "auto_failover": true,
      "is_active": true,
      "is_online": true,
      "last_ping_at": "2025-09-22T13:31:06.000000Z",
      "created_at": "2025-09-22T13:31:06.000000Z",
      "updated_at": "2025-09-22T13:31:06.000000Z"
    }
  ],
  "message": "Processing engines retrieved successfully"
}
```

### **Register Processing Engine**
```http
POST /api/v2/processing-engines
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Jetson Orin Nano - CV System",
  "type": "nvidia_cuda",
  "server_address": "100.117.234.2",
  "port": 5000,
  "gpu_memory_limit": 8,
  "docker_gpu_passthrough": true,
  "model_path": "/models/yolo11n.pt",
  "processing_timeout": 30,
  "auto_failover": true,
  "is_active": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 25,
    "name": "Jetson Orin Nano - CV System",
    "type": "nvidia_cuda",
    "server_address": "100.117.234.2",
    "port": 5000,
    "gpu_memory_limit": 8,
    "docker_gpu_passthrough": true,
    "model_path": "/models/yolo11n.pt",
    "processing_timeout": 30,
    "auto_failover": true,
    "is_active": true,
    "is_online": true,
    "last_ping_at": "2025-09-22T13:31:06.000000Z",
    "created_at": "2025-09-22T13:31:06.000000Z",
    "updated_at": "2025-09-22T13:31:06.000000Z"
  },
  "message": "Processing engine created successfully"
}
```

**Field Requirements:**
- `name` (required): Engine name
- `type` (required): Engine type (`nvidia_cuda`, `jetson_edge`)
- `server_address` (required): IP address of the engine
- `port` (required): Port number (1-65535)
- `gpu_memory_limit` (optional): GPU memory limit in GB
- `docker_gpu_passthrough` (optional): Enable Docker GPU passthrough
- `model_path` (optional): Path to AI models
- `processing_timeout` (optional): Processing timeout in seconds
- `auto_failover` (optional): Enable auto failover
- `is_active` (optional): Engine active status

### **Get Processing Engine**
```http
GET /api/v2/processing-engines/{id}
Authorization: Bearer {token}
```

### **Update Processing Engine**
```http
PUT /api/v2/processing-engines/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Jetson Orin Nano - CV System",
  "is_active": false
}
```

### **Delete Processing Engine**
```http
DELETE /api/v2/processing-engines/{id}
Authorization: Bearer {token}
```

### **Ping Processing Engine**
```http
POST /api/v2/processing-engines/{id}/ping
Authorization: Bearer {token}
```

### **Assign Processing Engine to RVM**
```http
POST /api/v2/processing-engines/{id}/assign
Authorization: Bearer {token}
Content-Type: application/json

{
  "rvm_id": 1,
  "priority": "primary",
  "is_active": true
}
```

## 📸 Detection Results

### **List Detection Results**
```http
GET /api/v2/detection-results
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "rvm_id": 1,
      "image_path": "/storages/images/output/camera_yolo/results/images/detection_20250922_133106.jpg",
      "detections": [
        {
          "class": "plastic_bottle",
          "confidence": 0.95,
          "bbox": [100, 100, 200, 200],
          "segmentation_mask": "base64_encoded_mask_data"
        }
      ],
      "status": "processed",
      "timestamp": "2025-09-22T13:31:06.000000Z",
      "created_at": "2025-09-22T13:31:06.000000Z",
      "updated_at": "2025-09-22T13:31:06.000000Z"
    }
  ],
  "message": "Detection results retrieved successfully"
}
```

### **Upload Detection Results**
```http
POST /api/v2/detection-results
Authorization: Bearer {token}
Content-Type: application/json

{
  "rvm_id": 1,
  "image_path": "/storages/images/output/camera_yolo/results/images/detection_20250922_133106.jpg",
  "detections": [
    {
      "class": "plastic_bottle",
      "confidence": 0.95,
      "bbox": [100, 100, 200, 200],
      "segmentation_mask": "base64_encoded_mask_data"
    }
  ],
  "status": "processed",
  "timestamp": "2025-09-22T13:31:06.000000Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "rvm_id": 1,
    "image_path": "/storages/images/output/camera_yolo/results/images/detection_20250922_133106.jpg",
    "detections": [
      {
        "class": "plastic_bottle",
        "confidence": 0.95,
        "bbox": [100, 100, 200, 200],
        "segmentation_mask": "base64_encoded_mask_data"
      }
    ],
    "status": "processed",
    "timestamp": "2025-09-22T13:31:06.000000Z",
    "created_at": "2025-09-22T13:31:06.000000Z",
    "updated_at": "2025-09-22T13:31:06.000000Z"
  },
  "message": "Detection result stored successfully"
}
```

### **Get Detection Result**
```http
GET /api/v2/detection-results/{id}
Authorization: Bearer {token}
```

### **Get RVM Status** ⚠️ **UPDATED ENDPOINT**
```http
GET /api/v2/detection-results/rvm/{rvmId}/status
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "rvm_id": 1,
    "rvm_name": "RVM-001",
    "current_status": "active",
    "latest_detection_result": {
      "id": 1,
      "image_path": "/storages/images/output/camera_yolo/results/images/detection_20250922_133106.jpg",
    "detections": [
      {
        "class": "plastic_bottle",
        "confidence": 0.95,
          "bbox": [100, 100, 200, 200]
      }
    ],
    "status": "processed",
      "timestamp": "2025-09-22T13:31:06.000000Z"
    },
    "timestamp": "2025-09-22T13:31:06.000000Z"
  },
  "message": "RVM status retrieved successfully"
}
```

### **Trigger Processing** ⚠️ **UPDATED ENDPOINT**
```http
POST /api/v2/detection-results/trigger-processing
Authorization: Bearer {token}
Content-Type: application/json

{
  "rvm_id": 1,
  "command": "run_inference"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Processing command 'run_inference' triggered for RVM 1"
}
```

### **Get Processing History** ⚠️ **UPDATED ENDPOINT**
```http
GET /api/v2/detection-results/processing-history
Authorization: Bearer {token}
```

**Query Parameters:**
- `rvm_id` (optional): Filter by RVM ID
- `limit` (optional): Number of results (default: 10)
- `date_from` (optional): Start date filter
- `date_to` (optional): End date filter

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "rvm_id": 1,
      "processing_engine_id": 25,
      "detection_type": "yolo11",
      "status": "completed",
      "processing_time": 1.5,
      "objects_detected": 2,
      "confidence_avg": 0.92,
      "created_at": "2025-09-22T13:31:06.000000Z"
    }
  ],
  "message": "Processing history retrieved successfully"
}
```

## 💰 Deposits

### **List Deposits**
```http
GET /api/v2/deposits
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "rvm_id": 1,
      "user_id": 1,
      "waste_type": "plastic",
      "quantity": 1,
      "weight": 0.5,
      "reward_amount": 100,
      "status": "completed",
      "location": "Jetson Orin Nano Test",
      "notes": "Test deposit from updated API client",
      "created_at": "2025-09-22T13:31:06.000000Z",
      "updated_at": "2025-09-22T13:31:06.000000Z"
    }
  ],
  "message": "Deposits retrieved successfully"
}
```

### **Create Deposit**
```http
POST /api/v2/deposits
Authorization: Bearer {token}
Content-Type: application/json

{
  "rvm_id": 1,
  "user_id": 1,
  "waste_type": "plastic",
  "quantity": 1,
  "weight": 0.5,
  "location": "Jetson Orin Nano Test",
  "notes": "Test deposit from updated API client"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "rvm_id": 1,
    "user_id": 1,
    "waste_type": "plastic",
    "quantity": 1,
    "weight": 0.5,
    "reward_amount": 100,
    "status": "pending",
    "location": "Jetson Orin Nano Test",
    "notes": "Test deposit from updated API client",
    "created_at": "2025-09-22T13:31:06.000000Z",
    "updated_at": "2025-09-22T13:31:06.000000Z"
  },
  "message": "Deposit created successfully"
}
```

### **Process Deposit**
```http
POST /api/v2/deposits/{id}/process
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "completed",
  "reward_amount": 100,
  "ai_analysis": "Plastic bottle detected with 95% confidence",
  "cv_analysis": "YOLO11 detection successful"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "rvm_id": 1,
    "user_id": 1,
    "waste_type": "plastic",
    "quantity": 1,
    "weight": 0.5,
    "reward_amount": 100,
    "status": "completed",
    "location": "Jetson Orin Nano Test",
    "notes": "Test deposit from updated API client",
    "ai_analysis": "Plastic bottle detected with 95% confidence",
    "cv_analysis": "YOLO11 detection successful",
    "created_at": "2025-09-22T13:31:06.000000Z",
    "updated_at": "2025-09-22T13:31:06.000000Z"
  },
  "message": "Deposit processed successfully"
}
```

### **Get Deposit Statistics**
```http
GET /api/v2/deposits/statistics
Authorization: Bearer {token}
```

## 🏪 RVM Management

### **⚠️ IMPORTANT: IP Address for Remote Access & Maintenance**

**IP Address (`ip_address`) dan Port (`port`) sangat penting untuk:**
- **Remote Access:** Akses jarak jauh ke RVM untuk monitoring dan control
- **Maintenance Mode:** Mode maintenance untuk perawatan RVM
- **Health Check:** Pengecekan status kesehatan RVM
- **Command Execution:** Eksekusi perintah remote ke RVM
- **Metrics Collection:** Pengumpulan data metrics dari RVM

**Port Configuration:**

**Server Ports (MyRVM-Platform):**
- **Port 8000:** Web Dashboard (Admin Panel) - Server menyediakan
- **Port 8001:** API Endpoints (REST API) - Server menyediakan

**Edge Ports (RVM-Jetson):**
- **Port 5000:** Remote Access Controller (Main service) - RVM menyediakan
- **Port 5001:** GUI Client (Touch screen interface) - RVM menyediakan
- **Port 5002:** Camera Manager (On-demand camera service) - RVM menyediakan

**Contoh Penggunaan:**
```python
# RVM dengan IP untuk remote access
rvm_data = {
    'name': 'RVM-Orin1',
    'ip_address': '192.168.1.100',  # IP address RVM
    'port': 5000,                   # Port untuk remote access
    'status': 'active'
}

# Setelah register, bisa digunakan untuk:
# - Remote access: http://rvm_ip:5000 (Server → RVM)
# - Maintenance mode: POST /api/v2/rvms/{id}/maintenance (Server → RVM)
# - Health check: GET http://rvm_ip:5000/health (Server → RVM)
# - Metrics collection: POST http://server_ip:8001/api/v2/rvms/{id}/metrics (RVM → Server)
```

### **List RVMs** ⚠️ **AUTHENTICATION REQUIRED**
```http
GET /api/v2/rvms
Authorization: Bearer {token}
```

### **Get RVM**
```http
GET /api/v2/rvms/{id}
Authorization: Bearer {token}
```

### **Create RVM**
```http
POST /api/v2/rvms
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "RVM-001",
  "location_description": "Lobby Building A",
  "status": "active",
  "ip_address": "rvm_ip",  // atau "100.117.234.2" (Tailscale)
  "port": 5000,
  "api_key": "custom_api_key_123"
}
```

After creation in Admin Dashboard, the API key is shown to the operator for use on the RVM device UI (copy and store securely).

### **Update RVM**
```http
PUT /api/v2/rvms/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated RVM-001",
  "status": "maintenance",
  "ip_address": "rvm_ip",  // atau "100.117.234.2" (Tailscale)
  "port": 5000
}
```

**Field Requirements:**
- `name` (required): RVM name (unique, max 255 chars)
- `location_description` (optional): Location description (max 1000 chars)
- `status` (required): RVM status (`active`, `inactive`, `maintenance`, `full`)
- `ip_address` (optional): IP address of RVM device (for remote access, maintenance mode)
- `port` (optional): Port number for RVM services (default: 5000)
- `api_key` (optional): API key for RVM authentication (auto-generated if not provided)

### **RVM Self-Claim** (NEW)
```http
POST /api/v2/rvm/self/claim
X-API-Key: {api_key}
Content-Type: application/json

{
  "rvm_id": 1,
  "device_name": "RVM-Orin1",
  "software_version": "v1.2.3",
  "timezone": "Asia/Jakarta"
}
```

### **RVM Self-Update** (NEW)
```http
PATCH /api/v2/rvm/self/update
X-API-Key: {api_key}
Content-Type: application/json

{
  "ip_address": "rvm_ip",  // atau "100.117.234.2" (Tailscale)
  "port": 5000,
  "timezone": "Asia/Jakarta"
}
```

Notes:
- RVM Self APIs use API key authentication and are meant to be called by the RVM device UI after Admin pre-registration
- The server updates the RVM record and the changes are reflected on the Admin dashboard

**Response:**
```json
{
  "success": true,
  "message": "RVM created successfully",
  "data": {
    "id": 1,
    "name": "RVM-001",
    "location_description": "Lobby Building A",
    "status": "active",
    "ip_address": "rvm_ip",  // atau "100.117.234.2" (Tailscale)
    "port": 5000,
    "api_key": "rvm_abc123def456...",
    "created_at": "2025-09-22T13:31:06.000000Z"
  }
}
```

### **Get RVM Statistics**
```http
GET /api/v2/rvms/{id}/statistics
Authorization: Bearer {token}
```

## 📁 File Upload

### **Upload Image File**
```http
POST /api/v2/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [image file]
metadata: {
  "rvm_id": 1,
  "detection_type": "yolo11",
  "timestamp": "2025-09-22T13:31:06.000000Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "file_path": "/storages/images/uploaded/detection_20250922_133106.jpg",
    "file_size": 245760,
    "mime_type": "image/jpeg",
    "metadata": {
      "rvm_id": 1,
      "detection_type": "yolo11",
      "timestamp": "2025-09-22T13:31:06.000000Z"
    }
  },
  "message": "File uploaded successfully"
}
```

## 🔧 Installation Method APIs

**Provider:** RVM-Jetson (Edge Device)  
**Base URL:** `http://rvm_ip:8080` atau `http://localhost:8080` (jika menggunakan port forwarding)  
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
    "total_steps": 5
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

### **Server Connectivity Test**
```http
POST /api/server/test
Content-Type: application/json

{
  "server_url": "http://100.123.143.87:8001"
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
    },
    "gemini": {
      "status": "disabled",
      "reason": "Not available"
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

### **Deployment Start**
```http
POST /api/deploy/start
```

**Response:**
```json
{
  "success": true,
  "data": {
    "deployment_id": "deploy_20250923_123456",
    "status": "started",
    "estimated_time": "5 minutes"
  }
}
```

## 🌐 Remote Access APIs

**Provider:** RVM-Jetson (Edge Device)  
**Base URL:** `http://rvm_ip:5000` atau `http://localhost:5000` (jika menggunakan port forwarding)  
**Purpose:** Remote control, monitoring, command execution  
**Access:** Remote endpoints (API key authentication)

### **Remote Access Health Check**
```http
GET /health
```

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-09-23T12:34:56.000000Z",
    "services": {
      "remote_access": "operational",
      "camera_service": "operational",
      "gui_client": "operational"
    }
  }
}
```

### **Remote Command Execution**
```http
POST /api/remote/command
X-API-Key: {api_key}
Content-Type: application/json

{
  "command": "run_inference",
  "parameters": {
    "image_path": "/path/to/image.jpg",
    "confidence_threshold": 0.5
  }
}
```

### **System Metrics Collection**
```http
GET /api/metrics
X-API-Key: {api_key}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "system": {
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "gpu_usage": 23.1,
      "temperature": 42.5
    },
    "network": {
      "wifi_connected": true,
      "ip_address": "192.168.1.11",
      "internet_access": true
    },
    "timestamp": "2025-09-23T12:34:56.000000Z"
  }
}
```

### **Remote Maintenance Mode**
```http
POST /api/maintenance/start
X-API-Key: {api_key}
Content-Type: application/json

{
  "reason": "Hardware calibration",
  "estimated_duration": "30 minutes"
}
```

## 📱 GUI Client APIs

**Provider:** RVM-Jetson (Edge Device)  
**Base URL:** `http://rvm_ip:5001` atau `http://localhost:5001` (jika menggunakan port forwarding)  
**Purpose:** Touch screen interface, user interaction  
**Access:** Local endpoints (no authentication required)

### **GUI Status**
```http
GET /api/gui/status
```

### **User Authentication via QR Code**
```http
POST /api/gui/authenticate
Content-Type: application/json

{
  "qr_code": "base64_encoded_qr_data"
}
```

### **Touch Screen Events**
```http
POST /api/gui/touch
Content-Type: application/json

{
  "x": 150,
  "y": 200,
  "action": "tap",
  "timestamp": "2025-09-23T12:34:56.000000Z"
}
```

## 📷 Camera Service APIs

**Provider:** RVM-Jetson (Edge Device)  
**Base URL:** `http://rvm_ip:5002` atau `http://localhost:5002` (jika menggunakan port forwarding)  
**Purpose:** Camera control, image capture, streaming  
**Access:** Local endpoints (API key authentication)

### **Camera Status**
```http
GET /api/camera/status
X-API-Key: {api_key}
```

### **Capture Image**
```http
POST /api/camera/capture
X-API-Key: {api_key}
Content-Type: application/json

{
  "resolution": "1920x1080",
  "format": "jpeg",
  "quality": 95
}
```

### **Start Video Stream**
```http
POST /api/camera/stream/start
X-API-Key: {api_key}
Content-Type: application/json

{
  "resolution": "1280x720",
  "fps": 30,
  "format": "mjpeg"
}
```

### **Stop Video Stream**
```http
POST /api/camera/stream/stop
X-API-Key: {api_key}
```

## 🏥 Health Check

### **Server Health Check**
```http
GET /api/health-check
```

**Response:**
```json
{
  "success": true,
  "message": "MyRVM Platform is healthy",
  "data": {
    "status": "healthy",
    "timestamp": "2025-09-22T13:31:06.000000Z",
    "server": {
      "name": "MyRVM Platform",
      "version": "1.0.0",
      "environment": "production",
      "uptime": "up 2 days, 3 hours"
    },
    "database": {
      "status": "connected",
      "connection": "pgsql"
    },
    "services": {
      "api": "operational",
      "authentication": "operational",
      "metrics": "operational",
      "commands": "operational"
    }
  }
}
```

## 🚨 Error Responses

### **Validation Error (422)**
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "type": ["The selected type is invalid."],
    "server_address": ["The server address field is required."],
    "port": ["The port field is required."]
  }
}
```

### **Authentication Error (401)**
```json
{
  "success": false,
  "message": "Unauthorized"
}
```

### **Not Found Error (404)**
```json
{
  "success": false,
  "message": "Processing engine not found"
}
```

### **Server Error (500)**
```json
{
  "success": false,
  "message": "Internal server error",
  "error": "Call to undefined relationship [reverseVendingMachines] on model [App\\Models\\ProcessingEngine]"
}
```

## 🔧 Python Client Usage

### **Basic Usage**
```python
from myrvm_integration.api_client.myrvm_api_client import MyRVMAPIClient

# Initialize client
client = MyRVMAPIClient(
    base_url="http://server_ip:8001",  # atau http://100.123.143.87:8001 (Tailscale)
    use_tunnel=False
)

# Login
success, response = client.login("admin@myrvm.com", "password")
if success:
    print(f"Login successful: {response['data']['token']}")
else:
    print(f"Login failed: {response['error']}")

# Register processing engine
engine_data = {
    'name': 'Jetson Orin Nano - CV System',
    'type': 'nvidia_cuda',
    'server_address': 'rvm_ip',  # atau '100.117.234.2' (Tailscale)
    'port': 5000,
    'gpu_memory_limit': 8,
    'docker_gpu_passthrough': True,
    'model_path': '/models/yolo11n.pt',
    'processing_timeout': 30,
    'auto_failover': True,
    'is_active': True
}

success, response = client.register_processing_engine(engine_data)
if success:
    print(f"Engine registered: {response['data']['id']}")
else:
    print(f"Registration failed: {response['error']}")

# Register RVM (Minimal)
rvm_data_minimal = {
    'name': 'RVM-001',
    'status': 'active'
}

success, response = client.create_rvm(rvm_data_minimal)
if success:
    print(f"RVM registered: {response['data']['id']}")
    print(f"API Key: {response['data']['api_key']}")
else:
    print(f"Registration failed: {response['error']}")

# Register RVM (Complete with IP)
rvm_data_complete = {
    'name': 'RVM-Orin1',
    'location_description': 'Lobby Building A - Ground Floor',
    'status': 'active',
    'ip_address': 'rvm_ip',  # atau '100.117.234.2' (Tailscale) - IP address for remote access & maintenance
    'port': 5000,            # Port for RVM services
    'api_key': 'rvm_orin1_api_key_2025'
}

success, response = client.create_rvm(rvm_data_complete)
if success:
    print(f"RVM registered: {response['data']['id']}")
    print(f"Name: {response['data']['name']}")
    print(f"IP: {response['data']['ip_address']}")
    print(f"Port: {response['data']['port']}")
    print(f"API Key: {response['data']['api_key']}")
else:
    print(f"Registration failed: {response['error']}")
```

### **Advanced Usage**
```python
# Upload detection results
detection_data = {
    'rvm_id': 1,
    'image_path': '/storages/images/output/detection_20250922_133106.jpg',
    'detections': [
        {
            'class': 'plastic_bottle',
            'confidence': 0.95,
            'bbox': [100, 100, 200, 200],
            'segmentation_mask': 'base64_encoded_mask_data'
        }
    ],
    'status': 'processed',
    'timestamp': '2025-09-22T13:31:06.000000Z'
}

success, response = client.upload_detection_results(detection_data)
if success:
    print(f"Detection results uploaded: {response['data']['id']}")

# Create deposit
deposit_data = {
    'rvm_id': 1,
    'user_id': 1,
    'waste_type': 'plastic',
    'quantity': 1,
    'weight': 0.5,
    'location': 'Jetson Orin Nano Test',
    'notes': 'Test deposit from API client'
}

success, response = client.create_deposit(deposit_data)
if success:
    print(f"Deposit created: {response['data']['id']}")

# Get RVM status (updated endpoint)
success, response = client.get_rvm_status(1)
if success:
    print(f"RVM status: {response['data']['current_status']}")
```

## 📊 Rate Limits

- **Authentication:** 10 requests per minute
- **Processing Engines:** 100 requests per minute
- **Detection Results:** 200 requests per minute
- **Deposits:** 100 requests per minute
- **File Upload:** 50 requests per minute

## 🔒 Security

### **Authentication**
- Bearer token authentication required for most endpoints
- Public endpoints: `/api/health-check`, `/api/v2/auth/login`, `/api/v2/auth/register`
- Protected endpoints: All others require Bearer token
- Tokens expire after 24 hours
- Refresh token available for extended sessions

### **Rate Limiting**
- Rate limits applied per IP address
- Exceeded limits return 429 status code
- Rate limit headers included in responses

### **Data Validation**
- All input data validated on server-side
- SQL injection protection
- XSS protection for text fields

## ⚠️ **IMPORTANT CHANGES FROM V1.0.0**

### **Updated Endpoints:**
- ❌ `/api/v2/rvm-status/{id}` → ✅ `/api/v2/detection-results/rvm/{rvmId}/status`
- ❌ `/api/v2/trigger-processing` → ✅ `/api/v2/detection-results/trigger-processing`
- ❌ `/api/v2/processing-history` → ✅ `/api/v2/detection-results/processing-history`

### **Authentication Changes:**
- ❌ Most endpoints were public → ✅ Most endpoints now require authentication
- ✅ Public endpoints: Health check, auth login/register, RVM metrics
- ✅ Protected endpoints: All management and data endpoints

### **Base URL Changes:**
- ❌ `http://172.28.233.83:8001` → ✅ `http://server_ip:8001` (production)

## 📊 **API Endpoints Summary**

### **📈 Total Endpoints: 50+ APIs**

#### **🏢 MyRVM-Platform (Server) - 35+ APIs**
- **🔐 Authentication APIs:** 3 endpoints
- **🤖 Processing Engine APIs:** 8 endpoints  
- **📸 Detection Results APIs:** 6 endpoints
- **💰 Deposit Management APIs:** 4 endpoints
- **🏪 RVM Management APIs:** 5 endpoints
- **📁 File Upload APIs:** 2 endpoints
- **🏥 Health Check APIs:** 2 endpoints
- **📊 Additional APIs:** 5+ endpoints

#### **🔧 RVM-Jetson (Edge Device) - 15+ APIs**
- **🔧 Installation Method APIs:** 8 endpoints (Port 8080)
- **🌐 Remote Access APIs:** 4 endpoints (Port 5000)
- **📱 GUI Client APIs:** 3 endpoints (Port 5001)
- **📷 Camera Service APIs:** 4 endpoints (Port 5002)

### **🌐 Network Access Summary**

#### **MyRVM-Platform Server:**
- **Primary:** `100.123.143.87:8001` (Tailscale)
- **Backup:** `172.28.233.83:8001` (ZeroTier)
- **Local:** `localhost:8001` (SSH tunnel)

#### **RVM-Jetson Edge Device:**
- **Primary:** `100.117.234.2` (Tailscale)
- **Backup:** `172.28.93.97` (ZeroTier)
- **Local:** `localhost` (SSH tunnel)

#### **Port Configuration:**
- **8000:** Web Dashboard (Server)
- **8001:** API Endpoints (Server)
- **5000:** Remote Access (RVM)
- **5001:** GUI Client (RVM)
- **5002:** Camera Service (RVM)
- **8080:** Installation Method (RVM)

### **🔐 Authentication Summary**

#### **Public Endpoints (No Auth Required):**
- Health checks
- Authentication login/register
- Installation method APIs
- GUI client APIs

#### **Protected Endpoints (Auth Required):**
- **Bearer Token:** MyRVM-Platform APIs
- **API Key:** RVM remote access APIs
- **X-API-Key Header:** Camera service APIs

### **📋 Usage Examples by Category**

#### **🔧 Installation & Setup:**
```bash
# Hardware detection
curl http://rvm_ip:8080/api/hardware/detect

# Network scan
curl http://rvm_ip:8080/api/network/scan

# Server test
curl -X POST http://rvm_ip:8080/api/server/test \
  -H "Content-Type: application/json" \
  -d '{"server_url": "http://server_ip:8001"}'
```

#### **🤖 AI Processing:**
```bash
# Register processing engine
curl -X POST http://100.123.143.87:8001/api/v2/processing-engines \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Jetson Orin Nano", "type": "nvidia_cuda"}'

# Upload detection results
curl -X POST http://100.123.143.87:8001/api/v2/detection-results \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"rvm_id": 1, "detections": [...]}'
```

#### **🌐 Remote Control:**
```bash
# Remote command execution
curl -X POST http://100.117.234.2:5000/api/remote/command \
  -H "X-API-Key: {api_key}" \
  -H "Content-Type: application/json" \
  -d '{"command": "run_inference"}'

# System metrics
curl http://100.117.234.2:5000/api/metrics \
  -H "X-API-Key: {api_key}"
```

#### **📷 Camera Operations:**
```bash
# Capture image
curl -X POST http://100.117.234.2:5002/api/camera/capture \
  -H "X-API-Key: {api_key}" \
  -H "Content-Type: application/json" \
  -d '{"resolution": "1920x1080", "format": "jpeg"}'

# Start video stream
curl -X POST http://100.117.234.2:5002/api/camera/stream/start \
  -H "X-API-Key: {api_key}" \
  -H "Content-Type: application/json" \
  -d '{"resolution": "1280x720", "fps": 30}'
```

## 📚 Related Documentation

- [Changelog](CHANGELOG.md)
- [Technical Changes](TECHNICAL_CHANGES.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Integration Test Report](INTEGRATION_TEST_REPORT.md)

---

**Last Updated:** September 23, 2025  
**Next Review:** September 30, 2025  
**Maintainer:** RVM System (Jetson Orin)  
**Status:** ✅ Production Ready (Comprehensive API Documentation)