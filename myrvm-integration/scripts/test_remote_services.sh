#!/bin/bash
# Test Remote Camera and GUI Services

set -e

echo "🧪 Testing RVM Remote Services..."
echo "================================="

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "Testing services on IP: $LOCAL_IP"
echo ""

# Test Camera Service (Port 5000)
echo "📹 Testing Camera Service (Port 5000)..."
if curl -s -o /dev/null -w "%{http_code}" "http://$LOCAL_IP:5000" | grep -q "200"; then
    echo "✅ Camera Service is responding"
    
    # Test camera info endpoint
    echo "   Testing camera info endpoint..."
    if curl -s "http://$LOCAL_IP:5000/camera_info" | grep -q "rvm_id"; then
        echo "   ✅ Camera info endpoint working"
    else
        echo "   ❌ Camera info endpoint not working"
    fi
    
    # Test camera status endpoint
    echo "   Testing camera status endpoint..."
    if curl -s "http://$LOCAL_IP:5000/status" | grep -q "service"; then
        echo "   ✅ Camera status endpoint working"
    else
        echo "   ❌ Camera status endpoint not working"
    fi
else
    echo "❌ Camera Service is not responding"
fi

echo ""

# Test GUI Service (Port 5001)
echo "🎛️ Testing GUI Service (Port 5001)..."
if curl -s -o /dev/null -w "%{http_code}" "http://$LOCAL_IP:5001" | grep -q "200"; then
    echo "✅ GUI Service is responding"
    
    # Test system status endpoint
    echo "   Testing system status endpoint..."
    if curl -s "http://$LOCAL_IP:5001/system/status" | grep -q "cpu_usage"; then
        echo "   ✅ System status endpoint working"
    else
        echo "   ❌ System status endpoint not working"
    fi
    
    # Test API status endpoint
    echo "   Testing API status endpoint..."
    if curl -s "http://$LOCAL_IP:5001/api/status" | grep -q "connected"; then
        echo "   ✅ API status endpoint working"
    else
        echo "   ❌ API status endpoint not working"
    fi
else
    echo "❌ GUI Service is not responding"
fi

echo ""

# Test port connectivity
echo "🔌 Testing Port Connectivity..."
echo "==============================="

# Test port 5000
if nc -z $LOCAL_IP 5000; then
    echo "✅ Port 5000 (Camera) is open"
else
    echo "❌ Port 5000 (Camera) is closed"
fi

# Test port 5001
if nc -z $LOCAL_IP 5001; then
    echo "✅ Port 5001 (GUI) is open"
else
    echo "❌ Port 5001 (GUI) is closed"
fi

echo ""

# Test service status
echo "⚙️ Testing Service Status..."
echo "============================"

# Check camera service
if systemctl is-active --quiet rvm-remote-camera; then
    echo "✅ Camera service is active"
else
    echo "❌ Camera service is not active"
fi

# Check GUI service
if systemctl is-active --quiet rvm-remote-gui; then
    echo "✅ GUI service is active"
else
    echo "❌ GUI service is not active"
fi

echo ""

# Test from external perspective (simulate MyRVM Platform ping)
echo "🌐 Testing External Connectivity..."
echo "==================================="

echo "Testing from external perspective (simulating MyRVM Platform ping)..."

# Test camera service from external
if timeout 5 bash -c "</dev/tcp/$LOCAL_IP/5000"; then
    echo "✅ Camera Service (Port 5000) is accessible externally"
else
    echo "❌ Camera Service (Port 5000) is not accessible externally"
fi

# Test GUI service from external
if timeout 5 bash -c "</dev/tcp/$LOCAL_IP/5001"; then
    echo "✅ GUI Service (Port 5001) is accessible externally"
else
    echo "❌ GUI Service (Port 5001) is not accessible externally"
fi

echo ""
echo "🎯 Test Summary:"
echo "================"
echo "Camera Service: http://$LOCAL_IP:5000"
echo "GUI Service: http://$LOCAL_IP:5001"
echo ""
echo "📋 If tests fail, check:"
echo "1. Services are running: sudo systemctl status rvm-remote-camera rvm-remote-gui"
echo "2. Ports are open: netstat -tlnp | grep -E '(5000|5001)'"
echo "3. Firewall settings: sudo ufw status"
echo "4. Service logs: sudo journalctl -u rvm-remote-camera -f"
echo "5. Service logs: sudo journalctl -u rvm-remote-gui -f"
