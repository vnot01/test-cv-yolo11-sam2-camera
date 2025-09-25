# API Reference (Quick Guide)

Project: MyRVM Integration on Jetson Orin
Last Tested: 2025-09-24

This quick guide summarizes the primary APIs for installation and operation. For the complete, tested reference, see `API_REFERENCE-v2.md`.

## Base URLs
- Installation (Jetson): `http://rvm_ip:8080`
- Remote Access (Jetson): `http://rvm_ip:5000`
- GUI Client (Jetson): `http://rvm_ip:5001`
- Camera Service (Jetson): `http://rvm_ip:5002`
- MyRVM-Platform (Server): `http://server_ip:8001`

Notes:
- Prefer Tailscale IP (`tailscale0`) for `rvm_ip`. Fallback to LAN/WiFi.

## Installation APIs (8080)
- `GET /api/status`
- `GET /api/hardware/detect`
- `GET /api/network/scan`
- `GET /api/ai/test`
- `POST /api/server/test` { server_url }
- `POST /api/deploy/start`

## 1-Click Services
- `POST /api/services/start`
  - Enables/starts: camera(5000), gui(5001), access(5002)
  - Requires sudo (NOPASSWD) or `RVM_SUDO_PASS`.

## Tailscale
- `POST /api/tailscale/up` { auth_key }
- `GET /api/tailscale/ip`

## RVM Self APIs (Server; X-API-Key)
- `POST /api/v2/rvm/self/claim`
- `PATCH /api/v2/rvm/self/update`

Deployment data source: `GET /api/deployment/data` (8080)

## Jetson Services
- 5000 Remote Access: API key required
- 5001 GUI Client: local APIs
- 5002 Camera Service: API key required

Recommendation: add simple health endpoints for each service.

## Quick Checks
```bash
curl -s http://server_ip:8001/api/health-check
curl -s http://rvm_ip:8080/api/status
```

Related:
- `docs/catatan/UJI_API_REFERENCE.md` (smoke tests)
- `API_REFERENCE-v2.md` (full, tested)



