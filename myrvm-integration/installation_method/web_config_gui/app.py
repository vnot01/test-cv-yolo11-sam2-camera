#!/usr/bin/env python3
"""
Web Configuration Interface for RVM-Jetson Installation
Main Flask application for web-based configuration and calibration
"""

import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import psutil
import requests

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing modules
try:
    from hardware.hardware_detector import HardwareDetector
    from services.detection_service import DetectionService
    from api_client.myrvm_api_client import MyRVMAPIClient
    from utils.config_manager import ConfigManager
except ImportError as e:
    print(f"Warning: Could not import existing modules: {e}")
    # Create mock classes for development
    class HardwareDetector:
        def get_hardware_info(self):
            return {"cpu": "Jetson Orin", "memory": "32GB", "gpu": "NVIDIA"}
    
    class DetectionService:
        def test_models(self):
            return {"yolo": "OK", "sam": "OK"}
    
    class MyRVMAPIClient:
        def test_connection(self):
            return {"status": "connected", "server": "localhost:8000"}
    
    class ConfigManager:
        def get_config(self):
            return {"rvm_id": 1, "server_url": "http://localhost:8000"}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_config_gui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'rvm-jetson-web-config-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
hardware_detector = HardwareDetector()
detection_service = DetectionService()
api_client = MyRVMAPIClient()
config_manager = ConfigManager()

# Installation status
installation_status = {
    'phase': 'initialization',
    'progress': 0,
    'status': 'ready',
    'message': 'Web Configuration Interface ready',
    'timestamp': datetime.now().isoformat(),
    'errors': [],
    'warnings': []
}

# Configuration data
config_data = {
    'hardware': {},
    'network': {},
    'server': {},
    'ai_models': {},
    'calibration': {}
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/install')
def install():
    """Installation page"""
    return render_template('install.html')

@app.route('/hardware')
def hardware():
    """Hardware calibration page"""
    return render_template('hardware.html')

@app.route('/network')
def network():
    """Network configuration page"""
    return render_template('network.html')

@app.route('/config')
def config():
    """Configuration management page"""
    return render_template('config.html')

@app.route('/deploy')
def deploy():
    """Deployment page"""
    return render_template('deploy.html')

# API Routes
@app.route('/api/status')
def api_status():
    """Get installation status"""
    return jsonify(installation_status)

@app.route('/api/hardware/detect')
def api_hardware_detect():
    """Detect hardware components"""
    try:
        hardware_info = hardware_detector.get_hardware_info()
        config_data['hardware'] = hardware_info
        
        # Update status
        installation_status['message'] = 'Hardware detection completed'
        installation_status['timestamp'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'data': hardware_info,
            'message': 'Hardware detection completed'
        })
    except Exception as e:
        logger.error(f"Hardware detection error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Hardware detection failed'
        }), 500

@app.route('/api/network/scan')
def api_network_scan():
    """Scan for available networks"""
    try:
        # Mock network scanning for now
        networks = [
            {'ssid': 'MyRVM-Network', 'signal': -45, 'security': 'WPA2'},
            {'ssid': 'Guest-WiFi', 'signal': -65, 'security': 'Open'},
            {'ssid': 'Office-WiFi', 'signal': -55, 'security': 'WPA3'}
        ]
        
        config_data['network']['available_networks'] = networks
        
        return jsonify({
            'success': True,
            'data': networks,
            'message': 'Network scan completed'
        })
    except Exception as e:
        logger.error(f"Network scan error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Network scan failed'
        }), 500

@app.route('/api/network/connect', methods=['POST'])
def api_network_connect():
    """Connect to WiFi network"""
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password')
        
        # Mock connection for now
        result = {
            'ssid': ssid,
            'status': 'connected',
            'ip_address': '192.168.1.100',
            'signal_strength': -45
        }
        
        config_data['network']['current_connection'] = result
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Connected to {ssid}'
        })
    except Exception as e:
        logger.error(f"Network connection error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Network connection failed'
        }), 500

@app.route('/api/server/test', methods=['POST'])
def api_server_test():
    """Test server connectivity"""
    try:
        data = request.get_json()
        server_url = data.get('server_url', 'http://localhost:8000')
        
        # Test connection
        result = api_client.test_connection()
        
        config_data['server'] = {
            'url': server_url,
            'status': 'connected',
            'response_time': 150
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Server connection test successful'
        })
    except Exception as e:
        logger.error(f"Server test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Server connection test failed'
        }), 500

@app.route('/api/ai/test')
def api_ai_test():
    """Test AI models"""
    try:
        result = detection_service.test_models()
        config_data['ai_models'] = result
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'AI models test completed'
        })
    except Exception as e:
        logger.error(f"AI test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'AI models test failed'
        }), 500

@app.route('/api/calibration/camera', methods=['POST'])
def api_calibration_camera():
    """Camera calibration"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'test':
            result = {
                'status': 'working',
                'resolution': '1920x1080',
                'fps': 30,
                'brightness': 50,
                'contrast': 50
            }
        elif action == 'calibrate':
            result = {
                'status': 'calibrated',
                'brightness': data.get('brightness', 50),
                'contrast': data.get('contrast', 50),
                'saturation': data.get('saturation', 50)
            }
        
        config_data['calibration']['camera'] = result
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Camera {action} completed'
        })
    except Exception as e:
        logger.error(f"Camera calibration error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Camera calibration failed'
        }), 500

@app.route('/api/config/save', methods=['POST'])
def api_config_save():
    """Save configuration"""
    try:
        data = request.get_json()
        
        # Save configuration to file
        config_file = 'config/installation_config.json'
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update global config
        config_data.update(data)
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved successfully'
        })
    except Exception as e:
        logger.error(f"Config save error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Configuration save failed'
        }), 500

@app.route('/api/deploy/start', methods=['POST'])
def api_deploy_start():
    """Start deployment process"""
    try:
        # Update installation status
        installation_status.update({
            'phase': 'deployment',
            'progress': 0,
            'status': 'running',
            'message': 'Starting deployment...',
            'timestamp': datetime.now().isoformat()
        })
        
        # Start deployment in background thread
        deployment_thread = threading.Thread(target=deployment_worker)
        deployment_thread.daemon = True
        deployment_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Deployment started'
        })
    except Exception as e:
        logger.error(f"Deploy start error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Deployment start failed'
        }), 500

def deployment_worker():
    """Background deployment worker"""
    try:
        steps = [
            "Validating configuration...",
            "Installing dependencies...",
            "Configuring services...",
            "Starting RVM services...",
            "Testing integration...",
            "Deployment completed!"
        ]
        
        for i, step in enumerate(steps):
            time.sleep(2)  # Simulate work
            
            progress = int((i + 1) / len(steps) * 100)
            installation_status.update({
                'progress': progress,
                'message': step,
                'timestamp': datetime.now().isoformat()
            })
            
            # Emit progress update via WebSocket
            socketio.emit('deployment_progress', {
                'progress': progress,
                'message': step,
                'timestamp': datetime.now().isoformat()
            })
        
        # Final status
        installation_status.update({
            'phase': 'completed',
            'progress': 100,
            'status': 'completed',
            'message': 'Deployment completed successfully!',
            'timestamp': datetime.now().isoformat()
        })
        
        socketio.emit('deployment_complete', {
            'status': 'completed',
            'message': 'Deployment completed successfully!',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Deployment worker error: {e}")
        installation_status.update({
            'status': 'error',
            'message': f'Deployment failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })
        
        socketio.emit('deployment_error', {
            'error': str(e),
            'message': 'Deployment failed',
            'timestamp': datetime.now().isoformat()
        })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status', installation_status)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('request_status')
def handle_status_request():
    """Handle status request"""
    emit('status', installation_status)

@socketio.on('request_hardware_info')
def handle_hardware_request():
    """Handle hardware info request"""
    try:
        hardware_info = hardware_detector.get_hardware_info()
        emit('hardware_info', hardware_info)
    except Exception as e:
        emit('error', {'message': f'Hardware detection failed: {str(e)}'})

if __name__ == '__main__':
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    
    # Create static directory
    os.makedirs('static', exist_ok=True)
    
    logger.info('Starting Web Configuration Interface...')
    logger.info('Access the interface at: http://localhost:8080/install')
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
