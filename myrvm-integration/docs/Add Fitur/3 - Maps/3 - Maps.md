# Add Fitur: Maps (Picker + Search)

Tanggal: 2025-09-23
Status: Draft Rekomendasi + Rencana Implementasi

## Tujuan
Menambahkan fasilitas peta pada form RVM sehingga admin dapat:
- Mencari lokasi berdasarkan nama/alamat (geocoding)
- Klik pada peta untuk menempatkan pin dan menangkap koordinat latitude/longitude
- Menyimpan hasil lat/long ke tabel `reverse_vending_machines`

## Kebutuhan Teknis
- Input: Name, Location (sudah ada), tambahan koordinat lat/long (sudah ditambahkan via migration)
- UI: Map picker dengan pin draggable + search box
- Backend: Menyimpan `latitude`, `longitude` sebagai decimal(10,7)

## Opsi Provider & Layanan

Kriteria: (1) Pencarian alamat, (2) Pin → lat/long, (3) Free/kuota besar, (4) Open-source opsi.

1) Leaflet (library peta) + OpenStreetMap tiles
- Fungsi: render peta, interaksi klik/drag pin (gratis, open-source)
- Perlu penyedia tiles yang comply dengan OSM Tile Usage Policy (hindari memakai tile OSM publik untuk beban berat/komersial)
- Cocok: sebagai fondasi UI

2) Geocoding (cari alamat → lat/long dan sebaliknya)
- Nominatim (OSM) – gratis, open-source, rate limit ketat untuk instance publik; disarankan self-host untuk beban tinggi
- Photon (Komoot) – open-source, bisa self-host; ada publik endpoint namun tetap ada limit
- Pelias – open-source, enterprise-grade, bisa self-host; resources lebih berat
- LocationIQ – komersial dengan free tier cukup besar, API sederhana, OSM-based
- MapTiler Geocoding – komersial, free tier lumayan untuk prototyping

3) Tiles/Map data
- MapTiler – generous free tier, SDK mudah, komersial
- Stadia Maps – komersial, free tier
- OpenMapTiles (self-host) – open-source stack untuk tiles; perlu resource server
- MapLibre GL – library render vektor (opsional jika mau vektor vs raster)

4) Google Maps / Mapbox / HERE (komersial)
- Kaya fitur, namun tidak free unlimited. Biasanya butuh kartu kredit & biaya pemakaian

## Rekomendasi Praktis (Balance: Gratis, Stabil, Mudah)
- UI peta: Leaflet (gratis, battle-tested)
- Tiles: MapTiler raster (free tier, dapat diganti self-host nanti)
- Geocoding: LocationIQ (free tier cukup besar) atau MapTiler Geocoding sebagai alternatif
- Alternatif open-source murni (untuk on-prem besar): Leaflet + self-host OpenMapTiles + self-host Pelias/Photon/Nominatim

Alasan:
- Leaflet ringan dan mudah integrasi (drag/klik marker → lat/long)
- LocationIQ: API sederhana, OSM-based, free tier relatif ramah untuk MVP
- Dapat di-swap ke self-host jika traffic naik (OpenMapTiles + Pelias/Nominatim)

## Perbandingan Ringkas
- **Leaflet**: UI peta (gratis). Kelebihan: fleksibel, ekosistem luas. Kekurangan: butuh penyedia tiles terpisah
- **LocationIQ**: Geocoding (free tier). Kelebihan: simple, OSM-based. Kekurangan: tetap ada rate limit
- **MapTiler**: Tiles & Geocoding (free tier). Kelebihan: satu vendor; Kekurangan: komersial bila scale besar
- **Nominatim (publik)**: gratis tapi rate limit ketat; production disarankan self-host
- **Pelias/Photon (self-host)**: elastis, tapi butuh infrastruktur

## Sumber Data/Render (OSM atau Bukan)
- Leaflet: Hanya library render; sumber data/tiles mengikuti provider yang dipakai (bisa OSM atau non-OSM)
- OpenStreetMap (OSM) Tiles: OSM (open data); untuk produksi gunakan penyedia tiles pihak ketiga atau self-host
- MapTiler: OSM-derived (OpenMapTiles) + sumber tambahan; lisensi komersial dengan free tier
- LocationIQ (Geocoding): Berbasis OSM (open data) dengan infrastruktur komersial
- Nominatim/Photon/Pelias (self-host): OSM (open data)
- Google Maps / Mapbox / HERE: Bukan OSM murni (sumber data campuran/tertutup, berlisensi komersial)

## Rencana Implementasi (Front-End Admin)

1) Tambah Map Picker di halaman `admin/rvm/*` (pada modal Edit RVM – Add tetap minimal):
- Komponen Leaflet map 100% width, tinggi 320–420px
- Marker draggable; event `dragend` untuk update input hidden `latitude` dan `longitude`
- Klik map menempatkan/relokasi pin

2) Search Box (Geocoding)
- Input text + tombol search
- Panggil API geocoding (LocationIQ/MapTiler) → ambil lat/long + bounding box
- Set view peta ke hasil dan pindahkan pin ke koordinat tersebut

3) Penyimpanan
- Saat submit, kirim `latitude`, `longitude` (hidden) bersama field lain ke controller
- Backend `RvmController@store/update` menerima dan menyimpan jika ada

4) Konfigurasi Kunci API
- `.env` contoh:
  - MAP_TILES_KEY=...
  - GEOCODING_PROVIDER=locationiq | maptiler
  - GEOCODING_API_KEY=...
- Ambil kunci via config dan injeksi aman ke Blade

## Contoh Teknis (Skema Integrasi)
- Leaflet Init:
  - Tile URL (MapTiler raster): `https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?key=YOUR_KEY`
  - Attribution sesuai lisensi
- Marker & Event:
  - `L.marker([lat, lng], {draggable: true})`
  - `marker.on('dragend', () => { /* update hidden inputs */ })`
  - `map.on('click', (e) => { marker.setLatLng(e.latlng); /* update inputs */ })`
- Geocoding Search (LocationIQ):
  - Endpoint: `https://us1.locationiq.com/v1/search?key=KEY&q=QUERY&format=json`
  - Ambil hasil pertama → set map view + marker

Catatan:
- Tambahkan debounce untuk search, caching ringan untuk query populer
- Tampilkan attribution OSM/penyedia tiles

## Roadmap & Alternatif Self-host (Jika Traffic Besar)
- Tiles: Self-host OpenMapTiles + TileServer GL
- Geocoding: Self-host Pelias atau Nominatim
- Pro: bebas limit, kontrol penuh. Kontra: operasional & biaya infra

## Estimasi Effort
- Integrasi dasar (Leaflet+geocoding+picker): 0.5–1 hari
- Backend wiring: minor (sudah siap kolom)
- Self-host stack: beberapa hari–minggu

## Keputusan Rekomendasi
- Tahap 1: Leaflet + MapTiler tiles (free) + LocationIQ geocoding (free tier)
- Tahap 2: Evaluasi pindah ke MapTiler full atau self-host OpenMapTiles + Pelias

## Risiko & Mitigasi
- Rate limit tercapai → debounce, cache, fallback provider
- API key terekspos → .env + proxy server-side bila perlu
- Kebijakan tiles → gunakan penyedia resmi atau self-host

---

## Checklist Implementasi (Tahap 1)
- [ ] Tambah env keys untuk tiles & geocoding
- [ ] Tambah komponen peta (Leaflet) di Edit RVM (Add tetap minimal)
- [ ] Implement click & drag pin → isi hidden `latitude`, `longitude`
- [ ] Implement search → geocoding API → set view & pin
- [ ] Submit → controller simpan lat/long
- [ ] (Opsional) tampilkan koordinat ringkas di kartu RVM
