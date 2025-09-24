# Uji Coba API_REFERENCE.md

- Referensi utama: [API_REFERENCE.md](../API_REFERENCE.md)

## Ringkasan Smoke Test
Tanggal: 2025-09-24

### Port 8080 (Installation Method)

```json
{"note":"hasil runtime tersedia di log pengujian"}
```

### Port 5000/5001/5002 (RVM-Jetson Services)
- Listener check: lihat hasil runtime.

- Health/status uji (sementara 404/500, endpoint perlu disesuaikan dengan implementasi aktual layanan):
```
GET /health @5000 → 404
GET /api/gui/status @5001 → 404; / → 500 (template belum tersedia)
GET /api/camera/status @5002 → 404
```

## Catatan
- Endpoint `/api/services/start` berhasil menyalakan layanan via RVM_SUDO_PASS.
- Endpoint health untuk 5000/5001/5002 belum sesuai contoh di API_REFERENCE.md; butuh implementasi/route health di masing-masing service.

## Tindak Lanjut
- Tambahkan route health sederhana pada tiap service:
  - 5000: GET /health → {"success":true}
  - 5001: GET /api/gui/status → {"success":true}
  - 5002: GET /api/camera/status (X-API-Key) → {"success":true}
  Lalu update dokumen ini dengan hasil baru.
