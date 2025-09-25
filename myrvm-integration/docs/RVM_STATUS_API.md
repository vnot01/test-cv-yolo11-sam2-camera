# RVM Status API Documentation

## Overview
API endpoint untuk pemeriksaan status RVM dengan kategori: **active**, **inactive**, **maintenance**, **error**, **unknown**.

## Endpoint

### GET `/rvm/status`
Mendapatkan status komprehensif RVM dengan semua komponen.

**URL:** `http://100.117.234.2:5001/rvm/status`

**Response Format:**
```json
{
  "rvm_id": 1,
  "overall_status": "active",
  "status_details": {
    "system_health": {
      "status": "active",
      "cpu_usage": 0.7,
      "memory_usage": 41.8,
      "disk_usage": 36.9,
      "details": {
        "cpu_percent": 0.7,
        "memory_available": 4650872832,
        "memory_total": 7989948416,
        "disk_free": 149402394624,
        "disk_total": 249366470656
      }
    },
    "services": {
      "status": "active",
      "services": {
        "rvm-remote-camera.service": "active",
        "rvm-remote-gui.service": "active",
        "rvm-remote-access.service": "active",
        "rvm-metrics-sender.service": "active",
        "myrvm-application.service": "unknown"
      }
    },
    "api_connectivity": {
      "status": "active",
      "response": "Connected"
    },
        "hardware": {
            "status": "active",
            "temperature": "active",
            "disk": "active",
            "details": {
                "gpu_temperature": 51.0,
                "disk_usage": 36.9
            }
        },
        "power": {
            "status": "active",
            "details": {
                "total_power_mw": 10677.12,
                "total_power_w": 10.68,
                "total_power_display": "10.68 W",
                "cpu_power_mw": 2662.85,
                "cpu_power_display": "2.66 W",
                "gpu_power_mw": 8014.27,
                "gpu_power_display": "8.01 W",
                "cpu_gpu_combined_mw": 10677.12,
                "cpu_gpu_combined_display": "10.68 W",
                "soc_power_mw": 0.0,
                "soc_power_w": 0.0,
                "soc_power_display": "0 mW",
                "measured_total_mw": 1990.0,
                "measured_total_display": "1.99 W",
                "sensor_path": "/sys/devices/platform/bus@0/c240000.i2c/i2c-1/1-0040/hwmon/hwmon1"
            }
        },
    "network": {
      "status": "active",
      "local_network": "active",
      "internet": "active",
      "details": {
        "local_ip": "192.168.1.11",
        "public_ip": "182.8.227.111"
      }
    }
  },
  "timestamp": "2025-09-25T11:48:14.258040+07:00",
  "timezone_info": {
    "timezone": "Asia/Jakarta",
    "offset": "+0700",
    "offset_hours": 7.0,
    "current_time": "2025-09-25 11:48:14 WIB",
    "current_time_iso": "2025-09-25T11:48:14.258040+07:00"
  }
}
```

## Status Categories

### 1. **active** ✅
RVM berfungsi normal, semua komponen kritis berjalan dengan baik.

**Kondisi:**
- System health: CPU < 70%, Memory < 70%, Disk < 70%
- Services: Minimal 80% service aktif
- API connectivity: Terhubung ke server
- Network: Local dan internet aktif
- Hardware: Suhu normal, disk sehat

### 2. **inactive** ⏸️
RVM tidak aktif atau beberapa service tidak berjalan.

**Kondisi:**
- Services: Ada service yang inactive
- API connectivity: Tidak terhubung ke server
- Network: Local network atau internet tidak aktif

### 3. **maintenance** 🔧
RVM memerlukan maintenance atau perhatian.

**Kondisi:**
- System health: CPU > 70%, Memory > 70%, atau Disk > 70%
- Hardware: Suhu tinggi (>80°C) atau disk usage > 80%

### 4. **error** ❌
RVM mengalami error atau masalah serius.

**Kondisi:**
- System health: CPU > 90%, Memory > 90%, atau Disk > 90%
- Services: Ada service yang failed/error
- API connectivity: Error koneksi
- Hardware: Suhu sangat tinggi (>90°C) atau disk usage > 90%
- Network: Error koneksi

### 5. **unknown** ❓
Status tidak dapat ditentukan atau komponen tidak terdeteksi.

**Kondisi:**
- Hardware: Sensor tidak tersedia
- Services: Service tidak terdeteksi
- Network: Koneksi tidak dapat diverifikasi

## Status Details

### System Health
- **cpu_usage**: Persentase penggunaan CPU
- **memory_usage**: Persentase penggunaan memory
- **disk_usage**: Persentase penggunaan disk

### Services
Daftar status semua service RVM:
- `rvm-remote-camera.service`
- `rvm-remote-gui.service`
- `rvm-remote-access.service`
- `rvm-metrics-sender.service`
- `myrvm-application.service`

### API Connectivity
- **status**: Status koneksi ke server
- **response**: Response dari server

### Hardware
- **temperature**: Status suhu GPU
- **disk**: Status kesehatan disk
- **gpu_temperature**: Suhu GPU aktual (dari /sys/class/thermal)
- **disk_usage**: Persentase penggunaan disk

**GPU Temperature Logic:**
- **< 80°C**: `active` (Normal)
- **80-90°C**: `maintenance` (Perlu perhatian)
- **> 90°C**: `error` (Kritis)

### Power
- **status**: Status konsumsi daya
- **total_power_w**: Total daya dalam Watt
- **total_power_display**: Total daya dengan konversi otomatis (W/mW)
- **cpu_power_mw**: Daya CPU dalam mW
- **cpu_power_display**: Daya CPU dengan konversi otomatis (W/mW)
- **gpu_power_mw**: Daya GPU dalam mW
- **gpu_power_display**: Daya GPU dengan konversi otomatis (W/mW)
- **soc_power_w**: Daya SOC dalam Watt
- **soc_power_display**: Daya SOC dengan konversi otomatis (W/mW)
- **cpu_gpu_combined_mw**: Gabungan daya CPU+GPU
- **cpu_gpu_combined_display**: Gabungan daya CPU+GPU dengan konversi otomatis

**Power Status Logic:**
- **< 5W**: `inactive` (Daya rendah)
- **5-12W**: `active` (Normal)
- **12-15W**: `maintenance` (Daya tinggi)
- **> 15W**: `error` (Konsumsi daya berlebihan)

**Auto Conversion Logic:**
- **≥ 1000 mW**: Otomatis konversi ke W (Watt)
- **< 1000 mW**: Tetap menampilkan mW (milliWatt)

### Network
- **local_network**: Status jaringan lokal
- **internet**: Status koneksi internet
- **local_ip**: IP address lokal
- **public_ip**: IP address publik

## Usage Examples

### JavaScript/HTML
```html
<div id="rvm-status">
    <div>Status: <span id="status">Loading...</span></div>
    <div>Last Check: <span id="timestamp">Loading...</span></div>
    <div>Power: <span id="power">Loading...</span></div>
    <div>GPU Temp: <span id="gpu-temp">Loading...</span></div>
</div>

<script>
async function updateRVMStatus() {
    try {
        const response = await fetch('/rvm/status');
        const data = await response.json();
        
        document.getElementById('status').textContent = data.overall_status;
        document.getElementById('timestamp').textContent = data.timestamp;
        
        // Display power with auto conversion
        const powerDisplay = data.status_details.power.details.total_power_display;
        document.getElementById('power').textContent = powerDisplay;
        
        // Display GPU temperature
        const gpuTemp = data.status_details.hardware.details.gpu_temperature;
        document.getElementById('gpu-temp').textContent = `${gpuTemp}°C`;
        
        // Update status color
        const statusElement = document.getElementById('status');
        statusElement.className = `status-${data.overall_status}`;
        
    } catch (error) {
        console.error('Error fetching RVM status:', error);
    }
}

// Update every 30 seconds
setInterval(updateRVMStatus, 30000);
updateRVMStatus();
</script>

<style>
.status-active { color: green; }
.status-inactive { color: orange; }
.status-maintenance { color: yellow; }
.status-error { color: red; }
.status-unknown { color: gray; }
</style>
```

### Python
```python
import requests
import json

def get_rvm_status():
    try:
        response = requests.get('http://100.117.234.2:5001/rvm/status')
        data = response.json()
        
        print(f"RVM ID: {data['rvm_id']}")
        print(f"Overall Status: {data['overall_status']}")
        print(f"Timestamp: {data['timestamp']}")
        
        for component, details in data['status_details'].items():
            print(f"{component.upper()}: {details['status']}")
            
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

# Usage
status = get_rvm_status()
```

### cURL
```bash
# Get RVM status
curl -s http://100.117.234.2:5001/rvm/status | jq '.'

# Get only overall status
curl -s http://100.117.234.2:5001/rvm/status | jq '.overall_status'

# Get system health details
curl -s http://100.117.234.2:5001/rvm/status | jq '.status_details.system_health'

# Get services status
curl -s http://100.117.234.2:5001/rvm/status | jq '.status_details.services.services'
```

## Monitoring Integration

### Dashboard Integration
```javascript
// Real-time status monitoring
function startStatusMonitoring() {
    setInterval(async () => {
        const status = await fetch('/rvm/status').then(r => r.json());
        
        // Update dashboard
        updateStatusCard(status.overall_status);
        updateSystemHealth(status.status_details.system_health);
        updateServicesStatus(status.status_details.services);
        updateNetworkStatus(status.status_details.network);
        
    }, 30000); // Update every 30 seconds
}
```

### Alert System
```javascript
function checkStatusAlerts(status) {
    if (status.overall_status === 'error') {
        showAlert('RVM Error', 'RVM is experiencing critical issues');
    } else if (status.overall_status === 'maintenance') {
        showAlert('Maintenance Required', 'RVM needs attention');
    } else if (status.overall_status === 'inactive') {
        showAlert('RVM Inactive', 'RVM services are not running');
    }
}
```

## Error Handling

### Common Errors
- **Connection Error**: RVM tidak dapat diakses
- **Service Error**: Service tidak berjalan
- **Hardware Error**: Masalah hardware terdeteksi
- **Network Error**: Koneksi jaringan bermasalah

### Troubleshooting
1. **Status "unknown"**: Periksa koneksi dan service
2. **Status "error"**: Periksa log dan restart service
3. **Status "maintenance"**: Periksa resource usage
4. **Status "inactive"**: Start service yang diperlukan

## Related Endpoints

- `GET /system/status` - System metrics
- `GET /api/status` - API connectivity
- `GET /timezone/info` - Timezone information
- `POST /timezone/convert` - Timezone conversion
