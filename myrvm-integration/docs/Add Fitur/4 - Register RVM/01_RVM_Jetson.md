# Register RVM — RVM/Jetson-Orin (Edge)

Status: Siap implementasi pada Dashboard (Installation Method, port 8080)

## Input yang diperlukan (Dashboard 8080)
- Server URL (otomatis dari config)
- API Key Server (RVM)
- AUTH Key Tailscale (tskey-...)
- Name dan Location Description

## Urutan saat deployment
1. Install Tailscale bila belum terpasang
2. Jalankan `tailscale up` dengan AUTH Key (tskey-...)
3. Poll hingga IP `tailscale0` tersedia → set `rvm_ip`
4. Kirim registrasi ke Server (`POST /api/v2/rvms`) menggunakan header `X-API-Key`

## Data yang dikirim
- name, location_description (input teknisi)
- ip_address: IP Tailscale (`tailscale0`) — prioritas utama
- port: 5000 (Remote Access)
- device_id: isi dari `/etc/machine-id`
- mac_address: MAC `tailscale0` (fallback `wlP1p1s0`)

## Catatan
- AUTH Key Tailscale tidak disimpan permanen; digunakan sebagai variabel runtime saat deployment.
- Gunakan HTTPS jika tersedia.
