#!/bin/bash
# Run All MyRVM Integration Services

set -e

echo "🚀 Starting All MyRVM Integration Services..."
echo "============================================="

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project directory: $PROJECT_DIR"
echo ""

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/services/remote_camera_service.py" ]; then
    echo "❌ Please run this script from the myrvm-integration directory"
    exit 1
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if netstat -tlnp | grep -q ":$port "; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start service in background
start_service() {
    local service_name=$1
    local service_script=$2
    local port=$3
    
    echo "Starting $service_name..."
    
    if check_port $port; then
        echo "   ⚠️  Port $port is already in use. Skipping $service_name"
        return 1
    fi
    
    cd "$PROJECT_DIR"
    nohup python3 "$service_script" > "logs/${service_name}.log" 2>&1 &
    local pid=$!
    echo "   ✅ $service_name started with PID: $pid"
    echo $pid > "logs/${service_name}.pid"
    
    # Wait a moment for service to start
    sleep 2
    
    # Check if service is still running
    if kill -0 $pid 2>/dev/null; then
        echo "   ✅ $service_name is running"
        return 0
    else
        echo "   ❌ $service_name failed to start"
        return 1
    fi
}

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Start services
echo "📹 Starting Remote Camera Service..."
start_service "remote_camera" "services/remote_camera_service.py" 5000

echo ""
echo "🎛️ Starting Remote GUI Service..."
start_service "remote_gui" "services/remote_gui_service.py" 5001

echo ""
echo "📊 Starting Monitoring Dashboard..."
start_service "monitoring_dashboard" "monitoring/dashboard_server.py" 5002

echo ""
echo "🔧 Starting Enhanced Jetson Main..."
start_service "enhanced_jetson_main" "main/enhanced_jetson_main.py" 8000

# Wait for all services to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check service status
echo ""
echo "📊 Service Status:"
echo "=================="

# Check each service
services=("remote_camera:5000" "remote_gui:5001" "monitoring_dashboard:5002" "enhanced_jetson_main:8000")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    
    if check_port $port; then
        echo "✅ $name (Port $port) is running"
    else
        echo "❌ $name (Port $port) is not running"
    fi
done

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "🎉 All services started!"
echo ""
echo "📱 Access URLs:"
echo "Camera Service: http://$LOCAL_IP:5000"
echo "GUI Service: http://$LOCAL_IP:5001"
echo "Monitoring Dashboard: http://$LOCAL_IP:5002"
echo "Enhanced Jetson Main: http://$LOCAL_IP:8000"
echo ""
echo "📋 Service Management:"
echo "View logs: tail -f logs/remote_camera.log"
echo "View logs: tail -f logs/remote_gui.log"
echo "View logs: tail -f logs/monitoring_dashboard.log"
echo "View logs: tail -f logs/enhanced_jetson_main.log"
echo ""
echo "Stop services: pkill -f remote_camera_service.py"
echo "Stop services: pkill -f remote_gui_service.py"
echo "Stop services: pkill -f dashboard_server.py"
echo "Stop services: pkill -f enhanced_jetson_main.py"
echo ""
echo "🔍 Test connectivity:"
echo "curl http://$LOCAL_IP:5000/status"
echo "curl http://$LOCAL_IP:5001/system/status"
echo "curl http://$LOCAL_IP:5002/dashboard"
