## API Reference v2 (RVM Jetson Integration)

This document describes version 2 of the RVM Integration API exposed by the Remote GUI Service (port 5001) and the metrics sender. It supersedes prior quick references.

### Base
- Base URL (RVM): http://<RVM_IP>:5001
- Auth: For server callbacks (if any), custom headers may be used. Client → Server metrics use `X-API-Key` provided by the platform.

### OTA Management
- POST `/ota/github/pull`
  - Description: Stop services, git reset to origin/main, download models (RVM, SAM2.1, YOLO11), write `.version` files from release tags, restart services.
  - Body (JSON, optional overrides):
    - `rvm_model_url` (string)
    - `sam_model_url` (string)
    - `yolo_model_url` (string)
  - Response: `{ success: boolean, message: string, status_file: string }`

- GET `/ota/status`
  - Description: Check last OTA run status and log tail.
  - Response: `{ success: boolean, data: { status: running|success|error, log_tail: string } }`

### Timezone Utilities
- GET `/timezone/info`
  - Returns RVM local timezone info (name, offset, current time).

- POST `/timezone/convert`
  - Body: `{ timestamp: string (UTC or ISO) }`
  - Returns local time string, ISO, and relative string.

### Metrics Ingest (Server-side Endpoint)
- POST `/api/v2/rvms/{rvm_id}/metrics`
  - Description: RVM sends metrics payload to server. Implemented by the metrics sender.
  - Headers: `Content-Type: application/json`, `X-API-Key`, `X-RVM-ID`, `X-Requested-With`
  - Payload (example):
```
{
  "rvm_id": 1,
  "timezone": "Asia/Jakarta",
  "timestamp": "2025-09-25T14:45:29.726274+07:00",
  "system_metrics": {
    "cpu_usage": 1.5,
    "memory_usage": 41.7,
    "disk_usage": 35.0,
    "gpu_usage": 0.0,
    "temperature": 51.6,
    "gpu_temperature": 51.4,
    "disk_read_speed": 0,
    "disk_write_speed": 0,
    "network_upload_speed": 0,
    "network_download_speed": 0,
    "memory_available": 4655190016,
    "disk_available": 149394894848,
    "process_count": 339,
    "load_average": 1.01,
    "uptime": 9999,
    "power_consumption": {
      "sensor_path": "/sys/devices/platform/bus@0/c240000.i2c/i2c-1/1-0040/hwmon/hwmon1",
      "gpu_power_mw": 6549.504,
      "cpu_power_mw": 1791.36,
      "measured_total_mw": 1757.184,
      "cpu_gpu_combined_mw": 8340.864,
      "total_power_mw": 8340.864,
      "soc_power_mw": 0.0,
      "gpu_power_display": "6.55 W",
      "cpu_power_display": "1.79 W",
      "measured_total_display": "1.76 W",
      "cpu_gpu_combined_display": "8.34 W",
      "total_power_display": "8.34 W",
      "soc_power_display": "0.0 mW"
    }
  },
  "application_metrics": {
    "software_version": "1.0.0",
    "ai_model_version": "v1.0.0",
    "ai_model_path": "/home/my/models/best.pt",
    "uptime_seconds": 11,
    "deposit_count_since_restart": 0,
    "last_deposit_time": null,
    "error_count": 0,
    "warning_count": 0
  },
  "network_info": {
    "local_ip": "203.0.113.45",  // via ip-api.com "query"
    "virtual_ip": "100.117.234.2",
    "gateway_ip": "192.168.1.1",
    "dns_servers": ["127.0.0.53"],
    "network_interface": "wlP1p1s0",
    "connection_type": "wireless",
    "signal_strength": 80,
    "last_network_check": "2025-09-25T14:45:29.725826+07:00"
  }
}
```

Notes:
- `network_info.local_ip` is resolved via `http://ip-api.com/json` (field `query`) with fallbacks to routing table and interface enumeration.
- `application_metrics.ai_model_version` is sourced from `models/best.pt.version` (tag from release URL), falling back to file modified timestamp.
- Power metrics are read from Jetson hwmon at `/sys/devices/platform/bus@0/c240000.i2c/i2c-1/1-0040/hwmon/hwmon1`, with automatic mW→W display when ≥1000 mW.

### RVM Status
- GET `/rvm/status`
  - Provides aggregated status with components: system, services, API connectivity, hardware, network, power.
  - Includes GPU temperature and power breakdown with auto-converted display fields.

### Time Handling
- All timestamps include local timezone offset from the RVM device. Client-side endpoints provide conversion helpers.

### External References
- IP Geolocation service used for `local_ip`: [ip-api.com](https://ip-api.com)


