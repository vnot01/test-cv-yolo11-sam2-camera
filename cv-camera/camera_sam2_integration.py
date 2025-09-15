#!/usr/bin/env python3
"""
Camera + SAM2 Integration Script
Integrates web camera with SAM2 segmentation for real-time object detection and segmentation
"""

import cv2
import sys
import time
import threading
import subprocess
import os
from pathlib import Path
from flask import Flask, render_template, Response, jsonify
import json

app = Flask(__name__)

# Global variables
camera = None
camera_index = 0
frame_width = 640
frame_height = 480
fps = 25
is_streaming = False
frame_count = 0
start_time = time.time()

# Paths
CAPTURE_DIR = Path("/home/my/mycv/storages/images/camera_captures")
OUTPUT_DIR = Path("/home/my/mycv/storages/images/output")
CAMERA_SAM2_DIR = Path("/home/my/mycv/storages/images/output/camera_sam2")
RESULTS_DIR = Path("/home/my/mycv/storages/images/output/camera_sam2/results")
INFERENCE_LOG_DIR = Path("/home/my/mycv/storages/images/output/camera_sam2/results/inference")
DETECTION_IMAGES_DIR = Path("/home/my/mycv/storages/images/output/camera_sam2/results/images")
SAM2_SCRIPT = Path("/home/my/mycv/cv-camera/camera_sam2_inference.py")

def init_camera():
    """Initialize camera"""
    global camera, camera_index, frame_width, frame_height, fps
    
    print(f"🔧 Initializing camera {camera_index}...")
    camera = cv2.VideoCapture(camera_index)
    
    if not camera.isOpened():
        print(f"❌ Error: Cannot open camera {camera_index}")
        return False
    
    # Set camera properties
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    camera.set(cv2.CAP_PROP_FPS, fps)
    
    # Get actual properties
    actual_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = camera.get(cv2.CAP_PROP_FPS)
    
    print(f"✅ Camera initialized: {actual_width}x{actual_height} @ {actual_fps} FPS")
    return True

def generate_frames():
    """Generate frames for streaming"""
    global camera, is_streaming, frame_count, start_time
    
    while True:
        if not is_streaming or camera is None:
            time.sleep(0.1)
            continue
            
        if not camera.isOpened():
            time.sleep(0.1)
            continue
            
        ret, frame = camera.read()
        
        if not ret:
            time.sleep(0.1)
            continue
        
        frame_count += 1
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        if ret:
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(1.0 / fps)

def run_sam2_inference(image_path):
    """Run SAM2 inference on captured image"""
    try:
        print(f"🔍 Running SAM2 inference on: {image_path}")
        
        # Run SAM2 script with image path as argument
        result = subprocess.run([
            sys.executable, str(SAM2_SCRIPT), str(image_path)
        ], capture_output=True, text=True, cwd="/home/my/mycv")
        
        if result.returncode == 0:
            print("✅ SAM2 inference completed successfully")
            return True, result.stdout
        else:
            print(f"❌ SAM2 inference failed: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        print(f"❌ Error running SAM2 inference: {e}")
        return False, str(e)

@app.route('/')
def index():
    """Main page"""
    return render_template('camera_sam2.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    global is_streaming
    
    if not is_streaming:
        is_streaming = True
    
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera_info')
def camera_info():
    """Get camera information"""
    global camera, frame_count, start_time, is_streaming
    
    if camera is None or not is_streaming:
        return jsonify({
            'error': 'Camera not initialized',
            'resolution': 'N/A',
            'fps': 0,
            'current_fps': 0,
            'frame_count': 0,
            'uptime': 0
        })
    
    try:
        elapsed_time = time.time() - start_time
        current_fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        
        width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        camera_fps = camera.get(cv2.CAP_PROP_FPS)
        
        return jsonify({
            'resolution': f"{width}x{height}",
            'fps': camera_fps,
            'current_fps': round(current_fps, 2),
            'frame_count': frame_count,
            'uptime': round(elapsed_time, 2)
        })
    except Exception as e:
        return jsonify({
            'error': f'Camera error: {str(e)}',
            'resolution': 'N/A',
            'fps': 0,
            'current_fps': 0,
            'frame_count': 0,
            'uptime': 0
        })

@app.route('/capture_and_infer')
def capture_and_infer():
    """Capture image and run SAM2 inference"""
    global camera
    
    if camera is None:
        return jsonify({'error': 'Camera not initialized'})
    
    ret, frame = camera.read()
    
    if not ret:
        return jsonify({'error': 'Cannot capture frame'})
    
    # Create directories
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CAMERA_SAM2_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    INFERENCE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    DETECTION_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save captured image
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"camera_capture_{timestamp}.jpg"
    filepath = CAPTURE_DIR / filename
    
    cv2.imwrite(str(filepath), frame)
    print(f"📸 Image captured: {filepath}")
    
    # Run SAM2 inference in background thread
    def run_inference():
        success, output = run_sam2_inference(str(filepath))
        
        # Save inference result to inference log folder
        result_file = INFERENCE_LOG_DIR / f"inference_result_{timestamp}.txt"
        with open(result_file, 'w') as f:
            f.write(f"Image: {filename}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Success: {success}\n")
            f.write(f"Output:\n{output}\n")
        
        print(f"📊 Inference result saved: {result_file}")
    
    # Start inference in background
    inference_thread = threading.Thread(target=run_inference)
    inference_thread.daemon = True
    inference_thread.start()
    
    return jsonify({
        'success': True,
        'filename': filename,
        'path': str(filepath),
        'message': 'Image captured and SAM2 inference started'
    })

@app.route('/capture')
def capture():
    """Capture current frame only"""
    global camera
    
    if camera is None:
        return jsonify({'error': 'Camera not initialized'})
    
    ret, frame = camera.read()
    
    if not ret:
        return jsonify({'error': 'Cannot capture frame'})
    
    # Save image
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"camera_capture_{timestamp}.jpg"
    filepath = CAPTURE_DIR / filename
    
    cv2.imwrite(str(filepath), frame)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'path': str(filepath)
    })

@app.route('/start')
def start_camera():
    """Start camera streaming"""
    global is_streaming, camera, camera_index, frame_count, start_time
    
    if camera is not None and camera.isOpened():
        return jsonify({'success': False, 'message': 'Camera already running'})
    
    if camera is not None:
        camera.release()
        camera = None
    
    time.sleep(0.5)
    
    camera = cv2.VideoCapture(camera_index)
    
    if not camera.isOpened():
        return jsonify({'success': False, 'message': 'Cannot open camera'})
    
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    camera.set(cv2.CAP_PROP_FPS, fps)
    
    frame_count = 0
    start_time = time.time()
    
    time.sleep(0.5)
    
    is_streaming = True
    
    return jsonify({'success': True, 'message': 'Camera started'})

@app.route('/stop')
def stop_camera():
    """Stop camera streaming"""
    global is_streaming, camera
    
    is_streaming = False
    
    if camera:
        camera.release()
        camera = None
    
    return jsonify({'success': True, 'message': 'Camera stopped'})

def create_html_template():
    """Create HTML template for camera + SAM2 interface"""
    template_dir = Path("templates")
    template_dir.mkdir(exist_ok=True)
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jetson Orin Nano - Camera + SAM2</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .camera-container {
            text-align: center;
            margin-bottom: 20px;
        }
        #video-stream {
            max-width: 100%;
            height: auto;
            border: 2px solid #ddd;
            border-radius: 10px;
        }
        .controls {
            text-align: center;
            margin: 20px 0;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 0 10px;
            font-size: 16px;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .sam2-button {
            background-color: #9C27B0;
        }
        .sam2-button:hover {
            background-color: #7B1FA2;
        }
        .info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .info-card {
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }
        .info-card h3 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .info-card p {
            margin: 0;
            font-size: 18px;
            font-weight: bold;
            color: #666;
        }
        .status {
            text-align: center;
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .status.online {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.offline {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .log {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            margin-top: 20px;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥🎯 Jetson Orin Nano - Camera + SAM2</h1>
        
        <div class="status online" id="status">
            📡 Camera Online
        </div>
        
        <div class="camera-container">
            <img id="video-stream" src="{{ url_for('video_feed') }}" alt="Camera Feed">
        </div>
        
        <div class="controls">
            <button onclick="captureImage()">📸 Capture Image</button>
            <button onclick="captureAndInfer()" class="sam2-button">🎯 Capture + SAM2</button>
            <button onclick="refreshStream()">🔄 Refresh Stream</button>
            <button onclick="startCamera()" id="start-btn">▶️ Start Camera</button>
            <button onclick="stopCamera()" id="stop-btn">⏹️ Stop Camera</button>
        </div>
        
        <div class="info" id="camera-info">
            <div class="info-card">
                <h3>Resolution</h3>
                <p id="resolution">Loading...</p>
            </div>
            <div class="info-card">
                <h3>FPS</h3>
                <p id="fps">Loading...</p>
            </div>
            <div class="info-card">
                <h3>Current FPS</h3>
                <p id="current-fps">Loading...</p>
            </div>
            <div class="info-card">
                <h3>Frame Count</h3>
                <p id="frame-count">Loading...</p>
            </div>
            <div class="info-card">
                <h3>Uptime</h3>
                <p id="uptime">Loading...</p>
            </div>
        </div>
        
        <div class="log" id="log">
            <strong>📋 Activity Log:</strong><br>
            <div id="log-content">System ready...</div>
        </div>
    </div>

    <script>
        function log(message) {
            const logContent = document.getElementById('log-content');
            const timestamp = new Date().toLocaleTimeString();
            logContent.innerHTML += `[${timestamp}] ${message}<br>`;
            logContent.scrollTop = logContent.scrollHeight;
        }
        
        function updateCameraInfo() {
            fetch('/camera_info')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('status').innerHTML = '❌ Camera Error';
                        document.getElementById('status').className = 'status offline';
                        return;
                    }
                    
                    document.getElementById('resolution').textContent = data.resolution;
                    document.getElementById('fps').textContent = data.fps;
                    document.getElementById('current-fps').textContent = data.current_fps;
                    document.getElementById('frame-count').textContent = data.frame_count;
                    document.getElementById('uptime').textContent = data.uptime + 's';
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('status').innerHTML = '❌ Connection Error';
                    document.getElementById('status').className = 'status offline';
                });
        }
        
        function captureImage() {
            log('📸 Capturing image...');
            fetch('/capture')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        log(`✅ Image captured: ${data.filename}`);
                        alert('Image captured: ' + data.filename);
                    } else {
                        log(`❌ Capture failed: ${data.error}`);
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    log('❌ Capture error');
                    alert('Error capturing image');
                });
        }
        
        function captureAndInfer() {
            log('🎯 Capturing image and running SAM2 inference...');
            fetch('/capture_and_infer')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        log(`✅ Image captured: ${data.filename}`);
                        log('🔍 SAM2 inference started in background...');
                        alert('Image captured and SAM2 inference started!');
                    } else {
                        log(`❌ Capture + SAM2 failed: ${data.error}`);
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    log('❌ Capture + SAM2 error');
                    alert('Error capturing image and running SAM2');
                });
        }
        
        function refreshStream() {
            const img = document.getElementById('video-stream');
            img.src = '/video_feed?t=' + new Date().getTime();
            log('🔄 Video stream refreshed');
        }
        
        function startCamera() {
            log('▶️ Starting camera...');
            fetch('/start')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        log('✅ Camera started');
                        updateButtonStates(true);
                        const img = document.getElementById('video-stream');
                        img.src = '/video_feed?t=' + new Date().getTime();
                    } else {
                        log(`❌ Start failed: ${data.message}`);
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    log('❌ Start error');
                    alert('Error starting camera');
                });
        }
        
        function stopCamera() {
            log('⏹️ Stopping camera...');
            fetch('/stop')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        log('✅ Camera stopped');
                        updateButtonStates(false);
                        const img = document.getElementById('video-stream');
                        img.src = '';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    log('❌ Stop error');
                    alert('Error stopping camera');
                });
        }
        
        function updateButtonStates(cameraRunning) {
            const startBtn = document.getElementById('start-btn');
            const stopBtn = document.getElementById('stop-btn');
            
            if (cameraRunning) {
                startBtn.disabled = true;
                stopBtn.disabled = false;
                document.getElementById('status').innerHTML = '📡 Camera Online';
                document.getElementById('status').className = 'status online';
            } else {
                startBtn.disabled = false;
                stopBtn.disabled = true;
                document.getElementById('status').innerHTML = '⏹️ Camera Offline';
                document.getElementById('status').className = 'status offline';
            }
        }
        
        // Update camera info every 2 seconds
        setInterval(updateCameraInfo, 2000);
        
        // Initial update
        updateCameraInfo();
        updateButtonStates(true);
        log('🚀 Camera + SAM2 system ready');
    </script>
</body>
</html>
    """
    
    template_file = template_dir / "camera_sam2.html"
    with open(template_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ HTML template created: {template_file}")

def main():
    """Main function"""
    global camera_index
    
    print("🎥🎯 Jetson Orin Nano - Camera + SAM2 Integration")
    print("=" * 60)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        try:
            camera_index = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid camera index. Using default (0)")
    
    print(f"Using camera index: {camera_index}")
    
    # Create HTML template
    create_html_template()
    
    # Initialize camera
    if not init_camera():
        print("❌ Failed to initialize camera. Exiting...")
        return
    
    # Set streaming to true after successful initialization
    is_streaming = True
    print("✅ Camera initialized successfully")
    print("🌐 Starting web server...")
    print("=" * 60)
    print("📱 Access the camera + SAM2 at:")
    print("   • http://localhost:5000")
    print("   • http://127.0.0.1:5000")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start Flask app
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    finally:
        if camera:
            camera.release()
        print("✅ Camera released")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)





