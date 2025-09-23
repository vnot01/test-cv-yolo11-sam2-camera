# 📎 Addendum Laporan Perubahan - myrvm-integration (2025-09-23)

Dokumen ini menambahkan rincian tanpa mengubah laporan sebelumnya.

## Tambahan Rincian
- API_REFERENCE.md ditambah alur registrasi terbaru:
  - Pre-register di Admin → API key diperoleh dari modal.
  - RVM “confirm/claim” via UI RVM menggunakan API key, lalu self-update (IP/port/timezone/lat/long).
- Seksi baru “RVM Self APIs (API Key Auth)” dengan contoh payload `self/claim` dan `self/update`.
- Paket dokumentasi Maps:
  - Implementasi Mapbox (Search suggest→retrieve, render, click-to-drop + deeplink)
  - Perencanaan Leaflet + MapTiler + LocationIQ (alternatif open/low-cost)

## Catatan Operasional
- Simpan API key dari Admin ke UI RVM secara aman untuk dipakai saat claim/update.
- Gunakan koordinat (lat/long) sebagai kebenaran utama; label tempat bisa di-override manual.

## Status
- Dokumentasi konsisten dengan backend terbaru dan siap dipakai di lapangan.
