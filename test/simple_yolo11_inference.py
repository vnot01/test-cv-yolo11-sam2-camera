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

def main():
    # Configuration
    MODEL_PATH = "../models/best.pt"  # Change to your model path
    INPUT_IMAGE = "../storages/images/input/55_mineral_filled.jpg"
    OUTPUT_FOLDER = "../storages/images/output/yolo11"
    
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
    
    print("🔍 Loading model...")
    model = YOLO(MODEL_PATH)
    
    print(f"🎯 Running inference on: {INPUT_IMAGE}")
    results = model(INPUT_IMAGE)
    
    # Generate output filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"yolo11_detection__{timestamp}.jpg"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    
    # Save results
    results[0].save(output_path)
    print(f"✅ Results saved to: {output_path}")
    
    # Print detection summary
    if results[0].boxes is not None:
        num_detections = len(results[0].boxes)
        print(f"📊 Found {num_detections} objects")
        
        # Print details for each detection
        for i, box in enumerate(results[0].boxes):
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            print(f"   • Object {i+1}: Class {cls}, Confidence {conf:.2f}")
    else:
        print("No objects detected")
    
    print("Inference completed!")

if __name__ == "__main__":
    main()
