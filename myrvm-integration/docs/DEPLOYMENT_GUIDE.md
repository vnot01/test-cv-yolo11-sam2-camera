# Deployment Guide

**Project:** MyRVM Platform Integration with Jetson Orin Nano  
**Date:** September 18, 2025  
**Version:** 1.0.0  

## 📋 Overview

This guide provides step-by-step instructions for deploying the MyRVM Platform integration with the Jetson Orin Nano CV system.

## 🚀 Prerequisites

### **Server Requirements (MyRVM Platform)**
- Docker and Docker Compose installed
- Laravel 10.x application
- PostgreSQL database
- Nginx web server
- Minimum 4GB RAM
- Minimum 20GB storage

### **Client Requirements (Jetson Orin)**
- NVIDIA Jetson Orin Nano
- Ubuntu 22.04 LTS
- Python 3.10+
- Virtual environment setup
- ZeroTier network access
- Minimum 8GB RAM
- Minimum 16GB storage

### **Network Requirements**
- ZeroTier network configured
- RVM IP: 172.28.93.97
- Platform IP: 172.28.233.83:8001
- Network latency: < 50ms

## 🔧 Server-side Deployment (MyRVM Platform)

### **Step 1: Update MyRVM Platform**

```bash
# Navigate to MyRVM Platform directory
cd /home/my/MySuperApps/MyRVM-Platform

# Pull latest changes
git pull origin main

# Verify changes
git log --oneline -5
```

### **Step 2: Apply Database Migrations**

```bash
# Check migration status
docker compose exec app php artisan migrate:status

# Apply pending migrations
docker compose exec app php artisan migrate

# Verify database structure
docker compose exec app php artisan tinker
>>> App\Models\ProcessingEngine::count()
>>> exit
```

### **Step 3: Restart Services**

```bash
# Restart all services
docker compose restart

# Check service status
docker compose ps

# Verify API endpoints
curl http://localhost:8001/api/v2/processing-engines
```

### **Step 4: Verify Server Configuration**

```bash
# Check Laravel configuration
docker compose exec app php artisan config:cache

# Check route registration
docker compose exec app php artisan route:list --path=api/v2

# Test database connection
docker compose exec app php artisan tinker
>>> DB::connection()->getPdo();
>>> exit
```

## 🔧 Client-side Deployment (Jetson Orin)

### **Step 1: Update Jetson Orin Project**

```bash
# Navigate to Jetson Orin project
cd /home/my/test-cv-yolo11-sam2-camera

# Pull latest changes
git pull origin main

# Verify changes
git log --oneline -5
```

### **Step 2: Setup Virtual Environment**

```bash
# Activate virtual environment
source myenv/bin/activate

# Verify Python version
python --version

# Install/update dependencies
pip install -r myrvm-integration/requirements.txt
```

### **Step 3: Configure Network Settings**

```bash
# Check ZeroTier status
sudo zerotier-cli status

# Verify network connectivity
ping 172.28.233.83

# Test HTTP connectivity
curl http://172.28.233.83:8001/
```

### **Step 4: Update Configuration**

```bash
# Edit configuration file
nano myrvm-integration/main/config.json
```

**Configuration Template:**
```json
{
  "myrvm_base_url": "http://172.28.233.83:8001",
  "myrvm_tunnel_url": "https://your-tunnel-domain.com",
  "api_token": null,
  "camera_index": 0,
  "rvm_id": 1,
  "models_dir": "../models",
  "capture_interval": 5.0,
  "confidence_threshold": 0.5,
  "auto_processing": true,
  "debug_mode": true,
  "jetson_ip": "172.28.93.97",
  "jetson_port": 5000,
  "log_level": "INFO",
  "max_processing_queue": 10,
  "processing_timeout": 30.0,
  "retry_attempts": 3,
  "retry_delay": 2.0,
  "use_tunnel": false,
  "tunnel_type": "zerotier",
  "fallback_to_local": true,
  "zerotier_network": {
    "rvm_ip": "172.28.93.97",
    "platform_ip": "172.28.233.83",
    "platform_port": 8001,
    "network_id": "9bee8941b52c05b9"
  }
}
```

## 🧪 Testing Deployment

### **Step 1: Run Basic Connectivity Tests**

```bash
# Test basic API connectivity
python3 myrvm-integration/debug/test_api_connection.py

# Expected output:
# 🚀 MyRVM Platform API Connection Test
# ============================================================
# Testing connection to: http://172.28.233.83:8001
# 🔍 Testing basic connectivity...
#    Status: 200
#    ✅ Basic connectivity successful
# ...
# 🎯 Overall Result: 6/6 tests passed
# 🎉 All tests passed! API integration is working correctly.
```

### **Step 2: Run Processing Engine Registration Test**

```bash
# Test processing engine registration
python3 myrvm-integration/debug/test_processing_engine_registration.py

# Expected output:
# 🚀 Processing Engine Registration Test
# ============================================================
# Testing with: http://172.28.233.83:8001
# 🔐 Getting authentication token...
# ✅ Authentication token obtained: 21|epxqGDMSdKgZ357EmWxlQBOuh4XtqRJD0WBzhs934cd94f41...
# 🤖 Testing processing engine registration with correct fields...
#    Status: 201
#    ✅ Processing engine registered successfully
#    Engine ID: 25
# ...
# 🎯 Overall Result: 2/2 tests passed
# 🎉 All processing engine tests passed!
```

### **Step 3: Run Full Integration Test**

```bash
# Test complete integration
python3 myrvm-integration/debug/test_full_integration.py

# Expected output:
# 🚀 MyRVM Platform - Full Integration Test
# ============================================================
# Testing complete workflow with: http://172.28.233.83:8001
# 🔐 Getting authentication token...
# ✅ Authentication token obtained: 21|epxqGDMSdKgZ357EmWxlQBOuh4XtqRJD0WBzhs934cd94f41...
# 🤖 Testing register processing engine...
#    Status: 201
#    ✅ Processing engine registered successfully
#    Engine ID: 25
# ...
# 🎯 Overall Result: 3/5 tests passed
# ⚠️  Some integration tests failed. Check the logs above for details.
```

## 🚀 Production Deployment

### **Step 1: Start Main Application**

```bash
# Start Jetson Orin main application
python3 myrvm-integration/main/jetson_main.py

# Expected output:
# 🚀 Jetson Orin Nano - MyRVM Platform Integration
# ============================================================
# 📋 Configuration loaded from: config.json
# 🔧 Initializing camera...
# ✅ Camera initialized: 640x480 @ 25.0 FPS
# 🔐 Authenticating with MyRVM Platform...
# ✅ Authentication successful
# 🤖 Registering as processing engine...
# ✅ Processing engine registered successfully (ID: 25)
# 🎯 Starting processing worker...
# ✅ Processing worker started
# 🎥 Starting camera capture...
# ✅ Camera capture started
# 🚀 Integration started successfully!
```

### **Step 2: Monitor System Status**

```bash
# Check system resources
htop

# Check network connectivity
ping 172.28.233.83

# Check logs
tail -f myrvm-integration/logs/api_client_*.log
tail -f myrvm-integration/logs/integration_test_results.log
```

### **Step 3: Verify Integration**

```bash
# Check processing engine status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://172.28.233.83:8001/api/v2/processing-engines/25

# Check detection results
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://172.28.233.83:8001/api/v2/detection-results

# Check RVM status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://172.28.233.83:8001/api/v2/rvm-status/1
```

## 🔍 Troubleshooting

### **Common Issues and Solutions**

#### **1. Authentication Issues**

**Problem:** 401 Unauthorized
```
❌ Login failed: 401
Response: {"message":"Unauthorized"}
```

**Solution:**
```bash
# Verify admin credentials
curl -X POST http://172.28.233.83:8001/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@myrvm.com","password":"password"}'

# Check user table
docker compose exec app php artisan tinker
>>> App\Models\User::where('email', 'admin@myrvm.com')->first()
>>> exit
```

#### **2. Network Connectivity Issues**

**Problem:** Connection timeout
```
❌ Connection failed to http://172.28.233.83:8001
```

**Solution:**
```bash
# Check ZeroTier status
sudo zerotier-cli status

# Check network connectivity
ping 172.28.233.83

# Check firewall
sudo ufw status

# Test with curl
curl -v http://172.28.233.83:8001/
```

#### **3. Processing Engine Registration Issues**

**Problem:** 422 Validation Error
```
❌ Failed to register processing engine: 422
Response: {"success":false,"message":"Validation failed","errors":{"type":["The selected type is invalid."]}}
```

**Solution:**
```bash
# Use valid engine type
python3 -c "
import requests
import json

engine_data = {
    'name': 'Jetson Orin Nano - CV System',
    'type': 'nvidia_cuda',  # Valid type
    'server_address': '172.28.93.97',
    'port': 5000,
    'gpu_memory_limit': 8,
    'docker_gpu_passthrough': True,
    'model_path': '/models/yolo11n.pt',
    'processing_timeout': 30,
    'auto_failover': True,
    'is_active': True
}

# Test registration
response = requests.post('http://172.28.233.83:8001/api/v2/processing-engines', 
                        json=engine_data, 
                        headers={'Authorization': 'Bearer YOUR_TOKEN'})
print(f'Status: {response.status_code}')
print(f'Response: {response.text}')
"
```

#### **4. Database Issues**

**Problem:** 500 Internal Server Error
```
❌ Processing engines endpoint failed: 500
Response: {"message":"Call to undefined relationship [reverseVendingMachines] on model [App\\Models\\ProcessingEngine]"}
```

**Solution:**
```bash
# Check if server-side changes are applied
docker compose exec app php artisan route:list --path=api/v2

# Check ProcessingEngineController
docker compose exec app cat app/Http/Controllers/Api/V2/ProcessingEngineController.php | grep -A 5 "with("

# Restart services
docker compose restart
```

#### **5. Camera Issues**

**Problem:** Camera not detected
```
❌ Error: Cannot open camera 0
```

**Solution:**
```bash
# Check camera devices
ls /dev/video*

# Check camera permissions
sudo chmod 666 /dev/video0

# Test camera
python3 camera/camera_test.py

# Check USB devices
lsusb
```

### **Debug Commands**

#### **Server-side Debugging**
```bash
# Check Laravel logs
docker compose exec app tail -f storage/logs/laravel.log

# Check API routes
docker compose exec app php artisan route:list --path=api/v2

# Test database connection
docker compose exec app php artisan tinker
>>> App\Models\ProcessingEngine::count()
>>> App\Models\ProcessingEngine::first()
>>> exit

# Check service status
docker compose ps
docker compose logs app
```

#### **Client-side Debugging**
```bash
# Check system resources
htop
free -h
df -h

# Check network connectivity
ping 172.28.233.83
curl -v http://172.28.233.83:8001/

# Check logs
tail -f myrvm-integration/logs/*.log

# Test individual components
python3 myrvm-integration/debug/test_api_connection.py
python3 myrvm-integration/debug/test_processing_engine_registration.py
```

## 📊 Monitoring

### **System Monitoring**

#### **Server-side Monitoring**
```bash
# Monitor Docker containers
docker stats

# Monitor Laravel logs
docker compose exec app tail -f storage/logs/laravel.log

# Monitor database
docker compose exec app php artisan tinker
>>> DB::table('processing_engines')->count()
>>> DB::table('detection_results')->count()
>>> exit
```

#### **Client-side Monitoring**
```bash
# Monitor system resources
htop
nvidia-smi

# Monitor network
ping 172.28.233.83
netstat -tulpn | grep :5000

# Monitor logs
tail -f myrvm-integration/logs/*.log
```

### **Performance Metrics**

#### **Response Times**
- **Basic Connectivity:** ~300ms
- **Authentication:** ~300ms
- **Data Retrieval:** ~200ms
- **Data Upload:** ~400ms
- **Processing Engine Registration:** ~500ms

#### **Success Rates**
- **Basic API Tests:** 100% (6/6)
- **Processing Engine Registration:** 100% (1/1)
- **Advanced Workflow:** 0% (0/5) - Database schema issues

## 🔄 Maintenance

### **Regular Maintenance Tasks**

#### **Daily Tasks**
```bash
# Check system status
docker compose ps
htop

# Check logs for errors
grep -i error myrvm-integration/logs/*.log
docker compose exec app tail -f storage/logs/laravel.log | grep -i error
```

#### **Weekly Tasks**
```bash
# Update dependencies
pip install -r myrvm-integration/requirements.txt --upgrade

# Clean up logs
find myrvm-integration/logs -name "*.log" -mtime +7 -delete

# Check disk space
df -h
```

#### **Monthly Tasks**
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Clean up Docker images
docker system prune -a

# Backup configuration
cp myrvm-integration/main/config.json myrvm-integration/main/config.json.backup
```

## 📚 Related Documentation

- [Changelog](CHANGELOG.md)
- [Technical Changes](TECHNICAL_CHANGES.md)
- [Integration Test Report](INTEGRATION_TEST_REPORT.md)
- [Tunnel Setup Guide](TUNNEL_SETUP.md)

---

**Last Updated:** September 18, 2025  
**Next Review:** September 25, 2025  
**Maintainer:** AI Assistant  
**Status:** ✅ Production Ready (Basic Features)
