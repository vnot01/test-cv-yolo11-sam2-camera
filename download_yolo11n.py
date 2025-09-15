#!/usr/bin/env python3
"""
Script untuk mendownload model YOLO v11n ke folder mycv/models
"""

import os
import sys
import requests
from pathlib import Path

# Aktifkan virtual environment
venv_path = "/home/my/mycv/myenv"
if os.path.exists(venv_path):
    venv_site_packages = os.path.join(venv_path, "lib", "python3.10", "site-packages")
    if venv_site_packages not in sys.path:
        sys.path.insert(0, venv_site_packages)

try:
    from ultralytics import YOLO
    print("✅ ultralytics berhasil diimport")
except ImportError as e:
    print(f"❌ Gagal import ultralytics: {e}")
    print("💡 Pastikan virtual environment aktif: source myenv/bin/activate")
    sys.exit(1)

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

def download_model(model_name, description="", custom_url=None):
    """Download model YOLO"""
    
    print(f"🚀 Downloading {model_name}...")
    if description:
        print(f"   {description}")
    
    # Buat direktori models jika belum ada
    models_dir = Path("/home/my/mycv/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Direktori models: {models_dir}")
    
    # Path model
    model_path = models_dir / model_name
    
    # Cek apakah model sudah ada
    if model_path.exists():
        print(f"⏭️  {model_name} sudah ada di {model_path}")
        return True
    
    print(f"📥 Downloading {model_name}...")
    
    try:
        if custom_url:
            # Download dari custom URL
            download_with_progress(custom_url, model_path)
            print(f"✅ {model_name} berhasil didownload ke {model_path}")
        else:
            # Download menggunakan ultralytics
            model = YOLO(model_name)
            
            # Pindahkan ke direktori models
            if os.path.exists(model_name):
                os.rename(model_name, model_path)
                print(f"✅ {model_name} berhasil didownload ke {model_path}")
            else:
                print(f"❌ File {model_name} tidak ditemukan setelah download")
                return False
        
        # Test loading model
        test_model = YOLO(str(model_path))
        print(f"✅ Model berhasil dimuat dan siap digunakan")
        return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def download_models():
    """Download YOLO v11n dan best.pt"""
    
    models_to_download = [
        ("yolo11n.pt", "YOLOv11 Nano - Model terkecil, tercepat", None),
        ("best.pt", "Best model - Model terbaik yang sudah dilatih", "https://github.com/vnot01/MySuperApps/releases/download/trained-models/best.pt")
    ]
    
    success_count = 0
    
    for model_name, description, custom_url in models_to_download:
        print(f"\n{'='*50}")
        if download_model(model_name, description, custom_url):
            success_count += 1
        print(f"{'='*50}")
    
    return success_count == len(models_to_download)

if __name__ == "__main__":
    success = download_models()
    if success:
        print("\n🎉 Download selesai! Model YOLO tersedia di /home/my/mycv/models/")
    else:
        print("\n❌ Download gagal. Periksa koneksi internet dan virtual environment.")
