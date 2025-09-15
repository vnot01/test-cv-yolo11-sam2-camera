#!/usr/bin/env python3
"""
Web-based Live Camera Feed for Jetson Orin Nano
Streams camera feed through web browser using Flask
"""

import cv2
import sys
import time
import threading
from flask import Flask, render_template, Response, jsonify
from pathlib import Path
import base64
import io
from PIL import Image

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

def init_camera():
    """Initialize camera"""
    global camera, camera_index, frame_width, frame_height, fps
    
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
    
    while is_streaming:
        if camera is None:
            break
            
        ret, frame = camera.read()
        
        if not ret:
            print("❌ Error: Cannot read frame from camera")
            break
        
        frame_count += 1
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        if ret:
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Control frame rate
        time.sleep(1.0 / fps)

@app.route('/')
def index():
    """Main page"""
    return render_template('camera.html')

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
    global camera, frame_count, start_time
    
    if camera is None:
        return jsonify({'error': 'Camera not initialized'})
    
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

@app.route('/capture')
def capture():
    """Capture current frame"""
    global camera
    
    if camera is None:
        return jsonify({'error': 'Camera not initialized'})
    
    ret, frame = camera.read()
    
    if not ret:
        return jsonify({'error': 'Cannot capture frame'})
    
    # Save image
    output_dir = Path("../storages/images/camera_captures")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"web_capture_{timestamp}.jpg"
    filepath = output_dir / filename
    
    cv2.imwrite(str(filepath), frame)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'path': str(filepath)
    })

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
    """Create HTML template for camera interface"""
    template_dir = Path("templates")
    template_dir.mkdir(exist_ok=True)
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jetson Orin Nano - Web Camera</title>
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Jetson Orin Nano - Web Camera</h1>
        
        <div class="status online" id="status">
            📡 Camera Online
        </div>
        
        <div class="camera-container">
            <img id="video-stream" src="{{ url_for('video_feed') }}" alt="Camera Feed">
        </div>
        
        <div class="controls">
            <button onclick="captureImage()">📸 Capture Image</button>
            <button onclick="refreshStream()">🔄 Refresh Stream</button>
            <button onclick="stopCamera()">⏹️ Stop Camera</button>
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
    </div>

    <script>
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
            fetch('/capture')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Image captured: ' + data.filename);
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error capturing image');
                });
        }
        
        function refreshStream() {
            const img = document.getElementById('video-stream');
            img.src = img.src + '?t=' + new Date().getTime();
        }
        
        function stopCamera() {
            fetch('/stop')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Camera stopped');
                        window.location.reload();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error stopping camera');
                });
        }
        
        // Update camera info every 2 seconds
        setInterval(updateCameraInfo, 2000);
        
        // Initial update
        updateCameraInfo();
    </script>
</body>
</html>
    """
    
    template_file = template_dir / "camera.html"
    with open(template_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ HTML template created: {template_file}")

def main():
    """Main function"""
    global camera_index
    
    print("🌐 Jetson Orin Nano - Web Camera Server")
    print("=" * 50)
    
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
    
    print("✅ Camera initialized successfully")
    print("🌐 Starting web server...")
    print("=" * 50)
    print("📱 Access the camera at:")
    print("   • http://localhost:5000")
    print("   • http://127.0.0.1:5000")
    print("=" * 50)
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
