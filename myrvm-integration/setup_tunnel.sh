#!/bin/bash
# Tunnel Setup Script for MyRVM Platform
# This script helps setup tunneling for external access to MyRVM Platform

echo "🌐 MyRVM Platform Tunnel Setup"
echo "=============================="

# Check if we're in the right directory
if [[ ! -f "main/config.json" ]]; then
    echo "❌ Please run this script from the myrvm-integration directory"
    exit 1
fi

echo "✅ Running from correct directory"

# Check if MyRVM Platform is running
echo ""
echo "🔍 Checking MyRVM Platform status..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ MyRVM Platform is running on port 8000"
    PLATFORM_PORT=8000
elif curl -s http://localhost:8001/api/health > /dev/null; then
    echo "✅ MyRVM Platform is running on port 8001"
    PLATFORM_PORT=8001
else
    echo "❌ MyRVM Platform is not running on ports 8000 or 8001"
    echo "Please start MyRVM Platform first:"
    echo "  cd /home/my/MySuperApps/MyRVM-Platform"
    echo "  docker-compose up -d"
    exit 1
fi

echo ""
echo "🚀 Tunnel Setup Options:"
echo "========================"
echo "1. Cloudflare Tunnel (Recommended)"
echo "2. ngrok Tunnel"
echo "3. Local Network Access Only"
echo "4. Manual Configuration"

read -p "Choose option (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🌩️  Setting up Cloudflare Tunnel..."
        echo "=================================="
        
        # Check if cloudflared is installed
        if ! command -v cloudflared &> /dev/null; then
            echo "📥 Installing cloudflared..."
            wget -O cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
            sudo dpkg -i cloudflared.deb
            rm cloudflared.deb
        fi
        
        echo "🔑 Please login to Cloudflare:"
        cloudflared tunnel login
        
        echo "🏗️  Creating tunnel..."
        TUNNEL_NAME="myrvm-platform-$(date +%s)"
        cloudflared tunnel create $TUNNEL_NAME
        
        echo "📝 Creating tunnel configuration..."
        TUNNEL_CONFIG_DIR="$HOME/.cloudflared"
        mkdir -p $TUNNEL_CONFIG_DIR
        
        cat > $TUNNEL_CONFIG_DIR/config.yml << EOF
tunnel: $TUNNEL_NAME
credentials-file: $TUNNEL_CONFIG_DIR/$TUNNEL_NAME.json

ingress:
  - hostname: myrvm-platform.your-domain.com
    service: http://localhost:$PLATFORM_PORT
  - service: http_status:404
EOF
        
        echo "🌐 Setting up DNS record..."
        echo "Please add a CNAME record in your Cloudflare DNS:"
        echo "  Name: myrvm-platform"
        echo "  Target: $TUNNEL_NAME.cfargotunnel.com"
        echo "  TTL: Auto"
        
        read -p "Press Enter after adding the DNS record..."
        
        echo "🚀 Starting tunnel..."
        cloudflared tunnel --config $TUNNEL_CONFIG_DIR/config.yml run $TUNNEL_NAME &
        TUNNEL_PID=$!
        
        echo "⏳ Waiting for tunnel to be ready..."
        sleep 10
        
        TUNNEL_URL="https://myrvm-platform.your-domain.com"
        echo "✅ Tunnel URL: $TUNNEL_URL"
        
        # Update config
        jq --arg url "$TUNNEL_URL" '.myrvm_tunnel_url = $url | .use_tunnel = true' main/config.json > main/config.json.tmp
        mv main/config.json.tmp main/config.json
        
        echo "📝 Configuration updated with tunnel URL"
        echo "🔄 Tunnel PID: $TUNNEL_PID (save this for stopping the tunnel)"
        ;;
        
    2)
        echo ""
        echo "🔗 Setting up ngrok Tunnel..."
        echo "============================="
        
        # Check if ngrok is installed
        if ! command -v ngrok &> /dev/null; then
            echo "📥 Installing ngrok..."
            curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
            echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
            sudo apt update && sudo apt install ngrok
        fi
        
        echo "🔑 Please login to ngrok:"
        ngrok config add-authtoken YOUR_AUTHTOKEN
        
        echo "🚀 Starting ngrok tunnel..."
        ngrok http $PLATFORM_PORT &
        NGROK_PID=$!
        
        echo "⏳ Waiting for tunnel to be ready..."
        sleep 5
        
        # Get tunnel URL
        TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
        echo "✅ Tunnel URL: $TUNNEL_URL"
        
        # Update config
        jq --arg url "$TUNNEL_URL" '.myrvm_tunnel_url = $url | .use_tunnel = true' main/config.json > main/config.json.tmp
        mv main/config.json.tmp main/config.json
        
        echo "📝 Configuration updated with tunnel URL"
        echo "🔄 ngrok PID: $NGROK_PID (save this for stopping the tunnel)"
        ;;
        
    3)
        echo ""
        echo "🏠 Local Network Access Only"
        echo "============================"
        
        # Get local IP
        LOCAL_IP=$(hostname -I | awk '{print $1}')
        LOCAL_URL="http://$LOCAL_IP:$PLATFORM_PORT"
        
        echo "🌐 Local URL: $LOCAL_URL"
        echo "📝 Make sure Jetson Orin can access this IP"
        
        # Update config
        jq --arg url "$LOCAL_URL" '.myrvm_base_url = $url | .use_tunnel = false' main/config.json > main/config.json.tmp
        mv main/config.json.tmp main/config.json
        
        echo "📝 Configuration updated with local URL"
        ;;
        
    4)
        echo ""
        echo "⚙️  Manual Configuration"
        echo "======================="
        
        read -p "Enter MyRVM Platform URL: " MANUAL_URL
        read -p "Use tunnel? (y/n): " USE_TUNNEL
        
        if [[ $USE_TUNNEL == "y" ]]; then
            jq --arg url "$MANUAL_URL" '.myrvm_tunnel_url = $url | .use_tunnel = true' main/config.json > main/config.json.tmp
        else
            jq --arg url "$MANUAL_URL" '.myrvm_base_url = $url | .use_tunnel = false' main/config.json > main/config.json.tmp
        fi
        
        mv main/config.json.tmp main/config.json
        echo "📝 Configuration updated"
        ;;
        
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "🧪 Testing connection..."
python3 -c "
import sys
sys.path.append('.')
from api_client.myrvm_api_client import MyRVMAPIClient
import json

with open('main/config.json', 'r') as f:
    config = json.load(f)

client = MyRVMAPIClient(
    base_url=config.get('myrvm_base_url', 'http://localhost:8000'),
    tunnel_url=config.get('myrvm_tunnel_url'),
    use_tunnel=config.get('use_tunnel', False)
)

success, response = client.ping_platform()
if success:
    print('✅ Connection successful!')
    print(f'Response: {response}')
else:
    print('❌ Connection failed!')
    print(f'Error: {response}')
"

echo ""
echo "🎉 Tunnel setup completed!"
echo "========================="
echo "Next steps:"
echo "1. Test the connection: python3 debug/test_integration.py"
echo "2. Start the main application: python3 main/jetson_main.py"
echo "3. Monitor with: python3 debug/system_monitor.py"
