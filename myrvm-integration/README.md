# MyRVM Integration for Jetson Orin

This folder contains the integration layer between Jetson Orin and MyRVM Platform for computer vision and object detection.

## 📁 Folder Structure

```
myrvm-integration/
├── api-client/                    # API communication with MyRVM Platform
│   └── myrvm_api_client.py       # Main API client
├── services/                      # Core services
│   └── detection_service.py      # AI detection and segmentation service
├── main/                         # Main application
│   ├── jetson_main.py           # Main coordinator
│   └── config.json              # Configuration file
├── debug/                        # Debugging and monitoring tools
│   ├── system_monitor.py        # System monitoring
│   └── test_integration.py      # Integration testing
├── logs/                         # Log files (auto-created)
└── README.md                     # This file
```

## 🚀 Quick Start

### 1. Prerequisites

Make sure you have:
- Python 3.8+ with virtual environment activated
- Required packages installed (see requirements below)
- AI models in `../models/` directory
- MyRVM Platform running on `http://localhost:8000`

### 2. Configuration

Edit `main/config.json` to match your setup:

```json
{
  "myrvm_base_url": "http://localhost:8000",
  "camera_index": 0,
  "rvm_id": 1,
  "models_dir": "../models",
  "capture_interval": 5.0,
  "confidence_threshold": 0.5,
  "auto_processing": true
}
```

### 3. Run Integration Tests

```bash
cd myrvm-integration
python3 debug/test_integration.py
```

### 4. Start Main Application

```bash
cd myrvm-integration
python3 main/jetson_main.py
```

## 🔧 Components

### API Client (`api-client/myrvm_api_client.py`)

Handles all communication with MyRVM Platform:

- **Engine Registration**: Register Jetson Orin as processing engine
- **Session Management**: Create and manage RVM sessions
- **Deposit Processing**: Create deposits and upload AI analysis results
- **Edge Vision Integration**: Upload detection results and trigger processing
- **File Upload**: Upload images and detection data

**Key Methods:**
- `register_processing_engine()` - Register with MyRVM Platform
- `create_deposit()` - Create new deposit record
- `process_deposit()` - Upload AI analysis results
- `upload_detection_results()` - Send detection results to Edge Vision

### Detection Service (`services/detection_service.py`)

Handles AI model operations:

- **Object Detection**: YOLO11 object detection
- **Object Segmentation**: SAM2 segmentation
- **Model Management**: Load and manage AI models
- **Result Processing**: Process and format detection results

**Key Methods:**
- `detect_objects()` - Run YOLO detection
- `segment_objects()` - Run SAM2 segmentation
- `detect_and_segment()` - Run both detection and segmentation
- `save_results()` - Save results to file

### Main Coordinator (`main/jetson_main.py`)

Main application that coordinates everything:

- **Camera Management**: Initialize and manage camera
- **Processing Loop**: Continuous image capture and processing
- **Background Processing**: Queue-based processing system
- **Platform Integration**: Register and communicate with MyRVM Platform

**Key Features:**
- Automatic image capture at intervals
- Background AI processing
- Real-time communication with MyRVM Platform
- Graceful shutdown handling

### System Monitor (`debug/system_monitor.py`)

Monitors system resources and performance:

- **System Resources**: CPU, memory, disk, network usage
- **GPU Monitoring**: NVIDIA GPU status and usage
- **Process Monitoring**: Running processes and resource usage
- **Network Connections**: Active network connections
- **Health Status**: Overall system health assessment

### Integration Tester (`debug/test_integration.py`)

Comprehensive testing tool:

- **System Requirements**: Check Python version, packages, system health
- **Model Availability**: Verify AI models are loaded
- **Camera Testing**: Test camera functionality
- **Platform Connectivity**: Test MyRVM Platform connection
- **Detection Service**: Test AI detection and segmentation
- **File System**: Check directories and permissions
- **Network**: Test internet and platform connectivity

## 📊 Data Flow

```
Camera → Image Capture → AI Processing → Results → MyRVM Platform
   ↓           ↓              ↓           ↓            ↓
  CV2    →  Detection   →  YOLO/SAM2  →  JSON    →  API Client
```

### 1. Image Capture
- Camera captures image at configured intervals
- Image saved to `../storages/images/camera_captures/`

### 2. AI Processing
- YOLO11 detects objects in image
- SAM2 segments detected objects
- Results formatted as JSON

### 3. Platform Communication
- Results uploaded to MyRVM Platform
- Deposit records created/updated
- Edge Vision dashboard updated

## 🔍 Debugging and Monitoring

### Log Files

All components generate detailed logs in `logs/` directory:

- `api_client_YYYYMMDD.log` - API communication logs
- `detection_service_YYYYMMDD.log` - AI processing logs
- `jetson_main_YYYYMMDD.log` - Main application logs
- `system_monitor_YYYYMMDD.log` - System monitoring logs
- `integration_test_results_YYYYMMDD_HHMMSS.json` - Test results

### System Monitoring

```bash
# Monitor system resources
python3 debug/system_monitor.py

# Run integration tests
python3 debug/test_integration.py
```

### Debug Mode

Enable debug mode in `config.json`:

```json
{
  "debug_mode": true,
  "log_level": "DEBUG"
}
```

## 📋 Requirements

### Python Packages

```bash
pip install opencv-python numpy requests ultralytics psutil
```

### AI Models

Required models in `../models/` directory:

- `best.pt` - Custom YOLO model (preferred)
- `yolo11n.pt` - YOLO11 nano model (fallback)
- `sam2.1_b.pt` - SAM2.1 base model

### System Requirements

- **RAM**: 4GB+ (8GB recommended)
- **Storage**: 2GB+ free space
- **Camera**: USB webcam
- **Network**: Connection to MyRVM Platform

## 🎯 Configuration Options

### Main Configuration (`main/config.json`)

| Option | Description | Default |
|--------|-------------|---------|
| `myrvm_base_url` | MyRVM Platform URL | `http://localhost:8000` |
| `camera_index` | Camera device index | `0` |
| `rvm_id` | RVM ID for this device | `1` |
| `capture_interval` | Image capture interval (seconds) | `5.0` |
| `confidence_threshold` | AI detection confidence threshold | `0.5` |
| `auto_processing` | Enable automatic processing | `true` |
| `debug_mode` | Enable debug logging | `true` |

### API Client Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `api_token` | API authentication token | `null` |
| `timeout` | Request timeout (seconds) | `30` |
| `retry_attempts` | Number of retry attempts | `3` |

## 🚨 Troubleshooting

### Common Issues

1. **Camera not detected**
   ```bash
   # Check camera devices
   ls /dev/video*
   
   # Test camera
   python3 ../camera/camera_test.py
   ```

2. **Models not found**
   ```bash
   # Check models directory
   ls -la ../models/
   
   # Download models
   python3 ../download_yolo11n.py
   ```

3. **MyRVM Platform connection failed**
   ```bash
   # Test connectivity
   curl http://localhost:8000/api/health
   
   # Check platform status
   docker-compose ps
   ```

4. **High memory usage**
   ```bash
   # Monitor system resources
   python3 debug/system_monitor.py
   
   # Check processes
   htop
   ```

### Performance Optimization

1. **Reduce capture interval** for lower CPU usage
2. **Lower confidence threshold** for more detections
3. **Use lighter models** (yolo11n.pt instead of best.pt)
4. **Enable GPU acceleration** if available

## 📈 Performance Metrics

### Expected Performance

- **Image Capture**: 1-2 FPS
- **YOLO Detection**: 0.5-2 seconds per image
- **SAM2 Segmentation**: 1-3 seconds per image
- **API Communication**: 0.1-0.5 seconds per request

### Monitoring

Use system monitor to track:
- CPU usage (should be < 80%)
- Memory usage (should be < 80%)
- GPU usage (if available)
- Network throughput
- Processing queue length

## 🔄 Updates and Maintenance

### Regular Maintenance

1. **Check logs** for errors and warnings
2. **Monitor system resources** for performance issues
3. **Update models** when new versions available
4. **Test integration** after system updates

### Updates

1. **Pull latest changes** from GitHub
2. **Run integration tests** to verify functionality
3. **Update configuration** if needed
4. **Restart services** to apply changes

## 📞 Support

For issues and questions:

1. **Check logs** in `logs/` directory
2. **Run integration tests** to identify problems
3. **Monitor system resources** for performance issues
4. **Review configuration** for incorrect settings

## 📄 License

This integration layer is part of the MyRVM Platform project.
