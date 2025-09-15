# Camera Scripts for Jetson Orin Nano

This folder contains Python scripts for camera functionality on Jetson Orin Nano.

## 📁 Available Scripts

### 1. `camera_test.py` - Camera Testing Script
Tests USB camera functionality and displays camera information.

**Features:**
- ✅ **Camera detection** - Scans for available cameras (indices 0-9)
- ✅ **Camera properties** - Shows resolution, FPS, and capabilities
- ✅ **Test frame capture** - Captures and saves a test image
- ✅ **Error handling** - Comprehensive error checking and tips

**Usage:**
```bash
cd camera
python3 camera_test.py
```

**Output:**
- Lists all available cameras
- Tests first available camera
- Saves test image to `storages/images/camera_test/`

### 2. `live_camera.py` - Web-based Live Camera Feed
Web-based live camera feed with start/stop controls (TTY compatible).

**Features:**
- ✅ **Web interface** - Access camera through web browser
- ✅ **Start/Stop controls** - Start and stop camera remotely
- ✅ **Live feed** - Real-time camera display
- ✅ **FPS counter** - Shows current and average FPS
- ✅ **Frame capture** - Save frames via web interface
- ✅ **Statistics** - Session statistics and performance metrics
- ✅ **TTY compatible** - Works without GUI display

**Usage:**
```bash
cd camera
python3 live_camera.py [camera_index]
```

**Access:**
- **Local**: http://localhost:5000
- **Network**: http://[JETSON_IP]:5000

**Web Controls:**
- **📸 Capture Image** - Save current frame
- **🔄 Refresh Stream** - Restart video stream
- **▶️ Start Camera** - Start camera streaming
- **⏹️ Stop Camera** - Stop camera streaming

**Output:**
- Web interface accessible from any browser
- Captured images saved to `storages/images/camera_captures/`

### 3. `camera_yolo_inference.py` - Real-time YOLO Detection
Combines camera feed with YOLO object detection for real-time inference.

**Features:**
- ✅ **Auto-download models** - Automatically downloads YOLO models if missing
- ✅ **Real-time detection** - Live object detection on camera feed
- ✅ **Detection overlay** - Bounding boxes and labels on video
- ✅ **Performance metrics** - FPS and detection statistics
- ✅ **Frame saving** - Save frames with detection results
- ✅ **Multiple models** - Support for different YOLO models

**Usage:**
```bash
cd camera
python3 camera_yolo_inference.py [camera_index] [model_path]
```

**Examples:**
```bash
# Use default camera (0) and best.pt model
python3 camera_yolo_inference.py

# Use camera index 1
python3 camera_yolo_inference.py 1

# Use specific model
python3 camera_yolo_inference.py 0 ../models/yolo11n.pt
```

**Controls:**
- `q` or `ESC` - Quit
- `s` - Save current frame with detection
- `Ctrl+C` - Force quit

**Output:**
- Live detection window
- Detection results saved to `storages/images/camera_yolo/`

### 4. `web_camera.py` - Advanced Web-based Camera Feed
Advanced web camera with full features and controls (TTY compatible).

**Features:**
- ✅ **Web interface** - Access camera through web browser
- ✅ **TTY compatible** - Works without GUI display
- ✅ **Network access** - Access from any device on same network
- ✅ **Advanced controls** - Capture, info, and camera management
- ✅ **Real-time streaming** - Live camera feed in browser
- ✅ **Statistics** - FPS, frame count, and uptime monitoring

**Usage:**
```bash
cd camera
python3 web_camera.py [camera_index]
```

**Access:**
- **Local**: http://localhost:5000
- **Network**: http://[JETSON_IP]:5000
- **Example**: http://192.168.1.11:5000

**Features:**
- Live camera feed in web browser
- Works on any device (phone, tablet, computer)
- No GUI required (perfect for TTY/SSH)
- Real-time streaming with MJPEG
- Camera information and statistics
- Image capture functionality

**Output:**
- Web interface accessible from any browser
- Live camera feed at `/video_feed` endpoint
- Captured images saved to `storages/images/camera_captures/`

## 🔧 Camera Setup

### USB Camera Connection
1. Connect USB camera to Jetson Orin Nano
2. Check camera detection:
   ```bash
   lsusb
   ls /dev/video*
   ```

### Camera Index Detection
Run the test script to find available cameras:
```bash
python3 camera_test.py
```

### Common Camera Indices
- `/dev/video0` - Usually first USB camera
- `/dev/video1` - Second USB camera or built-in camera
- `/dev/video2` - Additional cameras

## 📊 Performance Tips

### For Better Performance
1. **Lower resolution** - Scripts default to 640x480
2. **Reduce FPS** - Lower FPS for better processing
3. **Use lighter models** - yolo11n.pt is faster than best.pt
4. **Close other applications** - Free up system resources

### For Better Quality
1. **Higher resolution** - Modify camera settings in scripts
2. **Better lighting** - Ensure good lighting conditions
3. **Stable camera** - Use tripod or stable mount
4. **Use best.pt model** - For highest detection accuracy

## 🐛 Troubleshooting

### Camera Not Detected
```bash
# Check USB devices
lsusb

# Check video devices
ls /dev/video*

# Check camera permissions
sudo chmod 666 /dev/video0
```

### Camera Permission Issues
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Logout and login again
```

### Low FPS Issues
1. Check system resources: `htop`
2. Close unnecessary applications
3. Use lighter YOLO model (yolo11n.pt)
4. Reduce camera resolution

### OpenCV Issues
```bash
# Reinstall opencv-python
pip uninstall opencv-python
pip install opencv-python
```

## 📁 Output Directories

- `../storages/images/camera_test/` - Test images
- `../storages/images/camera_captures/` - Live feed captures
- `../storages/images/camera_yolo/` - YOLO detection results

## 🔗 Integration

These camera scripts integrate with:
- **YOLO models** - Auto-download from `download_yolo11n.py`
- **Storage system** - Uses existing `storages/` structure
- **Model system** - Compatible with `models/` folder

## 📝 Notes

- Scripts are optimized for Jetson Orin Nano
- Default camera resolution: 640x480
- Default FPS: 30 (may vary by camera)
- All scripts include comprehensive error handling
- Keyboard interrupts are properly handled
