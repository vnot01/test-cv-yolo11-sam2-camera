# 4 - Register RVM

Dokumentasi fitur registrasi RVM dibagi 2 perspektif agar jelas siapa yang mengerjakan:

- 01_RVM_Jetson.md — Implementasi di sisi RVM/Jetson-Orin (Edge)
- 02_Server_MyRVM_Platform.md — Implementasi di sisi Server MyRVM-Platform

Catatan penting:
- Server URL mengikuti konfigurasi di sistem (lihat `installation_method/config/installation_config.json` atau `docs/NETWORK_CONFIGURATION.md`).
- Registrasi menggunakan API Key yang digenerate oleh teknisi dari Dashboard Server. Tidak membutuhkan approval admin tambahan.
- Gunakan juga input terpisah “AUTH Key Tailscale” untuk otomatis `tailscale up --authkey=...` saat deployment sehingga `rvm_ip` menggunakan IP Tailscale.


