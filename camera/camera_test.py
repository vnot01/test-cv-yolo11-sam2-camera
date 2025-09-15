#!/usr/bin/env python3
"""
Camera Test Script for Jetson Orin Nano
Tests USB camera functionality and displays live feed
"""

import cv2
import sys
import time
from pathlib import Path

def test_camera(camera_index=0):
    """
    Test camera functionality
    
    Args:
        camera_index (int): Camera index (usually 0 for first USB camera)
    """
    
    print(f"🎥 Testing camera index: {camera_index}")
    print("=" * 50)
    
    # Try to open camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot open camera {camera_index}")
        print("💡 Tips:")
        print("   • Check if camera is connected")
        print("   • Try different camera index (0, 1, 2, etc.)")
        print("   • Check camera permissions")
        return False
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"✅ Camera opened successfully!")
    print(f"   • Resolution: {width}x{height}")
    print(f"   • FPS: {fps}")
    print(f"   • Camera Index: {camera_index}")
    
    # Test frame capture
    ret, frame = cap.read()
    if not ret:
        print("❌ Error: Cannot read frame from camera")
        cap.release()
        return False
    
    print(f"✅ Frame captured successfully!")
    print(f"   • Frame shape: {frame.shape}")
    
    # Save test frame
    output_dir = Path("../storages/images/camera_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    test_image_path = output_dir / f"camera_test_{timestamp}.jpg"
    
    cv2.imwrite(str(test_image_path), frame)
    print(f"✅ Test image saved to: {test_image_path}")
    
    cap.release()
    return True

def list_available_cameras():
    """List all available cameras"""
    print("🔍 Scanning for available cameras...")
    print("=" * 50)
    
    available_cameras = []
    
    # Test camera indices 0-9
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                print(f"✅ Camera {i}: {width}x{height} @ {fps} FPS")
                available_cameras.append(i)
            cap.release()
        else:
            print(f"❌ Camera {i}: Not available")
    
    if available_cameras:
        print(f"\n📊 Found {len(available_cameras)} available camera(s): {available_cameras}")
    else:
        print("\n❌ No cameras found!")
        print("💡 Check:")
        print("   • USB camera connection")
        print("   • Camera drivers")
        print("   • USB port functionality")
    
    return available_cameras

def main():
    """Main function"""
    print("🎥 Jetson Orin Nano Camera Test")
    print("=" * 50)
    
    # List available cameras
    available_cameras = list_available_cameras()
    
    if not available_cameras:
        print("\n❌ No cameras available. Exiting...")
        return
    
    # Test first available camera
    camera_index = available_cameras[0]
    print(f"\n🧪 Testing camera {camera_index}...")
    
    if test_camera(camera_index):
        print(f"\n🎉 Camera test completed successfully!")
        print(f"   • Camera {camera_index} is working properly")
        print(f"   • Test image saved to storages/images/camera_test/")
    else:
        print(f"\n❌ Camera test failed!")
        print(f"   • Camera {camera_index} has issues")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Camera test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
