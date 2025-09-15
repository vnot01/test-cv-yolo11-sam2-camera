from ultralytics import YOLO
from ultralytics import SAM
import os
import sys
import subprocess
import requests
from pathlib import Path

def download_with_progress(url, filepath):
    """Download file dengan progress bar sederhana"""
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
            # Jalankan script download
            download_script = Path("/home/my/mycv/download_yolo11n.py")
            if download_script.exists():
                result = subprocess.run([sys.executable, str(download_script)], 
                                      capture_output=True, text=True, cwd="/home/my/mycv")
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

# Check and download models if needed
if not check_and_download_models():
    print("❌ Gagal mendownload model. Keluar dari program.")
    sys.exit(1)

# Load your trained YOLO11 model
my_model = YOLO('../models/best.pt')

# Load the SAM2 model
sam_model = SAM('../models/sam2.1_b.pt')

# Run YOLO11 prediction to get bounding boxes
print("🔍 Running YOLO11 detection...")
my_results = my_model('../storages/images/input/55_mineral_filled.jpg')

# Extract bounding box coordinates from the YOLO results
bboxes = my_results[0].boxes.xyxy
print(f"✅ Found {len(bboxes)} objects with YOLO11")

# Use the bounding boxes as prompts for the SAM2 model
print("🎯 Running SAM2 segmentation...")
sam_results = sam_model('../storages/images/input/55_mineral_filled.jpg', bboxes=bboxes)

# Display or save the combined results with segmentation masks
# sam_results[0].show()

# Save results to output folder with timestamp
OUTPUT_FOLDER = "../storages/images/output/sam2"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
import datetime
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f"sam2_detection_{timestamp}.jpg"
output_path = os.path.join(OUTPUT_FOLDER, output_filename)

sam_results[0].save(output_path)
print(f"✅ SAM2 results saved to: {output_path}")

# Print detection summary
if my_results[0].boxes is not None:
    num_detections = len(my_results[0].boxes)
    print(f"📊 Detection Summary:")
    print(f"   • YOLO11 detected: {num_detections} objects")
    print(f"   • SAM2 segmented: {num_detections} objects")
    
    # Print details for each detection
    for i, box in enumerate(my_results[0].boxes):
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        print(f"   • Object {i+1}: Class {cls}, Confidence {conf:.2f}")
else:
    print("❌ No objects detected by YOLO11")

print("🎉 SAM2 inference completed!")
