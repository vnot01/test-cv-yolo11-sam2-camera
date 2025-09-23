# Maps Provider Comparison

Tanggal: 2025-09-23

Tujuan: Membandingkan penyedia peta/geocoding untuk integrasi dengan Leaflet.

## Ringkasan Kombinasi yang Disarankan
- UI Peta: Leaflet (open-source)
- Tiles: MapTiler (free tier, mudah diintegrasikan; OSM-derived)
- Geocoding: LocationIQ (OSM-based, free tier) atau MapTiler Geocoding (alternatif)

Catatan: Ini memang kombinasi (Leaflet + Tiles provider + Geocoding provider).

---

## Perbandingan

### 1) Google Maps Platform
- Sumber data/render: Proprietary (bukan OSM). Tiles & geocoding milik Google
- Fitur: Maps, Geocoding, Places, Directions, Distance Matrix, dsb.
- Integrasi Leaflet: Tidak resmi; biasanya pakai Google Maps JS native (bukan Leaflet)
- Harga/Free tier: Kredit bulanan ±USD 200; usage-based, kartu kredit diperlukan
- Limit: Tinggi, namun berbayar jika melewati kredit
- Lisensi: Komersial; pembatasan caching & penyajian
- Pro:
  - Kualitas data & fitur sangat kaya (autocomplete, places detail)
  - Performa tinggi, dokumentasi sangat lengkap
- Kontra:
  - Tidak OSM; biaya dapat meningkat
  - Vendor lock-in dan TOS ketat

### 2) Mapbox
- Sumber data/render: Banyak OSM + data tambahan; tiles vektor kuat
- Fitur: Maps (vector/raster), Geocoding, Directions, Isochrones, dsb.
- Integrasi Leaflet: Sangat baik (mapbox tiles/GL + plugin)
- Harga/Free tier: Ada free tier; usage-based pricing
- Limit: Cukup besar untuk dev; skala berbayar
- Lisensi: Komersial
- Pro:
  - Peta vektor modern, style kustom
  - Tooling/SDK matang
- Kontra:
  - Biaya meningkat di skala besar
  - Ketergantungan vendor untuk fitur advanced

### 3) HERE (Here Technologies)
- Sumber data/render: Proprietary (bukan OSM)
- Fitur: Maps, Geocoding/Reverse, Routing, Traffic, Fleet, dsb.
- Integrasi Leaflet: Ada (tiles raster + API)
- Harga/Free tier: Ada; usage-based pricing
- Limit: Baik untuk enterprise/logistik
- Lisensi: Komersial
- Pro:
  - Kuat untuk routing/logistics enterprise
  - Kualitas data tinggi & coverage global
- Kontra:
  - Komersial; pricing kompleks
  - Bukan OSM murni

### 4) MapTiler
- Sumber data/render: OSM-derived (OpenMapTiles) + sumber tambahan; tiles vector/raster
- Fitur: Tiles, Geocoding opsional, SDK, style editor
- Integrasi Leaflet: Sangat baik (URL tiles siap pakai)
- Harga/Free tier: Free tier cukup untuk dev/MVP; skala berbayar
- Limit: Usage limit di free tier; attribution wajib
- Lisensi: Komersial (berbasis OSM)
- Pro:
  - Sangat mudah untuk Leaflet
  - Bisa migrasi ke self-host (OpenMapTiles)
- Kontra:
  - Geocoding tidak setajam Google
  - Hosted tetap usage-based

### 5) LocationIQ
- Sumber data/render: Geocoding OSM-based (tidak menyediakan tiles render)
- Fitur: Geocoding/Reverse, Autocomplete, Timezone, dsb.
- Integrasi Leaflet: Mudah (REST geocoding + Leaflet untuk peta)
- Harga/Free tier: Free tier besar; usage-based pricing
- Limit: Rate limit; perlu API key
- Lisensi: Komersial (OSM-based)
- Pro:
  - API sederhana, ekonomis untuk MVP/SMB
  - OSM-based, cocok dengan MapTiler tiles
- Kontra:
  - Fitur tidak sekaya Google Places
  - Kualitas tergantung data OSM

---

## Tabel Ringkas

| Provider   | Data Source          | Tiles | Geocoding | Leaflet Fit | Free Tier | Cocok Untuk |
|------------|----------------------|-------|-----------|-------------|-----------|-------------|
| Google     | Proprietary (non-OSM)| Ya    | Ya        | Medium (native lib disarankan) | Kredit USD 200 | Fitur kaya, enterprise umum |
| Mapbox     | OSM + tambahan       | Ya    | Ya        | Sangat Baik | Ada       | Peta vektor modern, kustom style |
| HERE       | Proprietary          | Ya    | Ya        | Baik        | Ada       | Routing/logistik enterprise |
| MapTiler   | OSM-derived          | Ya    | Opsional  | Sangat Baik | Ada       | Leaflet + OSM tiles mudah |
| LocationIQ | OSM-based            | -     | Ya        | Sangat Baik | Ada       | Geocoding murah & simpel |

Keterangan: "Leaflet Fit" = kemudahan integrasi dengan Leaflet.

---

## Rekomendasi Akhir
- MVP/produksi ringan: **Leaflet + MapTiler (tiles) + LocationIQ (geocoding)**
- Satu vendor: **Leaflet + MapTiler (tiles+geocoding)**
- Fitur kaya (Places, autocomplete canggih): **Google Maps**
- Vektor & style kustom intensif: **Mapbox**
- Logistik/routing enterprise: **HERE**

## Catatan Operasional
- Simpan API key di `.env` dan gunakan proxy bila perlu
- Penuhi attribution OSM/penyedia tiles
- Sediakan fallback/caching untuk geocoding
