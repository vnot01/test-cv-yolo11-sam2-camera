from ultralytics import YOLO
import os
import datetime
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

def batch_inference(model_path, input_folder, output_folder):
    """
    Run batch inference on all images in input folder
    
    Args:
        model_path (str): Path to the model file
        input_folder (str): Path to input images folder
        output_folder (str): Path to save output images
    """
    
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
    MODEL_PATH = "../models/best.pt"  # or "yolo11n.pt", "yolo11s.pt"
    INPUT_FOLDER = "../storages/images/input"
    OUTPUT_FOLDER = "../storages/images/output"
    
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
