# INSTALLATION GUIDE - RVM LOCATION A

**Tanggal**: 2025-09-21  
**Versi**: 1.0.0  
**Target**: Jetson Orin dengan MyRVM Integration  

---

## **📋 PREREQUISITES**

### **✅ Hardware Requirements:**
- **Jetson Orin** (sudah terinstal OS)
- **Motor Stepper** (untuk door control)
- **LED/LCD Touchscreen** (untuk user interface)
- **Camera** (untuk object detection)
- **Network Connection** (WiFi/Ethernet)
- **Power Supply** (stable power)

### **✅ Software Requirements:**
- **Ubuntu 20.04/22.04** (sudah terinstal)
- **Python 3.8+** (sudah terinstal)
- **Git** (sudah terinstal)
- **Network Access** (untuk download dependencies)

---

## **🚀 INSTALLATION STEPS**

### **STEP 1: Clone Repository**
```bash
# Clone MyRVM Integration repository
cd /home/my
git clone https://github.com/vnot01/test-cv-yolo11-sam2-camera.git
cd test-cv-yolo11-sam2-camera/myrvm-integration
```

### **STEP 2: Setup Virtual Environment**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### **STEP 3: Configure RVM Identity**
```bash
# Edit production configuration
nano config/production_config.json
```

**Update konfigurasi untuk Location A:**
```json
{
  "application": {
    "name": "MyRVM Application - Location A",
    "version": "1.0.0",
    "environment": "production",
    "debug": false,
    "log_level": "INFO"
  },
  "remote_access": {
    "server_url": "http://172.28.233.83:8001",
    "api_key": "your_api_key_here",
    "rvm_id": 5,
    "metrics_interval": 30,
    "command_timeout": 30
  }
}
```

**Note**: Ubah `rvm_id` dari `4` ke `5` untuk Location A.

### **STEP 4: Hardware Configuration**
```bash
# Test hardware components
python3 -c "
from hardware.hardware_detector import HardwareDetector
detector = HardwareDetector()
status = detector.detect_all_hardware()
print('Hardware Status:', status)
"
```

### **STEP 5: Camera Configuration**
```bash
# Test camera
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print('✅ Camera working')
    cap.release()
else:
    print('❌ Camera not working')
"
```

### **STEP 6: Network Configuration**
```bash
# Test network connectivity
curl http://172.28.233.83:8001/api/health-check
```

### **STEP 7: Install System Dependencies**
```bash
# Install system packages
sudo apt update
sudo apt install -y chromium-browser
sudo apt install -y xdotool
sudo apt install -y unclutter
```

### **STEP 8: Deploy Application**
```bash
# Run deployment script
chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh
```

### **STEP 9: Configure Auto-start**
```bash
# Enable systemd service
sudo systemctl enable myrvm-application.service
sudo systemctl start myrvm-application.service

# Check status
sudo systemctl status myrvm-application.service
```

### **STEP 10: Test GUI Client**
```bash
# Test GUI client
chmod +x scripts/start_gui_client.sh
./scripts/start_gui_client.sh
```

---

## **🔧 CONFIGURATION CUSTOMIZATION**

### **1. RVM ID Configuration**
```bash
# Set unique RVM ID for Location A
export RVM_ID=5
echo "RVM_ID=5" >> ~/.bashrc
```

### **2. Network Configuration**
```bash
# Configure network settings
sudo nano /etc/netplan/01-netcfg.yaml
```

### **3. Display Configuration**
```bash
# Configure display for LED/LCD Touchscreen
sudo nano /etc/X11/xorg.conf
```

### **4. Camera Configuration**
```bash
# Configure camera settings
sudo nano /etc/modprobe.d/camera.conf
```

---

## **🧪 TESTING & VALIDATION**

### **1. System Health Check**
```bash
# Test all components
python3 test_analisis3_integration.py
```

### **2. Hardware Test**
```bash
# Test hardware components
python3 -c "
from hardware.led_touch_screen_interface import LEDTouchScreenInterface
interface = LEDTouchScreenInterface()
interface.initialize()
print('Hardware Status:', interface.get_status())
"
```

### **3. Network Test**
```bash
# Test server connectivity
curl -X GET http://172.28.233.83:8001/api/health-check
```

### **4. GUI Test**
```bash
# Test GUI client
python3 -c "
from gui.gui_client import GUIClient
client = GUIClient(rvm_id='location_a_001', host='0.0.0.0', port=5001)
print('GUI Client initialized')
"
```

---

## **📊 MONITORING & LOGS**

### **1. Application Logs**
```bash
# View application logs
tail -f logs/myrvm_application.log
```

### **2. System Logs**
```bash
# View systemd logs
sudo journalctl -u myrvm-application.service -f
```

### **3. Hardware Logs**
```bash
# View hardware logs
tail -f logs/hardware_detector.log
```

### **4. Network Logs**
```bash
# View network logs
tail -f logs/api_client.log
```

---

## **🔧 TROUBLESHOOTING**

### **Common Issues:**

#### **1. Camera Not Working**
```bash
# Check camera permissions
ls -la /dev/video*
sudo usermod -a -G video $USER
```

#### **2. Display Issues**
```bash
# Check display configuration
xrandr
sudo nano /etc/X11/xorg.conf
```

#### **3. Network Issues**
```bash
# Check network connectivity
ping 172.28.233.83
nslookup 172.28.233.83
```

#### **4. Service Not Starting**
```bash
# Check service status
sudo systemctl status myrvm-application.service
sudo journalctl -u myrvm-application.service
```

---

## **📋 POST-INSTALLATION CHECKLIST**

### **✅ System Requirements:**
- [ ] Jetson Orin OS updated
- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed

### **✅ Application Configuration:**
- [ ] Repository cloned
- [ ] RVM ID configured (Location A = 5)
- [ ] Production config updated
- [ ] Network settings configured

### **✅ Hardware Configuration:**
- [ ] Motor stepper connected
- [ ] LED/LCD Touchscreen working
- [ ] Camera functional
- [ ] Network connectivity established

### **✅ Application Deployment:**
- [ ] Application deployed
- [ ] Systemd service enabled
- [ ] Auto-start configured
- [ ] GUI client working

### **✅ Testing & Validation:**
- [ ] System health check passed
- [ ] Hardware test passed
- [ ] Network test passed
- [ ] GUI test passed

### **✅ Monitoring:**
- [ ] Logs configured
- [ ] Monitoring enabled
- [ ] Alerts configured
- [ ] Backup configured

---

## **🎯 LOCATION A SPECIFIC CONFIGURATION**

### **RVM Identity:**
- **RVM ID**: 5
- **Location**: A
- **Name**: MyRVM Location A
- **Server URL**: http://172.28.233.83:8001

### **Hardware Configuration:**
- **Display**: LED/LCD Touchscreen
- **Camera**: USB/CSI Camera
- **Motor**: Stepper Motor
- **Network**: WiFi/Ethernet

### **Network Configuration:**
- **Local IP**: Auto-assigned
- **Server IP**: 172.28.233.83:8001
- **API Key**: your_api_key_here

---

## **📞 SUPPORT & MAINTENANCE**

### **Log Files:**
- Application: `/home/my/test-cv-yolo11-sam2-camera/myrvm-integration/logs/`
- System: `/var/log/myrvm-application.log`
- Hardware: `/var/log/hardware.log`

### **Configuration Files:**
- Main Config: `config/production_config.json`
- Service Config: `/etc/systemd/system/myrvm-application.service`
- Network Config: `/etc/netplan/01-netcfg.yaml`

### **Backup:**
- Config Backup: `backup/config/`
- Log Backup: `backup/logs/`
- Database Backup: `backup/database/`

---

**Status**: ✅ **READY FOR INSTALLATION**  
**Estimated Time**: 2-3 hours  
**Difficulty**: Intermediate  
**Prerequisites**: Basic Linux knowledge, Hardware setup experience
