#!/usr/bin/env python3
"""
Camera SAM2 Inference Script
Processes captured camera images with SAM2 segmentation
"""

from ultralytics import YOLO, SAM
import datetime
import os
import sys
import subprocess
from pathlib import Path

def check_and_download_models():
    """Check if models exist, download if not"""
    models_dir = Path("../models")
    models_dir.mkdir(exist_ok=True)
    
    # Check YOLO models
    yolo_models_to_check = ["best.pt", "yolo11n.pt"]
    missing_yolo_models = []
    
    for model in yolo_models_to_check:
        model_path = models_dir / model
        if not model_path.exists():
            missing_yolo_models.append(model)
    
    # Check SAM2 models
    sam_models_to_check = [
        ("sam2.1_b.pt", "https://github.com/ultralytics/assets/releases/download/v8.3.0/sam2.1_b.pt"),
        ("sam2_b.pt", "https://github.com/ultralytics/assets/releases/download/v8.3.0/sam2_b.pt")
    ]
    missing_sam_models = []
    
    for model_name, model_url in sam_models_to_check:
        model_path = models_dir / model_name
        if not model_path.exists():
            missing_sam_models.append((model_name, model_url))
    
    # Download missing YOLO models
    if missing_yolo_models:
        print(f"⚠️  YOLO model tidak ditemukan: {', '.join(missing_yolo_models)}")
        print("📥 Memulai download YOLO model...")
        
        try:
            download_script = Path("../download_yolo11n.py")
            if download_script.exists():
                result = subprocess.run([sys.executable, str(download_script)], 
                                      capture_output=True, text=True, cwd="./")
                if result.returncode == 0:
                    print("✅ YOLO model berhasil didownload")
                else:
                    print(f"❌ Error downloading YOLO models: {result.stderr}")
                    return False
            else:
                print("❌ Script download YOLO tidak ditemukan")
                return False
        except Exception as e:
            print(f"❌ Error running YOLO download script: {e}")
            return False
    
    # Download missing SAM2 models
    if missing_sam_models:
        print(f"⚠️  SAM2 model tidak ditemukan: {', '.join([m[0] for m in missing_sam_models])}")
        print("📥 Memulai download SAM2 model...")
        
        for model_name, model_url in missing_sam_models:
            model_path = models_dir / model_name
            try:
                download_with_progress(model_url, model_path)
                print(f"✅ {model_name} berhasil didownload")
            except Exception as e:
                print(f"❌ Error downloading {model_name}: {e}")
                return False
    
    return True

def download_with_progress(url, filepath):
    """Download file dengan progress bar sederhana"""
    import requests
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    print(f"📥 Downloading {filepath.name}...")
    if total_size > 0:
        print(f"   Total size: {total_size / (1024*1024):.1f} MB")
    
    downloaded = 0
    with open(filepath, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    progress = (downloaded / total_size) * 100
                    print(f"\r   Progress: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)", end="", flush=True)
    
    print()  # New line after progress

def process_camera_image_with_sam2(image_path):
    """Process captured camera image with YOLO + SAM2"""
    # Configuration
    YOLO_MODEL_PATH = "../models/best.pt"
    SAM2_MODEL_PATH = "../models/sam2.1_b.pt"
    OUTPUT_FOLDER = "../storages/images/output/camera_sam2/results/images"
    
    # Check and download models if needed
    if not check_and_download_models():
        print("❌ Gagal mendownload model.")
        return False, "Failed to download models"
    
    # Create output folder if it doesn't exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Check if model files exist
    if not os.path.exists(YOLO_MODEL_PATH):
        print(f"❌ YOLO model tidak ditemukan: {YOLO_MODEL_PATH}")
        return False, f"YOLO model not found: {YOLO_MODEL_PATH}"
    
    if not os.path.exists(SAM2_MODEL_PATH):
        print(f"❌ SAM2 model tidak ditemukan: {SAM2_MODEL_PATH}")
        return False, f"SAM2 model not found: {SAM2_MODEL_PATH}"
    
    # Check if input image exists
    if not os.path.exists(image_path):
        print(f"❌ Image tidak ditemukan: {image_path}")
        return False, f"Image not found: {image_path}"
    
    try:
        print("🔍 Loading YOLO model...")
        yolo_model = YOLO(YOLO_MODEL_PATH)
        
        print("🔍 Loading SAM2 model...")
        sam2_model = SAM(SAM2_MODEL_PATH)
        
        print(f"🎯 Running YOLO detection on: {image_path}")
        yolo_results = yolo_model(image_path)
        
        # Extract bounding box coordinates from the YOLO results
        bboxes = yolo_results[0].boxes.xyxy if yolo_results[0].boxes is not None else []
        print(f"✅ Found {len(bboxes)} objects with YOLO")
        
        if len(bboxes) == 0:
            print("⚠️  No objects detected by YOLO, skipping SAM2")
            return True, "No objects detected by YOLO"
        
        print("🎯 Running SAM2 segmentation...")
        sam2_results = sam2_model(image_path, bboxes=bboxes)
        
        # Generate output filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"camera_sam2_detection_{timestamp}.jpg"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # Save results
        sam2_results[0].save(output_path)
        print(f"✅ Results saved to: {output_path}")
        
        # Prepare detection summary
        detection_summary = []
        detection_summary.append(f"📊 YOLO detected: {len(bboxes)} objects")
        detection_summary.append(f"📊 SAM2 segmented: {len(bboxes)} objects")
        
        # Add details for each detection
        for i, box in enumerate(yolo_results[0].boxes):
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            detection_summary.append(f"   • Object {i+1}: Class {cls}, Confidence {conf:.2f}")
        
        summary_text = "\n".join(detection_summary)
        print(summary_text)
        
        return True, f"Success! {summary_text}"
        
    except Exception as e:
        error_msg = f"Error during SAM2 inference: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 camera_sam2_inference.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    success, message = process_camera_image_with_sam2(image_path)
    
    if success:
        print("🎉 SAM2 inference completed successfully!")
    else:
        print("❌ SAM2 inference failed!")
        sys.exit(1)
