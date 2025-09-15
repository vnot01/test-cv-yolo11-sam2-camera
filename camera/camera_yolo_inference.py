#!/usr/bin/env python3
"""
Real-time YOLO Inference with Camera for Jetson Orin Nano
Combines camera feed with YOLO object detection
"""

import cv2
import sys
import time
import datetime
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def check_and_download_models():
    """Check if YOLO models exist, download if not"""
    models_dir = Path("../models")
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
            download_script = Path("/home/my/mycv/download_yolo11n.py")
            if download_script.exists():
                result = subprocess.run([sys.executable, str(download_script)], 
                                      capture_output=True, text=True, cwd="/home/my/mycv")
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

def camera_yolo_inference(camera_index=0, model_path="../models/best.pt"):
    """
    Real-time YOLO inference with camera
    
    Args:
        camera_index (int): Camera index
        model_path (str): Path to YOLO model
    """
    
    print(f"🎥 Starting real-time YOLO inference (Camera {camera_index})")
    print(f"🤖 Using model: {model_path}")
    print("=" * 50)
    print("Controls:")
    print("   • Press 'q' to quit")
    print("   • Press 's' to save current frame with detection")
    print("   • Press 'ESC' to quit")
    print("=" * 50)
    
    # Import YOLO after checking models
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ Error: ultralytics not found. Please install ultralytics.")
        return False
    
    # Load YOLO model
    try:
        model = YOLO(model_path)
        print(f"✅ YOLO model loaded: {model_path}")
    except Exception as e:
        print(f"❌ Error loading YOLO model: {e}")
        return False
    
    # Open camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot open camera {camera_index}")
        return False
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Get actual camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"✅ Camera initialized: {width}x{height} @ {fps} FPS")
    
    # Create output directory
    output_dir = Path("../storages/images/camera_yolo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    frame_count = 0
    detection_count = 0
    start_time = time.time()
    
    try:
        while True:
            # Capture frame
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Error: Cannot read frame from camera")
                break
            
            frame_count += 1
            
            # Run YOLO inference
            results = model(frame, verbose=False)
            
            # Draw detections on frame
            annotated_frame = results[0].plot()
            
            # Count detections
            if results[0].boxes is not None:
                current_detections = len(results[0].boxes)
                detection_count += current_detections
            else:
                current_detections = 0
            
            # Calculate FPS
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                current_fps = frame_count / elapsed_time
            else:
                current_fps = 0
            
            # Add text overlay
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(annotated_frame, f"FPS: {current_fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Detections: {current_detections}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(annotated_frame, timestamp, (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(annotated_frame, f"Frame: {frame_count}", (10, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Display frame
            cv2.imshow('Jetson Orin Nano - YOLO Real-time Detection', annotated_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:  # 'q' or ESC
                print("👋 Quitting real-time inference...")
                break
            elif key == ord('s'):  # 's' to save
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"yolo_detection_{timestamp}.jpg"
                filepath = output_dir / filename
                
                cv2.imwrite(str(filepath), annotated_frame)
                print(f"📸 Detection saved: {filepath}")
    
    except KeyboardInterrupt:
        print("\n⏹️  Real-time inference interrupted by user")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        # Print statistics
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time if total_time > 0 else 0
        avg_detections = detection_count / frame_count if frame_count > 0 else 0
        
        print(f"\n📊 Session Statistics:")
        print(f"   • Total frames: {frame_count}")
        print(f"   • Total detections: {detection_count}")
        print(f"   • Total time: {total_time:.2f} seconds")
        print(f"   • Average FPS: {avg_fps:.2f}")
        print(f"   • Average detections per frame: {avg_detections:.2f}")
        print(f"   • Detections saved to: {output_dir}")
    
    return True

def main():
    """Main function"""
    print("🎥 Jetson Orin Nano - Real-time YOLO Inference")
    print("=" * 50)
    
    # Check and download models
    if not check_and_download_models():
        print("❌ Failed to download models. Exiting...")
        return
    
    # Check for command line arguments
    camera_index = 0
    model_path = "../models/best.pt"
    
    if len(sys.argv) > 1:
        try:
            camera_index = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid camera index. Using default (0)")
    
    if len(sys.argv) > 2:
        model_path = sys.argv[2]
    
    print(f"Using camera index: {camera_index}")
    print(f"Using model: {model_path}")
    
    # Start real-time inference
    success = camera_yolo_inference(camera_index, model_path)
    
    if success:
        print("✅ Real-time YOLO inference completed successfully!")
    else:
        print("❌ Real-time YOLO inference failed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Program interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
