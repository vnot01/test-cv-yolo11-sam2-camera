#!/bin/bash
# MyRVM Integration Test Runner Script
# Run this script to test the MyRVM integration and compatibility

echo "🚀 MyRVM Integration Test Runner"
echo "================================"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please activate your virtual environment first:"
    echo "  source venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment: $VIRTUAL_ENV"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ Python version: $python_version"

# Check if we're in the right directory
if [[ ! -f "main_application.py" ]]; then
    echo "❌ Please run this script from the myrvm-integration directory"
    exit 1
fi

echo "✅ Running from correct directory"

# Create logs directory if it doesn't exist
mkdir -p logs

# Create models directory if it doesn't exist
mkdir -p models

# Function to check and install dependencies
check_and_install_dependencies() {
    echo "🔍 Checking dependencies..."
    
    # Check if requirements.txt exists
    if [[ -f "requirements.txt" ]]; then
        echo "📦 Installing dependencies from requirements.txt..."
        pip install -r requirements.txt 2>&1 | tee logs/dependency_install.log
        
        if [[ $? -eq 0 ]]; then
            echo "✅ Dependencies installed successfully"
        else
            echo "❌ Failed to install some dependencies"
            echo "Check logs/dependency_install.log for details"
        fi
    else
        echo "⚠️  requirements.txt not found, installing basic dependencies..."
        
        # Install basic dependencies
        pip install torch torchvision opencv-python numpy requests psutil flask 2>&1 | tee logs/dependency_install.log
        
        if [[ $? -eq 0 ]]; then
            echo "✅ Basic dependencies installed successfully"
        else
            echo "❌ Failed to install basic dependencies"
            echo "Check logs/dependency_install.log for details"
        fi
    fi
}

# Check and install dependencies
check_and_install_dependencies

echo ""
echo "🧪 Running Compatibility Tests..."
echo "================================="

# Test PyTorch installation
echo "Testing PyTorch installation..."
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
" 2>&1 | tee logs/pytorch_test.log

# Check if PyTorch test failed and try to install
if [[ $? -ne 0 ]]; then
    echo "❌ PyTorch test failed, attempting to install..."
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 2>&1 | tee logs/pytorch_install.log
    echo "🔄 Retesting PyTorch..."
    python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
" 2>&1 | tee logs/pytorch_test_retry.log
fi

# Validate PyTorch version and CUDA for Jetson Platform
echo "🔍 Validating PyTorch for Jetson Platform..."
pytorch_version=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null)
cuda_available=$(python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null)
cuda_version=$(python3 -c "import torch; print(torch.version.cuda)" 2>/dev/null)

echo "Current PyTorch version: $pytorch_version"
echo "Current CUDA available: $cuda_available"
echo "Current CUDA version: $cuda_version"

# Check if PyTorch version is correct for Jetson (should be 2.5.0a0+872d972e41.nv24.08)
if [[ "$pytorch_version" != "2.5.0a0+872d972e41.nv24.08" ]] || [[ "$cuda_available" != "True" ]]; then
    echo "❌ PyTorch version or CUDA not correct for Jetson Platform"
    echo "Expected: PyTorch 2.5.0a0+872d972e41.nv24.08 with CUDA=True"
    echo "Installing correct PyTorch for Jetson Platform 6.1..."
    
    # Install PyTorch 2.5.0 for Jetson Platform 6.1
    pip install https://github.com/ultralytics/assets/releases/download/v0.0.0/torch-2.5.0a0+872d972e41.nv24.08-cp310-cp310-linux_aarch64.whl 2>&1 | tee logs/pytorch_jetson_install.log
    
    echo "🔄 Retesting PyTorch after Jetson installation..."
    python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
" 2>&1 | tee logs/pytorch_jetson_test.log
else
    echo "✅ PyTorch version and CUDA are correct for Jetson Platform"
fi

# Test TorchVision
echo "Testing TorchVision..."
python3 -c "
import torchvision
print(f'TorchVision version: {torchvision.__version__}')
" 2>&1 | tee logs/torchvision_test.log

# Check if TorchVision test failed and try to install
if [[ $? -ne 0 ]]; then
    echo "❌ TorchVision test failed, attempting to install..."
    pip install torchvision 2>&1 | tee logs/torchvision_install.log
    echo "🔄 Retesting TorchVision..."
    python3 -c "
import torchvision
print(f'TorchVision version: {torchvision.__version__}')
" 2>&1 | tee logs/torchvision_test_retry.log
fi

# Validate TorchVision version for Jetson Platform
echo "🔍 Validating TorchVision for Jetson Platform..."
torchvision_version=$(python3 -c "import torchvision; print(torchvision.__version__)" 2>/dev/null)

echo "Current TorchVision version: $torchvision_version"

# Check if TorchVision version is correct for Jetson (should be 0.20.0a0+afc54f7)
if [[ "$torchvision_version" != "0.20.0a0+afc54f7" ]]; then
    echo "❌ TorchVision version not correct for Jetson Platform"
    echo "Expected: TorchVision 0.20.0a0+afc54f7"
    echo "Installing correct TorchVision for Jetson Platform 6.1..."
    
    # Install TorchVision 0.20.0 for Jetson Platform 6.1
    pip install https://github.com/ultralytics/assets/releases/download/v0.0.0/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl 2>&1 | tee logs/torchvision_jetson_install.log
    
    echo "🔄 Retesting TorchVision after Jetson installation..."
    python3 -c "
import torchvision
print(f'TorchVision version: {torchvision.__version__}')
" 2>&1 | tee logs/torchvision_jetson_test.log
else
    echo "✅ TorchVision version is correct for Jetson Platform"
fi

# Test OpenCV
echo "Testing OpenCV..."
python3 -c "
import cv2
print(f'OpenCV version: {cv2.__version__}')
" 2>&1 | tee logs/opencv_test.log

# Check if OpenCV test failed and try to install
if [[ $? -ne 0 ]]; then
    echo "❌ OpenCV test failed, attempting to install..."
    pip install opencv-python 2>&1 | tee logs/opencv_install.log
    echo "🔄 Retesting OpenCV..."
    python3 -c "
import cv2
print(f'OpenCV version: {cv2.__version__}')
" 2>&1 | tee logs/opencv_test_retry.log
fi

# Test NumPy
echo "Testing NumPy..."
python3 -c "
import numpy as np
print(f'NumPy version: {np.__version__}')
" 2>&1 | tee logs/numpy_test.log

# Check if NumPy test failed and try to install
if [[ $? -ne 0 ]]; then
    echo "❌ NumPy test failed, attempting to install..."
    pip install numpy 2>&1 | tee logs/numpy_install.log
    echo "🔄 Retesting NumPy..."
    python3 -c "
import numpy as np
print(f'NumPy version: {np.__version__}')
" 2>&1 | tee logs/numpy_test_retry.log
fi

# Comprehensive compatibility test
echo "Running comprehensive compatibility test..."
python3 -c "
import torch
import torchvision
import cv2
import numpy as np

print('=== COMPATIBILITY TEST ===')
print(f'NumPy version: {np.__version__}')
print(f'PyTorch version: {torch.__version__}')
print(f'TorchVision version: {torchvision.__version__}')
print(f'OpenCV version: {cv2.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
print('=== ALL MODULES LOADED SUCCESSFULLY ===')
" 2>&1 | tee logs/compatibility_test.log

# Check CUDA availability
cuda_available=$(python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null)
if [[ "$cuda_available" == "True" ]]; then
    echo "✅ CUDA is available and working"
else
    echo "❌ CUDA is not available"
    echo "⚠️  Please check your CUDA installation"
fi

# Check if models directory exists and create if needed
if [[ ! -d "models" ]]; then
    echo "📁 Creating models directory..."
    mkdir -p models
    echo "✅ Models directory created"
else
    echo "✅ Models directory exists"
fi

# Check if logs directory exists and create if needed
if [[ ! -d "logs" ]]; then
    echo "📁 Creating logs directory..."
    mkdir -p logs
    echo "✅ Logs directory created"
else
    echo "✅ Logs directory exists"
fi

echo ""
echo "📊 Test Results Summary:"
echo "========================"
echo "✅ Dependency installation: logs/dependency_install.log"
echo "✅ PyTorch test: logs/pytorch_test.log"
echo "✅ TorchVision test: logs/torchvision_test.log"
echo "✅ OpenCV test: logs/opencv_test.log"
echo "✅ NumPy test: logs/numpy_test.log"
echo "✅ Compatibility test: logs/compatibility_test.log"

# Check for retry logs
if [[ -f "logs/pytorch_test_retry.log" ]]; then
    echo "🔄 PyTorch retry test: logs/pytorch_test_retry.log"
fi
if [[ -f "logs/torchvision_test_retry.log" ]]; then
    echo "🔄 TorchVision retry test: logs/torchvision_test_retry.log"
fi
if [[ -f "logs/opencv_test_retry.log" ]]; then
    echo "🔄 OpenCV retry test: logs/opencv_test_retry.log"
fi
if [[ -f "logs/numpy_test_retry.log" ]]; then
    echo "🔄 NumPy retry test: logs/numpy_test_retry.log"
fi

# Check for Jetson-specific installation logs
if [[ -f "logs/pytorch_jetson_install.log" ]]; then
    echo "🚀 PyTorch Jetson installation: logs/pytorch_jetson_install.log"
fi
if [[ -f "logs/pytorch_jetson_test.log" ]]; then
    echo "🚀 PyTorch Jetson test: logs/pytorch_jetson_test.log"
fi
if [[ -f "logs/torchvision_jetson_install.log" ]]; then
    echo "🚀 TorchVision Jetson installation: logs/torchvision_jetson_install.log"
fi
if [[ -f "logs/torchvision_jetson_test.log" ]]; then
    echo "🚀 TorchVision Jetson test: logs/torchvision_jetson_test.log"
fi

echo ""
echo "🚀 Next Steps:"
echo "=============="
echo "1. Review test results in logs/"
echo "2. If any dependencies were auto-installed, check installation logs"
echo "3. If Jetson-specific PyTorch/TorchVision were installed, check Jetson logs"
echo "4. For models: Use autodownload and move to models/ folder"
echo "5. All computer vision operations should use this folder"
echo "6. All logs (success, failure, error, info) saved to logs/"
echo "7. Run: python3 main_application.py"
echo "8. Monitor with: python3 debug/system_monitor.py"

echo ""
echo "📖 Documentation:"
echo "================="
echo "Read test-cv-yolo11-sam2-camera/README.md for more information"
echo "All information, messages, success, failure, error, info must be saved to logs/"
