# Register RVM — Server (MyRVM-Platform)

Tanggung jawab tim Server:
- Menyediakan API Key untuk teknisi (RVM) lewat Dashboard Admin.
- Endpoint registrasi RVM dan validasi API Key.

## Persiapan di Server
1. Buat API Key RVM untuk teknisi (Dashboard Admin)
2. (Opsional) Buat Preauth/AUTH Key Tailscale di Admin Console untuk otomatisasi join jaringan

## Endpoint yang digunakan
- `POST /api/v2/rvm/self/claim` (header: `X-API-Key`)
- `PATCH /api/v2/rvm/self/update` (header: `X-API-Key`)

### Body minimal — Self Claim
```json
{
  "device_name": "RVM-Orin1",
  "software_version": "v1.2.3",
  "timezone": "Asia/Jakarta",
  "device_id": "<machine-id>",
  "mac_address": "<mac>"
}
```

### Body minimal — Self Update
```json
{
  "ip_address": "rvm_ip",
  "port": 5000,
  "timezone": "Asia/Jakarta",
  "latitude": -7.795,
  "longitude": 110.366
}
```
- Response sukses: 200/201 dengan objek RVM terdaftar dan/atau informasi lanjutan

## Catatan
- Admin membuat RVM (pre-register) via Dashboard → API Key tampil dan diberikan ke teknisi.
- Device melakukan self-claim dan self-update menggunakan `X-API-Key` (tanpa Bearer token).
- Server URL mengikuti konfigurasi produksi (lihat Network Configuration). Hindari localhost kecuali via port forwarding.
- Validasi API Key dilakukan di sisi Server; tidak perlu approval manual tambahan.


