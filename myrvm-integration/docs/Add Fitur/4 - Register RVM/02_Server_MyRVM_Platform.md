# Register RVM — Server (MyRVM-Platform)

Tanggung jawab tim Server:
- Menyediakan API Key untuk teknisi (RVM) lewat Dashboard Admin.
- Endpoint registrasi RVM dan validasi API Key.

## Persiapan di Server
1. Buat API Key RVM untuk teknisi (Dashboard Admin)
2. (Opsional) Buat Preauth/AUTH Key Tailscale di Admin Console untuk otomatisasi join jaringan

## Endpoint yang digunakan
- `POST /api/v2/rvms` (header: `X-API-Key`)
- Body minimal:
```json
{
  "name": "RVM-Orin1",
  "location_description": "Lobby A",
  "ip_address": "rvm_ip",
  "port": 5000,
  "device_id": "<machine-id>",
  "mac_address": "<mac>"
}
```
- Response sukses: 200/201 dengan objek RVM terdaftar dan/atau informasi lanjutan

## Catatan
- Server URL mengikuti konfigurasi produksi (lihat Network Configuration). Hindari localhost kecuali via port forwarding.
- Validasi API Key dilakukan di sisi Server; tidak perlu approval manual tambahan.
