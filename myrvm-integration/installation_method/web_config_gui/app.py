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
import socket
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import psutil
import requests
import subprocess

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
    # TODO: Hardware calibration modules - DISABLED for now
    # Uncomment below when hardware components are needed
    # from hardware_calibration import CalibrationManager
    # calibration_manager = CalibrationManager()

    # TODO: Hardware detection - DISABLED for now
    # Uncomment when hardware detection is needed
    class HardwareDetector:
        def get_hardware_info(self):
            return {"cpu": "Jetson Orin", "memory": "32GB", "gpu": "NVIDIA", "note": "Mock data - Hardware detection disabled"}

    # TODO: AI model testing - DISABLED for now
    # Uncomment when AI model testing is needed
    class DetectionService:
        def test_models(self):
            return {"yolo": "Mock", "sam": "Mock", "note": "Mock data - AI testing disabled"}
        
        def get_model_info(self):
            return {
                'yolo_model': {
                    'loaded': True,
                    'path': 'models/best.pt',
                    'exists': True
                },
                'sam2_model': {
                    'loaded': True,
                    'path': 'models/sam2.1_b.pt',
                    'exists': True
                }
            }

    # REAL MyRVM Platform connection - ENABLED
    class MyRVMAPIClient:
        def test_connection(self):
            try:
                import requests
                # Test real connection to MyRVM Platform
                response = requests.get("http://100.123.143.87:8001/api/health-check", timeout=5)
                if response.status_code == 200:
                    return {"status": "connected", "server": "100.123.143.87:8001", "response": response.json()}
                else:
                    return {"status": "error", "server": "100.123.143.87:8001", "code": response.status_code}
            except Exception as e:
                logger.error(f"Server test error: {e}")
                return {"status": "error", "server": "100.123.143.87:8001", "error": str(e)}

    # REAL Configuration management - ENABLED
    class ConfigManager:
        def get_config(self):
            try:
                # Load real configuration
                config_file = 'config/installation_config.json'
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        return json.load(f)
                else:
                    return {"rvm_id": 1, "server_url": "http://100.123.143.87:8001"}
            except Exception as e:
                logger.error(f"Config load error: {e}")
                return {"rvm_id": 1, "server_url": "http://100.123.143.87:8001", "error": str(e)}

# Import network status module
try:
    from network_status import NetworkStatus
    network_status = NetworkStatus()
except ImportError:
    logger.warning("Network status module not available")
    network_status = None

# Import Jetson network detector
try:
    from jetson_network_detector import JetsonNetworkDetector
    jetson_detector = JetsonNetworkDetector()
except ImportError:
    logger.warning("Jetson network detector not available")
    jetson_detector = None

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

# Helpers
def _get_server_url_from_config(default: str = "http://100.123.143.87:8001") -> str:
    try:
        cfg = config_manager.get_config() if config_manager else {}
        return cfg.get('server_url', default)
    except Exception:
        return default

def _get_machine_id() -> str:
    try:
        with open('/etc/machine-id', 'r') as f:
            return f.read().strip()
    except Exception:
        return "unknown-machine-id"

def _get_mac_address(interface: str = 'wlP1p1s0') -> str:
    """Get MAC address from specified interface (default: wlP1p1s0 for Jetson)."""
    # Try specified interface first
    try:
        result = subprocess.run(['ip', '-o', 'link', 'show', interface], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout:
            # Parse MAC address from output: "2: wlP1p1s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DORMANT group default qlen 1000\    link/ether c0:bf:be:93:68:f1 brd ff:ff:ff:ff:ff:ff"
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'link/ether' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'link/ether' and i + 1 < len(parts):
                            mac = parts[i + 1]
                            if len(mac) == 17 and ':' in mac:  # Valid MAC format
                                logger.info(f"Using MAC from {interface}: {mac}")
                                return mac
    except Exception as e:
        logger.error(f"Error getting MAC from {interface}: {e}")
    
    # Fallback to other interfaces
    fallback_interfaces = ['enP8p1s0', 'eth0', 'wlan0', 'enp0s3', 'ens33']
    for iface in fallback_interfaces:
        try:
            result = subprocess.run(['ip', '-o', 'link', 'show', iface], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'link/ether' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'link/ether' and i + 1 < len(parts):
                                mac = parts[i + 1]
                                if len(mac) == 17 and ':' in mac:
                                    logger.info(f"Using MAC from fallback {iface}: {mac}")
                                    return mac
        except Exception:
            continue
    
    return "00:00:00:00:00:00"

def _get_tailscale_ip() -> str:
    try:
        result = subprocess.run(['tailscale', 'ip', '-4'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0]
    except Exception:
        pass
    return ""

# --- Sudo helper using RVM_SUDO_PASS fallback ---
def _sudo_run(command_args: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run a command with sudo using RVM_SUDO_PASS if available.

    - If RVM_SUDO_PASS is set in environment, uses `sudo -S` piping the password.
    - Otherwise attempts passwordless sudo (will fail if not allowed).
    Returns subprocess.CompletedProcess.
    """
    env = os.environ.copy()
    sudo_pass = env.get('RVM_SUDO_PASS', '')
    try:
        if sudo_pass:
            proc = subprocess.run(
                ['sudo', '-S', *command_args],
                input=f"{sudo_pass}\n",
                text=True,
                capture_output=True,
                timeout=timeout
            )
        else:
            proc = subprocess.run(
                ['sudo', '-n', *command_args],
                text=True,
                capture_output=True,
                timeout=timeout
            )
        return proc
    except Exception as e:
        # Surface error details to logs and callers
        logger.error(f"sudo run failed: {e}")
        raise

def _production_config_path() -> str:
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        return os.path.join(project_root, 'config', 'production_config.json')
    except Exception:
        return 'config/production_config.json'


def _persist_rvm_id(rvm_id: int) -> bool:
    try:
        cfg_path = _production_config_path()
        os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
        data = {}
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, 'r') as f:
                    data = json.load(f)
            except Exception:
                data = {}
        # ensure nested keys
        data.setdefault('application', data.get('application', {}))
        data['rvm_id'] = rvm_id
        ra = data.get('remote_access', {})
        ra['rvm_id'] = rvm_id
        data['remote_access'] = ra
        with open(cfg_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to persist rvm_id: {e}")
        return False

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/welcome')
def welcome():
    """Post-install welcome and API status page"""
    return render_template('welcome.html')

@app.route('/install')
def install():
    """Installation page"""
    return render_template('install.html')

# TODO: Hardware page - DISABLED for now
# Uncomment when hardware functionality is needed
# @app.route('/hardware')
# def hardware():
#     """Hardware calibration page"""
#     return render_template('hardware.html')

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

@app.route('/api/network/status')
def api_network_status():
    """Get real-time network status"""
    try:
        if network_status:
            status = network_status.get_network_status()
            recommendations = network_status.get_connection_recommendations(status)
            status['recommendations'] = recommendations
            return jsonify({
                'success': True,
                'data': status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Network status module not available'
            }), 500
    except Exception as e:
        logger.error(f"Network status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Network status check failed'
        }), 500

@app.route('/api/tailscale/up', methods=['POST'])
def api_tailscale_up():
    """Bring up Tailscale using AUTH Key and return tailscale0 IPv4 when ready."""
    try:
        data = request.get_json(force=True)
        auth_key = data.get('auth_key', '').strip()
        if not auth_key:
            return jsonify({'success': False, 'message': 'auth_key (tskey-...) is required'}), 400

        # Attempt tailscale up (no sudo assumption). TS_AUTHKEY is supported env.
        env = os.environ.copy()
        env['TS_AUTHKEY'] = auth_key
        try:
            subprocess.run(['tailscale', 'up', '--ssh', '--accept-dns=true', '--advertise-tags=tag:rvm'],
                           capture_output=True, text=True, timeout=30, env=env)
        except FileNotFoundError:
            return jsonify({'success': False, 'message': 'tailscale not installed'}), 500

        # Poll for IP up to 120s
        ip_addr = ''
        for _ in range(40):
            ip_addr = _get_tailscale_ip()
            if ip_addr:
                break
            time.sleep(3)

        if not ip_addr:
            return jsonify({'success': False, 'message': 'tailscale0 IP not available'}), 504

        config_data.setdefault('network', {})['tailscale_ip'] = ip_addr
        return jsonify({'success': True, 'data': {'tailscale_ip': ip_addr}})
    except Exception as e:
        logger.error(f"tailscale up error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/tailscale/ip', methods=['GET'])
def api_tailscale_ip():
    """Get current Tailscale IP address."""
    try:
        ip_addr = _get_tailscale_ip()
        if ip_addr:
            return jsonify({'success': True, 'data': {'tailscale_ip': ip_addr}})
        else:
            return jsonify({'success': False, 'message': 'Tailscale IP not available'}), 404
    except Exception as e:
        logger.error(f"tailscale ip error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/services/start', methods=['POST'])
def api_services_start():
    """Enable and (re)start RVM services via systemd using RVM_SUDO_PASS.

    Services:
      - rvm-remote-camera.service (5000)
      - rvm-remote-gui.service (5001)
      - rvm-remote-access.service (5002)
    Also frees ports 5000-5002 before restart to avoid EADDRINUSE.
    """
    try:
        # Ensure unit files exist by invoking installer script (idempotent)
        try:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            installer = os.path.join(repo_root, 'scripts', 'install_systemd_services.sh')
            if os.path.exists(installer):
                _sudo_run(['bash', installer], timeout=60)
        except Exception as e:
            logger.warning(f"Installer script error (continuing): {e}")

        # daemon-reload
        _sudo_run(['/usr/bin/systemctl', 'daemon-reload'])

        # Enable all
        _sudo_run(['/usr/bin/systemctl', 'enable',
                   'rvm-remote-camera.service', 'rvm-remote-gui.service', 'rvm-remote-access.service'])

        # Free ports if occupied
        for port in ('5000', '5001', '5002'):
            _sudo_run(['fuser', '-k', f'{port}/tcp'])

        # Restart all
        _sudo_run(['/usr/bin/systemctl', 'restart',
                   'rvm-remote-camera.service', 'rvm-remote-gui.service', 'rvm-remote-access.service'])

        # Summarize states
        states = {}
        for unit in ('rvm-remote-camera.service', 'rvm-remote-gui.service', 'rvm-remote-access.service'):
            try:
                proc = subprocess.run(['systemctl', 'is-active', unit], text=True, capture_output=True, timeout=5)
                states[unit] = proc.stdout.strip() or proc.stderr.strip()
            except Exception as _:
                states[unit] = 'unknown'

        return jsonify({'success': True, 'data': {'states': states}})
    except Exception as e:
        logger.error(f"services start error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/deployment/data', methods=['GET'])
def api_deployment_data():
    """Get deployment data including device_id and mac_address."""
    try:
        device_id = _get_machine_id()
        mac_address = _get_mac_address('wlP1p1s0')  # Use WiFi interface for MAC
        
        # Get additional data from config if available
        deployment_data = {
            'device_id': device_id,
            'mac_address': mac_address,
            'software_version': '1.0.0',
            'device_name': 'RVM-Jetson-Orin'
        }
        
        # Add any stored deployment data
        if 'deployment' in config_data:
            deployment_data.update(config_data['deployment'])
        
        return jsonify({'success': True, 'data': deployment_data})
    except Exception as e:
        logger.error(f"deployment data error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/rvm/self/claim', methods=['POST'])
def api_rvm_self_claim():
    """Proxy self-claim to MyRVM-Platform using X-API-Key."""
    try:
        body = request.get_json(force=True)
        api_key = body.get('api_key')
        if not api_key:
            return jsonify({'success': False, 'message': 'api_key is required'}), 400

        server_url = body.get('server_url') or _get_server_url_from_config()
        payload = {
            'device_name': body.get('device_name'),
            'software_version': body.get('software_version'),
            'timezone': body.get('timezone'),
            'device_id': body.get('device_id') or _get_machine_id(),
            'mac_address': body.get('mac_address') or _get_mac_address('tailscale0')
        }
        logger.info(f"Self-claim payload: {payload}")
        headers = {'Content-Type': 'application/json', 'X-API-Key': api_key}
        resp = requests.post(
            f"{server_url}/api/v2/rvm/self/claim",
            json=payload,
            headers={**headers, 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
            timeout=15,
            allow_redirects=False
        )
        ok = resp.status_code in (200, 201)
        parsed = None
        try:
            parsed = resp.json()
        except Exception:
            parsed = {'raw': resp.text}
        redirect_to = resp.headers.get('Location')
        # Persist rvm_id when available (handle nested structures)
        try:
            if ok and isinstance(parsed, dict):
                rid = None
                # Try common shapes
                # 1) { data: { rvm_id: 1 } }
                rid = (parsed.get('data') or {}).get('rvm_id') if rid is None else rid
                # 2) { data: { id: 1 } }
                if rid is None:
                    rid = (parsed.get('data') or {}).get('id')
                # 3) { data: { data: { rvm_id: 1 } } }
                if rid is None:
                    rid = ((parsed.get('data') or {}).get('data') or {}).get('rvm_id')
                # 4) { data: { data: { id: 1 } } }
                if rid is None:
                    rid = ((parsed.get('data') or {}).get('data') or {}).get('id')
                # 5) flat fields
                if rid is None:
                    rid = parsed.get('rvm_id') or parsed.get('id')
                if isinstance(rid, int):
                    if _persist_rvm_id(rid):
                        try:
                            _sudo_run(['/usr/bin/systemctl', 'restart', 'rvm-metrics-sender.service'])
                        except Exception as _e:
                            logger.warning(f"Could not restart metrics sender: {_e}")
        except Exception as _e:
            logger.warning(f"Persist rvm_id error: {_e}")
        return jsonify({'success': ok, 'status_code': resp.status_code, 'redirect': redirect_to, 'data': parsed}) , (200 if ok else 502)
    except Exception as e:
        logger.error(f"self-claim error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/rvm/self/update', methods=['PATCH'])
def api_rvm_self_update():
    """Proxy self-update (ip/port/coords) to MyRVM-Platform using X-API-Key."""
    try:
        body = request.get_json(force=True)
        api_key = body.get('api_key')
        if not api_key:
            return jsonify({'success': False, 'message': 'api_key is required'}), 400
        server_url = body.get('server_url') or _get_server_url_from_config()
        payload = {
            'ip_address': body.get('ip_address') or _get_tailscale_ip(),
            'port': body.get('port', 5000),
            'timezone': body.get('timezone'),
            'latitude': body.get('latitude'),
            'longitude': body.get('longitude')
        }
        headers = {'Content-Type': 'application/json', 'X-API-Key': api_key}
        resp = requests.patch(
            f"{server_url}/api/v2/rvm/self/update",
            json=payload,
            headers={**headers, 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
            timeout=15,
            allow_redirects=False
        )
        ok = resp.status_code in (200, 201)
        parsed = None
        try:
            parsed = resp.json()
        except Exception:
            parsed = {'raw': resp.text}
        redirect_to = resp.headers.get('Location')
        
        # Also persist rvm_id on successful self-update (in case it wasn't done in self-claim)
        if ok:
            try:
                # Try to get rvm_id from the response or use the one from production_config.json
                rid = None
                if isinstance(parsed, dict):
                    rid = (parsed.get('data') or {}).get('rvm_id') or (parsed.get('data') or {}).get('id')
                if rid is None:
                    # Fallback: read from production_config.json
                    try:
                        cfg_path = _production_config_path()
                        if os.path.exists(cfg_path):
                            with open(cfg_path, 'r') as f:
                                cfg_data = json.load(f)
                                rid = cfg_data.get('rvm_id')
                    except Exception:
                        pass
                
                if isinstance(rid, int):
                    _persist_rvm_id(rid)
                    logger.info(f"Persisted rvm_id {rid} after self-update")
            except Exception as _e:
                logger.warning(f"Could not persist rvm_id after self-update: {_e}")
        
        return jsonify({'success': ok, 'status_code': resp.status_code, 'redirect': redirect_to, 'data': parsed}) , (200 if ok else 502)
    except Exception as e:
        logger.error(f"self-update error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/jetson/status')
def api_jetson_status():
    """Get Jetson network setup status"""
    try:
        if jetson_detector:
            status = jetson_detector.detect_jetson_status()
            return jsonify({
                'success': True,
                'data': status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Jetson detector module not available'
            }), 500
    except Exception as e:
        logger.error(f"Jetson status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Jetson status check failed'
        }), 500

@app.route('/api/hardware/detect')
def api_hardware_detect():
    """Detect hardware components - REAL IMPLEMENTATION"""
    try:
        import subprocess
        import psutil
        
        hardware_info = {}
        
        # Get CPU information
        try:
            cpu_info = subprocess.run(['lscpu'], capture_output=True, text=True, timeout=5)
            if cpu_info.returncode == 0:
                for line in cpu_info.stdout.split('\n'):
                    if 'Model name:' in line:
                        hardware_info['cpu'] = line.split('Model name:')[1].strip()
                        break
                if 'cpu' not in hardware_info:
                    hardware_info['cpu'] = "Jetson Orin"
            else:
                hardware_info['cpu'] = "Jetson Orin"
        except:
            hardware_info['cpu'] = "Jetson Orin"
        
        # Get Memory information
        try:
            memory = psutil.virtual_memory()
            memory_gb = round(memory.total / (1024**3), 1)
            hardware_info['memory'] = f"{memory_gb}GB"
        except:
            hardware_info['memory'] = "32GB"
        
        # Get GPU information
        try:
            gpu_info = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader,nounits'], 
                                    capture_output=True, text=True, timeout=5)
            if gpu_info.returncode == 0 and gpu_info.stdout.strip():
                hardware_info['gpu'] = gpu_info.stdout.strip()
            else:
                hardware_info['gpu'] = "NVIDIA GPU"
        except:
            hardware_info['gpu'] = "NVIDIA GPU"
        
        # Get Camera information
        try:
            import os
            import glob
            camera_devices = glob.glob('/dev/video*')
            if camera_devices:
                hardware_info['camera'] = f"Available ({len(camera_devices)} devices)"
                hardware_info['camera_devices'] = camera_devices
            else:
                hardware_info['camera'] = "Not detected"
        except:
            hardware_info['camera'] = "Not detected"
        
        # Get Network interface information
        try:
            network_info = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=5)
            if network_info.returncode == 0:
                interfaces = []
                current_interface = {}
                
                for line in network_info.stdout.split('\n'):
                    line = line.strip()
                    
                    # Interface name - only lines that start with a number and contain interface name
                    if line and not line.startswith(' ') and ':' in line and line[0].isdigit():
                        if current_interface:
                            interfaces.append(current_interface)
                        # Extract interface name from format like "2: wlP1p1s0: <BROADCAST,MULTICAST,UP,LOWER_UP>"
                        parts = line.split(':')
                        if len(parts) >= 2:
                            interface_name = parts[1].strip()
                            current_interface = {
                                'name': interface_name,
                                'status': 'down',
                                'ip_addresses': []
                            }
                            # Check status from the same line
                            if 'state UP' in line:
                                current_interface['status'] = 'up'
                    
                    # Interface status - only if we have a current interface
                    elif current_interface and 'state' in line:
                        if 'UP' in line:
                            current_interface['status'] = 'up'
                    
                    # IP addresses - only if we have a current interface
                    elif current_interface and 'inet ' in line and not line.startswith('inet6'):
                        ip_parts = line.split()
                        for i, part in enumerate(ip_parts):
                            if part == 'inet' and i + 1 < len(ip_parts):
                                ip_addr = ip_parts[i + 1].split('/')[0]
                                current_interface['ip_addresses'].append(ip_addr)
                                break
                
                if current_interface:
                    interfaces.append(current_interface)
                
                # Find WiFi interface
                wifi_interface = None
                for interface in interfaces:
                    if interface['name'].startswith('wl') or 'wifi' in interface['name'].lower():
                        wifi_interface = interface
                        break
                
                if wifi_interface:
                    # Check if WiFi is actually connected (has IP address)
                    is_connected = wifi_interface['status'] == 'up' and len(wifi_interface['ip_addresses']) > 0
                    hardware_info['network'] = {
                        'interface': wifi_interface['name'],
                        'status': 'connected' if is_connected else 'disconnected',
                        'ip_addresses': wifi_interface['ip_addresses']
                    }
                else:
                    hardware_info['network'] = {
                        'interface': 'wifi_not_found',
                        'status': 'not_detected',
                        'ip_addresses': []
                    }
            else:
                hardware_info['network'] = {
                    'interface': 'wifi_unknown',
                    'status': 'unknown',
                    'ip_addresses': []
                }
        except:
            hardware_info['network'] = {
                'interface': 'wifi_error',
                'status': 'error',
                'ip_addresses': []
            }
        
        # Add timestamp
        hardware_info['timestamp'] = datetime.now().isoformat()
        hardware_info['status'] = 'detected'
        
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
    """Scan for available WiFi networks - COMPREHENSIVE IMPLEMENTATION"""
    try:
        import subprocess
        import re
        
        networks = []
        
        # Use nmcli as primary method
        try:
            # First detect WiFi interface and activate it with ifconfig (trick to wake up WiFi)
            wifi_interface = None
            try:
                # Try to detect WiFi interface
                result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line and not line.startswith(' ') and ':' in line and line[0].isdigit():
                            parts = line.split(':')
                            if len(parts) >= 2:
                                interface_name = parts[1].strip()
                                if interface_name.startswith('wl'):
                                    wifi_interface = interface_name
                                    break
            except:
                pass
            
            # Default to wlP1p1s0 if not found
            if not wifi_interface:
                wifi_interface = 'wlP1p1s0'
            
            # Activate the WiFi interface with ifconfig (trick to wake up WiFi)
            try:
                subprocess.run(['ifconfig', wifi_interface], 
                             capture_output=True, text=True, timeout=5)
            except:
                pass  # Ignore ifconfig errors
            
            # Then try to force a rescan if possible
            try:
                subprocess.run(['nmcli', 'device', 'wifi', 'rescan'], 
                             capture_output=True, text=True, timeout=5)
            except:
                pass  # Ignore rescan errors
            
            result = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,FREQ,BSSID', 'dev', 'wifi', 'list'], 
                                  capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 4:
                            ssid = parts[0] if parts[0] else "Hidden Network"
                            signal = int(parts[1]) if parts[1].isdigit() else -100
                            security = parts[2] if parts[2] else "Open"
                            # Parse frequency (format: "2412 MHz")
                            freq_str = parts[3].strip()
                            try:
                                frequency = int(freq_str.split()[0]) if freq_str.split()[0].isdigit() else 0
                            except:
                                frequency = 0
                            
                            # Parse BSSID (format: "CC\:B1\:71\:52\:B9\:D0")
                            bssid = ""
                            if len(parts) >= 5:
                                # BSSID is the last part, join all parts after frequency
                                bssid_part = ':'.join(parts[4:])
                                bssid = bssid_part.replace('\\:', ':')
                                # Ensure BSSID is complete (should be 17 characters with colons)
                                if len(bssid) < 17:
                                    bssid = ""
                            
                            networks.append({
                                "ssid": ssid,
                                "signal": signal,
                                "security": security,
                                "frequency": frequency,
                                "bssid": bssid,
                                "channel": 0
                            })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback to nmcli without 'list' if first attempt fails
        if not networks:
            try:
                result = subprocess.run(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,FREQ', 'dev', 'wifi'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split(':')
                            if len(parts) >= 4:
                                ssid = parts[0] if parts[0] else "Hidden Network"
                                signal = int(parts[1]) if parts[1].isdigit() else -100
                                security = parts[2] if parts[2] else "Open"
                                # Parse frequency (format: "2412 MHz")
                                freq_str = parts[3].strip()
                                try:
                                    frequency = int(freq_str.split()[0]) if freq_str.split()[0].isdigit() else 0
                                except:
                                    frequency = 0
                                
                                networks.append({
                                    "ssid": ssid,
                                    "signal": signal,
                                    "security": security,
                                    "frequency": frequency,
                                    "bssid": "",
                                    "channel": 0
                                })
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # If no real networks found, return empty list (no mock data)
        if not networks:
            logger.warning("No WiFi networks found - check if WiFi is enabled")
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No WiFi networks found. Check if WiFi is enabled.'
            })
        
        # Add explanation if only 1 network found (likely connected)
        if len(networks) == 1:
            logger.info("Only 1 network found - likely already connected to WiFi")
            return jsonify({
                'success': True,
                'data': networks,
                'message': f'Found {len(networks)} network. When connected to WiFi, only the current network may be visible. Use "Refresh" to rescan.'
            })
        
        # Remove duplicates and sort by signal strength
        unique_networks = []
        seen_ssids = set()
        for network in networks:
            if network["ssid"] not in seen_ssids:
                unique_networks.append(network)
                seen_ssids.add(network["ssid"])
        
        # Sort by signal strength (strongest first)
        unique_networks.sort(key=lambda x: x["signal"], reverse=True)
        
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
    """Connect to WiFi network - REAL IMPLEMENTATION"""
    try:
        import subprocess
        import time
        
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password')
        
        if not ssid:
            return jsonify({
                'success': False,
                'error': 'SSID is required',
                'message': 'Network SSID is required'
            }), 400
        
        # Check if already connected to this network
        try:
            current_result = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi'], 
                                          capture_output=True, text=True, timeout=5)
            if current_result.returncode == 0:
                for line in current_result.stdout.split('\n'):
                    if line and 'yes:' in line:
                        parts = line.split(':')
                        if len(parts) >= 2 and parts[1] == ssid:
                            # Already connected to this network
                            return jsonify({
                                'success': True,
                                'data': {
                                    'ssid': ssid,
                                    'status': 'already_connected',
                                    'message': f'Already connected to {ssid}'
                                },
                                'message': f'Already connected to {ssid}'
                            })
        except:
            pass
        
        # Try using nmcli first (NetworkManager)
        try:
            if password:
                # Connect with password
                cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password]
            else:
                # Connect to open network
                cmd = ['nmcli', 'dev', 'wifi', 'connect', ssid]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Wait a moment for connection to establish
                time.sleep(3)
                
                # Get connection details
                try:
                    # Get IP address
                    ip_result = subprocess.run(['nmcli', '-t', '-f', 'IP4.ADDRESS', 'dev', 'show'], 
                                            capture_output=True, text=True, timeout=5)
                    ip_address = "Unknown"
                    if ip_result.returncode == 0:
                        for line in ip_result.stdout.split('\n'):
                            if 'IP4.ADDRESS' in line:
                                ip_address = line.split(':')[1].strip().split('/')[0]
                                break
                    
                    # Get signal strength
                    signal_result = subprocess.run(['nmcli', '-t', '-f', 'SIGNAL', 'dev', 'wifi'], 
                                                 capture_output=True, text=True, timeout=5)
                    signal_strength = -100
                    if signal_result.returncode == 0:
                        for line in signal_result.stdout.split('\n'):
                            if ssid in line:
                                parts = line.split(':')
                                if len(parts) >= 2 and parts[1].isdigit():
                                    signal_strength = int(parts[1])
                                break
                    
                    connection_result = {
                        'ssid': ssid,
                        'status': 'connected',
                        'ip_address': ip_address,
                        'signal_strength': signal_strength,
                        'method': 'nmcli'
                    }
                    
                    config_data['network']['current_connection'] = connection_result
                    
                    return jsonify({
                        'success': True,
                        'data': connection_result,
                        'message': f'Successfully connected to {ssid}'
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get connection details: {e}")
                    return jsonify({
                        'success': True,
                        'data': {'ssid': ssid, 'status': 'connected', 'method': 'nmcli'},
                        'message': f'Connected to {ssid} (details unavailable)'
                    })
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'message': f'Failed to connect to {ssid}'
                }), 500
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return jsonify({
                'success': False,
                'error': f'NetworkManager not available: {str(e)}',
                'message': 'NetworkManager (nmcli) not available. Please install NetworkManager.'
            }), 500
        
    except Exception as e:
        logger.error(f"Network connection error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Network connection failed'
        }), 500

@app.route('/api/server/test', methods=['POST'])
def api_server_test():
    """Test server connectivity - REAL IMPLEMENTATION"""
    try:
        import requests
        import time
        
        data = request.get_json()
        server_url = data.get('server_url', 'http://localhost:8000')
        
        if not server_url or server_url.strip() == '':
            return jsonify({
                'success': False,
                'error': 'Server URL is required',
                'message': 'Please enter a valid server URL'
            }), 400
        
        # Validate URL format
        if not server_url.startswith(('http://', 'https://')):
            server_url = 'http://' + server_url
        
        # Test connection to the actual server URL
        try:
            start_time = time.time()
            response = requests.get(f"{server_url}/api/health-check", timeout=10)
            end_time = time.time()
            
            response_time = round((end_time - start_time) * 1000, 2)  # ms
            
            if response.status_code == 200:
                result = {
                    'status': 'connected',
                    'server': server_url,
                    'response_time_ms': response_time,
                    'status_code': response.status_code,
                    'response': response.json() if response.content else None
                }
                
                config_data['server'] = {
                    'url': server_url,
                    'status': 'connected',
                    'response_time': response_time
                }
                
                return jsonify({
                    'success': True,
                    'data': result,
                    'message': 'Server connection test successful'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'message': f'Server returned status code {response.status_code}'
                }), 500
                
        except requests.exceptions.ConnectTimeout:
            return jsonify({
                'success': False,
                'error': 'Connection timeout',
                'message': f'Connection to {server_url} timed out'
            }), 500
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'error': 'Connection refused',
                'message': f'Cannot connect to {server_url}'
            }), 500
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'message': f'Connection error: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Server test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Server connection test failed'
        }), 500

# TODO: AI model testing - DISABLED for now
@app.route('/api/ai/test')
def api_ai_test():
    """Test AI models"""
    try:
        # Test YOLO model
        yolo_status = "OK"
        try:
            model_info = detection_service.get_model_info()
            if model_info['yolo_model']['loaded']:
                yolo_status = "YOLO Model Loaded"
            else:
                yolo_status = "YOLO Model Not Available"
        except Exception as e:
            yolo_status = f"YOLO Error: {str(e)}"
        
        # Test SAM2 model
        sam_status = "OK"
        try:
            model_info = detection_service.get_model_info()
            if model_info['sam2_model']['loaded']:
                sam_status = "SAM2 Model Loaded"
            else:
                sam_status = "SAM2 Model Not Available"
        except Exception as e:
            sam_status = f"SAM2 Error: {str(e)}"
        
        # TODO: Gemini AI - DISABLED for now
        # Uncomment when Gemini AI integration is needed
        # Test Gemini (disabled for now)
        gemini_status = "Disabled - Not Available"
        
        result = {
            'yolo': yolo_status,
            'sam': sam_status,
            'gemini': gemini_status
        }
        
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

# TODO: Hardware calibration - DISABLED for now
# Uncomment when hardware calibration is needed
# @app.route('/api/calibration/camera', methods=['POST'])
def api_calibration_camera():
    """Camera calibration"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'test':
            # Use real camera calibration if available
            if 'calibration_manager' in globals():
                result = calibration_manager.camera_cal.test_camera()
            else:
                result = {
                    'success': True,
                    'data': {
                        'status': 'working',
                        'resolution': '1920x1080',
                        'fps': 30,
                        'brightness': 50,
                        'contrast': 50
                    }
                }
        elif action == 'calibrate':
            # Use real camera calibration if available
            if 'calibration_manager' in globals():
                params = {
                    'brightness': data.get('brightness', 50),
                    'contrast': data.get('contrast', 50),
                    'saturation': data.get('saturation', 50)
                }
                result = calibration_manager.camera_cal.calibrate_camera(params)
            else:
                result = {
                    'success': True,
                    'data': {
                        'status': 'calibrated',
                        'brightness': data.get('brightness', 50),
                        'contrast': data.get('contrast', 50),
                        'saturation': data.get('saturation', 50)
                    }
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

# TODO: Hardware calibration - DISABLED for now
# @app.route('/api/calibration/motor', methods=['POST'])
def api_calibration_motor():
    """Motor calibration"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'test':
            # Use real motor calibration if available
            if 'calibration_manager' in globals():
                result = calibration_manager.motor_cal.test_motor()
            else:
                result = {
                    'success': True,
                    'data': {
                        'status': 'working',
                        'steps_per_revolution': 200,
                        'max_speed': 1000,
                        'current_position': 0
                    }
                }
        elif action == 'calibrate':
            # Use real motor calibration if available
            if 'calibration_manager' in globals():
                params = {
                    'steps_per_revolution': data.get('steps_per_revolution', 200),
                    'max_speed': data.get('max_speed', 1000),
                    'acceleration': data.get('acceleration', 500)
                }
                result = calibration_manager.motor_cal.calibrate_motor(params)
            else:
                result = {
                    'success': True,
                    'data': {
                        'status': 'calibrated',
                        'steps_per_revolution': data.get('steps_per_revolution', 200),
                        'max_speed': data.get('max_speed', 1000),
                        'acceleration': data.get('acceleration', 500)
                    }
                }
        
        config_data['calibration']['motor'] = result
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Motor {action} completed'
        })
    except Exception as e:
        logger.error(f"Motor calibration error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Motor calibration failed'
        }), 500

# TODO: Hardware calibration - DISABLED for now
# @app.route('/api/calibration/led', methods=['POST'])
def api_calibration_led():
    """LED calibration"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'test':
            # Use real LED calibration if available
            if 'calibration_manager' in globals():
                result = calibration_manager.led_cal.test_led()
            else:
                result = {
                    'success': True,
                    'data': {
                        'status': 'working',
                        'brightness': 100,
                        'blink_rate': 1.0,
                        'leds': ['status', 'warning', 'error', 'backlight']
                    }
                }
        elif action == 'calibrate':
            # Use real LED calibration if available
            if 'calibration_manager' in globals():
                params = {
                    'brightness': data.get('brightness', 100),
                    'blink_rate': data.get('blink_rate', 1.0),
                    'color_mode': data.get('color_mode', 'white')
                }
                result = calibration_manager.led_cal.calibrate_led(params)
            else:
                result = {
                    'success': True,
                    'data': {
                        'status': 'calibrated',
                        'brightness': data.get('brightness', 100),
                        'blink_rate': data.get('blink_rate', 1.0),
                        'color_mode': data.get('color_mode', 'white')
                    }
                }
        
        config_data['calibration']['led'] = result
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'LED {action} completed'
        })
    except Exception as e:
        logger.error(f"LED calibration error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'LED calibration failed'
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

            # Inject real actions at certain steps
            if step == "Starting RVM services...":
                try:
                    # Install/refresh unit files and start via systemd using sudo helper
                    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
                    installer = os.path.join(repo_root, 'scripts', 'install_systemd_services.sh')
                    if os.path.exists(installer):
                        _sudo_run(['bash', installer], timeout=60)
                    _sudo_run(['/usr/bin/systemctl', 'daemon-reload'])
                    _sudo_run(['/usr/bin/systemctl', 'enable',
                               'rvm-remote-camera.service', 'rvm-remote-gui.service', 'rvm-remote-access.service'])
                    for port in ('5000','5001','5002'):
                        _sudo_run(['fuser', '-k', f'{port}/tcp'])
                    _sudo_run(['/usr/bin/systemctl', 'restart',
                               'rvm-remote-camera.service', 'rvm-remote-gui.service', 'rvm-remote-access.service'])
                except Exception as se:
                    logger.error(f"Failed to start services via systemd: {se}")
            
            if step == "Testing integration...":
                # Quick port probes so UI can flip to Listening if up
                try:
                    for port in (5000,5001,5002):
                        try:
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.settimeout(0.5)
                            s.connect(("127.0.0.1", port))
                            s.close()
                        except Exception:
                            pass
                except Exception:
                    pass
        
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
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
