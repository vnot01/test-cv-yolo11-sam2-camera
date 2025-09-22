# RVM-Jetson Installation Method

This directory contains the complete installation method implementation for RVM-Jetson devices, providing a web-based interface for hardware calibration, network configuration, and system deployment.

## 🚀 Quick Start

### Prerequisites
- NVIDIA Jetson device (Orin Nano recommended)
- Python 3.10+ with virtual environment
- Internet connection for initial setup

### Installation

1. **Activate Virtual Environment**
   ```bash
   cd /home/my/test-cv-yolo11-sam2-camera/myrvm-integration
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   cd installation_method
   pip install -r requirements.txt
   ```

3. **Run Installation Script**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

4. **Access Web Interface**
   - Open browser to: `http://localhost:8080/install`
   - Follow the installation wizard

## 📁 Directory Structure

```
installation_method/
├── web_config_gui/           # Web-based configuration interface
│   ├── app.py               # Main Flask application
│   ├── templates/           # HTML templates
│   │   ├── dashboard.html   # Main dashboard
│   │   ├── install.html     # Installation wizard
│   │   ├── hardware.html    # Hardware calibration
│   │   ├── network.html     # Network configuration
│   │   ├── config.html      # System configuration
│   │   └── deploy.html      # Deployment interface
│   └── static/              # Static assets (CSS, JS, images)
├── hardware_calibration/     # Hardware calibration modules
│   ├── __init__.py
│   ├── calibration_manager.py
│   ├── camera_calibration.py
│   ├── motor_calibration.py
│   ├── led_calibration.py
│   ├── touch_calibration.py
│   ├── gpio_calibration.py
│   ├── sensor_calibration.py
│   └── audio_calibration.py
├── install.sh               # Main installation script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Features

### Web Configuration Interface
- **Dashboard**: Overview of system status and quick actions
- **Installation Wizard**: Step-by-step installation process
- **Hardware Calibration**: Test and calibrate all hardware components
- **Network Configuration**: WiFi setup and server connection
- **System Configuration**: Review and validate system settings
- **Deployment**: Deploy and start RVM services

### Hardware Calibration
- **Camera**: Resolution, FPS, brightness, contrast calibration
- **Motor**: Stepper motor testing and calibration
- **LEDs**: Status, warning, and error LED testing
- **Touch Screen**: Sensitivity and pressure threshold calibration
- **GPIO**: Input/output pin testing and configuration
- **Sensors**: Door, weight, proximity, temperature, humidity sensors
- **Audio**: Speaker and microphone testing

### Network Management
- **WiFi Scanning**: Automatic network discovery
- **Connection Management**: Easy WiFi connection setup
- **Server Configuration**: API endpoint and authentication setup
- **Network Monitoring**: Connection status and history

### System Deployment
- **Pre-deployment Checks**: System validation
- **Service Installation**: Automated service setup
- **Hardware Initialization**: Component testing and setup
- **AI Models Loading**: YOLO and SAM model initialization
- **Network Configuration**: Final network setup
- **Service Startup**: Starting all RVM services
- **System Testing**: Final validation tests

## 🎯 Installation Process

### Phase 1: Hardware Detection
1. Detect and validate all hardware components
2. Test camera, motor, LEDs, touch screen, GPIO, sensors, audio
3. Generate hardware compatibility report

### Phase 2: Network Configuration
1. Scan for available WiFi networks
2. Connect to selected network
3. Test server connectivity
4. Configure API endpoints

### Phase 3: AI Models Testing
1. Test YOLO object detection model
2. Test SAM segmentation model
3. Test Gemini AI integration
4. Validate model performance

### Phase 4: Hardware Calibration
1. Calibrate camera settings (brightness, contrast, resolution)
2. Calibrate motor parameters (steps, speed, acceleration)
3. Calibrate LED brightness and patterns
4. Calibrate touch screen sensitivity
5. Configure GPIO pins and sensors
6. Test audio system

### Phase 5: System Configuration
1. Set RVM ID and location
2. Configure timezone and system settings
3. Validate all configuration parameters
4. Generate configuration report

### Phase 6: Deployment
1. Run pre-deployment validation
2. Install and configure services
3. Initialize hardware components
4. Load AI models
5. Configure network connections
6. Start all RVM services
7. Run final system tests

## 🔌 API Endpoints

### Hardware Calibration
- `GET /api/hardware/detect` - Detect hardware components
- `POST /api/calibration/camera` - Camera calibration
- `POST /api/calibration/motor` - Motor calibration
- `POST /api/calibration/led` - LED calibration
- `POST /api/calibration/touch` - Touch screen calibration
- `POST /api/calibration/gpio` - GPIO calibration
- `POST /api/calibration/sensors` - Sensor calibration
- `POST /api/calibration/audio` - Audio calibration

### Network Management
- `GET /api/network/scan` - Scan WiFi networks
- `POST /api/network/connect` - Connect to WiFi
- `POST /api/server/test` - Test server connection

### AI Models
- `GET /api/ai/test` - Test AI models
- `POST /api/ai/load` - Load AI models

### Configuration
- `GET /api/config/status` - Get configuration status
- `POST /api/config/save` - Save configuration
- `GET /api/config/export` - Export configuration

### Deployment
- `POST /api/deploy/start` - Start deployment
- `GET /api/deploy/status` - Get deployment status
- `POST /api/deploy/stop` - Stop deployment

## 🛠️ Usage Examples

### Manual Hardware Testing
```python
from hardware_calibration import CalibrationManager

# Initialize calibration manager
cal_manager = CalibrationManager()

# Test all hardware components
results = cal_manager.test_all_components()
print(f"Hardware test results: {results}")

# Calibrate specific component
camera_result = cal_manager.calibrate_component('camera', {
    'brightness': 60,
    'contrast': 70,
    'resolution': '1920x1080'
})
```

### Network Configuration
```python
# Test network connection
import requests

response = requests.get('http://localhost:8080/api/network/scan')
networks = response.json()['data']

# Connect to network
connect_data = {
    'ssid': 'MyRVM-Network',
    'password': 'password123'
}
response = requests.post('http://localhost:8080/api/network/connect', json=connect_data)
```

### Deployment Monitoring
```python
# Monitor deployment progress
import socketio

sio = socketio.Client()

@sio.event
def deployment_progress(data):
    print(f"Deployment progress: {data['progress']}% - {data['message']}")

@sio.event
def deployment_complete(data):
    print("Deployment completed successfully!")

sio.connect('http://localhost:8080')
```

## 🔍 Troubleshooting

### Common Issues

1. **Camera Not Detected**
   - Check camera permissions
   - Verify camera is not in use by another process
   - Test with `v4l2-ctl --list-devices`

2. **GPIO Permission Denied**
   - Add user to gpio group: `sudo usermod -a -G gpio $USER`
   - Reboot or logout/login

3. **Network Connection Failed**
   - Check WiFi credentials
   - Verify network interface is up
   - Test with `iwconfig` and `ifconfig`

4. **AI Models Not Loading**
   - Check model files exist
   - Verify sufficient memory available
   - Check CUDA/GPU availability

### Log Files
- Installation logs: `logs/installation.log`
- Web GUI logs: `logs/web_config_gui.log`
- Hardware calibration: `logs/hardware_calibration.log`

### Debug Mode
Enable debug mode by setting environment variable:
```bash
export FLASK_DEBUG=1
python web_config_gui/app.py
```

## 📊 Performance Monitoring

### System Resources
- CPU usage monitoring
- Memory usage tracking
- GPU utilization
- Temperature monitoring

### Hardware Status
- Real-time hardware status
- Component health monitoring
- Performance metrics
- Error reporting

## 🔒 Security Considerations

- All network communications use HTTPS in production
- Authentication tokens for API access
- Input validation and sanitization
- Secure configuration storage
- Regular security updates

## 📈 Future Enhancements

- [ ] Remote deployment capabilities
- [ ] Automated testing suite
- [ ] Performance benchmarking
- [ ] Cloud configuration sync
- [ ] Advanced diagnostics
- [ ] Multi-device management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Contact the development team

---

**Note**: This installation method is designed specifically for NVIDIA Jetson devices running the RVM-Jetson system. Ensure your hardware meets the minimum requirements before proceeding with installation.
