#!/usr/bin/env python3
"""
Camera Resolution Test Script for Jetson Orin Nano
Tests different camera resolutions and capabilities
"""

import cv2
import sys
import time
from pathlib import Path

def test_camera_resolutions(camera_index=0):
    """
    Test different camera resolutions
    
    Args:
        camera_index (int): Camera index
    """
    
    print(f"🎥 Testing camera resolutions (Camera {camera_index})")
    print("=" * 60)
    
    # Open camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot open camera {camera_index}")
        return False
    
    # Common resolutions to test
    resolutions = [
        (320, 240),    # QVGA
        (640, 480),    # VGA
        (800, 600),    # SVGA
        (1024, 768),   # XGA
        (1280, 720),   # HD 720p
        (1280, 960),   # SXGA
        (1600, 1200),  # UXGA
        (1920, 1080),  # Full HD 1080p
        (2048, 1536),  # QXGA
        (2560, 1440),  # QHD
        (3840, 2160),  # 4K UHD
    ]
    
    print("Testing different resolutions:")
    print("-" * 60)
    
    successful_resolutions = []
    
    for width, height in resolutions:
        print(f"Testing {width}x{height}...", end=" ")
        
        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Get actual resolution
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Test frame capture
        ret, frame = cap.read()
        
        if ret and frame is not None:
            if actual_width == width and actual_height == height:
                print(f"✅ {actual_width}x{actual_height} @ {fps:.1f} FPS")
                successful_resolutions.append((actual_width, actual_height, fps))
            else:
                print(f"⚠️  {actual_width}x{actual_height} @ {fps:.1f} FPS (requested {width}x{height})")
                successful_resolutions.append((actual_width, actual_height, fps))
        else:
            print("❌ Failed")
    
    cap.release()
    
    print("\n" + "=" * 60)
    print("📊 RESOLUTION SUMMARY:")
    print("=" * 60)
    
    if successful_resolutions:
        print("✅ Supported resolutions:")
        for width, height, fps in successful_resolutions:
            print(f"   • {width}x{height} @ {fps:.1f} FPS")
        
        # Find maximum resolution
        max_res = max(successful_resolutions, key=lambda x: x[0] * x[1])
        print(f"\n🏆 Maximum resolution: {max_res[0]}x{max_res[1]} @ {max_res[2]:.1f} FPS")
        
        # Find best FPS resolution
        best_fps_res = max(successful_resolutions, key=lambda x: x[2])
        print(f"⚡ Best FPS resolution: {best_fps_res[0]}x{best_fps_res[1]} @ {best_fps_res[2]:.1f} FPS")
        
    else:
        print("❌ No supported resolutions found")
    
    return successful_resolutions

def test_camera_properties(camera_index=0):
    """
    Test camera properties and capabilities
    
    Args:
        camera_index (int): Camera index
    """
    
    print(f"\n🔧 Camera Properties Test (Camera {camera_index})")
    print("=" * 60)
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot open camera {camera_index}")
        return
    
    # Camera properties to check
    properties = {
        cv2.CAP_PROP_FRAME_WIDTH: "Frame Width",
        cv2.CAP_PROP_FRAME_HEIGHT: "Frame Height", 
        cv2.CAP_PROP_FPS: "FPS",
        cv2.CAP_PROP_BRIGHTNESS: "Brightness",
        cv2.CAP_PROP_CONTRAST: "Contrast",
        cv2.CAP_PROP_SATURATION: "Saturation",
        cv2.CAP_PROP_HUE: "Hue",
        cv2.CAP_PROP_GAIN: "Gain",
        cv2.CAP_PROP_EXPOSURE: "Exposure",
        cv2.CAP_PROP_AUTO_EXPOSURE: "Auto Exposure",
        cv2.CAP_PROP_FOURCC: "FourCC Codec",
        cv2.CAP_PROP_BUFFERSIZE: "Buffer Size",
    }
    
    print("Camera Properties:")
    print("-" * 60)
    
    for prop_id, prop_name in properties.items():
        value = cap.get(prop_id)
        if value != -1:
            if prop_id == cv2.CAP_PROP_FOURCC:
                # Convert FourCC to string
                fourcc_str = "".join([chr((int(value) >> 8 * i) & 0xFF) for i in range(4)])
                print(f"   • {prop_name}: {fourcc_str} ({int(value)})")
            else:
                print(f"   • {prop_name}: {value}")
        else:
            print(f"   • {prop_name}: Not supported")
    
    cap.release()

def capture_high_res_image(camera_index=0, width=1920, height=1080):
    """
    Capture high resolution image
    
    Args:
        camera_index (int): Camera index
        width (int): Image width
        height (int): Image height
    """
    
    print(f"\n📸 Capturing high resolution image ({width}x{height})")
    print("=" * 60)
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot open camera {camera_index}")
        return False
    
    # Set high resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # Get actual resolution
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Requested: {width}x{height}")
    print(f"Actual: {actual_width}x{actual_height}")
    
    # Capture frame
    ret, frame = cap.read()
    
    if ret and frame is not None:
        # Save image
        output_dir = Path("../storages/images/camera_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"high_res_{actual_width}x{actual_height}_{timestamp}.jpg"
        filepath = output_dir / filename
        
        cv2.imwrite(str(filepath), frame)
        print(f"✅ High resolution image saved: {filepath}")
        
        # Get file size
        file_size = filepath.stat().st_size / (1024 * 1024)  # MB
        print(f"   • File size: {file_size:.2f} MB")
        print(f"   • Image shape: {frame.shape}")
        
        cap.release()
        return True
    else:
        print("❌ Failed to capture high resolution image")
        cap.release()
        return False

def main():
    """Main function"""
    print("🎥 Jetson Orin Nano - Camera Resolution Test")
    print("=" * 60)
    
    # Check for command line arguments
    camera_index = 0
    if len(sys.argv) > 1:
        try:
            camera_index = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid camera index. Using default (0)")
    
    print(f"Using camera index: {camera_index}")
    
    # Test resolutions
    successful_resolutions = test_camera_resolutions(camera_index)
    
    # Test camera properties
    test_camera_properties(camera_index)
    
    # Try to capture high resolution image
    if successful_resolutions:
        # Try to capture at maximum resolution
        max_res = max(successful_resolutions, key=lambda x: x[0] * x[1])
        capture_high_res_image(camera_index, max_res[0], max_res[1])
    
    print("\n🎉 Camera resolution test completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
