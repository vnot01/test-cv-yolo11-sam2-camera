# API Reference v2 (Full, Tested)

Project: MyRVM Integration on Jetson Orin
Last Tested: 2025-09-24
Status: Stable (based on smoke tests in `docs/catatan/UJI_API_REFERENCE.md`)

## Overview
- Installation and deployment via port 8080 (Flask GUI)
- Edge services on ports 5000/5001/5002 (Remote/GUI/Camera)
- Platform server on port 8001 (MyRVM-Platform)
- RVM Self APIs use `X-API-Key`
- Prefer Tailscale IP for `rvm_ip`

## Base URLs
- RVM Installation: `http://rvm_ip:8080`
- RVM Remote: `http://rvm_ip:5000`
- RVM GUI: `http://rvm_ip:5001`
- RVM Camera: `http://rvm_ip:5002`
- Server: `http://server_ip:8001`

## 1) Installation Method APIs (8080)

### GET /api/status
Returns installation status and progress.

### GET /api/hardware/detect
Detects CPU/GPU/Camera/Network.

### GET /api/network/scan
Scans nearby WiFi networks.

### GET /api/ai/test
Checks YOLO and SAM2 model availability.

### POST /api/server/test
Request: `{ "server_url": "http://server_ip:8001" }`

### POST /api/deploy/start
Starts deployment worker; background process continues.

### POST /api/services/start
- Frees ports 5000/5001/5002; enables and restarts systemd services.
- Uses `RVM_SUDO_PASS` or NOPASSWD sudoers.
Response: `{ "success": true, "data": { "states": {"rvm-remote-camera.service": "active", ...} } }`

### Tailscale
- POST /api/tailscale/up `{ "auth_key": "tskey-..." }`
- GET /api/tailscale/ip → `100.x.x.x` if up

### Deployment Data
- GET /api/deployment/data → `{ device_id, mac_address, software_version, device_name }`

## 2) RVM Self APIs (Server 8001, X-API-Key)

### POST /api/v2/rvm/self/claim
Headers: `X-API-Key: {api_key}`
Body (example):
```json
{
  "device_name": "RVM-Orin1",
  "software_version": "v1.2.3",
  "timezone": "Asia/Jakarta",
  "device_id": "MACHINE-ID",
  "mac_address": "aa:bb:cc:dd:ee:ff"
}
```
Response: `{ success, data: { rvm_id, name, location_description, timezone, ... } }`

### PATCH /api/v2/rvm/self/update
Headers: `X-API-Key: {api_key}`
Body example:
```json
{
  "ip_address": "100.117.234.2",
  "port": 5000,
  "timezone": "Asia/Jakarta",
  "latitude": -6.2,
  "longitude": 106.8
}
```

## 3) Edge Services (5000/5001/5002)

Note: Health endpoints recommended. Current smoke tests show listeners are up; some routes may be pending.

### Remote Access (5000)
- Suggested health: `GET /health` → `{ "success": true }`
- Remote command: `POST /api/remote/command` (X-API-Key)
- Metrics: `GET /api/metrics` (X-API-Key)

Curl examples:
```bash
curl -s -H "X-API-Key: {api_key}" http://rvm_ip:5000/api/metrics
```

### GUI Client (5001)
- `GET /` (HTML UI)
- `GET /api/gui/status`

### Camera Service (5002)
- `GET /api/camera/status` (X-API-Key)
- `POST /api/camera/capture` (X-API-Key)
- `POST /api/camera/stream/{start|stop}` (X-API-Key)

Capture example:
```bash
curl -s -X POST http://rvm_ip:5002/api/camera/capture \
  -H "X-API-Key: {api_key}" \
  -H "Content-Type: application/json" \
  -d '{"resolution":"1920x1080","format":"jpeg"}'
```

## 4) MyRVM-Platform Server (8001)
- URL endpoint: `http://server_ip:8001`
### Health
- `GET /api/health-check`

### Auth
- `POST /api/v2/auth/login` → Bearer token

### Processing Engines (sample)
- `POST /api/v2/processing-engines` (Bearer)

## 5) Tested Results (Summary)
From `docs/catatan/UJI_API_REFERENCE.md`:
- 8080: status, hardware, network, ai, deploy OK
- /api/services/start OK (states active)
- 5000/5001/5002 listeners up; health routes pending
- 8001: health-check OK

## 6) Best Practices & Notes
- Use `X-API-Key` for RVM self APIs and edge-protected routes
- Prefer Tailscale IP for `rvm_ip` in self-update
- Ensure sudo config or `RVM_SUDO_PASS` for systemd operations
- Add minimal health endpoints on 5000/5001/5002 for monitoring parity with docs

## 7) Quick Verification Cheatsheet
```bash
# Server health
curl -s http://server_ip:8001/api/health-check

# Jetson install status
curl -s http://rvm_ip:8080/api/status

# Start services (1-click)
curl -s -X POST http://rvm_ip:8080/api/services/start

# Tailscale IP
curl -s http://rvm_ip:8080/api/tailscale/ip
```

## 8) Cross-links
- `docs/catatan/UJI_API_REFERENCE.md` (smoke tests)
- `docs/API_REFERENCE.md` (original detailed doc inside docs/)
- `NETWORK_CONFIGURATION.md` (if present)
