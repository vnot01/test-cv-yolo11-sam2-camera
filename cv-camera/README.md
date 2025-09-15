# CV-Camera Integration

Folder ini berisi script integrasi antara web camera dengan YOLO dan SAM2 inference untuk real-time object detection dan segmentation.

## 📁 File Structure

```
cv-camera/
├── camera_yolo_integration.py    # Script integrasi Camera + YOLO
├── camera_yolo_inference.py      # Script YOLO inference untuk camera
├── camera_sam2_integration.py    # Script integrasi Camera + SAM2
├── camera_sam2_inference.py      # Script SAM2 inference untuk camera
└── README.md                     # Dokumentasi ini
```

## 🎥🤖 Camera + YOLO Integration

### Fitur Utama:

1. **Web Camera Interface** - Live camera feed via browser
2. **Image Capture** - Simpan gambar dari camera
3. **YOLO Inference** - Otomatis proses gambar dengan YOLO11
4. **Real-time Controls** - Start/Stop camera via web
5. **Activity Log** - Monitor aktivitas sistem

### Cara Menjalankan:

```bash
# Aktifkan virtual environment
cd /home/my/mycv
source myenv/bin/activate

# Jalankan script integrasi
cd cv-camera
python3 camera_yolo_integration.py
```

### Akses Web Interface:

- **Local**: http://localhost:5000
- **Network**: http://192.168.1.11:5000

## 🎯 Fitur Web Interface:

### Tombol Kontrol:
- **📸 Capture Image** - Simpan gambar saja
- **🤖 Capture + YOLO** - Simpan gambar + jalankan YOLO inference
- **🔄 Refresh Stream** - Refresh video stream
- **▶️ Start Camera** - Mulai camera
- **⏹️ Stop Camera** - Hentikan camera

### Informasi Real-time:
- **Resolution** - Resolusi camera
- **FPS** - Frame rate camera
- **Current FPS** - FPS aktual
- **Frame Count** - Jumlah frame yang diproses
- **Uptime** - Waktu camera aktif

### Activity Log:
- Monitor semua aktivitas sistem
- Timestamp untuk setiap aksi
- Status capture dan inference

## 📂 File Output:

### Gambar yang Di-capture:
- **Lokasi**: `../storages/images/camera_captures/`
- **Format**: `camera_capture_YYYYMMDD_HHMMSS.jpg`

### Hasil YOLO Inference:
- **Lokasi**: `../storages/images/output/`
- **Format**: `inference_result_YYYYMMDD_HHMMSS.txt`

## 🔧 Konfigurasi:

### Camera Settings:
- **Resolution**: 640x480
- **FPS**: 25
- **Camera Index**: 0 (default)

### Paths:
- **Capture Directory**: `../storages/images/camera_captures/`
- **Output Directory**: `../storages/images/output/`
- **YOLO Script**: `../test/simple_yolo11_inference.py`

## 🚀 Workflow:

1. **Start Camera** - Mulai camera streaming
2. **Capture + YOLO** - Klik tombol untuk capture dan inference
3. **Background Processing** - YOLO inference berjalan di background
4. **View Results** - Cek hasil di folder output

## 📋 Requirements:

- Python 3.x
- OpenCV (cv2)
- Flask
- Virtual environment aktif
- YOLO11 models tersedia
- Camera USB terhubung

## 🎥🎯 Camera + SAM2 Integration

### Fitur Utama:

1. **Web Camera Interface** - Live camera feed via browser
2. **Image Capture** - Simpan gambar dari camera
3. **SAM2 Segmentation** - Otomatis proses gambar dengan YOLO + SAM2
4. **Real-time Controls** - Start/Stop camera via web
5. **Activity Log** - Monitor aktivitas sistem

### Cara Menjalankan:

```bash
# Aktifkan virtual environment
cd /home/my/mycv
source myenv/bin/activate

# Jalankan script integrasi SAM2
cd cv-camera
python3 camera_sam2_integration.py
```

### Akses Web Interface:

- **Local**: http://localhost:5000
- **Network**: http://192.168.1.11:5000

## 🎯 Fitur Web Interface:

### Tombol Kontrol:
- **📸 Capture Image** - Simpan gambar saja
- **🎯 Capture + SAM2** - Simpan gambar + jalankan SAM2 segmentation
- **🔄 Refresh Stream** - Refresh video stream
- **▶️ Start Camera** - Mulai camera
- **⏹️ Stop Camera** - Hentikan camera

## 📂 File Output SAM2:

### Gambar yang Di-capture:
- **Lokasi**: `../storages/images/camera_captures/`
- **Format**: `camera_capture_YYYYMMDD_HHMMSS.jpg`

### Hasil SAM2 Segmentation:
- **Lokasi**: `../storages/images/output/camera_sam2/results/`
- **Inference Log**: `inference/inference_result_YYYYMMDD_HHMMSS.txt`
- **Segmentation Image**: `images/camera_sam2_detection_YYYYMMDD_HHMMSS.jpg`

## 🎉 Keunggulan:

- **Real-time** - Camera feed langsung
- **Integrated** - Camera + YOLO/SAM2 dalam satu interface
- **Background Processing** - Inference tidak mengganggu camera
- **Web-based** - Akses via browser dari device manapun
- **Activity Logging** - Monitor semua aktivitas
- **TTY Compatible** - Bisa dijalankan tanpa GUI
- **Dual AI Models** - YOLO untuk detection, SAM2 untuk segmentation
