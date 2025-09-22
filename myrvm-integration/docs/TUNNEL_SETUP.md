# 🌐 Tunnel Setup Guide for MyRVM Platform

This guide explains how to setup tunneling for external access to MyRVM Platform from Jetson Orin.

## 📋 **Overview**

### **Problem:**
- **MyRVM Platform** runs on Docker-host (`/home/my/MySuperApps/MyRVM-Platform`)
- **Jetson Orin** needs to access it from external network
- **Port**: `8000` (Laravel) or `8001` (alternative)

### **Solution:**
Setup tunneling to expose MyRVM Platform to external network.

## 🚀 **Quick Setup**

### **Option 1: Automated Setup (Recommended)**
```bash
cd myrvm-integration
./setup_tunnel.sh
```

### **Option 2: Manual Setup**
Follow the detailed steps below.

## 🔧 **Tunneling Options**

### **1. Tailscale (Primary - Recommended)**

#### **Advantages:**
- ✅ Easy setup and management
- ✅ Built-in security and encryption
- ✅ Works behind NAT/firewall
- ✅ Mesh networking
- ✅ Cross-platform support

#### **Setup Steps:**
```bash
# 1. Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Start Tailscale
sudo tailscale up

# 3. Get Tailscale IP
tailscale ip -4

# 4. Configure hostname (optional)
sudo tailscale set --hostname=myrvm-jetson
```

### **2. ZeroTier (Emergency Backup)**

#### **Advantages:**
- ✅ Free tier available
- ✅ Works behind NAT/firewall
- ✅ Cross-platform support
- ✅ Good for emergency situations

#### **Setup Steps:**
```bash
# 1. Install ZeroTier
curl -s https://install.zerotier.com | sudo bash

# 2. Join network
sudo zerotier-cli join <NETWORK_ID>

# 3. Check status
sudo zerotier-cli listnetworks
```

### **3. Cloudflare Tunnel (Alternative)**

#### **Advantages:**
- ✅ Free and reliable
- ✅ HTTPS by default
- ✅ No port forwarding needed
- ✅ Works behind NAT/firewall

#### **Setup Steps:**
```bash
# 1. Install cloudflared
wget -O cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# 2. Login to Cloudflare
cloudflared tunnel login

# 3. Create tunnel
cloudflared tunnel create myrvm-platform

# 4. Configure tunnel
cat > ~/.cloudflared/config.yml << EOF
tunnel: myrvm-platform
credentials-file: ~/.cloudflared/myrvm-platform.json

ingress:
  - hostname: myrvm-platform.your-domain.com
    service: http://localhost:8000
  - service: http_status:404
EOF

# 5. Add DNS record in Cloudflare dashboard
# CNAME: myrvm-platform -> your-tunnel-id.cfargotunnel.com

# 6. Start tunnel
cloudflared tunnel --config ~/.cloudflared/config.yml run myrvm-platform
```

### **2. ngrok Tunnel**

#### **Advantages:**
- ✅ Quick setup
- ✅ Public URL immediately
- ✅ Good for testing

#### **Setup Steps:**
```bash
# 1. Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# 2. Login to ngrok
ngrok config add-authtoken YOUR_AUTHTOKEN

# 3. Start tunnel
ngrok http 8000
```

### **3. Local Network Access**

#### **For Same Network:**
```bash
# Get local IP
hostname -I

# Update config.json
{
  "myrvm_base_url": "http://192.168.1.100:8000",
  "use_tunnel": false
}
```

## ⚙️ **Configuration**

### **config.json Settings:**
```json
{
  "server_url": "http://100.123.143.87:8001",
  "use_tunnel": true,
  "tunnel_type": "tailscale",
  "fallback_to_local": true,
  "tailscale_network": {
    "rvm_ip": "172.28.93.97",
    "server_ip": "100.123.143.87",
    "server_port": 8001,
    "tailscale_hostname": "myrvm-jetson"
  },
  "emergency_tunnel": {
    "type": "zerotier",
    "enabled": true,
    "zerotier_network": {
      "rvm_ip": "172.28.93.97",
      "server_ip": "100.123.143.87",
      "server_port": 8001
    }
  }
}
```

### **Dynamic URL Switching:**
The API client can automatically switch between local and tunnel URLs:

```python
# Switch to tunnel
client.switch_to_tunnel()

# Switch to local
client.switch_to_local()

# Test connectivity
success, message = client.test_connectivity()
```

## 🧪 **Testing**

### **1. Test Tunnel Connection:**
```bash
cd myrvm-integration
python3 -c "
from api_client.myrvm_api_client import MyRVMAPIClient
client = MyRVMAPIClient(use_tunnel=True)
success, response = client.ping_platform()
print('✅ Connected' if success else '❌ Failed')
"
```

### **2. Run Integration Tests:**
```bash
python3 debug/test_integration.py
```

### **3. Test from Jetson Orin:**
```bash
# On Jetson Orin
curl https://your-tunnel-url.com/api/health
```

## 🔄 **Port Configuration**

### **MyRVM Platform Ports:**
- **Port 8000**: Laravel application (default)
- **Port 8001**: Alternative service (if configured)

### **Check Running Port:**
```bash
# Check which port is running
curl http://localhost:8000/api/health
curl http://localhost:8001/api/health

# Check Docker containers
docker-compose ps
```

### **Update Port in Config:**
```json
{
  "myrvm_base_url": "http://localhost:8001",
  "myrvm_tunnel_url": "https://myrvm-platform.your-domain.com"
}
```

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **1. Tunnel Not Accessible:**
```bash
# Check tunnel status
cloudflared tunnel list
ngrok http 8000 --log=stdout

# Test local access
curl http://localhost:8000/api/health
```

#### **2. DNS Not Resolving:**
```bash
# Check DNS
nslookup myrvm-platform.your-domain.com

# Test with IP
curl https://tunnel-ip/api/health
```

#### **3. Firewall Issues:**
```bash
# Check firewall
sudo ufw status

# Allow port 8000
sudo ufw allow 8000
```

#### **4. MyRVM Platform Not Running:**
```bash
# Start MyRVM Platform
cd /home/my/MySuperApps/MyRVM-Platform
docker-compose up -d

# Check status
docker-compose ps
```

### **Debug Commands:**
```bash
# Check tunnel logs
cloudflared tunnel --config ~/.cloudflared/config.yml run myrvm-platform --loglevel debug

# Check ngrok logs
ngrok http 8000 --log=stdout

# Test connectivity
python3 debug/test_integration.py
```

## 📊 **Performance Considerations**

### **Tunnel Performance:**
- **Cloudflare**: ~50-100ms latency
- **ngrok**: ~100-200ms latency
- **Local Network**: ~1-10ms latency

### **Optimization:**
1. **Use Cloudflare** for production
2. **Use local network** for development
3. **Enable compression** in tunnel config
4. **Use HTTP/2** when possible

## 🔒 **Security**

### **Best Practices:**
1. **Use HTTPS** tunnels (Cloudflare default)
2. **Enable authentication** in MyRVM Platform
3. **Use API tokens** for authentication
4. **Limit tunnel access** to specific IPs
5. **Monitor tunnel usage**

### **API Authentication:**
```json
{
  "api_token": "your-api-token-here",
  "use_tunnel": true
}
```

## 📝 **Example Configurations**

### **Development (Local):**
```json
{
  "myrvm_base_url": "http://192.168.1.100:8000",
  "use_tunnel": false,
  "debug_mode": true
}
```

### **Production (Cloudflare):**
```json
{
  "myrvm_base_url": "http://localhost:8000",
  "myrvm_tunnel_url": "https://myrvm-platform.your-domain.com",
  "use_tunnel": true,
  "tunnel_type": "cloudflare",
  "api_token": "your-production-token"
}
```

### **Testing (ngrok):**
```json
{
  "myrvm_base_url": "http://localhost:8000",
  "myrvm_tunnel_url": "https://abc123.ngrok.io",
  "use_tunnel": true,
  "tunnel_type": "ngrok"
}
```

## 🎯 **Next Steps**

1. **Setup tunnel** using automated script
2. **Test connection** from Jetson Orin
3. **Update config.json** with tunnel URL
4. **Run integration tests**
5. **Start main application**

## 📞 **Support**

For issues:
1. Check tunnel logs
2. Test local connectivity
3. Verify DNS resolution
4. Check firewall settings
5. Review MyRVM Platform status
