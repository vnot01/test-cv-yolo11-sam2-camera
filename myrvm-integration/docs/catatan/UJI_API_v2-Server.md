### endpoint: /api/v2/rvms/{rvm_id}/metrics
### URL untuk mengirim data: ``POST /api/v2/rvms/{id}/metrics``
- Ganti {id} dengan ID dari RVM yang bersangkutan.

### Struktur Data (JSON Payload)
#### Data yang dikirim harus dalam format JSON dengan struktur sebagai berikut:
```json
{
  "system_metrics": {
    "cpu_usage": 25.5,
    "memory_usage": 60.2,
    "disk_usage": 45.8,
    "gpu_usage": 30.1,
    "temperature": 42.5,
    "gpu_temperature": 55.0,
    "disk_read_speed": 100.5,
    "disk_write_speed": 50.2,
    "network_upload_speed": 10.5,
    "network_download_speed": 100.2,
    "memory_available": 4096,
    "disk_available": 102400,
    "load_average": 1.5
  },
  "application_metrics": {
    "software_version": "v1.3.0-test",
    "ai_model_version": "best.pt-v2.2",
    "ai_model_path": "/models/best.pt",
    "uptime_seconds": 3600,
    "deposit_count_since_restart": 35,
    "last_deposit_time": "2025-09-24T12:30:00Z",
    "error_count": 1,
    "warning_count": 5
  },
  "network_info": {
    "local_ip": "192.168.1.101",
    "virtual_ip": "10.0.0.101",
    "gateway_ip": "192.168.1.1",
    "dns_servers": ["8.8.8.8", "1.1.1.1"],
    "network_interface": "eth0",
    "connection_type": "ethernet",
    "signal_strength": -40
  }
}
```

```bash
curl -X POST "http://server:8001/api/v2/rvms/1/metrics" \
  -H "Content-Type: application/json" \
  -d '{ /* JSON structure above */ }'
```

### Mengambil Metrics dari Server :
```bash
curl -X GET "http://server:8001/api/v2/rvms/1/metrics" \
  -H "Accept: application/json"
```



### POST Response (Success) :
```json
{
  "success": true,
  "message": "Metrics stored successfully"
}
```
### GET Response :
```json
{
  "success": true,
  "data": {
    "system": { /* system metrics */ },
    "application": { /* application metrics */ },
    "network": { /* network info */ },
    "timestamp": "2025-09-24T12:33:56.342489Z"
  }
}
```


### Yang Perlu Diperhatikan untuk Implementasi RVM
1. Pastikan uptime_seconds ≤ 9999 untuk menghindari database overflow
2. Gunakan endpoint API v2 untuk fitur yang lebih lengkap
3. Kirim data secara berkala (misalnya setiap 5-10 menit) untuk monitoring real-time
4. Handle error response dengan baik di sisi RVM