#!/usr/bin/env python3
"""
Camera YOLO Inference Script
Processes captured camera images with YOLO11
"""

from ultralytics import YOLO
import datetime
import os
import sys
import subprocess
from pathlib import Path

def check_and_download_models():
    """Check if models exist, download if not"""
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
            download_script = Path("../download_yolo11n.py")
            if download_script.exists():
                result = subprocess.run([sys.executable, str(download_script)], 
                                      capture_output=True, text=True, cwd="./")
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

def process_camera_image(image_path):
    """Process captured camera image with YOLO"""
    # Configuration
    MODEL_PATH = "../models/best.pt"
    OUTPUT_FOLDER = "../storages/images/output/camera_yolo/results/images"
    
    # Check and download models if needed
    if not check_and_download_models():
        print("❌ Gagal mendownload model.")
        return False, "Failed to download models"
    
    # Create output folder if it doesn't exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Check if model file exists
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model tidak ditemukan: {MODEL_PATH}")
        return False, f"Model not found: {MODEL_PATH}"
    
    # Check if input image exists
    if not os.path.exists(image_path):
        print(f"❌ Image tidak ditemukan: {image_path}")
        return False, f"Image not found: {image_path}"
    
    try:
        print("🔍 Loading model...")
        model = YOLO(MODEL_PATH)
        
        print(f"🎯 Running inference on: {image_path}")
        results = model(image_path)
        
        # Generate output filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"camera_yolo_detection_{timestamp}.jpg"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Save results
        results[0].save(output_path)
        print(f"✅ Results saved to: {output_path}")
        
        # Prepare detection summary
        detection_summary = []
        if results[0].boxes is not None:
            num_detections = len(results[0].boxes)
            detection_summary.append(f"📊 Found {num_detections} objects")
            
            # Add details for each detection
            for i, box in enumerate(results[0].boxes):
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                detection_summary.append(f"   • Object {i+1}: Class {cls}, Confidence {conf:.2f}")
        else:
            detection_summary.append("No objects detected")
        
        summary_text = "\n".join(detection_summary)
        print(summary_text)
        
        return True, f"Success! {summary_text}"
        
    except Exception as e:
        error_msg = f"Error during inference: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 camera_yolo_inference.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    success, message = process_camera_image(image_path)
    
    if success:
        print("🎉 Inference completed successfully!")
    else:
        print("❌ Inference failed!")
        sys.exit(1)
