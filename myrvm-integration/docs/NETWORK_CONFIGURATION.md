# Network Configuration - Real IP Addresses

**Tanggal:** 2025-09-23  
**Versi:** 1.0.0  
**Status:** Production Configuration  
**Priority:** HIGH

## 📋 Overview

Dokumen ini berisi konfigurasi network yang sesungguhnya untuk sistem RVM, menghindari penggunaan localhost, dummy, atau placeholder IP addresses.

## 🌐 Network Architecture

### **System Components:**

```
┌─────────────────────────────────────────────────────────────┐
│                    RVM System Network                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   RVM-Jetson    │    │ MyRVM-Platform  │                │
│  │  (Edge Device)  │    │   (Server)      │                │
│  │                 │    │                 │                │
│  │ 100.117.234.2   │    │ 100.123.143.87  │                │
│  │ (Tailscale)     │    │ (Tailscale)     │                │
│  │                 │    │                 │                │
│  │ 172.28.93.97    │    │ 172.28.233.83   │                │
│  │ (ZeroTier)      │    │ (ZeroTier)      │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 RVM-Jetson (Edge Device) Configuration

### **Primary Network (Tailscale):**
- **IP Address:** `100.117.234.2`
- **Network:** Tailscale VPN
- **Status:** Primary production network
- **Access:** Remote access enabled

### **Backup Network (ZeroTier):**
- **IP Address:** `172.28.93.97`
- **Network:** ZeroTier VPN
- **Status:** Backup network
- **Access:** Failover network

### **Service Ports:**

| Service | Port | URL (Tailscale) | URL (ZeroTier) | Purpose |
|---------|------|-----------------|----------------|---------|
| **Installation Method** | 8080 | `http://100.117.234.2:8080` | `http://172.28.93.97:8080` | First-time setup |
| **Remote Access** | 5000 | `http://100.117.234.2:5000` | `http://172.28.93.97:5000` | Remote control |
| **GUI Client** | 5001 | `http://100.117.234.2:5001` | `http://172.28.93.97:5001` | Touch screen |
| **Camera Service** | 5002 | `http://100.117.234.2:5002` | `http://172.28.93.97:5002` | Camera control |

## 🏢 MyRVM-Platform (Server) Configuration

### **Primary Network (Tailscale):**
- **IP Address:** `100.123.143.87`
- **Network:** Tailscale VPN
- **Status:** Primary production network
- **Access:** Remote access enabled

### **Backup Network (ZeroTier):**
- **IP Address:** `172.28.233.83`
- **Network:** ZeroTier VPN
- **Status:** Backup network
- **Access:** Failover network

### **Service Ports:**

| Service | Port | URL (Tailscale) | URL (ZeroTier) | Purpose |
|---------|------|-----------------|----------------|---------|
| **Web Dashboard** | 8000 | `http://100.123.143.87:8000` | `http://172.28.233.83:8000` | Admin panel |
| **API Endpoints** | 8001 | `http://100.123.143.87:8001` | `http://172.28.233.83:8001` | REST API |

## 📝 IP Address Placeholders

### **Placeholder Usage:**

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

## 🔗 Network Access Examples

### **Installation Method APIs:**

#### **Hardware Detection:**
```bash
# Menggunakan placeholder (recommended)
curl http://rvm_ip:8080/api/hardware/detect

# Primary (Tailscale) - contoh IP sesungguhnya
curl http://100.117.234.2:8080/api/hardware/detect

# Backup (ZeroTier) - contoh IP sesungguhnya
curl http://172.28.93.97:8080/api/hardware/detect

# SSH Port Forwarding
ssh -L 8080:rvm_ip:8080 user@rvm
curl http://localhost:8080/api/hardware/detect
```

#### **Network Scan:**
```bash
# Primary (Tailscale)
curl http://100.117.234.2:8080/api/network/scan

# Backup (ZeroTier)
curl http://172.28.93.97:8080/api/network/scan
```

#### **Server Test:**
```bash
# Primary (Tailscale)
curl -X POST http://100.117.234.2:8080/api/server/test \
  -H "Content-Type: application/json" \
  -d '{"server_url": "http://100.123.143.87:8001"}'

# Backup (ZeroTier)
curl -X POST http://172.28.93.97:8080/api/server/test \
  -H "Content-Type: application/json" \
  -d '{"server_url": "http://172.28.233.83:8001"}'
```

### **Production APIs:**

#### **Remote Access:**
```bash
# Primary (Tailscale)
curl http://100.117.234.2:5000/health

# Backup (ZeroTier)
curl http://172.28.93.97:5000/health
```

#### **GUI Client:**
```bash
# Primary (Tailscale)
curl http://100.117.234.2:5001/api/gui/status

# Backup (ZeroTier)
curl http://172.28.93.97:5001/api/gui/status
```

#### **Camera Service:**
```bash
# Primary (Tailscale)
curl http://100.117.234.2:5002/api/camera/status

# Backup (ZeroTier)
curl http://172.28.93.97:5002/api/camera/status
```

### **MyRVM-Platform APIs:**

#### **Health Check:**
```bash
# Primary (Tailscale)
curl http://100.123.143.87:8001/api/health-check

# Backup (ZeroTier)
curl http://172.28.233.83:8001/api/health-check
```

#### **Authentication:**
```bash
# Primary (Tailscale)
curl -X POST http://100.123.143.87:8001/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@myrvm.com", "password": "password"}'

# Backup (ZeroTier)
curl -X POST http://172.28.233.83:8001/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@myrvm.com", "password": "password"}'
```

## 🔧 Service Configuration

### **Installation Method Service:**
```bash
# Start with specific IP
cd /opt/myrvm/installation_method
python3 app.py --host=100.117.234.2 --port=8080

# Or with ZeroTier
python3 app.py --host=172.28.93.97 --port=8080
```

### **Remote Access Service:**
```bash
# Start with specific IP
cd /opt/myrvm/services
python3 remote_access.py --host=100.117.234.2 --port=5000

# Or with ZeroTier
python3 remote_access.py --host=172.28.93.97 --port=5000
```

### **GUI Client Service:**
```bash
# Start with specific IP
cd /opt/myrvm/services
python3 gui_client.py --host=100.117.234.2 --port=5001

# Or with ZeroTier
python3 gui_client.py --host=172.28.93.97 --port=5001
```

### **Camera Service:**
```bash
# Start with specific IP
cd /opt/myrvm/services
python3 camera_service.py --host=100.117.234.2 --port=5002

# Or with ZeroTier
python3 camera_service.py --host=172.28.93.97 --port=5002
```

## 📊 Network Monitoring

### **Connectivity Test:**
```bash
#!/bin/bash
# Network connectivity test script

# Test RVM-Jetson connectivity
echo "Testing RVM-Jetson connectivity..."
ping -c 3 100.117.234.2
ping -c 3 172.28.93.97

# Test MyRVM-Platform connectivity
echo "Testing MyRVM-Platform connectivity..."
ping -c 3 100.123.143.87
ping -c 3 172.28.233.83

# Test service ports
echo "Testing service ports..."
nc -zv 100.117.234.2 8080  # Installation Method
nc -zv 100.117.234.2 5000  # Remote Access
nc -zv 100.117.234.2 5001  # GUI Client
nc -zv 100.117.234.2 5002  # Camera Service
nc -zv 100.123.143.87 8001 # MyRVM-Platform API
```

### **Service Status Check:**
```bash
#!/bin/bash
# Service status check script

# Check RVM-Jetson services
echo "Checking RVM-Jetson services..."
curl -s http://100.117.234.2:8080/api/status || echo "Installation Method: DOWN"
curl -s http://100.117.234.2:5000/health || echo "Remote Access: DOWN"
curl -s http://100.117.234.2:5001/api/gui/status || echo "GUI Client: DOWN"
curl -s http://100.117.234.2:5002/api/camera/status || echo "Camera Service: DOWN"

# Check MyRVM-Platform services
echo "Checking MyRVM-Platform services..."
curl -s http://100.123.143.87:8001/api/health-check || echo "MyRVM-Platform: DOWN"
```

## 🚨 Network Troubleshooting

### **Common Issues:**

#### **1. Connection Timeout:**
```bash
# Check network connectivity
ping 100.117.234.2
ping 100.123.143.87

# Check port accessibility
telnet 100.117.234.2 8080
telnet 100.123.143.87 8001
```

#### **2. Service Not Responding:**
```bash
# Check if service is running
ps aux | grep python3

# Check port usage
netstat -tlnp | grep :8080
netstat -tlnp | grep :5000
netstat -tlnp | grep :8001
```

#### **3. VPN Connection Issues:**
```bash
# Check Tailscale status
tailscale status

# Check ZeroTier status
zerotier-cli status

# Restart VPN services
sudo systemctl restart tailscaled
sudo systemctl restart zerotier-one
```

## 📋 Configuration Files

### **Environment Variables:**
```bash
# File: /opt/myrvm/config/network.conf
export RVM_IP_PRIMARY="100.117.234.2"
export RVM_IP_BACKUP="172.28.93.97"
export SERVER_IP_PRIMARY="100.123.143.87"
export SERVER_IP_BACKUP="172.28.233.83"

export RVM_INSTALLATION_PORT=8080
export RVM_REMOTE_ACCESS_PORT=5000
export RVM_GUI_CLIENT_PORT=5001
export RVM_CAMERA_SERVICE_PORT=5002

export SERVER_WEB_PORT=8000
export SERVER_API_PORT=8001
```

### **Service Configuration:**
```json
{
  "network": {
    "primary": {
      "rvm_ip": "100.117.234.2",
      "server_ip": "100.123.143.87",
      "network": "tailscale"
    },
    "backup": {
      "rvm_ip": "172.28.93.97",
      "server_ip": "172.28.233.83",
      "network": "zerotier"
    }
  },
  "services": {
    "installation_method": {
      "port": 8080,
      "auto_start": true
    },
    "remote_access": {
      "port": 5000,
      "auto_start": false
    },
    "gui_client": {
      "port": 5001,
      "auto_start": false
    },
    "camera_service": {
      "port": 5002,
      "auto_start": false
    }
  }
}
```

## 🔍 Security Considerations

### **Network Security:**
- **VPN Only:** All services accessible only through VPN networks
- **No Public Access:** No services exposed to public internet
- **Firewall Rules:** Strict firewall rules for port access
- **Authentication:** API key authentication for remote services

### **Access Control:**
- **Tailscale:** Primary network with device authentication
- **ZeroTier:** Backup network with network authentication
- **Local Access:** Services bound to specific IP addresses
- **Remote Access:** Limited to authenticated devices only

## 📊 Performance Monitoring

### **Network Latency:**
```bash
# Monitor network latency
ping -c 10 100.117.234.2
ping -c 10 100.123.143.87

# Monitor service response time
time curl -s http://100.117.234.2:8080/api/status
time curl -s http://100.123.143.87:8001/api/health-check
```

### **Bandwidth Usage:**
```bash
# Monitor bandwidth usage
iftop -i tailscale0
iftop -i zt0

# Monitor service traffic
netstat -i
ss -tuln
```

## 🎯 Best Practices

### **Network Configuration:**
1. **Use Primary Network:** Always use Tailscale for primary operations
2. **Backup Network:** Use ZeroTier only for failover scenarios
3. **IP Binding:** Bind services to specific IP addresses
4. **Port Management:** Use standard port assignments
5. **Monitoring:** Regular network connectivity monitoring

### **Service Management:**
1. **Health Checks:** Regular service health monitoring
2. **Failover:** Automatic failover to backup network
3. **Logging:** Comprehensive network and service logging
4. **Alerting:** Network and service failure alerting
5. **Documentation:** Keep network documentation updated

---

**Last Updated:** 2025-09-23  
**Next Review:** 2025-09-30  
**Maintainer:** RVM-Jetson Team  
**Status:** Production Configuration
