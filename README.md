# Jetson Orin Nano - CV YOLO11 SAM2 Camera Integration

## Overview
Complete computer vision system for NVIDIA Jetson Orin Nano featuring YOLO11 object detection, SAM2 segmentation, and real-time camera integration with web-based interfaces.

## System Specifications
- **Device**: NVIDIA Jetson Orin Nano
- **OS**: Ubuntu 22.04 LTS (ARM64)
- **Kernel**: Linux 5.15.148-tegra
- **Python**: 3.10.12
- **Memory Configuration**: 8GB RAM + 19GB Swap (Total: 27GB)

## Prerequisites
- Jetson Orin Nano with Ubuntu 22.04
- Internet connection
- sudo privileges

## Installation Steps

### 1. System Update and Package Installation

```bash
# Update package lists
sudo apt update

# Install essential packages
sudo apt install python3-pip python3-venv -y
```

### 2. Memory Optimization - Swap Configuration

#### Current Memory Status
- **RAM**: 7.4GB total, 6.0GB available
- **Original Swap**: 3.7GB (zram compressed)
- **Target**: Add 16GB file swap

#### Create 16GB Swap File

```bash
# Create 16GB swap file
sudo fallocate -l 16G /swapfile

# Set proper permissions
sudo chmod 600 /swapfile

# Format as swap
sudo mkswap /swapfile

# Activate swap file
sudo swapon /swapfile
```

#### Make Swap Permanent

```bash
# Add to fstab for automatic mounting
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### Optimize for Jetson Orin Nano

```bash
# Optimize swappiness (lower = less aggressive swap usage)
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf

# Apply settings immediately
sudo sysctl vm.swappiness=10
sudo sysctl vm.vfs_cache_pressure=50
```

#### Verify Memory Configuration

```bash
# Check total memory
free -h

# Check active swap devices
swapon --show
```

**Expected Output:**
```
               total        used        free      shared  buff/cache   available
Mem:           7.4Gi       1.2Gi       3.1Gi        21Mi       3.1Gi       6.0Gi
Swap:           19Gi          0B        19Gi
```

### 3. Python Virtual Environment Setup

#### if New Create Virtual Environment

```bash
# Go to Directory
cd test-cv-yolo11-sam2-camera/

# Create virtual environment
python3 -m venv myenv

# Activate virtual environment
source myenv/bin/activate

# Verify activation
which python
python --version
pip --version
```

#### Virtual Environment Management

```bash
# Activate environment
source myenv/bin/activate

# Deactivate environment
deactivate

# Create requirements.txt
pip freeze > requirements.txt

# Install from requirements.txt
pip install -r requirements.txt
```

### 4. PyTorch Installation for Jetson Platform 6.1

#### Install PyTorch 2.5.0 and TorchVision 0.20.0

```bash
# Activate virtual environment first
source myenv/bin/activate

# Install PyTorch 2.5.0 for Jetson Platform 6.1
pip install https://github.com/ultralytics/assets/releases/download/v0.0.0/torch-2.5.0a0+872d972e41.nv24.08-cp310-cp310-linux_aarch64.whl

# Install TorchVision 0.20.0 for Jetson Platform 6.1
pip install https://github.com/ultralytics/assets/releases/download/v0.0.0/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl
```

#### Verify PyTorch Installation

```bash
# Test PyTorch installation
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"

# Test TorchVision
python -c "import torchvision; print(f'TorchVision version: {torchvision.__version__}')"
```

### 5. Ultralytics Installation

#### Install Ultralytics (Standard Version)

```bash
# Install ultralytics (without export dependencies)
pip install ultralytics
```

#### Download YOLO11 Models

```bash
# Download YOLO11 nano model (fastest)
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt

# Download YOLO11 small model (balanced)
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt

# Download custom trained model
wget https://github.com/vnot01/MySuperApps/releases/download/trained-models/best.pt
```

#### Verify Ultralytics Installation

```bash
# Test ultralytics installation
python -c "import ultralytics; print(f'Ultralytics version: {ultralytics.__version__}')"

# Quick YOLO test
python -c "from ultralytics import YOLO; print('YOLO import successful')"

# Test YOLO11 model loading
python -c "from ultralytics import YOLO; model = YOLO('yolo11n.pt'); print('YOLO11 model loaded successfully')"
```

## System Verification

### Memory Verification

```bash
# Check total available memory
free -h

# Check swap usage
cat /proc/meminfo | grep -i swap

# Monitor memory usage in real-time
htop
```

### GPU Verification

```bash
# Check NVIDIA GPU status
nvidia-smi

# Check CUDA availability in PyTorch
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU count:', torch.cuda.device_count())"
```

### Performance Testing

```bash
# Test PyTorch performance
python -c "
import torch
import time

# Create test tensor
x = torch.randn(1000, 1000)
if torch.cuda.is_available():
    x = x.cuda()
    print('GPU tensor operations available')
else:
    print('CPU tensor operations only')

# Simple performance test
start = time.time()
for i in range(100):
    y = torch.mm(x, x)
end = time.time()
print(f'Matrix multiplication time: {end-start:.4f} seconds')
"
```

## Troubleshooting

### Common Issues

#### 1. Swap Not Activating on Boot
```bash
# Check fstab entry
cat /etc/fstab | grep swap

# Manually activate if needed
sudo swapon /swapfile
```

#### 2. PyTorch CUDA Not Available
```bash
# Check NVIDIA driver
nvidia-smi

# Reinstall PyTorch with correct version
pip uninstall torch torchvision
pip install https://github.com/ultralytics/assets/releases/download/v0.0.0/torch-2.5.0a0+872d972e41.nv24.08-cp310-cp310-linux_aarch64.whl
```

#### 3. libcusparseLt.so.0 Error
If you encounter this error:
```
ImportError: libcusparseLt.so.0: cannot open shared object file: No such file or directory
```

**Solution:**

1. **Check CUDA library directory:**
```bash
ls /usr/local/cuda/lib64
```

2. **Download and install libcusparseLt library:**
```bash
# Download the library for ARM64 (linux-sbsa)
wget https://developer.download.nvidia.com/compute/cusparselt/redist/libcusparse_lt/linux-sbsa/libcusparse_lt-linux-sbsa-0.5.2.1-archive.tar.xz

# Extract the archive
tar xf libcusparse_lt-linux-sbsa-0.5.2.1-archive.tar.xz

# Copy libraries to CUDA directory
sudo cp -a libcusparse_lt-linux-sbsa-0.5.2.1-archive/lib/* /usr/local/cuda/lib64/

# Copy headers to CUDA include directory
sudo cp -a libcusparse_lt-linux-sbsa-0.5.2.1-archive/include/* /usr/local/cuda/include/
```

3. **Update LD_LIBRARY_PATH:**
```bash
# Add to ~/.bashrc for permanent solution
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Or set temporarily
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

4. **Test PyTorch CUDA:**
```bash
python3 -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
```

#### 4. Memory Issues
```bash
# Check swap usage
swapon --show

# Monitor memory usage
watch -n 1 free -h
```

### Performance Optimization

#### 1. Increase GPU Memory
```bash
# Set GPU memory fraction (if needed)
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

#### 2. Optimize for AI Workloads
```bash
# Set optimal number of threads
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
```
----
## 📁 **Project Structure**
```
test-cv-yolo11-sam2-camera/
├── 📁 camera/                       # Camera functionality scripts
│   ├── camera_test.py              # Camera testing and detection
│   ├── camera_yolo_inference.py    # Real-time YOLO detection
│   ├── live_camera.py              # Web-based live camera feed
│   ├── web_camera.py               # Advanced web camera interface
│   ├── camera_resolution_test.py   # Camera resolution testing
│   ├── templates/                  # HTML templates
│   │   └── camera.html             # Camera web interface
│   └── README.md                   # Camera documentation
├── 📁 cv-camera/                   # Camera + AI integration
│   ├── camera_yolo_integration.py  # Camera + YOLO web interface
│   ├── camera_yolo_inference.py    # YOLO inference for camera
│   ├── camera_sam2_integration.py  # Camera + SAM2 web interface
│   ├── camera_sam2_inference.py    # SAM2 inference for camera
│   ├── templates/                  # HTML templates
│   │   ├── camera_yolo.html        # YOLO web interface
│   │   └── camera_sam2.html        # SAM2 web interface
│   └── README.md                   # Integration documentation
├── 📁 test/                        # AI inference scripts
│   ├── simple_yolo11_inference.py  # Single image YOLO inference
│   ├── batch_yolo11_inference.py   # Batch YOLO processing
│   ├── simple_sam2_inference.py    # SAM2 segmentation script
│   └── requirements.txt            # Test-specific dependencies
├── 📁 models/                      # AI model files (auto-downloaded)
│   ├── best.pt                     # Custom trained YOLO model
│   ├── yolo11n.pt                  # YOLO11 nano model
│   ├── sam2.1_b.pt                 # SAM2.1 base model
│   └── sam2_b.pt                   # SAM2 base model
├── 📁 storages/                    # Data storage
│   └── images/
│       ├── input/                  # Input images
│       │   ├── 55_mineral_filled.jpg
│       │   └── camera_capture.jpg
│       ├── camera_captures/        # Camera captured images
│       └── output/                 # AI processing results
│           ├── camera_yolo/        # YOLO detection results
│           │   └── results/
│           │       ├── inference/  # Inference logs
│           │       └── images/     # Detection images
│           ├── camera_sam2/        # SAM2 segmentation results
│           │   └── results/
│           │       ├── inference/  # Inference logs
│           │       └── images/     # Segmentation images
│           ├── yolo11/             # YOLO11 test results
│           └── sam2/               # SAM2 test results
├── 📁 myenv/                       # Python virtual environment
│   ├── bin/                        # Executable scripts
│   ├── lib/                        # Python packages
│   └── pyvenv.cfg                  # Environment configuration
├── 📁 docs/                        # Documentation
│   └── 1.md                        # PyTorch installation guide
├── download_yolo11n.py             # Model download script
├── requirements.txt                # Main Python dependencies
├── requirements.backups            # Backup requirements files
├── .gitignore                      # Git ignore rules
└── README.md                       # This documentation
```

### 🎯 **Keuntungan Struktur Baru**

#### **1. Separation of Concerns**
- **GitHub Integration** terpisah dari project - bisa digunakan untuk project lain
- **Project test-cv-yolo11-sam2-camera** bersih tanpa dokumentasi GitHub
- **Models dan storages** bisa di-share antar project

#### **2. Reusability**
- **GitHub Integration** bisa digunakan untuk project baru
- **Scripts setup** bisa di-reuse untuk project lain
- **Documentation** terpusat dan mudah di-maintain

#### **3. Organization**
- **Clear separation** antara tools dan project
- **Modular structure** untuk maintainability
- **Easy navigation** dengan struktur yang jelas

#### **4. Scalability**
- **Easy to add** project baru
- **Consistent structure** across projects
- **Centralized tools** untuk semua project

### 📋 **File Organization Benefits**

| Component | Location | Purpose | Reusability |
|-----------|----------|---------|-------------|
| **GitHub Integration** | `/home/my/Github Integration/` | Tools & documentation | ✅ All projects |
| **Main Project** | `/home/my/test-cv-yolo11-sam2-camera/` | CV system | ❌ Project specific |
| **Shared Models** | `/home/my/models/` | AI models | ✅ All projects |
| **Shared Storage** | `/home/my/storages/` | Data storage | ✅ All projects |

## System Information

### Memory Configuration
- **Total RAM**: 7.4GB
- **Available RAM**: 6.0GB
- **zram Swap**: 3.7GB (compressed)
- **File Swap**: 16GB
- **Total Memory**: 27GB

### Software Versions
- **Python**: 3.10.12
- **pip**: 22.0.2
- **PyTorch**: 2.5.0a0+872d972e41.nv24.08
- **TorchVision**: 0.20.0a0+afc54f7
- **Ultralytics**: Latest stable

### Kernel Parameters
- **vm.swappiness**: 10
- **vm.vfs_cache_pressure**: 50

## 🚀 Quick Start Guide

### 1. Setup Environment

```bash
# Clone or navigate to project directory
cd test-cv-yolo11-sam2-camera

# Activate virtual environment
source myenv/bin/activate

# Install dependencies (if not already installed)
source myenv/bin/activate

# Install PyTorch 2.5.0 for Jetson Platform 6.1
pip install https://github.com/ultralytics/assets/releases/download/v0.0.0/torch-2.5.0a0+872d972e41.nv24.08-cp310-cp310-linux_aarch64.whl

# Install TorchVision 0.20.0 for Jetson Platform 6.1
pip install https://github.com/ultralytics/assets/releases/download/v0.0.0/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl

pip install ultralytics==8.3.199

pip install numpy==1.26.4 # (Optional)

pip install -r requirements.txt # (Optional)
```

### 2. Test Camera

```bash
# Test camera functionality
cd camera
python3 camera_test.py

# Start web-based live camera
python3 live_camera.py
# Access at: http://localhost:5000
```

### 3. Run AI Inference

```bash
# Test YOLO inference
cd test
python3 simple_yolo11_inference.py

# Test SAM2 segmentation
python3 simple_sam2_inference.py

# Batch processing
python3 batch_yolo11_inference.py
```

### 4. Camera + AI Integration

```bash
# Install Flask for Web
pip install flask

# Camera + YOLO integration
cd cv-camera
python3 camera_yolo_integration.py
# Access at: http://localhost:5000

# Camera + SAM2 integration
python3 camera_sam2_integration.py
# Access at: http://localhost:5000
```

## 🎯 Main Features

### 🎥 Camera System
- **Web-based Interface** - Access camera from any browser
- **Real-time Streaming** - Live camera feed with MJPEG
- **TTY Compatible** - Works without GUI display
- **Multi-camera Support** - Support for multiple USB cameras
- **Resolution Testing** - Test different camera resolutions
- **Start/Stop Controls** - Remote camera control via web
- **Frame Capture** - Save individual frames
- **Performance Monitoring** - FPS, frame count, uptime tracking

### 🤖 AI Integration
- **YOLO11 Object Detection** - Real-time object detection
- **SAM2 Segmentation** - Advanced image segmentation
- **Auto Model Download** - Automatically downloads missing models
- **Background Processing** - AI inference doesn't block camera
- **Web Controls** - Control AI processing via web interface
- **Multiple Models** - Support for various YOLO and SAM2 models
- **Custom Models** - Use your own trained models
- **Batch Processing** - Process multiple images at once

### 📊 Output Management
- **Organized Storage** - Structured output folders
- **Timestamped Results** - All results include timestamps
- **Multiple Formats** - Images, logs, and detection data
- **Real-time Logging** - Activity logs for monitoring
- **Result Tracking** - Easy access to all processing results
- **Data Export** - Export detection data and statistics

### 🌐 Web Interface Features
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Real-time Updates** - Live camera feed and statistics
- **Interactive Controls** - Easy-to-use buttons and controls
- **Activity Logging** - Monitor all system activities
- **Network Access** - Access from any device on the network
- **No GUI Required** - Perfect for headless systems

## 📋 Detailed Feature List

### Camera Scripts (`camera/` folder)
1. **camera_test.py** - Camera detection and testing
2. **live_camera.py** - Web-based live camera feed
3. **web_camera.py** - Advanced web camera interface
4. **camera_yolo_inference.py** - Real-time YOLO detection
5. **camera_resolution_test.py** - Camera resolution testing

### AI Integration Scripts (`cv-camera/` folder)
1. **camera_yolo_integration.py** - Camera + YOLO web interface
2. **camera_yolo_inference.py** - YOLO inference for camera
3. **camera_sam2_integration.py** - Camera + SAM2 web interface
4. **camera_sam2_inference.py** - SAM2 inference for camera

### Test Scripts (`test/` folder)
1. **simple_yolo11_inference.py** - Single image YOLO inference
2. **batch_yolo11_inference.py** - Batch YOLO processing
3. **simple_sam2_inference.py** - SAM2 segmentation script

### Model Management
- **Auto Download** - Automatically downloads missing models
- **Model Validation** - Checks model integrity after download
- **Progress Tracking** - Shows download progress
- **Multiple Sources** - Downloads from official repositories

## 📖 Usage Examples

### Basic YOLO Inference

#### Using YOLO11 Pre-trained Models

```python
from ultralytics import YOLO
import datetime

# Load YOLO11 nano model (faster, less accurate)
model = YOLO('models/yolo11n.pt')

# Or load custom trained model
# model = YOLO('models/best.pt')

# Run inference on sample image
results = model('storages/images/input/55_mineral_filled.jpg')

# Save results to output folder
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f'storages/images/output/yolo11n_detection_{timestamp}.jpg'
results[0].save(output_path)
print(f"Results saved to: {output_path}")

# Print detection results
for result in results:
    boxes = result.boxes
    for box in boxes:
        print(f"Class: {box.cls}, Confidence: {box.conf}, Bbox: {box.xyxy}")
```

#### Using Custom Trained Model

```python
#!/usr/bin/env python3
"""
Simple YOLO inference script for testing
Saves results to storages/images/output folder
Automatically downloads models if not found
"""

from ultralytics import YOLO
import datetime
import os
import sys
import subprocess
from pathlib import Path

def check_and_download_models():
    """Check if models exist, download if not"""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    models_to_check = ["best.pt", "yolo11n.pt"]
    missing_models = []
    
    for model in models_to_check:
        model_path = models_dir / model
        if not model_path.exists():
            missing_models.append(model)
    
    if missing_models:
        print(f"⚠️  Model tidak ditemukan: {', '.join(missing_models)}")
        print("📥 Memulai download model...")
        
        try:
            # Jalankan script download
            download_script = Path("download_yolo11n.py")
            if download_script.exists():
                result = subprocess.run([sys.executable, str(download_script)], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Model berhasil didownload")
                else:
                    print(f"❌ Error downloading models: {result.stderr}")
                    return False
            else:
                print("❌ Script download tidak ditemukan")
                return False
        except Exception as e:
            print(f"❌ Error running download script: {e}")
            return False
    
    return True

def main():
    # Configuration
    MODEL_PATH = "models/best.pt"  # Change to your model path
    INPUT_IMAGE = "storages/images/input/55_mineral_filled.jpg"
    OUTPUT_FOLDER = "storages/images/output"
    
    # Check and download models if needed
    if not check_and_download_models():
        print("❌ Gagal mendownload model. Keluar dari program.")
        return
    
    # Create output folder if it doesn't exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Check if model file exists
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model tidak ditemukan: {MODEL_PATH}")
        return
    
    print("Loading model...")
    model = YOLO(MODEL_PATH)
    
    print(f"Running inference on: {INPUT_IMAGE}")
    results = model(INPUT_IMAGE)
    
    # Generate output filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"detection_{timestamp}.jpg"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    
    # Save results
    results[0].save(output_path)
    print(f"Results saved to: {output_path}")
    
    # Print detection summary
    if results[0].boxes is not None:
        num_detections = len(results[0].boxes)
        print(f"Found {num_detections} objects")
        
        # Print details for each detection
        for i, box in enumerate(results[0].boxes):
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            print(f"  Object {i+1}: Class {cls}, Confidence {conf:.2f}")
    else:
        print("No objects detected")
    
    print("Inference completed!")

if __name__ == "__main__":
    main()
```


#### Available Models

- **YOLO11 Nano**: [yolo11n.pt](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt) - Fastest, smallest model
- **YOLO11 Small**: [yolo11s.pt](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt) - Balanced speed and accuracy
- **Custom Trained**: [best.pt](https://github.com/vnot01/MySuperApps/releases/download/trained-models/best.pt) - Your trained model

### Batch Processing Multiple Images

```python
from ultralytics import YOLO
import os
import datetime
import sys
import subprocess
from pathlib import Path

def check_and_download_models():
    """Check if models exist, download if not"""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    models_to_check = ["best.pt", "yolo11n.pt"]
    missing_models = []
    
    for model in models_to_check:
        model_path = models_dir / model
        if not model_path.exists():
            missing_models.append(model)
    
    if missing_models:
        print(f"⚠️  Model tidak ditemukan: {', '.join(missing_models)}")
        print("📥 Memulai download model...")
        
        try:
            # Jalankan script download
            download_script = Path("download_yolo11n.py")
            if download_script.exists():
                result = subprocess.run([sys.executable, str(download_script)], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Model berhasil didownload")
                else:
                    print(f"❌ Error downloading models: {result.stderr}")
                    return False
            else:
                print("❌ Script download tidak ditemukan")
                return False
        except Exception as e:
            print(f"❌ Error running download script: {e}")
            return False
    
    return True

def batch_inference(model_path, input_folder, output_folder):
    """Run batch inference on all images in input folder"""
    
    # Load model
    model = YOLO(model_path)
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all image files from input folder
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    input_path = Path(input_folder)
    
    if not input_path.exists():
        print(f"Input folder {input_folder} does not exist!")
        return
    
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_path.glob(f'*{ext}'))
        image_files.extend(input_path.glob(f'*{ext.upper()}'))
    
    if not image_files:
        print(f"No image files found in {input_folder}")
        return
    
    print(f"Found {len(image_files)} images to process...")
    
    # Process each image
    for i, image_file in enumerate(image_files, 1):
        print(f"Processing {i}/{len(image_files)}: {image_file.name}")
        
        try:
            # Run inference
            results = model(str(image_file))
            
            # Generate output filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{image_file.stem}_detected_{timestamp}.jpg"
            output_path = os.path.join(output_folder, output_filename)
            
            # Save results
            results[0].save(output_path)
            print(f"  ✓ Saved to: {output_path}")
            
            # Print detection info
            if results[0].boxes is not None:
                num_detections = len(results[0].boxes)
                print(f"  ✓ Found {num_detections} objects")
            else:
                print(f"  ✓ No objects detected")
                
        except Exception as e:
            print(f"  ✗ Error processing {image_file.name}: {str(e)}")
    
    print(f"\nBatch processing completed! Results saved to: {output_folder}")

if __name__ == "__main__":
    # Configuration
    MODEL_PATH = "models/best.pt"  # or "yolo11n.pt", "yolo11s.pt"
    INPUT_FOLDER = "storages/images/input"
    OUTPUT_FOLDER = "storages/images/output"
    
    # Check and download models if needed
    if not check_and_download_models():
        print("❌ Gagal mendownload model. Keluar dari program.")
        sys.exit(1)
    
    # Check if model file exists
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model tidak ditemukan: {MODEL_PATH}")
        sys.exit(1)
    
    # Run batch inference
    batch_inference(MODEL_PATH, INPUT_FOLDER, OUTPUT_FOLDER)
```


### SAM2 Segmentation

```python
from ultralytics import YOLO, SAM
import datetime

# Load YOLO model for object detection
yolo_model = YOLO('models/best.pt')

# Load SAM2 model for segmentation
sam2_model = SAM('models/sam2.1_b.pt')

# Run YOLO detection first
image_path = 'storages/images/input/55_mineral_filled.jpg'
yolo_results = yolo_model(image_path)

# Extract bounding boxes from YOLO results
bboxes = yolo_results[0].boxes.xyxy if yolo_results[0].boxes is not None else []

# Run SAM2 segmentation
sam2_results = sam2_model(image_path, bboxes=bboxes)

# Save results
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f'storages/images/output/sam2_segmentation_{timestamp}.jpg'
sam2_results[0].save(output_path)
print(f"SAM2 results saved to: {output_path}")
```

### Web-based Camera + AI Integration

#### Camera + YOLO Integration
```bash
# Start camera + YOLO web interface
cd cv-camera
python3 camera_yolo_integration.py

# Access web interface
# Local: http://localhost:5000
# Network: http://192.168.1.11:5000
```

**Web Interface Features:**
- 📸 **Capture Image** - Save current frame
- 🤖 **Capture + YOLO** - Capture and run YOLO detection
- 🔄 **Refresh Stream** - Restart video stream
- ▶️ **Start Camera** - Start camera streaming
- ⏹️ **Stop Camera** - Stop camera streaming

#### Camera + SAM2 Integration
```bash
# Start camera + SAM2 web interface
cd cv-camera
python3 camera_sam2_integration.py

# Access web interface
# Local: http://localhost:5000
# Network: http://192.168.1.11:5000
```

**Web Interface Features:**
- 📸 **Capture Image** - Save current frame
- 🎯 **Capture + SAM2** - Capture and run SAM2 segmentation
- 🔄 **Refresh Stream** - Restart video stream
- ▶️ **Start Camera** - Start camera streaming
- ⏹️ **Stop Camera** - Stop camera streaming

### Training Custom Model
```python
from ultralytics import YOLO

# Load YOLO11 model for training
model = YOLO('models/yolo11n.pt')

# Train model
results = model.train(
    data='path/to/dataset.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0  # Use GPU if available
)

# Save trained model
model.save('models/best.pt')
```

## Maintenance

### Regular Maintenance Tasks

#### 1. Update Packages
```bash
# Activate environment
source myenv/bin/activate

# Update pip
pip install --upgrade pip

# Update ultralytics
pip install --upgrade ultralytics
```

#### 2. Monitor System Resources
```bash
# Check memory usage
free -h

# Check disk usage
df -h

# Check GPU usage
nvidia-smi
```

#### 3. Clean Up
```bash
# Remove old pip cache
pip cache purge

# Clean system packages
sudo apt autoremove
sudo apt autoclean
```

## 🔧 Troubleshooting

### Common Issues

#### Camera Not Detected
```bash
# Check USB devices
lsusb

# Check video devices
ls /dev/video*

# Check camera permissions
sudo chmod 666 /dev/video0
```

#### Model Download Issues
```bash
# Check internet connection
ping google.com

# Manually download models
cd models
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt
wget https://github.com/vnot01/MySuperApps/releases/download/trained-models/best.pt
```

#### Web Interface Not Loading
```bash
# Check if port 5000 is in use
sudo netstat -tlnp | grep :5000

# Kill existing processes
pkill -f camera_yolo_integration.py
pkill -f camera_sam2_integration.py

# Restart service
cd cv-camera
python3 camera_yolo_integration.py
```

#### Low Performance
1. **Reduce camera resolution** - Modify scripts to use 320x240
2. **Use lighter models** - Use yolo11n.pt instead of best.pt
3. **Close other applications** - Free up system resources
4. **Check GPU usage** - `nvidia-smi`

### Performance Optimization

#### For Better Speed
```bash
# Set optimal environment variables
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

#### For Better Quality
1. **Use higher resolution models** - best.pt for accuracy
2. **Ensure good lighting** - Better lighting = better detection
3. **Stable camera mount** - Reduce motion blur
4. **Higher camera resolution** - 1280x720 or higher

## 📚 Available Models

### YOLO Models
- **yolo11n.pt** - Nano model (fastest, smallest)
- **yolo11s.pt** - Small model (balanced)
- **yolo11m.pt** - Medium model (good accuracy)
- **yolo11l.pt** - Large model (high accuracy)
- **yolo11x.pt** - Extra large model (highest accuracy)
- **best.pt** - Custom trained model

### SAM2 Models
- **sam2.1_b.pt** - SAM2.1 base model (recommended)
- **sam2_b.pt** - SAM2 base model
- **sam2.1_l.pt** - SAM2.1 large model
- **sam2_l.pt** - SAM2 large model

## 🔗 Integration Features

### Auto Model Download
- Automatically downloads missing YOLO and SAM2 models
- Progress tracking during download
- Model validation after download
- Support for custom model URLs

### Web-based Control
- Remote camera control via web browser
- Real-time streaming with MJPEG
- Background AI processing
- Activity logging and monitoring
- Multi-device access

### Organized Output
- Timestamped results
- Structured folder organization
- Multiple output formats (images, logs, data)
- Easy result management
- Automatic folder creation

## 🔄 Workflow Examples

### 1. Basic Camera Testing
```bash
# Test camera functionality
cd camera
python3 camera_test.py

# Start live camera feed
python3 live_camera.py
# Access at: http://localhost:5000
```

### 2. YOLO Object Detection
```bash
# Test YOLO on single image
cd test
python3 simple_yolo11_inference.py

# Batch process multiple images
python3 batch_yolo11_inference.py

# Real-time camera + YOLO
cd cv-camera
python3 camera_yolo_integration.py
```

### 3. SAM2 Segmentation
```bash
# Test SAM2 on single image
cd test
python3 simple_sam2_inference.py

# Real-time camera + SAM2
cd cv-camera
python3 camera_sam2_integration.py
```

### 4. Production Workflow
```bash
# 1. Test camera
cd camera && python3 camera_test.py

# 2. Start camera + AI integration
cd cv-camera && python3 camera_yolo_integration.py

# 3. Access web interface
# http://localhost:5000

# 4. Monitor results
ls -la storages/images/output/camera_yolo/results/
```

## 🎯 Best Practices

### Performance Optimization
1. **Use appropriate models** - yolo11n.pt for speed, best.pt for accuracy
2. **Optimize camera settings** - Lower resolution for better performance
3. **Monitor system resources** - Use `htop` and `nvidia-smi`
4. **Close unnecessary applications** - Free up RAM and GPU memory

### Quality Improvement
1. **Good lighting** - Ensure adequate lighting for better detection
2. **Stable camera** - Use tripod or stable mount
3. **Higher resolution** - Use higher resolution models for accuracy
4. **Regular model updates** - Keep models up to date

### System Maintenance
1. **Regular cleanup** - Remove old result files
2. **Monitor disk space** - Results can accumulate quickly
3. **Update dependencies** - Keep packages up to date
4. **Backup models** - Keep copies of custom trained models

### Security Considerations
1. **Network access** - Web interfaces are accessible on network
2. **Firewall settings** - Configure firewall if needed
3. **User permissions** - Ensure proper file permissions
4. **Regular updates** - Keep system and packages updated

## 📊 System Requirements

### Minimum Requirements
- **RAM**: 4GB (8GB recommended)
- **Storage**: 10GB free space
- **Camera**: USB webcam
- **Network**: For model downloads

### Recommended Setup
- **RAM**: 8GB+ with 16GB swap
- **Storage**: 20GB+ free space
- **Camera**: 1080p USB webcam
- **Network**: Stable internet connection

## 🆘 Support and Resources

### Official Documentation
- [NVIDIA Jetson Documentation](https://docs.nvidia.com/jetson/)
- [PyTorch for Jetson](https://pytorch.org/get-started/locally/)
- [Ultralytics Documentation](https://docs.ultralytics.com/)
- [OpenCV Documentation](https://docs.opencv.org/)

### Community Resources
- [NVIDIA Developer Forums](https://forums.developer.nvidia.com/)
- [JetsonHacks](https://jetsonhacks.com/)
- [Ultralytics GitHub](https://github.com/ultralytics/ultralytics)
- [OpenCV GitHub](https://github.com/opencv/opencv)

### Project Structure
- **camera/** - Basic camera functionality
- **cv-camera/** - Camera + AI integration
- **test/** - AI inference scripts
- **models/** - AI model files
- **storages/** - Data storage and results

## 📄 License
This project is provided as-is for educational and development purposes.

---

**Last Updated**: September 2024  
**Tested On**: NVIDIA Jetson Orin Nano with Ubuntu 22.04 LTS  
**Jetson Platform**: 6.1
**Python Version**: 3.10.12  
**PyTorch Version**: 2.5.0a0+872d972e41.nv24.08  
**Ultralytics Version**: 8.3.199
