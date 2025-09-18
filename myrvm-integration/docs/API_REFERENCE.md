# API Reference

**Project:** MyRVM Platform Integration with Jetson Orin Nano  
**Date:** September 18, 2025  
**Version:** 1.0.0  

## 📋 Overview

This document provides comprehensive API reference for the MyRVM Platform integration with the Jetson Orin Nano CV system.

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

response = requests.post('http://172.28.233.83:8001/api/v2/auth/login', 
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
      "server_address": "172.28.93.97",
      "port": 5000,
      "gpu_memory_limit": 8,
      "docker_gpu_passthrough": true,
      "model_path": "/models/yolo11n.pt",
      "processing_timeout": 30,
      "auto_failover": true,
      "is_active": true,
      "is_online": true,
      "last_ping_at": "2025-09-18T17:30:00.000000Z",
      "created_at": "2025-09-18T17:30:00.000000Z",
      "updated_at": "2025-09-18T17:30:00.000000Z"
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
  "server_address": "172.28.93.97",
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
    "server_address": "172.28.93.97",
    "port": 5000,
    "gpu_memory_limit": 8,
    "docker_gpu_passthrough": true,
    "model_path": "/models/yolo11n.pt",
    "processing_timeout": 30,
    "auto_failover": true,
    "is_active": true,
    "is_online": true,
    "last_ping_at": "2025-09-18T17:30:00.000000Z",
    "created_at": "2025-09-18T17:30:00.000000Z",
    "updated_at": "2025-09-18T17:30:00.000000Z"
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

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 25,
    "name": "Jetson Orin Nano - CV System",
    "type": "nvidia_cuda",
    "server_address": "172.28.93.97",
    "port": 5000,
    "gpu_memory_limit": 8,
    "docker_gpu_passthrough": true,
    "model_path": "/models/yolo11n.pt",
    "processing_timeout": 30,
    "auto_failover": true,
    "is_active": true,
    "is_online": true,
    "last_ping_at": "2025-09-18T17:30:00.000000Z",
    "created_at": "2025-09-18T17:30:00.000000Z",
    "updated_at": "2025-09-18T17:30:00.000000Z"
  },
  "message": "Processing engine retrieved successfully"
}
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

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 25,
    "name": "Updated Jetson Orin Nano - CV System",
    "type": "nvidia_cuda",
    "server_address": "172.28.93.97",
    "port": 5000,
    "gpu_memory_limit": 8,
    "docker_gpu_passthrough": true,
    "model_path": "/models/yolo11n.pt",
    "processing_timeout": 30,
    "auto_failover": true,
    "is_active": false,
    "is_online": true,
    "last_ping_at": "2025-09-18T17:30:00.000000Z",
    "created_at": "2025-09-18T17:30:00.000000Z",
    "updated_at": "2025-09-18T17:35:00.000000Z"
  },
  "message": "Processing engine updated successfully"
}
```

### **Delete Processing Engine**
```http
DELETE /api/v2/processing-engines/{id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Processing engine deleted successfully"
}
```

### **Ping Processing Engine**
```http
POST /api/v2/processing-engines/{id}/ping
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 25,
    "name": "Jetson Orin Nano - CV System",
    "is_active": true,
    "is_online": true,
    "last_ping_at": "2025-09-18T17:35:00.000000Z",
    "server_address": "172.28.93.97",
    "port": 5000
  },
  "message": "Processing engine pinged successfully"
}
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

**Response:**
```json
{
  "success": true,
  "message": "Processing engine Jetson Orin Nano - CV System assigned to RVM 1 successfully"
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
      "image_path": "/storages/images/output/camera_yolo/results/images/detection_20250918_150800.jpg",
      "detections": [
        {
          "class": "plastic_bottle",
          "confidence": 0.95,
          "bbox": [100, 100, 200, 200],
          "segmentation_mask": "base64_encoded_mask_data"
        }
      ],
      "status": "processed",
      "timestamp": "2025-09-18T15:08:00.000000Z",
      "created_at": "2025-09-18T15:08:00.000000Z",
      "updated_at": "2025-09-18T15:08:00.000000Z"
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
  "image_path": "/storages/images/output/camera_yolo/results/images/detection_20250918_150800.jpg",
  "detections": [
    {
      "class": "plastic_bottle",
      "confidence": 0.95,
      "bbox": [100, 100, 200, 200],
      "segmentation_mask": "base64_encoded_mask_data"
    }
  ],
  "status": "processed",
  "timestamp": "2025-09-18T15:08:00.000000Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "rvm_id": 1,
    "image_path": "/storages/images/output/camera_yolo/results/images/detection_20250918_150800.jpg",
    "detections": [
      {
        "class": "plastic_bottle",
        "confidence": 0.95,
        "bbox": [100, 100, 200, 200],
        "segmentation_mask": "base64_encoded_mask_data"
      }
    ],
    "status": "processed",
    "timestamp": "2025-09-18T15:08:00.000000Z",
    "created_at": "2025-09-18T15:08:00.000000Z",
    "updated_at": "2025-09-18T15:08:00.000000Z"
  },
  "message": "Detection result stored successfully"
}
```

### **Get Detection Result**
```http
GET /api/v2/detection-results/{id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "rvm_id": 1,
    "image_path": "/storages/images/output/camera_yolo/results/images/detection_20250918_150800.jpg",
    "detections": [
      {
        "class": "plastic_bottle",
        "confidence": 0.95,
        "bbox": [100, 100, 200, 200],
        "segmentation_mask": "base64_encoded_mask_data"
      }
    ],
    "status": "processed",
    "timestamp": "2025-09-18T15:08:00.000000Z",
    "created_at": "2025-09-18T15:08:00.000000Z",
    "updated_at": "2025-09-18T15:08:00.000000Z"
  },
  "message": "Detection result retrieved successfully"
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
      "created_at": "2025-09-18T15:08:00.000000Z",
      "updated_at": "2025-09-18T15:08:00.000000Z"
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
    "created_at": "2025-09-18T15:08:00.000000Z",
    "updated_at": "2025-09-18T15:08:00.000000Z"
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
    "created_at": "2025-09-18T15:08:00.000000Z",
    "updated_at": "2025-09-18T15:10:00.000000Z"
  },
  "message": "Deposit processed successfully"
}
```

## 🏪 RVM Status

### **Get RVM Status**
```http
GET /api/v2/rvm-status/{id}
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
      "image_path": "/storages/images/output/camera_yolo/results/images/detection_20250918_150800.jpg",
      "detections": [
        {
          "class": "plastic_bottle",
          "confidence": 0.95,
          "bbox": [100, 100, 200, 200]
        }
      ],
      "status": "processed",
      "timestamp": "2025-09-18T15:08:00.000000Z"
    },
    "timestamp": "2025-09-18T17:35:00.000000Z"
  },
  "message": "RVM status retrieved successfully"
}
```

## ⚡ Trigger Processing

### **Trigger Processing**
```http
POST /api/v2/trigger-processing
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
  "timestamp": "2025-09-18T15:08:00.000000Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "file_path": "/storages/images/uploaded/detection_20250918_150800.jpg",
    "file_size": 245760,
    "mime_type": "image/jpeg",
    "metadata": {
      "rvm_id": 1,
      "detection_type": "yolo11",
      "timestamp": "2025-09-18T15:08:00.000000Z"
    }
  },
  "message": "File uploaded successfully"
}
```

## 🔍 Processing History

### **Get Processing History**
```http
GET /api/v2/processing-history
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
      "created_at": "2025-09-18T15:08:00.000000Z"
    }
  ],
  "message": "Processing history retrieved successfully"
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
    base_url="http://172.28.233.83:8001",
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
    'server_address': '172.28.93.97',
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
```

### **Advanced Usage**
```python
# Upload detection results
detection_data = {
    'rvm_id': 1,
    'image_path': '/storages/images/output/detection_20250918_150800.jpg',
    'detections': [
        {
            'class': 'plastic_bottle',
            'confidence': 0.95,
            'bbox': [100, 100, 200, 200],
            'segmentation_mask': 'base64_encoded_mask_data'
        }
    ],
    'status': 'processed',
    'timestamp': '2025-09-18T15:08:00.000000Z'
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

# Get RVM status
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
- Bearer token authentication required for all endpoints
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

## 📚 Related Documentation

- [Changelog](CHANGELOG.md)
- [Technical Changes](TECHNICAL_CHANGES.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Integration Test Report](INTEGRATION_TEST_REPORT.md)

---

**Last Updated:** September 18, 2025  
**Next Review:** September 25, 2025  
**Maintainer:** AI Assistant  
**Status:** ✅ Production Ready (Basic Features)
